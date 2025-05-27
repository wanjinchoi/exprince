"""
====================================
 :mod:`community/teamblind`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for teamblind
"""
# Authors
# ===========
#
# * Sebin Eun
#
# Change Log
# --------
#  * [2024/10/21]
#     - 게시글에 광고성 이미지가 포함 되어 있을 경우 제외하고 수집
#     - 댓글에 뱃지 이미지 제외 하고 수집
#  * [2024/08/14]
#     - 투표 게시글 수집 로직 추가
#  * [2024/08/08]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. 이미지 자르는 방식
#     - 크롬 옵션에 사이즈 변경 추가(넓이가 작은 경우 검색 박스를 찾지 못함)
#  * [2024/08/06]
#     - 광고 제거를 위한 크롬 옵션 추가 (ublockorigin 사용)
#  * [2024/07/29]
#     - 광고 팝업 삭제 로직 중복 실행
#  * [2024/07/24]
#     - 광고 팝업 삭제 로직 추가
#     - 조회수 K로 노출되는 게시글 존재
#  * [2024/07/11]
#     - 게시글 내부 이미지 가져오는 로직 수정
#     - 게시글 본문에서 tag 제외하는 부분 수정
#     - 댓글에 제한된 댓글이라는 케이스 추가되어 처리 로직 추가
#     - 투표 수집하여 본문에 추가하도록 수정
#  * [2024/07/08]
#     - 게시글 내부 이미지 가져오는 부분의 xpath 수정
#  * [2024/06/10]
#     - 구글 자체 광고창 제거 로직 추가(옵션 변경)
#  * [2024/06/04]
#     - 게시글 스크린샷 전에 광고 팝업창 기다리는 로직 추가
#  * [2024/03/19]
#     - 게시글 스크린샷 순서 변경
#     - 에러로그 세분화
#  * [2024/03/14]
#     - 수집 모듈 최적화
#     - 에러 코드 세분화(chrome 에러:11, 나머지:1)
#  * [2024/02/19]
#     - 게시글 페이지에 광고가 위,양옆에 추가되면서 게시글 스크린샷 로직 수정
#  * [2023/07/26]
#     1. 게시글 등록 시간 '어제'인 경우 23:30:00 으로 고정 시간 값 추가
#     2. 수집 영역 수정 ( 5가지 -> 전체 )
#     3. 게시글 목록 스크린 샷 추가
#  * [2023/07/18]
#     - 게시글 수집 후 창 닫는 부분 수정
#  * [2023/05/11]
#     - starting


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
import traceback
import urllib.request
import datetime
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, WebDriverWait, By, webdriver
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO


################################################################################
class teamblindSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'BlindSearch.log'),
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
        self.cmt_done = False
        self.article_num = 0
        out_config = deepcopy(self.config)
        # del out_config['params']['site']['passwd']
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
        self.logger.info(f'Starting Nate Pann Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================

    def login(self):
        try:
            # 로그인 클릭
            e = self.get_by_xpath('//*[@id="GnbWrap"]/div[2]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # login 화면
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="uid"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//*[@id="upw"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="f_login"]/fieldset/input',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
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
            e = self.get_by_xpath('//*[@name="keyword"]')
            if 'search_complex' in self.config['params']['site']:
                self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
            else:
                self.send_keys(e, self.config['params']['site']['search'])
            # 검색 단추
            e = self.get_by_xpath('//button[@class="btn-srch"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=2)
            # 날짜순 정렬
            e = self.get_by_xpath('//div[@class="wrap-category-pc"]/div[@class="sort"]', cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            for date in e.find_elements_by_xpath('.//div[@id="search_sort"]/a'):
                if date.text.strip() == '최신순':
                    self.safe_click(date)
                    self.implicitly_wait(after_wait=1)
        except Exception as err:
            raise

    # ==========================================================================
    def save_e_img(self, re_img, msg, cmt):
        cmt_img_f = self.get_safe_path(
            self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"]+"_0"}.png')
        re_img.screenshot(cmt_img_f)

    # ==========================================================================
    def next_cmt(self):

        # 역할
        # 1. 대댓글 페이지를 넘기는 기능과
        # 2. 더 이상 페이지가 없는 경우 대댓글이 없음을 알려주는 기능 수행 self.reply_done = true
        # 참고 : 최문창님의 코드 인용하여 적용

        # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
        # 따라서 두 가지 종류의 태그를 모두 구해야 함
        # 현재의 게시글이 포함된 페이지는 class가 current이다.
        try:
           cmtPagePart = self.get_by_xpath('//div[@class="paginate-reple"]')
           is_current = False # 다음 페이지로 넘기기 위해 사용하는 플래그
           for cmtPage in cmtPagePart.find_elements_by_xpath('.//strong | .//a'):
               if cmtPage.get_attribute('class') == 'current':
                   is_current = True
                   continue
               if is_current:
                   self.safe_click(cmtPage)
                   self.implicitly_wait()
                   return
           self.cmt_done = True
        except Exception as err:
           raise
        finally:
           return

    # ==========================================================================
    def get_cmt(self, msg):
        try:
            self.remove_html('//span[@class="badge"]')
            comments_e = self.get_by_xpath('//div[@class="article-comments"]')
            comments = comments_e.find_elements_by_xpath('./div')
            parent_comment_id = None
            for i, cmt_e in enumerate(comments):
                comments_es = self.get_by_xpath('//div[@class="article-comments"]')
                comments_e = comments_es.find_elements_by_xpath('./div')
                cmt_e = comments_e[i]
                # 댓글 작성하기
                if cmt_e.get_attribute('class') == 'write_area':
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

                    # 대댓글인지 확인
                    if cmt_e.get_attribute('class') == 'wrap-reply':
                        re_cmts = cmt_e.find_elements_by_xpath('./div[@class="wrap-comment comment_area"]')
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
                            re_cmts = cmt_e.find_elements_by_xpath('./div[@class="wrap-comment comment_area"]')
                            re_cmt = re_cmts[j]
                            # 댓글 id
                            self.move_to_element(re_cmt)
                            cmt['comment_id'] = re_cmt.get_attribute('id')

                            # 삭제된 댓글
                            e_del_reply = re_cmt.get_attribute('innerHTML')
                            if e_del_reply.find('cmt-txt delete') > 0:
                                continue
                            # 제한된 댓글
                            elif e_del_reply.find('contents-limit') > 0:
                                continue
                            else:
                                # 댓글 작성자 닉네임
                                e = re_cmt.find_element_by_xpath('./p[@class="name"]')
                                cmt['nickname'] = e.text.strip()
                                # 좋아요
                                e = re_cmt.find_element_by_xpath('.//a[@class="like"]')
                                like = e.text.strip().split('\n')[1]
                                if like == '좋아요':
                                    cmt['like'] = 0
                                else:
                                    cmt['like'] = int(like)
                                # 댓글 작성 시간
                                e = re_cmt.find_element_by_xpath('.//span[@class="date"]')
                                et = e.text
                                ddd, hhh, mmm = 0, 0, 0
                                cmt['create_ts'] = ""
                                if et.find('방금') > 0:
                                    d = datetime.datetime.now()
                                    cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                                elif et.find('분') > 0:
                                    mm = re.sub(r'[^0-9]', '', et)
                                    mmm = int(mm)
                                elif et.find('시간') > 0:
                                    hh = re.sub(r'[^0-9]', '', et)
                                    hhh = int(hh)
                                elif et.find('어제') > 0:
                                    ddd = int(1)
                                elif len(et) == 15:
                                    cmt['create_ts'] = et.split('\n')[1].rpartition('.')[0] + ' 00:00:00'
                                elif len(et) == 9:
                                    cmt['create_ts'] = str(datetime.datetime.now().year) + '.' + et.split('\n')[1] + ' 00:00:00'
                                elif et.find('일') > 0:
                                    dd = re.sub(r'[^0-9]', '', et)
                                    ddd = int(dd)
                                else:
                                    cmt['create_ts'] = et.split('\n')[1] + ' 00:00:00'
                                if cmt['create_ts'] == "":
                                    d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                                    cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                                cmt['create_ts'] = datetime.datetime.strptime(msg['create_ts'],
                                                                              '%Y.%m.%d %H:%M:%S').strftime(
                                    '%Y.%m.%d %H:%M:%S')
                                # 댓글 내용 text
                                e = re_cmt.find_element_by_xpath('./p[@class="cmt-txt"]')
                                cmt['contents'] = e.text.strip()
                                # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                                inner_html = e.get_attribute('innerHTML')
                                if inner_html.find('video') > 0:
                                    re_img = e.find_element_by_tag_name('video')
                                    cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                    self.save_e_img(re_img, msg, cmt)
                                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                                elif inner_html.find('img') > 0:
                                    re_img = e.find_element_by_tag_name('img')
                                    cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                    self.save_e_img(re_img, msg, cmt)
                                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                            # 댓글 목록에 추가
                            msg['comment_list'].append(cmt)
                    else:
                        cmt['is_reply'] = False
                        # 댓글 id
                        self.move_to_element(cmt_e)
                        cmt['comment_id'] = cmt_e.get_attribute('id')
                        # 댓글 부모 대댓글이 아니면 공백
                        parent_comment_id = cmt['comment_id']

                        # 삭제된 댓글
                        e_del_reply = cmt_e.get_attribute('innerHTML')
                        if e_del_reply.find('cmt-txt delete') > 0:
                            continue
                        # 제한된 댓글
                        elif e_del_reply.find('contents-limit') > 0:
                            continue
                        else:
                            # 댓글 작성자 닉네임
                            e = cmt_e.find_element_by_xpath('./p[@class="name"]')
                            cmt['nickname'] = e.text.strip()
                            # 좋아요
                            e = cmt_e.find_element_by_xpath('.//a[@class="like"]')
                            like = e.text.strip().split('\n')[1]
                            if like == '좋아요':
                                cmt['like'] = 0
                            else:
                                cmt['like'] = int(like)
                            # 댓글 작성 시간
                            e = cmt_e.find_element_by_xpath('.//span[@class="date"]')
                            et = e.text
                            ddd, hhh, mmm = 0, 0, 0
                            cmt['create_ts'] = ""
                            if et.find('방금') > 0:
                                d = datetime.datetime.now()
                                cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                            elif et.find('분') > 0:
                                mm = re.sub(r'[^0-9]', '', et)
                                mmm = int(mm)
                            elif et.find('시간') > 0:
                                hh = re.sub(r'[^0-9]', '', et)
                                hhh = int(hh)
                            elif et.find('어제') > 0:
                                ddd = int(1)
                            elif len(et) == 15:
                                cmt['create_ts'] = et.split('\n')[1].rpartition('.')[0] + ' 00:00:00'
                            elif len(et) == 9:
                                cmt['create_ts'] = str(datetime.datetime.now().year) + '.' + et.split('\n')[1] + ' 00:00:00'
                            elif et.find('일') > 0:
                                dd = re.sub(r'[^0-9]', '', et)
                                ddd = int(dd)
                            else:
                                cmt['create_ts'] = et.split('\n')[1] + ' 00:00:00'
                            if cmt['create_ts'] == "":
                                d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                                cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                            cmt['create_ts'] = datetime.datetime.strptime(msg['create_ts'],
                                                                          '%Y.%m.%d %H:%M:%S').strftime(
                                '%Y.%m.%d %H:%M:%S')
                            # 댓글 내용 text
                            e = cmt_e.find_element_by_xpath('./p[@class="cmt-txt"]')
                            cmt['contents'] = e.text.strip()
                            # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                            inner_html = cmt_e.get_attribute('innerHTML')
                            if inner_html.find('video') > 0:
                                re_img = cmt_e.find_element_by_tag_name('video')
                                cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                self.save_e_img(re_img, msg, cmt)
                                cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                            elif inner_html.find('img') > 0:
                                re_img = cmt_e.find_element_by_tag_name('img')
                                cmt['comment_img_url'].append(re_img.get_attribute('src'))
                                self.save_e_img(re_img, msg, cmt)
                                cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                        # 댓글 목록에 추가
                        msg['comment_list'].append(cmt)
                    self.logger.info(f'   [{i + 1}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            raise

    # ==========================================================================
    def get_vote_data(self, msg):
        try:
            msg['vote'] = []
            e_ab = self.get_by_xpath('//div[@class="contents"]')
            vote_list = e_ab.find_elements_by_xpath('.//div[@class="attach-poll"]')

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
                # 투표 참여 인원
                vote_involve_cnt = self.get_by_xpath('//div[@class="state"]/strong/em')
                vote['vote_involve_cnt'] = vote_involve_cnt.text.strip()
                vote['vote_complete'] = False
                # 투표 항목 & 결과 수집
                re_list = e_ab.find_elements_by_xpath('./div[@class="article-view-contents"]//div[@class="bx-radio"]')
                for j, vote_list_a in enumerate(re_list):
                    vote_item = {
                        'vote_num': j,  # 투표항목 넘버링
                        'vote_text': None,  # 투표항목
                        'vote_cnt': None,  # 투표 득표수
                        'vote_rate': None,  # 투표 득표퍼센트
                    }
                    vote_item['vote_text'] = vote_list_a.text.strip()
                    vote['vote_item'].append(vote_item)
                # 투표 목록에 추가
                msg['vote'].append(vote)
        except Exception as err:
            self.logger.error(f'get_vote_data: error: {str(err)}')
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            e_ab = self.get_by_xpath('//div[@class="contents"]')
            # 1) 제목
            e = e_ab.find_element_by_xpath('./div[@class="article-view-head"]/h2')
            msg['title'] = e.text.strip()
            # 2) 작성자
            e = e_ab.find_element_by_xpath('./div[@class="article-view-head"]/div[@class="name"]')
            msg['author'] = e.text.strip()
            # 3) 작성일
            e = e_ab.find_element_by_xpath('./div[@class="article-view-head"]/div[@class="wrap-info"]/span[@class="date"]')
            et = e.text.strip()
            ddd, hhh, mmm = 0, 0, 0
            msg['create_ts'] = ""
            if et.find('방금') > 0:
                d = datetime.datetime.now()
                msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
            elif et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            elif et.find('어제') > 0:
                dd = 1
                ddd = int(dd)
                d = datetime.datetime.now() - timedelta(days=ddd)
                msg['create_ts'] = d.strftime('%Y.%m.%d') + ' 23:30:00'
            elif len(et) == 15:
                msg['create_ts'] = et.split('\n')[1].rpartition('.')[0] + ' 00:00:00'
            elif len(et) == 9:
                msg['create_ts'] = str(datetime.datetime.now().year) + '.' + et.split('\n')[1] + ' 00:00:00'
            elif et.find('일') > 0:
                dd = re.sub(r'[^0-9]', '', et)
                ddd = int(dd)
            else:
                msg['create_ts'] = et.split('\n')[1] + ' 00:00:00'
            if msg['create_ts'] == "":
                d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
            msg['create_ts'] = datetime.datetime.strptime(msg['create_ts'],
                                                          '%Y.%m.%d %H:%M:%S').strftime(
                '%Y.%m.%d %H:%M:%S')
            # 5) 조회수
            e = e_ab.find_element_by_xpath('./div[@class="article-view-head"]/div[@class="wrap-info"]/span[@class="pv"]')
            e_a = e.text.strip().split('\n')[1]
            if ',' in e_a:
                e_aa = e_a.replace(',', '')
            elif 'K' in e_a:
                e_aa = e_a.replace('K', '1000')
            else:
                e_aa = e_a
            msg['view_count'] = int(e_aa)
            # 7) 댓글수
            e = e_ab.find_element_by_xpath('./div[@class="article-view-contents"]//a[@class="cmt"]')
            cmt = e.text.strip().split('\n')[1]
            if cmt == '댓글':
                msg['num_comments'] = 0
            else:
                msg['num_comments'] = int(cmt)
            # 6) 추천수
            e = e_ab.find_element_by_xpath('./div[@class="article-view-contents"]//a[@class="like"]')
            like = e.text.strip().split('\n')[1]
            if like == '좋아요':
                msg['like'] = 0
            else:
                msg['like'] = int(like)

            # 8) 해쉬태그
            for tag in e_ab.find_elements_by_xpath('./div[@class="article-view-contents"]/p/a[@class="tag"]'):
                msg['tag_list'].append(tag.text.strip())
            # 투표
            if len(e_ab.find_elements_by_xpath('.//div[@class="attach-poll"]')) > 0:
                self.get_vote_data(msg)
            # 8) 본문
            e = e_ab.find_element_by_xpath('./div[@class="article-view-contents"]/p')
            self.move_to_element(e)
            contents = e.text.strip()
            if len(msg['tag_list']) == 0:
                contents = contents
            else:
                for tag in msg['tag_list']:
                    contents = contents.replace(tag, '')
            msg['contents'] = contents
            # 이미지
            self.remove_html('//div[@class="article-view-contents"]/ul')
            e_b = self.get_by_xpath('//div[@class="article-view-contents"]')
            inner_html = e_b.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                img_e = e_b.find_elements_by_tag_name('img')
                for j, img in enumerate(img_e):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    # cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                    #                                f'{j}.png')
                    # img.screenshot(cmt_img_f)
                    # msg['image_list'].append(f'{j}.png')

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            try:
                # 특정 요소가 로드될 때까지 기다림
                wait = WebDriverWait(self.driver, 10)
                wait.until(
                    EC.presence_of_element_located((By.XPATH, '(//div[@class="m_no_533"])[1]|//div[@class="banner-fd"]')))
            except:
                self.logger.error(f'cannot find ad-popup before screenshot')
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                # self.driver.execute_script('window.scrollTo(0,0)')
                # self.implicitly_wait(after_wait=1)
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    elements = self.driver.find_elements_by_xpath("//ins[@class='adsbygoogle adsbygoogle-noablate']")
                    # 각 요소의 스타일을 "display: none;"로 설정합니다.
                    for element in elements:
                        self.driver.execute_script("arguments[0].style.display = 'none'", element)
                        self.logger.info('광고창 삭제 완료')
                    ad_heads = self.driver.find_elements_by_xpath('(//div[@class="m_no_533"])[1]|//div[@class="banner-fixed"]')
                    for ad_head in ad_heads:
                        self.driver.execute_script("""
                                                                                    var element = arguments[0];
                                                                                    element.parentNode.removeChild(element);
                                                                                    """, ad_head)
                    self.implicitly_wait(after_wait=1)
                    ad_sides = self.driver.find_elements_by_xpath('//div[@class="sticky"]')
                    for ad_side in ad_sides:
                        self.driver.execute_script("""
                                                                                    var element = arguments[0];
                                                                                    element.parentNode.removeChild(element);
                                                                                    """, ad_side)
                    self.implicitly_wait(after_wait=1)
                    headers = self.driver.find_elements_by_xpath('//div[@class="sticky-head"]')
                    for header in headers:
                        self.driver.execute_script("""
                                                                                    var element = arguments[0];
                                                                                    element.parentNode.removeChild(element);
                                                                                    """, header)
                    self.implicitly_wait(after_wait=1)
                    elements = self.driver.find_elements_by_xpath("//ins[@class='adsbygoogle adsbygoogle-noablate']")
                    # 각 요소의 스타일을 "display: none;"로 설정합니다.
                    for element in elements:
                        self.driver.execute_script("arguments[0].style.display = 'none'", element)
                        self.logger.info('광고창 추가 삭제 완료')
                    self.full_screenshot1(msg_capture_f)

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            self.get_cmt(msg)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # 이전 페이지
            # self.driver.back()
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
            # '2021.12.21 21:48'
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

            # 게시글 목록 스크린샷
            self.driver.set_window_size(self.config['params']['kwargs']['width'], 2000)
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))

            self.switch_to_window(0)

            count_a = 0
            while True:
                # 페이지 테이블 구하기
                e_s = self.driver.find_elements_by_xpath('//div[@class="article-list"]/div')
                if not e_s:
                    self.logger.error(f'Cannot find Result!')
                    self.is_done = True
                    break
                e_a = e_s[count_a]

                msg = {
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
                try:
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    # 0) 게시글 카테고리: board_name
                    a = e_a.find_element_by_xpath('./span[@class="category"]/a[last()]')
                    board_name = a.text.strip()
                    msg['board_name'] = board_name
                    # if board_name in ["블라블라", "이직·커리어", "여행·먹방", "직장인 취미생활", "유우머"]:
                    #     msg['board_name'] = board_name
                    # else:
                    #     self.logger.info('pass')
                    #     count_a += 1
                    #     continue
                    # 1) 게시글 주소: article_url
                    e_url = e_a.find_element_by_xpath('./div[@class="tit"]/h3/a')
                    a_url = e_url.get_attribute('href')
                    msg['article_url'] = a_url
                    # 2) 게시글 id : article_id  300143_55268553
                    v = a_url.rpartition('-')[2]
                    # v_a = re.sub(r'[^0-9]', '', v)
                    msg['article_id'] = v
                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, count_a + 1)
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'게시글의 url: {msg["article_url"]}')
                    self.logger.error(f'게시글의 title: {msg["title"]}')
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))
                    raise

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
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
                # bi = self.get_by_xpath('//div[@id="app"]//div/strong[@class="tit_guide"]')
                # # 비공개 게시글
                # if bi:
                #     self.logger.debug('멤버에게만 공개된 게시글 입니다.')
                #     continue
                self.move_to_element(e_a)
                count_a += 1
        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="paginate"]')

            # 다음 페이지로 넘기기 위해 사용하는 플래그
            is_current = False

            # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
            # 따라서 두 가지 종류의 태그를 모두 구해야 함
            # 현재의 게시글이 포함된 페이지는 class가 current이다.
            # 따라서 다음 페이지를 클릭하기 위해 is_current 플래그를 True로 전환하고
            # for 문을 통해 다음 페이지 정보를 추출후
            # 두번 째 if 문에서 클릭을 통해 다음 페이지로 넘어간다.
            for pa in ple.find_elements_by_xpath('.//a | .//strong'):
                if pa.get_attribute('class') == 'current':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
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
        # for cmt in article['comment_list']:
        #     if not ('comment_img' in cmt and cmt['comment_img']):
        #         continue
        #     for k, cmt_url in enumerate(cmt['comment_img_url']):
        #         try:
        #             cmt_img_f = self.get_safe_path(
        #                 self.config['target']['folder'],
        #                 article['article_id'],
        #                 f'{cmt["comment_id"] + "_" + str(k)}.png'
        #             )
        #             urllib.request.urlretrieve(cmt_url, cmt_img_f)
        #         except Exception as err:
        #             self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img_url"]}: {str(err)}')

    # ==========================================================================
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )
        self.save_d(at_js_f, article)
    # ==========================================================================
    def full_screenshot1(self, output_file):
        self.remove_html("//div[@class='ad_md is_web']")
        xpath = '//div[@class="contents"]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)
        xpath = '//div[@class="article hire-ad"]'
        element2 = self.driver.find_element_by_xpath(xpath)
        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size
        location2 = element2.location
        size2 = element2.size

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
    def remove_html(self,xpath):
        try:
            # 로그인
            power_link = self.get_by_xpath(xpath)
            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", power_link)
            # self.driver.execute_script("arguments[0].remove();", article_list)
            # self.driver.execute_script("arguments[0].remove();", btm_area)
            # self.driver.execute_script("arguments[0].remove();", ft)

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass
    # ==========================================================================
    def save(self):
        myLen = len(self.output['article_list'])  # 디버깅
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
    def chrome_option(self):
        try:
            options = webdriver.ChromeOptions()
            if self.config['params']['kwargs']['headless']:
                options.add_argument('--headless')
            options.add_argument("disable-gpu")
            # options.add_argument('--incognito')
            options.add_extension(r'C:\work\chrome_option\ublockorigin.crx')
            # options.add_argument(f'--user-agent={generate_user_agent(device_type="smartphone")}')
            # options.add_argument('--kiosk-printing')
            self.width = self.config['params']['kwargs']['width']
            self.height = self.config['params']['kwargs']['height']
            self.driver.start_session(options.to_capabilities())
            self.driver.get(self.config['params']['kwargs']['url'])
            # 넓이 변경안하면 검색창이 보이지 않아서 검색 에러 발생
            self.driver.set_window_size(self.width, self.height)
            time.sleep(5)
        except Exception as err:
            self.logger.error(f'chrome_option: error: {str(err)}')
            raise

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            self.chrome_option()
            self.search()
            # 페이지 읽어오기
            self.is_done = False
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
        with teamblindSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'teamblind.yaml'
    do_start(config_f=_config_f)
