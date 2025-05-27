"""
====================================
 :mod:`dcinside_closing_articleID`
====================================

"""
# ===========
#
# * Lee yong seok
#
# Change Log
# --------
#  * [2024/10/14]
#     - 게시글 대댓글에 보이스 리플이 있을 경우 보이스 리플의 위치 확인 로직을 정확하게 파악하도록 수정
#  * [2024/10/10]
#     - 게시글 목록에 보이스가 있을경우 XPath가 달라짐 게시글 목록에서 url을 추출할때 보이스가 있을 경우 XPath와 없을 경우 XPath 모두 찾도록 변경
#  * [2024/08/26]
#     - 디시인사이드 페이지 비교 로직 추가. page_count와 url의 페이지, 페이지네이션의 페이지 비교
#     - 추가 이유: 수집 범위인 게시글이 하나만 있는 경우 무한 루프로 빠짐
#  * [2024/08/16]
#     - 디시인사이드 수집 성능 개선


################################################################################
# import re
import os
import sys
import yaml
import json
import time
import shutil
import random
import tarfile
import datetime
import sqlite3
import traceback
import binascii
import re
import requests
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
        self.config['target']['folder'] += '/' + folder_name
        self.is_done = False
        self.cur_page = 0
        # DB 폴더 위치
        self.log_d = r'C:\work\voc_data\logs\upload2_DB'
        # 수집 키워드
        self.keyword = self.config['params']['site']['search']
        # 사이트 순서
        self.site_sequence = self.config['params']['site']['site_sequence']
        # 디시인사이드 갤러리
        self.gallery = self.config['params']['site']['gallery']
        out_config = deepcopy(self.config)
        del out_config['params']['kwargs']['logger']
        self.output = {
            'start_ts': start_ts,
            'config': out_config,
            'article_list': [],
            'latest_create_article_ts': None,
            'cafe_info': {
                'name': self.config['params']['site']['site_name'],
                'url': self.config['params']['kwargs']['url'],
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
    def get_cafe_info(self):
        # 카페 개설일
        e = self.get_by_xpath('//div[@class="info_contbox"]/div[@class="info_cont"][3]/p')
        self.output['cafe_info']['since'] = e.text.strip()

        # 카페 설명
        e = self.get_by_xpath('//div[@class="mintro_txtbox "]/p[@class="mintro_txt"]')
        self.output['cafe_info']['category'] = e.text.strip()

    # ==========================================================================
    def search(self):

        # 검색 어 입력
        e = self.get_by_xpath('//div[@class="bottom_search fl clear"]//input[@class="in_keyword js-bound"] |'
                              '//div[@class="bottom_search fl clear"]//input[@class="in_keyword"]')
        self.implicitly_wait(after_wait=1)
        self.move_to_element(e)
        self.send_keys(e, self.config['params']['site']['search'])
        self.implicitly_wait(after_wait=1)
        # 검색 단추
        e = self.get_by_xpath('//div[@class="bottom_search fl clear"]//button[@class="sp_img bnt_search"]',
                              cond='element_to_be_clickable')
        self.move_to_element(e)
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

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
                            e_voice_reply = re_cmt.get_attribute('innerHTML')
                            if e_del_reply.find('del_reply') > 0:
                                e = cmt_e.find_element_by_xpath('.//p[@class="del_reply"]')
                                cmt['contents'] = e.text.strip().replace(' - dc App', '')
                                cmt['comment_id'] = None
                            elif e_voice_reply.find('voice_wrap') > 0:
                                cmt['contents'] = '보이스리플'
                                # 댓글 작성 시간
                                e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                                cmt_c = e.text.strip()
                                if self.check_cmt_create(cmt_c):
                                    cmt['create_ts'] = cmt_c
                                else:
                                    cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                                self.logger.info('대댓글 보이스리플')
                            else:
                                # 댓글 내용 text
                                e = re_cmt.find_element_by_xpath('.//div[@class="clear cmt_txtbox"]')
                                cmt['contents'] = e.text.strip().replace(' - dc App', '')
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
                                # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
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
                            cmt['contents'] = e.text.strip().replace(' - dc App', '')
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
                            # # 댓글 작성 시간
                            # e = cmt_e.find_element_by_xpath('.//span[@class="date_time"]')
                            # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                        else:
                            # 댓글 작성 시간
                            # e = cmt_e.find_element_by_xpath('.//span[@class="date_time"]')
                            # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                            # 댓글 내용 text
                            e = cmt_e.find_element_by_xpath('.//div[@class="clear cmt_txtbox btn_reply_write_all"]')
                            cmt['contents'] = e.text.strip().replace(' - dc App', '')
                            # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                            media_elements = e.find_elements_by_xpath('.//video | .//img')

                            # media_elements 리스트에서 src 속성을 가진 태그를 처리
                            for media_element in media_elements:
                                src = media_element.get_attribute('src') or media_element.get_attribute('data-src')
                                if src:
                                    cmt['comment_img_url'].append(src)
                                    self.save_e_img(media_element, msg, cmt)
                                    cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')
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
    def enable_download_headless(self, download_dir):
        self.browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        self.browser.execute("send_command", params)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.page_count}:{ndx}],article_id[{msg["article_id"]}]')

            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
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
            if self.config['params']['site']['capture_article']:
                # 캡처할때 광고가 따라와서 꺼주는게 보기 좋음 광고가 올라오는 시간이 좀 있음.
                # e = self.get_by_xpath('//a[@id="wif_adx_banner_close"]')
                # self.safe_click(e)
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

            # 제목
            title_e = soup.find('h3', class_='title ub-word')
            # 글 제목 + 글유형
            title_category = title_e.find('span', class_='title_headtext')
            title = title_e.find('span', class_='title_subject')
            msg['title'] = title_category.text.strip() + ' ' + title.text.strip()

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

            # 작성일시
            create_ts = high_e.find('span', class_='gall_date')
            msg['create_ts'] = create_ts.text.strip()

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
            # self.close_tab()
            self.driver.close()
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
    def article_ids_from_web(self):
        # 폐쇄 갤러리는 request.get(url) 응답 데이터가 없음. 게시글 목록 띄워서 확인
        self.driver.get(self.page_url)
        # self.switch_to_window(1)
        # HTML 추출
        html_source = self.driver.page_source
        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(html_source, 'html.parser')
        # url_list = []
        # url_list = [tag.get('href') for tag in soup.find_all('a', class_='tit_txt')]
        # 게시글 정보를 저장할 리스트
        articles = []
        # 게시글 목록 - beautifulSoup 사용 시 게시글 목록 tbody의 class가 'listwrap2'로 보임. 관리자 도구로 보면 'listwrap2 '
        article_list = soup.find('tbody', class_='listwrap2')
        article_elements = article_list.find_all('tr', class_='ub-content us-post')

        for element in article_elements:
            # URL 추출
            # title_e = element.find('td', class_='gall_tit ub-word')
            # 보이스가 있을 경우에 XPath가 달라져도 url을 가져올수 있도록 수정
            title_e = element.find('td', class_=lambda c: c and ('gall_tit ub-word' in c or 'gall_tit ub-word voice_tit' in c))
            title_url = title_e.find('a').get('href')
            if self.gallery == 'de':
                url = 'https://gall.dcinside.com' + title_url
            else:
                url = 'https://gall.dcinside.com' + title_url

            # URL에서 Article ID 추출
            ids_pattern = re.compile(r'no=(\d+)')
            article_id = ids_pattern.search(url).group(1)

            # 게시글 정보를 튜플로 저장
            articles.append((url, article_id))

        return articles

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
    def get_current_page_from_url(self):
        # URL에서 page 파라미터 값을 추출
        match = re.search(r'page=(\d+)', self.page_url)
        if match:
            return int(match.group(1))
        return None

    # ==========================================================================
    def get_pagination_page(self):
        # 페이지네이션에서 현재 페이지를 추출
        pagination = self.get_by_xpath('(//div[@class="bottom_paging_box iconpaging"])[1]//em', timeout=2)
        if pagination:
            return int(pagination.text.strip())
        return None

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
            # 게시글 목록 URL
            # 배민대행 기사들 모임 갤러리: https://gall.dcinside.com/mgallery/board/lists/?id=dsrqsv&s_type=search_subject_memo&s_keyword=.EB.B0.B0.EB.AF.BC
            # 배달 갤러리 : https://gall.dcinside.com/board/lists?id=de&s_type=search_subject_memo&s_keyword=.EB.B0.B0.EB.AF.BC
            # 배민 커넥트 갤러리 https://gall.dcinside.com/mgallery/board/lists/?id=bamin&page=1&search_pos=&s_type=search_subject_memo&s_keyword=.EB.B0.B0.EB.AF.BC
            # 배달 갤러리는 url에서 mgallery 제외. 갤러리 차이
            if self.gallery == 'de':
                self.page_url = 'https://gall.dcinside.com/board/lists/?id=' + self.gallery + '&page=' + str(
                    self.page_count) + '&search_pos=&s_type=search_subject_memo' \
                                + '&s_keyword=.' + self.change_keyword
            else:
                # 052, 054 갤러리
                self.page_url = 'https://gall.dcinside.com/mgallery/board/lists/?id=' + self.gallery + '&page=' + str(
                    self.page_count) + '&search_pos=&s_type=search_subject_memo' \
                                + '&s_keyword=.' + self.change_keyword
            self.logger.info(f'게시글 목록 URL: {self.page_url}')
            # 서버 요청 횟수
            re_count = 4
            re_timeout = 10
            # URL로 서버 요청(폐쇄 갤러리는 응답 데이터를 못받음)
            # re_info = self.request_url(self.page_url, re_count, re_timeout)
            # HTML 소스에서 URL, Article_ID 추출
            new_ids = list(self.article_ids_from_web())
            # 게시글 목록 검증
            # 게시글이 없는 경우 종료
            if not new_ids:
                self.logger.info('수집 게시글 없음')
                self.is_done = True
                return
            # 현재 게시글 URL page와 페이지네이션의 현재 페이지 비교
            # url에서 page 추출
            url_page = self.get_current_page_from_url()
            # 페이지네이션의 페이지 추출
            pagination_page = self.get_pagination_page()
            if url_page != self.page_count:
                self.logger.info('URL의 페이지와 page_count 다름')
                self.is_done = True
                return
            if pagination_page != self.page_count:
                self.logger.info('페이지네이션와 page_count 다름')
                self.is_done = True
                return
            # self.check_page(url_page, pagination_page)

            # OrderedDict의 키로 URL을 사용하고, 값으로 전체 게시글 정보를 사용
            ordered_new_ids = OrderedDict((item[0], item) for item in new_ids if item[1] is not None)

            # 게시글 목록 게시글 ID - 로그로만 사용
            new_article_ids = list(ordered_new_ids.keys())

            # DB 데이터 조회
            # self.load_latest_article_ids가 실제로 어떤 ID를 반환하는지 가정합니다.
            known_ids = set(self.load_latest_article_ids(self.keyword, self.site_sequence))

            # 중복되지 않은 article_id 찾기
            unique_article_ids = [article_id for _, article_id in ordered_new_ids.values() if
                                  article_id not in known_ids]
            unique_data = [(url, article_id) for url, (url, article_id) in
                           ordered_new_ids.items() if article_id in unique_article_ids]
            # 전처리 종료 시간
            end_time = time.time()
            execution_time = end_time - start_time
            self.logger.info(f'데이터 전처리 소요 시간: {execution_time}초')
            self.logger.info(
                f'게시글 목록: {len(new_ids)}개, DB 조회 데이터: {len(known_ids)}개, 중복되지 않은 게시글:{len(unique_article_ids)}개')
            self.logger.info(
                f'게시글 목록: {new_article_ids}\n DB 조회 데이터: {known_ids}\n 중복되지 않은 게시글 ID:{unique_article_ids}')

            # 게시글 순서 인덱스
            count_a = 0
            self.switch_to_window(0)
            for u_data in unique_data:
                coll_start = time.time()
                msg = {
                    'page': self.page_count,
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
                    'board_name': self.config['params']['site']['site_name'],
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
                    # 윈도우창 갯수 체크 로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()

                    # 게시글 URL, ID 저장
                    # 디시 폐쇄 갤러리는 사이트명, 갤러리 고정
                    # 작성 시간은 게시글 내부에서 확인
                    msg['article_url'] = u_data[0]
                    msg['article_id'] = u_data[1]

                    for count in range(re_count):
                        try:
                            # 게시글 오픈
                            self.driver.execute_script(f"window.open('{u_data[0]}');")
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
                            continue

                    # self.implicitly_wait(after_wait=1)
                    # 게시글 수집
                    self.get_article(msg, count_a + 1)
                    coll_end = time.time()
                    collection_time = coll_end - coll_start
                    self.logger.info(f'게시글 수집 소요 시간: {collection_time}초')
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.page_count}:{count_a + 1}]:{msg["error_backtrace"]}')
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
        )
        self.save_d(at_js_f, article)

    # ==========================================================================
    def save(self):
        self.output['num_articles'] = len(self.output['article_list'])
        if self.config['target']['is_separate_article']:
            del self.output['article_list']
        if 'site_sequence' in self.output['config']['params']['site']:
            del self.output['config']['params']['site']['site_sequence']
        if 'gallery' in self.output['config']['params']['site']:
            del self.output['config']['params']['site']['gallery']
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
            if self.config['params']['site']['get_cafe_info']:
                self.get_cafe_info()

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
    _config_f = 'dcinside_bamin.yaml'
    do_start(config_f=_config_f)
