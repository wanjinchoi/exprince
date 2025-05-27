"""
====================================
 :mod:`cafe/cafe_daum`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# * Jerry Chae
#
# Change Log
# --------
#
#  * [2024/08/16]
#     - 투표 결과보기 선택 및 득표수 수정
#  * [2024/08/13]
#     - 투표 게시글 수집 로직 추가
#  * [2024/08/05]
#     - 작성자 xpath 변경으로 인한 수정 작업
#  * [2024/07/30]
#     - 전체 스크린샷 방식 원복(스크롤 내리는 방식으로)
#  * [2024/07/29]
#     - 전체 이미지 캡쳐 방식 변경(불필요한 부분 제거)
#  * [2024/07/03]
#     - 투표 부분 xpath 수정
#  * [2024/07/02]
#     - site_sequence 필드 삭제
#  * [2024/07/02]
#     - site_name 필드 누락되어 추가
#  * [2024/06/25]
#     - 수집 성능 개선 모듈
#     - (DB 사용, 게시글 목록에 있는 URL 우선 수집, URL로 들어가서 수집)

################################################################################
import os
import re
import sys
import yaml
import json
import time
import shutil
import sqlite3
import random
import tarfile
import datetime
import traceback
import itertools
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from datetime import timedelta
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
from collections import OrderedDict


################################################################################

# 이미지 다운(403 에러 해결코드)
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)


################################################################################
class DaumCafeSearchAll(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DaumCafeSearchAll.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # for output
        self.url_list_all = []
        self.url_list_all_sum = []
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['search'],
             start_ts]
        )
        self.site_sequence = self.config['params']['site']['site_sequence']
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
        self.logger.info(f'Starting Daum Cafe Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:
            # 해당 iFrame으로 이동
            # self.switch_to_iframe_by_name('down')

            # # 검색 아이콘 누름
            # e = self.get_by_xpath('//button[@class="btn_search_top btn_search_open"]')
            # self.safe_click(e)

            # 검색어 입력
            e = self.get_by_xpath('//input[@class="tf_keyword inp_search"]')
            if self.config['params']['site']['search_complex']:
                self.send_keys(e, self.config['params']['site']['search_complex'] + Keys.ENTER)
            else:
                self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
            self.implicitly_wait(after_wait=1)

            # 카페글 최신 누름 : 'link_option date '
            e = self.get_by_xpath('//a[@class="link_option date "]')
            self.safe_click(e)


            # # 검색어 필터
            # e = self.get_by_xpath('//select[@name="item"]')
            # e_s = e.find_elements_by_xpath('./option')
            # for i, e_filter in enumerate(e_s):
            #     if e_filter.text.find(self.config['params']['site']['search_filter']) >= 0:
            #         self.safe_click(e_filter)
            #         self.implicitly_wait(after_wait=1)
            #         e = self.get_by_xpath('//img[@alt="검색"]')
            #         self.safe_click(e)
            #         self.implicitly_wait(after_wait=1)
            #         break
        finally:
            # self.switch_from_iframe()
            pass

    # ==========================================================================
    def get_comments(self, msg):
        try:
            # self.switch_to_iframe_by_name('down')
            try:
                e = self.get_by_xpath('//ul[@class="list_comment"]')
            except:
                return
            comments = e.find_elements_by_xpath('./li[@class]')
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
                # 대댓글?
                is_reply = cmt_e.get_attribute('data-parseq') != '0'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                is_deleted = False
                # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find('opt_more_g') > 0:
                    e = cmt_e.find_element_by_xpath('.//div[@class="opt_more_g"]')
                    cmt['nickname'] = e.text.strip()
                else:
                    is_deleted = True
                if not is_deleted:
                    # 댓글 내용
                    e = cmt_e.find_element_by_xpath('.//div[@class="box_post"]')
                    self.move_to_element(e)
                    if i == 0:
                        cmt_contents = e.text.strip().replace('첫댓글 ', '')
                    else:
                        cmt_contents = e.text.strip()
                    cmt['contents'] = cmt_contents
                    # 댓글에 이모티콘 혹은 이미지
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    try:
                        img_elements = e.find_element_by_tag_name('img')
                    except:
                        img_elements = False
                    if img_elements:
                        # 댓글 이미지의 경우 축소되어있는경우 클릭해줘야함.
                        # if inner_html.find("img_thumb zoom_in") > 0:
                        #     e.find_element_by_xpath('//img[@class="img_thumb zoom_in"]').click()
                        #     self.implicitly_wait(after_wait=1)
                        img_e = e.find_element_by_tag_name('img')
                        cmt['comment_img_url'].append(img_e.get_attribute('src'))
                        # 이모티콘은 이미지를 가져올수 없음. 바로 캡쳐
                        cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{cmt["comment_id"] + "_0"}.png')
                        try:
                            urlretrieve(cmt['comment_img_url'], cmt_img_f)
                        except:
                            img_e.screenshot(cmt_img_f)
                        cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                    # 댓글 작성 시각
                    e = cmt_e.find_element_by_xpath('.//span[@class="txt_date"]')
                    create_ts = e.text.strip()
                    if len(create_ts.split()) == 1:
                        doday_ts = datetime.datetime.today().strftime("%Y.%m.%d")
                        create_ts = f'{doday_ts[2:]} ' + create_ts
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                else:
                    cmt['comment_id'] = None
                    cmt['contents'] = cmt_e.text.strip()
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    cmt['nickname'] = ""
                    # 댓글 작성 시각 작성자와 운영자만 보는 경우에도 가져올수 있음
                    inner_html = cmt_e.get_attribute('innerHTML')
                    if inner_html.find('txt_date') > 0:
                        e = cmt_e.find_element_by_xpath('.//span[@class="txt_date"]')
                        create_ts = e.text.strip()
                        if len(create_ts.split()) == 1:
                            doday_ts = datetime.datetime.today().strftime("%Y.%m.%d")
                            create_ts = f'{doday_ts[2:]} ' + create_ts
                        cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    else:
                        cmt['create_ts'] = ""
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                if len(msg['comment_list']) >= msg['num_comments']:
                    break
        finally:
            self.switch_to_iframe_by_name('down')

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)
        # self.driver.find_element_by_xpath('//div[@class="primary_content"]').screenshot(f)

    # ==========================================================================
    def get_article(self, msg, ndx):
        click_count = 1
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            # 새로운 탭으로 이동
            self.switch_to_window(1)
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_iframe_by_name('down')
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                # 불필요한 이미지 제거
                self.remove_html()
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # e_body.screenshot(msg_capture_f)
                # self._screenshot(msg_capture_f)
                self.full_screenshot(msg_capture_f)
            # 게시글 URL로 HTML 소스 가져오기
            article_source = self.driver.page_source
            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(article_source, 'html.parser')
            # 사이트명
            site_name = soup.find('div', class_='cafename')
            msg['site_name'] = site_name.text.strip()
            # 작성자
            author = soup.find('a', class_='link_item')
            if not author:
                top_author = soup.find('div', class_='primary_content')
                author = top_author.find('span', class_='txt_name')
                msg['author'] = author.text.strip()
            else:
                msg['author'] = author.get('data-nickname')
            middle = soup.find('div', class_='primary_content')
            # 게시글 제목
            e = middle.find('strong', class_='tit_info')
            title = e.text.strip()
            etc = middle.find('span', class_='txt_head_cont')
            if etc:
                etc_t = etc.text.strip()
                msg['title'] = title.replace(etc_t, '').lstrip()
            else:
                msg['title'] = title
            # 게시판 이름
            e = middle.find('a', class_='txt_subhead')
            msg['board_name'] = e.text.strip()
            # 추천 : "추천 0"
            e = middle.find_all('span', class_='txt_item')[0]
            msg['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 조회수 : "조회 93"
            e = middle.find_all('span', class_='txt_item')[1]
            msg['view_count'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 작성일시
            e = middle.find_all('span', class_='txt_item')[2]
            create_ts = e.text.strip()
            msg['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
            # 댓글수
            e = middle.find_all('span', class_='txt_item')[3]
            msg['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 본문
            e = middle.find('div', class_='board_post tx-content-container')
            msg['contents'] = e.text.strip()
            # 투표
            if len(e.find_all('div', class_='figure-poll')) > 0:
                self.vote_data = True
                self.get_vote_data(msg)
            else:
                pass
            self.switch_to_iframe_by_name('down')
            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = middle.find('div', class_='board_post tx-content-container')
            # 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if len(inner_html.find_all('img', class_='txc-image')) > 0:
                # for sub_e in e.find_elements_by_xpath('.//img[@class="txc-image"]'):
                for j, sub_e in enumerate(inner_html.find_all('img', class_='txc-image')):
                    sub_e_url = sub_e.get('src')
                    msg['image_url_list'].append(sub_e_url)

            # 댓글 : 댓글이 없는 경우 있음
            if msg['num_comments'] <= 0:
                return
            msg['comment_list'] = []

            # 코멘트 페이징이 있는 경우
            e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
            coments_es = e.find_elements_by_xpath('./ul/li')
            if coments_es[1].get_attribute('class') == 'active':
                self.get_comments(msg)
                return
            # 1을 클릭하기위함.
            self.safe_click(coments_es[1])
            self.implicitly_wait(after_wait=1)
            click_count += 1
            while True:
                e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
                coments_es = e.find_elements_by_xpath('./ul/li')
                is_next = False
                for coments_e in coments_es:
                    if coments_e.text.find('다음') >= 0:
                        is_next = False
                        break
                    elif coments_e.get_attribute('class') == 'active':
                        self.get_comments(msg)
                        is_next = True
                        continue
                    if is_next:
                        self.safe_click(coments_e)
                        self.implicitly_wait(after_wait=1)
                        click_count += 1
                        break
                if not is_next:
                    break
            # 속도 개선전 코드
            # for page_cnt in range(1, 11):
            #     self.switch_to_iframe_by_name('down')
            #     e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
            #     b_page_found = False
            #     for k, cp_e in enumerate(e.find_elements_by_xpath('.//a[@class="page-link"]')):
            #         if cp_e.text.strip() == str(page_cnt):
            #             b_page_found = True
            #             self.safe_click(cp_e)
            #             self.implicitly_wait()
            #             self.get_comments(msg)
            #             break
            #     if not b_page_found:
            #         if page_cnt == 1:
            #             i = self.get_comments(msg)
            #         break
            # # 다음은 디버깅 용도!
            # if len(msg['comment_list']) != msg['num_comments']:
            #     j = i
        except Exception as err:
            raise
        finally:
            # 뒤로 돌아감 댓글
            # for _ in range(click_count):
            #     self.driver.back()
            self.driver.close()
            self.switch_to_main_window()

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
        except:
            return False

    # ==========================================================================
    def article_ids_from_web(self):
        # 게시글 목록 30개 까지만 가져옴
        # res = requests.get(self.driver.current_url)
        # 페이지의 HTML 소스 가져오기
        html_source = self.driver.page_source
        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(html_source, 'html.parser')
        ul_list = soup.find_all('ul', class_='list_scafe')
        li_items = [li for ul in ul_list for li in ul.find_all('li')]
        li_url_items = [a for ul in li_items for a in ul.find_all('a', class_='link_url')]
        self.url_list = [tag.get('href') for tag in li_url_items]
        last_time = [a.get_text() for ul in li_items for a in ul.find_all('span', class_='info_scafe')][-1]
        self.last_time = last_time.strip()
        return self.url_list, self.last_time

    # ==========================================================================
    def get_article_id_from_url(self):

        pattern = r"https://cafe\.daum\.net/([^/]+)/[^/]+/([^?]+)"
        article_ids = [(url, re.search(pattern, url).group(1) + '_' + re.search(pattern, url).group(2)) for url in
                       self.url_list_all_sum]
        return article_ids

    # ==========================================================================
    def article_ids_from_db(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('compare_data.db')
        c = conn.cursor()

        # SQL 쿼리문 실행
        start_date = '2024-04-04 00:00:00'
        end_date = '2024-04-04 14:00:00'
        c.execute('''SELECT * FROM compare 
                            WHERE collection_date BETWEEN ? AND ?
                            LIMIT 1000''', (start_date, end_date))

        # 결과 가져오기
        rows = c.fetchall()

        # 결과 출력
        # for row in rows:
        #     print(row)

        # 연결 종료
        conn.close()

        # article_id만 추출하여 리스트로 만들기
        known_ids = [row[0] for row in rows]

        return known_ids

    # ==========================================================================
    def load_latest_article_ids(self, site_sequence):
        try:
            keyword = self.config['params']['site']['search']
            # SQLite3 데이터베이스 연결 - 시나리오 순번(bot 변수)
            conn = sqlite3.connect(f'C:\\work\\voc_data\\logs\\upload2_DB\\{site_sequence}.db')
            c = conn.cursor()

            # 현재 시간 구하기
            current_time = datetime.datetime.now()
            current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

            # 1일 전 날짜 구하기 strp
            previous_day = current_time - timedelta(days=1)
            previous_day_str = previous_day.strftime('%Y-%m-%d %H:%M:%S')

            # DB 쿼리문
            query = """
                SELECT *
                FROM Articles
                WHERE collection_date >= ? AND keyword = ?
                ORDER BY collection_date DESC
                LIMIT 1000;
            """
            c.execute(query, (previous_day_str, keyword))

            # 결과 가져오기
            rows = c.fetchall()
            self.logger.info(f'DB 쿼리문: {query}\n 조회한 날짜: {previous_day_str} ~ {current_time_str}, 키워드: {keyword}')

            # 연결 종료
            c.close()
            conn.close()

            # article_id만 추출하여 리스트로 만들기
            article_ids = [row[0] for row in rows]

            return article_ids

            # 메모장 조회
            # files = glob.glob(f'{keyword}*.txt')
            # if files:
            #     latest_file = max(files, key=os.path.getctime)
            #     with open(latest_file, 'r') as f:
            #         return f.read().splitlines()
            # return []
        except Exception as err:
            self.logger.error(err)

    # ==========================================================================
    def get_page(self):
        try:
            # 검색 결과 존재 여부 확인
            try:
                e = self.get_by_xpath('//ul[@class="list_scafe"]')
            except:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return
            current_url = self.driver.current_url
            # 수집 범위 날짜 계산(재수집을 진행할 경우 수정 필요)
            end_date = datetime.datetime.now() - timedelta(days=1)
            end_date_f = end_date.strftime("%Y.%m.%d")
            end_date_c = datetime.datetime.strptime(end_date_f, "%Y.%m.%d")
            # 게시글 목록 수집
            for i in range(50):
                page_url = current_url + '&p=' + f'{i+1}'
                self.driver.get(page_url)
                self.implicitly_wait(after_wait=0.5)
                try:
                    e = self.get_by_xpath('//ul[@class="list_scafe"]')
                    self.logger.info(f'cnt_page is {i+1}')
                    # 네이버 게시글 목록 URL, article_id 추출
                    self.article_ids_from_web()
                    self.url_list_all.append(self.url_list)
                    if datetime.datetime.strptime(self.last_time, "%Y.%m.%d") <= end_date_c:
                        self.logger.info(f'last_article_create_ts is {self.last_time} - older than {end_date_c}')
                        break
                except:
                    self.logger.info(f'cnt_page is end')
                    break
            # 수집된 전체 url목록에서 article_id 추출
            self.url_list_all_sum = list(itertools.chain(*self.url_list_all))
            new_ids = list(self.get_article_id_from_url())
            # new_ids를 OrderedDict로 변환하여 순서 유지
            ordered_new_ids = OrderedDict(new_ids)
            # 게시글 목록 게시글 ID- 로그로만 사용
            new_article_ids = list(ordered_new_ids.values())
            # self.logger.info(f'all_id_list is {new_article_ids}')

            # DB 파일 존재 여부 확인
            if os.path.isfile(f'C:\\work\\voc_data\\logs\\upload2_DB\\{self.site_sequence}.db'):
                # DB에서 키워드 별 article_id select
                known_ids = set(self.load_latest_article_ids(self.site_sequence))
                # # new_ids에서 article_id만 뽑기
                # new_article_ids = set(article_id for _, article_id in new_ids)
                # 중복되지 않은 article_id 찾기
                unique_article_ids = [article_id for article_id in ordered_new_ids.values() if
                                      article_id not in known_ids]
                unique_data = [(url, article_id) for url, article_id in ordered_new_ids.items() if
                               article_id in unique_article_ids]
                # new_ids, knwon_ids, unique_aritles 로그 찍기
                self.logger.info(
                    f'게시글 목록: {len(new_ids)}개, DB 조회 데이터: {len(known_ids)}개, 중복되지 않은 게시글:{len(unique_article_ids)}개')
                # self.logger.info(
                #     f'게시글 목록: {new_article_ids}\n DB 조회 데이터: {known_ids}\n 중복되지 않은 게시글 ID:{unique_article_ids}')
                # # 중복되지 않은 article_id 찾기
                # unique_article_ids = new_article_ids - known_ids
                # 중복되지 않은 article_id에 해당하는 데이터 추출 - 리스트 순서 바뀜 -> 딕셔너리, append
            else:
                unique_data = [(url, article_id) for url, article_id in ordered_new_ids.items()]
                self.logger.info('There is no DB in this PC')
            count_a = 0
            for url, article_id in unique_data:
                msg = {
                    'page': self.cur_page,
                    'row': count_a + 1,
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
                    'vote': [],
                }
                try:
                    # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
                    delay_a = random.uniform(
                        self.config['params']['site']['delay']['article']['min'],
                        self.config['params']['site']['delay']['article']['max'],
                    )
                    time.sleep(delay_a)
                    self.vote_data = False
                    msg['article_id'] = article_id
                    msg['article_url'] = url
                    c_start_time = time.time()
                    # 실제 수집
                    self.driver.execute_script(f"window.open('{url}');")
                    self.get_article(msg, count_a + 1)
                    c_end_time = time.time()

                    collections_time = c_end_time - c_start_time
                    self.logger.info(f'게시글 수집 시간: {collections_time}, article_id[{msg["article_id"]} ]')
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    continue

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
                if self.vote_data:
                    if self.vote_not_end:
                        self.store_vote_data(msg)
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
                count_a += 1

        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            # # "카페 메인 (cafe_main)" iFrame으로 이동
            # self.switch_to_iframe_by_name('down')
            # 페이지 목록
            next_page_str = str(self.cur_page + 1)
            ple = self.get_by_xpath('//span[@class="paging_inner"]', timeout=2)
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == next_page_str:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
        except Exception as err:
            self.logger.error(f'Cannot find Result!')
            self.is_done = True
        finally:
            # self.switch_from_iframe()
            pass

    # ========================================================================
    def remove_html(self):
        try:
            # 하당 광고창
            under_ad = self.get_by_xpath("//div[@id='ad_wrapper']")
            # 왼쪽 메뉴창
            left_menu = self.get_by_xpath("//div[@class='menuBox']")
            # 게시글 목록
            article_list = self.get_by_xpath("//div[@class='cont_boardlist article_more_board']")

            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", under_ad)
            self.driver.execute_script("arguments[0].remove();", left_menu)
            self.driver.execute_script("arguments[0].remove();", article_list)

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass

    # ==========================================================================
    def store_vote_data(self, msg):
        try:
            vote_data_path = r'C:\work\voc_data\logs\vote_db'
            if not os.path.exists(vote_data_path):
                os.mkdir(vote_data_path)

            user_type = self.config['params']['site']['user_type']
            site = self.config['params']['site']['site']
            site_name = self.config['params']['site']['site_name']
            channel = self.config['params']['site']['channel']
            search_type = self.config['params']['site']['search_type']
            service = self.config['params']['site']['service']
            article_id = msg['article_id']
            keyword = self.config['params']['site']['search']
            site_num = self.config['params']['site']['site_number']
            article_url = msg['article_url']
            # 현재 시간을 수집된 날짜로 사용
            collection_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # SQLite 데이터베이스 연결 및 커서 생성
            conn = sqlite3.connect(r'C:\work\voc_data\logs\vote_db' + '/' + 'vote_data.db')
            cursor = conn.cursor()
            # 게시글 테이블 생성
            cursor.execute('''
                    CREATE TABLE IF NOT EXISTS vote_Articles (
                        user_type TEXT,
                        site TEXT,
                        site_name TEXT,
                        channel TEXT,
                        search_type TEXT,
                        service TEXT,
                        article_id TEXT,
                        keyword TEXT,
                        site_num TEXT,
                        article_url TEXT,
                        collection_date TEXT,
                        PRIMARY KEY (keyword, article_id)
                    )
                ''')

            # 데이터베이스에 게시글 추가 또는 업데이트
            cursor.execute(
                "INSERT OR IGNORE INTO vote_Articles (user_type, site, site_name, channel, search_type, service, article_id, keyword, site_num, article_url, collection_date) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_type, site, site_name, channel, search_type, service, article_id, keyword, site_num, article_url, collection_date))
            conn.commit()
            self.logger.info("투표 게시글 저장 완료.")

        except Exception as err:
            self.logger.error(f'get_vote_data: error: {str(err)}')
            raise

    # ==========================================================================
    def get_vote_data(self, msg):
        try:
            self.vote_not_end = True
            msg['vote'] = []
            vote_list = self.driver.find_elements_by_xpath('//div[@class="figure-poll"]')
            for i, vote_e in enumerate(vote_list):
                # 딜레이
                delay_c = random.uniform(
                    self.config['params']['site']['delay']['comment']['min'],
                    self.config['params']['site']['delay']['comment']['max'],
                )
                time.sleep(delay_c)
                vote = {
                    'vote_id': i,
                    'vote_title': None,
                    'vote_start': None,
                    'vote_end': None,
                    'vote_involve_cnt': None,
                    'vote_complete': None,
                    'vote_item': [],
                }
                self.move_to_element(vote_e)
                try:
                    e = vote_e.find_element_by_xpath('.//iframe[@id="pollFrame"]')
                    self.driver.switch_to_frame(e)
                except:
                    self.logger.error(f'투표 내용이 사라짐 - pass')
                    self.switch_to_iframe_by_name('down')
                    return
                # 투표 종료 여부 확인
                try:
                    try:
                        # 결과 보기 선택
                        re_click = self.get_by_xpath('//div[@class="group_btn"]/button[@class="btn_vote activated"]')
                        self.safe_click(re_click)
                        self.implicitly_wait(after_wait=1)
                    except:
                        pass
                    vote_status = self.get_by_xpath('//span[@class="txt_noti"]')
                    vote['vote_complete'] = False
                    # 투표 제목 수집
                    vo_title = self.get_by_xpath('html//div[@class="title_vote"]/strong[@class="tit_subject"]')
                    vote['vote_title'] = vo_title.text.strip()
                    vote_involve_cnt = self.get_by_xpath('html//div[@class="title_vote"]/p[@class="txt_subject_noti"]')
                    vote['vote_involve_cnt'] = vote_involve_cnt.text.strip().split(', ')[1].replace(' 참여', '').replace('명', '')
                    vote_date = self.get_by_xpath('//p[@class="txt_info"]/span[@class="txt_date"]').text.strip()
                    vote_date_s = vote_date.split(' ~ ')[0]
                    vote['vote_start'] = datetime.datetime.strptime(vote_date_s, '%Y-%m-%d').strftime('%Y.%m.%d')
                    vote_date_e = vote_date.split(' ~ ')[1]
                    vote['vote_end'] = datetime.datetime.strptime(vote_date_e, '%Y-%m-%d').strftime('%Y.%m.%d')
                    # 투표 항목 & 결과 수집
                    re_list = self.driver.find_elements_by_xpath('//div[@class="box_vote"]/ul/li')
                    for j, vote_list_a in enumerate(re_list):
                        vote_item = {
                            'vote_num': j,  # 투표항목 넘버링
                            'vote_text': None,  # 투표항목
                            'vote_cnt': None,  # 투표 득표수
                            'vote_rate': None,  # 투표 득표퍼센트
                        }
                        e_a = vote_list_a.text.strip()
                        vote_item['vote_text'] = e_a.split('\n')[0]
                        vote_item['vote_cnt'] = e_a.split('\n')[1].split(' ')[1].replace('(', '').replace(')', '').replace('표', '')
                        vote_item['vote_rate'] = e_a.split('\n')[1].split(' ')[0].replace('%', '')
                        vote['vote_item'].append(vote_item)
                except:
                    self.vote_not_end = False
                    vote['vote_complete'] = True
                    # 투표 제목 수집
                    vo_title = self.get_by_xpath('html//div[@class="title_vote"]/strong[@class="tit_subject"]')
                    vote['vote_title'] = vo_title.text.strip()
                    vote_involve_cnt = self.get_by_xpath('html//div[@class="title_vote"]/p[@class="txt_subject_noti"]')
                    vote['vote_involve_cnt'] = vote_involve_cnt.text.strip().split(', ')[1].replace(' 참여', '').replace('명', '')
                    vote_date = self.get_by_xpath('//p[@class="txt_info"]/span[@class="txt_date"]').text.strip()
                    vote_date_s = vote_date.split(' ~ ')[0]
                    vote['vote_start'] = datetime.datetime.strptime(vote_date_s, '%Y-%m-%d').strftime('%Y.%m.%d')
                    vote_date_e = vote_date.split(' ~ ')[1]
                    vote['vote_end'] = datetime.datetime.strptime(vote_date_e, '%Y-%m-%d').strftime('%Y.%m.%d')
                    # 투표 항목 & 결과 수집
                    re_list = self.driver.find_elements_by_xpath('//div[@class="box_vote"]/ul/li')
                    for j, vote_list_a in enumerate(re_list):
                        vote_item = {
                            'vote_num': j,  # 투표항목 넘버링
                            'vote_text': None,  # 투표항목
                            'vote_cnt': None,  # 투표 득표수
                            'vote_rate': None,  # 투표 득표퍼센트
                        }
                        e_a = vote_list_a.text.strip()
                        vote_item['vote_text'] = e_a.split('\n')[0]
                        vote_item['vote_cnt'] = e_a.split('\n')[1].split(' ')[1].replace('(', '').replace(')', '').replace('표', '')
                        vote_item['vote_rate'] = e_a.split('\n')[1].split(' ')[0].replace('%', '')
                        vote['vote_item'].append(vote_item)
                # 투표 목록에 추가
                msg['vote'].append(vote)
                self.switch_to_iframe_by_name('down')
        except Exception as err:
            self.logger.error(f'get_vote_data: error: {str(err)}')
            raise

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
                        self.logger.info(f'save_img: {j}.png : retry{count+1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

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
        if 'site_sequence' in self.output['config']['params']['site']:
            del self.output['config']['params']['site']['site_sequence']
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
            self.get_page()
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 1
        finally:
            # print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with DaumCafeSearchAll(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'daum_total.yaml'
    do_start(config_f=_config_f)
