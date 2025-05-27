"""
====================================
 :mod:`ilbe`
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
#  * [2024/08/23]
#     - 댓글 수집 로직 수정
#  * [2024/08/20]
#     - 댓글내용에 닉네임이 포함되어 수정 진행
#  * [2024/08/05]
#     - 본문만 스크린샷 찍도록 수정(스크린샷 방식 변경)
#  * [2024/04/16]
#     - 게시글 수집 이후 뒤로가기 명령 시 다른 사이트로 이동하는 오류 수정
#     - 게시글을 Tap으로 띄워서 수집하고 탭 종료 방식으로 수정
#  * [2024/04/12]
#     - 키워드 내부에 있는 고정값 제거 로직 추가
#  * [2024/03/18]
#     - 에러 코드 세분화(chrome 에러:11, 나머지 :1)
#  * [2024/01/03]
#     - 키워드 검색 방식 변경 (URL -> 검색창 검색)
#  * [2024/01/03]
#     - 제목 부분 xpath 수정(닉네임 들어가지 않도록)
#  * [2023/10/31]
#     - ssl 인증서 오류 해결 로직 추가
#  * [2023/04/28]
#     - 댓글 추천수/비추천수 xpath 수정
#  * [2023/03/24]
#     - 댓글을 새로운 탭 띄워서 수집
#  * [2022/03/22]
#     - 포맷적용
#  * [2022/01/14]
#     - 성인 게시판은 로그인이 필요함. login() 추가. 조회수는 주석 처리함.
#  * [2022/01/12]
#     - 조회수 구하는 로직추가. 작성자 닉네임 클릭후 작성한 게시글 내에서 찾아야함.
#  * [2022/01/03]
#     - article_url 추가. 각 게시글 별로 url추출
#  * [2021/12/30]
#     - starting

################################################################################
import re
import os
import sys
import yaml
import json
import ssl
import time
import shutil
import pickle
import random
import tarfile
import datetime
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from PIL import Image
from io import BytesIO

from selenium.webdriver.common.keys import Keys


################################################################################
class ILBESearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'ILBESearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

        self.parent_comment_id = ""
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
        self.logger.info(f'Starting ILBE Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            # 사용자 입력
            e = self.get_by_xpath('//input[@name="user_id"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//input[@name="password"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//div/button[@type="submit"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=2)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def search(self):
        try:
            # 검색 어 입력 검색창에 디폴트되어 있는 입력어가 있음 url로 접근
            # self.driver.get(self.config['params']['kwargs']['url'] + "/search?q=" + self.config['params']['site']['search'])
            # self.implicitly_wait(after_wait=1)

            # 검색 창에 키워드 검색하는 방식
            # 검색어 입력
            e = self.get_by_xpath('//span[@class="search-window"]/input')
            self.driver.execute_script("window.keyword = '{}'".format(''))
            if 'search_complex' in self.config['params']['site']:
                self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
            else:
                self.send_keys(e, self.config['params']['site']['search'])

            # 검색 단추
            e = self.get_by_xpath('//button[@class="btn-search"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
        except Exception as err:
            self.logger.error(f'search: error: {str(err)}')
            raise

    # ==========================================================================
    def get_comments(self, msg):
        try:
            # 댓글 list 없는 경우도 있슴
            comments_e = self.get_by_xpath('//html//body')

            comments = comments_e.find_elements_by_xpath('.//div/div[@class="comment-item-box"]')

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
                # 댓글에 대댓글이 모두 한 테이블 안에 잇는 구조 경로로 찾아야함.
                # 댓글 id
                parent_e = cmt_e.find_element_by_xpath('./..')
                cmt['comment_id'] = parent_e.get_attribute('id')
                # 대댓글인지 확인
                is_reply = parent_e.get_attribute('data-depth') != '0'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    self.parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = self.parent_comment_id

                # 댓글 작성자 닉네임
                e = cmt_e.find_element_by_xpath('.//span[@class="global-nick nick"]')
                self.move_to_element(e)
                cmt['nickname'] = e.text.strip()
                # 닉네임이 없는 경우 삭제된 글
                if cmt['nickname'] == "":
                    continue
                cmt_e = comments_e.find_element_by_xpath(f'.//div[@id="{cmt["comment_id"]}"]')
                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath('.//span[@class="date-line"]')
                cmt['create_ts'] = e.text.strip()
                # 댓글 추천수 (댓글이 삭제된 경우 찾지 못함.)
                e = cmt_e.find_element_by_xpath('.//div[@class="cmt-btn-wrap"]/em[1]')
                cmt['like'] = int(e.text.strip())
                # 댓글 비추천수
                e = cmt_e.find_element_by_xpath('.//div[@class="cmt-btn-wrap"]/em[2]')
                cmt['dislike'] = int(e.text.strip())
                # 댓글 내용 text
                e = cmt_e.find_element_by_xpath('.//span[@class="cmt"]')
                cmt['contents'] = e.text.strip()
                # 댓글 이미지
                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                e = cmt_e.find_element_by_xpath('.//div[@class="comment "]|.//div[@class="comment comment-origin"]')
                inner_html = e.get_attribute('innerHTML')
                if inner_html.find("comment-image img-landscape") > 0:
                    re_img = e.find_element_by_xpath('.//img[@class="comment-image img-landscape"]')
                    cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            raise

    # ==========================================================================
    def full_screenshot_article(self, output_file):
        # 하단 광고 제거
        under_ads = self.driver.find_elements_by_xpath("//div[@class='cutin-banner']")
        for under_ad in under_ads:
            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", under_ad)
        xpath = '//div[@class="board-view"]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)

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

    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot_article(msg_capture_f)

            content_e = self.get_by_xpath('//div[@class="board-view"]')
            # 게시글 제목
            e = content_e.find_element_by_xpath('.//div[@class="post-header"]/h3')
            msg['title'] = e.text.strip()
            # 작성자 이름
            e = content_e.find_element_by_xpath('//div[@class="post-header"]/span')
            msg['author'] = e.text.strip()
            # # 조회수(검색 결과 목록과 본문에 조회수가 존재하지 않음. 작성자이름을 클릭해 들어가서 작성자가 작성한 글목록에서 찾아야함.)
            # try:
            #     self.safe_click(e)
            #     self.implicitly_wait(after_wait=1)
            #     # 작성자이름이 익명인 경우 에러남
            #     e = self.get_by_xpath('//div[@class="user-pop-menu"]', timeout=1)
            #     self.safe_click(e)
            #     veiw_find = True
            #     # 작성자가 작성한 게시글이 많은경우 페이지를 넘겨야함.
            #     click_count = 1
            #     while veiw_find:
            #         v_es = self.driver.find_elements_by_xpath('//a[@class="subject "]')
            #         if len(v_es) == 0:
            #             msg['view_count'] = 0
            #             self.driver.back()
            #             break
            #         for v_e in v_es:
            #             v_id = re.sub(r'[^0-9]', '', v_e.get_attribute('href').partition('?')[0])
            #             if v_id == msg['article_id']:
            #                 e = v_e.find_element_by_xpath('./../../span[@class="view"]')
            #                 msg['view_count'] = int(e.text.strip().replace(',', ''))
            #                 veiw_find = False
            #                 for _ in range(click_count):
            #                     self.driver.back()
            #                     self.implicitly_wait(after_wait=1)
            #                 break
            #             elif v_e.find_element_by_xpath('./../../span[@class="count"]').text.strip() == "1":
            #                 for _ in range(click_count):
            #                     self.driver.back()
            #                     self.implicitly_wait(after_wait=1)
            #                 raise
            #         if veiw_find:
            #             ple = self.get_by_xpath('//div[@class="paginate"]', timeout=1)
            #             self.move_to_element(ple)
            #             is_on = False
            #             for pa in ple.find_elements_by_xpath('./a'):
            #                 if pa.get_attribute('class') == 'page-on':
            #                     is_on = True
            #                     continue
            #                 if is_on:
            #                     self.safe_click(pa)
            #                     self.implicitly_wait(after_wait=1)
            #                     click_count += 1
            #                     break
            # except:
            #     msg['view_count'] = 0
            # # 페이지를 나갔다와서 다시 찾아야함.
            # content_e = self.get_by_xpath('//div[@class="board-view"]')

            # 작성일시 년-월-일 시:분
            e = content_e.find_element_by_xpath('//div[@class="post-count"]/div[@class="count"]')
            msg['create_ts'] = e.find_element_by_xpath('./span[@class="date"]').text.replace('-', '.')
            # 댓글수
            msg['num_comments'] = int(e.find_element_by_xpath('./span[@class="comment-num"]').text)
            # 추천수
            e = content_e.find_element_by_xpath('.//button[@class="btn-vote good"]')
            self.move_to_element(e)
            msg['like'] = int(re.sub(r'[^0-9]', '', e.text))
            e = content_e.find_element_by_xpath('.//button[@class="btn-vote notgood"]')
            dislike = re.sub(r'[^0-9]', '', e.text)
            if dislike == '':
                msg['dislike'] = 0
            else:
                msg['dislike'] = int(dislike)

            # 본문
            e = content_e.find_element_by_xpath('//div[@class="post-content"]')
            inner_html = e.get_attribute('innerHTML')
            # 본문 text (글이 없으면 알아서 ''로 나옴.)
            msg['contents'] = e.text.strip()
            # 본문 이미지는 tagname으로 찾아야함.
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                img_e = e.find_elements_by_tag_name('img')
                for j, img in enumerate(img_e):
                    self.move_to_element(img)
                    sub_e_url = img.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 댓글이 없는 경우
            msg['comment_list'] = []
            if msg['num_comments'] <= 0:
                return
            # 댓글을 맨처음 가도록
            # e = content_e.find_element_by_xpath('//div[@class="board-view"]//div[@class="paginate"]/a[2]',
            #                                     cond='element_to_be_clickable')
            # self.safe_click(e)

            # 댓글 첫페이지로 선택
            e_a = content_e.find_element_by_xpath('(//div[@class="paginate"]/a)[1]')
            self.safe_click(e_a)
            self.implicitly_wait(after_wait=1)

            end_cmt_page = False
            for page_cnt in range(1, 100):
                # 댓글 페이지가 있는 경우 수집
                e = content_e.find_element_by_xpath('//div[@class="paginate"]')
                for k, cp_e in enumerate(e.find_elements_by_xpath('./a')):
                    if cp_e.text.strip() == str(page_cnt):
                        link_url = 'https://www.ilbe.com/commentlist/' + msg['article_id'] + '?page=' + cp_e.text.strip()
                        self.driver.execute_script(f"window.open('{link_url}')")
                        self.implicitly_wait(after_wait=1)
                        self.switch_to_window(2)
                        self.implicitly_wait(after_wait=1)
                        self.get_comments(msg)
                        break
                    elif cp_e.text.strip() == "다음":
                        end_cmt_page = True
                        break
                if end_cmt_page:
                    break

                # 윈도우 창 체크 로직(댓글)
                for _ in self.driver.window_handles:
                    if len(self.driver.window_handles) == 2:
                        break
                    self.switch_to_window(2)
                    self.driver.close()
                    self.implicitly_wait(after_wait=0.5)
                # self.switch_to_main_window()
                self.switch_to_window(1)
                self.implicitly_wait(after_wait=1)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # 윈도우창 갯수 체크로직
            for _ in self.driver.window_handles:
                if len(self.driver.window_handles) == 1:
                    break
                self.switch_to_window(1)
                self.driver.close()
                self.implicitly_wait(after_wait=0.5)
            self.switch_to_main_window()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_window(0)

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
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            ae_list = self.driver.find_elements_by_xpath('//div[@class="search-list"]/ul/li')
            for i in range(len(ae_list)):
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
                    # xpath가 사라짐 다시 구해주어야함
                    ae_list = self.driver.find_elements_by_xpath('//div[@class="search-list"]/ul/li')
                    ae = ae_list[i]
                    # 1) 게시글id : article_id
                    #  ilbe의 경우 고유 id개념이 없지만 링크에 게시글의 고유 넘버가 있음
                    e = ae.find_element_by_xpath('./a')
                    e_url = e.get_attribute('href')
                    msg['article_id'] = e_url.partition('view/')[2].strip()
                    # 2) 게시글 URL:  article_url
                    msg['article_url'] = e_url
                    # 3) 게시글판 이름:  board_name
                    e = ae.find_element_by_xpath('.//a[@class="title"]/span')
                    msg['board_name'] = e.text.strip()
                    # self.safe_click(e)
                    self.driver.execute_script(f"window.open('{e_url}')")
                    self.implicitly_wait(after_wait=1)

                    if os.path.isdir("\\".join([self.config['target']['folder'], msg['article_id']])):
                        self.is_done = True
                        break
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

    # ==========================================================================
    def next_page(self):
        ple = None
        try:
            # 목록으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="paginate2"]', timeout=2)
            self.move_to_element(ple)
            is_on = False
            for pa in ple.find_elements_by_xpath('./a'):
                if pa.get_attribute('class') == 'page-on':
                    is_on = True
                    continue
                if is_on:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            if ple is None:
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
            else:
                self.logger.error(f'next_page: error: {str(err)}')
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
                        # ssl 인증서 오류 해결
                        ssl._create_default_https_context = ssl._create_unverified_context
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
    def a_cookie(self):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            if self.search_index == 0:
                self.login()
            else:
                self.a_cookie()
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
        with open(kwargs['config_f'], encoding='utf-8') as ifp:
            f_yaml = yaml.load(ifp, yaml.SafeLoader)
            for i, keyword in enumerate(f_yaml['params']['site']['search'].split(',')):
                with ILBESearch(kwargs['config_f'], keyword, i) as ws:
                    ws.start()
    except Exception as err:
        print(err)
        return 11

################################################################################
if __name__ == '__main__':
    _config_f = 'ilbe.yaml'
    do_start(config_f=_config_f)
