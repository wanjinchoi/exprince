"""
====================================
 :mod:`dcinside`
====================================
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# Change Log
# --------
#  * [2024/11/07]
#     - 게시글이 삭제되거나 열리지 않아 실패시 재시도 할 수있도록 수정
#  * [2024/08/23]
#     - 게시글 목록의 중복된 게시글 중복 처리
#  * [2024/08/09]
#     - 제외 게시판 추가(배드민턴, 2024 파리 올림픽)
#  * [2024/08/06]
#     - 전체 스크린샷 방식 변경(제목, 본문, 댓글)
#  * [2024/07/17]
#     - 본문 이미지의 포함된 텍스트 제거
#  * [2024/07/16]
#     - 게시글 내 이미지의 이미지 순서 버튼 제거(클릭)
#  * [2024/07/15]
#     - 게시글 본문 이미지, 비디오 수집 로직 변경(XPath)
#     - 댓글 비디오, 동영상 수집 로직 변경
#     - 게시글 내에 video(동영상) 태그 수집 추가
#     - 중복 제거용 DB 파일 없으면 생성
#  * [2024/05/13]ㄹ
#     - starting
#     - 이전 변경 이력은 dcinside.py 참고

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
import sqlite3
import datetime
import traceback
import requests
import binascii
import pandas as pd
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from bs4 import BeautifulSoup
from collections import OrderedDict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
class DCinsideSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DCinsideSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # self.config['params']['site']['search'] = self.config['params']['site']['search'].strip()

        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['search'],
             start_ts]
        )
        self.log_d = r'C:\work\voc_data\logs\upload2_DB'
        self.keyword = self.config['params']['site']['search']
        self.site_sequence = self.config['params']['site']['site_sequence']
        self.config['target']['folder'] += '/' + folder_name
        self.is_done = False
        self.cur_page = 0
        self.except_alert_list = self.config['params']['site']['except_alert_list'].split(',')
        del self.config['params']['site']['except_alert_list']
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
        self.logger.info(f'Starting DCinside Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def check_cmt_create(self, cmt_c):
        create_pattern = re.compile(r'^\d{4}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}$')

        return bool(create_pattern.match(cmt_c))

    # ==========================================================================
    def save_e_img(self, re_img, msg, cmt):
        cmt_img_f = self.get_safe_path(
            self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"]+"_0"}.png')
        re_img.screenshot(cmt_img_f)

    # ==========================================================================
    def get_comments(self, msg):
        try:
            comments_e = self.get_by_xpath('//ul[@class="cmt_list"]')
            comments = comments_e.find_elements_by_xpath('./li')
            parent_comment_id = None
            for i, cmt_e in enumerate(comments):
                comments_es = self.get_by_xpath('//ul[@class="cmt_list"]')
                comments_e = comments_es.find_elements_by_xpath('./li')
                cmt_e = comments_e[i]
                # 광고
                if cmt_e.get_attribute('class') == 'ub-content dory':
                    pass
                else:
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
                    delay_c = random.uniform(
                        self.config['params']['site']['delay']['comment']['min'],
                        self.config['params']['site']['delay']['comment']['max'],
                    )
                    time.sleep(delay_c)

                    # 댓글 연도 구하기
                    a_ts = msg['create_ts'].split('.')

                    # 대댓글인지 확인
                    inner_html = cmt_e.get_attribute('innerHTML')
                    if inner_html.find('reply show') > 0:
                        re_cmts_e = cmt_e.find_element_by_xpath('.//ul[@class="reply_list"]')
                        re_cmts = re_cmts_e.find_elements_by_xpath('./li')
                        for j, re_cmt in enumerate(re_cmts):
                            cmt = {
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
                            re_s = cmt_e.find_elements_by_xpath('.//ul[@class="reply_list"]/li')
                            re_cmt = re_s[j]
                            # 댓글 id
                            e = re_cmt.find_element_by_xpath('.//div[@class="reply_info clear"]')
                            self.move_to_element(e)
                            cmt['comment_id'] = e.get_attribute('data-no')
                            # 댓글 작성자 닉네임
                            e = re_cmt.find_element_by_xpath('.//div[@class="cmt_nickbox"]')
                            cmt['nickname'] = e.text.strip()

                            # 삭제된 댓글
                            e_del_reply = cmt_e.get_attribute('innerHTML')
                            if e_del_reply.find('del_reply') > 0:
                                e = cmt_e.find_element_by_xpath('.//p[@class="del_reply"]')
                                cmt['contents'] = e.text.strip()
                                cmt['comment_id'] = None
                            elif inner_html.find('voice_wrap') > 0:
                                cmt['contents'] = '보이스리플'
                                # 댓글 작성 시간
                                e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                cmt_c = e.text.strip()
                                if self.check_cmt_create(cmt_c):
                                    cmt['create_ts'] = cmt_c
                                else:
                                    cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                            else:
                                # # 댓글 작성 시간
                                # e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                # cmt_c = e.text.strip()
                                # if self.check_cmt_create(cmt_c):
                                #     cmt['create_ts'] = cmt_c
                                # else:
                                #     cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                                # 댓글 내용 text
                                e = re_cmt.find_element_by_xpath('.//div[@class="clear cmt_txtbox"]')
                                cmt['contents'] = e.text.strip()
                                # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                                media_elements = e.find_elements_by_xpath('.//video | .//img')

                                # media_elements 리스트에서 src 속성을 가진 태그를 처리
                                for media_element in media_elements:
                                    src = media_element.get_attribute('src') or media_element.get_attribute('data-src')
                                    if src:
                                        cmt['comment_img_url'].append(src)
                                        self.save_e_img(media_element, msg, cmt)
                                        cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')
                                # inner_html = e.get_attribute('innerHTML')
                                # if inner_html.find('video') > 0:
                                #     re_img = e.find_element_by_tag_name('video')
                                #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                #     self.save_e_img(re_img, msg, cmt)
                                #     cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                                # elif inner_html.find('img') > 0:
                                #     re_img = e.find_element_by_tag_name('img')
                                #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                #     self.save_e_img(re_img, msg, cmt)
                                #     cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                                # 댓글 작성 시간
                                e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                cmt_c = e.text.strip()
                                if self.check_cmt_create(cmt_c):
                                    cmt['create_ts'] = cmt_c
                                else:
                                    cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                            # 댓글 목록에 추가
                            msg['comment_list'].append(cmt)
                    else:
                        cmt['is_reply'] = False
                        # 댓글 id
                        e = cmt_e.find_element_by_tag_name('div')
                        self.move_to_element(e)
                        cmt['comment_id'] = e.get_attribute('data-no')
                        # 댓글 부모 대댓글이 아니면 공백
                        parent_comment_id = cmt['comment_id']
                        # 댓글 작성자 닉네임
                        e = cmt_e.find_element_by_xpath('.//div[@class="cmt_nickbox"]')
                        cmt['nickname'] = e.text.strip()

                        # 삭제된 댓글
                        e_del_reply = cmt_e.get_attribute('innerHTML')
                        if e_del_reply.find('del_reply') > 0:
                            e = cmt_e.find_element_by_xpath('.//p[@class="del_reply"]')
                            cmt['contents'] = e.text.strip()
                            cmt['comment_id'] = None
                        elif inner_html.find('voice_wrap') > 0:
                            cmt['contents'] = '보이스리플'
                            # 댓글 등록 시간
                            e = cmt_e.find_element_by_xpath('.//span[@class="date_time"]')
                            cmt_c = e.text.strip()
                            if self.check_cmt_create(cmt_c):
                                cmt['create_ts'] = cmt_c
                            else:
                                cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                        else:
                            # 댓글 작성 시간
                            # e = cmt_e.find_element_by_xpath('.//span[@class="date_time"]')
                            # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                            # 댓글 내용 text
                            e = cmt_e.find_element_by_xpath('.//div[@class="clear cmt_txtbox btn_reply_write_all"]|.//div[@class="clear cmt_txtbox"]')
                            cmt['contents'] = e.text.strip()
                            # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                            media_elements = e.find_elements_by_xpath('.//video | .//img')

                            # media_elements 리스트에서 src 속성을 가진 태그를 처리
                            for media_element in media_elements:
                                src = media_element.get_attribute('src') or media_element.get_attribute('data-src')
                                if src:
                                    cmt['comment_img_url'].append(src)
                                    self.save_e_img(media_element, msg, cmt)
                                    cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')
                            # inner_html = e.get_attribute('innerHTML')
                            # if inner_html.find('video') > 0:
                            #     re_img = e.find_element_by_tag_name('video')
                            #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                            #     self.save_e_img(re_img, msg, cmt)
                            #     cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                            # elif inner_html.find('img') > 0:
                            #     re_img = e.find_element_by_tag_name('img')
                            #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                            #     self.save_e_img(re_img, msg, cmt)
                            #     cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')

                            # 댓글 등록 시간
                            e = cmt_e.find_element_by_xpath('.//span[@class="date_time"]')
                            cmt_c = e.text.strip()
                            if self.check_cmt_create(cmt_c):
                                cmt['create_ts'] = cmt_c
                            else:
                                cmt['create_ts'] = a_ts[0] + '.' + cmt_c

                        # 댓글 목록에 추가
                        msg['comment_list'].append(cmt)
                    self.logger.info(f'   [{i + 1}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            raise

    # ========================================================================
    def remove_html(self):
        try:
            # 게시글 리스트
            article_list = self.get_by_xpath('//div[@class="listwrap clear"]')
            self.driver.execute_script("arguments[0].remove();", article_list)

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass

    # ==========================================================================
    def _screenshot(self, f):
        # 불필요한 부분 제거
        self.remove_html()
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        self.driver.find_element_by_xpath('//main[@id="container"]').screenshot(f)

    # ==========================================================================
    def get_article(self, msg, count):
        try:
            self.logger.info(f'Page[{self.page_count}:{count}],article_id[{msg["article_id"]}], 제목[{msg["title"]}]')
            self.switch_to_window(1)
            if self.config['params']['site']['capture_article']:
                # 캡처할때 광고가 따라와서 꺼주는게 보기 좋음 광고가 올라오는 시간이 좀 있음.
                # e = self.get_by_xpath('//a[@id="wif_adx_banner_close"]')
                # self.safe_click(e)
                try:
                    # 이미지 순서 버튼 on/off
                    btn = self.driver.find_elements(By.XPATH, "//button[@onclick='img_numbering_toggle(this, 3, event)']")
                    # img 순서
                    img_index = self.driver.find_elements(By.XPATH, "//span[@class='num']")
                    # 버튼 클릭해서 끔
                    self.driver.execute_script("img_numbering_toggle(arguments[0], 3, new Event('click'));", btn)
                    # 이미지 수 만큼 진행
                    for btn, img_index in zip(btn, img_index):
                        # 이미지 순서 버튼 제거
                        self.driver.execute_script("arguments[0].remove();", btn)
                        # 이미지 순서 텍스트 제거
                        self.driver.execute_script("arguments[0].remove();", img_index)
                    # 메시지 박스가 본문 내용에 포함되어 제거(위에 제거 로직 진행 후에 생김)
                    msg_box = self.get_by_xpath('//div[@id="dcimg_num_tip"]')
                    self.driver.execute_script("arguments[0].remove();", msg_box)
                except:
                    pass
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot(msg_capture_f)

            # 게시글 URL로 HTML 소스 가져오기
            article_source = self.driver.page_source
            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(article_source, 'html.parser')
            # 상단
            high_e = soup.find('div', class_='gall_writer ub-writer')
            # 작성자
            author = high_e.find('span', class_='nickname')
            msg['author'] = author.text.strip()

            # 조회수
            view = high_e.find('span', class_='gall_count')
            msg['view_count'] = int(view.text.split()[1].replace(',', ''))
            # 추천수
            like = high_e.find('span', class_='gall_reply_num')
            msg['like'] = int(like.text.split()[1].replace(',', ''))

            # # 본문(write_div 아래 모든 형식이 있슴.)
            content_e = soup.find('div', class_='write_div')
            msg['contents'] = content_e.text.strip()

            # 매니저 차단 이미지 활성화(활성화 안하면 이미지 에러 발생)
            block_img = content_e.find('button', class_='btn_img_block block_img_e')
            if block_img:
                # beautifulSoup로 가져오면 Click이 안됨. XPath 경로로 클릭
                img_c = self.get_by_xpath('//button[@class="btn_img_block block_img_e"]')
                self.safe_click(img_c)
                # 클릭하는 경우 HTML 변경돼서 소스 다시 가져옴
                article_source = self.driver.page_source
                # BeautifulSoup을 사용하여 HTML 파싱
                soup = BeautifulSoup(article_source, 'html.parser')
                # 소스 다시 가져와서 변수 다시 설정함
                content_e = soup.find('div', class_='write_div')

            # 본문 이미지 추출
            msg['image_list'] = []
            img_e = content_e.find_all(['img', 'video'])
            if img_e:
                e = self.get_by_xpath('//div[@class="write_div"]')
                img_e = e.find_elements_by_xpath('.//video | .//img')
                for j, img in enumerate(img_e):
                    # 이미지의 모든 부모 요소를 확인하여 display 속성이 있는지 검사
                    parent_elements = img.find_elements_by_xpath('./parent::*')
                    display_none = False
                    for parent in parent_elements:
                        if 'none' in parent.get_attribute('style'):
                            display_none = True
                            break
                    if not display_none:
                        src = img.get_attribute('src') or img.get_attribute('data-src')
                        if src:
                            msg['image_url_list'].append(src)
                            cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                           f'{j}.png')
                            img.screenshot(cmt_img_f)
                            msg['image_list'].append(f'{j}.png')
            # 댓글수
            b_com = soup.find('div', class_='fl num_box')
            num_comments = b_com.find('em', class_='font_red')
            msg['num_comments'] = int(num_comments.text.strip())

            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            self.get_comments(msg)

        except Exception as err:
            raise
        finally:
            self.close_tab()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_main_window()

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
    def get_user_type(self, boardname):
        if boardname in ["배민커넥트", "배달", "배달대행 기사들 모임"]:
            return "라이더"
        else:
            return "소비자"

    # ==========================================================================
    def encode_word(self):
        # 수집 키워드 받아옴
        word = self.config['params']['site']['search']
        # 단어를 바이트로 변환합니다.
        byte_string = word.encode('utf-8')

        # 주어진 인코딩을 사용하여 바이트를 인코딩합니다.
        encoded_bytes = binascii.hexlify(byte_string)

        # 인코딩된 바이트를 문자열로 변환합니다.
        encoded_word = encoded_bytes.decode('utf-8')

        # 각 바이트 사이에 점을 추가하여 구분합니다.
        encoded_with_periods = ''
        for i in range(0, len(encoded_word), 2):
            if i > 0:
                encoded_with_periods += '.'
            encoded_with_periods += encoded_word[i:i + 2]

        return encoded_with_periods

    # ==========================================================================
    def request_url(self, url, re_count, timeout):
        for count in range(re_count):
            try:
                # URL에 GET 요청을 보내고 응답을 받습니다.
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    self.logger.info(f'URL을 통한 서버 요청 성공 Page={self.page_url}')
                    # 응답에서 HTML 소스코드를 반환합니다.
                    return response
                else:
                    self.logger.info(f'URL을 통한 서버 요청 실패!! Page={self.page_url}, try={count}, Timeout={timeout}초')
            except:
                self.logger.info(f'서버 요청 Time out 발생, Page={self.page_url}, try={count}')
                if count + 1 == re_count:
                    self.logger.info(f'서버 요청 재시도 {re_count}번 실패(TimeOut) Page={self.page_url}')

    # ==========================================================================
    def article_ids_from_web(self, re_info):
        # 게시글 목록 30개 까지만 가져옴
        # res = requests.get(self.driver.current_url)
        # 페이지의 HTML 소스 가져오기
        html_source = re_info.text
        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(html_source, 'html.parser')
        # url_list = []
        # url_list = [tag.get('href') for tag in soup.find_all('a', class_='tit_txt')]
        # 게시글 정보를 저장할 리스트
        articles = []
        # 게시글 목록
        article_list = soup.find('ul', class_='sch_result_list')
        article_elements = article_list.find_all('li')

        # 중복 제거를 위한 set
        seen_article_ids = set()

        for element in article_elements:
            # URL 추출
            url = element.find('a', class_='tit_txt').get('href')

            # 제목 추출
            title = element.find('a', class_='tit_txt').text.strip()

            # 작성자 추출
            board = element.find('a', class_='sub_txt').text.strip()

            # 작성일 추출
            date = element.find('span', class_='date_time').text.strip()
            # 날짜 형식을 맞추기 위해 ":00" 추가
            if len(date.split()) == 2:
                date += ":00"

            # URL에서 Article ID 추출
            ids_pattern = re.compile(r'no=(\d+)')
            board_pattern = re.compile(r'id=([a-zA-Z0-9_]+)')
            article_id = ids_pattern.search(url).group(1) + '_' + board_pattern.search(url).group(1)

            if article_id not in seen_article_ids:
                # 중복이 아니라면 set에 추가하고, articles 리스트에도 추가
                seen_article_ids.add(article_id)
                # 게시글 정보를 튜플로 저장
                articles.append((url, article_id, title, board, date))
            # # 게시글 정보를 튜플로 저장
            # articles.append((url, article_id, title, board, date))

        return articles

        # ids_pattern = re.compile(r'no=(\d+)')
        # article_ids = [(url, ids_pattern.search(url).group(1)) for url in url_list]
        # return article_ids

    # ==========================================================================
    def load_latest_article_ids(self, keyword, site_sequence):
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
    # ==========================================================================
    def replace_dc(self, j_data):
        # 대상구분 엑셀 파일 불러오기
        filename = r'C:\work\voc\keywords\dc_update.xlsx'

        # 엑셀 파일 읽기: 제외 카페 시트 읽기
        df = pd.read_excel(filename, sheet_name='대상구분', engine='openpyxl')

        # 디시인사이드 게시판
        target_site = df['사이트명']
        # 변경할 대상구분 값
        target_category = df['대상구분']

        for row_index, site in target_site.items():
            if j_data['site_name'] == site:
                j_data['user_type'] = target_category.loc[row_index]
                break

        return j_data

    # ==========================================================================
    def create_table(self, log_d, site_num):
        if not os.path.exists(log_d):
            os.mkdir(log_d)

        # SQLite 데이터베이스 연결 및 커서 생성
        conn = sqlite3.connect(r'C:\work\voc_data\logs\upload2_DB' + '/' + site_num + '.db')
        cursor = conn.cursor()

        try:
            # 게시글 테이블 생성
            cursor.execute('''
                 CREATE TABLE IF NOT EXISTS Articles (
                     article_id TEXT,
                     keyword TEXT,
                     title TEXT,
                     collection_date TEXT,
                     creation_date TEXT,
                     PRIMARY KEY (keyword, article_id)
                 )
             ''')
            conn.commit()
        except sqlite3.Error as e:
            self.logger.error("SQLite 오류:", e)

        finally:
            # 연결 종료
            cursor.close()
            conn.close()

    # ==========================================================================
    def get_page(self):
        try:
            # SQLite DB 파일 없는 경우 생성
            if not os.path.isfile(f'C:\\work\\voc_data\\logs\\upload2_DB\\{self.site_sequence}.db'):
                self.create_table(self.log_d, self.site_sequence)

            # 전처리 시작 시간
            start_time = time.time()
            # URL 검색 방식에 맞게 키워드 인코딩 변환
            self.change_keyword = self.encode_word()
            # 게시글 목록 URL: https://search.dcinside.com/post/p/1/q/.EB.B0.B0.EB.AF.BC
            self.page_url = 'https://search.dcinside.com/post/p/' + str(self.page_count) + '/q/.' + self.change_keyword
            # 서버 요청 횟수
            re_count = 3
            re_timeout = 10
            # URL로 서버 요청
            re_info = self.request_url(self.page_url, re_count, re_timeout)
            # HTML 소스에서 URL, Article_ID 추출
            new_ids = list(self.article_ids_from_web(re_info))

            # OrderedDict의 키로 URL을 사용하고, 값으로 전체 게시글 정보를 사용
            ordered_new_ids = OrderedDict((item[0], item) for item in new_ids if item[1] is not None)

            # 게시글 목록 게시글 ID - 로그로만 사용
            new_article_ids = list(ordered_new_ids.keys())

            # DB 데이터 조회
            # self.load_latest_article_ids가 실제로 어떤 ID를 반환하는지 가정합니다.
            known_ids = set(self.load_latest_article_ids(self.keyword, self.site_sequence))

            # 중복되지 않은 article_id 찾기
            unique_article_ids = [article_id for _, article_id, _, _, _ in ordered_new_ids.values() if
                                  article_id not in known_ids]
            unique_data = [(url, article_id, title, author, date) for url, (url, article_id, title, author, date) in
                           ordered_new_ids.items() if article_id in unique_article_ids]
            # 전처리 종료 시간
            end_time = time.time()
            execution_time = end_time - start_time
            self.logger.info(f'데이터 전처리 소요 시간: {execution_time}초')
            self.logger.info(f'게시글 목록: {len(new_ids)}개, DB 조회 데이터: {len(known_ids)}개, 중복되지 않은 게시글:{len(unique_article_ids)}개')
            self.logger.info(f'게시글 목록: {new_article_ids}\n DB 조회 데이터: {known_ids}\n 중복되지 않은 게시글 ID:{unique_article_ids}')

            # 게시글 순서 인덱스
            count_a = 0
            self.switch_to_window(0)
            for u_data in unique_data:
                coll_start = time.time()
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
                    'author': None,      # 변경
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
                    # 별도 수집 게시판 제외
                    board_list = ['배민커넥트', '배달', '배달대행 기사들 모임', '배드민턴', '2024 파리 올림픽']
                    # # 갤러리 제외
                    # if u_data[3] in board_list:
                    #     self.logger.info(f'get_page[{self.page_count}:{count_a + 1}] 게시글ID: {u_data[1]} ,{u_data[3]} have different contents')
                    #     count_a += 1
                    #     continue

                    # 윈도우창 갯수 체크 로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()

                    # 게시글 URL, ID, 제목, 게시판, 사이트명 작성일시 저장
                    msg['article_url'] = u_data[0]
                    msg['article_id'] = u_data[1]
                    msg['title'] = u_data[2]
                    msg['board_name'] = u_data[3]
                    msg['site_name'] = u_data[3]
                    msg['create_ts'] = u_data[4]

                    # 갤러리 제외
                    if u_data[3] in board_list:
                        self.logger.info(
                            f'get_page[{self.page_count}:{count_a + 1}] 게시글ID: {u_data[1]} ,{u_data[3]} have different contents')
                        # 별도 수집 게시판만 있는 경우도 등록 시간 확인
                        if self.stop_article_older_than(msg):
                            if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                                shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                            self.is_done = True
                            break
                        count_a += 1
                        continue

                    # '대상구분' 변경 게시판 불러오기
                    # dc_field_update.main(msg)
                    self.replace_dc(msg)

                    for count in range(re_count):
                        # alert 메세지 회피 로직 추가(우울증 갤러리)
                        if "depression_new" in msg['article_id']:
                            self.driver.execute_script(f"window.open();")
                            self.implicitly_wait(after_wait=1)
                            self.switch_to_window(1)
                            self.driver.get(f'{u_data[0]}')
                            self.implicitly_wait(after_wait=1)
                            try:
                                alert = self.driver.switch_to.alert
                                alert.accept()
                                self.logger.info('board name is 우울증갤러리')
                            except:
                                self.logger.info('board name is 우울증갤러리 but alert already accept')
                        else:
                            # # 삭제된 게시글 테스트
                            # del_url = 'https://gall.dcinside.com/mgallery/board/view/?id=baemin&no=14809'
                            # self.driver.execute_script(f"window.open('{del_url}');")
                            self.driver.execute_script(f"window.open('{u_data[0]}');")

                        try:
                            self.switch_to_window(1)
                            # 특정 요소가 로드될 때까지 기다림
                            wait = WebDriverWait(self.driver, 10)
                            element = wait.until(
                                EC.presence_of_element_located((By.XPATH, '//span[@class="title_subject"]')))
                            break
                        except:
                            self.logger.info(
                                f'삭제된 게시글 입니다. article_url[{msg["article_url"]}], article_id[{msg["article_id"]}], 제목[{msg["title"]}]')
                            self.driver.close()
                            self.switch_to_main_window()
                            continue

                    # # 삭제된 게시글 확인
                    # for count in range(re_count):
                    #     try:
                    #         self.switch_to_window(1)
                    #         # 특정 요소가 로드될 때까지 기다림
                    #         wait = WebDriverWait(self.driver, 10)
                    #         element = wait.until(
                    #             EC.presence_of_element_located((By.XPATH, '//span[@class="title_subject"]')))
                    #         break
                    #     except:
                    #         self.logger.info(
                    #             f'삭제된 게시글 입니다. article_url[{msg["article_url"]}], article_id[{msg["article_id"]}], 제목[{msg["title"]}]')
                    #         self.driver.close()
                    #         continue

                    self.get_article(msg, count_a + 1)
                    coll_end = time.time()
                    collection_time = coll_end - coll_start
                    self.logger.info(f'게시글 수집 소요 시간: {collection_time}초')

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{count_a+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True
                    break
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
                count_a += 1
        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            f'{article["article_id"]}'
            # f'{self.output["start_ts"]}'
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
            # 게시글 목록 페이지 순서
            self.page_count = 1
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                # 게시글 목록 페이지 +1
                self.page_count += 1
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9
        finally:
            # print(self.output['latest_create_article_ts'])
            # DB 저장 시에 target folder 경로를 전달해줘야 함 - 나머지 print 제거
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with DCinsideSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'dcinside_articleID.yaml'
    do_start(config_f=_config_f)
