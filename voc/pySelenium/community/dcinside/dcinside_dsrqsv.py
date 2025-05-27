"""
====================================
 :mod:`dcinside_dsrqsv`
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
#
#  * [2024/08/06]
#     - 전체 스크린샷 방식 변경(제목, 본문, 댓글)
#  * [2024/07/17]
#     - 본문 이미지의 포함된 텍스트 제거
#  * [2024/07/16]
#     - 게시글 내에 이미지 순서 버튼 제거(클릭)
#  * [2024/07/15]
#     - 게시글 내에 video(동영상) 태그 수집 추가
#  * [2024/07/11]
#     -댓글 디시콘 다운로드 로직 수정
#  * [2024/06/26]
#     - 게시글 내에 이미지 태그가 있으나 데이터가 없어서 보이지 않는 이미지의 스킵 로직 추가
#  * [2024/05/09]
#     - 댓글부분에 포함된 "- dc App" 제거 로직 추가
#  * [2024/04/01]
#     - 매니저 차단 이미지 수집 로직 추가
#  * [2024/02/28]
#     - 수집 키워드 검색 여부 확인 검색 실패 시 종료/검색 재시도 실패함
#  * [2024/01/24]
#     - 삭제된 댓글 등록 시간 처리
#  * [2024/01/15]
#     - 댓글 등록 시간 로직 수정
#     - 대댓글 보이스리플 추가
#  * [2024/01/08]
#     - 게시글 목록 스크린 샷 추가
#     - 보이스리플 게시글은 목록에서 XPath가 달라서 XPath 수정
#     - 새 해로 바뀌면 댓글 등록 시간 형식이 변경되어 정규 표현식으로 날짜 형식 확인. ex) 12.23 -> 2023.12.23
#  * [2023/08/02]
#     - 사이트 UI 원복으로 검색 박스 XPath에 이전 버전 포함
#  * [2023/08/01]
#     - 검색 박스 UI 변경으로 XPath 수정
#  * [2023/02/20]
#     - 보이스리플 박스 텍스트로 변환
#  * [2022/11/02]
#     - 다음 페이지 넘어가는 로직 수정
#  * [2022/06/14]
#     - 게시글 닉네임 찾는 xpath 변경
#  * [2022/04/27]
#     - 댓글 create_ts 찾는 xpath 변경
#  * [2022/04/12]
#     - 댓글 이미지 이름 변경
#  * [2022/04/06]
#     - 게시글 목록에 공지와 설문제외 
#  * [2022/03/21]
#     - 갤러리 별로 분리작업

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
import datetime
import traceback
from pathlib import Path
from copy import deepcopy
# from PIL import Image
# from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
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
        self.send_keys(e, self.config['params']['site']['search'])
        # 검색 단추
        e = self.get_by_xpath('//div[@class="bottom_search fl clear"]//button[@class="sp_img bnt_search"]',
                              cond='element_to_be_clickable')
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
                            if e_del_reply.find('del_reply') > 0:
                                e = cmt_e.find_element_by_xpath('.//p[@class="del_reply"]')
                                cmt['contents'] = e.text.strip().replace(' - dc App', '')
                                cmt['comment_id'] = None
                            elif inner_html.find('voice_wrap') > 0:
                                cmt['contents'] = '보이스리플'
                                # 댓글 작성 시간
                                e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                                cmt_c = e.text.strip()
                                if self.check_cmt_create(cmt_c):
                                    cmt['create_ts'] = cmt_c
                                else:
                                    cmt['create_ts'] = a_ts[0] + '.' + cmt_c
                            else:
                                # # 댓글 작성 시간
                                # e = re_cmt.find_element_by_xpath('.//div[@class="fr clear"]/span')
                                # # cmt['create_ts'] = a_ts[0] + '.' + e.text.strip()
                                # cmt_c = e.text.strip()
                                # if self.check_cmt_create(cmt_c):
                                #     cmt['create_ts'] = cmt_c
                                # else:
                                #     cmt['create_ts'] = a_ts[0] + '.' + cmt_c
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
    def enable_download_headless(self, download_dir):
        self.browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        self.browser.execute("send_command", params)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]')

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

            content_e = self.get_by_xpath('//div[@class="view_content_wrap"]')
            # 글 제목 + 글유형
            e_t = content_e.find_element_by_xpath('//span[@class="title_headtext"]')
            e = content_e.find_element_by_xpath('//span[@class="title_subject"]')
            msg['title'] = e_t.text.strip() + ' ' + e.text.strip()
            # # 접속한 디바이스
            # e = content_e.find_element_by_xpath('//span[@class="title_device"]')
            # inner_html = e.get_attribute('innerHTML')
            # if inner_html.find('blind') > 0:
            #     create_device = e.find_element_by_xpath('//em[@class="blind"]')
            #     msg['create_device'] = create_device.text.strip()
            # else:
            #     msg['create_device'] = "PC에서 작성"
            # 작성자
            e = content_e.find_element_by_xpath('.//span[@class="nickname in"]|.//span[@class="nickname"]')
            msg['author'] = e.text.strip()
            # # 회원IP 없는 경우도 있슴.
            # try:
            #     e = content_e.find_element_by_xpath('//span[@class="ip"]')
            #     msg['author_ip'] = e.text.strip()
            # except:
            #     msg['author_ip'] = ''
            # 작성일시
            e = content_e.find_element_by_xpath('//span[@class="gall_date"]')
            msg['create_ts'] = e.text.strip()
            # 추천수
            e = content_e.find_element_by_xpath('//span[@class="gall_reply_num"]')
            msg['like'] = int(e.text.split()[1].replace(',', ''))
            # 조회수
            e = content_e.find_element_by_xpath('//span[@class="gall_count"]')
            msg['view_count'] = int(e.text.split()[1].replace(',', ''))
            # 댓글수
            e = content_e.find_element_by_xpath('//div[@class="fl num_box"]//em[@class="font_red"]')
            msg['num_comments'] = int(e.text.strip())

            # 본문(write_div 아래 모든 형식이 있슴.)
            e = self.get_by_xpath('//div[@class="write_div"]')
            inner_html = e.get_attribute('innerHTML')
            # 본문 text (글이 없으면 알아서 ''로 나옴.)
            msg['contents'] = e.text.strip()
            # 매니저 차단 이미지 활성화(활성화 안하면 이미지 에러 발생)
            if 'alt="매니저 차단 이미지"' in inner_html:
                img_c = e.find_element_by_xpath('//button[@class="btn_img_block block_img_e"]')
                self.safe_click(img_c)
            # 본문 이미지는 tagname으로 찾아야함.
            msg['image_list'] = []
            # 이미지, 비디오 태그 확인
            img_e = e.find_elements_by_xpath('.//video | .//img')
            if img_e:
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
            # TODO: 첨부파일 headless 사용시 에러,  click이 작동을 안함.
            # inner_html = content_e.get_attribute('innerHTML')
            # if inner_html.find('appending_file_box') > 0:
            #     attachments = content_e.find_elements_by_xpath('.//ul[@class="appending_file"]/li')
            #     for sub_k in attachments:
            #         self.move_to_element(sub_k)
            #         sub_k_url_e = sub_k.find_element_by_xpath('./a')
            #         sub_k_url = sub_k_url_e.get_attribute('href')
            #         # 다운로드폴더에 다운 받음
            #         set1 = set(os.listdir(self.get_download_path()))
            #         # self.safe_click(sub_k)
            #         self.safe_click(sub_k_url_e)
            #         self.implicitly_wait(after_wait=1)
            #         download_wait(self.get_download_path(), 10)
            #         set2 = set(os.listdir(self.get_download_path()))
            #         # 실제로 다운 받는 파일의 이름이 다를수 있음.
            #         sub_k_name = list(set1 ^ set2)[0]
            #         msg['attachment_url'].append(sub_k_url)
            #         msg['attachment_name'].append(sub_k_name)
            #         src = "\\".join([self.get_download_path(), sub_k_name])
            #         dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
            #         # 파일 이동
            #         shutil.move(src, dst)
            # 본문 내 모든 링크 (링크는 본문내용에 포함됨)
            # msg['link_list'] = []
            # if inner_html.find('a href=')>0:
            #     link_e = e.find_elements_by_xpath('.//a[@target"_blank"]')
            #     for link in link_e:
            #         msg['link_list'].append(link.get_attribute('href'))

            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            self.get_comments(msg)

        except Exception as err:
            raise
        finally:
            # self.close_tab()
            self.driver.back()
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
    def get_page(self):
        try:
            # 게시글 목록 스크린샷
            self.driver.set_window_size(self.config['params']['kwargs']['width'], 3000)
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))

            self.cur_page += 1
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            ae_list = self.driver.find_elements_by_xpath('//table[@class="gall_list"]/tbody/tr[@data-no]')
            # ae_list = self.driver.find_elements_by_xpath('//ul[@class="sch_result_list"]/li/a[@target="_blank"]')
            for i, ae in enumerate(ae_list):
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
                    ae_list = self.driver.find_elements_by_xpath('//table[@class="gall_list"]/tbody/tr[@data-no]')
                    ae = ae_list[i]
                    self.move_to_element(ae)
                    # e_url = ae.get_attribute('href')
                    eu = ae.find_element_by_xpath('.//td[@class="gall_tit ub-word"]/a | .//td[@class="gall_tit ub-word voice_tit"]/a')
                    e_url = eu.get_attribute('href')
                    # 1) 게시글 URL:  article_url
                    msg['article_url'] = e_url
                    # 2) 게시글id : article_id
                    #  dc의 경우 고유 id개념이 없지만 링크마다 고유 넘버와 아이디가 있음. 게시글시간_넘버_아이디
                    e = ae.find_element_by_xpath('.//td[@class="gall_num"]')
                    msg['article_id'] = e.text.strip()

                    self.safe_click(eu)
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i+1)

                except Exception as err:
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
            pass

    # ==========================================================================
    def next_page(self):
        ple = None
        try:
            # np = self.cur_page + 1
            # 목록으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            ple = self.get_by_xpath('(//div[@class="bottom_paging_box iconpaging"])[1]', timeout=2)
            is_on = False
            if ple.text == '다음 검색':
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
                return
            else:
                in_page = ple.find_element_by_tag_name('em').text
                for pa in ple.find_elements_by_xpath('.//a'):
                    if pa.text.strip().isalpha():
                        if pa.text.strip() == '다음':
                            self.safe_click(pa)
                            self.implicitly_wait()
                            return
                        continue
                    elif int(pa.text.strip()) > int(in_page):
                        self.safe_click(pa)
                        self.implicitly_wait()
                        return
                self.is_done = True
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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            f'{article["article_id"]}'
            # f'{self.output["start_ts"]}'
        )
        self.save_d(at_js_f, article)
        # save image dcinside는 이미지 다운로드가 안됨
        # for j, sub_e_url in enumerate(article['image_list']):
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{j + 1}.png'
        #     )
        #     urlretrieve(sub_e_url, cmt_img_f)
        # for cmt in article['comment_list']:
        #     if not('comment_img_url' in cmt and cmt['comment_img_url']):
        #         continue
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{cmt["comment_id"]}.png'
        #     )
        #     urlretrieve(cmt['comment_img_url'], cmt_img_f)

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
            # self.login()
            if self.config['params']['site']['get_cafe_info']:
                self.get_cafe_info()
            # 첨부파일 다운로드 옵션
            # self.enable_download_headless(self.get_download_path())
            self.search()
            # 검색어 실패하면 종료
            e = self.get_by_xpath('//div[@class="bottom_search fl clear"]//input[@class="in_keyword js-bound"] |'
                                  '//div[@class="bottom_search fl clear"]//input[@class="in_keyword"]')
            e_va = e.get_attribute('value')
            if e_va == '':
                is_done = False
                self.logger.error(f'Stop crawling because 검색어 검색 실패')
                return
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
    with DCinsideSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'dcinside_dsrqsv.yaml'
    do_start(config_f=_config_f)
