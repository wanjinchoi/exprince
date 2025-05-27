"""
====================================
 :mod:`chosun`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for chosun (조선일보)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#  * [2023/06/09]
#     - 동영상 광고 스킵
#  * [2023/06/02]
#     - 검색 전 스크린샷 추가
#  * [2023/04/18]
#     - 스크린샷에 댓글 부분 포함
#  * [2023/03/30]
#     - 작성일 포멧 변경으로 인한 모듈 수정
#  * [2023/01/30]
#     - 댓글 xpath 변경
#  * [2022/07/22]
#     - 작성자 xpath 추가
#  * [2022/02/16]
#     - 1차 버전 완료

import os
import re
import sys
import yaml
import json
import time
import pickle
import shutil
import random
import tarfile
import datetime
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################
class ChosunSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'ChosunSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        # 특정 키워드는 키워드의 성격을 바꿔줌
        if self.search_index == 0:
            n_user_type = len(self.config['params']['site']['user_type'].split(','))
            n_search = len(self.config['params']['site']['search'].split(','))
            n_search_type = len(self.config['params']['site']['search_type'].split(','))
            n_service = len(self.config['params']['site']['service'].split(','))
            if n_user_type != n_search_type or n_search != n_service or n_user_type != n_search:
                err_msg = 'the length of list of user_type, search, search_type, service is different'
                # print(err_msg)
                self.logger.error(err_msg)
                raise ValueError(err_msg)
        self.config['params']['site']['user_type'] = self.config['params']['site']['user_type'].split(',')[i]
        self.config['params']['site']['search_type'] = self.config['params']['site']['search_type'].split(',')[i]
        self.config['params']['site']['service'] = self.config['params']['site']['service'].split(',')[i]
        self.config['params']['site']['search'] = keyword

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
        out_config = deepcopy(self.config)
        del out_config['params']['site']['passwd']
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
        self.logger.info(f'Starting Chosun Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        # 로그인 창 클릭
        e = self.get_by_xpath('(//div[@class="nav__bar-icon |"]/div/a)[1]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # ID
        e = self.get_by_xpath('//input[@id="username"]')
        self.send_keys(e, self.config['params']['site']['userid'])
        self.implicitly_wait(after_wait=1)
        # PW
        e = self.get_by_xpath('//input[@id="subsPassword"]')
        self.send_keys(e, self.config['params']['site']['passwd'])
        self.implicitly_wait(after_wait=1)

        # 로그인 버튼 클릭
        e = self.get_by_xpath('//button[@id="subsSignIn"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 로그인 쿠키를 담아둠
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))

    # ==========================================================================
    def search(self):
        # 게시글 목록 스크린샷
        self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
        s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
        s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
        self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
        # # 검색 카테고리 '사회'면 선택하기
        # e = self.get_by_xpath('//*[@id="nav"]/div[2]/div[2]/div[7]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

        # 검색란 보이기
        e = self.get_by_xpath('//*[@id="nav-bar-left"]/div[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 검색어 입력 및 리턴키
        e = self.get_by_xpath('//*[@id="nav-bar-left"]/div[2]/form/div/input')
        search_key = self.config['params']['site']['search']
        self.send_keys(e, search_key + Keys.RETURN)
        self.implicitly_wait(after_wait=3)

        search_result = self.get_by_xpath('//*[@id="main"]/div[1]/div[1]/div[1]')
        search_result_num = search_result.text.strip().split('\n')[2].replace('건', '')
        self.logger.info(f" >>>>> 검색 단어: {self.config['params']['site']['search']} || 검색 결과 갯수: {search_result_num}")
        if search_result_num == '0':
            return

    # ==========================================================================
    def get_cmt_reply(self, msg):

        e = self.get_by_xpath('//div[@class="comment-feed | box--position-relative"]')
        mixed_cmts = e.find_elements_by_xpath('./div')

        self.move_to_element(e)
        # 댓글이 없으면 다음 게시글로 돌아간다
        if len(mixed_cmts) == 2:  # 댓글 내용이 없으면 2개의 div 존재함
            msg['num_comments'] = 0
            self.cmt_done = True
            return
        msg['comment_list'] = []
        # 댓글 '항목' 펼치기
        while True:
            try:
                e = self.get_by_xpath('//div[@class="comment-feed | box--position-relative"]')
                more_cmt = e.find_element_by_xpath('./button[@id="comment-more-id"]')
            except:
                break
            else:
                self.safe_click(more_cmt)
                self.implicitly_wait(after_wait=1)

        # 댓글을 다 펼친 후 직접 갯수를 셈 (표시되는 댓글 갯수 정보가 정확하지 않은 경우 대비)
        cmt_list = e.find_elements_by_xpath('./div')
        del(cmt_list[0:3])  # 댓글 헤드에 속하는 div 3개 제거
        msg['num_comments'] = len(cmt_list)

        # 댓글 처리
        for i, cmt_e in enumerate(cmt_list): # 확보된 댓글 리스트를 하나씩 처리하기

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
                'comment_img_url': [],
            }
            try:
                div_3e = cmt_e.find_elements_by_xpath('./div/div/div')
                inner_html = cmt_e.get_attribute('innerHTML')   # 이미지 추출용
            except:
                pass
            else:
                self.move_to_element(cmt_e)

                # 댓글 작성자와 작성 일시, cmd id
                nickname, create_ts = div_3e[0].text.strip().split('\n')
                cmt['nickname'] = nickname
                cmt['create_ts'] = create_ts
                cmt_href = div_3e[0].find_element_by_tag_name('a').get_attribute('href')
                cmt['comment_id'] = re.search('uuid=(.+?)$', cmt_href).group(1)
                parent_comment_id = cmt['comment_id']

                # 댓글 내용
                cmt['contents'] = div_3e[1].text.strip()

                # 답글(대댓글) 여부와 댓글에 대한 반응
                if len(div_3e) == 2:  # 관리자가 댓글을 삭제한 경우
                    cmt['like'] = 0
                    cmt['dislike'] = 0
                elif div_3e[2].text.find('답글작성') >= 0:
                    reply_status, up_count, down_count = div_3e[2].text.strip().split('\n')
                    cmt['like'] = int(up_count)
                    cmt['dislike'] = int(down_count)
                else:
                    reply_status, reply_num, up_count, down_count = div_3e[2].text.strip().split('\n')
                    cmt['like'] = int(up_count)
                    cmt['dislike'] = int(down_count)

                self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{i+1}]')

            # 답글 여부 확인
            if reply_status == '답글작성':  # 답글(대댓글)이 없는 경우
                msg['comment_list'].append(cmt)
                continue
            else:  # 답글(대댓글)이 있는 경우
                # 답글(대댓글) 펼치기 작업 필요
                # 답글(대댓글) 1차 펼치기 (시작은 5개 펼쳐짐)
                button = div_3e[2].find_element_by_tag_name('button')
                self.safe_click(button)
                self.implicitly_wait(after_wait=1)
                # 답글(대댓글) 추가 펼치기 (답글(대댓글) 5개를 초과하는 경우 즉 6개 이상)
                while True:
                    try:
                        reply_part = cmt_e.find_element_by_xpath('./div/div[2]')
                        reply_more = reply_part.find_element_by_tag_name('button')
                    except:
                        break
                    else:  # 답글이 10개씩 펼쳐짐
                        self.safe_click(reply_more)
                        self.implicitly_wait(after_wait=1)

                # 펼쳐진 답글(대댓글) 처리
                # 답글(대댓글)이 플랫 구조임
                reply_list = cmt_e.find_elements_by_xpath('./div/div[2]/div')
                del (reply_list[0])  # 로그인 박스 제거
                reply_length = len(reply_list)
                for j, reply_e in enumerate(reply_list):
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
                    try:
                        div_2e = reply_e.find_elements_by_xpath('./div/div')
                    except:
                        pass
                    else:
                        self.move_to_element(reply_e)

                        # 답글(대댓글) 작성자와 작성 일시
                        nickname, create_ts = div_2e[0].text.strip().split('\n')
                        reply['nickname'] = nickname
                        reply['create_ts'] = create_ts
                        reply_href = div_2e[0].find_element_by_tag_name('a').get_attribute('href')
                        reply['comment_id'] = re.search('uuid=(.+?)$', reply_href).group(1)

                        # 답글(대댓글) 내용
                        reply['contents'] = div_2e[1].text.strip()

                    self.logger.info(
                            f'\t\t   대댓글(답글) [{reply_length}/{j+1}] ')
                    # 답글(대댓글) 목록에 추가
                    msg['comment_list'].append(reply)
                msg['comment_list'].append(cmt)
        self.cmt_done = True
        return

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.implicitly_wait(after_wait=1)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        # 페이지 오류 발생 처리
        urling = self.driver.current_url
        if urling != msg['article_url']:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            return

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 게시글 제목
            if msg['title'] == '':
                title = self.get_by_xpath('//*[@id="fusion-app"]/div[1]/div[2]/div/div/div[3]/h1')
                msg['title'] = title.text.strip()
            e = self.get_by_xpath('//*[@id="fusion-app"]/div[1]/div[2]/div/section/article')

            # 등록일
            se = e.find_element_by_xpath('//*[@id="fusion-app"]/div[1]/div[2]/div/section/article/div[2]/span')
            a = se.text.partition(' ')[2].rpartition('수정 ')[2].partition(' ')[0]
            if a.count('.') == 3:
                create_t = a.rpartition('.')[0]
            else:
                create_t = a
            msg['create_ts'] = create_t + ' ' + se.text.partition(' ')[2].rpartition('수정 ')[2].partition(' ')[2] + ":00"

            # 게시글 id (게시글 id가 없어서 임의로 생성함)
            # msg['article_id'] = create_ts.replace('.', '').replace(' ', '').replace(':', '') + str(ndx)

            # 작성자(기자)
            se = e.find_element_by_xpath('//*[@id="fusion-app"]/div[1]/div[2]/div/section/article/div[1]/div/span | //*[@id="fusion-app"]/div[1]/div[2]/div/section/article/div[1]/div/a')
            msg['author'] = se.text.strip()

            # 내용
            try:
                contents = e.find_element_by_xpath('.//section[@class="article-body"]')
                msg['contents'] = contents.text
            except:
                msg['contents'] = ''

            # 본문 안의 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = contents.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = contents.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_e_url = img.get_attribute('src')
                    if not img_e_url:
                        pass
                    else:
                        msg['image_url_list'].append(img_e_url)
                        msg['image_list'].append(f'{x}.png')

            # 댓글 저장
            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt_reply(msg)
                if self.cmt_done:
                    break
            self.driver.switch_to.default_content()  # iframe 다시 전환
            self.driver.execute_script("window.scrollTo(0, 0)")
            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_element_by_xpath('//nav[@id="nav"]')
                    self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_heads)
                    self.full_screenshot(msg_capture_f)
        except Exception as err:
            raise
        finally:
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21 21:48:00'
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
    def stop_article_older_than_date(self, date):
        try:
            # '2021.12.21'
            create_ts = datetime.datetime.strptime(date, '%Y.%m.%d').date()
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            ).date()
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because article create_date "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//div[@class="search-feed"]')
            bil = [bi for bi in e.find_elements_by_xpath('./div')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
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
                    # 검색 결과물 페이지의 목록(List) 읽기
                    e = self.get_by_xpath('//div[@class="search-feed"]', timeout=5, wait_until_valid_text=True)
                    ail = [bi for bi in e.find_elements_by_xpath('./div')]
                    bi = ail[i]
                    self.move_to_element(bi)

                    # 게시글 제목
                    # try:
                    #     title = bi.find_element_by_xpath('.//a[@class="text__link story-card__headline | box--margin-none text--black font--primary h3 text--left"]')
                    # except:
                    #     msg['title'] = ''
                    # else:
                    #     if title.text.strip() == '':
                    #         msg['title'] = ''
                    #         pass
                    #     else:
                    #         msg['title'] = title.text.strip()
                    #         self.logger.info(f'>>>>> Page[{self.cur_page}:{i+1}] : {msg["title"]}')
                    title = bi.find_element_by_xpath('.//a[@class="text__link story-card__headline | box--margin-none text--black font--primary h3 text--left"]')
                    msg['title'] = title.text.strip()

                    # 게시글 URL
                    article_url = title.get_attribute('href')
                    msg['article_url'] = article_url
                    msg['article_id'] = article_url.split('/')[-2]
                    # 게시글 카테고리 # 조선일보는 검색이 사회면 기사만을 골라내지 못하므로 검색 결과에서 사회면을 찾아 기사로 넘어감
                    e = bi.find_element_by_xpath('.//span/span[@class="hover-underline | box--pointer"]')
                    msg['board_name'] = e.text.strip()
                    date_e = bi.find_element_by_xpath('.//span/span[@class="hover-underline | box--pointer"]/../..')
                    date_a = date_e.text.rpartition('| ')[2]
                    # 게시글 목록에서 날Wk만보고 파악.
                    if self.stop_article_older_than_date(date_a):
                        self.is_done = True
                        break
                    if not msg['board_name'].startswith('사회'):
                        # self.logger.info(f'Page[{self.cur_page}:{i+1}], title="{msg["title"]}"')
                        self.logger.info(f'Page[{self.cur_page}:{i+1}], The category of this post is not society.'
                                         f' {msg["board_name"]}')
                        continue
                    else:
                        self.logger.info(f'***************************** {msg["board_name"]} ******************************')

                    # 게시글 본문으로 이동
                    se = bi.find_element_by_xpath('.//a[@href]')
                    title_e = se
                    self.move_to_element(se)
                    self.get_article(title_e, msg, i+1)
                    self.implicitly_wait(after_wait=1)
                except Exception as err:
                    if msg['article_id'] is None:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
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
            raise
        finally:
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="number"]')
            pa_list = ple.find_elements_by_tag_name('li')
            next_e = self.get_by_xpath('//div[@class="next"]')
            pa_list.append(next_e)

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'active':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=2)
                    try:
                        alert = self.driver.switch_to_alert()
                        message = alert.text
                    except:
                        self.implicitly_wait(after_wait=1)
                        return
                    else:
                        if '마지막 페이지 입니다.' in message:
                            alert.accept()
                            self.switch_to_window(self.driver.window_handles[0])
                            self.is_done = True
                            self.implicitly_wait(after_wait=1)
                            return
                        self.implicitly_wait(after_wait=1)
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
                        # article['image_list'].append(f'{j}.png') 왜 들어가 있는지를 이해 하지 못함
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
        # json 파일 생성
        self.save_d(at_js_f, article)

    # ==========================================================================
    def save(self):
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
    def a_cookie(self):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            if self.search_index == 0:
                self.login()
            else:
                self.a_cookie()
            self.search()

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.implicitly_wait(after_wait=1)  # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                self.next_page()
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with open(kwargs['config_f'], encoding='utf-8') as ifp:
        f_yaml = yaml.load(ifp, yaml.SafeLoader)
        for i, keyword in enumerate(f_yaml['params']['site']['search'].split(',')):
            with ChosunSearch(kwargs['config_f'], keyword, i) as ws:
                ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'chosun.yaml'
    do_start(config_f=_config_f)
