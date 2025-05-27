"""
====================================
 :mod:`cafe/naver_total
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
#  * [2023/04/19]
#     - 삭제된 게시글 회피 로직 수정
#  * [2022/09/13]
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
        e = self.get_by_xpath('//button[@class="btn_search"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 전체 글 더 보기
        e = self.get_by_xpath('//div[@class="SectionSearchCombinations"]/div[2]/div')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 검색필터
        if self.config['params']['site']['search_filter'] in ['게시글', '제목']:
            search_filter = self.config['params']['site']['search_filter']
            e = self.get_by_xpath(f'//div[@label-text="{search_filter}"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        # 최신순
        e = self.get_by_xpath('//div[@class="SortTab articles_sort_tab"]/a[@class="sort_tab"]')
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
            # 카페에 main iframe으로 이동
            self.switch_to_iframe_by_name('cafe_main')
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

            e_ab = self.get_by_xpath('//div[@class="ArticleContentBox"]', timeout=1)

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

            # 게시글 내용 :
            comments_xpath = './/div[@class="se-main-container"]' \
                             '|.//div[@class="ContentRenderer"]'
            e = e_ab.find_element_by_xpath(comments_xpath)
            msg['contents'] = e.text.strip()

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
            # self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            # self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
            self._screenshot(self.get_safe_path(s_shot))

            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="SectionSearchArticles"]')
            # 최신순 클릭
            # e_tab = e.find_element_by_xpath('./div[2]/div/a[2]')
            # self.safe_click(e_tab)
            # self.implicitly_wait(after_wait=1)

            es = e.find_elements_by_xpath('./div[3]/ul/li')

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
                    e = self.get_by_xpath('//div[@class="SectionSearchArticles"]')
                    es = e.find_elements_by_xpath('./div[3]/ul/li')
                    ea = es[i]

                    # 1) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('.//div[@class="detail_area"]/a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('?art')[0].rpartition('com/')[2].replace('/','_')
                    msg['article_id'] = v
                    # 2) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 3) 제목: title
                    e_t = ea.find_element_by_xpath('.//div[@class="detail_area"]/a')
                    out_title = e_t.text.strip()
                    msg['title'] = e_t.text.strip()
                    # 4) 카페 이름: site_name
                    e = ea.find_element_by_xpath('.//span[@class="cafe_name"]')
                    msg['site_name'] = e.text.strip()

                    self.safe_click(e_url)
                    self.implicitly_wait(after_wait=1)
                    try:
                        # 커넥션 에러로 인해 새로 고침 추가
                        # self.switch_to_main_window()
                        # self.switch_to_window(1)
                        # self.driver.refresh()
                        # self.implicitly_wait(after_wait=1)
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
        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//div[@class="SectionPagination"]')
            ple = e.find_elements_by_xpath('./a')
            e_n = e.find_element_by_xpath('./a[@class="page_item isActive"]')
            now_page = e_n.text.strip()
            self.move_to_element(e)
            is_on = False

            for pa, sub_pa in enumerate(ple):
                if sub_pa.text.strip() == now_page:
                    is_on = True
                    continue
                elif is_on:
                    self.safe_click(sub_pa)
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
    with NaverTotalSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'naver_total.yaml'
    do_start(config_f=_config_f)
