"""
====================================
 :mod:`news/news_kmib`
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
#  * [2023/04/18]
#     - 게시글 스크린샷에 댓글 부분 포함 / 윈도우 창 크기 설정
#  * [2023/04/11]
#     - 게시글 스크린 샷 추가
#  * [2022/11/24]
#     - 댓글 부분의 ifrmae 수정  # 검색 전 스크린 샷 추가
#  * [2022/06/14]
#     - Thread.join에 timeout 파라미터 수정
#  * [2022/05/24]
#     - Python Selenium에서는 모듈이 설치가 안되서 돌리지 못함.
#     - page timeout 시간 yaml에서 수정 가능하도록 변경
#  * [2022/05/19]
#     - 댓글 중복 수집오류 수정.
#  * [2022/05/17]
#     - 무한로딩 최적화 수정
#     - 무한로딩 최적화 재수정 (22.5.18)
#  * [2022/05/13]
#     - 댓글 무한루프에러 수정
#  * [2022/05/09]
#     - 새탭으로 게시글 오픈 로직. 댓글 최신순으로 한번더 클릭하는 로직 추가
#  * [2022/02/07]
#     - starting
################################################################################
import os
# import re
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
from threading import Thread
import functools
import pyautogui
#
# ################################################################################
# def d_timeout(time_out):
#     def deco(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, time_out))]
#
#             def newFunc():
#                 try:
#                     res[0] = func(*args, **kwargs)
#                 except Exception as e:
#                     res[0] = e
#             t = Thread(target=newFunc)
#             t.daemon = True
#             try:
#                 t.start()
#                 t.join(time_out)
#             except Exception as je:
#                 print('error starting thread')
#                 raise je
#             ret = res[0]
#             if isinstance(ret, BaseException):
#                 raise ret
#             return ret
#         return wrapper
#     return deco


def _get_cmt_id(n):
    return n['comment_id']


################################################################################
class NewsKmibSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NewsKmibSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        self.page_timeout = self.config['params']['site']['page_wait_time']
        del self.config['params']['site']['page_wait_time']
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
        self.logger.info(f'Starting Kmib News Crawaling... with '
                         f'config:\n{out_config}')

    ################################################################################
    def d_timeout(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            this = args[0]
            time_out = this.page_timeout
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, time_out))]

            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e

            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout=time_out)
            except Exception as je:
                print('error starting thread')
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret
        return wrapper

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e = self.get_by_xpath('//div[@class="srch_wrap"]/input[1]')
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//div[@class="srch_wrap"]/input[2]',
                              cond='element_to_be_clickable')
        self.safe_click(e)

        # 최신순 클릭
        e = self.get_by_xpath('//div[@id="searchResultInfo"]/div/ul/li[1]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        try:
            e_a = self.get_by_xpath('//div[@id="wrapper"]')
            comments = e_a.find_elements_by_xpath('.//div[@id="list"]/div[@class="reply-wrapper"]|.//div[@id="list"]/div[@class="reply-wrapper"]/div/div[@class="child-reply"]/div[@class="reply-wrapper"]')
            # '|.//div[@class="reply-wrapper reply-best-wrapper"]
            parent_comment_id = None

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
                e_a = self.get_by_xpath('//div[@id="wrapper"]')
                comments = e_a.find_elements_by_xpath('.//div[@id="list"]/div[@class="reply-wrapper"]|.//div[@id="list"]/div[@class="reply-wrapper"]/div/div[@class="child-reply"]/div[@class="reply-wrapper"]')
                cmt_e = comments[i]
                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath(
                    './div/div/ul/li/div[@class="reply-history-time"]/span[@class="modify-time"]')
                create_ts_e = e.get_attribute('title').replace('오후', 'pm').replace('오전', 'am')
                create_ts = datetime.datetime.strptime(create_ts_e, '%Y년 %m월 %d일 %p %I:%M').strftime('%Y.%m.%d %H:%M:%S')
                cmt['create_ts'] = create_ts

                # 댓글 아이디
                e = cmt_e.get_attribute('data-seq')
                cmt['comment_id'] = e
                # 중복 id체크
                if cmt['comment_id'] in list(map(_get_cmt_id, msg['comment_list'])):
                    self.logger.debug(f'duplicate comments : {cmt["comment_id"]}')
                    continue

                # 대댓글 확인
                e = cmt_e.find_element_by_xpath('./..')
                e_re = e.get_attribute('class')
                if e_re == 'child-reply':
                    is_reply = True
                    cmt['parent_comment_id'] = parent_comment_id
                else:
                    is_reply = False
                    parent_comment_id = cmt['comment_id']
                cmt['is_reply'] = is_reply

                # 댓글 nickname
                e = cmt_e.find_element_by_xpath('./div/div/ul/li[@class="writer-name"]/button/span')
                cmt['nickname'] = e.text.strip()

                # 댓글 좋아요, 싫어요
                e = cmt_e.find_element_by_xpath(
                    './div/div[@class="reply-content-wrapper"]/div/div[@class="right"]/button[@title="공감"]/span[2]')
                cmt['like'] = int(e.text.strip())
                e = cmt_e.find_element_by_xpath(
                    './div/div[@class="reply-content-wrapper"]/div/div[@class="right"]/button[@title="반대"]/span[2]')
                cmt['dislike'] = int(e.text.strip())

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('./div/div[@class="reply-content-wrapper"]/div[@class="reply-content"]')
                cmt['contents'] = e.text.strip()
                # 댓글 이미지
                inner_html = e.get_attribute('innerHTML')
                if inner_html.find('attached-image') > 0:
                    re_imgs = cmt_e.find_elements_by_xpath('.//img|.//span[@class="reply-image-viewer attached-image text-indent"]')
                    for re_img in re_imgs:
                        cmt['comment_img_url'].append(re_img.get_attribute('data-src'))  # data-src가 이미지 주소
                    # 이미지의 텍스트도 가져오는 경우가 있슴.
                    cmt['contents'] = cmt['contents'].replace('이미지 확대하기', '').replace('첨부된 이미지\n첨부된 이미지', '').replace('첨부된 이미지', '')
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            ...

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # 이미지로딩을 위해 기다려줘야함.
        self.implicitly_wait(after_wait=1)
        self.driver.find_element_by_tag_name('body').screenshot(f)

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

            # 기사 상단
            e_ab = self.get_by_xpath('//div[@class="sub_header"]', timeout=1)
            # 작성 시간
            e = e_ab.find_element_by_xpath('.//div[@class="nwsti_btm"]/div/span[1]')
            msg['create_ts'] = e.text.replace('-', '.') + ':00'
            # 카테고리
            e = e_ab.find_element_by_xpath('.//p[@class="loca"]')
            msg['board_name'] = e.text.strip()
            # 기사 하단
            e_ac = self.get_by_xpath('//div[@id="articleBody"]')
            # 게시글 내용:
            e = e_ac
            msg['contents'] = e.text.strip()

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e_ac.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                img_xpath = './/div[@align="center"]' \
                            '|.//div[@id="gisaimage"]'
                for j, sub_e in enumerate(e_ac.find_elements_by_xpath(img_xpath)):
                    self.move_to_element(sub_e)
                    img_es = e.find_elements_by_xpath(img_xpath)
                    sub_e = img_es[j]
                    sub_e_url = sub_e.get_attribute('innerHTML')
                    sub_e_url_l = sub_e_url.partition('src="')[2].partition('"')[0]
                    msg['image_url_list'].append(sub_e_url_l)

            # 댓글에 iframe이 있음. 하지만 스크롤 내려야 생겨남.
            self.scroll_by(0, 10000)
            self.implicitly_wait(after_wait=2)
            self.switch_to_iframe('//div[@id="lv-container"]/iframe[@title]')
            # e = self.get_by_xpath('//*[@id="lv-comment-745"]')
            e_c = self.get_by_xpath('//div[@id="wrapper"]', timeout=1)

            # 댓글 개수
            try:
                e = self.get_by_xpath('//div[@class="reply-count"]//span[@class="count-text"]')
                # e = self.get_by_xpath('//div[@class="reply-count"]//span[@class="count-text"]',
                #                       timeout=3,
                #                       wait_until_valid_text=True)
                msg['num_comments'] = int(e.text.strip())
            except:
                msg['num_comments'] = 0

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []

            # 최신순 best댓글이 있어서 한번 눌러줘야함
            e = e_c.find_element_by_xpath('.//button[@data-value="recent"]')
            self.move_to_element(e)
            self.safe_click(e)
            self.implicitly_wait(1)
            self.safe_click(e)
            self.implicitly_wait(1)
            # 댓글 페이지가 있는 경우
            try:
                is_on = None
                while True:
                    e = e_c.find_element_by_xpath('.//div[@class="more-wrapper"]')
                    b_ple = e.find_elements_by_xpath('./button/span')
                    for pa, cmt_page in enumerate(b_ple):
                        e = e_c.find_element_by_xpath('.//div[@class="more-wrapper"]')
                        b_ple = e.find_elements_by_xpath('./button/span')
                        cmt_page = b_ple[pa]
                        is_on = cmt_page.text
                        if is_on == '< 이전페이지':
                            continue
                        elif is_on == '다음페이지 >':
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                        elif int(is_on) > 0:
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                            # 대댓글 버튼
                            e_re_bt = e_c.find_elements_by_xpath('.//button[@class="reply-comment-btn"]')
                            for c_bt in e_re_bt:
                                if c_bt.get_attribute('innerHTML').find('comment-count  hide ') > 0:
                                    continue
                                self.safe_click(c_bt)
                                self.implicitly_wait(after_wait=1)
                            # 댓글내용 더보기 버튼
                            e_m_c_bt = e_c.find_elements_by_xpath('.//div[@class="list-reduce"]/button[@type="button"]')
                            for m_c_bt in e_m_c_bt:
                                self.safe_click(m_c_bt)
                                self.implicitly_wait(after_wait=1)
                        self.get_comment(msg)
                        if msg['num_comments'] == len(msg['comment_list']):
                            break
                    if msg['num_comments'] == len(msg['comment_list']):
                        break
                    elif is_on != '다음페이지 >':
                        msg['num_comments'] = len(msg['comment_list'])
                        break

            except:
                return

        except Exception as err:
            raise
        finally:
            # 스크린샷
            self.driver.switch_to.default_content()  # iframe 다시 전환
            self.driver.set_window_size(1600, 768)
            if self.config['params']['site']['capture_article']:
                # save capture
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    # 광고제거
                    e = self.get_by_xpath('//div[@class="__staxbn_wrap on"]', timeout=1)
                    self.driver.execute_script("""
                                            var element = arguments[0];
                                            element.parentNode.removeChild(element);
                                            """, e)
                    self.implicitly_wait(after_wait=1)
                    self.full_screenshot(msg_capture_f)
            # 이전 페이지
            # self.driver.back()
            self.driver.close()
            self.implicitly_wait(after_wait=2)
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
            e = self.get_by_xpath('//div[@id="searchList"]')
            es = e.find_elements_by_xpath('./div')

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
                    e = self.get_by_xpath('//div[@id="searchList"]')
                    es = e.find_elements_by_xpath('./div')
                    ea = es[i]
                    self.move_to_element(ea)
                    # 1) 게시글 id : article_id  300143_55268553
                    e_url = ea.find_element_by_xpath('.//dt[@class="tit"]/a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('id=')[2]
                    msg['article_id'] = v
                    # 1) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 2) 제목: title
                    e = ea.find_element_by_xpath('.//dt[@class="tit"]/a')
                    msg['title'] = e.text.strip()

                    # self.safe_click(e_url)
                    try:
                        self._open_url(a_url)
                    except Exception as err:
                        self.logger.error(f"Timeout error!! page_url : {msg['article_url']}")
                        self.logger.error(err)
                        # 로딩중인 페이지를 셀레니움 동작으로 접은하면 로딩이 끝날때까지 기다림.
                        pyautogui.hotkey('ctrl', 'w')
                        self.switch_to_main_window()
                        continue
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
                except Exception as err:
                    if not msg['article_id']:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
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
            self.switch_to_main_window()

    # ==========================================================================
    @d_timeout
    def _open_url(self, url):
        # element 찾는 시간 설정
        # self.driver.set_page_load_timeout(60)
        # 스크립트 시간 설정
        # self.driver.set_script_timeout(180)
        # self.driver.execute_script(f"window.open('{url}');")
        self.driver.execute_script(f"window.open('');")
        self.switch_to_window(1)
        self.driver.get(url)
        return

    # ==========================================================================
    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//div[@class="NwsCon"]')
            ple = e.find_element_by_xpath('.//div[@id="paging"]')
            e = ple.find_element_by_xpath('./strong')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('class') == 'next':
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.get_attribute('class') == 'first':
                    continue
                elif pa.get_attribute('class') == 'prev':
                    continue
                elif int(pa.text.strip()) > is_on:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
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
            for k, cmt_url in enumerate(cmt['comment_img_url']):
                try:
                    cmt_img_f = self.get_safe_path(
                        self.config['target']['folder'],
                        article['article_id'],
                        f'{cmt["comment_id"] + "_" + str(k)}.png'
                    )
                    urllib.request.urlretrieve(cmt_url, cmt_img_f)
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_" + str(k)}.png')
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
# def do_start(**kwargs):
#     with NewsKmibSearch(kwargs['config_f']) as ws:
#         ws.start()
#         return 0
################################################################################
def main(**kwargs):
    with NewsKmibSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'news_kmib.yaml'
    main(config_f=_config_f)
    # do_start(config_f=_config_f)
