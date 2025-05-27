"""
====================================
 :mod:`cafe/naver_total_mobile
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
#  * [2024/03/25]
#     - 수집 제외 키워드 추가(파트너스, 초성어등)
#  * [2024/02/28]
#     - 수집 제외 키워드 추가(-매물)
#  * [2024/02/02]
#     - 게시글 목록 xpath 변경
#     - view 삭제로 인한 search 부분 수정
#  * [2023/12/06]
#     - 기본적으로는 백그라운드에서 실행(백그라운드 스크린샷 에러 발생할 경우, 별도의 headless옵션 false인 창을 띄워 스크린샷 진행)
#     - headless_option 필드 추가
#     - 게시글 목록에서 시간 비교 추가적으로 진행 로직 제거
#     - 게시글 내부에 들어가자마자 1.작성시간 확인 --> 2.폐쇄카페 확인
#  * [2023/12/04]
#     - 수집 시작 페이지 변경
#     (https://m.search.naver.com/search.naver?nso=so%3Add%2Cp%3Aall&nso_open=1&prdtype=0&sm=mtb_opt&st=date&stnm=rel&where=m_articleg&opt_tab=0&query=)
#  * [2023/11/22]
#     - 게시글 목록에서 시간 비교 추가적으로 진행(몇시간전, 몇일전만 처리 나머지 날짜는 들어가서 비교하도록)
#  * [2023/11/17]
#     - 검색 창에 팝업 제거
#  * [2023/11/08]
#     - 게시글 목록에서 폐쇄 제외, 필터에서 일반 게시글만 선택
#  * [2023/10/20]
#     - 게시글 목록 전체 UI 변경
#  * [2023/09/25]
#     - 비공개 게시글 처리 로직 수정
#       out_title이 in_title안에 포함되지 않으면 비공개 게시글로 처리
#  * [2023/09/11]
#     - 게시글 목록에서 카페 도메인 비교해서 제외 - 배달세상
#  * [2023/09/07]
#     - VIEW 카테고리 검색하는 UI 변경으로 XPath 수정
#  * [2023/07/01]
#     - 본문 내용 xpath 추가
#  * [2023/06/07]
#     - 조회수, 비공개 게시글 회피 로직 수정
#  * [2023/06/05]
#     - 스크린샷 에러 발생할 경우, 필드(screenshot_error)에 True로 표시
#  * [2023/05/24]
#     - 이미지url이 null인 경우 넘어가도록 수정
#  * [2023/04/11]
#     - 검색 전 스크린 샷 추가
#  * [2023/02/10]
#     - 해쉬태그 수집
#  * [2022/12/05]
#     - 삭제된 게시글 회피 로직 수정
#     - 삭제된 게시글의 경우 로그 메세지 추가(게시글의 url과 title)
#     - 해쉬 태그 수집하는 로직 추가
#  * [2022/10/20]
#     - 윈도우 창 개수 확인하는 로직 추가
#  * [2022/10/17]
#     - 삭제된 게시글 회피 로직 수정
#  * [2022/09/28]
#     - 삭제된 게시글 회피 로직 추가
#  * [2022/02/14]
#     - starting
################################################################################
import math
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
from Screenshot import Screenshot_Clipping
import urllib.request
# from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys, webdriver
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
        e = self.get_by_xpath('//input[@class="search_input"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        e = self.get_by_xpath('(//div[@class="search_input_inner"]//input[@type="search"])[1]')
        self.move_to_element(e)
        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'] + ' -매물 -파트너스 -초성어등')
        # 검색 단추
        e = self.get_by_xpath('(//div[@class="search_btn_box"]//button[@type="submit"])[1]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # # 팝업 지우기
        # self.driver.execute_script("document.getElementById('MM_ALERT_LAYER').style.display = 'none';")

        # 검색어 입력
        # e = self.get_by_xpath('//input[@class="sch_input MM_SWIPE_IGNORE"]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # e = self.get_by_xpath('(//div[@class="sch_inner"]//input[@type="search"])[1]')
        # self.move_to_element(e)
        # if 'search_complex' in self.config['params']['site']:
        #     self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        # else:
        #     self.send_keys(e, self.config['params']['site']['search'])

        # # 검색 단추
        # # e = self.get_by_xpath('//button[@id="search_btn"]',
        # #                       cond='element_to_be_clickable')
        # e = self.get_by_xpath('(//div[@class="sch_inner"]//button[@type="submit"])[1]')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)
        # # view 선택
        # e = self.get_by_xpath('//div[@id="_sch_tab"]')
        # for i in e.find_elements_by_xpath('.//div/div[@class="flick_bx"]/a'):
        #     if i.text.strip() == 'VIEW':
        #         self.safe_click(i)
        #         self.implicitly_wait(after_wait=1)
        #         break
        #     else:
        #         continue
        #
        # # 카페
        # e = self.get_by_xpath('//*[@id="snb"]/div[1]/div/div[1]/a[3]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)
        # 옵션 필터
        e = self.get_by_xpath('//div[@class="option_filter"]/a',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 일반글
        e = self.get_by_xpath('//li[@class="bx target"]//div[@role="tablist"]')
        for i in e.find_elements_by_xpath('./a'):
            if i.text.strip() == '일반글':
                self.safe_click(i)
                self.implicitly_wait(after_wait=1)
                break
            else:
                continue
        # 최신순
        e = self.get_by_xpath('//div[@id="snb"]/div[@role="listbox"]')
        l = e.find_element_by_xpath('.//ul/li[@class="bx lineup"]//div[@role="tablist"]/a[2]')
        self.safe_click(l)
        self.implicitly_wait(after_wait=1)
        # 옵션 닫기
        e = self.get_by_xpath('//div[@class="option_filter"]/a[@aria-expanded="true"]',
                              cond='element_to_be_clickable')
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
                # 댓글 id (id를 찾을수 없어 순서로 입력)
                cmt['comment_id'] = str(i)

                # 대댓글
                is_reply = cmt_e.get_attribute('class') == 'reply'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ''
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                # 댓글 nickname : 삭제된 댓글인 경우 발견 불가
                try:
                    e = cmt_e.find_element_by_xpath('.//span[@class="nick_name"]/span')
                    cmt['nickname'] = e.text.strip()
                except:
                    continue

                # 댓글 작성 시각
                e = cmt_e.find_element_by_xpath('.//span[@class="date"]')
                create_ts = e.text.strip().rpartition('.')
                cmt['create_ts'] = create_ts[0] + create_ts[2] + ':00'

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('.//div[@class="comment_content"]/p')
                self.move_to_element(e)
                cmt['contents'] = e.text.strip()

                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                # 댓글 스티커 or 이미지
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find('TownCommentstickerContents upload_sticker') > 0:
                    s = cmt_e.find_element_by_xpath('.//div[@class="TownCommentstickerContents upload_sticker"]//source')
                    cmt['comment_img_url'].append(s.get_attribute('srcset'))
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                elif inner_html.find('TownCommentImageContents upload_img') > 0:
                    s = cmt_e.find_element_by_xpath('.//div[@class="TownCommentImageContents upload_img"]//source')
                    cmt['comment_img_url'].append(s.get_attribute('srcset'))
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
            self.cmt_done = True
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
            self.save_data = True
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            self.switch_to_window(1)
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            # 수집 범위 여부 확인 ( 1.작성시간 확인 -> 2.폐쇄카페 제외)
            # 작성 시간
            e_ab = self.get_by_xpath('//div[@class="ArticleContentWrap MediaViewerWrapper"]')
            e = e_ab.find_element_by_xpath(
                './/div[@class="post_title"]/div[@class="user_wrap"]//span[@class="date font_l"]')
            create_t = e.text.strip().partition('\n')[2].rpartition('.')
            msg['create_ts'] = create_t[0] + create_t[2] + ':00'
            if self.stop_article_older_than(msg):
                if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                    shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                self.is_done = True  # 동시성 런타임
                return
            # 도메인 값 비교로 폐쇄 카페 스킵
            remove_cafe_list = ['nds07', 'galaxysc', 'jihosoccer123', 'dieselmania', 'barman', 'cosmania',
                                'remonterrace', 'skybluezw4rh']
            if self.compare_domain in remove_cafe_list:
                self.logger.debug('폐쇄카페 게시글입니다.--------------(SKIP)')
                self.logger.debug(f'게시글의 url: {msg["article_url"]}')
                self.save_data = False
                return
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # self.full_screenshot(msg_capture_f)
                if self.config['params']['kwargs']['headless']:
                    try:
                        self._screenshot(msg_capture_f)
                        msg['screenshot_error'] = False
                        msg['headless_option'] = True
                    except:
                        try:
                            # 새로운 드라이버 옵션 설정
                            options_new = webdriver.ChromeOptions()
                            options_new.headless = False
                            # driver_new = self.driver.start_session(options_new.to_capabilities())
                            driver_new = webdriver.Remote(command_executor=self.driver.command_executor,
                                                          desired_capabilities=options_new.to_capabilities())
                            driver_new.get(msg['article_url'])
                            self.implicitly_wait(after_wait=5)
                            # 스크린샷 실행
                            e_heads = driver_new.find_elements_by_xpath('//div[@class="gnb"]')
                            for e_head in e_heads:
                                driver_new.execute_script("""
                                                                                                                            var element = arguments[0];
                                                                                                                            element.parentNode.removeChild(element);
                                                                                                                            """,
                                                          e_head)
                            e_footers = driver_new.find_elements_by_xpath('//div[@class="footer_fix"]')
                            for e_footer in e_footers:
                                driver_new.execute_script("""
                                                                                                                             var element = arguments[0];
                                                                                                                             element.parentNode.removeChild(element);
                                                                                                                             """,
                                                          e_footer)
                            obj = Screenshot_Clipping.Screenshot()
                            obj.full_Screenshot(driver_new,
                                                save_path=os.path.dirname(msg_capture_f),
                                                image_name=os.path.basename(msg_capture_f))
                            # 새로운 드라이버 종료
                            driver_new.quit()
                            msg['screenshot_error'] = False
                            msg['headless_option'] = False
                        except:
                            msg['headless_option'] = False
                            msg['screenshot_error'] = True
                        self.switch_to_window(1)
                else:
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
                    try:
                        self.full_screenshot(msg_capture_f)
                        msg['screenshot_error'] = False
                    except:
                        msg['screenshot_error'] = True
            # 카페에 main iframe으로 이동
            # self.switch_to_iframe_by_name('cafe_main')

            e_ab = self.get_by_xpath('//div[@class="ArticleContentWrap MediaViewerWrapper"]')
            # 게시판 이름
            e = e_ab.find_element_by_xpath('.//div[@class="post_title"]/div[@class="tit_menu"]/a/span')
            msg['board_name'] = e.text.strip()
            # 작성 시간
            e = e_ab.find_element_by_xpath('.//div[@class="post_title"]/div[@class="user_wrap"]//span[@class="date font_l"]')
            create_t = e.text.strip().partition('\n')[2].rpartition('.')
            msg['create_ts'] = create_t[0] + create_t[2] + ':00'
            # 작성자
            e = e_ab.find_element_by_xpath('.//div[@class="post_title"]/div[@class="user_wrap"]//span[@class="end_user_nick"]')
            msg['author'] = e.text.strip()
            # 조회수: view_count
            e = e_ab.find_element_by_xpath('.//div[@class="post_title"]/div[@class="user_wrap"]//span[@class="no font_l"]')
            e_v = e.text.partition('조회')[2].strip().replace(',', '')
            if '만' in e_v:
                se_a = e_v.replace('만', '0000').replace('.', '')
            else:
                se_a = e_v.replace(',', '')
            # msg['view_count'] = self.get_num_from_str(e_v)
            msg['view_count'] = int(se_a)
            # 댓글 수: 누르면 바로 댓글 창으로 가짐
            e_c = e_ab.find_element_by_xpath('//div[@class="CafeCommentSort"]//em')
            msg['num_comments'] = int(e_c.text.strip())
            # 좋아요
            # try:
            #     e = e_ab.find_element_by_xpath('.//em[@class="u_cnt _count"]')
            #     msg['like'] = int(e.text.strip().replace('+', ''))
            # except:
            #     msg['like'] = 0
            # 해쉬태그
            msg['tag_list'] = []
            for tag in self.driver.find_elements_by_xpath('//div[@class="tag_area bottom_space"]/a'):
                msg['tag_list'].append(tag.text.strip())

            # 게시글 내용 :
            contents_xpath = './/div[@class="se-main-container"]' \
                             '|.//div[@class="ContentRenderer"]'  \
                             '|.//div[@class="article_content_se"]'
            e = e_ab.find_element_by_xpath(contents_xpath)
            contents = e.text.strip()
            msg['contents'] = contents

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
                    if not sub_e_url:
                        pass
                    else:
                        msg['image_url_list'].append(sub_e_url)

            # 첨부파일 # 찾은 다음 하기
            inner_html = e_ab.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            if inner_html.find('tblForFl') > 0:
                for k, sub_k in enumerate(e_ab.find_elements_by_xpath('.//div[@class="se-component se-file se-l-default __se-component"]')):
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('href')
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
                e = self.get_by_xpath('//div[@class="CafeCommentSort"]//a[@class="link"]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
                # 댓글 더 보기가 있는 경우
                while msg['num_comments'] != 0:
                    fold_flag = False

                    # 두 번째 : 펼쳐야 하는 경우가 없는 경우는 빠져 나가기
                    for more in self.driver.find_elements_by_xpath('//div[@class="comment_more"]//a[@class="more_next"]'):
                        self.safe_click(more)
                        self.implicitly_wait(after_wait=1)
                        fold_flag = True

                    # 세 번째 : 펼쳐야 하는 경우
                    for more in self.driver.find_elements_by_xpath('//div[@class="comment_more"]//a[@class="more_next"]'):
                        self.safe_click(more)
                        self.implicitly_wait(after_wait=1)
                        break

                    # while 문 빠져나가기
                    if fold_flag == False:
                        break
                self.get_comment(msg)
            except:
                pass

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
            self.switch_to_window(0)

            count_a = 0
            while True:
                # 페이지 테이블 구하기
                e_s = self.driver.find_elements_by_xpath('//div[@class="api_subject_bx"]/ul/li')
                e_a = e_s[count_a]
                # 게시글 목록 캡쳐
                if count_a % 15 == 0:
                    self.implicitly_wait(after_wait=1)
                    self.driver.set_window_size(self.config['params']['kwargs']['width'], 3500)
                    s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{int(count_a / 15)}.png'
                    s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
                    self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
                    # self._screenshot(self.get_safe_path(s_shot))
                msg = {
                    'page': self.cur_page,
                    'row': count_a + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': None,
                    # 'site_board': self.config['params']['site']['site_board'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'article_id': None,
                    'create_ts': None,
                    'board_name': None,
                    'title': None,
                    'contents': None,
                    'tag_list': [],
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
                    'screenshot_error': None,
                    'headless_option': None,
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
                    # 1) 게시글 주소: article_url
                    e_url = e_a.find_element_by_xpath('.//div[@class="title_area"]/a')
                    a_url = e_url.get_attribute('href')
                    msg['article_url'] = a_url
                    # 2) 게시글 id : article_id  300143_55268553
                    v = a_url.partition('?')[0]
                    v_a = v.partition('.com/')[2].partition('/')[2]
                    # v_a = re.sub(r'[^0-9]', '', v)
                    msg['article_id'] = v_a
                    # 도메인 값 비교로 폐쇄 카페 스킵
                    v_domain = v.partition('.com/')[2].partition('/')[0]
                    self.compare_domain = v_domain
                    # 카페 이름: site_name
                    e = e_a.find_element_by_xpath('.//div[@class="user_box_inner"]/div/a')
                    msg['site_name'] = e.text.strip()
                    # 2) 제목: title
                    e = e_a.find_element_by_xpath('.//div[@class="title_area"]/a')
                    msg['title'] = e.text.strip()
                    a = e.text.strip()
                    out_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", a)
                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    try:
                        self.switch_to_main_window()
                        # 커넥션 에러로 인해 새로 고침 추가
                        self.switch_to_window(1)
                        self.driver.refresh()
                        self.implicitly_wait(after_wait=1)
                        # 비공개글 회피로직
                        self.switch_to_window(1)
                        self.implicitly_wait(after_wait=2)
                        # 게시글 제목 비교 띄어쓰기가 단락으로 인해 차이가 있을 수 있음
                        e = self.driver.find_element_by_xpath('//div[@class="title_area"]//h2').text.strip()
                        sub_e = ''
                        for sub in self.driver.find_elements_by_xpath('//div[@class="title_area"]//h2[@class="tit"]/span'):
                            sub_e = sub.text.strip()
                        e = re.sub(sub_e, "", e)
                        in_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", e)
                        # if not in_title.replace(' ', '').startswith(out_title.replace(' ', '')[:-3]):
                        if not out_title.replace(' ','') in in_title.replace(' ',''):
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
                            count_a += 1
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
                        count_a += 1
                        continue
                    self.get_article(msg, count_a + 1)
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

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
                if self.save_data == True:
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
                # bi = self.get_by_xpath('//div[@id="app"]//div/strong[@class="tit_guide"]')
                # # 비공개 게시글
                # if bi:
                #     self.logger.debug('멤버에게만 공개된 게시글 입니다.')
                #     continue
                self.move_to_element(e_a)
                count_a += 1

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
    def mobile_mode(self):
        options = webdriver.ChromeOptions()
        if self.config['params']['kwargs']['headless']:
            options.add_argument('--headless')
        options.add_argument("disable-gpu")
        options.add_argument('--incognito')
        options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1')
        # options.add_argument(f'--user-agent={generate_user_agent(device_type="smartphone")}')
        # options.add_argument('--kiosk-printing')

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['params']['kwargs']['url'])
        time.sleep(5)

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
