"""
====================================
 :mod:`gov/ instiz_02 : 인스티즈 이슈
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
# * Yeonhee Ji
#
# Change Log
# --------
#  * [2024/11/06]
#     - 게시글 접속 방식 변경(링크 click -> 탭으로 띄움)
#  * [2024/09/18]
#     - 게시글과 댓글의 등록 시간 형식 변경되어 날짜 형식 변경(2024.03.24 00:00:00 -> 2024/03/24 00:00:00)
#  * [2024/08/26]
#     -  검색 박스 UI 변경으로 XPath 수정
#     - 제목 옆 댓글 수 제거
#  * [2024/08/01]
#     -  전체 스크린샷에 본문만 포함되도록 수정
#  * [2024/03/19]
#     -  에러 코드 세분화
#     -  에러 로그 세분화
#     -  게시글 존재 여부 확인 로직 수정
#  * [2024/01/25]
#     -  제목에 댓글수 들어가지 않도록 수정
#  * [2024/01/23]
#     -  제목 , 댓글수 xpath 변경
#  * [2024/01/11]
#     -  게시글 본문에 있는 더보기 버튼 제외 -> p태그만 수집
#  * [2023/12/29]
#     -  게시글 본문 UI 변경
#  * [2023/12/19]
#     -  게시글 본문 UI 변경
#  * [2022/12/08]
#     -  사이트 UI 변경
#  * [2022/08/31]
#     -  article_id xpath 변경
#  * [2022/04/20]
#     - 회원만 접근되는 글 제거
#  * [2022/04/05]
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
import requests
import datetime
import urllib.request
# from datetime import timedelta
from bs4 import BeautifulSoup
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
# from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

################################################################################
def download_wait(directory, timeout, nfiles=None):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1
    return seconds


################################################################################

class Instiz02(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'Instiz02.log'),
                            logsize=1024 * 1024 * 10)
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
        self.logger.info(f'Starting Instiz02 Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:

            # # HOT 댓글 많은 거 찾아 볼 때
            # e = self.get_by_xpath('//a[@id="sort_btn_4"]')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)

            # 검색어 입력
            e = self.get_by_xpath('//input[@onclick="searchbox();"]')
            self.send_keys(e, self.config['params']['site']['search']+Keys.ENTER)
            self.implicitly_wait(after_wait=1)
        except Exception as err:
            self.logger.error(f'search: error: {str(err)}')
            raise
    # ==========================================================================

    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================

    def get_comment(self, msg):
        try:
            e_a = self.get_by_xpath('//iframe[@id="ifrm_notify"]/..//div[@id="ajax_comment"]//tbody')
            comments = e_a.find_elements_by_xpath('./tr[@id]//div[@class="comment_line"]')
            parent_comment_id = ''

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

                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath('//div[@class="comment_line"]/span[2]')
                e_t = e.get_attribute('onmouseover')
                create_ts = e_t.partition("html('")[2].rpartition("'")[0]
                # cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                if re.search(r'/', create_ts):
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y/%m/%d %H:%M:%S').strftime(
                        '%Y.%m.%d %H:%M:%S')
                else:
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                        '%Y.%m.%d %H:%M:%S')

                # 댓글 아이디
                e = cmt_e.find_element_by_xpath('//div[@class="comment_line"]/span[1]')
                ea = e.get_attribute('id')
                cmt['comment_id'] = ea
                self.move_to_element(e)

                # 대댓글 확인
                e = cmt_e.find_element_by_xpath('./../div[3]')
                e_re = e.get_attribute('class')
                if e_re.find('cmt_sb') != 0:
                    is_reply = True
                else:
                    is_reply = False
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id

                # 댓글 nickname
                e = cmt_e.find_element_by_xpath('./..//span/span')
                cmt['nickname'] = e.text.strip()

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('./span')
                cmt['contents'] = e.text.strip()

                # 댓글 이미지
                inner_html = cmt_e.get_attribute('innerHTML')
                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                if inner_html.find('lazy addimg_th') > 0:
                    re_img = cmt_e.find_element_by_xpath('.//img')
                    cmt['comment_img_url'].append(re_img.get_attribute('src'))   # src가 이미지 주소
                    cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except:
            ...
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
            try:
                # 비밀글이면 iframe를 찾지 못함
                e_ab = self.get_by_xpath('//iframe[@id="ifrm_notify"]/..', timeout=1)
            except:
                self.logger.info(f'{msg["title"]} is secret article')
                return
            # 1) 작성자
            e = e_ab.find_element_by_xpath('.//td[@class="tb_lr minitext"]/div/span[1]|.//div[@class="tb_left minitext"]//a[1]')
            msg['author'] = e.text.strip()
            # 4) 작성 시간
            e = e_ab.find_element_by_xpath('.//td[@class="tb_lr minitext"]/div/span[3]|.//div[@class="tb_left minitext"]//a[2]')
            create_ts = e.get_attribute('title')
            # 작성 시간 형식이 바뀜 2024.03.24 00:00:00 -> 2024/03/24 00:00:00
            if re.search(r'/', create_ts):
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y/%m/%d %H:%M:%S').strftime(
                    '%Y.%m.%d %H:%M:%S')
            else:
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                    '%Y.%m.%d %H:%M:%S')
            # 댓글 수 : 댓글 없는 경우에는 path를 못 찾음
            e = e_ab.find_element_by_xpath('.//span[@class="cmt"]')
            num_comments = e.text.strip()
            if num_comments != '':
                msg['num_comments'] = int(num_comments)
            else:
                msg['num_comments'] = 0
            # 본문
            e = e_ab.find_element_by_xpath('.//div[@class="memo_content"]|.//div[@class="memo_content backlogo"]')
            # msg['contents'] = e.text.strip()
            # 본문 HTML
            inner_html = e.get_attribute('innerHTML')
            soup = BeautifulSoup(inner_html, 'html.parser')
            # 본문 내에 P태그 전체 찾기
            p_tags = soup.find_all('p')
            contents = ''
            for p_tag in p_tags:
                contents += p_tag.text.strip()

            msg['contents'] = contents
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//span/img' 
                                                                   '|.//p/img'
                                                                   '|./img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@id="menuall"]|'
                                                                 '//div[@id="remoteparent"]|'
                                                                 '//div[@id="sidead3"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                                        var element = arguments[0];
                                                                        element.parentNode.removeChild(element);
                                                                        """, e_head)
                    self.implicitly_wait(after_wait=1)
                    # self.full_screenshot(msg_capture_f)
                    self.full_screenshot_article(msg_capture_f)
            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            try:
                # 댓글 페이지
                while True:
                    try:
                        e = self.get_by_xpath('//iframe[@id="ifrm_notify"]/..//div[@id="ajax_comment"]//tbody')
                        cmt_page = e.find_element_by_xpath('//*[@id="indextable"]/tbody/tr/td[1]//span')
                        if cmt_page.text == '◀':
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                        else:
                            break
                    except:
                        break
                # 1페이지 누르기
                e = self.get_by_xpath('//iframe[@id="ifrm_notify"]/..//div[@id="ajax_comment"]//tbody')
                cmt_1 = e.find_element_by_xpath('//*[@id="indextable"]/tbody/tr/td[1]')
                if cmt_1.tag_name == 'td':
                    self.safe_click(cmt_1)
                    self.implicitly_wait(after_wait=1)
                cmt_page_n = 1
                while True:
                    e = self.get_by_xpath(
                        '//iframe[@id="ifrm_notify"]/..//div[@id="ajax_comment"]//tbody//table[@id="indextable"]')
                    cmt_ple = e.find_element_by_xpath('./tbody//tr')
                    now_page = False
                    self.get_comment(msg)
                    cmt_ps = cmt_ple.find_elements_by_xpath('.//td/a')
                    for cmt_p in cmt_ps:
                        if cmt_p.text == '◀ 이전':
                            continue
                        elif cmt_p.find_element_by_xpath('./..').get_attribute('class') == 'indexing1':
                            now_page = True
                            continue
                        elif now_page:
                            cmt_page_n += 1
                            self.safe_click(cmt_p)
                            self.implicitly_wait(after_wait=1)
                            break
                            # 댓글이 실시간 업데이트 되면 num_comment 에 반영 안 될 때가 있어서 초과함
                        if msg['num_comments'] <= len(msg['comment_list']):
                            break
                    if msg['num_comments'] <= len(msg['comment_list']):
                        break

            except:
                self.get_comment(msg)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # 이전 페이지
            self.driver.close()
            self.implicitly_wait(after_wait=1)
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
            # 검색 결과 존재 여부 확인
            try:
                e = self.get_by_xpath('//table[@id="mboard"]/tbody/tr[@id="detour"]', timeout=1)
            except:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return

            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//table[@id="mboard"]/tbody', timeout=1)
            es = e.find_elements_by_xpath('./tr/td[@class="minitext listnm"]/..')

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
                    e = self.get_by_xpath('//table[@id="mboard"]/tbody')
                    es = e.find_elements_by_xpath('./tr/td[@class="minitext listnm"]/..')
                    ea = es[i]

                    # 1) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./td[2]/a[1]')
                    a_url = e_url.get_attribute('href')
                    v = a_url.rpartition('pt/')[2].partition('?')[0]
                    msg['article_id'] = v
                    # 2) 게시글 url : article_url
                    msg['article_url'] = a_url
                    # 3) 조회수
                    e = ea.find_element_by_xpath('./td[@class="listno"][1]')
                    msg['view_count'] = int(e.text.strip())
                    # 4) 좋아요
                    e = ea.find_element_by_xpath('./td[@class="listno"][2]|./td[@class="listno menuicon_red"]')
                    msg['like'] = int(e.text.strip())
                    # 5) 제목: title
                    # 제목 옆 댓글 수 제거
                    try:
                        top_area = ea.find_element_by_xpath('.//span[@class="cmt2"]')
                        self.driver.execute_script("arguments[0].remove();", top_area)
                    except Exception as e:
                        self.logger.error(f'하단 광고 제거 실패: {e}')
                    e_t = ea.find_element_by_xpath('./td[2]/a[1]')
                    title = e_t.text.strip()
                    msg['title'] = title
                    # try:
                    #     e_q = e_t.find_element_by_xpath('./span[@class="cmt2"]')
                    #     num_com = e_q.text.strip()
                    #     msg['title'] = title.replace(num_com.strip(), '')
                    # except:
                    #     msg['title'] = title
                    self.move_to_element(e_t)

                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                # 회원 공개글 제거로직
                # if not msg['create_ts']:
                #     shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                #     continue
                if msg['contents'] is None:
                    continue
                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
                self.save_attachment(msg)
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
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//form[@id="list"]')
            ple = e.find_element_by_xpath('.//table[@id="indextable"]/tbody/tr')
            e = ple.find_element_by_xpath('./td[@class]')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == '다음':
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.text.strip() in ['끝', '처음', '이전']:
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
    def save_attachment(self, article):
        for i, attach_url in enumerate(article['attachment_url']):
            article_attach_p = self.get_safe_path(
                self.config['target']['folder'],
                article['article_id'],
                article['attachment_name'][i]
            )
            file = requests.get(attach_url, stream= True)
            with open(article_attach_p, "wb") as d_file:
                for chunk in file.iter_content(chunk_size=1024):
                    if chunk:
                        d_file.write(chunk)

    # ==========================================================================
    def full_screenshot_article(self, output_file):
        try:
            # 광고
            ad = self.get_by_xpath("//div[@class='imgbox responsive_main']")
            self.driver.execute_script("arguments[0].remove();", ad)
        except:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass
        # 요소 찾기
        element = self.driver.find_element_by_xpath('//div[@class="responsive_main"]/table/tbody/tr')

        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size

        # 현재 페이지의 크기 가져오기
        original_window_size = self.driver.get_window_size()
        original_scroll_position = self.driver.execute_script("return window.pageYOffset;")

        # 페이지의 높이 가져오기
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")

        # 리스트 초기화
        images = []
        scroll_position = 0

        # 페이지를 스크롤하면서 스크린샷 찍기
        while scroll_position < page_height:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)

            # 스크린샷 찍기
            png = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(png))
            images.append(image)

            # 스크롤 위치를 업데이트
            scroll_position += viewport_height

        # 페이지 원래 상태로 복원
        self.driver.set_window_size(original_window_size['width'], original_window_size['height'])
        self.driver.execute_script(f"window.scrollTo(0, {original_scroll_position});")

        # 이미지 병합
        total_height = len(images) * images[0].height
        merged_image = Image.new('RGB', (images[0].width, total_height))

        current_height = 0
        for image in images:
            merged_image.paste(image, (0, current_height))
            current_height += image.height

        # 원하는 영역만 잘라내기
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']

        cropped_image = merged_image.crop((left, top, right, bottom))

        # 최종 이미지 저장
        cropped_image.save(output_file)
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
        with Instiz02(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'instiz_02.yaml'
    do_start(config_f=_config_f)
