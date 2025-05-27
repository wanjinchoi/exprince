"""
====================================
 :mod:`ruliweb`
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
#  * [2024/11/01]
#     - 조회수, 좋아요 수 xpath 변경으로 인한 수정
#  * [2024/08/20]
#     - 대댓글 판단 UI 변경
#     - 댓글 내용에 닉네임 포함되지 않도록 수정
#  * [2024/08/08]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. 이미지 자르는 방식
#  * [2024/08/05]
#     - 앱설치 팝업 제거 로직 추가
#  * [2024/05/14]
#     - 사이트 UI 변경으로 인한 모듈 수정(게시글 작성일, 조회수, 좋아요, 댓글수)
#  * [2024/03/20]
#     - 에러 코드 세분화/에러 로그 세분화
#     - 스크린샷 광고 부분 제거 추가
#     - 검색 결과 존재 여부 확인 로직 추가
#  * [2024/01/11]
#     - 본문 내용에서 좋아요/싫어요(분리수거) 제외
#  * [2023/11/21]
#     - 게시글 목록 풀스크린샷 추가
#  * [2023/10/23]
#     - '유머 게시판' 게시판만 URL 변경으로 article_id 값에 특수문자 '?' 가 들어가면서 게시글 폴더명 오류 발생
#     - '유머 게시판' article_id 생성 로직 변경
#  * [2023/06/16]
#     - 댓글 이미지 가져오는 로직 수정
#  * [2023/04/27]
#     - 루리웹 댓글 추천수 XPath 변경/비추천수 사라짐
#  * [2023/04/14]
#     - 루리웹 댓글 추천수 XPath 변경
#  * [2022/10/14]
#     - 루리웹 댓글 비추천수 존재하지 않는 게시글 존재하여 해당 부분 수정
#  * [2022/06/14]
#     - headless 추가
#  * [2022/06/13]
#     - main() 추가 (Pyhton Run Script에서 실행하기위함)
#  * [2022/04/28]
#     - user_agent 값을 매번 바꿔 주도록 변경
#  * [2022/04/18]
#     - 셀레니움 브라우저를 모바일로 오픈 해서 클롤링 시작. 첫시작때 10초정도 딜레이.
#     처음에 url로 오픈한뒤에 검색창 찾을때 간헐적으로 종료됨. 원인불명..
#  * [2022/02/11] MinJung
#     - from alabslib.selenium import PySelenium 로 변경
#     - def start 부분 finally 밑에 print 부분 추가. 첫 수집한 게시글의 작성 시간을 'latest_create_article_ts'에 추가되는 로직.
#     - def __init__ 부분의 for output 변경.
#     - def get_page에서 msg {} 의 내용 추가.
#     - def save_image 추가 및 def save_article 변경.
#     - emoticon_url 을 comment_img_url로 변경.
#     - 첫 수집한 게시글의 작성 시간을 'latest_create_article_ts'에 추가되는 로직 수정.
#     - do_start 부분 return 0 추가.
#     -  ruliweb.yaml 내용 수정.
#  * [2021/12/27]
#     - 이미지중에 막힌 이미지가 존재함. 움직이는 사진 등.
#  * [2021/12/20]
#     - starting

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
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys, webdriver
# from user_agent import generate_user_agent, generate_navigator
from user_agent import generate_user_agent
from PIL import Image
from io import BytesIO


################################################################################
class RULIWEBSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'RULIWEBSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        self.config['params']['kwargs']['url'] = 'https://www.ruliweb.com/search'
        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

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
        self.logger.info(f'Starting RULIWEB Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:
            # 검색 어 입력
            e = self.get_by_xpath('//input[@id="search_bar"]', timeout=3, wait_until_valid_text=True)
            self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
            # for i, st in enumerate(self.config['params']['site']['search']):
            #     if len(self.config['params']['site']['search']) == i + 1:
            #         self.send_keys(e, st + Keys.ENTER)
            #     else:
            #         self.send_keys(e, st)
            #         self.implicitly_wait(after_wait=1)
            self.implicitly_wait(after_wait=3)
        except Exception as err:
            self.logger.error(f'search: error: {str(err)}')
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def full_screenshot1(self, output_file):
        self.remove_html()
        xpath = '//div[@class="content_wrapper"]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)
        xpath = '//div[@class="flex line_deco_both text_center"]'
        element2 = self.driver.find_element_by_xpath(xpath)
        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size
        location2 = element2.location
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
        bottom = location2['y']

        cropped_image = merged_image.crop((left, top, right, bottom))

        # 최종 이미지 저장
        cropped_image.save(output_file)

    # ========================================================================
    def remove_html(self):
        try:
            # 로그인
            power_link = self.get_by_xpath("//div[@class='nbp_container line_deco_bottom']")
            # 게시글 목록 리스트
            # article_list = self.get_by_xpath('//div[@class="ad_banner is_mobile"]')
            # 하단 광고
            # btm_area = self.get_by_xpath('//div[@class="UIArticleBottomArea"]')
            # footer
            # ft = self.get_by_xpath('//div[@class="footer_inner"]')

            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", power_link)
            # self.driver.execute_script("arguments[0].remove();", article_list)
            # self.driver.execute_script("arguments[0].remove();", btm_area)
            # self.driver.execute_script("arguments[0].remove();", ft)

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass

    # ==========================================================================
    def get_comments(self, msg):
        parent_comment_id = None
        try:
            # 댓글 list 없는 경우도 있슴
            try:
                comments_e = self.get_by_xpath('//table[@class="comment_table"]', timeout=3)
            except:
                return
            comments = comments_e.find_elements_by_xpath('./tbody/tr')

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
                # 해당 댓글로 이동 루리웹에는 이미지가 있을 때 클릭해줘야하는데 클릭 후에 xpath가 변경됨
                try:
                    self.move_to_element(cmt_e)
                except:
                    comments_e = self.get_by_xpath('//table[@class="comment_table"]')
                    comments = comments_e.find_elements_by_xpath('./tbody/tr')
                    cmt_e = comments[i]
                    self.move_to_element(cmt_e)
                if cmt_e.get_attribute('class').endswith('close') or cmt_e.text == '삭제된 댓글입니다.':
                    cmt['contents'] = cmt_e.text.strip()
                    # 댓글 목록에 추가 삭제된 댓글
                    msg['comment_list'].append(cmt)
                    continue
                # 댓글 id
                cmt['comment_id'] = cmt_e.get_attribute('id')
                # 대댓글인지 확인
                is_reply = 'child' in cmt_e.get_attribute('class')
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                # 댓글 작성자 닉네임
                e = cmt_e.find_element_by_xpath('.//div[@class="nick"]|.//strong[@class="nick"]')
                # e = cmt_e.find_element_by_xpath('.//strong[@class="nick"]')
                cmt['nickname'] = e.text.strip()
                # # 댓글 작성자 번호
                # e = cmt_e.find_element_by_xpath('.//span[@class="member_srl"]')
                # cmt['nickname_number'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
                # # 댓글 작성자 ip
                # e = cmt_e.find_element_by_xpath('.//p[@class="ip"]')
                # cmt['nickname_ip'] = e.text.strip()
                # 댓글 작성 시간 '21.12.21 11:24'
                e = cmt_e.find_element_by_xpath('.//span[@class="time"]')
                c_datetime = e.text.replace('|', '').strip()
                cmt['create_ts'] = datetime.datetime.strptime(c_datetime, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                # 댓글 추천수
                # e = cmt_e.find_element_by_xpath('.//button[@class="btn_like"]')
                e = cmt_e.find_element_by_xpath('.//button[@class="btn_like hitting-button"]/span|.//button[@class="btn_like"]/span')
                cmt['like'] = int(e.text.strip())
                # # 댓글 비추천수
                # try:
                #     e = cmt_e.find_element_by_xpath('.//button[@class="btn_dislike r_col col_4"]/span|.//button[@class="btn_dislike"]/span')
                #     cmt['dislike'] = int(e.text.strip())
                # except:
                #     cmt['dislike'] = 0
                # 댓글 내용 text
                # e = cmt_e.find_element_by_xpath('.//span[@class="text"]')
                e = cmt_e.find_element_by_xpath('.//div[@class="text_wrapper"]/p[@class="text"]')
                cmt['contents'] = e.text.strip()
                # 댓글 이미지
                inner_html = e.get_attribute('innerHTML')
                # if inner_html.find('comment_img_text') > 0:
                #     re_img = e.find_element_by_xpath('.//div[@class="comment_img_text"]')
                #     self.safe_click(re_img)
                #     # 이미지 보이게 클릭한후에는 다시 경로를 찾아야함.(클릭하고 잠시 시간을 줘야함.. loading)
                #     self.implicitly_wait(after_wait=1)
                #     e = self.get_by_xpath(f'//tr[@id="{cmt["comment_id"]}"]')
                #     inner_html = e.get_attribute('innerHTML')
                #     # 움직이는 이미지
                #     if inner_html.find('video') > 0:
                #         re_img = e.find_element_by_tag_name('video')
                #     else:
                #         re_img = e.find_element_by_xpath('.//img[@class="comment_img"]')
                #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                #     cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')
                #
                # elif inner_html.find('comment_img') > 0 or inner_html.find('comment_video') > 0:
                #     if inner_html.find('comment_video') > 0:
                #         re_img = e.find_element_by_xpath('.//td[@class="comment"]//div')
                #     else:
                #         re_img = e.find_element_by_xpath('.//img[@class="comment_img"]')
                #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                #     cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')
                if inner_html.find('comment_img') > 0:
                    # 기본 이미지(img)와 움직이는 이미지(vidio)는 태그 이름이 달라서 동일한 class로 찾음.
                    re_img = e.find_element_by_xpath('.//*[@class="comment_img"]')
                    cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')

                # elif inner_html.find('comment_video') > 0:
                #     if inner_html.find('comment_video') > 0:
                #         re_img = e.find_element_by_xpath('.//td[@class="comment"]//div')
                #     else:
                #         re_img = e.find_element_by_xpath('.//img[@class="comment_img"]')
                #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                #     cmt['comment_img'].append(f'{cmt["comment_id"]}_0.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{i + 1}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            raise

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]"')

            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)

            # content_e = self.get_by_xpath('//div[@class="board_main"]')
            content_e = self.get_by_xpath('//div[@class="board_main line_deco_bottom"]')
            # 글유형
            e = content_e.find_element_by_xpath('//span[@class="category_text"]')
            msg['title'] = ' '.join([e.text.strip(), msg['title']])
            # 작성자
            e = content_e.find_element_by_xpath('//strong[@class="nick"]|'
                                                '//a[@class="nick"]')
            msg['author'] = e.text.strip()
            # # 작성자 이미지
            # try:
            #     e = content_e.find_element_by_xpath('//img[@class="profile_image"]')
            #     msg['author_img'] = e.get_attribute('src')
            # except:
            #     e = content_e.find_element_by_xpath('//img[@class="profile_image_default"]')
            #     msg['author_img'] = e.get_attribute('src')

            # # 작성자 번호
            # e = content_e.find_element_by_xpath('.//span[@class="member_srl"]')
            # msg['author_number'] = int(re.sub(r'[^0-9]', '', e.text.strip()))

            # # 회원IP
            # e = content_e.find_element_by_xpath('//div[@class="user_info"]/p[7]/span')
            # msg['author_ip'] = e.text.partition(':')[2].strip()

            # 작성일시 년.월.일 시:분:초
            e = content_e.find_element_by_xpath('//span[@class="regdate"]')
            msg['create_ts'] = \
                datetime.datetime.strptime(e.get_attribute('innerHTML'), '%y.%m.%d (%H:%M:%S)').strftime('%Y.%m.%d %H:%M:%S')
            # 추천수 기존 class="like에서 like_value로 변했기 때문에 다시 바뀌어도 성공하도록 수정함
            try:
                e = content_e.find_element_by_xpath('//span[@class="like_value"]')
                msg['like'] = int(e.get_attribute('innerHTML').replace(',', ''))
                #조회수
                e = content_e.find_element_by_xpath('//div[@class="info_wrapper"]//div[2]//div[2]//span[4]')
                msg['view_count'] = int(e.text)

            except:
                e = content_e.find_element_by_xpath('//span[@class="like"]')
                msg['like'] = int(e.get_attribute('innerHTML').replace(',', ''))
                # 조회수는 경로로 찾아야함.
                e = content_e.find_element_by_xpath('//span[@class="like"]/..')
                msg['view_count'] = int(
                    e.get_attribute('innerHTML').partition("조회 ")[2].partition('\t')[0].replace(',', ''))
            # 댓글수
            e = content_e.find_element_by_xpath('//span[@class="num_txt"]/strong[@class="reply_count"]')
            msg['num_comments'] = int(e.get_attribute('innerHTML').replace(',', ''))
            # 본문
            e = content_e.find_element_by_xpath('//div[@class="board_main_view"]//div[1]')
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
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                elements = self.driver.find_elements_by_xpath("//div[@class='app_install']")
                # 각 요소의 스타일을 "display: none;"로 설정합니다.
                for element in elements:
                    self.driver.execute_script("arguments[0].style.display = 'none'", element)
                    self.logger.info('앱 설치 광고창 삭제 완료')
                # 캡처할때 광고가 따라와서 꺼주는게 보기 좋음 광고가 올라오는 시간이 좀 있음.
                # e = self.get_by_xpath('//a[@id="wif_adx_banner_close"]')
                # self.safe_click(e)
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e = self.driver.find_element_by_xpath('//div[@id="fixed_ad"]')
                    self.driver.execute_script("""
                                            var element = arguments[0];
                                            element.parentNode.removeChild(element);
                                            """, e)
                    p_bar = self.driver.find_element_by_xpath('//div[@id="push_bar"]')
                    self.driver.execute_script("""
                                                                var element = arguments[0];
                                                                element.parentNode.removeChild(element);
                                                                """, p_bar)
                    self.full_screenshot1(msg_capture_f)
            # 댓글
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            c_e = self.get_by_xpath('//div[@class="paging_wrapper row bottom noselect"]', timeout=1)
            cmt_pages = c_e.find_elements_by_xpath('./a')
            is_next = False
            for k, cmt_page in enumerate(cmt_pages):
                c_e = self.get_by_xpath('//div[@class="paging_wrapper row bottom noselect"]', timeout=1)
                cmt_pages = c_e.find_elements_by_xpath('./a')
                cmt_page = cmt_pages[k]
                if cmt_page.get_attribute('class') == 'btn_end':
                    break
                elif cmt_page.get_attribute('class') == 'btn_num active':
                    self.get_comments(msg)
                    is_next = True
                elif is_next:
                    self.safe_click(cmt_page)
                    self.implicitly_wait(after_wait=1)
                    self.get_comments(msg)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            self.driver.close()
            self.implicitly_wait(after_wait=2)
            # 처음 페이지로 스위치 해줘야함.
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
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            self.driver.execute_script("document.getElementById('fixed_ad').style.display = 'none';")

            # 게시글 목록 스크린샷
            self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            self.full_screenshot(self.get_safe_path(s_shot))
            # self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))

            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            # e = self.driver.find_element_by_xpath('//div[@class="fixed_ad_wrapper line_h_50"]')
            # self.driver.execute_script("""
            #                         var element = arguments[0];
            #                         element.parentNode.removeChild(element);
            #                         """, e)
            # ae_list = self.driver.find_elements_by_xpath(
            #     './/div[@class="result box"][2]//div//ul//li[@class="search_result_item"]')
            try:
                e = self.get_by_xpath('//div[@id="board_search"]//ul[@class="search_result_list"]',
                                      timeout=10, wait_until_valid_text=True)
            except:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return
            ae_list = e.find_elements_by_xpath('./li')
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
                    # ae_list = self.driver.find_elements_by_xpath(
                    #     './/div[@class="result box"][2]//div//ul//li[@class="search_result_item"]')
                    self.switch_to_main_window()
                    e = self.get_by_xpath('//div[@id="board_search"]//ul[@class="search_result_list"]',
                                          timeout=10, wait_until_valid_text=True)
                    ae_list = e.find_elements_by_xpath('./li')
                    ae = ae_list[i]

                    # 3) 게시판이름 : board_name(통일성) - '유머 게시판' URL이 달라서 게시판 먼저 가져옴.
                    e = ae.find_element_by_xpath('.//a[@class="name"]')
                    msg['board_name'] = e.text.strip()
                    # 1) 게시글id : article_id
                    #  ruliweb의 경우 고유 id개념이 없지만 링크에 개시판의 고유번호와 게시글의 고유번호가 있음. 게시판_넘버
                    e_t = ae.find_element_by_xpath('.//a[@class="title text_over"]')
                    a_url = e_t.get_attribute('href')
                    id = a_url.partition("/board/")[2].partition("/read/")
                    if msg['board_name'] == '[유머 게시판]':
                        ad = id[2].partition("?")
                        msg['article_id'] = id[0] + '_' + ad[0]
                    else:
                        msg['article_id'] = id[0] + '_' + id[2]

                    msg['article_url'] = a_url

                    # 2) 게시글이름 : title
                    msg['title'] = e_t.text.strip()

                    # self.safe_click(e_t)
                    # self.driver.get(a_url)
                    self.driver.execute_script(f"window.open('{a_url}')")

                    self.implicitly_wait(after_wait=3)
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
            self.switch_to_main_window()
            # 페이지 목록
            ple = self.get_by_xpath('//div[@id="board_search"]//ul[@class="search_result_list"]/../div[@class="row"]',
                                    timeout=5, wait_until_valid_text=True)
            self.move_to_element(ple)
            is_active = False
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('class') == 'btn_num active':
                    is_active = True
                    continue
                if is_active:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            if ple is None:
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
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
    def save_image(self, msg):
        for j, sub_e_url in enumerate(msg['image_url_list']):
            try:
                article_img_p = self.get_safe_path(
                    self.config['target']['folder'],
                    msg['article_id'],
                    f'{j}.png'
                )
                # 가끔 에러 나는 경우가 있슴
                for count in range(10):
                    try:
                        urllib.request.urlretrieve(sub_e_url, article_img_p)
                        msg['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count+1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

        # 댓글 이미지
        for cmt in msg['comment_list']:
            if not('comment_img' in cmt and cmt['comment_img']):
                continue
            for k, cmt_url in enumerate(cmt['comment_img_url']):
                try:
                    cmt_img_f = self.get_safe_path(
                        self.config['target']['folder'],
                        msg['article_id'],
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
            f'{article["article_id"]}'
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
    def mobile_mode(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("disable-gpu")
            options.add_argument('--incognito')
            # options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1')
            options.add_argument(f'--user-agent={generate_user_agent(device_type="smartphone")}')
            options.add_argument('--kiosk-printing')
            if self.config['params']['kwargs']['headless']:
                options.add_argument('headless')

            self.driver.start_session(options.to_capabilities())
            self.driver.get(self.config['params']['kwargs']['url'])
            time.sleep(5)
        except Exception as err:
            self.logger.error(f'mobile_mode: error: {str(err)}')
            raise

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            self.mobile_mode()
            self.search()
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.next_page()
            print(0)
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            print(1)
            return 1
        finally:
            # print(self.output['latest_create_article_ts'])
            # print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with RULIWEBSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
def main(**kwargs):
    try:
        with RULIWEBSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(11)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'ruliweb.yaml'
    do_start(config_f=_config_f)
