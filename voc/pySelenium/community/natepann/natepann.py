"""
====================================
 :mod:`community/natepann`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for Nate Pann
"""
# Authors
# ===========
#
# * JeYoung Park, Jerry Chae
#
# Change Log
# --------
#
#  * [2024/07/30]
#     - 본문만 찍는것으로 변경
#  * [2024/07/29]
#     - 스크린샷 찍기 전, 불필요한 정보 제거 로직 추가
#  * [2024/03/19]
#     - 에러 코드 세분화, 에러 로그 세분화
#  * [2023/06/23]
#     - 게시글 제목, 게시글 수 XPath 변경
#  * [2023/04/25]
#     - 답글까지 스크린샷에 포함되도록 수정
#  * [2022/08/03]
#     - 게시글 작성일 xpath변경
#  * [2022/04/19]
#     - stop_article_older_than 에러 수정.
#  * [2022/04/14]
#     - 네이트판 게시글 제목 찾는 방식변경 목록 -> 게시글 내
#  * [2022/03/22]
#     - 포맷 적용완료. 코드클리어링 진행  headless해야 게시글 캡쳐에 오래걸리지않음.
#  * [2022/01/06]
#     - 대댓글 페이지네이션 처리
#  * [2022/01/05]
#     - starting


################################################################################
import re
import os
import sys
import yaml
import json
import time
import shutil
import random
import tarfile
import datetime
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
class PannSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'PannSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['search'],
             start_ts]
        )
        self.config['target']['folder'] += '/' + folder_name
        self.is_done = False
        self.cur_page = 0
        self.cmt_done = False
        self.article_num = 0
        out_config = deepcopy(self.config)
        # del out_config['params']['site']['passwd']
        del out_config['params']['kwargs']['logger']
        self.output = {
            'start_ts': start_ts,
            'config': out_config,
            'article_list': [],
            'latest_create_article_ts': None,
            'cafe_info': {
                'name': None,
                'url': None,
                'since': None,
                'category': None,
                'register_type': None,
                'write_condition': None,
                'num_members': None,
                'num_visitors': None,
            },
            'app_info': {
                'star_like': None,
                'num_reviews': None,
                'title': None,
                'contents': None,
                'version': None,
                'num_download': None,
            }
        }
        self.logger.info(f'Starting Nate Pann Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            # 로그인 클릭
            e = self.get_by_xpath('//*[@id="GnbWrap"]/div[2]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # login 화면
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="uid"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//*[@id="upw"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="f_login"]/fieldset/input',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def search(self):
        try:
            # 검색어 입력
            e = self.get_by_xpath('//*[@id="input_search"]')
            self.send_keys(e, self.config['params']['site']['search'])
            # 검색 단추
            e = self.get_by_xpath('//*[@id="search"]/fieldset/button',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        except Exception as err:
            self.logger.error(f'search: Error: "{str(err)}"')

    # ==========================================================================
    def next_cmt(self):

        # 역할
        # 1. 대댓글 페이지를 넘기는 기능과
        # 2. 더 이상 페이지가 없는 경우 대댓글이 없음을 알려주는 기능 수행 self.reply_done = true
        # 참고 : 최문창님의 코드 인용하여 적용

        # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
        # 따라서 두 가지 종류의 태그를 모두 구해야 함
        # 현재의 게시글이 포함된 페이지는 class가 current이다.
        try:
           cmtPagePart = self.get_by_xpath('//div[@class="paginate-reple"]')
           is_current = False # 다음 페이지로 넘기기 위해 사용하는 플래그
           for cmtPage in cmtPagePart.find_elements_by_xpath('.//strong | .//a'):
               if cmtPage.get_attribute('class') == 'current':
                   is_current = True
                   continue
               if is_current:
                   self.safe_click(cmtPage)
                   self.implicitly_wait()
                   return
           self.cmt_done = True
        except Exception as err:
           raise
        finally:
           return

    # ==========================================================================
    def get_cmt(self, msg, biasNum):
        # 댓글이 0 인 경우나 한 페이지일 경우 self.cmt_done = True 설정

        # 댓글 = 0 인 경우  1. 댓글이 애초에 없는 경우 2. 댓글이 있다가 삭제된 경우

        # 댓글이 없으면 다음 게시글로 돌아간다 : return
        if msg['num_comments'] == 0:
            self.cmt_done = True
            return
        msg['comment_list'] = []
        # 댓글 >= 1 인 경우
        e = self.get_by_xpath('//div[@class="cmt_list"]')
        # 첫번째 댓글과 나머지 댓글의 클래스가 다르므로 다음과 같은 연산자를 사용하여 추출
        comments = e.find_elements_by_xpath('.//dl[@class="cmt_item f_line  "] | .//dl[@class="cmt_item  "]')
        parent_comment_id = ''

        # 네이트판의 댓글 한 페이지 = 20개 댓글
        for i, cmt_e in enumerate(comments):  # 확보된 댓글 리스트를 하나씩 처리하기
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            cmt = {
                'comment_id': None,
                'is_reply': False,
                'parent_comment_id': None,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': []
            }

            try:
                comment = cmt_e.find_element_by_xpath('.//dd[@class="usertxt"]').text.strip()
            except:
                comment = cmt_e.find_element_by_xpath('.//dt[@class="del"]').text.strip()
                cmt['contents'] = '삭제된 댓글입니다.'
                # cmt['comment_id'] = 'id 삭제됨'
                # cmt['nickname'] = 'nickname 삭제됨'
                cmt['create_ts'] = None
                cmt['like'] = 0
                cmt['dislike'] = 0
                # cmt['sensibility_num'] = '삭제됨'
            else:
                self.move_to_element(e)
                cmt['contents'] = comment  # 댓글 내용
                cmt['comment_id'] = cmt_e.get_attribute('id').split('_')[-1] # 숫자만 추출
                cmt['nickname'] = cmt_e.find_element_by_xpath('.//dt/span[@class="nameui"]').text.strip()  # 댓글 작성자(닉네임)
                e = cmt_e.find_element_by_xpath('.//i')
                cmt['create_ts'] = e.text.strip() + ':00'
                cmt['like'] = int(cmt_e.find_element_by_xpath('.//dd[@class="n_good"]').text.strip())  # 댓글 좋아요 갯수
                cmt['dislike'] = int(cmt_e.find_element_by_xpath('.//dd[@class="n_bad"]').text.strip())  # 댓글 싫어요 갯수
                # cmt['sensibility_num'] = str(int(cmt['like']) + int(cmt['dislike']))  # 댓글 감성수

                # 댓글 스티커 or 이미지
                # 문제점 : 한번에 이미지를 찾지 못해 두 개를 찾은 후 뒤의 이미지를 처리하는 방식 취함
                # 대책안 : 채문창님께 의뢰
                cmt['comment_img'] = []
                cmt['comment_img_url'] = []
                try:
                    sub_cmt_e = cmt_e.find_elements_by_tag_name('img')
                    # img_s = cmt_e.find_element_by_xpath('.//dd[@class="usertxt"]/span[@class="img"]')
                except:
                    # cmt['imagefile_list'] = []
                    ...
                else:
                    # 채문창 변경
                    if len(sub_cmt_e) >= 2:
                        for k, img_e in enumerate(sub_cmt_e[1:]):
                            image_url = img_e.get_attribute('src')
                            cmt['comment_img_url'].append(image_url)
                            cmt['comment_img'].append(cmt['comment_id']+'_'+str(k)+'.png')
                            # img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'], f'comment_{cmt["comment_id"]}.png')
                            # urlretrieve(cmt['emoticon_url'], img_f)
                            # imagefile = self.get_safe_path('crawling', msg['article_id'], f'comment_{cmt["comment_id"]}.png')
                            # cmt['imagefile_list'].append(imagefile)

            finally:
                # 부모 아이디 저장
                parent_comment_id = cmt['comment_id']
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   \t 댓글 [{i + 1 + biasNum}/{self.num_comments}] {cmt["comment_id"]} ')

            # 답글이 삭제되어도 대댓글은 존재 가능
            # 네이트판의 대댓글(답글) 한 페이지 = 5개 대댓글(답글)
            # 네이트판의 대댓글(답글)은 댓글의 하부 계층으로 들어가 숨겨져 있음
            # 대댓글 추출은 숨겨진 대댓글(답글) 버턴을 클릭하여 대댓글 페이지 노출후 가능
            reples_area = cmt_e.find_element_by_xpath('.//dd[@class="reples"]').text
            reples_total = reples_num = int(re.sub(r'[^0-9]', '', reples_area))
            msg['num_comments'] += reples_num

            if reples_num == 0:  # 대댓글이 없으므로 다음 댓글 처리로 이동
                continue

            try:  # 숨겨진 대댓글을 클릭하여 노출시킴
                cmt_e.find_element_by_xpath('.//dd[@class="reples"]/a[@class="cmtsum hide"]').click()
                self.implicitly_wait()
                # reples = cmt_e.find_elements_by_xpath('.//dl[@class="re-cmt f_line"]/dd[@class="usertxt"]')
            except:
                continue

            # 대댓글을 읽어서 저장
            self.reply_done = False
            # cmt['reples_count'] = 0
            # cmt['is_reply'] = {}
            # while not self.reply_done:
            #     added_replies = ''
            #     reples = cmt_e.find_elements_by_xpath('.//dl[@class="re-cmt f_line"]/dd[@class="usertxt"]')
            #     for reple in reples:
            #         cmt['is_reply'][cmt['reples_count']] = reple.text.strip()
            #         cmt['parent_comment_id'] = cmt['comment_id']
            #         cmt['reples_count'] += 1
            #         # 디버깅용
            #         self.logger.info(f'  \t\t대댓글 [{cmt["reples_count"]}/{cmt["reples_total"]}] {reple.text.strip()}')
            #
            #     if self.reply_done | (cmt['reples_total'] <= 5):
            #         break
            #     else:
            #         self.next_reply()

            # 채문창 : 다음 페이지네이션 대댓글 가져오기
            reply_list = list()
            while not self.reply_done:
                for r_e in cmt_e.find_elements_by_xpath(
                        './/dd[@class="reples"]/div[@class="hiddenreple"]/ul/li'):
                    self.move_to_element(r_e)
                    try:
                        reply = {
                            'comment_id': None,
                            'is_reply': True,
                            'parent_comment_id': parent_comment_id,
                            'create_ts': None,
                            'nickname': None,
                            'contents': None,
                            'like': None,
                            'dislike': None,
                            'comment_img': [],
                            'comment_img_url': [],
                        }
                        # 대댓글 작성자
                        e = r_e.find_element_by_xpath('.//dt[@class="user"]/span')
                        reply['nickname'] = e.text.strip()
                        # 대댓글 작성일시
                        e = r_e.find_element_by_xpath('.//dt[@class="user"]/i')
                        reply['create_ts'] = e.text.strip() + ':00'
                        # 대댓글 좋아요 개수
                        e = r_e.find_element_by_xpath('.//dd[@class="n_good"]')
                        reply['like'] = int(e.text.strip().replace(',', ''))
                        # 대댓글 싫어요 개수
                        e = r_e.find_element_by_xpath('.//dd[@class="n_bad"]')
                        reply['dislike'] = int(e.text.strip().replace(',', ''))
                        # 대댓글 내용
                        e = r_e.find_element_by_xpath('.//dd[@class="usertxt"]')
                        reply['contents'] = e.text.strip()

                        for ks,img_e in enumerate(r_e.find_elements_by_xpath('.//img')):
                            reply['comment_img_url'].append(img_e.get_attribute('src'))
                            reply['comment_img'].append(cmt['comment_id'] + '_' + str(ks) + '.png')

                        reply_list.append(reply)
                        msg['comment_list'].append(reply)
                        self.logger.info(f'  \t\t대댓글 [{len(reply_list)}/{reples_total}]')
                    except Exception as err:
                        ...
                try:
                    is_next = False
                    is_current = False
                    for pg_e in cmt_e.find_elements_by_xpath('.//span[@class="paging"]/a'):
                        if pg_e.get_attribute('class') == 'current':
                            is_current = True
                            continue
                        # get the next page link
                        if is_current:
                            self.safe_click(pg_e)
                            self.implicitly_wait(after_wait=1)
                            is_next = True
                            break
                    if not is_next:
                        self.reply_done = True
                except Exception as err:
                    self.reply_done = True

            if len(reply_list) != reples_total:
                self.logger.info(f'   *** ERROR : 대댓글 일부가 처리되지 못했음 ***  ')

            # 노출된 대댓글을 클릭하여 숨김
            # try:
            #     cmt_e.find_element_by_xpath('//dd[@class="reples"]/a[@class="cmtsum show"]').click()
            #     self.implicitly_wait()
            # except:
            #     self.logger.info(f'   : *** ERROR *** 답글이 닫히지 않음')
            #     continue

    # ==========================================================================
    def next_reply(self):

        # 역할
        # 1. 대댓글 페이지를 넘기는 기능과
        # 2. 더 이상 페이지가 없는 경우 대댓글이 없음을 알려주는 기능 수행 self.reply_done = true
        # 참고 : 채문창님의 코드 인용하여 적용
        try:
            reple_pages = self.get_by_xpath('//div[@class="paginator_s"]/span[@class="paging"]')
        except:
            self.reply_done = True
            return

        is_current = False
        for reple_page in reple_pages.find_elements_by_xpath('.//a'):
            if reple_page.get_attribute('class') == 'current':
                is_current = True
                continue
            if is_current:
                self.safe_click(reple_page)
                self.implicitly_wait()
                return
        self.reply_done = True
        return

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="view-wrap"]').screenshot(f)

    # ==========================================================================
    def get_article(self, title_e, msg, ndx, title):
        self.safe_click(title_e)
        # self.implicitly_wait() # 키워드= '배민 ' 으로 시험했을 경우 연결 문제 발생하여 시간 늘리면 문제 사라짐
        self.implicitly_wait(after_wait=2)  # 키워드= '배민 ' 으로 시험했을 경우 간혹 연결 문제 발생하여 시간 늘리면 문제 사라짐

        # 본문 내용에 타 사이트의 링크 정보를 통해 많은 이미지를 가져오는 경우 이미지 로딩 시간이 길어져서 추출에 어려움이 있는데
        # 이를 어떻게 해결해야 할까?
        # 대표 검색어 사례 : 퇴원한 전광훈 목사의 첫 말은?

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{title}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 게시판 이름 & 카테고리 , 채널명
            e = self.get_by_xpath('//span[@class="location"]')
            msg['board_name'] = (e.text.strip().split(' '))[-1]
            # msg['board_name'] = (e.text.strip().split(' '))[0]
            # msg['channel_name'] = (e.text.strip().split(' '))[-1]
            # msg['category'] = (e.text.replace(msg['board_name'], '')).replace(msg['channel_name'], '')

            # 게시글 제목
            e = self.get_by_xpath('//div[@class="view-wrap"]/div[1]/h1')
            msg['title'] = e.text.strip()

            # 작성자 / 작성일시 / 조회수
            # 톡톡과 팬톡의 코딩이 다름
            e = self.get_by_xpath('//div[@class="info"]\
                                  | //div[@class="info fan_pro"]')
            myWords = e.text.split()
            msg['author'] = myWords[0]  # 작성자(닉네임)
            msg['create_ts'] = myWords[1] + " " + myWords[2] + ':00'  # 작성일시
            msg['view_count'] = int(myWords[-1].replace('조회', '').replace(',', ''))  # 조회수 ('조회'라는 단어 제거)

            e = self.get_by_xpath('//div[@class="btnbox up"]/span[@class="count"]')
            msg['like'] = int(e.text.strip())  # 추천수
            e = self.get_by_xpath('//div[@class="btnbox down"]/span[@class="count"]')
            msg['dislike'] = int(e.text.strip())  # 반대수
            # msg['sensibility_num'] = str(int(msg['like']) + int(msg['dislike'])) # 감성수

            # 내용 : 비어 있는 경우도 있음 (사진만)
            try:
                e = self.get_by_xpath('//div[@id="contentArea"]')
                msg['contents'] = e.text.strip()
            except:
                msg['contents'] = ''

            # 이미지 주소 가져오기
            try:
                img_s = e.find_elements_by_tag_name('img')
            except:
                pass
            else:
                for j, img in enumerate(img_s):
                    msg['image_url_list'].append(img.get_attribute('src'))

            # 주의 : 게시글 리스트의 글제목 옆에 표시된 댓글 수와 게시글 본문 하단의 댓글 수가 다르다.
            # 이유 : 코드상에서 반영을 실시간으로 하지 못하는 것으로 추정
            # 선택 : 정확한 댓글 수는 게시글 본문 하단에 표시되는 정보를 사용
            # 댓글수
            e = self.get_by_xpath('//span[@class="num"]')
            msg['num_comments'] = self.num_comments = int(e.text.split('개')[0])

            # # 링크 주소 가져오기
            # msg['link_list'] = []
            # try:
            #     sub_e = e.find_elements_by_xpath('//p/span/a[@href]')
            # except:
            #     pass
            # else:
            #     for link in sub_e:
            #         msg['link_list'].append(link.get_attribute('href'))

            # 네이트는 댓글밑에 또다른 클래스로 처리된 대댓글(답글)이 존재
            # 즉 계층적 구조로 댓글과 대댓글이 존재,
            # 그런데 대댓글의 대대댓글은 대댓글과 같은 계위로 존재

            # 댓글 페이지 처리 루틴
            self.cmt_done = False
            cmtPageUnit = 0
            while not self.cmt_done:
                self.get_cmt(msg, cmtPageUnit)
                if self.cmt_done:
                    break
                self.next_cmt()
                if(self.cmt_done == False):
                    cmtPageUnit += 20

            # 화면 캡쳐 (중요: 아직 미해결)
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot(msg_capture_f)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # 이전 페이지로 돌아가기 위해서 들어간 횟수만큼 돌아가야 함
            if (cmtPageUnit == 0):
                self.driver.back()
            else:
                driverBackNum = (cmtPageUnit/20) + 2
                while True:
                    driverBackNum -= 1
                    self.driver.back()
                    if driverBackNum == 0:
                        return

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21 21:48'
            create_ts = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because article create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[3]/ul')
            bil = [bi for bi in e.find_elements_by_xpath('./li')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            # for bi in bil:
            for i in range(len(bil)):
                msg = {
                    'page': self.cur_page,
                    'row': i + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    # 'site_board': self.config['params']['site']['site_board'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'article_id': None,
                    'create_ts': None,
                    'board_name': None,
                    'title': None,
                    'contents': None,
                    'author': None,
                    'view_count': None,
                    'good': None,
                    'great': None,
                    'sad': None,
                    'angry': None,
                    'news': None,
                    'like': None,
                    'dislike': None,
                    'star_like': None,
                    'num_comments': None,
                    'article_url': None,
                    'image_list': [],
                    'image_url_list': [],
                    'attachment_name': [],
                    'attachment_url': [],
                    'comment_list': [
                        {
                            'comment_id': None,
                            'is_reply': None,
                            'parent_comment_id': None,
                            'create_ts': None,
                            'nickname': None,
                            'contents': None,
                            'like': None,
                            'dislike': None,
                            'comment_img': [],
                            'comment_img_url': [],
                        }
                    ],
                }
                try:
                    e = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[3]/ul')
                    ail = [bi for bi in e.find_elements_by_xpath('./li')]
                    bi = ail[i]

                    # 1) 게시글id : article_id (네이트판 톡톡의 게시글은 href링크에서 추출)
                    se = bi.find_element_by_xpath('.//a[@href]')
                    url_split = se.get_attribute('href').split('/')
                    msg['article_id'] = '_'.join(url_split[-2:])
                    msg['article_url'] = se.get_attribute('href')

                    # 2) 제목: title
                    title_e = se = bi.find_element_by_xpath('.//*[@class="subject"]')
                    title = se.get_attribute('title').strip()

                    # 3) 작성일시: '21.11.30 23:19' => '2021.11.30 23:19' 표시 변환시킴
                    # se = bi.find_element_by_xpath('.//span[@class="date"]')
                    # msg['create_date'] = "20" + se.text.strip()

                    # # 4) 작성자:  네이트판에는 작성자가 보이지 않고 닉네임만 보임
                    # msg['author'] = ''

                    self.get_article(title_e, msg, i+1, title)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True
                    break
                self.save_image(msg)
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    self.save_article(msg)

                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = msg['create_ts']

                if len(self.output['article_list']) >= \
                        self.config['params']['site']['max_articles'] > 0:
                    self.is_done = True
                    break

        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
            raise
        finally:
            time.sleep(0.1)

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="paginate"]')

            # 다음 페이지로 넘기기 위해 사용하는 플래그
            is_current = False

            # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
            # 따라서 두 가지 종류의 태그를 모두 구해야 함
            # 현재의 게시글이 포함된 페이지는 class가 current이다.
            # 따라서 다음 페이지를 클릭하기 위해 is_current 플래그를 True로 전환하고
            # for 문을 통해 다음 페이지 정보를 추출후
            # 두번 째 if 문에서 클릭을 통해 다음 페이지로 넘어간다.
            for pa in ple.find_elements_by_xpath('.//a | .//strong'):
                if pa.get_attribute('class') == 'current':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            raise
        finally:
            pass

    # ==========================================================================
    def make_tgz(self):
        src_d = self.config['target']['folder']
        tgz_f = self.config['target']['folder'] + '.tgz'
        with tarfile.open(tgz_f, "w:gz") as tar:
            tar.add(src_d, arcname=os.path.basename(src_d))

    # ==========================================================================
    def save_d(self, fn, d):
        fn += '.yaml' if self.config['target']['is_yaml'] else '.json'
        with open(fn, 'w', encoding='utf-8') as ofp:
            if self.config['target']['is_yaml']:
                yaml.dump(d, ofp, allow_unicode=True)
            else:
                ofp.write(json.dumps(d, ensure_ascii=False))

        # ==========================================================================

    def save_image(self, article):
        # 게시글 이미지
        for j, sub_e_url in enumerate(article['image_url_list']):
            try:
                article_img_p = self.get_safe_path(
                    self.config['target']['folder'],
                    article['article_id'],
                    f'{j}.png'
                )
                # 가끔 에러 나는 경우가 있슴
                for count in range(10):
                    try:
                        urllib.request.urlretrieve(sub_e_url, article_img_p)
                        article['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

        # 댓글 이미지
        for cmt in article['comment_list']:
            if not ('comment_img' in cmt and cmt['comment_img']):
                continue
            for k, cmt_url in enumerate(cmt['comment_img_url']):
                try:
                    cmt_img_f = self.get_safe_path(
                        self.config['target']['folder'],
                        article['article_id'],
                        f'{cmt["comment_id"] + "_" + str(k)}.png'
                    )
                    urllib.request.urlretrieve(cmt_url, cmt_img_f)
                except Exception as err:
                    self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img_url"]}: {str(err)}')

    # ==========================================================================
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )
        self.save_d(at_js_f, article)

    # ==========================================================================
    def save(self):
        myLen = len(self.output['article_list'])  # 디버깅
        self.output['num_articles'] = len(self.output['article_list'])
        if self.config['target']['is_separate_article']:
            del self.output['article_list']
        js_f = self.get_safe_path(
            self.config['target']['folder'],
            f'{self.output["start_ts"]}'
        )
        self.save_d(js_f, self.output)
        if self.config['target']['is_tar_gz']:
            self.make_tgz()

    # ==========================================================================
    def clean(self):
        for path in Path(self.config['target']['folder']).rglob('*.*'):
            cts_ut = os.path.getctime(str(path))
            cts = datetime.datetime.fromtimestamp(cts_ut)
            diff_t = datetime.datetime.now() - cts
            if diff_t.days >= self.config['target']['keep_day']:
                os.remove(str(path))

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            # self.login()
            # if self.config['params']['site']['get_cafe_info']:
            #     self.get_cafe_info()
            self.search()

            # 네이트판의 검색 결과는 톡톡과 팬톡으로 나뉘어져 새로운 페이지에 나타남
            # 어떻게 처리를 해야 할까?
            # yaml에서 선택하게 할까?

            # 검색 결과를 먼저 검토하여 다음 단계로 넘어간다.
            tt = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[3]/div/span')
            ttalk_count = re.sub(r'[^0-9]', '', tt.text)

            ft = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[4]/div/span')
            ftalk_count = re.sub(r'[^0-9]', '', ft.text)

            # 톡톡 리스트를 수집
            if ttalk_count != '0':
                e = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[1]/ul/li[2]/a/span',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

                # 정확도순에서 최신순으로 다시 정렬하기 위해 클릭
                e = self.get_by_xpath('/html/body/div[2]/div[2]/div[2]/div[1]/div[3]/div/a[2]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

                # 팬톡에서 설정된 값을 다시 False로 설정해 주어야 실행가능
                self.is_done = False
                while not self.is_done:
                    self.get_page()
                    if self.is_done:
                        break
                    self.next_page()

            # 팬톡 게시글 리스트를 수집
            # if(ftalk_count != '0'):
            #     e = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[1]/ul/li[3]/a/span',
            #                           cond='element_to_be_clickable')
            #     self.safe_click(e)
            #     self.implicitly_wait(after_wait=1)
            #
            #     while not self.is_done:
            #         self.get_page()
            #         if self.is_done:
            #             break
            #         self.next_page()
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 1
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    try:
        with PannSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'natepann.yaml'
    do_start(config_f=_config_f)
