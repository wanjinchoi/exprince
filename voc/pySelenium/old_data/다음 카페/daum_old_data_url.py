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
#  * [2022/09/28]
#     - 댓글 오류 수정, 로그인 버튼 xpath 추가
#  * [2022/09/23]
#     - 로그인 xpath 수정
#  * [2022/09/22]
#     - 댓글수가 100개 이상일 경우 100개 까지만 수집
#  * [2022/07/06]Kyobong An
#     - 바로 로그인창이 뜨는 카페가 존재함. (우리동네 목욕탕)
#  * [2022/06/20]Kyobong An
#     - 기존 article_id 앞에 카페id를 붙임 (분석팀 요청)
#  * [2022/04/05] Kyobong An
#     - 다음 계정 로그인 추가
#  * [2022/03/16] Kyobong An
#     - 포맷 적용
#  * [2022/01/26] Kyobong An
#     - 출력값 변경 아웃풋 파일 path와 최신글의 작성시간
#  * [2022/01/14] Kyobong An
#     - 로그인은 한번만 하고 키워드 여러개 돌릴 수 있게 변경함.
#     - 검색어 필터 기능 추가
#  * [2022/01/14] Kyobong An
#     - 댓글읽는 속도 개선
#     - 분석팀과 협의된 내용 적용
#     - 일부 데이터 잘못 가져오던 부분 수정
#     - search_complex, latest_create_article_ts 추가
#     - 댓글이모티콘은 캡처로 처리
#  * [2022/01/03] Kyobong An
#     - article_url 추가. 각 게시글 별로 url추출
#  * [2021/12/29]
#     - \n ==> \\n 부분 필요없음
#  * [2021/12/22]
#     - article 별로 별도 저장 시점 조종, save_article()
#     - image_list 에 직접 저장하는 것을 save_article로 옮김
#     - start() 에서 save()를 finally 블락으로 이동
#     - 입력에 stop_article_older_than 조건 추가, stop_article_older_than() 에서 처리
#     - 검색결과 없는 경우, next_page 에서 exception is_done=True 하도록
#  * [2021/12/20] Kyobong An
#     - 내용 이미지, 댓글에 이모틴콘 또는 이미지 가져오는 것추가 가려진글(작성자와운영자만 볼수 있는 댓글)에 대해서 key 추가.
#     - cafe_info 설립일, 설명, 가입조건등 추가
#  * [2021/12/06]
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
import datetime
import traceback
import openpyxl
import urllib.request
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


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
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        self.cookie_path = r'C:\work\voc\pySelenium\cafe\daum\cookies.pkl'
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DaumCafeSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 특정 키워드는 키워드의 성격을 바꿔줌
        if self.search_index == 0:
            n_user_type = len(self.config['params']['site']['user_type'].split(','))
            n_search = len(self.config['params']['site']['search'].split(','))
            n_search_type = len(self.config['params']['site']['search_type'].split(','))
            n_service = len(self.config['params']['site']['service'].split(','))
            if n_user_type != n_search_type or n_search != n_service or n_user_type != n_search:
                err_msg = 'the length of list of user_type, search, search_type, service is different'
                # print(err_msg)
                self.logger.error(err_msg)
                raise ValueError(err_msg)
        self.config['params']['site']['user_type'] = self.config['params']['site']['user_type'].split(',')[i]
        self.config['params']['site']['search_type'] = self.config['params']['site']['search_type'].split(',')[i]
        self.config['params']['site']['service'] = self.config['params']['site']['service'].split(',')[i]
        self.config['params']['site']['search'] = keyword

        # 카페id
        self.cafe_id = self.config['params']['kwargs']['url'].rpartition('/')[2]

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
        if 'search_complex' in self.config['params']['site']:
            out_config['params']['site']['search_complex'] = \
                self.config['params']['site']['search_complex'].split(',')[i]
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

            # 사용자 입력
            e = self.get_by_xpath('//input[@class="tf_g tf_email"]|//input[@id="id"]|//input[@id="loginKey--1"]')
            # self.send_keys_clipboard(e, self.config['params']['site']['userid'])
            self.send_keys(e, self.config['params']['site']['userid'])
            time.sleep(1)

            # 암호 입력
            e = self.get_by_xpath('//input[@data-type="password"]|//input[@name="pw"]|//input[@id="password--2"]')
            # self.send_keys_clipboard(e, self.config['params']['site']['passwd'])
            self.send_keys(e, self.config['params']['site']['passwd'])
            time.sleep(1)

            # 로그인 단추 누름
            e = self.get_by_xpath('//button[@class="btn_g highlight submit"]|//button[@class="btn_g highlight"]',
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
    def search(self):
        try:
            # 해당 iFrame으로 이동
            self.switch_to_iframe_by_name('down')

            # 검색어 입력
            e = self.get_by_xpath('//input[@name="search_left_query"]')
            if 'search_complex' in self.config['params']['site']:
                self.send_keys(e, self.config['params']['site']['search_complex'].split(',')[self.search_index] + Keys.ENTER)
            else:
                self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
            self.implicitly_wait(after_wait=1)

            # 검색어 필터
            e = self.get_by_xpath('//select[@name="item"]')
            e_s = e.find_elements_by_xpath('./option')
            for i, e_filter in enumerate(e_s):
                if e_filter.text.find(self.config['params']['site']['search_filter']) >= 0:
                    self.safe_click(e_filter)
                    self.implicitly_wait(after_wait=1)
                    e = self.get_by_xpath('//img[@alt="검색"]')
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=1)
                    break
        finally:
            self.switch_from_iframe()

    # ==========================================================================
    def get_comments(self, msg):
        try:
            # self.switch_to_iframe_by_name('down')
            try:
                e = self.get_by_xpath('//ul[@id="commentList"]')
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
                is_reply = cmt_e.get_attribute('class') == 'reply_on  '
                cmt['is_reply'] = is_reply
                if not is_reply:
                    cmt['parent_comment_id'] = ""
                else:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = parent_comment_id
                # is_deleted = False
                # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
                # inner_html = cmt_e.get_attribute('innerHTML')
                # if inner_html.find('opt_more_g') > 0:
                #     e = cmt_e.find_element_by_xpath('.//div[@class="opt_more_g"]')
                #     cmt['nickname'] = e.text.strip()
                # else:
                #     is_deleted = True
                # if not is_deleted:
                # 댓글 내용
                e = cmt_e.find_element_by_xpath('.//span[@class="txt_detail"]')
                self.move_to_element(e)
                cmt['contents'] = e.text.strip()
                is_deleted = False
                if cmt['contents'] == '삭제된 댓글입니다.':
                    is_deleted = True
                if not is_deleted:
                    # e = cmt_e.find_element_by_xpath('.//div[@class="opt_more_g"]')
                    # cmt['nickname'] = e.text.strip()
                    # 댓글에 이모티콘 혹은 이미지
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    inner_html = e.get_attribute('innerHTML')
                    if inner_html.find('img') > 0:
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
                    e = cmt_e.find_element_by_xpath('.//span[@class="created_at"]')
                    self.move_to_element(e)
                    create_ts = e.text.strip()
                    # if len(create_ts.split()) == 1:
                    #     doday_ts = datetime.datetime.today().strftime("%Y.%m.%d")
                    #     create_ts = f'{doday_ts[2:]} ' + create_ts
                    # cmt['create_ts'] = create_ts
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d').strftime('%Y.%m.%d 00:00:00')
                    msg['comment_list'].append(cmt)
                else:
                    pass
            # 댓글 목록에 추가
            if msg['num_comments_plus'] == True:
                if len(msg['comment_list']) >= 100:
                    return True
            self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
            if len(msg['comment_list']) >= msg['num_comments']:
                return
        except Exception as err:
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):
        self.safe_click(title_e)
        self.implicitly_wait(after_wait=1)
        click_count = 1
        try:
            b = self.driver.find_element_by_xpath(
                '//div[@id="content"]//tbody/tr[@class="pos_rel"]/td[@class="cb pos_rel"]/div[@class="sub_content_box"]//a[@class="u"]')
            if b.text.find('이 카페 회원 등급 보기') >= 0:
                pass
        except:
            try:
                self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
                # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
                delay_a = random.uniform(
                    self.config['params']['site']['delay']['article']['min'],
                    self.config['params']['site']['delay']['article']['max'],
                )
                time.sleep(delay_a)
                # "카페 메인 (cafe_main)" iFrame으로 이동
                self.switch_to_iframe_by_name('down')
                if self.config['params']['site']['capture_article']:
                    # save capture
                    # e_body = self.get_by_xpath('//body')
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{msg["article_id"]}.png')
                    if self.config['params']['kwargs']['headless']:
                        self._screenshot(msg_capture_f)
                    else:
                        self.full_screenshot(msg_capture_f)

                content_e = self.get_by_xpath('//div[@class="primary_content"]')
                # 게시판 이름
                e = content_e.find_element_by_xpath('.//a[@class="txt_subhead"]')
                msg['board_name'] = e.text.strip()
                # 추천 : "추천 0"
                e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][1]')
                msg['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
                # 조회수 : "조회 93"
                e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][2]')
                msg['view_count'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
                # 작성일시
                e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][3]')
                create_ts = e.text.strip()
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                # 댓글수
                # e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][4]/a')
                # msg['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
                # 투표

                # 본문
                e = content_e.find_element_by_xpath('.//div[@id="user_contents"]')
                msg['contents'] = e.text.strip()

                # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
                # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
                inner_html = e.get_attribute('innerHTML')
                # 이미지 주소 가져오기
                msg['image_list'] = []
                msg['image_url_list'] = []
                if inner_html.find('txc-image') > 0:
                    # for sub_e in e.find_elements_by_xpath('.//img[@class="txc-image"]'):
                    for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                        sub_e_url = sub_e.get_attribute('src')
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
                for _ in range(click_count):
                    self.driver.back()

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
    def get_page(self):
        try:
            wb = openpyxl.load_workbook(self.config['target']['url_list_path'], data_only=True)
            ws = wb.active
            row_max = ws.max_row
            for i in range(1, row_max+1):
                # 윈도우 개수 확인
                for _ in self.driver.window_handles:
                    if len(self.driver.window_handles) == 1:
                        break
                    self.switch_to_window(1)
                    self.driver.close()
                    self.implicitly_wait(after_wait=0.5)
                self.switch_to_main_window()
                self.index = i
                self.url = ws['A' + str(i)].value
                self.driver.get(self.url)
                self.implicitly_wait(after_wait=1)
                self.logger.info(f'>>>>>>{self.index} start')
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
                        'num_comments_plus': None,
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
                    # "카페 메인 (cafe_main)" iFrame으로 이동
                    # self.switch_to_iframe_by_name('down')
                    # 게시판 이름
                    e = self.get_by_xpath('//div[@class="cafe_navi "]//strong')
                    msg['board_name'] = e.text.strip()
                    header = self.get_by_xpath('//div[@class="view_subject #subject_area"]')
                    # 5) 작성자: author 링크를 못 찾으면 "(익명)"
                    try:
                        se = header.find_element_by_xpath('./span[@class="txt_subject"]/text()[1]')
                        msg['author'] = se.text.strip()
                    except:
                        msg['author'] = ''
                    # 4) 게시글 URL:  article_url
                    msg['article_url'] = self.url
                    # 1) 게시글id : article_id
                    a = self.url.split('/')[5]
                    if '?' in a:
                        e_a = a.split('?')[0]
                    else:
                        e_a = a
                    msg['article_id'] = e_a
                    # 2) 제목: title
                    se = header.find_element_by_xpath('./h3')
                    msg['title'] = se.text.strip()
                    # 작성일시
                    e = header.find_element_by_xpath('./span[@class="txt_subject"]/span[@class="num_subject"][1]')
                    create_ts = e.text.strip()
                    msg['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d').strftime(
                        '%Y.%m.%d 00:00:00')
                    # 조회수 : "조회 93"
                    e = header.find_element_by_xpath('./span[@class="txt_subject"]/span[@class="num_subject"][2]')
                    msg['view_count'] = int(e.text.strip())
                    # msg['view_count'] = int(re.sub(r'[^0-9]', '', e.text.strip()))

                    # 3) 댓글수: num_comments
                    try:
                        e = header.find_element_by_xpath('./span[@class="desc_subject"]//span[@class="num_cmt"]')
                        if e:
                            msg['num_comments'] = int(e.text.strip())
                            if msg['num_comments'] >= 100:
                                msg['num_comments_plus'] = True
                            else:
                                msg['num_comments_plus'] = False
                    except:
                        msg['num_comments'] = 0
                        msg['num_comments_plus'] = False
                    # 본문
                    e = self.get_by_xpath('//div[@class="view_info"]')
                    msg['contents'] = e.text.strip()
                    # 스크린샷
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{msg["article_id"]}.png')
                    self.full_screenshot(msg_capture_f)
                    # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
                    # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
                    inner_html = e.get_attribute('innerHTML')
                    # 이미지 주소 가져오기
                    msg['image_list'] = []
                    msg['image_url_list'] = []
                    if inner_html.find('txc-image') > 0:
                        # for sub_e in e.find_elements_by_xpath('.//img[@class="txc-image"]'):
                        for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                            sub_e_url = sub_e.get_attribute('src')
                            msg['image_url_list'].append(sub_e_url)

                    # 댓글 : 댓글이 없는 경우 있음
                    if msg['num_comments'] <= 0:
                        pass
                    else:
                        msg['comment_list'] = []
                        # 코멘트 페이징이 있는 경우
                        try:
                            e = self.get_by_xpath('//span[@class="desc_subject"]/a[@class="link_cmt make-return-uri #comment_upper_btn"]')
                            e_a = e.get_attribute('href')
                            self.driver.execute_script(f"window.open('{e_a}');")
                            self.implicitly_wait(after_wait=1)
                            self.switch_to_main_window()
                            self.switch_to_window(1)
                            comments = self.get_by_xpath('//div[@class="paging_board"]/span')
                            comments_list = comments.find_elements_by_xpath('./span[@class="num_page"]')
                            # 1을 클릭하기위함.
                            self.safe_click(comments_list[0])
                            self.implicitly_wait(after_wait=1)
                            for comments_e in comments_list:
                                self.safe_click(comments_e)
                                self.get_comments(msg)
                        except:
                            self.logger.error(f'{self.index} 댓글 수집 에러 발생')
                        self.switch_to_main_window()
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=1)
                        self.switch_to_main_window()
                    self.save_image(msg)
                    self.output['article_list'].append(msg)
                    if self.config['target']['is_separate_article']:
                        self.save_article(msg)
                        self.logger.info(f'>>>>>>{self.index} end')
                    # 첫번째로 크롤링한 게시글의 작성시간을 저장
                    if self.output["latest_create_article_ts"] is None:
                        self.output["latest_create_article_ts"] = msg['create_ts']
                except:
                    self.logger.info(f'{self.index}: 삭제된 게시글')
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], '수집 불가', f'{self.index}.png')
                    self._screenshot(msg_capture_f)
        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
            raise

    # ==========================================================================
    def next_page(self):
        try:
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_iframe_by_name('down')
            # 페이지 목록
            next_page_str = str(self.cur_page + 1)
            ple = self.get_by_xpath('//div[@class="paging pagingtype_search"]', timeout=2)
            for pa in ple.find_elements_by_xpath('.//a[@class="num_box"]'):
                if pa.text.strip() == next_page_str:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            try:
                next_e = ple.find_element_by_xpath('.//span[@class="num_next"]/a')
                self.safe_click(next_e)
                self.implicitly_wait()
                return self.next_page()
            except:
                self.is_done = True
        except Exception as err:
            self.logger.error(f'Cannot find Result!')
            self.is_done = True
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
        try:
            if not os.path.exists(os.path.dirname(self.cookie_path)):
                print("no cookie")
                self.logger.error('The cookie file could not be found.')
                os.makedirs(os.path.dirname(self.cookie_path))
            cookies = pickle.load(open(self.cookie_path, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
            self.implicitly_wait(after_wait=1)
            self.switch_to_iframe_by_name('down')
            e = self.get_by_xpath('//li[@class="mini_btn"][1]//span')
            if e.text.strip() != '로그아웃':
                self.logger.error('Cookie file need to be update.')
                self.login()
                cookies = pickle.load(open(self.cookie_path, "rb"))
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
                self.driver.refresh()
                self.implicitly_wait(after_wait=1)
                if e.text.strip() != '로그아웃':
                    raise

        except Exception as e:
            raise LOGINERROR(e)

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            # if self.search_index == 0:
            self.login()
            # else:
            #     self.a_cookie()
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
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):

    with open(kwargs['config_f'], encoding='utf-8') as ifp:
        f_yaml = yaml.load(ifp, yaml.SafeLoader)
        for i, keyword in enumerate(f_yaml['params']['site']['search'].split(',')):
            with DaumCafeSearch(kwargs['config_f'], keyword, i) as ws:
                ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'cafe_daum.yaml'
    do_start(config_f=_config_f)
