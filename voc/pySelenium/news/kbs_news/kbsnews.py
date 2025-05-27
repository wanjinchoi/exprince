"""
====================================
 :mod:`kbsnews`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for kbsnews (kbsnews)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/04/25]
#     - 댓글 영역이 존재하지 않는 게시글 존재하여 해당 부분 넘어가도록 로직 수정
#  * [2023/04/19]
#     - 게시글 내부에서 카테고리 비교하는 부분 주석 처리
#  * [2023/04/18]
#     - board_name에 값 입력
#  * [2023/03/28]
#     - 검색 필터의 xpath 변경
#  * [2023/02/20]
#     - 게시글 안에 사회 카테고리 비교하도록 로직 추가
#  * [2022/11/21]
#     - 검색어 입력 후, 자동으로 검색 필터 노출
#  * [2022/04/27]
#     - 댓글 작성시간 오류 해결. 다른 포맷도 일부 수정. headless false시 상단바 제거
#  * [2022/02/16]
#     - 1차 버전 완료

import os
import re
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
from alabslib.selenium import PySelenium, Keys


################################################################################
class KbsnewsSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'KbsnewsSearch.log'),
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
        out_config = deepcopy(self.config)
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
        self.logger.info(f'Starting Kbsnews Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_cmt(self, msg):

        try:
            e = self.get_by_xpath('//*[@id="msg"]/div')

            # 댓글은 iframe 내부에 존재
            # 커서를 옮겨 주어야 iframe 소스에 접근 가능
            self.move_to_element(e)
            iframe = e.find_element_by_tag_name('iframe')
            reply_url = iframe.get_attribute('src')

            # 댓글 처리용 별도탭 열기
            self.driver.execute_script('window.open("about:blank", "_blank");')
            self.implicitly_wait(after_wait=1)
            self.driver.switch_to_window(self.driver.window_handles[-1])

            # 별도의 웹주소로 이동(이동후에는 iframe이 없음)
            self.driver.get(reply_url)
            self.implicitly_wait(after_wait=1)

            # 댓글이 없으면 다음 게시글로 돌아간다
            e = self.get_by_xpath('//*[@id="wrapper"]/div[8]/div[1]/span')
            self.move_to_element(e)
            if e.text.strip() == '':
                msg['num_comments'] = 0
                self.cmt_done = True
                self.driver.close()
                return
            else:
                msg['num_comments'] = int(e.text.strip())

            # 댓글 '항목' 펼치기
            while True:
                e = self.get_by_xpath('//div[@id="list"]')
                try:
                    se = e.find_element_by_class_name('more-wrapper')
                    more_cmt = se.find_element_by_xpath('./button//span[@class="font-suny-red"]')
                except:
                    break
                else:
                    more_num = int(more_cmt.text.strip())
                    if more_num > 0:
                        self.safe_click(se)
                        self.implicitly_wait(after_wait=1)
                        self.move_to_element(e)

            msg['comment_list'] = []
            # 댓글 '내용' 펼치기
            # '댓글 펼쳐보기' 클릭을 해야 숨겨진 답글(대댓글)을 노출후 추출할 수 있음
            while True:
                try:
                    e = self.get_by_xpath('//div[@id="list"]')
                    se = e.find_elements_by_xpath('//div[@class="list-reduce-wrapper"]')
                except:
                    break
                else:
                    for content_skip in se:
                        attribute = content_skip.get_attribute('class')
                        self.move_to_element(e)
                        if attribute == 'list-reduce-wrapper':
                            button = content_skip.find_element_by_tag_name('button')
                            self.safe_click(button)
                            self.implicitly_wait(after_wait=1)
                            continue
                    break

            # 댓글 처리
            cur_num = 0
            cmt_list = e.find_elements_by_xpath('./div')
            for i, cmt_e in enumerate(cmt_list):  # 확보된 댓글 리스트를 하나씩 처리하기

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

                # 예외적 경우 처리
                try:
                    if cmt_e.get_attribute('class') == 'more-write-wrapper':
                        cnt_txt = cmt_e.text.strip()
                    elif cmt_e.get_attribute('class') == 'reply-wrapper':
                        cmt_part = cmt_e.find_element_by_xpath('.//div[@class="reply-content-wrapper"]')
                        cnt_txt = cmt_part.find_element_by_class_name('reply-content').text.strip()
                except:
                    pass
                else:
                    if '모든 댓글을 읽으셨습니다.' in cnt_txt:
                        break
                    elif '이 댓글은 작성자 또는 관리자에 의해 삭제된 댓글입니다.' in cnt_txt:
                        msg['num_comments'] += 1  # 시스로그 정보 표시를 위해 삭제된 댓글도 갯수에 포함시킴
                        cmt['contents'] = cmt_e.text.strip().split('\n')[1]
                        try:
                            reply_num_info = cmt_e.find_element_by_xpath('.//div[@class="reply-content-wrapper"]//span[2]')
                        except:
                            pass
                        else:
                            reply_count = reply_num_info.text.strip()
                            if reply_count == '':
                                continue

                try:
                    comment_id = cmt_e.find_element_by_class_name('writer')
                    writer_info = cmt_e.find_element_by_xpath('.//ul[@class="writer-account"]')
                    writer = writer_info.find_elements_by_xpath('./li')
                    create_ts_e = writer[3].find_element_by_class_name('modify-time')

                    cmt_part = cmt_e.find_element_by_xpath('.//div[@class="reply-content-wrapper"]')

                    contents = cmt_part.find_element_by_class_name('reply-content')
                    good_count = cmt_part.find_element_by_class_name('good-count')

                    inner_html = cmt_part.get_attribute('innerHTML') # 이미지 추출용
                except:
                    pass
                else:
                    # 댓글 작성자 정보
                    cmt['comment_id'] = comment_id.get_attribute('data-seq')
                    # cmt['id_from'] = writer[1].text.strip().split(' ')[0]
                    cmt['nickname'] = writer[2].text.strip()
                    create_ts = create_ts_e.get_attribute('title').replace('오후', 'pm').replace('오전', 'am')
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y년 %m월 %d일 %p %I:%M').strftime('%Y.%m.%d %H:%M:%S')

                    # 댓글 내용
                    cmt['contents'] = contents.text

                    # 댓글에 대한 반응
                    cmt['like'] = int(good_count.text.strip())

                    # 이미지 정보 추출
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    if inner_html.find('attached-image') > 0:
                        for j, sub_e in enumerate(cmt_part.find_elements_by_xpath('.//img[@class="attached-image"]')):
                            sub_e_url = sub_e.get_attribute('src')
                            cmt['comment_img_url'].append(sub_e_url)
                            cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                    cur_num += 1
                    self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{cur_num}] {cmt["contents"]} ')

                ####################
                # 대댓글(답글) 처리 호출 : get_cmt()에서 get_reply() 호출
                # 대댓글(답글)이 없다고 표시되지만 실제로는 대댓글(답글)이 존재하는 경우가 있음
                try:
                    reply_list = cmt_e.find_element_by_xpath('.//div[@class="child-reply"]')
                except:
                    continue
                else:
                    reply_list = reply_list.find_elements_by_xpath('./div')
                    if len(reply_list) == 0:
                        # 대댓글이 없는 경우
                        msg['comment_list'].append(cmt)
                    else:
                        # 대댓글이 있는 경우
                        # cmt['reply_list'] = list()
                        for x, reply_e in enumerate(reply_list): # 대댓글(답글) 리스트
                            cur_num = self.get_reply(msg, cmt, reply_e, cur_num)
                        msg['comment_list'].append(cmt)
            self.cmt_done = True
            self.driver.close()
            return
        except:
            self.cmt_done = True
            msg['num_comments'] = 0
            return

    # ==========================================================================
    def get_reply(self, msg, cmt, reply_part, cur_num):

        reply = {
            'comment_id': None,
            'is_reply': True,
            'parent_comment_id': cmt['comment_id'],
            'create_ts': None,
            'nickname': None,
            'contents': None,
            'like': None,
            'dislike': None,
            'comment_img': [],
            'comment_img_url': [],
        }

        # 먼저 지워진 대댓글(답글)인지 여부 확인
        try:
            reply_part_attr = reply_part.get_attribute('class')
        except:
            pass
        else:
            if reply_part_attr == 'reply-wrapper reply-delete-wrapper':
                # 지워진 대댓글(답글)
                msg['num_comments'] += 1  # 시스로그 정보 표시를 위해 삭제된 댓글도 갯수에 포함시킴
                reply['contents'] = reply_part.text.strip().split('\n')[1]

                cur_num += 1
                self.logger.info(
                    f'\t\t   대댓글(답글) [{msg["num_comments"]}/{cur_num}] {reply["contents"][:80]}')
                # cmt['reply_list'].append(reply)
                msg['comment_list'].append(reply)

        # 정상 대댓글(답글)
        try:
            reply_id = reply_part.find_element_by_class_name('writer')
            # 대댓글(답글) 역시 댓글의 작성자 및 글내용 구조가 동일하므로 같은 루틴 사용
            # 앞의 댓글에서 사용한 변수와 같은 이름을 사용함
            writer_info = reply_part.find_element_by_xpath('.//ul[@class="writer-account"]')
            writer = writer_info.find_elements_by_xpath('./li')
            create_ts_e = writer[3].find_element_by_class_name('modify-time')

            contents = reply_part.find_element_by_class_name('reply-content')
            good_count = reply_part.find_element_by_class_name('good-count')

            inner_html = reply_part.get_attribute('innerHTML')  # 이미지 추출용
        except:
            pass
        else:
            # 대댓글(답글) 작성자 정보
            reply['comment_id'] = reply_id.get_attribute('data-seq')
            # reply['id_from'] = writer[1].text.strip().split(' ')[0]
            reply['nickname'] = writer[2].text.strip()
            create_ts = create_ts_e.get_attribute('title').replace('오후', 'pm').replace('오전', 'am')
            reply['create_ts'] = datetime.datetime.strptime(create_ts, '%Y년 %m월 %d일 %p %I:%M').strftime('%Y.%m.%d %H:%M:%S')

            # 대댓글(답글) 내용
            reply['contents'] = contents.text

            # 대댓글(답글)에 대한 반응
            reply['like'] = int(good_count.text.strip())

            # 이미지 정보 추출
            if inner_html.find('attached-image') > 0:
                for j, sub_e in enumerate(reply_part.find_elements_by_xpath('.//img[@class="attached-image"]')):
                    sub_e_url = sub_e.get_attribute('src')
                    reply['comment_img_url'].append(sub_e_url)
                    reply['comment_img'].append(f'{reply["reply_id"] + "_0"}.png')

            cur_num += 1
            self.logger.info(
                f'\t\t   대댓글(답글) [{msg["num_comments"]}/{cur_num}] {reply["contents"][:80]}')
            # 대댓글(답글) 목록에 추가
            # cmt['reply_list'].append(reply)
            msg['comment_list'].append(reply)

        # 대댓글(답글)이 없다고 표시되지만 실제로는 지워진 대댓글(답글)이 존재하는 경우가 있음
        try:
            child_reply = reply_part.find_element_by_xpath('.//div[@class="child-reply"]')
        except:
            pass
        else:
            reply_list = child_reply.find_elements_by_xpath('./div')
            for x, reply_e in enumerate(reply_list):  # 대댓글 리스트
                cur_num = self.get_reply(msg, cmt, reply_e, cur_num)
        return cur_num

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        # 페이지 오류 발생 처리
        urling = self.driver.current_url
        urling = urling.replace('https://', 'http://')
        if urling != msg['article_url']:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            return

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], article_id[{msg["article_id"]}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 사회 카테고리 선택하여 조회하므로 해당 부분은 주석 처리
            # KBS 기사의 site_board 찾기 (현재 site_board 값 = 사회)
            # se = self.get_by_xpath('//div[@class="landing-box"]//span[@class="source"]//a')
            # category = se.text.strip()
            # msg['site_board'] = category
            # if category != self.config['params']['site']['site_board']:
            #     # 다음 항목은 디버깅용과 속도 문제로 인한 오류 발생을 방지하기 위함
            #     # 만약 제거한다면 time.sleep(1) 추가 필요
            #     self.logger.info(f'***** SKIPing {category} ..... Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            #     return

            e = self.get_by_xpath('//*[@id="content"]//div[@class="landing-box"]')
            # 등록일
            se = e.find_element_by_xpath('.//em[@class="date"]')
            if se.text.find('입력') >= 0:
                create_ts = se.text.partition('입력')[2].strip()
                msg['create_ts'] = create_ts.replace('(', '').replace(')', '') + ":" + "00"

            # 작성자(기자)
            se = e.find_element_by_xpath('.//ul[@class="list-reporter"]')
            if se.text.strip() == '':
                msg['author'] = ''  # 기자 정보가 없는 경우도 있음
            else:
                msg['author'] = se.text.strip().split()[0]

            # 내용
            try:
                contents = e.find_element_by_xpath('.//div[@id="cont_newstext"]')
                msg['contents'] = contents.text
            except:
                msg['contents'] = ''

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@id="header"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                    var element = arguments[0];
                                                    element.parentNode.removeChild(element);
                                                    """, e_head)
                    self.full_screenshot(msg_capture_f)

            # # 동영상 추출
            # msg['vod_url_list'] = []
            # msg['vod_list'] = []
            inner_html = e.get_attribute('innerHTML')  # 이미지 추출용
            # if inner_html.find('btnMainPlay') > 0:
            #     try:
            #         vod_button = e.find_element_by_id('btnMainPlay')
            #         self.safe_click(vod_button)
            #         self.implicitly_wait(after_wait=1)
            #         vod_info = e.find_element_by_xpath('//*[@id="JW_PLAYER"]//video[@class="jw-video jw-reset"]')
            #     except:
            #         pass
            #     else:
            #         msg['vod_url_list'].append(vod_info.get_attribute('src'))
            #         msg['vod_list'].append(f'{msg["title"]}.mpeg')

            # 본문 안의 이미지 주소 가져오기
            if inner_html.find("imgVodThumbnail") > 0:
                img_list = e.find_elements_by_xpath('.//img[@id="imgVodThumbnail"]|.//div'
                                                    '[@class="detail-body font-size"]/div[@class="view_img_wrap"]/img')
                for x, img in enumerate(img_list):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    msg['image_list'].append(f'{x}.png')

            # 기사 평가
            se = e.find_element_by_xpath('//span[@id="like_cnt_under"]')
            msg['like'] = int(se.text.strip())

            # 댓글
            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt(msg)
                if self.cmt_done:
                    break
        except Exception as err:
            raise
        finally:
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21. 21:48:00'
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

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//div[@class="newslist-grid4"]/ul')
            bil = [bi for bi in e.find_elements_by_xpath('./li')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            for i in range(len(bil)):
                msg = {
                    'page': self.cur_page,
                    'row': i + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    'site_board': self.config['params']['site']['site_board'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'article_id': None,
                    'create_ts': None,
                    'board_name': self.config['params']['site']['site_board'],
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
                    e = self.get_by_xpath('//div[@class="newslist-grid4"]/ul')
                    ail = [bi for bi in e.find_elements_by_xpath('./li')]
                    bi = ail[i]

                    # 게시글 제목
                    title = bi.find_element_by_xpath('.//em[@class="tit"]')
                    msg['title'] = title.text.strip()

                    # 게시글 URL
                    article_url = bi.find_element_by_tag_name('a').get_attribute('href')
                    msg['article_url'] = article_url

                    # 게시글 id
                    msg['article_id'] = re.search(r'view\.do\?ncd=(.+?)$', article_url).group(1)

                    # 게시글 본문으로 이동
                    se = bi.find_element_by_xpath('.//a[@href]')
                    title_e = se
                    self.move_to_element(se)
                    self.get_article(title_e, msg, i+1)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if msg['site_board'] == self.config['params']['site']['site_board']:
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
                else:
                    continue

        except Exception as err:
            raise
        finally:
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//ol[@id="paginglist"]')

            is_current = False
            for pa in ple.find_elements_by_tag_name('li'):
                if pa.get_attribute('class') == 'on':
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
        # vod 저장
        # crawling_dir = self.get_safe_path(self.config['target']['folder'], article['article_id'])
        # for x, download_file in enumerate(article['vod_list']):
        #     save_loc_fn = self.get_safe_path(crawling_dir, article['vod_list'][x])
        #     urllib.request.urlretrieve(article['vod_url_list'][x], save_loc_fn)

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
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])

            # 검색란 보이기
            e = self.get_by_xpath('//*[@id="header"]//a[@class="btn-search"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색어 입력
            e = self.get_by_xpath('//*[@id="header-search"]')
            # search_key = '\"' + self.config['params']['site']['search'] + '\"'
            search_key = self.config['params']['site']['search']
            self.send_keys(e, search_key)

            # 검색 단추
            e = self.get_by_xpath('//*[@id="header"]//button[@class="search-btn"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색 선택사양 보이기
            # e = self.get_by_xpath('//*[@id="btn-search-opt"]',
            #                       cond='element_to_be_clickable')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)

            # 제목+내용 선택하기
            e = self.get_by_xpath('//div[@class="detail-search-wrap"]/dl[2]//ul/li[2]//span',
                                      cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색 카테고리 선택하기
            #  - 먼저 전체선택 해제하기
            e = self.get_by_xpath('//*[@id="categoryfield"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            #  - '사회' 선택하기
            e = self.get_by_xpath('//div[@class="detail-search-wrap"]/dl[3]//ul/li[4]//span',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 최신순
            e = self.get_by_xpath('//li[@id="latest"]/button')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            search_result = self.get_by_xpath('//div[@class="section result"]/dl/dt/p/em')
            search_result_num = search_result.text.strip()
            self.logger.info(f" >>>>> 검색 단어: {self.config['params']['site']['search']} || 검색 결과 갯수: {search_result_num}")
            if search_result_num == '0':
                return

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
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
    with KbsnewsSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'kbsnews.yaml'
    do_start(config_f=_config_f)
