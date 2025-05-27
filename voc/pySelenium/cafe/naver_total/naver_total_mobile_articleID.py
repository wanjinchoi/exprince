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
#
# Change Log
# --------
#  * [2024/10/22]
#     - 본문에 해시태그가 존재할 경우 본문에서 삭제하고 hash_tag 필드에 분리하여 저장한다.
#  * [2024/10/14]
#     - '쿠팡잇츠' -매물파트너스 등 제외 키워드를 넣을 경우 수정이 발생하지 않아 수정이 발생할 경우와 안될 경우 에러가 나지 않도록 수정
#  * [2024/09/30]
#     - '쿠팡잇츠' 검색 포털에서 자동 수정될 경우 '쿠팡잇츠' 검색어로 변환
#  * [2024/09/12]
#     - 해시태그 원복
#  * [2024/09/03]
#     - 이미지 수집에 본문 xpath 추가
#     - 댓글 100개 이상인 경우에만 댓글 더보기 클릭하도록 변경. 댓글 더보기 버튼 xpath 찾는 시간 7초 단축
#  * [2024/08/29]
#     - 댓글 수집 원복(xpath -> html parsing)
#     - 정규표현식 사용해서 이미지 링크의 확장자 확인. 확장자가 다른 경우 NaverTotalImg.log에 남김
#  * [2024/08/23]
#     - 댓글 700개 이상 게시글 스킵. 제외 게시글은 별도 수집 로그에 리스트 추가(NaverTotalCommentOver.log)
#  * [2024/08/21]
#     - 게시글 목록에서 url, id 추출하는 로직 수정
#  * [2024/08/16]
#     - 게시글 본문, 댓글 이미지 수집 방식 변경(HTML parsing으로 Img 태그 찾기 -> xpath로 직접 찾기)
#     - 게시글 하단 광고 제거(XPath 수정)
#     - 댓글 수집 로그 추가
#  * [2024/08/08]
#     - 수집 멈춤 현상 원인 파악을 위한 수집 로그 추가
#     - UI 변경으로 제외 이미지 Xpath 수정
#  * [2024/07/24]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. HTML에서 제거
#  * [2024/07/15]
#     - '배달세상 배달이야기' 카페가 모바일 버전에서 '배달세상'으로 노출되어 실제 사이트명으로 변경 수집
#  * [2024/07/05]
#     - '배달나라' 카페 통합 검색 수집으로 전환
#  * [2024/06/21]
#     - 네이버 수집 제외 폐쇄 카페 추가 - 배달나라
#  * [2024/06/19]
#     - 댓글 본문 UI 변경으로 수집 경로 수정
#  * [2024/06/17]
#     - 게시글 이미지 다운로드 불가(403 forbidden) 시 이미지 링크를 본문 내용 필드에 추가하여 수집
#     - 게시글 ID 추출 방식 변경 (카페 domain)_(게시글 ID)
#  * [2024/06/12]
#     - 외부 컨텐츠(단일 동영상) 가져오는 embed 태그의 첨부 소스 수집(EXTVOCGE-1662)
#  * [2024/05/13]
#     - 클린봇 감지 댓글 스킵하는 로직 추가(EXTVOCGE-1612)
#     - 네이버 카페 댓글 내용 중 작성자 태그한 내용만 제외하여 수집하는 로직 추가(EXTVOCGE-1613)
#     - 댓글의 이미지 수집 로직 수정(EXTVOCGE-1617)
#     - 게시글 스크린 샷 오류 발생하면 등록 시간 None 처리(내부)
#     - 수집 멍때리는 현상 - 이미지 retry할 때 로그가 멈춰서 retry 횟수 10회에서 2회로 줄임
#  * [2024/04/29]
#     - 스크린 샷 에러 발생해도 수집한 데이터 저장하도록 변경
#     - 페이지 1초 고정으로 기다리는 시간 제거
#     - 사이트명 XPath로 페이지 로딩 확인. 로딩 안되면 10초 Time out 후 페이지 새로고침
#  * [2024/04/24]
#     - 네이버 카페 최상단 UI 변경으로 사이트명 Xpath 수정
#  * [2024/04/18]
#     - articleID를 사용한 중복 수집 제거 모듈
#     - 게시글 수집 HTML 소스로 Text 수집 방식으로 변경
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
import os
import sqlite3
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
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys, webdriver
from bs4 import BeautifulSoup
from collections import OrderedDict
from lxml import html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
        self.logger_c = get_logger(self.get_safe_path(log_d, 'NaverTotalCommentOver.log'),
                            logsize=1024 * 1024 * 10)
        self.logger_img = get_logger(self.get_safe_path(log_d, 'NaverTotalImg.log'),
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
        self.keyword = self.config['params']['site']['search']
        self.site_sequence = self.config['params']['site']['site_sequence']
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
        self.contents_tag = []
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
        # 검색어가 자동수정 됐는지 확인
        if self.config['params']['site']['search'] == '쿠팡잇츠':
            try:
                e = self.get_by_xpath('//div[@class="keyword"]/a')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
                self.logger.info('쿠팡잇츠 검색어 자동수정 원복')
            except:
                self.logger.info('쿠팡잇츠 검색어 네이버에서 자동 수정 되지 않음 ')


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
            # 댓글 페이지 HTML 소스 가져오기
            comment_source = self.driver.page_source
            self.logger.info('comment page source 수집')
            # 주어진 HTML 소스를 사용하여 BeautifulSoup 객체 생성
            soup = BeautifulSoup(comment_source, 'html.parser')
            self.logger.info('comment HTML parsing')
            # 모든 댓글을 선택합니다.
            c_e = soup.find('ul', class_='comment_list')
            comments = c_e.find_all('li')
            self.logger.info('Collect comment list')
            # 이미지 수집 방식 변경(태그 수집)을 위한 댓글 리스트 수집
            cmt_list = self.get_by_xpath('//ul[@class="comment_list"]')

            # 이미지 파일 확장자를 위한 정규표현식 패턴
            image_pattern = re.compile(r'\.(jpg|jpeg|gif|png)(\?.*)?$', re.IGNORECASE)

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
                self.logger.info('대댓글 여부 판단 완료')
                # 댓글의 작성 시간을 가져옵니다.
                try:
                    c_c = comment.find('span', class_='date')
                    create_ts = c_c.text.strip().rpartition('.')
                    cmt['create_ts'] = create_ts[0] + create_ts[2] + ':00'
                except:
                    continue
                self.logger.info('댓글 작성 시간 수집 완료')
                # 댓글 작성자의 닉네임을 가져옵니다.
                nickname = comment.find('span', class_='nick_name').text.strip()
                cmt['nickname'] = nickname
                self.logger.info('댓글 작성자 확인')
                # 댓글의 내용을 가져옵니다.
                contents = comment.find('div', class_='comment_content')
                for span in contents.find_all('span'):
                    span.extract()
                cmt['contents'] = contents.text.strip()
                self.logger.info('댓글 내용 확인')

                # 댓글에 포함된 이미지를 수집합니다.
                cmt['comment_img'] = []
                cmt['comment_img_url'] = []
                # img_c = comment.find('div', class_='comment_content')
                # comment_imgs = img_c.find_all('source')  # 댓글에 포함된 모든 이미지 태그를 가져옵니다.
                # self.logger.info('댓글 이미지 수집 시작')
                comment_imgs = contents.find_all('source')  # 댓글에 포함된 모든 이미지 태그를 가져옵니다.
                for j, img in enumerate(comment_imgs):
                    img_url = img['srcset']  # 이미지의 src 속성을 가져옵니다.
                    if image_pattern.search(img_url):
                        article_img_p = self.get_safe_path(
                            self.config['target']['folder'],
                            msg['article_id'],
                            f'{cmt["comment_id"] + "_" + str(j)}.png'
                        )
                        # img_url = img['srcset']  # 이미지의 src 속성을 가져옵니다.
                        self.logger.info('댓글 이미지 저장 시작')
                        urlretrieve(img_url, article_img_p)
                        self.logger.info('댓글 이미지 저장 성공')
                        cmt['comment_img_url'].append(img_url)  # 이미지
                        cmt['comment_img'].append(f'{cmt["comment_id"] + "_" + str(j)}.png')
                    else:
                        # 이미지 로그 별도 파일에 저장. 경로 동일 NaverTotalImg.log
                        self.logger_img.info(f'지원하지 않는 형식의 이미지: {img_url}')
                        # 실패한 이미지 URL을 본문 내용에 저장
                        cmt['contents'] += f'다운로드 실패 이미지 링크: {img_url}'

                # # # 댓글 이미지 수집을 위해 댓글 XPath 찾음
                # cmt_tag = cmt_list.find_elements_by_xpath('//div[@class="comment_item"]')[idx]
                # cmt_content = cmt_tag.find_element_by_xpath('.//div[@class="comment_content"]')
                # img_tags = cmt_content.find_elements_by_xpath('.//source')
                # if img_tags:
                #     for j, sub_e in enumerate(img_tags):
                #         try:
                #             self.move_to_element(sub_e)
                #             sub_e_url = sub_e.get_attribute('srcset')
                #             article_img_p = self.get_safe_path(
                #                 self.config['target']['folder'],
                #                 msg['article_id'],
                #                 f'{cmt["comment_id"] + "_" + str(j)}.png'
                #             )
                #             self.logger.info('댓글 이미지 저장 시작')
                #             urlretrieve(sub_e_url, article_img_p)
                #             self.logger.info('댓글 이미지 저장 성공')
                #             cmt['comment_img_url'].append(sub_e_url)
                #             cmt['comment_img'].append(f'{cmt["comment_id"] + "_" + str(j)}.png')
                #         except:
                #             # 실패한 이미지 URL 본문 내용에 저장
                #             cmt['contents'] += f'다운로드 실패 이미지 링크: {sub_e_url}'
                #             self.logger.info(f'save_img error: {j}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'[{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
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
    def get_article(self, msg, ndx, m_url):
        try:
            # 데이터 저장 여부 True
            self.save_data = True
            # delay_a = 1
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]')
            self.switch_to_window(1)
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            # delay_a = random.uniform(
            #     self.config['params']['site']['delay']['article']['min'],
            #     self.config['params']['site']['delay']['article']['max'],
            # )
            # Time out - 구조 기다리고 열리면 시작
            # time.sleep(delay_a)
            try:
                # 특정 요소가 로드될 때까지 기다림
                wait = WebDriverWait(self.driver, 10)
                element = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//a[@class="gnb_title_text typo_heading-xLarge"]')))
                self.logger.info('게시글 페이지 확인 완료')
            except:
                # 요소를 찾을 수 없는 경우, 페이지를 새로고침
                self.driver.refresh()

            # 게시글 URL로 HTML 소스 가져오기
            article_source = self.driver.page_source

            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(article_source, 'html.parser')
            self.logger.info('BeautifulSoup extraction complete')
            # 최상단 사이트명 가져오기
            high_e = soup.find('div', class_='gnb')
            site_name = high_e.find('a', class_='gnb_title_text typo_heading-xLarge')
            s_name = site_name.text.strip()
            if s_name == '배달세상':
                msg['site_name'] = '배달세상 배달이야기'
            else:
                msg['site_name'] = site_name.text.strip()

            # 상단 - 게시판명, 제목, 작성자, 등록시간, 조회수
            top_e = soup.find('div', class_='post_title')
            # 게시판명
            board_name = top_e.find('span', class_='ellip')
            msg['board_name'] = board_name.text.strip()
            # 제목
            title_name = top_e.find('h2', class_='tit')
            msg['title'] = title_name.text.strip()
            # 작성자
            nick = top_e.find('span', class_='end_user_nick')
            msg['author'] = nick.text.strip()
            # 등록시간
            c_e = top_e.find('span', class_='date font_l')
            create_ts = c_e.text.strip().partition('작성일')[2].rpartition('.')
            msg['create_ts'] = create_ts[0] + create_ts[2] + ':00'
            # 조회수
            view_count = top_e.find('span', class_='no font_l')
            e_v = view_count.text.partition('조회')[2].strip().replace(',', '')
            if '만' in e_v:
                se_a = e_v.replace('만', '0000').replace('.', '')
            else:
                se_a = e_v.replace(',', '')
            msg['view_count'] = int(se_a)
            self.logger.info('게시글 상단 수집 완료')
            # 정규표현식 패턴: /단어 형식이 10개 이상 포함된 경우
            pattern = r"(?:/[^<\s]+){10,}"
            # 중단 - 본문
            try:
                middle_e = soup.find('div', class_='se-main-container')
                # 자영업자의 쉼터, 사장님도 장사의신 카페의 경우 하단 검색 노출을 위한 키워드 문단 제거
                if self.compare_domain in ['jangsin1004', 'vozlt']:
                    e = self.get_by_xpath('//div[@class="se-main-container"]')
                    # 모든 <p> 태그를 순회하며 패턴에 맞는 태그를 제거
                    for index, p in enumerate(middle_e.find_all("p")):
                        # <p> 태그 텍스트에서 패턴이 5개 이상 존재하는지 확인
                        if re.search(pattern, p.text):
                            p.decompose()  # 태그 자체를 삭제
                            # 스크린샷에서 제거하기 위해 HTML 제거
                            m_e = e.find_elements_by_xpath('.//p')[index]
                            self.driver.execute_script("arguments[0].remove();", m_e)

                msg['contents'] = middle_e.text.strip()
            except:
                middle_e = soup.find('div', class_='article_content_se')

                # 자영업자의 쉼터, 사장님도 장사의신 카페의 경우 하단 검색 노출을 위한 키워드 문단 제거
                if self.compare_domain in ['jangsin1004', 'vozlt']:
                    e = self.get_by_xpath('//div[@class="article_content_se"]')
                    # 모든 <p> 태그를 순회하며 패턴에 맞는 태그를 제거
                    for index, p in enumerate(middle_e.find_all("p")):
                        # <p> 태그 텍스트에서 패턴이 5개 이상 존재하는지 확인
                        if re.search(pattern, p.text):
                            p.decompose()  # 태그 자체를 삭제
                            # 스크린샷에서 제거하기 위해 HTML 제거
                            m_e = e.find_elements_by_xpath('.//p')[index]
                            self.driver.execute_script("arguments[0].remove();", m_e)

                if middle_e.find('embed') == None:
                    msg['contents'] = middle_e.text.strip()
                else:
                    # 단일 동영상인 경우 게시글 본문 UI가 다름. 유튜브 링크 수집
                    middle_video = middle_e.find('embed')
                    msg['contents'] = middle_video['src'] + middle_e.text.strip()
                    self.logger.info('단일 동영상 게시글 수집')
            #### 해시태그#########################
            if re.search(r'#\w+', msg['contents']):

                original_content = msg['contents']

                # 1. URL을 임시로 본문에서 제거 (예: '[URL_REMOVED]'로 대체)
                url_pattern = r'(https?://[^\s]+)'  # URL 패턴
                url_removed_content = re.sub(url_pattern, '[URL_REMOVED]', original_content)

                # 2. URL이 제거된 본문에서 해시태그를 추출
                self.contents_tag = re.findall(r'#.*?(?=#|\s|\n|\u200b|$)', url_removed_content)

                # 3. 원본 본문에서 추출된 해시태그를 한 번에 제거 (URL은 그대로 남김)
                if self.contents_tag:
                    # 추출된 해시태그들을 모두 OR로 연결한 패턴을 만들고, 한 번에 제거
                    for tag in self.contents_tag:
                        tag_pattern = re.escape(tag)  # 해시태그를 정규식에 맞게 처리
                        # 첫 번째 해시태그만 제거하고 이후의 동일한 해시태그는 남김
                        original_content = re.sub(tag_pattern, '', original_content, count=1)

                # 결과를 업데이트
                msg['contents'] = original_content

                contents_tag = self.contents_tag
                self.contents_tag = []
                msg['tag_list'] = []
            else:
                contents_tag = False
            ####################################################
            hash_tag = soup.find('div', class_='tag_area bottom_space')
            if hash_tag:
                for tag in hash_tag.find_all('a'):
                    msg['tag_list'].append(tag.text.strip())
            if contents_tag:
                msg['tag_list'].extend(contents_tag)
                msg['tag_list'] = list(set(msg['tag_list']))
                self.logger.info(f'본문 해시태그 수집완료 {msg["article_url"]}')

            self.logger.info('게시글 본문 수집 완료')

            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            e = self.get_by_xpath('//div[@class="se-main-container"]|//div[@class="article_content_se"]')
            if e.find_elements_by_tag_name('img'):
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    try:
                        self.move_to_element(sub_e)
                        sub_e_url = sub_e.get_attribute('src')
                        article_img_p = self.get_safe_path(
                            self.config['target']['folder'],
                            msg['article_id'],
                            f'{j}.png'
                        )
                        self.logger.info('게시글 이미지 저장 시작')
                        urlretrieve(sub_e_url, article_img_p)
                        self.logger.info('게시글 이미지 저장 성공')
                        msg['image_url_list'].append(sub_e_url)
                        msg['image_list'].append(f'{j}.png')
                    except:
                        # 실패한 이미지 URL 본문 내용에 저장
                        msg['contents'] += f'다운로드 실패 이미지 링크: {sub_e_url}'
                        self.logger.info(f'save_img error: {j}.png')

            # img_tags = middle_e.find_all('img')
            # for j, img in enumerate(img_tags):
            #     if 'src' in img.attrs:  # 이미지 태그에 'src' 속성이 있는지 확인
            #         try:
            #             article_img_p = self.get_safe_path(
            #                 self.config['target']['folder'],
            #                 msg['article_id'],
            #                 f'{j}.png'
            #             )
            #             self.logger.info('게시글 이미지 저장 시작')
            #             urlretrieve(img['src'], article_img_p)
            #             self.logger.info('게시글 이미지 저장 성공')
            #             msg['image_url_list'].append(img['src'])
            #             msg['image_list'].append(f'{j}.png')
            #         except:
            #             # 실패한 이미지 URL 본문 내용에 저장
            #             msg['contents'] += f'다운로드 실패 이미지: {img["src"]}'
            #             self.logger.info(f'save_img error: {j}.png')

            # 하단(댓글 수)
            # 700개 이상인 댓글의 경우 스킵하고 별도로 재수집하는 방안 진행.
            # 시간 단축을 위해 스크린 샷 찍기 전으로 변경
            self.logger.info('Collect bottom elements')
            bottom_e = soup.find('div', class_='CommonComment talk_comment_wrap ArticleComment')
            comment_num = bottom_e.find('em', class_='num')
            msg['num_comments'] = int(comment_num.text.strip())
            self.logger.info('Collect bottom elements complete')

            if msg['num_comments'] > 700:
                # 댓글 700개 초과 게시글 별도 txt파일에 로그 남김
                self.logger_c.info(f'댓글 700개 초과 게시글: 게시글 ID[{msg["article_id"]}], 게시글 url[{msg["article_url"]}], 제목[{msg["title"]}]')
                # 기존 로그 파일
                self.logger.info(
                    f'댓글 700개 초과 게시글: 게시글 ID[{msg["article_id"]}], 게시글 url[{msg["article_url"]}], 제목[{msg["title"]}]')
                return

            # 첨부파일, 현재 수집 안하는중
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                # 불필요한 이미지 제거
                self.remove_html()
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # self.full_screenshot(msg_capture_f)
                if self.config['params']['kwargs']['headless']:
                    try:
                        self.logger.info('article screenshot start')
                        self._screenshot(msg_capture_f)
                        self.logger.info('article screenshot complete')
                        msg['screenshot_error'] = False
                        msg['headless_option'] = True
                    except:
                        self.logger.info(
                            f'스크린 샷 에러 발생: article_id[{msg["article_id"]}], 게시글 제목[{msg["title"]}] 게시글 URL: {msg["article_url"]}')
                        msg['screenshot_error'] = True
                        msg['create_ts'] = None
                        # 데이터 저장 여부(수집 대상 게시글의 스크린 샷 에러가 발생하는 경우 키워드의 meta json 생성 안됨)
                        # self.save_data = False
                        self.switch_to_window(1)
                        return
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


            # 댓글이 없는 경우
            if msg['num_comments'] == 0:
                return
            # 댓글
            msg['comment_list'] = []

            # 댓글 페이지가 있는 경우 : 없으면 댓글 페이지만 들어가면 된다.
            try:
                e = self.get_by_xpath('//div[@class="CafeCommentSort"]//a[@class="link"]',
                                      cond='element_to_be_clickable')
                self.logger.info('Collect comment page element')
                self.safe_click(e)
                self.logger.info('comment page click')
                self.implicitly_wait(after_wait=1)
                # 댓글 더 보기가 있는 경우
                # 목록 1페이지에 100개 씩 노출됨. 100개 이하는 더보기 버튼 없음
                while msg['num_comments'] >= 100:
                    fold_flag = False

                    # 두 번째 : 펼쳐야 하는 경우가 없는 경우는 빠져 나가기
                    for more in self.driver.find_elements_by_xpath('//div[@class="comment_more"]//a[@class="more_next"]'):
                        self.safe_click(more)
                        self.logger.info('comment page more')
                        self.implicitly_wait(after_wait=1)
                        fold_flag = True

                    # 세 번째 : 펼쳐야 하는 경우
                    for more in self.driver.find_elements_by_xpath('//div[@class="comment_more"]//a[@class="more_next"]'):
                        self.safe_click(more)
                        self.logger.info('comment page more')
                        self.implicitly_wait(after_wait=1)
                        break

                    # while 문 빠져나가기
                    if fold_flag == False:
                        break
                self.logger.info('comment page more complete')
                self.get_comment(msg)
                self.logger.info('comment collection complete')
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
    def article_ids_from_web(self):
        # 게시글 목록 30개 까지만 가져옴
        # res = requests.get(self.driver.current_url)
        # 페이지의 HTML 소스 가져오기
        html_source = self.driver.page_source
        # BeautifulSoup을 사용하여 HTML 파싱
        soup = BeautifulSoup(html_source, 'html.parser')
        url_list = []
        url_list = [tag.get('href') for tag in soup.find_all('a', class_='title_link')]

        ids_pattern = re.compile(r'(?<=\/)\d+(?=\?)')
        domain_pattern = re.compile(r'naver\.com\/([^\/]+)\/(\d+)')
        article_ids = []
        for url in url_list:
            if url is None:
                pass
            else:
                try:
                    article_ids.append((url, domain_pattern.search(url).group(1) + '_' + ids_pattern.search(url).group(0)))
                except:
                    self.logger.error(f'{url} : format error - pass')
                    pass
        return article_ids

    # ==========================================================================
    def article_ids_from_db(self):
        # SQLite3 데이터베이스 연결
        conn = sqlite3.connect('compare_data.db')
        c = conn.cursor()

        # SQL 쿼리문 실행
        start_date = '2024-04-04 00:00:00'
        end_date = '2024-04-04 14:00:00'
        c.execute('''SELECT * FROM compare 
                            WHERE collection_date BETWEEN ? AND ?
                            LIMIT 1000''', (start_date, end_date))

        # 결과 가져오기
        rows = c.fetchall()

        # 결과 출력
        # for row in rows:
        #     print(row)

        # 연결 종료
        conn.close()

        # article_id만 추출하여 리스트로 만들기
        known_ids = [row[0] for row in rows]

        return known_ids

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

        # 메모장 조회
        # files = glob.glob(f'{keyword}*.txt')
        # if files:
        #     latest_file = max(files, key=os.path.getctime)
        #     with open(latest_file, 'r') as f:
        #         return f.read().splitlines()
        # return []

        # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            self.switch_to_window(0)

            # 스크롤 시간 체크
            start_scroll = time.time()
            SCROLL_PAUSE_TIME = 0.5
            # PAUSE_TIME = 1(35초 소요), PAUSE_TIME = 0.5(20초 소요), PAUSE_TIME = 0.2(12초 소요) PAUSE_TIME 없으면 안내려감
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            # 게시글 목록 스크롤 다운. 페이지 높이 변화가 없으때 까지
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(SCROLL_PAUSE_TIME)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight-50);")
                time.sleep(SCROLL_PAUSE_TIME)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                # print(new_height)
                if new_height == last_height:
                    break
                last_height = new_height
            end_scroll = time.time()
            scroll_time = end_scroll - start_scroll

            start_time = time.time()
            # 네이버 게시글 목록 URL, article_id 추출
            new_ids = list(self.article_ids_from_web())
            # new_ids를 OrderedDict로 변환하여 순서 유지
            ordered_new_ids = OrderedDict(new_ids)
            # 게시글 목록 게시글 ID- 로그로만 사용
            new_article_ids = list(ordered_new_ids.values())
            # DB에서 키워드 별 article_id select
            # known_ids = set(self.load_latest_article_ids(self.keyword, self.site_sequence))
            known_ids = set(self.load_latest_article_ids(self.keyword, self.site_sequence))
            # # new_ids에서 article_id만 뽑기
            # new_article_ids = set(article_id for _, article_id in new_ids)
            # 중복되지 않은 article_id 찾기
            unique_article_ids = [article_id for article_id in ordered_new_ids.values() if
                                  article_id not in known_ids]
            unique_data = [(url, article_id) for url, article_id in ordered_new_ids.items() if
                           article_id in unique_article_ids]
            # # 중복되지 않은 article_id 찾기
            # unique_article_ids = new_article_ids - known_ids
            # 중복되지 않은 article_id에 해당하는 데이터 추출 - 리스트 순서 바뀜 -> 딕셔너리, append
            end_time = time.time()

            execution_time = end_time - start_time
            self.logger.info(f'스크롤 다운 소요 시간:{scroll_time}초, 중복 데이터 비교 소요 시간:{execution_time}초')
            # new_ids, knwon_ids, unique_aritles 로그 찍기
            self.logger.info(f'게시글 목록: {len(new_ids)}개, DB 조회 데이터: {len(known_ids)}개, 중복되지 않은 게시글:{len(unique_article_ids)}개')
            self.logger.info(f'게시글 목록: {new_article_ids}\n DB 조회 데이터: {known_ids}\n 중복되지 않은 게시글 ID:{unique_article_ids}')

            count_a = 0
            for url, article_id in unique_data:
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
                    # 폐쇄 카페 스킵
                    self.compare_domain = url.partition('.com/')[2].partition('/')[0]
                    # 도메인 값 비교로 폐쇄 카페 스킵
                    remove_cafe_list = ['nds07', 'galaxysc', 'jihosoccer123', 'dieselmania', 'barman', 'cosmania',
                                        'remonterrace', 'skybluezw4rh']
                    if self.compare_domain in remove_cafe_list:
                        self.logger.debug('폐쇄카페 게시글입니다.--------------(SKIP)')
                        self.logger.debug(f'게시글의 url: {url}')
                        self.save_data = False
                        continue
                    msg['article_id'] = article_id
                    msg['article_url'] = url

                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    c_start_time = time.time()
                    # 실제 수집
                    self.driver.execute_script(f"window.open('{url}');")
                    self.get_article(msg, count_a + 1, url)
                    c_end_time = time.time()

                    collections_time = c_end_time - c_start_time
                    self.logger.info(f'게시글 수집 시간: {collections_time}, article_id[{msg["article_id"]}]')
                    # print(f'게시글 수집 시간: {collections_time}, article_id[{msg["article_id"]}]')
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
                    # self.save_image(msg)
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
                    self.logger.error(f'comment_save_img: {cmt["comment_id"], cmt["comment_img_url"]}: {str(err)}')

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
            self.get_page()
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
    with NaverTotalSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = "naver_total.yaml"
    do_start(config_f=_config_f)
