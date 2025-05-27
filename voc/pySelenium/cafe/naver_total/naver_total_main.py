"""
====================================
 :mod:`cafe/naver_total_main
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
#  * [2023/04/11]
#     - 검색 전 스크린 샷 추가
#  * [2023/02/10]
#     - 해쉬태그 수집
#  * [2022/12/05]
#     - 삭제된 게시글 회피 로직 수정
#     - 삭제된 게시글의 경우 로그 메세지 추가(게시글의 url과 title)
#     - 해쉬 태그 수집하는 로직 추가
#  * [2022/10/20]
#     - 윈도우 창 개수 확인하는 로직 추가
#  * [2022/10/17]
#     - 삭제된 게시글 회피 로직 수정
#  * [2022/09/28]
#     - 삭제된 게시글 회피 로직 추가
#  * [2022/02/14]
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
# from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# from bs4 import BeautifulSoup


################################################################################
class NaverTotalSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverTotalSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
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
        self.logger.info(f'Starting NaverTotal Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e = self.get_by_xpath('//input[@class="input_text"]')
        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@id="search_btn"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # view 선택
        e = self.get_by_xpath('//div[@id="lnb"]')
        for i in e.find_elements_by_xpath('//div[@id="lnb"]//div/ul/li[@class="menu"]//a'):
            if i.text.strip() == 'VIEW':
                self.safe_click(i)
                self.implicitly_wait(after_wait=1)
                break
            else:
                continue

        # 카페
        e = self.get_by_xpath('//div[@id="snb"]//div[@class="list_option_filter type_solo"]//a[3]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 옵션 필터
        e = self.get_by_xpath('//div[@id="snb"]/div//div[@class="option_filter"]/a',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        e = self.get_by_xpath('//div[@id="snb"]/div[@role="listbox"]')
        # 최신순
        l = e.find_element_by_xpath('.//ul/li[@class="bx lineup"]//div[@role="tablist"]/a[2]')
        self.safe_click(l)
        self.implicitly_wait(after_wait=1)
        # 전체
        # a = e.find_element_by_xpath('.//ul/li[@class="bx term"]//div[@role="tablist"]/a[1]')
        # self.safe_click(a)
        # self.implicitly_wait(after_wait=1)
        # 옵션 닫기
        e = self.get_by_xpath('//button[@class="spnew_bf bt_close _search_option_close_btn"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_comment(self, msg):
        try:

            e_a = self.get_by_xpath('//ul[@class="comment_list"]')
            comments = e_a.find_elements_by_xpath('./li')
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
                # 댓글 id
                cmt['comment_id'] = cmt_e.get_attribute('id')

                # 대댓글
                is_reply = cmt_e.get_attribute('class') == 'CommentItem CommentItem--reply'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ''
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                # 댓글 nickname : 삭제된 댓글인 경우 발견 불가
                try:
                    e = cmt_e.find_element_by_xpath('.//a[@class="comment_nickname"]')
                    cmt['nickname'] = e.text.partition('|')[0].strip()
                except:
                    continue

                # 댓글 작성 시각
                e = cmt_e.find_element_by_xpath('.//span[@class="comment_info_date"]')
                create_ts = e.text.strip().rpartition('.')
                cmt['create_ts'] = create_ts[0] + create_ts[2] + ':00'

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('.//span[@class="text_comment"]')
                self.move_to_element(e)
                comment = e.text
                # 댓글 내용중에 멘션이 있을 경우 포함
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find("text_nickname") > 0:
                    tag = cmt_e.find_element_by_xpath('.//a[@class="text_nickname"]').text
                    cmt['contents'] = tag + ' ' + comment
                else:
                    cmt['contents'] = comment

                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                # 댓글 스티커 or 이미지
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find('CommentItemSticker') > 0 or inner_html.find('CommentItemImage') > 0:
                    s = cmt_e.find_element_by_xpath('.//img[@class="image"]')
                    cmt['comment_img_url'].append(s.get_attribute('src'))
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            raise

    # ========================================================================
    def get_num_from_str(self, s):
        # s = 1.5만개 or 1.4천회
        _s = s
        try:
            if _s.endswith(('개', '회')):
                _s = _s[:-1]
            times = 1
            if _s.endswith('천'):
                times = 1000
                _s = _s[:-1]
            elif _s.endswith('만'):
                times = 10000
                _s = _s[:-1]
            f = float(_s)
            f *= times
            return int(f)
        except Exception as err:
            self.logger.error(f'in _get_num_from_str: Cannot parse into int for "{s}"')
            raise

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            self.switch_to_window(1)
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # self.full_screenshot(msg_capture_f)
                self._screenshot(msg_capture_f)
            # 카페에 main iframe으로 이동
            self.switch_to_iframe_by_name('cafe_main')
            e_ab = self.get_by_xpath('//div[@class="ArticleContentBox"]')

            # 카페 이름: site_name
            e = self.get_by_xpath('//div[@class="CafeJoinInducement"]/a//strong')
            msg['site_name'] = e.text.strip()
            # 게시판 이름
            e = self.get_by_xpath('//a[@class="link_board"]')
            msg['board_name'] = e.text.strip()
            # 작성 시간
            e = e_ab.find_element_by_xpath('.//span[@class="date"]')
            create_t = e.text.strip().rpartition('.')
            msg['create_ts'] = create_t[0] + create_t[2] + ':00'
            # 작성자
            e = e_ab.find_element_by_xpath('.//button[@class="nickname"]')
            msg['author'] = e.text.strip()
            # 조회수: view_count
            e = e_ab.find_element_by_xpath('.//span[@class="count"]')
            e_v = e.text.partition('조회')[2].strip().replace(',', '')
            msg['view_count'] = self.get_num_from_str(e_v)
            # 댓글 수: 누르면 바로 댓글 창으로 가짐
            e_c = e_ab.find_element_by_xpath('//div[@class="ArticleTool"]//strong[@class="num"]')
            msg['num_comments'] = int(e_c.text.strip().replace(',', ''))
            # 좋아요
            try:
                e = e_ab.find_element_by_xpath('.//em[@class="u_cnt _count"]')
                msg['like'] = int(e.text.strip().replace('+', ''))
            except:
                msg['like'] = 0
            # 해쉬태그
            msg['tag_list'] = []
            for tag in self.driver.find_elements_by_xpath('//div[@class="ArticleTagList"]/ul/li'):
                msg['tag_list'].append(tag.text.strip())

            # 게시글 내용 :
            contents_xpath = './/div[@class="se-main-container"]' \
                             '|.//div[@class="ContentRenderer"]'
            e = e_ab.find_element_by_xpath(contents_xpath)
            contents = e.text.strip()
            msg['contents'] = contents

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 첨부파일 # 찾은 다음 하기
            inner_html = e_ab.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            if inner_html.find('tblForFl') > 0:
                for k, sub_k in enumerate(e_ab.find_elements_by_xpath('.//table[@id="tblForFl"]//a')):
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('data-href')
                    msg['attachment_url'].append(sub_k_url)
                    sub_k_name = sub_k.text.strip()
                    msg['attachment_name'].append(sub_k_name)

            # 댓글이 없는 경우
            if msg['num_comments'] == 0:
                return
            # 댓글
            msg['comment_list'] = []

            # 댓글 페이지가 있는 경우 : 없으면 댓글 페이지만 들어가면 된다.
            try:
                while True:
                    c_ple = e_ab.find_element_by_xpath('.//div[@class="ArticlePaginate"]')
                    e = c_ple.find_element_by_xpath('./button[@aria-pressed="true"]')
                    is_on = int(e.text.strip())
                    self.move_to_element(c_ple)
                    for ca, sub_ca in enumerate(c_ple.find_elements_by_xpath('.//button[@class]')):
                        if sub_ca.get_attribute('class') == 'btn type_next':
                            self.safe_click(sub_ca)
                            self.implicitly_wait(after_wait=1)
                            return
                        elif sub_ca.get_attribute('class') == 'btn type_end':
                            continue
                        elif sub_ca.get_attribute('class') == 'btn type_head':
                            continue
                        elif sub_ca.get_attribute('class') == 'btn type_prev':
                            continue
                        elif int(sub_ca.text.strip()) >= is_on:
                            self.safe_click(sub_ca)
                            self.get_comment(msg)
                            self.implicitly_wait(after_wait=1)
                    if msg['num_comments'] == len(msg['comment_list']):
                        break
            except:
                self.get_comment(msg)

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            self.driver.close()

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
            self.switch_to_window(0)

            count_a = 0
            while True:
                # 페이지 테이블 구하기
                e_s = self.driver.find_elements_by_xpath('//div[@class="_more_contents_event_base"]/ul/li')
                e_a = e_s[count_a]
                # 게시글 목록 캡쳐
                if count_a % 6 == 0:
                    # self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
                    s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{int(count_a / 6)}.png'
                    s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
                    # self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
                    self._screenshot(self.get_safe_path(s_shot))

                msg = {
                    'page': self.cur_page,
                    'row': count_a + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': None,
                    # 'site_board': self.config['params']['site']['site_board'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'article_id': None,
                    'create_ts': None,
                    'board_name': None,
                    'title': None,
                    'contents': None,
                    'tag_list': [],
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
                    # 1) 게시글 주소: article_url
                    e_url = e_a.find_element_by_xpath('.//div[@class="total_area"]/a')
                    a_url = e_url.get_attribute('href')
                    msg['article_url'] = a_url
                    # 2) 게시글 id : article_id  300143_55268553
                    v = a_url.partition('?')[0]
                    v_a = v.partition('.com/')[2].partition('/')[2]
                    # v_a = re.sub(r'[^0-9]', '', v)
                    msg['article_id'] = v_a
                    # 2) 제목: title
                    e = e_a.find_element_by_xpath('.//div[@class="total_area"]//a[@class="api_txt_lines total_tit"]')
                    msg['title'] = e.text.strip()
                    a = e.text.strip()
                    out_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", a)
                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    try:
                        self.switch_to_main_window()
                        # 커넥션 에러로 인해 새로 고침 추가
                        self.switch_to_window(1)
                        self.driver.refresh()
                        self.implicitly_wait(after_wait=1)
                        # 비공개글 회피로직
                        self.switch_to_window(1)
                        self.implicitly_wait(after_wait=2)
                        self.switch_to_iframe_by_name('cafe_main')
                        # 게시글 제목 비교 띄어쓰기가 단락으로 인해 차이가 있을 수 있음
                        e = self.driver.find_element_by_xpath('//div[@class="ArticleTitle"]//h3').text.strip()
                        in_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", e)
                        if not in_title.replace(' ', '').startswith(out_title.replace(' ', '')[:-3]):
                            self.logger.debug('비공개 게시글입니다.')
                            self.logger.debug(f'게시글의 url: {msg["article_url"]}')
                            self.logger.debug(f'게시글의 title: {msg["title"]}')
                            for _ in self.driver.window_handles:
                                if len(self.driver.window_handles) == 1:
                                    break
                                self.switch_to_window(1)
                                self.driver.close()
                            self.switch_to_main_window()
                            self.implicitly_wait(after_wait=1)
                            count_a += 1
                            continue
                    except:
                        self.logger.debug('삭제된 게시글입니다.')
                        self.logger.debug(f'게시글의 url: {msg["article_url"]}')
                        self.logger.debug(f'게시글의 title: {msg["title"]}')
                        for _ in self.driver.window_handles:
                            if len(self.driver.window_handles) == 1:
                                break
                            self.switch_to_window(1)
                            self.driver.close()
                        self.switch_to_main_window()
                        self.implicitly_wait(after_wait=1)
                        count_a += 1
                        continue
                    self.get_article(msg, count_a + 1)
                except Exception as err:
                    if 'article_id' not in msg:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'게시글의 url: {msg["article_url"]}')
                    self.logger.error(f'게시글의 title: {msg["title"]}')
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

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
                # bi = self.get_by_xpath('//div[@id="app"]//div/strong[@class="tit_guide"]')
                # # 비공개 게시글
                # if bi:
                #     self.logger.debug('멤버에게만 공개된 게시글 입니다.')
                #     continue
                self.move_to_element(e_a)
                count_a += 1

        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

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
                        urlretrieve(sub_e_url, article_img_p)
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
                    urlretrieve(cmt_url, cmt_img_f)
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
            #검색 전 스크린 샷 추가
            test = 'test'
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{test}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            # self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
            self._screenshot(self.get_safe_path(s_shot))
            self.search()
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
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
    with NaverTotalSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'naver_total.yaml'
    do_start(config_f=_config_f)
