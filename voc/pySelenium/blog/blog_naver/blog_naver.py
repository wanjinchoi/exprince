"""
====================================
 :mod:`blog/blog_naver`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# * Kyobong An
#
# Change Log
# --------
#  * [2022/12/06]
#     - 비공개 게시글 회피 로직 수정
#     - 에러 로그에 해당 게시글의 url추가
#  * [2022/10/20]
#     - 윈도우 개수창 확인 로직 수정
#  * [2022/10/13]
#     - 윈도우 개수창 확인 로직 추가
#  * [2022/06/13]
#     - create_ts 시간 포맷 추가
#  * [2022/06/10]
#     - capture_delay 기능추가
#     - capture element 변경
#     - 이미지 가져올때 403에러 해결코드 __init__ 부분에 추가 함
#  * [2022/06/09]
#     - search_complex 추가
#  * [2022/05/02]
#     - 게시글 내에 site_name 블로그명으로 변경
#  * [2022/03/28]
#     - 비공개 글 회피 추가. 포커스 이동으로 추가함.
#  * [2022/03/22]
#     - 포맷적용
#  * [2022/01/07]
#     - starting
################################################################################
import os
import re
import sys
import yaml
import json
import time
import shutil
import random
import tarfile
import traceback
import datetime
import urllib.request
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, WebDriverWait


################################################################################

class NaverBlogSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverBlogsearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        if 'capture_delay' in self.config['params']['site']:
            self.capture_delay = self.config['params']['site']['capture_delay']
            del self.config['params']['site']['capture_delay']
        else:
            self.capture_delay = 30
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
        self.logger.info(f'Starting Naver Blog Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        # 검색어 입력
        e = self.get_by_xpath('//div[@class="search"]/input')
        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//i[@class="sp_common icon_search"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)

        # 최신순 클릭
        e = self.get_by_xpath('//a[@bg-nclick="srs*o.latest"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        try:
            e = self.get_by_xpath('//div[@class="u_cbox"]')
            es = e.find_element_by_xpath('.//ul[@class="u_cbox_list"]')
            comments = es.find_elements_by_xpath('.//div[@class="u_cbox_area"]')
            parent_comment_id = ''
            # 댓글이 없는 경우
            if len(comments) == 0:
                return
            for i, cmt_e in enumerate(comments):
                delay_c = random.uniform(
                    self.config['params']['site']['delay']['comment']['min'],
                    self.config['params']['site']['delay']['comment']['max'],
                )
                time.sleep(delay_c)
                cmt = {
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
                # 댓글 작성시간
                e = cmt_e.find_element_by_xpath('.//span[@class="u_cbox_date"]')
                cmt_ts = e.text.rpartition('.')
                t = cmt_ts[0]+cmt_ts[2]+":00"
                cmt['create_ts'] = datetime.datetime.strptime(t, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')

                inner_html = cmt_e.get_attribute('innerHTML')
                # 삭제된 댓글 경우 넘어감 댓글수에 영향을 안줌
                if inner_html.find('u_cbox_delete_contents') > 0:
                    continue
                # 비밀댓글 댓글수에 영향을 줌
                elif inner_html.find('u_cbox_secret_contents') > 0:
                    # 대댓글인지 확인
                    e = cmt_e.find_element_by_xpath('./..')
                    inner_html = e.get_attribute('innerHTML')
                    if inner_html.find('u_cbox_ico_reply') > 0:
                        is_reply = True
                    else:
                        is_reply = False
                    cmt['is_reply'] = is_reply
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ""
                    else:
                        cmt['parent_comment_id'] = parent_comment_id
                    cmt['contents'] = '비밀 댓글입니다.'
                else:
                    # 댓글 nickname
                    e = cmt_e.find_element_by_xpath('.//span[@class="u_cbox_nick_area"]/span')
                    cmt['nickname'] = e.text.strip()
                    self.move_to_element(e)

                    # 댓글 공감수
                    e = cmt_e.find_element_by_xpath('.//a[@class="u_cbox_btn_recomm"]/em')
                    cmt['like'] = int(e.text.strip())

                    # 댓글 내용
                    e = cmt_e.find_element_by_xpath('.//span[@class="u_cbox_contents"]')
                    cmt['contents'] = e.text.strip()

                    # 댓글 아이디
                    e = cmt_e.find_element_by_xpath('.//div[@class="u_cbox_tool"]/a')
                    ea = e.get_attribute('data-param')
                    cmt['comment_id'] = ea

                    # 대댓글인지 확인
                    e = cmt_e.find_element_by_xpath('./..')
                    inner_html = e.get_attribute('innerHTML')
                    if inner_html.find('u_cbox_ico_reply') > 0:
                        is_reply = True
                    else:
                        is_reply = False
                    cmt['is_reply'] = is_reply
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ""
                    else:
                        cmt['parent_comment_id'] = parent_comment_id

                    # 댓글 이미지
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    inner_html = e.get_attribute('innerHTML')
                    if inner_html.find('u_cbox_sticker_wrap') > 0:
                        re_img = cmt_e.find_element_by_xpath('//span[@class="u_cbox_sticker_wrap"]/a/img')
                        cmt['comment_img_url'].append(re_img.get_attribute('src'))  # src가 이미지 주소
                        cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except:
            ...

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        time.sleep(self.capture_delay)
        self.driver.find_element_by_xpath('html/body').screenshot(f)

    # ========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            self.switch_to_iframe_by_name('mainFrame')

            # 작성 시간: xpath가 다른 경우가 존재함
            e = self.get_by_xpath('//span[@class="se_publishDate pcol2"]|//p[@class="date fil5 pcol2 _postAddDate"]', timeout=0)
            msg['create_ts'] = ""
            et = e.text
            hhh, mmm = 0, 0
            if et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            else:
                msg['create_ts'] = datetime.datetime.strptime(et, '%Y. %m. %d. %H:%M').strftime('%Y.%m.%d %H:%M:%S')

            if msg['create_ts'] == "":
                d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
            msg['create_ts'] = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')

            # 게시글 공감수
            # 공감 창이 없는 경우는 무조건 0으로 표시
            e = self.get_by_xpath('//div[@class="post-btn post_btn2"]', timeout=1)
            try:
                e_a = e.find_element_by_xpath('.//span[@class="u_likeit_list_btn _button btn_sympathy pcol2 off"]/em[2]')
                msg['like'] = int(e_a.text.strip())
            except:
                msg['like'] = 0

            # 게시글에 달린 댓글 수
            # 댓글 창이 없는 경우는 무조건 0으로 표시
            e = self.get_by_xpath('//div[@class="post-btn post_btn2"]', timeout=1)
            try:
                e_b = e.find_element_by_xpath('.//em[@class="_commentCount"]')
                msg['num_comments'] = int(e_b.text.strip())
            except:
                msg['num_comments'] = 0
            # 게시글 내용: 블로그 구조마다 xpath 형식이 다름. 3가지 케이스가 존재함.
            comments_xpath = '//div[@class="se-main-container"]' \
                             '|//div[@id="postViewArea"]' \
                             '|//div[@class="se_component_wrap sect_dsc __se_component_area"]'
            e = self.get_by_xpath(comments_xpath, timeout=1)
            msg['contents'] = e.text.strip()

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 가져오기. 이미지도 블로그 구조마다 xpath 형식이 다름
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                img_xpath = './/img[@class="se-image-resource egjs-visible"]' \
                            '|.//img[@class="se-sticker-image egjs-visible"]' \
                            '|.//img[@class="se-map-image egjs-visible"]' \
                            '|.//img[@class="_photoImage egjs-visible"]' \
                            '|.//img[@class="se_mediaImage __se_img_el egjs-visible"]'
                for j, sub_e in enumerate(e.find_elements_by_xpath(img_xpath)):
                    self.move_to_element(sub_e)
                    # self.implicitly_wait(after_wait=1)
                    img_es = e.find_elements_by_xpath(img_xpath)
                    sub_e = img_es[j]
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)
                    # 이미지캡쳐 headless의 경우 캡쳐를함.
                    if self.config['params']['kwargs']['headless']:
                        cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{j}.png')
                        sub_e.screenshot(cmt_img_f)
                        msg['image_list'].append(f'{j}.png')

            # 게시글 댓글 단 블로거 목록 열기
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            try:
                e = self.get_by_xpath('//span[@class="btn_arr"]', timeout=1)
                self.safe_click(e)
                # 댓글페이지가 많은 경우 1번부터 시작하도록 클릭. 먼저 이전페이지가 있는지 부터 체크 해야함.
                while True:
                    cmt_pre = self.get_by_xpath('//*[@class="u_cbox_pre"]', timeout=1)
                    if cmt_pre.tag_name == 'a':
                        self.safe_click(cmt_pre)
                    else:
                        break
                # 댓글페이지를 구해서 1페이지를 눌러줘야함.
                e = self.get_by_xpath('//div[@class="u_cbox_page_wrap"]/*[(@data-param="1")and(@class="u_cbox_page")]', timeout=1)
                if e.tag_name == 'a':
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=1)
                while True:
                    e = self.get_by_xpath('//div[@class="u_cbox_page_wrap"]', timeout=1)
                    cmt_page_wrap = e.find_elements_by_xpath('./*[@class="u_cbox_page"]|./a[@class="u_cbox_next"]')
                    read_c_page = False
                    is_end = True
                    for p_n, cmt_page in enumerate(cmt_page_wrap):
                        if cmt_page.tag_name == 'strong':
                            self.get_comment(msg)
                            read_c_page = True
                            continue
                        if read_c_page:
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                            is_end = False
                            break
                    # 마지막 댓글 페이지일경우 read_c_page가 true인 상태로 나옴.
                    if is_end:
                        break

            except:
                return

        except Exception as err:
            raise
        finally:
            # 마지막에 캡쳐하도록 변경
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                try:
                    if self.config['params']['kwargs']['headless']:
                        self._screenshot(msg_capture_f)
                    else:
                        # 상단바와 하단바 삭제
                        e_heads = self.driver.find_elements_by_xpath('//div[@id="floating_area_header"]|'
                                                                     '//div[@id="floating_bottom"]')
                        for e_head in e_heads:
                            self.driver.execute_script("""
                            var element = arguments[0];
                            element.parentNode.removeChild(element);
                            """, e_head)
                        self.full_screenshot(msg_capture_f)
                except:
                    ...
            # 이전 페이지
            self.driver.close()
            self.implicitly_wait(after_wait=3)
            try:
                self.switch_to_main_window()
            except:
                # selenium.common.exceptions.WebDriverException: Message: unknown error:
                # cannot determine loading status
                pass

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
    def get_page(self):
        try:
            self.cur_page += 1
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="area_list_search"]')
            es = e.find_elements_by_xpath('.//div[@class="list_search_post"]')

            for i, ea in enumerate(es):
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    e = self.get_by_xpath('//div[@class="area_list_search"]')
                    es = e.find_elements_by_xpath('.//div[@class="list_search_post"]')
                    ea = es[i]
                    # 1) 게시글 id : article_id  300143_55268553
                    e_url = ea.find_element_by_xpath('.//div[@class="desc"]/a[1]')
                    a_url = e_url.get_attribute('ng-href')
                    v = a_url.partition('.')[2].partition('/')[2].partition('/')[2]
                    msg['article_id'] = v
                    # 1) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 2) 제목: title
                    e = ea.find_element_by_xpath('.//strong[@class="title_post"]/span')
                    a = e.text.strip()
                    out_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", a)
                    # 3) 작성자
                    e = ea.find_element_by_xpath('.//div[@class="writer_info"]/a')
                    msg['author'] = e.text.strip()
                    # 4) 블로그 이름
                    e = ea.find_element_by_xpath('.//span[@class="name_blog"]')
                    msg['site_name'] = e.text.strip()

                    self.safe_click(e_url)
                    self.implicitly_wait(after_wait=1)
                    try:
                        # 비공개글 회피로직
                        self.switch_to_main_window()
                        self.switch_to_window(1)
                        self.implicitly_wait(after_wait=2)
                        self.switch_to_iframe_by_name('mainFrame')
                        # 게시글 제목 비교 띄어쓰기가 단락으로 인해 차이가 있을 수 있음
                        e = self.driver.find_element_by_xpath('//div[@class="pcol1"]|'
                                                                     '//span[@class="pcol1 itemSubjectBoldfont"]').text.strip()
                        msg['title'] = e
                        in_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", e)
                        if not in_title.replace(' ', '').startswith(out_title.replace(' ', '')[:-3]):
                            self.logger.debug('비공개 글 입니다.')
                            self.logger.debug(f'게시글의 url: {msg["article_url"]}')
                            self.logger.debug(f'게시글의 title: {msg["title"]}')
                            for _ in self.driver.window_handles:
                                if len(self.driver.window_handles) == 1:
                                    break
                                self.switch_to_window(1)
                                self.driver.close()
                            self.switch_to_main_window()
                            self.implicitly_wait(after_wait=2)
                            continue
                    except:
                        self.logger.debug('비공개 글 입니다.')
                        self.logger.debug(f'게시글의 url: {msg["article_url"]}')
                        for _ in self.driver.window_handles:
                            if len(self.driver.window_handles) == 1:
                                break
                            self.switch_to_window(1)
                            self.driver.close()
                        self.switch_to_main_window()
                        self.implicitly_wait(after_wait=2)
                        continue
                    self.get_article(msg, i + 1)
                except Exception as err:
                    if 'article_id' not in msg:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(f'게시글의 url: {msg["article_url"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True
                    break
                if not self.config['params']['kwargs']['headless']:
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
            self.switch_to_main_window()

        # ==========================================================================

    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//div[@class="layout_content"]')
            ple = e.find_element_by_xpath('.//div[@class="pagination"]')
            self.move_to_element(ple)
            is_on = False
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('ng-if') == 'currentPage==page':
                    is_on = True
                    continue

                if is_on:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            raise
        finally:
            self.switch_from_iframe()

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
            if not('comment_img' in cmt and cmt['comment_img']):
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
            self.search()
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.next_page()
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with NaverBlogSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'blog_naver.yaml'
    do_start(config_f=_config_f)
