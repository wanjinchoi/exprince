"""
====================================
 :mod:`cafe/cafe_daum`
====================================
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
#
# Change Log
# --------
#  * [2024/10/31]
#     - 본문에서 '검색 허용 해제 필수'라는 단어가 수집 될 경우 제거하는 로직 추가
#  * [2024/10/23]
#     - 게시글 이미지 저장을 2회 반복하여 Slack 컨텐츠 오류 발생(이미지 수량 불일치).
#     - save_image 로직 주석 처리. 게시글에서 이미지 수집하는 기능만 변경X
#  * [2024/10/15]
#     - '투표 결과 보기' 버튼 클릭 후 스크린샷 찍도록 순서 변경. 이전에는 스크린샷에 투표가 누락됨
#  * [2024/09/02]
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
import pickle
import tarfile
import sqlite3
import datetime
import traceback
import urllib.request
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from bs4 import BeautifulSoup
from collections import OrderedDict
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

################################################################################

# 이미지 다운(403 에러 해결코드)
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

################################################################################
class LOGINERROR(Exception):
    pass

################################################################################
class DaumCafeSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = "C:\\work\\voc_data\\logs\\vote_data"
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'Daumvote_data.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        self.cookie_path = r"C:\work\voc\yaml\카페\다음\cookies.pkl"

        # 카페id
        self.cafe_id = self.config['params']['kwargs']['url'].rpartition('/')[2]
        self.keyword = self.config['params']['site']['search']

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
        # 안에 값이 변경 될 우려가 있음.
        del out_config['params']['site']['passwd']
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
    def login(self):
        try:
            # 바로 로그인창이 뜨는 경우가 존재함. http://cafe.daum.net/Tlwkftlqkftlldlqkf
            if self.driver.current_url.find('accounts/loginform.do') == -1:
                # 해당 iFrame으로 이동
                self.switch_to_iframe_by_name('down')
                # 로그인 클릭
                e = self.get_by_xpath('//a[@class="btn fl #cafenavi-login_btn"]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

            # login 화면

            try:
                # 카카오계정으로 로그인
                if self.config['params']['site']['userid'].find('kakao') > 0:
                    e = self.get_by_xpath('//a[@class="link_login link_klogin"]',
                                          cond='element_to_be_clickable')
                # 다음계정으로 로그인
                else:
                    e = self.get_by_xpath('//a[@class="link_login link_dlogin"]',
                                          cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            except:
                pass

            # 개인 PC에서 로그인 화면에서 브라우저를 찾지 못하는 경우가 있음
            window_handles = self.driver.window_handles
            self.driver.switch_to.window(window_handles[0])
            # 사용자 입력
            e = self.get_by_xpath('//input[@class="tf_g tf_email"]|//input[@id="id"]|//input[@id="input-loginKey"]|//input[@id="loginKey--1"]|(//div[@class="box_tf"]/input)[1]')
            # self.send_keys_clipboard(e, self.config['params']['site']['userid'])
            self.send_keys(e, self.config['params']['site']['userid'])
            time.sleep(1)

            # 암호 입력
            e = self.get_by_xpath('//input[@data-type="password"]|//input[@name="pw"]|//input[@id="input-password"]|//input[@id="password--2"]|(//div[@class="box_tf"]/input)[2]')
            # self.send_keys_clipboard(e, self.config['params']['site']['passwd'])
            self.send_keys(e, self.config['params']['site']['passwd'])
            time.sleep(1)

            # 로그인 단추 누름
            e = self.get_by_xpath('//button[@class="btn_g btn_confirm submit"]|//button[@class="btn_g highlight"]|//button[@class="btn_g highlight submit"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 로그인 쿠키를 담아둠
            pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))

            self.switch_to_iframe_by_name('down')
            e_ab = self.get_by_xpath('//*[@id="minidaum"]')
            inner_html = e_ab.get_attribute('innerHTML')
            if inner_html.find('btn fl #cafenavi-login_btn') > 0:
                self.logger.error('로그인 실패')
                raise
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise LOGINERROR(e)
        finally:
            self.switch_from_iframe()

    # ==========================================================================
    def get_cafe_info(self):
        cafe_info = {}
        try:
            self.switch_to_iframe_by_name('down')
            e = self.get_by_xpath('//a[@class="profile_link"]')
            self.safe_click(e)
            self.implicitly_wait()

            # 해당 iFrame으로 이동
            self.switch_to_iframe_by_name('down')
            # 카페정보/내정보 사이를 스위칭하는데 기본이 카페정보임
            # e = self.get_by_xpath('//a[@class="txt_title1"]',
            #                       cond='element_to_be_clickable')
            # self.safe_click(e)

            cafe_info['url'] = self.config['params']['kwargs']['url']
            # 카페 이름
            e = self.get_by_xpath('//strong[@class="tit_profile"]')
            cafe_info['name'] = e.get_attribute('innerText').split('\n')[1]
            # 카페 단계 : 193단계(487677점
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[1]/dd/span[1]')
            cafe_info['rank'] = e.text.strip()
            # # 카페 프로필 : 레전드 (공개)
            # e = self.get_by_xpath('//a[@class="profile_link"]')
            # cafe_info['profile'] = e.text.strip()
            # 카페 아이콘
            e = self.get_by_xpath('//img[@class="img_profile"]')
            cafe_info['icon_src'] = e.get_attribute('src')
            # 카페 지기
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[2]/dd')
            cafe_info['manager'] = e.text.strip()
            # 카페 회원수
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[3]/dd/span[1]/em')
            cafe_info['num_members'] = int(e.text.strip().replace(',', ''))
            # 카페 개설일
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[3]/dd/span[2]/em')
            cafe_info['since'] = e.text.strip()
            # 카페 방문수
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[4]/dd/span[1]/em')
            cafe_info['num_visitors'] = int(e.text.strip().replace(',', ''))
            # 카페앱수
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[5]/dd')
            cafe_info['num_apps'] = int(e.text.strip().replace(',', ''))
            # 카페 설명
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[9]/dd/p')
            cafe_info['category'] = e.text.strip()
            # 카페 가입조건
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[7]/dd')
            cafe_info['register_type'] = e.text.strip()
            # 카페 가입방식
            e = self.get_by_xpath('//div[@class="profile_dl_wrap"]/dl[8]/dd')
            cafe_info['keywords'] = []
            for ae in e.find_elements_by_xpath('.//span[@class="item_profile"]'):
                cafe_info['keywords'].append(ae.text.strip())

        finally:
            self.output['cafe_info'] = cafe_info
            self.switch_from_iframe()
            # 이전 페이지
            self.driver.back()

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
                    # inner_html = e.get_attribute('innerHTML')
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
                    # cmt['create_ts'] = create_ts
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                else:
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
                if msg['num_comments_plus'] == True:
                    if len(msg['comment_list']) >= 100:
                        return True
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

    # ========================================================================
    def remove_html(self):
        try:
            # 하당 광고창
            under_ad = self.get_by_xpath("//div[@id='ad_wrapper']")
            # 왼쪽 메뉴창
            left_menu = self.get_by_xpath("//div[@class='menuBox']")
            # 카페 왼쪽 메뉴 목록
            cafe_menu = self.get_by_xpath("//div[@id='cafemenu']")
            # 게시글 목록
            article_list = self.get_by_xpath("//div[@class='cont_boardlist article_more_board search_result']")

            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", under_ad)
            self.driver.execute_script("arguments[0].remove();", left_menu)
            self.driver.execute_script("arguments[0].remove();", cafe_menu)
            self.driver.execute_script("arguments[0].remove();", article_list)
        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass

    # ==========================================================================
    def get_article(self, article):
        try:
            self.output['article_list'] = []
            self.output['config']['params']['site']['user_type'] = article[0]
            self.output['config']['params']['site']['search_type'] = article[4]
            self.output['config']['params']['site']['service'] = article[5]
            self.output['config']['params']['site']['search'] = article[7]
            self.output['config']['params']['site']['site_name'] = article[2]
            self.output['config']['params']['site']['site_number'] = article[8]
            self.output['config']['params']['kwargs']['url'] = article[9].split('/')[0] + '//' + article[9].split('/')[2] + '/' + article[9].split('/')[3]
            self.driver.get(article[9])
            self.implicitly_wait(after_wait=1)
            self.site_num = article[8]
            start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            folder_name = "_".join([str(self.site_num), article[7], start_ts])
            self.config['target']['folder'] = f'C:/work/voc_data/latest/{article[3]}/{article[1]}' + '/' + folder_name
            self.output['config']['target']['folder'] = self.config['target']['folder']
            msg = {
                'page': self.cur_page,
                'row': 1,
                'user_type': article[0],
                'site': article[1],
                'site_name': article[2],
                # 'site_board': self.config['params']['site']['site_board'],
                'channel': article[3],
                'search_type': article[4],
                'service': article[5],
                'article_id': article[6],
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
                'article_url': article[9],
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
            # 데이터 저장 여부 True
            self.save_data = True
            # delay_a = 1
            self.logger.info(f'article_id[{msg["article_id"]}]')
            click_count = 1
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            try:
                # # "카페 메인 (cafe_main)" iFrame으로 이동
                self.switch_to_iframe_by_name('down')
                # 게시글 URL로 HTML 소스 가져오기
                article_source = self.driver.page_source
                # BeautifulSoup을 사용하여 HTML 파싱
                soup = BeautifulSoup(article_source, 'html.parser')
                try:
                    # 회원 등급 제한 게시글 확인
                    soup.find('div', class_='sub_content_box').text
                    self.logger.info(f'회원 등급 제한 게시글입니다. title={msg["title"]}, 게시글ID={msg["article_id"]}, URL={msg["article_url"]}')
                    self.save_data = False
                    return
                except:
                    pass
                try:
                    # 삭제된 게시글
                    soup.find('p', class_='desc_g').text
                    self.logger.info(f'삭제된 게시글입니다. URL={msg["article_url"]}')
                    self.save_data = False
                    return
                except:
                    pass
                self.remove_html()
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
                # 상단
                high_e = soup.find('div', class_='bbs_read_tit')
                # 게시판 이름
                msg['board_name'] = high_e.find('a', class_='txt_subhead').text.strip()
                # 작성자
                try:
                    # 작성자: 닉네임
                    msg['author'] = high_e.find('a', class_='link_item').text.strip()
                except:
                    # 작성자: 익명
                    msg['author'] = high_e.find('span', class_='txt_name').text.strip()

                # 추천, 조회수, 작성일시, 댓글 수
                article_info = high_e.find_all('span', class_='txt_item')
                # 추천(int) : "추천 0"
                msg['like'] = int(re.sub(r'[^0-9]', '', article_info[0].text.strip()))
                # 조회수(int) : "조회 93"
                msg['view_count'] = int(re.sub(r'[^0-9]', '', article_info[1].text.strip()))
                # 작성일시
                create_ts = article_info[2].text.strip()
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                # 댓글 수(int)
                msg['num_comments'] = int(re.sub(r'[^0-9]', '', article_info[3].text.strip()))
                # 댓글 수 100개 이상 시 체크
                if msg['num_comments'] >= 100:
                    msg['num_comments_plus'] = True
                else:
                    msg['num_comments_plus'] = False

                # 본문
                content_e = soup.find('div', id='user_contents')
                msg['contents'] = content_e.text.strip()
                # 우리동네 목욕탕의 경우 검색 허용 해제 필수가 기본 템플릿이어서 필요없는 내용이 수집되어 삭제
                msg['contents'] = msg['contents'].replace('검색 허용 해제 필수', '')
                # 투표
                if len(content_e.find_all('div', class_='figure-poll')) > 0:
                    self.vote_data = True
                    self.get_vote_data(msg)
                # 스크린샷
                if self.config['params']['site']['capture_article']:
                    # save capture
                    # e_body = self.get_by_xpath('//body')
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{msg["article_id"]}.png')
                    if self.config['params']['kwargs']['headless']:
                        self._screenshot(msg_capture_f)
                    else:
                        self.full_screenshot(msg_capture_f)

                self.switch_to_iframe_by_name('down')
                # 이미지 주소 가져오기
                content_e = soup.find('div', id='user_contents')
                msg['image_list'] = []
                msg['image_url_list'] = []
                img_tags = content_e.find_all('img')
                for j, img in enumerate(img_tags):
                    if 'src' in img.attrs:  # 이미지 태그에 'src' 속성이 있는지 확인
                        try:
                            article_img_p = self.get_safe_path(
                                self.config['target']['folder'],
                                msg['article_id'],
                                f'{j}.png'
                            )
                            urlretrieve(img['src'], article_img_p)
                            msg['image_url_list'].append(img['src'])
                            msg['image_list'].append(f'{j}.png')
                        except:
                            # 실패한 이미지 URL 본문 내용에 저장
                            msg['contents'] += f'다운로드 실패 이미지: {img["src"]}'
                            self.logger.info(f'save_img error: {j}.png')

                # 투표 iframe 내부 데이터를 못가져옴
                # msg['vote'] = []
                # for vote in content_e.find_all('div', class_='figure-poll'):
                #     # iframe 태그는 다른 HTML 문서를 포함하여 iframe을 찾아서 URL 요청을 해야함 (네트워크 요청 및 HTML 파싱 속도에 의존).
                #     vote_content = vote.find('iframe', id='pollFrame')
                #     # iframe URL
                #     vote_e = vote_content['src']
                #     # iframe 정보 요청
                #     response = requests.get(vote_e)
                #     # iframe의 HTML 내용 파싱
                #     iframe_html = response.text
                #     iframe_soup = BeautifulSoup(iframe_html, 'html.parser')
                #     iframe_soup.find('strong', class_='tit_subject').text.strip()

                # 댓글 : 댓글이 없는 경우 있음
                if msg['num_comments'] <= 0:
                    pass
                else:
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
                                if self.get_comments(msg):
                                    is_next = False
                                    break
                                is_next = True
                                continue
                            if is_next:
                                self.safe_click(coments_e)
                                self.implicitly_wait(after_wait=1)
                                click_count += 1
                                break
                        if not is_next:
                            break
            except:
                self.save_data = False
                return
        except Exception as err:
            raise
        finally:
            if self.save_data:
                # self.save_image(msg)
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    self.save_article(msg)
                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = msg['create_ts']
                print(self.config['target']['folder'])
                self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
                if self.config['target']['is_save']:
                    self.save()
                self.clean()
            # 뒤로 돌아감 댓글
            # for _ in range(click_count):
            #     self.driver.back()
            self.switch_to_main_window()
            self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_vote_data_db(self):
        try:
            vote_data_path = r'C:\work\voc_data\logs\vote_db'
            if not os.path.exists(vote_data_path):
                self.logger.info('Vote_DB_file is not exist in this PC')
                return
            else:
                # SQLite 데이터베이스 연결 및 커서 생성
                conn = sqlite3.connect(r'C:\work\voc_data\logs\vote_db' + '/' + 'vote_data.db')
                cursor = conn.cursor()
                # 현재 시간 구하기
                current_time = datetime.datetime.now()
                current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

                # 1일 전 날짜 구하기 strp
                previous_day = current_time - timedelta(days=30)
                previous_day_str = previous_day.strftime('%Y-%m-%d %H:%M:%S')

                # DB 쿼리문
                query = """
                                SELECT *
                                FROM vote_Articles
                                WHERE collection_date >= ?
                                ORDER BY collection_date DESC;
                            """
                cursor.execute(query, [previous_day_str])

                # 결과 가져오기
                rows = cursor.fetchall()
                # self.logger.info(f'DB 쿼리문: {query}\n 조회한 날짜: {previous_day_str} ~ {current_time_str}, 키워드: {keyword}')
                self.logger.info(f'조회한 날짜: {previous_day_str} ~ {current_time_str}')

                # 연결 종료
                cursor.close()
                conn.close()

                self.article_list = rows

            self.logger.info("투표 게시글 추출 완료")

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
    def a_cookie(self):
        # 기존
        # cookies = pickle.load(open("cookies.pkl", "rb"))
        # for cookie in cookies:
        #     self.driver.add_cookie(cookie)
        # 방석위로 모여라 이슈로 인해 수정
        if self.config['params']['kwargs']['url'] == "https://cafe.daum.net/Duckgu":
            self.driver.get('https://cafe.daum.net/ok1221')
        cookies = pickle.load(open(self.cookie_path, "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        self.driver.refresh()
        self.driver.get(self.config['params']['kwargs']['url'])
        self.implicitly_wait(after_wait=1)

        # ==========================================================================
    def check_login(self):
        # 해당 iFrame으로 이동
        self.switch_to_iframe_by_name('down')
        # 로그인 클릭
        e = self.get_by_xpath('//span[@class="btn_txt p11"]')
        if e.text.strip() == '로그인':
            self.login()

    # ==========================================================================
    def start(self):
        try:
            self.a_cookie()
            # 로그인 체크 로직
            self.check_login()
            if os.path.isfile(f'C:\\work\\voc_data\\logs\\vote_db\\vote_data.db'):
                self.get_vote_data_db()
                for article in self.article_list:
                    # 수집
                    self.get_article(article)
                return 0
            else:
                self.logger.info('Vote_DB_file is not exist in this PC')
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            print(10)
            return 1


################################################################################
def do_start(**kwargs):
    with DaumCafeSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'cafe_daum_articleID.yaml'
    do_start(config_f=_config_f)
