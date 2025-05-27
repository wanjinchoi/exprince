"""
====================================
 :mod:`community/Youtube`
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
#  * [2024/09/26]
#     - 라이브는 수집 대상이 아니므로 라이브 게시글 스킵(XPath 수정)
#  * [2024/05/08]
#     - article_id에 존재하는 특수문자 제거
#  * [2023/11/08]
#     - 게시글 등록 시간 처리 추가 (초, 주, 월, 년)
#     - 라이브 예정 게시글 스킵
#  * [2023/11/01]
#     - 조회수, 작성 시간 게시글 목록에서 확인하도록 변경
#     - 공감수 XPath 수정
#  * [2023/08/01]
#     - 필터 부분의 xpath 변경
#  * [2023/06/26]
#     - 게시글 작성시간, 조회수, 공감수 xpath 변경
#  * [2023/05/03]
#     - 게시글 본문 더보기 펼치기 선택 후에 본문 수집하도록 수정
#     - 게시글 스크린샷 댓글까지 나오도록 수정
#     - 좋아요, 조회수 xpath 수정
#     - 댓글 수집 로직 수정(댓글은 있는데 댓글수는 0으로 노출되는 케이스가 존재)
#  * [2022/12/14]
#     - 게시글이 없을 때 로그 추가
#  * [2022/11/28]
#     - 댓글 부분의 xpath 변경
#  * [2022/11/21]
#     - 필터 xpath 변경
#     - 공감수  xpath 변경
#  * [2022/10/20]
#     - 쇼츠 xpath 변경
#  * [2022/06/16]
#     - 자막 추출 추가
#  * [2022/06/10]
#     - 1시간 전보다 오래된 데이터가 있을경우 모두 건너뛰도록 설정.
#     - 실시간 스트리밍도 건너뛰도록 설정
#     - 댓글 읽는 속도 개선
#  * [2022/06/08]
#     - 1시간 전으로 필터적용시 12시간전에 작성된 데이터도 섞여있는경우가 있음 해당 게시글은 넘어가도록 설정
#  * [2022/05/25]
#     - 실시간 동영상, 예약된 동영상 create_ts 수정
#  * [2022/04/08]
#     - create_ts 포맷 적용,
#  * [2022/04/06]
#     - 포멧 적용, shorts 추가, 상단바 제거
#  * [2022/01/18]
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
import tarfile
import traceback
import datetime
# from datetime import timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from copy import deepcopy
# from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# 자막추출
from pytube import YouTube
from bs4 import BeautifulSoup
################################################################################


class YoutubeSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'YoutubeSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        self.search_filter = self.config['params']['site']['search_filter']
        # del self.config['params']['site']['search_filter']

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
        self.logger.info(f'Starting Youtube Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e = self.get_by_xpath('//input[@aria-label="검색"]')
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@id="search-icon-legacy"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 게시글 목록 스크린샷
        self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
        s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
        s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture_검색 후' + s_shot[s_shot.rfind('/'):]
        self.driver.find_element_by_tag_name('ytd-app').screenshot(self.get_safe_path(s_shot))

        # 필터
        e = self.get_by_xpath(
            '//div[@id="filter-button"]//div[@class="yt-spec-touch-feedback-shape__fill"]',
            wait_until_valid_text=True)
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 필터 하나만 적용하도록.
        e = self.get_by_xpath(f'//div[@title="{self.search_filter}"]/yt-formatted-string', wait_until_valid_text=True)
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 재수집용
        # e = self.get_by_xpath('//div[@title="업로드 날짜순 정렬"]/yt-formatted-string[@class="style-scope ytd-search-filter-renderer"]', wait_until_valid_text=True)
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def caption_get(self, url):
        yt = YouTube(url)
        if 'a.ko' in yt.captions:
            cp = yt.captions['a.ko']
        elif 'ko' in yt.captions:
            cp = yt.captions['ko']
        elif 'a.en' in yt.captions:
            cp = yt.captions['a.en']
        elif 'en' in yt.captions:
            cp = yt.captions['en']
        else:
            return ''
        cp_str = cp.xml_captions
        cp_str = self.xml2text(cp_str)
        return ' 자막 :' + cp_str

    # ==========================================================================
    @staticmethod
    def xml2text(xmlstr):
        ts = list()
        soup = BeautifulSoup(xmlstr, 'html.parser')
        for p in soup.find_all('p'):
            ts.append(p.text.strip())
        return '\n'.join(ts)

    # ==========================================================================
    def get_recomment(self, msg, re_cmt_e, parent_comment_id):
        try:
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            re_cmt = {
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
            # 대댓글 확인
            re_cmt['parent_comment_id'] = parent_comment_id
            re_cmt['is_reply'] = True
            # 댓글 작성 시간
            e = re_cmt_e.find_element_by_xpath('.//yt-formatted-string[@class="published-time-text style-scope ytd-comment-renderer"]/a')
            et = e.text
            yyy, ooo, www, ddd, hhh, mmm, sss = 0, 0, 0, 0, 0, 0, 0
            re_cmt['create_ts'] = ""
            if et.find('초') > 0:
                ss = re.sub(r'[^0-9]', '', et)
                sss = int(ss)
            elif et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            elif et.find('일') > 0:
                dd = re.sub(r'[^0-9]', '', et)
                ddd = int(dd)
            elif et.find('주') > 0:
                ww = re.sub(r'[^0-9]', '', et)
                www = int(ww)
            elif et.find('개월') > 0:
                oo = re.sub(r'[^0-9]', '', et)
                ooo = int(oo)
            elif et.find('년') > 0:
                yy = re.sub(r'[^0-9]', '', et)
                yyy = int(yy)
            if yyy + ooo + www + ddd + hhh + mmm + sss != 0:
                d = datetime.datetime.now() - relativedelta(
                    years=yyy, months=ooo, weeks=www, days=ddd, hours=hhh, minutes=mmm, seconds=sss)
                re_cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')

            re_cmt['create_ts'] = datetime.datetime.strptime(re_cmt['create_ts'], '%Y.%m.%d %H:%M:%S').strftime(
                '%Y.%m.%d %H:%M:%S')
            # 댓글 아이디
            e = re_cmt_e.find_element_by_xpath('.//a[@id="author-text"]')
            try:
                ea = e.get_attribute('href')
                b = ea.partition('channel')[1]
                c = ea.partition('/channel/')[2]
                re_cmt['comment_id'] = b + '_' + c + '_' + str(len(msg['comment_list']))
            except:
                ...
                # 탈퇴, 규제된 회원은 id가 없음
            self.move_to_element(e)

            # 댓글 nickname
            re_cmt['nickname'] = ""
            e = re_cmt_e.find_element_by_xpath('.//a[@id="author-text"]/span')
            re_cmt['nickname'] = e.text.strip()
            if re_cmt['nickname'] == '':
                e = re_cmt_e.find_element_by_xpath(
                    './/div[@id="text-container"]/yt-formatted-string[@ellipsis-truncate]')
                re_cmt['nickname'] = e.text.strip()

            # 댓글 내용 # 더 보기 만드는 거 만들기
            e_t = re_cmt_e.find_element_by_xpath(
                './/ytd-expander[@id="expander"]//yt-formatted-string[@id="content-text"]')
            re_cmt['contents'] = e_t.get_attribute('innerText')

            # 댓글 좋아요
            e = re_cmt_e.find_element_by_xpath('.//span[@id="vote-count-middle"]')
            try:
                e_l = e.get_attribute('aria-label').partition(' ')[2]
                re_cmt['like'] = self.get_num_from_str(e_l)
            except:
                re_cmt['like'] = 0

            # 댓글 목록에 추가
            msg['comment_list'].append(re_cmt)

        except:
            ...

    # ==========================================================================
    def get_comment(self, msg, cmt_e):
        try:
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            parent_comment_id = ''
            cmt = {
                'comment_id': None,
                'is_reply': False,
                'parent_comment_id': parent_comment_id,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': [],
            }
            # 댓글 작성 시간
            e = cmt_e.find_element_by_xpath('.//yt-formatted-string[@class="published-time-text style-scope ytd-comment-renderer"]/a')
            et = e.text
            yyy, ooo, www, ddd, hhh, mmm, sss = 0, 0, 0, 0, 0, 0, 0
            cmt['create_ts'] = ""
            if et.find('초') > 0:
                ss = re.sub(r'[^0-9]', '', et)
                sss = int(ss)
            elif et.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', et)
                mmm = int(mm)
            elif et.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', et)
                hhh = int(hh)
            elif et.find('일') > 0:
                dd = re.sub(r'[^0-9]', '', et)
                ddd = int(dd)
            elif et.find('주') > 0:
                ww = re.sub(r'[^0-9]', '', et)
                www = int(ww)
            elif et.find('개월') > 0:
                oo = re.sub(r'[^0-9]', '', et)
                ooo = int(oo)
            elif et.find('년') > 0:
                yy = re.sub(r'[^0-9]', '', et)
                yyy = int(yy)
            if yyy+ooo+www+ddd+hhh+mmm+sss != 0:
                d = datetime.datetime.now() - relativedelta(
                    years=yyy, months=ooo, weeks=www, days=ddd, hours=hhh, minutes=mmm, seconds=sss)
                cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')

            cmt['create_ts'] = datetime.datetime.strptime(cmt['create_ts'], '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
            # 댓글 아이디
            e = cmt_e.find_element_by_xpath('.//a[@id="author-text"]')
            try:
                ea = e.get_attribute('href')
                b = ea.partition('channel')[1]
                c = ea.partition('/channel/')[2]
                cmt['comment_id'] = b + '_' + c + '_' + str(len(msg['comment_list']))
            except:
                ...
                # 탈퇴, 규제된 회원은 id가 없음

            # 대댓글
            parent_comment_id = cmt['comment_id']

            # 댓글 nickname
            cmt['nickname'] = ""
            e = cmt_e.find_element_by_xpath('.//a[@id="author-text"]/span')
            cmt['nickname'] = e.text.strip()
            # 작성자가 댓글을 달 경우 표식이 생겨서 위에서 닉네임을 못 찾기에 아래에서 찾아준다
            if cmt['nickname'] == '':
                e = cmt_e.find_element_by_xpath(
                    './/div[@id="text-container"]/yt-formatted-string[@ellipsis-truncate]')
                cmt['nickname'] = e.text.strip()

            # 댓글 내용 # 더 보기 만드는 거 만들기
            e_t = cmt_e.find_element_by_xpath(
                './/ytd-expander[@id="expander"]//yt-formatted-string[@id="content-text"]')
            cmt['contents'] = e_t.get_attribute('innerText')

            # 댓글 좋아요
            e = cmt_e.find_element_by_xpath('.//span[@id="vote-count-middle"]')
            try:
                e_l = e.get_attribute('aria-label').partition(' ')[2]
                cmt['like'] = self.get_num_from_str(e_l)
            except:
                cmt['like'] = 0

            # 댓글 목록에 추가
            msg['comment_list'].append(cmt)
            self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')

            # 대댓글 유무 확인
            # e_a = self.get_by_xpath('//ytd-comments[@id="comments"]')
            e_rb = cmt_e.find_element_by_xpath('.//div[@id="replies"]')
            outerhtml = e_rb.get_attribute('hidden')
            if outerhtml is None:
                self.safe_click(e_rb.find_element_by_xpath('.//div[@class="more-button style-scope ytd-comment-replies-renderer"]'))
                while True:
                    e_re_tb = cmt_e.find_element_by_xpath('.//div[@id="expander-contents"]')
                    e_re_ytd = e_re_tb.find_elements_by_xpath('./div/ytd-comment-renderer')
                    for e_re_li in e_re_ytd:
                        self.get_recomment(msg, e_re_li, parent_comment_id)
                        self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                        # self.driver.execute_script("""
                        #                     var element = arguments[0];
                        #                     element.parentNode.removeChild(element);
                        #                     """, e_re_li)
                        if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                            self.is_done = True
                            break
                    # 여기 고치기
                    # 대댓글 맨 밑에
                    e_re_stop = e_re_ytd.find_element_by_xpath('.//div[@class="cont-button style-scope ytd-comment-replies-renderer"]')
                    if e_re_stop > 0:
                        break

        except:
            ...

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
    def get_view_count(self, view_count):

        if view_count.find('천') > 0:
            v_e = view_count.replace('천', '000')
            v_count = re.sub(r'[^\d]', '', v_e)
        elif view_count.find('만') > 0:
            v_e = view_count.replace('만', '0000')
            v_count = re.sub(r'[^\d]', '', v_e)
        else:
            v_count = re.sub(r'[^\d]', '', view_count)

        return v_count

    # ==========================================================================
    def get_create_ts(self, create_ts):
        if create_ts.find('초') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(seconds=int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('분') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(minutes=int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('시') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(hours=int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('일') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(days=int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('주') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(weeks=int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('월') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(days=30 * int(re.sub(r'[^0-9]', '', create_ts)))
        elif create_ts.find('년') > 0:
            create_ts = datetime.datetime.now() - datetime.timedelta(days=365 * int(re.sub(r'[^0-9]', '', create_ts)))
        else:
            create_ts = datetime.datetime.strptime(create_ts.replace(' ', '')[:-1] + ' 00:00:00', '%Y.%m.%d %H:%M:%S')

        return create_ts.strftime('%Y.%m.%d %H:%M:%S')

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.switch_to_window(1)
            # 상단바 제거
            e = self.get_by_xpath('//div[@id="masthead-container"]', timeout=3, wait_until_valid_text=True)
            self.driver.execute_script("""
                                var element = arguments[0];
                                element.parentNode.removeChild(element);
                                """, e)
            # 영상 멈춤
            self.send_keys(self.driver.find_element_by_xpath('//body'), 'k')
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            e_ab = self.get_by_xpath('//div[@id="columns"]//div[@id="primary"]', timeout=1)
            # 작성 시간
            # e = e_ab.find_element_by_xpath('.//div[@id="info-container"]/yt-formatted-string')
            # e = e_ab.find_element_by_xpath('.//div[@id="info-container"]/div[@id="date-text"]')
            # # aria-label 속성에 있는 값 가져옴
            # create_ts = e.get_attribute("aria-label")
            # msg['create_ts'] = self.get_create_ts(create_ts)

            #  조회수
            # '조회수 없음' 으로 뜨는 경우 o
            # e = e_ab.find_element_by_xpath('.//span[@class="style-scope yt-formatted-string bold"][1]')
            # e_v = e.text.partition(' ')[2].partition('회')[0].strip()
            # v_e = e_ab.find_element_by_xpath('.//div[@id="info-container"]/div[@id="view-count"]')
            # v_ea = v_e.get_attribute("aria-label")
            # view = v_ea.split('  ')[0]
            # try:
            #     e_vv = re.sub(r'[^0-9]', '', view)
            #     msg['view_count'] = int(e_vv)
            # except:
            #     msg['view_count'] = 0
            # 게시글 공감수
            # 게시글 공감수 xpath 못찾음
            try:
                e = self.get_by_xpath('//button[@class="yt-spec-button-shape-next yt-spec-button-shape-next--tonal yt-spec-button-shape-next--mono yt-spec-button-shape-next--size-m yt-spec-button-shape-next--icon-leading yt-spec-button-shape-next--segmented-start"]')
                self.move_to_element(e)
                e_l = e.get_attribute('aria-label')
                like_e = re.sub(r'[^\d]', '', e_l)
                msg['like'] = int(like_e)
            except:
                msg['like'] = 0
            # self.move_to_element(e)

            # 더보기
            for more in self.driver.find_elements_by_xpath(
                    '//div[@id="description-inner"]//ytd-text-inline-expander/tp-yt-paper-button[@role="button"][1]'):
                self.safe_click(more)
                self.implicitly_wait()

            # 게시글 내용
            try:
                e = e_ab.find_element_by_xpath('.//div[@id="description-inner"]//ytd-text-inline-expander/yt-attributed-string')
                # msg['contents'] = e.get_attribute('innerText') + self.caption_get(msg['article_url'])
                msg['contents'] = e.text.strip()
            except:
                msg['contents'] = ''

            # 게시글 댓글 수
            # 댓글 사용을 막을 수도 있음
            try:
                e = e_ab.find_element_by_xpath('.//h2[@id="count"]/yt-formatted-string/span[2]')
                msg['num_comments'] = int(e.text.replace(',', ''))
            except:
                msg['num_comments'] = 0

            # 댓글이 없는 경우
            if msg['num_comments'] == 0:
                try:
                    e = self.get_by_xpath('//ytd-comments[@id="comments"]//ytd-comment-thread-renderer')
                    # 댓글 하나씩 읽기
                    msg['comment_list'] = []
                    e_a = self.get_by_xpath('//ytd-comments[@id="comments"]')
                    len_comments = 0
                    try:
                        # 댓글 정렬 기준
                        e = e_ab.find_element_by_xpath('.//yt-icon[@id="label-icon"]')
                        self.safe_click(e)
                        self.implicitly_wait(after_wait=1)
                        e_bu = e_ab.find_element_by_xpath('.//tp-yt-paper-listbox[@id="menu"]/a[2]')
                        self.safe_click(e_bu)
                        self.implicitly_wait(after_wait=1)
                        while True:
                            comments = e_a.find_elements_by_xpath('.//ytd-comment-thread-renderer')
                            # 무한스크롤이기때문에 마지막글인지 체크.
                            if len_comments == len(comments):
                                break
                            for i, cmt in enumerate(comments):
                                if i < len_comments:
                                    continue
                                self.move_to_element(cmt)
                                self.get_comment(msg, cmt)
                                # element 삭제하는 부분
                                # self.driver.execute_script("""
                                # var element = arguments[0];
                                # element.parentNode.removeChild(element);
                                # """, cmt)
                                if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                                    self.is_done = True
                                    break
                            len_comments = len(comments)
                        msg['num_comments'] = int(len_comments)
                        if msg['num_comments'] != len(msg['comment_list']):
                            msg['num_comments'] = len(msg['comment_list'])
                    except:
                        msg['num_comments'] = 0
                        return
                except:
                    return
            else:
                # 댓글 하나씩 읽기
                msg['comment_list'] = []
                e_a = self.get_by_xpath('//ytd-comments[@id="comments"]')
                len_comments = 0
                try:
                    # 댓글 정렬 기준
                    e = e_ab.find_element_by_xpath('.//yt-icon[@id="label-icon"]')
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=1)
                    e_bu = e_ab.find_element_by_xpath('.//tp-yt-paper-listbox[@id="menu"]/a[2]')
                    self.safe_click(e_bu)
                    self.implicitly_wait(after_wait=1)
                    while True:
                        comments = e_a.find_elements_by_xpath('.//ytd-comment-thread-renderer')
                        # 무한스크롤이기때문에 마지막글인지 체크.
                        if len_comments == len(comments):
                            break
                        for i, cmt in enumerate(comments):
                            if i < len_comments:
                                continue
                            self.move_to_element(cmt)
                            self.get_comment(msg, cmt)
                            # element 삭제하는 부분
                            # self.driver.execute_script("""
                            # var element = arguments[0];
                            # element.parentNode.removeChild(element);
                            # """, cmt)
                            if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                                self.is_done = True
                                break
                        len_comments = len(comments)
                    if msg['num_comments'] != len(msg['comment_list']):
                        msg['num_comments'] = len(msg['comment_list'])
                except:
                    msg['num_comments'] = 0
                    return

        except Exception as err:
            raise
        finally:
            # 게시글 캡처
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.full_screenshot(msg_capture_f)
            # 이전 페이지
            # self.driver.back()
            self.driver.close()
            try:
                self.switch_to_main_window()
            except:
                # selenium.common.exceptions.WebDriverException: Message: unknown error:
                # cannot determine loading status
                pass

    # ==========================================================================
    def get_article_shorts(self, msg, ndx):
        try:
            self.switch_to_window(1)
            # 상단바 제거
            e = self.get_by_xpath('//div[@id="masthead-container"]', timeout=3, wait_until_valid_text=True)
            self.driver.execute_script("""
                                var element = arguments[0];
                                element.parentNode.removeChild(element);
                                """, e)
            # 영상 멈춤
            self.send_keys(self.driver.find_element_by_xpath('//body'), 'k')
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.full_screenshot(msg_capture_f)

            # # 작성 시간과 조회수 가져오기 (가끔 가비지 데이터가 있는 경우가 있어서 두번 누르도록수정. 두개 랜덤하게 동작됨.)
            # self.implicitly_wait(after_wait=3)
            # es = self.driver.find_elements_by_xpath('(//div[@id="menu-button"]//yt-button-shape)[1]')
            # for e in es:
            #     try:
            #         self.safe_click(e)
            #         self.implicitly_wait(after_wait=1)
            #         break
            #     except:
            #         continue
            #
            # e = self.get_by_xpath('//div[@id="contentWrapper"]//ytd-menu-service-item-renderer',
            #                       wait_until_valid_text=True)
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)
            # # 작성 시간
            # e = self.get_by_xpath('//div[@id="factoids"]/ytd-factoid-renderer[3]/div', wait_until_valid_text=True)
            # e_i = e.get_attribute('aria-label')
            # create_ts = e_i.replace(' ', '')[:-1] + ' 00:00:00'
            # msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
            #
            # #  조회수
            # e = self.get_by_xpath('//div[@id="factoids"]/ytd-factoid-renderer[2]/div', wait_until_valid_text=True)
            # e_a = e.get_attribute('aria-label')
            # e_b = e_a.split(' ')[1]
            # e_v = re.sub(r'[^0-9]', '', e_b)
            # msg['view_count'] = int(e_v)
            # # 내용
            # e = self.get_by_xpath('//ytd-engagement-panel-section-list-renderer//div[@id="shorts-title"]//yt-formatted-string',
            #                       timeout=1)
            # msg['contents'] = e.text.strip()
            # # 조회수와 작성시간 페이지 나가기
            # # e = self.get_by_xpath('//ytd-popup-container/tp-yt-paper-dialog//button[@aria-label="닫기"]|//ytd-popup-container/tp-yt-paper-dialog//button[@aria-label="닫기"]'
            # #                       '|//ytd-button-renderer/yt-button-shape/button', cond='element_to_be_clickable')
            # # self.safe_click(e)
            # # self.implicitly_wait(after_wait=1)

            # 게시글 공감수
            try:
                e = self.driver.find_element_by_xpath('(//div[@id="like-button"]//button[@aria-label])[1]')
                e_l = e.get_attribute('aria-label')
                s = e_l.partition('사용자 ')[2].partition('명이')[0]
                msg['like'] = self.get_num_from_str(s)
            except:
                msg['like'] = 0

            # 게시글 내용 shorts는 내용이 없음.
            # e = e_ab.find_element_by_xpath('.//div[@id="description"]/yt-formatted-string')
            # msg['comments'] = e.get_attribute('innerText')

            # 게시글 댓글 수
            # 댓글 사용을 막을 수도 있음
            try:
                e = self.driver.find_element_by_xpath('//div[@id="comments-button"]')
                msg['num_comments'] = int(re.sub(r'[^0-9]', '', e.text))
            except:
                msg['num_comments'] = 0

            # 댓글이 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            # 댓글 / 정렬 최신순
            e = self.get_by_xpath('//div[@id="comments-button"]', wait_until_valid_text=True)
            self.safe_click(e)
            e = self.get_by_xpath('//tp-yt-paper-button[@aria-label="댓글 정렬"]', timeout=3, wait_until_valid_text=True)
            self.safe_click(e)
            e = self.get_by_xpath('//div[@id="contentWrapper"]/div/tp-yt-paper-listbox/a[2]',
                                  wait_until_valid_text=True)
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 댓글 하나씩 읽기
            e_a = self.get_by_xpath('//ytd-item-section-renderer[@id="sections"]/div[@id="contents"]')
            len_comments = 0
            while True:
                comments = e_a.find_elements_by_xpath('./ytd-comment-thread-renderer')
                # 무한스크롤이기때문에 마지막글인지 체크.
                if len_comments == len(comments):
                    break
                for i, cmt in enumerate(comments):
                    if i < len_comments:
                        continue
                    self.move_to_element(cmt)
                    self.get_comment(msg, cmt)
                    # element 삭제하는 부분
                    # self.driver.execute_script("""
                    # var element = arguments[0];
                    # element.parentNode.removeChild(element);
                    # """, cmt)
                    if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                        self.is_done = True
                        break
                len_comments = len(comments)

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            # self.driver.back()
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
                e_s = self.driver.find_elements_by_xpath('//ytd-video-renderer|//yt-formatted-string[@id="message"]')
                if not e_s:
                    self.logger.error(f'게시글 없습니다!')
                    self.is_done = True
                    return
                e_a = e_s[count_a]
                if e_a.text == '결과가 더 이상 없습니다.':
                    self.is_done = True
                    break
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
                    # live = e_a.find_elements_by_xpath('.//div[@class="badge  badge-style-type-live-now-alternate style-scope ytd-badge-supported-renderer style-scope ytd-badge-supported-renderer"]')
                    # if len(live) != 0:
                    #     self.move_to_element(e_a)
                    #     count_a += 1
                    #     continue
                    if self.search_filter == '지난 1시간 검색':
                        time_check = e_a.find_element_by_xpath('.//div[@id="metadata-line"]')
                        if any(time_format in time_check.text for time_format in ['일 전', '시간 전']):
                            self.move_to_element(e_a)
                            count_a += 1
                            continue
                    # 1) 게시글 id : article_id  300143_55268553
                    e_url = e_a.find_element_by_xpath('.//a[@id="video-title"]')
                    a_url = e_url.get_attribute('href')
                    v = a_url.rpartition('/')[2]
                    if '?v=' in v:
                        v_a = a_url.partition('?v=')[2]
                        article_id_e = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", v_a)
                        msg['article_id'] = article_id_e
                    else:
                        article_id_e = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", v)
                        msg['article_id'] = article_id_e
                    # 1) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 2) 제목: title
                    e = e_a.find_element_by_xpath('.//a[@id="video-title"]')
                    msg['title'] = e.text.strip()
                    # 라이브 게시글 확인. 수집 로그를 위해서 후순위에서 라이브 스킵
                    live = e_a.find_elements_by_xpath('.//div[@class="badge  badge-style-type-live-now-alternate style-scope ytd-badge-supported-renderer style-scope ytd-badge-supported-renderer"]')
                    if len(live) != 0:
                        self.move_to_element(e_a)
                        count_a += 1
                        self.logger.info(f'live 게시글입니다. url[{msg["article_url"]}], 제목[{msg["title"]}]')
                        continue
                    # 3) 작성자
                    e = e_a.find_element_by_xpath('.//div[@id="channel-info"]//div/div[@class="style-scope ytd-channel-name"]')
                    msg['author'] = e.text.strip()
                    # 4) 조회수
                    e = e_a.find_element_by_xpath('.//div[@id="metadata-line"]//span[1]')
                    v_e = e.text.strip()
                    if '예정일' in v_e:
                        self.move_to_element(e_a)
                        count_a += 1
                        continue
                    if v_e == '조회수 없음':
                        msg['view_count'] = 0
                    else:
                        msg['view_count'] = int(self.get_view_count(v_e))

                    # 5) 등록 시간
                    e = e_a.find_element_by_xpath('.//div[@id="metadata-line"]//span[2]')
                    create_ts = e.text.strip()
                    msg['create_ts'] = self.get_create_ts(create_ts)

                    # self.safe_click(e_url)
                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    if a_url.find('/shorts/') > 0:
                        v_ae = a_url.rpartition('.com/')[2].replace('/', '_')
                        article_id_e = re.sub(r"[^\uAC00-\uD7A30-9a-zA-Z\s]", "", v_ae)
                        msg['article_id'] = article_id_e
                        self.get_article_shorts(msg, count_a + 1)
                    else:
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
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))
                # 지난 1시간으로 검색해도 1시간전에 작성된 게시글이 검색되는 경우가 있음.
                if msg['create_ts'] == "한시간 이전글":
                    self.move_to_element(e_a)
                    count_a += 1
                    continue
                if self.search_filter != '지난 1시간 검색':
                    if self.stop_article_older_than(msg):
                        if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                            shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                        if self.search_filter == '지난 1시간 검색':
                            continue
                        self.is_done = True  # 동시성 런타임
                        break

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
                self.move_to_element(e_a)
                count_a += 1

        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def get_num_from_str(self, s):
        # s = 1.5만개 or 1.4천회
        if s == '':
            s = '1'
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
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
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
    with YoutubeSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
def main(**kwargs):
    with YoutubeSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'youtube.yaml'
    do_start(config_f=_config_f)
