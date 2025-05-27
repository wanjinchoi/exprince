"""
====================================
 :mod:`news/naver_mobile
====================================
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# * Sebin Eun
#
# Change Log
# --------
#  * [2024/11/1]
#     - 일반 뉴스 상단 카테고리 제거
#  * [2024/10/30]
#     - 네이버(모바일) 메인 화면에 팝업 생김. 메인 화면은 팝업이 계속 변경되어 검색 단계에서 시작하도록 변경.
#  * [2024/08/26]
#     - 일반 뉴스와 스포츠, 엔터테인먼트 뉴스 전체 스크린샷 방식 분리
#     - 광고 제거 로직 스포츠, 엔터테인먼트 뉴스에만 적용
#  * [2024/08/12]
#     - 스크린샷에 제목, 언론사명 노출되지 않는 이슈. 언론사명으로 이동 후 스크린샷 찍음
#  * [2024/07/31]
#     - 스크린샷에 광고 제거 로직 추가
#  * [2024/06/19]
#     - 스포츠 뉴스 UI 변경으로 수집 경로(XPath) 수정 - EXTVOCGE-1677
#  * [2024/05/29]
#     - 연애 뉴스 UI 변경으로 수집 경로 수정
#  * [2024/05/13]
#     - 일반 뉴스의 댓글 수집 전 등록 시간 확인(EXTVOCGE-1620)
#  * [2024/03/15]
#     - 스포츠 뉴스의 사이트명 수집 경로 수정
#  * [2024/02/27]
#     - 스포츠 뉴스의 접속 URL, Xpath 수정
#  * [2024/01/22]
#     - 게시글 목록 '더보기' 버튼 제거
#  * [2023/11/30]
#     - 감정수가 없는 케이스 존재하여 모듈 수정
#  * [2023/11/24]
#     - 네이버 메인 페이지 신규 팝업 제거
#  * [2023/10/24]
#     - 게시글 목록 '더보기' 버튼 XPath 수정
#  * [2023/08/16]
#     - entertain XPath 수정
#     - 게시글 목록 더보기 추가
#  * [2023/07/27]
#     - starting

################################################################################
import os
import sys
import yaml
import json
import time
import shutil
import random
import re
import tarfile
import datetime
import traceback
import requests
import urllib.request
from urllib.request import urlretrieve
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, webdriver


################################################################################
class NaverNewsSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverNewsSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

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
        self.logger.info(f'Starting Naver News Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 팝업 지우기
        # self.driver.execute_script("document.getElementById('MM_ALERT_LAYER').style.display = 'none';")

        # 검색어 입력
        # e = self.get_by_xpath('//input[@class="sch_input MM_SWIPE_IGNORE"]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # e = self.get_by_xpath('(//div[@class="sch_inner"]//input[@type="search"])[1]')
        # self.move_to_element(e)
        e = self.get_by_xpath('//input[@class="search_input"]')
        self.move_to_element(e)
        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@class="btn_search"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 옵션 필터
        e = self.get_by_xpath('//div[@class="option_filter"]/a',
                              cond='element_to_be_clickable')
        self.safe_click(e)

        e = self.get_by_xpath('//div[@id="snb"]/div[@role="listbox"]')
        # 최신순
        l = e.find_element_by_xpath('.//ul/li[@class="bx lineup"]//div[@role="tablist"]/a[2]')
        self.safe_click(l)

    # ==========================================================================
    # 스포츠 뉴스, 엔터테인먼트 뉴스 전체 스크린샷
    def _screenshot_other(self, f):
        try:
            # 언론사명으로 이동(안하면 언론사명, 제목이 스크린샷에 안보임)
            e = self.driver.find_element_by_xpath('//div[@class="news_end_main"]/div[1]')
            self.move_to_element(e)
        except:
            self.logger.info('언론사명 UI 변경')
            # 언론사명 페이지 이동

        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="news_end_main"]').screenshot(f)

    # ==========================================================================
    # 일반 뉴스 전체 스크린샷
    def _screenshot(self, f):
        try:
            # 언론사명으로 이동(안하면 언론사명, 제목이 스크린샷에 안보임)
            e = self.driver.find_element_by_xpath('//div[@class="media_end_head_top _LAZY_LOADING_WRAP"]')
            self.move_to_element(e)

            # 상단 카테고리 제거
            top_e = self.get_by_xpath('//div[@class="Nlnb_menu Ntype_scroll "]')
            self.driver.execute_script("arguments[0].remove();", top_e)
        except:
            self.logger.info('언론사명 UI 변경')

        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="newsct_wrapper _GRID_TEMPLATE_COLUMN _STICKY_CONTENT"]').screenshot(f)

    # ==========================================================================
    def get_comments(self, news):
        global comment_count, i
        try:
            self.logger.debug(f'Starting Comment processing')
            comment_count = {}
            # 현재 댓글 개수
            e = self.get_by_xpath('(//ul[@class="u_cbox_comment_count u_cbox_comment_count3"]/li/span)[1]')
            comment_count = int(e.text.strip().replace(',', ''))

            if comment_count < 0:
                return

            news['comment_list'] = []

            # 댓글 수집
            offset = 0
            rr_count = 0
            c_es = self.driver.find_elements_by_xpath(
                '//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li')

            for i in range(offset, len(c_es)):
                c_e = self.get_by_xpath(
                    f'(//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li)[{i + 1}]',
                    cond="visibility_of_element_located",
                    move_to_element=True)
                # self.move_to_element(c_e)
                inner_html = c_e.get_attribute('innerHTML')
                comment = {
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
                try:
                    # 댓글 id : comment_id
                    try:
                        e = c_e.find_element_by_xpath('.//button[@class="u_cbox_btn_totalcomment"]')
                        c_id = e.get_attribute('data-param').split(',')
                        c_id_2 = re.sub('[^(0-9)]', '', c_id[2])
                        comment['comment_id'] = c_id_2
                    except:
                        self.logger.debug('Delete or Clean bot or Non-compliance comment')
                        raise
                    # 대댓글 false 설정
                    comment['is_reply'] = False
                    # 부모 댓글의 id
                    # comment['parent_comment_id'] = ''
                    # 댓글 작성자 프로필 이미지
                    # if inner_html.find('u_cbox_img_profile') >= 0:
                    #     e = c_e.find_element_by_xpath('.//img[@class="u_cbox_img_profile"]')
                    #     comment['profile_img_url'] = e.get_attribute('src')
                    # 작성자 닉네임 (esac****) 뒤에 네자리 **** 처리됨
                    if inner_html.find('u_cbox_nick') < 0:
                        continue
                    e = c_e.find_element_by_xpath('.//span[@class="u_cbox_nick"]')
                    comment['nickname'] = e.text.strip()
                    # 작성 시간 : 2022.01.02 00:00:00
                    if inner_html.find('u_cbox_date') >= 0:
                        e = c_e.find_element_by_xpath('.//span[@class="u_cbox_date"]')
                        r_time = e.get_attribute('data-value')
                        re_time = r_time.replace('-', '.').replace('T', ' ').replace('+0900', '')
                        comment['create_ts'] = re_time
                    # 클린봇이 탐지한 내용인 경우
                    if inner_html.find('u_cbox_cleanbot_contents') > 0:
                        self.logger.debug('Clean bot comment')
                        raise
                    # 삭제된 댓글인지 체크
                    else:
                        e = c_e.find_element_by_xpath('.//span[@class="u_cbox_delete_contents"]')
                        if e.get_attribute('style'):  # 삭제되지 않은 글
                            # 댓글 내용
                            if inner_html.find('u_cbox_contents') >= 0:
                                e = c_e.find_element_by_xpath('.//span[@class="u_cbox_contents"]')
                                comment['contents'] = e.text.strip()
                            # 추천 개수
                            e = c_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_recomm"]')
                            comment['like'] = int(e.text.strip())
                            # 비추천 개수
                            e = c_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_unrecomm"]')
                            comment['dislike'] = int(e.text.strip())
                        else:  # 삭제된 글이나 규정 미준수
                            self.logger.debug('Non-compliance comment')
                            raise
                    # news의 comment_list에 댓글 추가
                    news['comment_list'].append(comment)

                    # 대댓글
                    # reply_list = []
                    try:
                        e = c_e.find_element_by_xpath('.//a[@class="u_cbox_btn_reply"]')
                        rr_str = e.text.strip()
                        if rr_str == '답글0' or rr_str == '답글\n0':
                            self.logger.debug('No reply comments')
                            raise
                        # 대댓글 개수 : 찾아지면 대댓글이 있는 경우임
                        # "댓글 2" 눌러 대댓글 보이게 함
                        # 동적 컨텐츠라 다시 읽음
                        c_e = self.driver.find_element_by_xpath(
                            f'(//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li)[{i + 1}]')
                        e = c_e.find_element_by_xpath('.//a[@class="u_cbox_btn_reply"]')
                        self.safe_click(e)
                        # 동적으로 늘어남
                        self.implicitly_wait(after_wait=1)
                        rr_count += 1
                        rr_e = self.driver.find_element_by_xpath(f'(.//div[@class="u_cbox_reply_area"])[{i + 1}]')
                        # 더보기 여부
                        try:
                            e = rr_e.find_element_by_xpath('.//span[@class="u_cbox_page_more"]')
                            e_txt = e.text
                            if e_txt == "더보기":
                                self.safe_click(e)
                                self.implicitly_wait(e)
                        except:
                            pass
                        # 대댓글 수집
                        for j, rc_e in enumerate(rr_e.find_elements_by_xpath('.//ul[@class="u_cbox_list"]/li')):
                            self.move_to_element(rc_e)
                            reply = {
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
                            r_inner_html = rc_e.get_attribute('innerHTML')
                            # 대댓글 id : comment_id
                            try:
                                e = rc_e.find_element_by_xpath('.//button[@class="u_cbox_btn_totalcomment"]')
                                c_id = e.get_attribute('data-param').split(',')
                                c_id_2 = re.sub('[^(0-9)]', '', c_id[2])
                                reply['comment_id'] = c_id_2
                            except:
                                self.logger.debug('Delete or Clean bot or Non-compliance reply comment')
                                raise
                            # 대댓글 설정
                            reply['is_reply'] = True
                            # 부모 댓글의 id
                            reply['parent_comment_id'] = comment['comment_id']
                            # # 댓글 작성자 프로필 이미지
                            # if r_inner_html.find('u_cbox_img_profile') >= 0:
                            #     e = rc_e.find_element_by_xpath('.//img[@class="u_cbox_img_profile"]')
                            #     reply['profile_img_url'] = e.get_attribute('src')
                            # 작성자 닉네임 (esac****) 뒤에 네자리 **** 처리됨
                            if r_inner_html.find('u_cbox_nick') < 0:
                                continue
                            e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_nick"]')
                            reply['nickname'] = e.text.strip()
                            # 작성 시간 : 2021.12.02 00:00:00
                            if r_inner_html.find('u_cbox_date') >= 0:
                                e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_date"]')
                                r_time = e.get_attribute('data-value')
                                re_time = r_time.replace('-', '.').replace('T', ' ').replace('+0900', '')
                                reply['create_ts'] = re_time
                            # 클린봇이 탐지한 내용인 경우
                            if r_inner_html.find('u_cbox_cleanbot_contents') > 0:
                                self.logger.debug('Non-compliance comment')
                                raise
                            else:
                                # 삭제된 댓글인지 체크
                                e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_delete_contents"]')
                                if e.get_attribute('style'):  # 삭제되지 않은 글
                                    # 댓글 내용
                                    if r_inner_html.find('u_cbox_contents') >= 0:
                                        e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_contents"]')
                                        reply['contents'] = e.text.strip()
                                    # 추천 개수
                                    e = rc_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_recomm"]')
                                    reply['like'] = int(e.text.strip())
                                    # 비추천 개수
                                    e = rc_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_unrecomm"]')
                                    reply['dislike'] = int(e.text.strip())
                                else:  # 삭제된 글이나 규정 미준수
                                    self.logger.debug('Non-compliance reply comment')
                                    raise
                            # news의 comment_list에 대댓글 추가
                            news['comment_list'].append(reply)
                        self.logger.info(f'[{i}/{comment_count["total"]}] Comment="{comment["contents"][:80]}"')
                    except Exception as err:
                        pass
                except Exception as err:
                    pass
                finally:
                    pass
                offset = len(news['comment_list'])
        except Exception as err:
            raise
        finally:
            # 이전 페이지
            # self.driver.back()
            if len(news['comment_list']) != comment_count['total']:
                i = i
                pass

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
    def remove_email(self, text):
        # 이메일 패턴을 정의합니다.
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        # 이메일을 포함한 괄호 패턴을 정의합니다.
        email_with_brackets_pattern = r'\([^)]*\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b[^)]*\)'

        # 이메일과 괄호 패턴을 제거합니다.
        text = re.sub(email_with_brackets_pattern, '', text)
        text = re.sub(email_pattern, '', text)

        # 여분의 공백을 제거합니다.
        text = re.sub(r'\s+', ' ', text).strip()

        return text
    # ==========================================================================

    def get_emotions(self, e_emotions, news):
        try:
            for e_emotion in e_emotions:
                emotion = e_emotion.get_attribute('data-type')
                emotion_count = e_emotion.find_element_by_xpath('./span[2]').get_attribute('innerHTML')
                # 좋아요
                if emotion == 'like':
                    news['good'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 훈훈해요
                elif emotion == 'warm':
                    news['warm'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 슬퍼요
                elif emotion == 'sad':
                    news['sad'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 화나요
                elif emotion == 'angry':
                    news['angry'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 팬이에요
                elif emotion == 'fan':
                    news['fan'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 응원해요
                elif emotion == 'cheer':
                    news['cheer'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 축하해요
                elif emotion == 'congrats':
                    news['congrats'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 기대해요
                elif emotion == 'expect':
                    news['expect'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 놀랐어요
                elif emotion == 'surprise':
                    news['surprise'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 쏠쏠정보
                elif emotion == 'useful':
                    news['useful'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 흥미진진
                elif emotion == 'wow':
                    news['wow'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 공감백배
                elif emotion == 'touched':
                    news['touched'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 분석탁월
                elif emotion == 'analytical':
                    news['analytical'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 후속기사 원해요, 후속 강추
                elif emotion in ['want', 'recommend']:
                    news['news'] = int(re.sub(r'([^0-9])', '', emotion_count))
        except Exception as err:
            self.logger.error(err)

    # ==========================================================================
    def remove_html(self):
        # 중간에 게시글 UI 변경 가능성이 있어 각각 try문으로 실행
        try:
            # 상단 광고
            try:
                top_area = self.get_by_xpath('//header')
                self.driver.execute_script("arguments[0].remove();", top_area)
            except Exception as e:
                self.logger.error(f'하단 광고 제거 실패: {e}')

            # 하단 광고
            try:
                btm_area = self.get_by_xpath('//div[@class="feed_group"]')
                self.driver.execute_script("arguments[0].remove();", btm_area)
            except Exception as e:
                self.logger.error(f'하단 광고 제거 실패: {e}')

            # footer
            # try:
            #     ft = self.get_by_xpath('//footer[@id="footer"]')
            #     self.driver.execute_script("arguments[0].remove();", ft)
            # except Exception as e:
            #     self.logger.error(f'푸터 제거 실패: {e}')

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경: {err}')
            pass

    # ==========================================================================
    def get_news(self, naver_news_e, news):
        # new tab
        self.switch_to_window(1)
        try:
            self.logger.info(f'Page[{news["page"]}:{news["row"]}] title="{news["title"]}"')
            # news 마다 delay.news.min ~ delay.news.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['news']['min'],
                self.config['params']['site']['delay']['news']['max'],
            )
            time.sleep(delay_a)
            # 현재 페이지 url
            now_url = self.driver.current_url
            if self.config['params']['site']['capture_article']:
                # 불필요한 이미지 제거
                # self.remove_html()
                # save capture
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], news['article_id'],
                                                   f'{news["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    if "entertain" in now_url or "sports" in now_url:
                        # 불필요한 이미지 제거.
                        self.remove_html()
                        self._screenshot_other(msg_capture_f)
                    else:
                        # 일반 뉴스 전체 스크린샷
                        # 일반 뉴스는 본문 xpath 다름. 하단 광고 없음
                        self._screenshot(msg_capture_f)

                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="Nlnb"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_head)
                    self.full_screenshot(msg_capture_f)
            # 게시글 수집
            # # 현재 페이지 url
            # now_url = self.driver.current_url
            # 상위 element 선언 : 뉴스, 스포츠, 엔터 순서
            if "entertain" in now_url:
                enter_e = self.get_by_xpath('//div[@class="news_end_main"]')
                # 원본 언론사 링크
                # e = enter_e.find_element_by_xpath('.//div[@class="press_logo"]/a')
                # news['press_url'] = e.get_attribute('href')
                # 원본 언론사 이름 및 아이콘 url
                e = enter_e.find_element_by_xpath('./div[1]//img')
                # news['press_name'] = e.get_attribute('alt')
                news['site_name'] = e.get_attribute('alt')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는경우도 있음
                try:
                    e = enter_e.find_element_by_xpath('.//span[@class="NewsEndMain_author__sl+2K"]')
                    author_e = self.remove_email(e.text)
                    news['author'] = author_e
                except:
                    ...
                # 감정수
                e_emotions = enter_e.find_elements_by_xpath('.//ul[@class="NewsEndMain_comp_likeit_reaction_list__xhIbM"]//em')
                # 좋아요
                news['good'] = int(e_emotions[0].text.strip())
                # 응원해요
                news['cheer'] = int(e_emotions[1].text.strip())
                # 축하해요
                news['congrats'] = int(e_emotions[2].text.strip())
                # 기대해요
                news['expect'] = int(e_emotions[3].text.strip())
                # 놀랐어요
                news['surprise'] = int(e_emotions[4].text.strip())
                # 슬퍼요
                news['sad'] = int(e_emotions[5].text.strip())
                # 연애 뉴스는 감정 표현 Xpath가 다름
                # self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    try:
                        e = enter_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                        like = e.text.strip().replace(',', '')
                        news['like'] = 0 if like == '' else int(like)
                    except:
                        pass

                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = enter_e.find_element_by_xpath('.//div[@class="NewsEndMain_info_item__t+40a"]/em')
                create_ts = e.text.strip().replace('오전', 'am').replace('오후', 'pm')
                news['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d. %p %I:%M').strftime(
                    '%Y.%m.%d %H:%M:%S')

                # 기사 원본 URL
                # e = self.get_by_xpath('(//div[@class="sponsor"]/a)[1]')
                # news['press_org_url'] = e.get_attribute('href')
                # 기사 본문
                e = enter_e.find_element_by_xpath('.//div[@class="_article_content"]')
                contents = e.text.strip()
                contents = contents.replace('\n\n', '\n')
                news['contents'] = contents
                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    news['image_url_list'].append(sub_e_url)

            elif "sports" in now_url:
                # 본문
                sports_e = self.get_by_xpath('//div[@class="news_end_main"]')
                # 원본 언론사 이름 및 아이콘 url
                e_name = self.get_by_xpath('//div[@class="news_end_main"]/div[1]')
                e = e_name.find_element_by_xpath('.//img')
                # news['press_name'] = e.get_attribute('alt')
                news['site_name'] = e.get_attribute('alt')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는 경우도 있음
                try:
                    e = sports_e.find_element_by_xpath('.//span[@class="NewsEndMain_author__sl+2K"]')
                    author_e = self.remove_email(e.text)
                    news['author'] = author_e
                except:
                    ...
                # 감정수
                e_emotions = sports_e.find_elements_by_xpath('.//ul[@class="NewsEndMain_comp_likeit_reaction_list__xhIbM"]//em')
                # 좋아요
                news['good'] = int(e_emotions[0].text.strip())
                # 슬퍼요
                news['sad'] = int(e_emotions[1].text.strip())
                # 화나요
                news['angry'] = int(e_emotions[2].text.strip())
                # 팬이에요
                news['fan'] = int(e_emotions[3].text.strip())
                # 후속기사 원해요
                news['news'] = int(e_emotions[4].text.strip())
                # self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    try:
                        e = sports_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                        like = e.text.strip().replace(',', '')
                        news['like'] = 0 if like == '' else int(like)
                    except:
                        pass

                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = sports_e.find_element_by_xpath('//div[@class="NewsEndMain_info_item__t+40a"]/em')
                c_ts = e.text.replace('기사입력', '')
                c_ts = c_ts.split()
                c_ts_0 = c_ts[0].rstrip('.')
                t_ts = c_ts[2].split(':')
                hour = int(t_ts[0])
                if t_ts[0] == '12':
                    hour -= 12
                if c_ts[1] == '오후':
                    hour += 12
                create_ts = f'{c_ts_0} {hour:02}:{t_ts[1]}:00'
                news['create_ts'] = create_ts
                # 기사 원본 URL
                # e = self.get_by_xpath('(//div[@class="sponsor"]/a)[1]')
                # news['press_org_url'] = e.get_attribute('href')
                # 기사 본문
                e = sports_e.find_element_by_xpath('.//div[@class="_article_content"]')
                contents = e.text.strip()
                contents = contents.replace('\n\n', '\n')
                news['contents'] = contents
                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    news['image_url_list'].append(sub_e_url)

            else:
                # 뉴스
                news_e = self.driver.find_element_by_xpath('//div[@id="main_content"]|//div[@class="newsct_wrapper _GRID_TEMPLATE_COLUMN"]|//div[@class="newsct_wrapper _GRID_TEMPLATE_COLUMN _STICKY_CONTENT"]')
                # 원본 언론사 링크
                # e = news_e.find_element_by_xpath('.//div[@class="press_logo"]/a')
                # news['press_url'] = e.get_attribute('href')
                # 원본 언론사 이름 및 아이콘 url
                e = news_e.find_element_by_xpath('.//img')
                # news['press_name'] = e.get_attribute('title')
                news['site_name'] = e.get_attribute('title')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는 경우도 있음
                try:
                    e = news_e.find_element_by_xpath('.//div[@class="journalistcard_summary_name"]|'
                                                     './/div[@class="byline"]/p')
                    news['author'] = e.text.strip()
                except:
                    ...

                # 감정수
                e_emotions = news_e.find_elements_by_xpath('(.//ul[@class="u_likeit_layer _faceLayer"])[1]/li/a')
                self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    try:
                        e = news_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                        like = e.text.strip().replace(',', '')
                        news['like'] = 0 if like == '' else int(like)
                    except:
                        pass
                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = news_e.find_element_by_xpath(
                    './/div[@class="sponsor"]/span[@class="t11"]|'
                    './/span[@class="media_end_head_info_datestamp_time _ARTICLE_DATE_TIME"]')
                create_ts = e.text.strip().replace('오전', 'am').replace('오후', 'pm')
                news['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d. %p %I:%M').strftime('%Y.%m.%d %H:%M:%S')

                # 일반 뉴스의 등록 시간 확인.
                if self.stop_article_older_than(news):
                    if os.path.isdir("/".join([self.config['target']['folder'], news['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], news['article_id']]))
                    self.logger.info(f'일반 뉴스 수집 전 게시글 등록 시간 확인 결과, 수집 범위 밖의 게시글로 확인 ArticleID=["{news["article_id"]}"]+')
                    self.is_done = True
                    return

                # 기사 본문
                e = news_e.find_element_by_xpath('.//div[@id="articleBodyContents"]|.//div[@id="newsct_article"]')
                contents = e.text.strip()
                # contents = contents.replace('\n\n', '\n')
                news['contents'] = contents

                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []

                try:
                    # 이미지가 없을 수도 있음.
                    for j, sub_e in enumerate(e.find_elements_by_xpath('.//p/img|.//div[@id]/img')):
                        self.move_to_element(sub_e)
                        sub_e_url = sub_e.get_attribute('src')
                        news['image_url_list'].append(sub_e_url)
                # 댓글 : 댓글이 없는 경우 있음
                    # 댓글 개수 확인
                    e = news_e.find_element_by_xpath(
                        './/span[@class="lo_txt"]|.//div[@class="media_end_head_info_variety_cmtcount _COMMENT_HIDE"]')
                    e_txt = e.text
                    try:
                        e_tt = int(re.sub('[^(0-9)]', '', e_txt))
                    except:
                        e_tt = 0
                    news['num_comments'] = e_tt
                    # 만약 댓글이 0개 이상이면
                    if e_tt > 0:
                        # 상단 댓글 (카운트) 누름
                        e = news_e.find_element_by_xpath('.//a[@id="articleTitleCommentCount"]|.//div[@class="media_end_head_info_variety_cmtcount _COMMENT_HIDE"]/a')
                        self.safe_click(e)
                        self.implicitly_wait(after_wait=2)
                        # 상위 element 설정
                        cont_e = self.get_by_xpath('//td[@class="content"]|//div[@id="cbox_module"]', timeout=1)
                        # 클린봇 클릭하기
                        try:
                            e = cont_e.find_element_by_xpath('.//a[@class="u_cbox_cleanbot_setbutton"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=2)
                            # 만약 클린봇이 비활성화 되어있다는 걸 찾으면
                            clean_e = self.get_by_xpath('//div[@class="u_cbox_layer_cleanbot2"]', timeout=1)
                            try:
                                e = clean_e.find_element_by_xpath('.//input[@class="u_cbox_layer_cleanbot2_checkbox"]')
                            # 찾지 못하면 클린봇 설정이 켜졌으니 끄기
                            except:
                                e = clean_e.find_element_by_xpath(
                                    './/input[@class="u_cbox_layer_cleanbot2_checkbox is_checked"]')
                                self.safe_click(e)
                                self.implicitly_wait(after_wait=2)
                            # 클린봇 확인 누르기
                            e = clean_e.find_element_by_xpath('.//button[@class="u_cbox_layer_cleanbot2_extrabtn"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=2)
                        # 한 번 클린봇을 끄면 다시 안 꺼줘도 된다
                        except:
                            pass
                        # 최신순 클릭
                        e = cont_e.find_element_by_xpath('.//a[@data-param="new"]|//a[@data-param="new"]')
                        self.safe_click(e)
                        self.move_to_element(e)
                        self.implicitly_wait(after_wait=2)
                        # 하단의 "더보기" 가 있는 경우
                        try:
                            e = cont_e.find_element_by_xpath('.//span[@class="u_cbox_more_wrap"]'
                                                             '|.//a[@class="u_cbox_btn_view_comment"]')
                            e_txt = e.text
                            while e_txt in "더보기":
                                self.move_to_element(e)
                                self.safe_click(e)
                                self.implicitly_wait(after_wait=2)
                        except:
                            pass

                        # 댓글 수집
                        self.get_comments(news)
                        if len(news['comment_list']) != news['num_comments']:
                            news['num_comments'] = len(news['comment_list'])
                except:
                    pass

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            self.close_tab()
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
            self.switch_to_window(0)

            count_a = 0
            while True:
                # if count_a % 15 == 0:
                #     e_more = self.get_by_xpath('//div[@class="mod_more_wrap"]')
                #     self.safe_click(e_more)
                #     self.implicitly_wait(after_wait=2)
                # 페이지 테이블 구하기
                e_s = self.driver.find_elements_by_xpath('//div[@class="group_news"]/ul/li')
                e_a = e_s[count_a]
                news = {
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
                    # ----------------------------------------------------------------------
                    'warm': None,
                    'cheer': None,
                    'congrats': None,
                    'expect': None,
                    'surprise': None,
                    'fan': None,
                    'useful': None,
                    'wow': None,
                    'touched': None,
                    'analytical': None,
                    # ----------------------------------------------------------------------
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    # 현재 뉴스가 보이도록 이동
                    self.move_to_element(e_a)

                    e = e_a.find_element_by_xpath('.//a[@class="news_tit"]')
                    title = e.find_element_by_xpath('./div')
                    news['title'] = title.text.strip()

                    # "뉴스1 25분 전 네이버뉴스" 와 같이 네이버뉴스 링크가 있는 것인지 체크
                    try:
                        e = e_a.find_element_by_xpath('.//div[@class="info_group"]')
                        e_str = e.text.strip()
                        if not e_str.endswith('네이버뉴스'):
                            raise Exception('No naver contents')

                        # https://news.naver.com/main/read.naver?mode=LSD&mid=sec&sid1=101&oid=023&aid=0003661894
                        # https://n.news.naver.com/mnews/article/018/0005244644?sid=102
                        e = e_a.find_element_by_xpath('.//div[@class="news_wrap"]/a[@class="news_tit"]')
                        article_url = e.get_attribute('href')
                        if '&aid=' in article_url:
                            aid = article_url.rpartition('oid=')[2].replace('&aid=', '_')
                        else:
                            aid = article_url.rpartition('/')[2].replace('?sid=', '_')
                        # aid = article_url[article_url.find('&sid=')+5:]
                        # aid = article_url.rpartition('/')[2].replace('?sid=', '_')
                        # 스포츠 뉴스 URL: https://n.news.naver.com/sports/article/356/0000065062
                        if "sports" in article_url:
                            news['article_url'] = article_url
                        else:
                            news['article_url'] = article_url.partition('/article')[0] + '/mnews' + article_url.partition('/article')[1] + article_url.partition('/article')[2]
                        news['article_id'] = aid
                    except:
                        self.logger.info(f'get_page[{self.cur_page}:{count_a + 1}]:{title} have no naver contents')
                        count_a += 1
                        continue
                    self.driver.execute_script(f"window.open('{news['article_url']}');")
                    self.implicitly_wait(after_wait=1)
                    self.get_news(e, news)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    news['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{news["error_backtrace"]}')
                    self.logger.error(f'뉴스 url: {news["article_url"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(news):
                    if os.path.isdir("/".join([self.config['target']['folder'], news['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], news['article_id']]))
                    self.is_done = True
                    break
                self.save_image(news)
                self.output['article_list'].append(news)
                if self.config['target']['is_separate_article']:
                    self.save_news(news)
                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = news['create_ts']
                if len(self.output['article_list']) >= \
                        self.config['params']['site']['max_articles'] > 0:
                    self.is_done = True
                    break
                self.move_to_element(e_a)
                count_a += 1

        except Exception as err:
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
    def save_news(self, news):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            news['article_id'],
            f'{news["article_id"]}'
        )
        self.save_d(at_js_f, news)

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
                # self.next_page()
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
    with NaverNewsSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'news_naver.yaml'
    do_start(config_f=_config_f)
