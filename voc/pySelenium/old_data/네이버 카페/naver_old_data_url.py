"""
====================================
 :mod:`cafe/cafe_naver`
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
#  * [2024/07/24]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. HTML에서 제거
#  * [2024/06/11]
#     - 조회수 정수형으로 변경
#  * [2024/05/29]
#     - URL 수집 방식 변경(게시글 목록 추출)
#     - 댓글 수집 방식 변경(HTML 소스 추출)
#  * [2024/05/17]
#     - 페이지 상단바 제거(스크린샷에서 겹침)
#  * [2024/05/09]
#     - Xpath 수정
#  * [2024/03/25]
#     - article_id 통합 검색과 폐쇄 카페 분리
#  * [2023/01/20]
#     - starting

################################################################################
import os
import sys
import yaml
import json
import time
import pickle
import shutil
import random
import requests
import ssl
import openpyxl
import tarfile
import datetime
import traceback
import pandas as pd
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
from bs4 import BeautifulSoup


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
class LOGINERROR(Exception):
    pass


################################################################################
class NaverCafeSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # self.user_data_path = self.config['target']['user_data_path']
        self.cookie_path = r'C:\work\voc\yaml\카페\네이버\cookies.pkl'
        log_d = 'C:/work/voc_data/logs/cafe/naver'
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'Naver_old_data.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        self.target_folder = 'C:/work/voc_data/latest/cafe/naver'

        # test
        self.url_list = None
        self.index = None

        # 카페id
        self.cafe_id = self.config['params']['kwargs']['url'].rpartition('/')[2]

        # URL 파일 경로
        self.url_list = r'C:\work\url_list\네이버카페_202203.xlsx'

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
        self.logger.info(f'Starting Naver Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            e = self.get_by_xpath('//body')
            inner_html = e.get_attribute('innerHTML')
            # 바로 로그인 되는 경우 처리 : https://cafe.naver.com/jbads
            if inner_html.find('gnb_login_button') > 0:
                # 로그인 클릭
                e = self.get_by_xpath('//*[@id="gnb_login_button"]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            else:
                self.logger.info('login: Directly login page shows up!')

            # login 화면
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="id"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//*[@id="pw"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="log.login"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 로그인 쿠키를 담아둠
            pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def get_cafe_info(self):
        cafe_info = {
            'name': None,
            'url': None,
            'since': None,
            'category': None,
            'register_type': None,
            'write_condition': None,
            'num_members': None,
            'num_visitors': None,
        }
        app_info = {
            'star_like': None,
            'num_reviews': None,
            'title': None,
            'contents': None,
            'version': None,
            'num_download': None,
        }
        try:
            e = self.get_by_xpath('//div[@class="info-view"]/a',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait()

            # 해당 iFrame으로 이동
            self.switch_to_iframe_by_name('cafe_main')
            for tr_e in self.driver.find_elements_by_xpath('//table[@class="tbl_cafe_info"]/tbody/tr'):
                try:
                    e = tr_e.find_element_by_xpath('.//th[@scope="row"]')
                    title = e.text.strip()
                    if title == '카페 이름':
                        e = tr_e.find_element_by_xpath('.//strong[@class="cafe_name"]')
                        cafe_info['name'] = e.text.strip()
                    elif title == '카페 주소':
                        # e = tr_e.find_element_by_xpath('.//*[@id="main-area"]/div/table[1]/tbody/tr[2]/td/a')
                        # cafe_info['url'] = e.text.strip()
                        cafe_info['url'] = self.config['params']['kwargs']['url']
                    elif title.startswith('모바일카페명'):
                        # 모바일카페 이름
                        e = tr_e.find_element_by_xpath('.//div[@class="mcafe_name"]')
                        cafe_info['mobile_name'] = e.text.strip()
                        # 모바일카페 아이콘
                        e = tr_e.find_element_by_xpath('.//div[@class="mcafe_icon cafe_thumb_70"]/img')
                        cafe_info['mobile_icon_src'] = e.get_attribute('src')
                    elif title == '카페 매니저':
                        e = tr_e.find_element_by_xpath('.//td[@class="p-nick"]/a[@class="m-tcol-c"]')
                        cafe_info['manager'] = e.text.strip()
                    elif title == '카페 스탭':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_staff"]')
                        cafe_info['staff'] = e.text.strip()
                    elif title == '카페 설립일':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_history"]')
                        cafe_info['since'] = e.text.split()[-1]
                    # elif title == '주제':
                    #     e = tr_e.find_element_by_xpath('.//td[@class="invite-padd02 m-tcol-c"]')
                    #     cafe_info['category'] = e.text.strip()
                    elif title == '카페 설명':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['category'] = e.text.strip()
                    elif title == '카페 검색어':
                        cafe_info['keywords'] = []
                        for ae in tr_e.find_elements_by_xpath('.//a[@class="keyword"]'):
                            cafe_info['keywords'].append(ae.text.strip())
                    elif title == '카페 성격':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['character'] = e.text.strip()
                    elif title == '가입 방식':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['register_type'] = e.text.strip()
                    elif title == '카페 가입 조건':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['register_condition'] = e.text.strip()
                    elif title == '글쓰기 조건':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['write_condition'] = e.text.strip()
                    elif title == '카페 활동':
                        # 카페 활동 : 멤버수  //*[@id="main-area"]/div/table/tbody/tr[17]/td/span[1]
                        e = tr_e.find_element_by_xpath('.//td/span[1]')
                        cafe_info['num_members'] = int(e.text.strip().replace(',',''))
                        # 카페 활동 : 전체 게시글
                        e = tr_e.find_element_by_xpath('.//td/span[2]')
                        cafe_info['num_articles'] = int(e.text.strip().replace(',',''))
                        # 카페 활동 : 총 방문자
                        e = tr_e.find_element_by_xpath('.//td/span[3]')
                        cafe_info['num_visitors'] = int(e.text.strip().replace(',',''))
                    elif title == '카페 랭킹':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_rank"]')
                        cafe_info['rank'] = e.text.strip()
                    elif title == '멤버 관리':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['member_manage'] = e.text.strip()
                    elif title.startswith('카페 활동정보'):
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['knowledge_in'] = e.text.strip()
                except:
                    try:
                        e = tr_e.find_element_by_xpath('.//td[1]/strong')
                        _title = e.text.strip()
                        if _title == '주제':
                            e = tr_e.find_element_by_xpath('.//td[2]')
                            cafe_info['subject'] = e.text.strip()
                        elif _title == '지역':
                            e = tr_e.find_element_by_xpath('.//td[2]')
                            cafe_info['local'] = e.text.strip()
                    except:
                        pass
        except Exception as err:
            self.logger.error(f'get_cafe_info: Error {str(err)}')
        finally:
            self.output['cafe_info'] = cafe_info
            self.output['app_info'] = app_info
            self.switch_from_iframe()
            # 이전 페이지
            self.driver.back()

    # ==========================================================================
    def search(self):
        # 검색 어 입력
        # self.switch_to_window(0)
        e = self.get_by_xpath('//input[@id="topLayerQueryInput"]')

        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 아래와 같이 검색 단추가 때때로 다른 엘리먼트로 구현되는 경우가 있어 엔터키로 변경
        time.sleep(1)
        self.send_keys(e, Keys.ENTER)

        # 검색 단추
        # e = self.get_by_xpath('//*[@id="cafe-search"]/form/button',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 댓글 내용으로 검색
        if self.config['params']['site']['search_filter'] in ['댓글', '제목']:
            self.switch_to_iframe_by_name('cafe_main')

            e = self.get_by_xpath('//form[@name="frmSearchTop"]')
            e_a = e.find_element_by_xpath('//form[@name="frmSearchTop"]/div[3]')
            self.safe_click(e_a)

            e_s = e_a.find_elements_by_xpath('//ul[@id="sl_general"]/li')
            for e_filter in e_s:
                if e_filter.text.find(self.config['params']['site']['search_filter']) >= 0:
                    self.safe_click(e_filter)
                    self.implicitly_wait(after_wait=1)

            e = self.get_by_xpath('//button[@class="btn-search-green"]')
            self.safe_click(e)

    # ==========================================================================
    # def get_article(self, msg, ndx):
    #     try:
    #         self.logger.info(self.config['kwargs']['url'])
    #         # 카페에 main iframe으로 이동
    #         self.switch_to_iframe_by_name('cafe_main')
    #         if self.config['params']['site']['capture_article']:
    #             msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
    #                                                f'{msg["article_id"]}.png')
    #             self._screenshot(msg_capture_f)
    #         # 게시판 이름
    #         e = self.get_by_xpath('//div[@class="post_title"]/div/a[@class="border_name"]/span')
    #         msg['board_name'] = e.text.strip()
    #         # 작성일시
    #         e = self.get_by_xpath('//div[@class="post_title"]//div[@class="user_wrap"]//div[@class="info"]//span[@class="date font_l"]')
    #         c_t = e.text.strip().replace("작성일\n", "")
    #         create_t = c_t.split(". ")
    #         create_ts = create_t[0] + create_t[1] + ':00'
    #         msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
    #         # 조회수
    #         e = self.get_by_xpath('//span[@class="no font_l"]')
    #         msg['view_count'] = int(e.text.split()[1].replace(',', ''))
    #         # 내용 : 비어 있는 경우도 있음 (사진만)
    #         try:
    #             e = self.get_by_xpath('//div[@class="se-main-container"]')
    #             msg['contents'] = e.text.strip()
    #         except:
    #             msg['contents'] = ''
    #
    #         e = self.get_by_xpath('//div[@class="se-main-container"]')
    #         # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
    #         # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
    #         inner_html = e.get_attribute('innerHTML')
    #         # 이미지 주소 가져오기
    #         msg['image_list'] = []
    #         msg['image_url_list'] = []
    #         if inner_html.find('se-image-resource') > 0:
    #             for j, sub_e in enumerate(e.find_elements_by_xpath('.//img[@class="se-image-resource"]')):
    #                 sub_e_url = sub_e.get_attribute('src')
    #                 msg['image_url_list'].append(sub_e_url)
    #                 art_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
    #                                                f'{j}.png')
    #                 sub_e.screenshot(art_img_f)
    #                 msg['image_list'].append(f'{j}.png')
    #         # 첨부파일  Todo:headless시 클릭으로 다운받지못함
    #         # if inner_html.find('data-linktype="file"') > 0:
    #         #     for sub_e in e.find_elements_by_xpath('.//div[@class="se-module se-module-file"]/a[@data-linktype="file"]'):
    #         #         self.move_to_element(sub_e)
    #         #         msg['attachment_url'].append(sub_e.get_attribute('href'))
    #         #         # 다운로드폴더에 다운 받음
    #         #         set1 = set(os.listdir(self.get_download_path()))
    #         #         self.safe_click(sub_e)
    #         #         self.implicitly_wait(after_wait=1)
    #         #         download_wait(self.get_download_path(), 30)
    #         #         set2 = set(os.listdir(self.get_download_path()))
    #         #         # 실제로 다운 받는 파일의 이름이 다를수 있음.
    #         #         sub_k_name = list(set1 ^ set2)[0]
    #         #         msg['attachment_name'].append(sub_k_name)
    #         #         src = "\\".join([self.get_download_path(), sub_k_name])
    #         #         dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
    #         #         # 파일 이동
    #         #         shutil.move(src, dst)
    #
    #         # 링크 주소 가져오기
    #         # msg['link_list'] = []
    #         # if inner_html.find('se-link') > 0:
    #         #     for sub_e in e.find_elements_by_xpath('.//a[@class="se-link"]'):
    #         #         msg['link_list'].append(sub_e.get_attribute('href'))
    #
    #         # 댓글 : 댓글이 없는 경우 있음
    #         if msg['num_comments'] == 0:
    #             return
    #         msg['comment_list'] = []
    #         comments = e.find_elements_by_xpath('./div[@class="CommentBox"]/ul[@class="comment_list"]/li')
    #         parent_comment_id = ''
    #         for i, cmt_e in enumerate(comments):
    #             delay_c = random.uniform(
    #                 self.config['params']['site']['delay']['comment']['min'],
    #                 self.config['params']['site']['delay']['comment']['max'],
    #             )
    #             time.sleep(delay_c)
    #             cmt = {
    #                    'comment_id': None,
    #                    'is_reply': None,
    #                    'parent_comment_id': None,
    #                    'create_ts': None,
    #                    'nickname': None,
    #                    'contents': None,
    #                    'like': None,
    #                    'dislike': None,
    #                    'comment_img': [],
    #                    'comment_img_url': [],
    #                    }
    #             # 댓글 id
    #             cmt['comment_id'] = cmt_e.get_attribute('id')
    #             # 대댓글?
    #             is_reply = cmt_e.get_attribute('class') == 'CommentItem CommentItem--reply'
    #             cmt['is_reply'] = is_reply
    #             if not is_reply:
    #                 parent_comment_id = cmt['comment_id']
    #                 cmt['parent_comment_id'] = ''
    #             else:
    #                 cmt['parent_comment_id'] = parent_comment_id
    #             # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
    #             try:
    #                 e = cmt_e.find_element_by_xpath('.//a[@class="comment_nickname"]')
    #                 cmt['nickname'] = e.text.strip()
    #             except:
    #                 continue
    #             # 댓글 내용
    #             e = cmt_e.find_element_by_xpath('.//span[@class="text_comment"]')
    #             self.move_to_element(e)
    #             comment = e.text
    #             # 댓글 내용중에 멘션이 있을 경우 포함
    #             inner_html = cmt_e.get_attribute('innerHTML')
    #             if inner_html.find("text_nickname") > 0:
    #                 tag = cmt_e.find_element_by_xpath('.//a[@class="text_nickname"]').text
    #                 cmt['contents'] = tag + ' ' + comment
    #             else:
    #                 cmt['contents'] = comment
    #             # 댓글 작성 시각
    #             e = cmt_e.find_element_by_xpath('.//span[@class="comment_info_date"]')
    #             create_t = e.text.strip().rpartition('.')
    #             create_ts = create_t[0] + create_t[2] + ':00'
    #             cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
    #
    #             cmt['comment_img_url'] = []
    #             cmt['comment_img'] = []
    #             # 댓글 스티커 or 이미지
    #             inner_html = cmt_e.get_attribute('innerHTML')
    #             if inner_html.find('CommentItemSticker') > 0 or inner_html.find('CommentItemImage') > 0:
    #                 s = cmt_e.find_element_by_xpath('.//img[@class="image"]')
    #                 cmt['comment_img_url'].append(s.get_attribute('src'))
    #                 cmt_img_f = self.get_safe_path(
    #                     self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"]+"_0"}.png')
    #                 s.screenshot(cmt_img_f)
    #                 cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
    #
    #             # 댓글 목록에 추가
    #             msg['comment_list'].append(cmt)
    #             self.logger.info(f'   [{i+1}/{msg["num_comments"]}]: {cmt["comment_id"]}')
    #
    #     except Exception as err:
    #         raise
    #     finally:
    #
    #         # 이전 페이지
    #         self.driver.back()
    #         try:
    #             self.switch_to_iframe_by_name('cafe_main')
    #         except:
    #             # selenium.common.exceptions.WebDriverException: Message: unknown error:
    #             # cannot determine loading status
    #             pass

    # ========================================================================
    def get_comment(self, msg):
        try:
            # 댓글 페이지 HTML 소스 가져오기
            comment_source = self.driver.page_source
            # 주어진 HTML 소스를 사용하여 BeautifulSoup 객체 생성
            soup = BeautifulSoup(comment_source, 'html.parser')

            # 모든 댓글을 선택합니다.
            c_e = soup.find('ul', class_='comment_list')
            comments = c_e.find_all('li')

            # 각 댓글에서 필요한 정보를 추출하여 데이터 셋에 저장합니다.
            for idx, comment in enumerate(comments):
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
                # 댓글의 comment_id는 순번으로 지정합니다.
                cmt['comment_id'] = str(idx + 1)

                # 대댓글 여부를 확인합니다.
                is_reply = 'class' in comment.attrs and 'reply' in comment['class']
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ''
                    cmt['is_reply'] = False
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                    cmt['is_reply'] = True

                # 댓글의 작성 시간을 가져옵니다.
                try:
                    c_c = comment.find('span', class_='date')
                    create_ts = c_c.text.strip().rpartition('.')
                    cmt['create_ts'] = create_ts[0] + create_ts[2] + ':00'
                except:
                    continue

                # 댓글 작성자의 닉네임을 가져옵니다.
                nickname = comment.find('span', class_='nick_name').text.strip()
                cmt['nickname'] = nickname

                # 댓글의 내용을 가져옵니다.
                contents = comment.find('div', class_='comment_content')
                for span in contents.find_all('span'):
                    span.extract()
                cmt['contents'] = contents.text.strip()

                # 댓글에 포함된 이미지를 수집합니다.
                cmt['comment_img'] = []
                cmt['comment_img_url'] = []
                img_c = comment.find('div', class_='comment_content')
                comment_imgs = img_c.find_all('source')  # 댓글에 포함된 모든 이미지 태그를 가져옵니다.
                for img in comment_imgs:
                    img_url = img['srcset']  # 이미지의 src 속성을 가져옵니다.
                    cmt['comment_img_url'].append(img_url)  # 이미지
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
            self.cmt_done = True
        except Exception as err:
            raise

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
    def read_key_file(self):
        # 수집 키워드 추출 파일이 있어야함
        site_name = '카페명'
        keyword_file = r'C:\work\voc\keywords\네이버' + f'{site_name}.xlsx'
        df = pd.read_excel(keyword_file)
        return df.values.tolist()

    # ========================================================================
    def remove_html(self):
        # 중간에 게시글 UI 변경 가능성이 있어 각각 try문으로 실행
        try:
            # 파워 링크
            try:
                power_link = self.get_by_xpath("//div[@class='ArticleSectionLoggerBannerTypeAdvert']")
                self.driver.execute_script("arguments[0].remove();", power_link)
            except Exception as e:
                self.logger.error(f'파워 링크 제거 실패: {e}')

            # 게시글 목록 리스트
            try:
                article_lists = self.driver.find_elements_by_xpath('//div[@class="section_forum_wrap"]')
                for article_list in article_lists:
                    self.driver.execute_script("arguments[0].remove();", article_list)
            except Exception as e:
                self.logger.error(f'게시글 목록 리스트 제거 실패: {e}')

            # 하단 광고
            try:
                btm_area = self.get_by_xpath('//div[@class="ArticleBottomArea"]')
                self.driver.execute_script("arguments[0].remove();", btm_area)
            except Exception as e:
                self.logger.error(f'하단 광고 제거 실패: {e}')

            # footer
            try:
                ft = self.get_by_xpath('//div[@class="footer_inner"]')
                self.driver.execute_script("arguments[0].remove();", ft)
            except Exception as e:
                self.logger.error(f'푸터 제거 실패: {e}')

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경: {err}')
            pass

    # ==========================================================================
    def get_page(self):
        try:
            wb = openpyxl.load_workbook(self.url_list, data_only=True)
            ws = wb.active
            row_max = ws.max_row
            # self.read_key_file()
            for i in range(1, row_max + 1):
                self.index = i
                self.url = ws['A' + str(i)].value
                self.driver.get(self.url)
                self.implicitly_wait(after_wait=1)
                try:
                    msg = {
                        'page': self.cur_page,
                        'row': 1,
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
                    self.switch_to_window(0)
                    # 게시판 이름
                    e = self.get_by_xpath('//div[@class="post_title"]/div/a[@class="border_name"]/span')
                    msg['board_name'] = e.text.strip()
                    # self.logger.info(self.config['kwargs']['url'])
                    # 작성자
                    e = self.get_by_xpath('//span[@class="end_user_nick"]')
                    msg['author'] = e.text.strip()
                    # 카페 사이트 이름
                    e = self.get_by_xpath('//div[@class="gnb"]//h1//a')
                    msg['site_name'] = e.text.strip()
                    # ID 추출
                    # e = self.get_by_xpath('//meta[@property="og:url"]')
                    # article_url = e.get_attribute('content')
                    msg['article_url'] = self.url
                    e_a = self.url.rpartition('/')[2]
                    # article_id = e_a.partition('?')[0]
                    if self.config['params']['site']['site_number'] == '188':
                        # 카페 통합검색
                        article_id = e_a.partition('?')[0]
                        cafe_domain = self.url.partition('.com/')[2].rpartition('/')[0]
                        msg['article_id'] = cafe_domain + '_' + article_id
                    else:
                        # 폐쇄 카페 전용
                        msg['article_id'] = self.cafe_id+'_'+e_a



                    # 제목
                    e = self.get_by_xpath('//div[@class="post_title"]//h2')
                    msg['title'] = e.text.strip()
                    # 작성일시
                    e = self.get_by_xpath('//div[@class="post_title"]//div[@class="user_wrap"]//div[@class="info"]//span[@class="date font_l"]')
                    e_a = e.text.strip()
                    e_b = e_a.partition('\n')[2]
                    create_t = e_b.partition('. ')
                    create_ts = create_t[0] + ' ' + create_t[2] + ':00'
                    msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                        '%Y.%m.%d %H:%M:%S')
                    # 조회수
                    e_s = self.get_by_xpath('//div[@class="post_title"]//div[@class="user_wrap"]//div[@class="info"]//span[@class="no font_l"]')
                    e_v = e_s.text.split()[1].replace(',', '')
                    if '만' in e_v:
                        se_a = e_v.replace('만', '0000').replace('.', '')
                    else:
                        se_a = e_v.replace(',', '')
                    msg['view_count'] = int(se_a)
                    # 해쉬태그
                    msg['tag_list'] = []

                    # 댓글 수: 누르면 바로 댓글 창으로 가짐
                    e_ab = self.get_by_xpath('//div[@class="ArticleContentWrap MediaViewerWrapper"]')
                    e_c = e_ab.find_element_by_xpath('//div[@class="CafeCommentSort"]//em')
                    msg['num_comments'] = int(e_c.text.strip())

                    self.remove_html()
                    # 내용 : 비어 있는 경우도 있음 (사진만)
                    try:
                        e = self.get_by_xpath('//div[@class="se-main-container"]|//div[@class="article_content_se"]|//div[@class="content"]')
                        msg['contents'] = e.text.strip()
                    except:
                        msg['contents'] = ''
                    # 스크린샷
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{msg["article_id"]}.png')
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="gnb"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                                                            var element = arguments[0];
                                                                                            element.parentNode.removeChild(element);
                                                                                            """, e_head)
                    e_footers = self.driver.find_elements_by_xpath('//div[@class="footer_fix"]')
                    for e_footer in e_footers:
                        self.driver.execute_script("""
                                                                                             var element = arguments[0];
                                                                                             element.parentNode.removeChild(element);
                                                                                             """, e_footer)
                    head_bar = self.driver.find_elements_by_xpath('//header[@class="WebHeader type_skin"]')
                    for head_bar in head_bar:
                        self.driver.execute_script("""
                                                                                            var element = arguments[0];
                                                                                            element.parentNode.removeChild(element);
                                                                                            """, head_bar)
                    self.full_screenshot(msg_capture_f)
                    # self._screenshot(msg_capture_f)
                    # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
                    # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
                    inner_html = e.get_attribute('innerHTML')
                    # 이미지 주소 갖고 오기
                    msg['image_list'] = []
                    msg['image_url_list'] = []
                    if inner_html.find('img') > 0:
                        for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                            # self.move_to_element(sub_e)
                            # sub_e_url = sub_e.get_attribute('src')
                            # msg['image_url_list'].append(sub_e_url)

                            try:
                                article_img_p = self.get_safe_path(
                                    self.config['target']['folder'],
                                    msg['article_id'],
                                    f'{j}.png'
                                )
                                self.move_to_element(sub_e)
                                sub_e_url = sub_e.get_attribute('src')
                                urlretrieve(sub_e_url, article_img_p)
                                msg['image_url_list'].append(sub_e_url)
                                msg['image_list'].append(f'{j}.png')
                            except:
                                # 실패한 이미지 URL 본문 내용에 저장
                                msg['contents'] += f'다운로드 실패 이미지: {sub_e_url}'
                                self.logger.info(f'save_img error: {j}.png')
                    # 첨부파일 # 찾은 다음 하기
                    inner_html = e.get_attribute('innerHTML')
                    msg['attachment_url'] = []
                    msg['attachment_name'] = []
                    if inner_html.find('tblForFl') > 0:
                        for k, sub_k in enumerate(e.find_elements_by_xpath('.//table[@id="tblForFl"]//a')):
                            self.move_to_element(sub_k)
                            sub_k_url = sub_k.get_attribute('data-href')
                            msg['attachment_url'].append(sub_k_url)
                            sub_k_name = sub_k.text.strip()
                            msg['attachment_name'].append(sub_k_name)

                    # 댓글이 없는 경우
                    if msg['num_comments'] == 0:
                        if self.config['target']['is_separate_article']:
                            self.save_article(msg)
                            self.save_attachment(msg)
                            self.save_image(msg)
                            self.output['article_list'].append(msg)
                            if self.config['target']['is_separate_article']:
                                self.save_article(msg)
                            continue
                        return
                    # 댓글
                    msg['comment_list'] = []

                    # 댓글 페이지가 있는 경우 : 없으면 댓글 페이지만 들어가면 된다.
                    try:
                        e = self.get_by_xpath('//div[@class="CafeCommentSort"]//a[@class="link"]',
                                              cond='element_to_be_clickable')
                        self.safe_click(e)
                        self.implicitly_wait(after_wait=1)
                        # 댓글 더 보기가 있는 경우
                        while msg['num_comments'] != 0:
                            fold_flag = False

                            # 두 번째 : 펼쳐야 하는 경우가 없는 경우는 빠져 나가기
                            for more in self.driver.find_elements_by_xpath(
                                    '//div[@class="comment_more"]//a[@class="more_next"]'):
                                self.safe_click(more)
                                self.implicitly_wait(after_wait=1)
                                fold_flag = True

                            # 세 번째 : 펼쳐야 하는 경우
                            for more in self.driver.find_elements_by_xpath(
                                    '//div[@class="comment_more"]//a[@class="more_next"]'):
                                self.safe_click(more)
                                self.implicitly_wait(after_wait=1)
                                break

                            # while 문 빠져나가기
                            if fold_flag == False:
                                break
                        self.get_comment(msg)
                    except:
                        pass
                    # 좋아요
                    # e = self.get_by_xpath('//div[@class="right_area"]/div/a/em[2]')
                    # msg['like'] = int(e.text.strip())
                    # 댓글 : 댓글이 없는 경우 있음
                    # e = self.get_by_xpath('//div[@class="right_area"]/a/em')
                    # msg['num_comments'] = int(e.text.strip())
                    # if msg['num_comments'] == 0:
                    #     if self.config['target']['is_separate_article']:
                    #         self.save_article(msg)
                    #         continue
                    # # 댓글 페이지 들어가기
                    # self.safe_click(e)
                    # self.implicitly_wait(after_wait=1)
                    # msg['comment_list'] = []
                    # e = self.get_by_xpath('//ul[@class="comment_list"]')
                    # comments = e.find_elements_by_xpath('./li')
                    # parent_comment_id = ''
                    # for i, cmt_e in enumerate(comments):
                    #     delay_c = random.uniform(
                    #         self.config['params']['site']['delay']['comment']['min'],
                    #         self.config['params']['site']['delay']['comment']['max'],
                    #     )
                    #     time.sleep(delay_c)
                    #     cmt = {
                    #         'comment_id': None,
                    #         'is_reply': None,
                    #         'parent_comment_id': None,
                    #         'create_ts': None,
                    #         'nickname': None,
                    #         'contents': None,
                    #         'like': None,
                    #         'dislike': None,
                    #         'comment_img': [],
                    #         'comment_img_url': [],
                    #     }
                    #     # 댓글 id (없어도 되는지 문의 후 찾기)
                    #     cmt['comment_id'] = cmt_e.get_attribute('id')
                    #     # 대댓글?
                    #     is_reply = cmt_e.get_attribute('class') == 'reply'
                    #     cmt['is_reply'] = is_reply
                    #     if not is_reply:
                    #         parent_comment_id = cmt['comment_id']
                    #         cmt['parent_comment_id'] = ''
                    #     else:
                    #         cmt['parent_comment_id'] = parent_comment_id
                    #     # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
                    #     try:
                    #         e = cmt_e.find_element_by_xpath('.//span[@class="nick_name"]')
                    #         cmt['nickname'] = e.text.strip()
                    #     except:
                    #         continue
                    #     # 댓글 내용
                    #     e = cmt_e.find_element_by_xpath('.//div[@class="comment_content"]')
                    #     self.move_to_element(e)
                    #     cmt['contents'] = e.text
                    #     # 댓글 내용중에 멘션이 있을 경우 포함
                    #     # inner_html = cmt_e.get_attribute('innerHTML')
                    #     # if inner_html.find("text_nickname") > 0:
                    #     #     tag = cmt_e.find_element_by_xpath('.//a[@class="text_nickname"]').text
                    #     #     cmt['contents'] = tag + ' ' + comment
                    #     # else:
                    #     #     cmt['contents'] = comment
                    #     # 댓글 작성 시각
                    #     e = cmt_e.find_element_by_xpath('.//span[@class="date"]')
                    #     e_a = e.text.strip()
                    #     e_b = e_a.partition('\n')[0]
                    #     create_t = e_b.partition('. ')
                    #     create_ts = create_t[0] + ' ' + create_t[2] + ':00'
                    #     cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                    #         '%Y.%m.%d %H:%M:%S')
                    #
                    #     cmt['comment_img_url'] = []
                    #     cmt['comment_img'] = []
                    #     # 댓글 스티커 or 이미지
                    #     # e = cmt_e.find_element_by_xpath('.//div[@class="comment_content"]')
                    #     # if e.find_element_by_xpath('//picture//img[@class="image"]') > 0:
                    #     #     cmt['comment_img_url'].append(e_b.get_attribute('src'))
                    #     #     cmt_img_f = self.get_safe_path(
                    #     #         self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"] + "_0"}.png')
                    #     #     e_b.screenshot(cmt_img_f)
                    #     #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                    #         # 댓글 목록에 추가
                    #     msg['comment_list'].append(cmt)
                    #     self.logger.info(f'   [{i + 1}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                    # return
                    self.save_attachment(msg)
                    self.save_image(msg)
                    self.output['article_list'].append(msg)
                    if self.config['target']['is_separate_article']:
                        self.save_article(msg)
                    # 첫번째로 크롤링한 게시글의 작성시간을 저장
                    if self.output["latest_create_article_ts"] is None:
                        self.output["latest_create_article_ts"] = msg['create_ts']
                except:
                    self.logger.info('삭제된 게시글')
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], '수집 불가',
                                                       f'{self.index}.png')
                    self._screenshot(msg_capture_f)
        except Exception as err:
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
    def save_attachment(self, article):
        for i, attach_url in enumerate(article['attachment_url']):
            article_attach_p = self.get_safe_path(
                self.config['target']['folder'],
                article['article_id'],
                article['attachment_name'][i]
            )
            file = requests.get(attach_url, stream=True)
            with open(article_attach_p, "wb") as d_file:
                for chunk in file.iter_content(chunk_size=1024):
                    if chunk:
                        d_file.write(chunk)

    # ==========================================================================
    def _screenshot(self, f):
        # S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        # self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)

        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        height = self.driver.execute_script('return document.body.scrollHeight')
        width = self.driver.execute_script('return document.body.scrollWidth')
        self.driver.set_window_size(S('Width') + width / 2, S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        # self.driver.find_element_by_xpath('//div[@class="article_wrap"]').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="se-main-container"]').screenshot(f)

    # ==========================================================================
    def save_image(self, article):
        # 게시글 이미지
        # for j, sub_e_url in enumerate(article['image_url_list']):
        #     try:
        #         article_img_p = self.get_safe_path(
        #             self.config['target']['folder'],
        #             article['article_id'],
        #             f'{j}.png'
        #         )
        #         # 가끔 에러 나는 경우가 있슴
        #         for count in range(10):
        #             try:
        #                 urlretrieve(sub_e_url, article_img_p)
        #                 article['image_list'].append(f'{j}.png')
        #                 break
        #             except:
        #                 # ssl 인증서 오류 해결
        #                 ssl._create_default_https_context = ssl._create_unverified_context
        #                 self.logger.info(f'save_img: {j}.png : retry{count}')
        #                 continue
        #     except Exception as err:
        #         self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

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
    def w_headless(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        options.add_argument("disable-gpu")

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['params']['kwargs']['url'])
        cookies = pickle.load(open(self.cookie_path, "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    # ==========================================================================
    def a_cookie(self):
        try:
            if not os.path.isfile(self.cookie_path):
                print("no cookie")
                self.logger.error('The cookie file could not be found.')
                raise
            cookies = pickle.load(open(self.cookie_path, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
            self.implicitly_wait(after_wait=1)
            e = self.get_by_xpath('//*[@id="gnb_login_button"]/..')
            if e.get_attribute('style') != 'display: none;':
                self.logger.error('Cookie file need to be update.')
                raise
        except Exception as e:
            raise LOGINERROR(e)

    # ==========================================================================
    def a_user_data(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            options.add_argument("disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            # options.add_argument(f"--user-data-dir={self.user_data_path}")
            # options.add_argument('headless')

            self.driver.start_session(options.to_capabilities())
            self.driver.get(self.config['params']['kwargs']['url'])
            self.driver.refresh()
            self.implicitly_wait(after_wait=1)
            e = self.get_by_xpath('//*[@id="gnb_login_button"]/..')
            if e.get_attribute('style') != 'display: none;':
                self.logger.error('userData dir need to be update.')
                raise
        except Exception as e:
            raise LOGINERROR(e)

    # ==========================================================================
    def start(self, i=None):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            # if i == 0:
            #     self.login()
            #     self.w_headless()
            # else:
            #     self.a_cookie()
            # self.a_user_data()
            # self.search()
            # self.login()
            self.a_cookie()
            self.get_page()
            return 0
        except LOGINERROR as e:
            self.logger.error(e)
            return 1
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9
        finally:
            # print(self.output["latest_create_article_ts"])
            # print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            self.save()
            # if self.config['target']['is_save']:
            #     self.save()
            # self.clean()


################################################################################
def do_start(**kwargs):
    with NaverCafeSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'cafe_naver_통합.yaml'
    do_start(config_f=_config_f)
