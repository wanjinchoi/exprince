"""
====================================
 :mod:`kin/kin_naver`
====================================
.. moduleauthor:: Sebin Eun <akb0930@argos-labs.com>
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
#  * [2024/01/08]
#     - 작성시간은 00:00:00으로 고정
#     - 첫번째 키워드에서 쿠키파일 만료 및 없는 경우, 로그인 진행
#     - 다음 키워드부터는 쿠키파일 가져와서 수집 진행
#  * [2024/01/04]
#     - 검색 결과값 존재 여부 확인 로직 수정
#     - 로그 파일 경로 수정
#  * [2023/12/27]
#     - 하단검색 개발
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
import urllib.request
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


################################################################################

class NaverKINSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        self.cookie_path = "C:\\work\\voc\\yaml\\카페\\네이버" + "\\cookies.pkl"
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverKINSearch_under.log'),
                            logsize=1024 * 1024 * 10)
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
        self.compare_create_ts = None

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
        self.logger.info(f'Starting Naver KIN Crawaling... with '
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
            # 게시글 목록 스크린샷
            # self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
            # s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            # s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            # self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
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
    def search(self):
        try:
            # 검색어 입력
            e = self.get_by_xpath('(//div[@class="search_area _heading_search"]/input)[1]')
            if 'search_complex' in self.config['params']['site']:
                self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
            else:
                self.send_keys(e, self.config['params']['site']['search'])

            # 검색 단추
            e = self.get_by_xpath('(//div[@class="search_area _heading_search"]/a)[1]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)

            # 필터 설정 (50개씩 보기)
            e = self.get_by_xpath('(//div[@class="select_area _countPerPageSelectBox"])[1]')
            e_a = e.find_element_by_xpath('./a')
            self.safe_click(e_a)
            e_b = e.find_element_by_xpath('./ul/li[7]')
            self.safe_click(e_b)

            # 최신순 클릭
            e = self.get_by_xpath('(//ul[@class="sort_list_module _sortOptionList"]/li[@class="_recent"])[1]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

        except Exception as err:
            self.logger.error(str(err))
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_parent_comment(self, msg, a_a):
        try:
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            cmt = {
                'comment_id': None,
                'is_reply': False,
                'parent_comment_id': None,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': [],
           }

            # 댓글이 삭제 됐으면 예외 처리
            try:
                a_a.find_element_by_xpath('.//div[@class="_endContents c-heading-answer__content"]')
            except:
                return
            # 댓글 nickname
            e = a_a.find_element_by_xpath('.//p[@class="title"]')
            cmt['nickname'] = e.text.rpartition('님')[0].strip()
            self.move_to_element(e)

            # 댓글 공감수
            try:
                e = a_a.find_element_by_xpath('.//span[@class="u_likeit_text _count num"]')
                cmt['like'] = int(e.text.strip())
            except:
                cmt['like'] = 0

            # 댓글 내용
            e = a_a.find_element_by_xpath('.//div[@class="se-module se-module-text"]')
            cmt['contents'] = e.text.strip()

            # 댓글 작성일시
            e = a_a.find_element_by_xpath('.//p[@class="c-heading-answer__content-date"]')
            cmt['create_ts'] = ""
            et = e.text.strip()
            hhh, mmm = 0, 0
            if et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            else:
                cmt['create_ts'] = et[:-1] + ' 00:00:00'
            try:
                if cmt['create_ts'] == "":
                    d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                    cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
            except:
                pass

            # 댓글 아이디
            cmt['comment_id'] = 'cmt' + str(len(msg['comment_list']))
            # 댓글 이미지
            cmt['comment_img_url'] = []
            cmt['comment_img'] = []
            inner_html = a_a.get_attribute('innerHTML')
            if inner_html.find('img') > 0:
                re_img = './/div[@class="se-module se-module-image"]/a/img' \
                         '|.//a[@class="se-oglink-thumbnail"]/img'
                for k, sub_a in enumerate(a_a.find_elements_by_xpath(re_img)):
                    img_url = sub_a.get_attribute('src')
                    cmt['comment_img_url'].append(img_url)
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_" + str(k)}.png')

            # 댓글 목록에 추가
            msg['comment_list'].append(cmt)
            self.logger.info(f'{cmt["comment_id"]}')

            # 대댓글 확인
            e = a_a.find_element_by_xpath('.//div[@class="c-userinfo-answer _answerBottom"]')
            # A의 댓글 수가 0이 아니면 댓글 창을 클릭
            try:
                e_b = e.find_element_by_xpath('.//em[@class="button_compose_count _commentCnt"]')
                b_comments = e_b.text
            except:
                return
            parent_comment_id = ''
            if e_b.text != '':
                self.safe_click(e_b)
                s_comments = int(b_comments) + len(msg['comment_list'])
                try:  # 추가 질문이 있으면 한 번 더 클릭 해야 열림
                    e_cmt = self.get_by_xpath('//div[@id="additionalQnaList"]')
                    self.safe_click(e_b)
                except:
                    pass
                is_end = True
                while is_end:
                    e_ce = self.get_by_xpath('//div[@class="answer-content__item _contentWrap _answer"]')
                    cmt_s = e_ce.find_elements_by_xpath(
                        './/div[@class="c-opinion__item"]')
                    for cmt in cmt_s: # 123
                        self.get_comment(msg, cmt, parent_comment_id)
                    # 질문 댓글에 페이지 테이블
                    e = self.get_by_xpath(
                        '//div[@class="answer-content__item _contentWrap _answer"]//div[@class="paginator paginator--number _pagingArea"]', timeout=1)
                    cmt_pages = e.find_elements_by_xpath('./a')
                    if len(cmt_pages) == 1:
                        break
                    is_on = False
                    for cmt_page in cmt_pages:
                        if cmt_page.get_attribute('class') == 'paginator__num_item _pagingBtn is-active':
                            is_on = True
                            continue
                        if is_on:
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                            break
                    if s_comments == len(msg['comment_list']):
                        break

        finally:
            self.switch_to_window(1)

    # ==========================================================================
    def get_comment(self, msg, cmt_e, parent_comment_id):
        try:

            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            cmt = {
                'comment_id': None,
                'is_reply': True,
                'parent_comment_id': None,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': [],
            }
            cmt['parent_comment_id'] = parent_comment_id
            cmt['is_reply'] = parent_comment_id != None
            # 대댓글 nickname
            e = cmt_e.find_element_by_xpath('.//p[@class="c-opinion__list-nick"]')
            cmt['nickname'] = e.text.strip()
            self.move_to_element(e)

            # 대댓글 내용
            e = cmt_e.find_element_by_xpath('.//div[@class="c-opinion__list-text"]/p')
            cmt['contents'] = e.text.strip()

            # 대댓글 작성 일시
            e = cmt_e.find_element_by_xpath('.//p[@class="c-opinion__list-date"]')
            e_ts = e.text
            v = e_ts.rpartition(".")[0]
            n = e_ts.rpartition(".")[2].strip()
            cmt['create_ts'] = v + " " + n

            # 댓글 아이디
            cmt['comment_id'] = 'cmt' + str(len(msg['comment_list']))

            # 댓글 좋아요 질문의 댓글에는 좋아요가 없음 무조건 0
            cmt['like'] = 0

            # 댓글 목록에 추가
            msg['comment_list'].append(cmt)
            self.logger.info(f'{cmt["comment_id"]}')
        finally:
            self.switch_to_window(1)

        # ========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)

            contents_e = self.get_by_xpath('//div[@class="question-content"]')

            if self.config['params']['site']['capture_article']:
                # save capture
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@id="smartEditorArea"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_head)
                    self.implicitly_wait(after_wait=1)
                    self.full_screenshot(msg_capture_f)
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
            # contents_e = self.get_by_xpath('//div[@class="question-content"]')
            parent_comment_id = ''
            cmt['is_reply'] = False
            cmt['parent_comment_id'] = ''
            cmt['comment_id'] = parent_comment_id

            # 작성 시간
            e = contents_e.find_element_by_xpath('.//span[@class="c-userinfo__info"][1]')
            et = e.text
            hhh, mmm = 0, 0
            if et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            else:
                ec = et.partition('작성일')[2].strip()
                msg['create_ts'] = ec + ' 00:00:00'
                self.compare_create_ts = ec + ' 00:00:00'
            try:
                if self.compare_create_ts is None:
                    d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                    msg['create_ts'] = d.strftime('%Y.%m.%d 00:00:00')
                    self.compare_create_ts = d.strftime('%Y.%m.%d %H:%M:%S')
            except:
                pass
            # 조회수
            e = contents_e.find_element_by_xpath('.//span[@class="c-userinfo__info"][2]')
            e_m = e.text.partition('조회수')[2].strip()
            msg['view_count'] = int(re.sub(r'[^0-9]', '', e_m))
            # 작성자
            try:
                e = contents_e.find_element_by_xpath('.//span[@class="c-userinfo__author"]')
                msg['author'] = e.text.partition('닉네임')[2].strip()
            except:  # 가끔 작성자가 없는 경우가 있음
                msg['author'] = ""

            # Q 페이지
            e_a = self.get_by_xpath('//div[@class="question-content"]')
            # 태그 이름
            e = e_a.find_element_by_xpath('.//div[@class="tag-list tag-list--end-title"]')
            tag_name = e.text.partition('Ξ')[2].strip()
            # msg['tag_name'] = tag_name
            # 게시글 내용:
            try:
                e = e_a.find_element_by_xpath('.//div[@class="c-heading__content"]')
                msg['contents'] = e.text.strip() + '\n' + tag_name
            except:
                msg['contents'] = "" + tag_name

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e_a.get_attribute('innerHTML')
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('se-module se-module-image') > 0:
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 게시글 댓글 단 목록 열기
            msg['comment_list'] = []
            e = self.get_by_xpath('//div[@class="question-content"]')
            # Q의 댓글 수가 0이 아니면 댓글 창을 클릭
            e_b = e.find_element_by_xpath('.//em[@class="button_compose_count _commentCnt"]')
            parent_comment_id = ''
            if e_b.text != '':
                self.safe_click(e_b)
                is_end = True
                while is_end: #567
                    cmt_d = self.get_by_xpath(
                        '//div[@class="question-content"]//div[@class="c-opinion _commentListArea"]')
                    cmt_s = cmt_d.find_elements_by_xpath('.//div[@class="c-opinion__item"]')
                    for cmt in cmt_s:
                        self.get_comment(msg, cmt, parent_comment_id)
                    # 질문 댓글에 페이지 테이블
                    e = self.get_by_xpath(
                        '//div[@class="question-content"]//div[@class="paginator paginator--number _pagingArea"]',timeout=1)
                    cmt_pages = \
                        e.find_elements_by_xpath('./a')
                    if len(cmt_pages) == 1:
                        break
                    is_on = False
                    for k, cmt_page in enumerate(cmt_pages):
                        if cmt_page.get_attribute('class') == 'paginator__num_item _pagingBtn is-active':
                            is_on = True
                            continue
                        if is_on:
                            self.safe_click(cmt_page)
                            self.implicitly_wait(after_wait=1)
                            break
                    if int(e_b.text) == len(msg['comment_list']):
                        break
                    # 질문의 댓글이 마지막 페이지인 경우
                    # if is_on:
                    #     break

            # 답변(없는 경우 리턴)
            try:
                e = contents_e.find_element_by_xpath('//div[@class="answer-content__list _answerList"]')
            except:
                return
            # 댓글 더보기 클릭
            try: # A가 5개 이상일시 더 보기가 생긴다.
                try:
                    while True:
                        e = self.get_by_xpath('//div[@class="answer-content__list _answerList"]/../..')
                        cmt_p = e.find_element_by_xpath('.//a[@id="nextPageButton"]')
                        self.safe_click(cmt_p)
                        self.implicitly_wait(after_wait=1)
                        if cmt_p.text == '':
                            break
                    e = self.get_by_xpath('//div[@class="answer-content__list _answerList"]')
                    a_as = e.find_elements_by_xpath('./div')
                    for a_a in a_as:
                        self.get_parent_comment(msg, a_a)
                except:
                    e = self.get_by_xpath('//div[@class="answer-content__list _answerList"]')
                    a_as = e.find_elements_by_xpath('./div')
                    for a_a in a_as:
                        self.get_parent_comment(msg, a_a)
            except:
                pass

            # 추가 질문 확인
            try:
                e_cmt = e.find_element_by_xpath('.//div[@id="additionalQnaList"]')
                e_cmts = e_cmt.find_elements_by_xpath('./div')
                for i, e_c in enumerate(e_cmts):
                    cmt = {
                        'comment_id': None,
                        'is_reply': True,
                        'parent_comment_id': None,
                        'create_ts': None,
                        'nickname': None,
                        'contents': None,
                        'like': None,
                        'dislike': None,
                        'comment_img': [],
                        'comment_img_url': [],
                    }
                    cmt['parent_comment_id'] = parent_comment_id
                    cmt['is_reply'] = parent_comment_id != ''
                    # 추가질문 작성자
                    e = e_c.find_element_by_xpath('.//div[@class="addition-qna__info-title"]')
                    cmt['nickname'] = e.text.strip()
                    # 추가질문자 id ( 0 ~ n )
                    e = e_c.get_attribute('data-answer-no')
                    cmt['comment_id'] = e
                    # 추가질문 내용
                    e = e_c.find_element_by_xpath('.//div[@class="addition-qna__info-text"]')
                    cmt['contents'] = e.text.strip()
                    # 추가질문 날짜
                    e = e_c.find_element_by_xpath('.//div[@class="addition-qna__info-date"]')
                    cmt['create_ts'] = ""
                    et = e.text.strip()
                    hhh, mmm = 0, 0
                    if et.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', et)
                        mmm = int(mm)
                    elif et.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', et)
                        hhh = int(hh)
                    else:
                        cmt['create_ts'] = et[:-1] + ' 00:00:00'
                    try:
                        if cmt['create_ts'] == "":
                            d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                            cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                    except:
                        pass
                    # 추가질문 좋아요
                    cmt['like'] = 0

                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
                    self.logger.info(f'{cmt["comment_id"]+ "_plus"}')
            except:
                pass
        except Exception as err:
            raise
        finally:
            # 이전 페이지
            msg['num_comments'] = len(msg['comment_list'])
            if len(msg['comment_list']) == 0:
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
                msg['comment_list'].append(cmt)
            self.driver.close()
            self.implicitly_wait(after_wait=1)
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
            create_ts = datetime.datetime.strptime(self.compare_create_ts, '%Y.%m.%d %H:%M:%S')
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
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            # 결과값 존재 여부 확인
            e = self.get_by_xpath('//div[@class="tc-panel tc-selected"]//div[@class="answer_list _dir_content_noanswer_noresult"]')
            e_a = e.get_attribute('style')
            if e_a == 'display: block;':
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
                return
            else:
                e = self.get_by_xpath('//div[@class="answer_list _noanswer_list"]')
            es = e.find_elements_by_xpath('./div')

            # 게시글 목록 스크린샷
            # self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
            # s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            # s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            # # self.driver.find_element_by_tag_name('body').full_screenshot(self.get_safe_path(s_shot))
            # self.full_screenshot(self.get_safe_path(s_shot))

            for i, ea in enumerate(es):
                self.compare_create_ts = None
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
                    e = self.get_by_xpath('//div[@class="answer_list _noanswer_list"]')
                    es = e.find_elements_by_xpath('./div')
                    ea = es[i]
                    # 1) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('.//div[@class="tit_wrap "]/a')
                    a_url = e_url.get_attribute('href')
                    id = a_url.partition('docId=')[2].partition('&')[0]
                    msg['article_id'] = id
                    # 1) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 2) 제목: title
                    e = ea.find_element_by_xpath('.//span[@class="tit_txt"]')
                    msg['title'] = e.text.strip()
                    # 3) 답변 수
                    # e = ea.find_element_by_xpath('.//span[@class="hit"]')
                    # en = e.text
                    # eb = re.sub(r'[^0-9]','', en)
                    # msg['A_number'] = int(eb)
                    # 4) 추천 수
                    # e = ea.find_element_by_xpath('.//dd[@class="txt_block"]')
                    # ec = e.text
                    # e_a = ec.partition('추천수')[2].partition('|')[0]
                    # msg['like'] = int(re.sub(r'[^0-9]', '', e_a))
                    # 5) 카테고리
                    e = ea.find_element_by_xpath('./div[@class="update_info"]/span[@class="info"][1]')
                    ec = e.text.strip()
                    msg['board_name'] = 'under_' + ec

                    self.safe_click(e_url)
                    self.implicitly_wait(after_wait=1)

                    try:
                        # self.switch_to_main_window()
                        # # 커넥션 에러로 인해 새로 고침 추가
                        # self.switch_to_window(1)
                        # self.driver.refresh()
                        # self.implicitly_wait(after_wait=1)

                        self.switch_to_window(1)
                        self.implicitly_wait(after_wait=1)

                        # 600초 동안 응답없으면 삭제된 게시글 처리
                        timeout = 600  # 초 단위
                        element_present = EC.presence_of_element_located((By.XPATH, "//div[@class='question-content']"))
                        WebDriverWait(self.driver, timeout).until(element_present)

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
                        i = i + 1
                        continue

                    # self.safe_click(e_url)
                    # self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
                except Exception as err:
                    if 'article_id' not in msg:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
                # 2일 전 데이터가 아닌 경우 스킵
                if msg['contents'] is None:
                    continue

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
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================

    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//div[@id="pagingArea0"]')
            self.move_to_element(e)
            for pa in e.find_elements_by_xpath('./a'):
                if pa.text.strip() == '다음':
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
                elif pa.text.strip() == '이전':
                    continue
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
        # 기존
        # cookies = pickle.load(open(self.cookie_path, "rb"))
        # for cookie in cookies:
        #     self.driver.add_cookie(cookie)
        # self.driver.refresh()
        # self.driver.get(self.config['params']['kwargs']['url'])
        # self.implicitly_wait(after_wait=1)
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
            raise

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            if self.search_index == 0:
                try:
                    self.a_cookie()
                except:
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
            return 9
        finally:
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
            with NaverKINSearch(kwargs['config_f'], keyword, i) as ws:
                r = ws.start()
            if r == 1:
                break
        return r
    # with NaverKINSearch(kwargs['config_f']) as ws:
    #     ws.start()
    #     return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'kin_naver_under.yaml'
    do_start(config_f=_config_f)
