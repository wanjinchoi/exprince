"""
====================================
 :mod:`hani`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for hani (한겨레)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An, Jerry Chae
#
# Change Log
# --------
#
#  * [2023/06/07]
#     - 삭제된 댓글 후처리에서 걸러지지 않도록 수정
#  * [2023/05/04]
#     - 키워드 검색 후 게시글 미노출일 경우 리프레쉬
#  * [2023/04/17]
#     - board_name 필드에 수집영역 입력
#  * [2023/04/10]
#     - 스크린샷 수정(댓글까지 스크린샷 범위에 포함)
#  * [2023/03/30]
#     - 댓글부분의 작성일에 방금전, 한시간전이 존재하여 해당 부분 수정
#  * [2023/03/13]
#     - 500 server error 발생 시 리프레쉬
#  * [2023/02/27]
#     - 키워드 검색 후 기다리는 시간 추가
#  * [2023/02/15]
#     - 댓글 xpath 수정
#  * [2023/02/13]
#     - 게시글이 없거나 최신 게시글 title log 추가
#  * [2023/01/30]
#     - 사이트 UI 변경
#  * [2022/11/28]
#     - 사이트 UI 변경
#  * [2022/04/13]
#     - 댓글 포맷 미흡한 부분 수정. create_ts 변경
#  * [2022/03/05]
#     - get_cmt_reply() 코드 수정
#     - save_image() 불필요한 코드 일부 제거


import re
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
from datetime import timedelta
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################
class HaniSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'HaniSearch.log'),
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
        self.cmt_done = False
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
        self.logger.info(f'Starting Hani Crawling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_cmt_reply(self, msg):

        e = self.get_by_xpath('//*[@id="lv-container"]')
        self.move_to_element(e)

        # 댓글은 iframe 내부에 존재
        self.switch_to_iframe('//iframe[@title="라이브리 - 댓글영역"]')

        # iframe 내부로 들어왔기에 다시 기준점을 설정
        e = self.get_by_xpath('//div[@id="container"]')

        se = e.find_element_by_xpath('.//div[@class="reply-count"]')
        cmt_num = se.find_element_by_xpath('.//span[@class="count-text"]')
        # 댓글이 없으면 다음 게시글로 돌아간다
        if cmt_num.text.strip() == '':
            msg['num_comments'] = 0
            # iframe 다시 전환
            self.driver.switch_to.default_content()
            self.cmt_done = True
            return
        else:
            msg['num_comments'] = int(cmt_num.text.strip())

        self.move_to_element(se)

        # '댓글 펼쳐보기' 혹은 ' N개 더보기'를 클릭하면 cmt_list 항목 수가 바뀜
        cmt_list = e.find_elements_by_xpath('.//div[@id="list"]/div')
        while len(cmt_list) != 1: # 첫 번째 : 댓글이 없는 경우를 제외시킴

            # 두 번째 : 펼쳐야 하는 경우가 없는 경우는 빠져 나가기
            fold_flag = False
            for i, cmt_e in enumerate(cmt_list):
                if cmt_e.get_attribute('class') == 'list-reduce-wrapper' \
                        or cmt_e.get_attribute('class') == 'more-wrapper':
                    fold_flag = True

            # while 문 빠져나가기
            if fold_flag == False:
                break

            # 세 번째 : 펼쳐야 하는 경우
            for i, cmt_e in enumerate(cmt_list):
                self.move_to_element(cmt_e)
                # '댓글 펼쳐보기' (접혀있는 한 개의 댓글 내용과 x개의 답글 펼치기 + N개의 대댓글(답글) 펼치기 )
                if cmt_e.get_attribute('class') == 'list-reduce-wrapper'\
                    or cmt_e.get_attribute('class') == 'more-wrapper':
                    self.safe_click(cmt_e)
                    self.implicitly_wait(after_wait=1)
                    break

            cmt_list = e.find_elements_by_xpath('.//div[@id="list"]/div')

        # 댓글 처리
        # 댓글이 달린 경우 마지막 댓글 리스트 항목은 데이타가 아닌 메세지이므로 사전에 제거
        cmt_list = e.find_elements_by_xpath('.//div[@id="list"]/div')
        if '모든 댓글을 읽으셨습니다.' in cmt_list[-1].text:
            del cmt_list[-1]

        cmt_count = 0
        for i, cmt_e in enumerate(cmt_list):  # 확보된 댓글 리스트를 하나씩 처리하기

            if cmt_e.text.strip() == '':
                break

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
            self.move_to_element(cmt_e)
            try:
                cmt_top, cmt_bottom = cmt_e.find_elements_by_xpath('./div')
            except:
                pass
            else:
                # 삭제된 댓글의 경우 특별 처리
                if cmt_e.get_attribute('class') == 'reply-wrapper reply-delete-wrapper' or \
                        cmt_e.get_attribute('class') == 'reply-wrapper reply-blind-wrapper':

                    cmt['comment_id'] = cmt_e.get_attribute('data-seq').strip()
                    cmt['is_reply'] = False
                    cmt['parent_comment_id'] = ''
                    cmt['create_ts'] = '0000.00.00 00:00:00'
                    cmt['nickname'] = '삭제된 댓글입니다.'
                    cmt['contents'] = '삭제된 댓글 입니다.'

                    up_count = cmt_bottom.find_element_by_class_name('good-count')
                    down_count = cmt_bottom.find_element_by_class_name('bad-count')
                    #삭제된 댓글은 좋아요 안가져와짐
                    cmt['like'] = 0
                    cmt['dislike'] = 0

                    cmt['comment_img'] = []
                    cmt['comment_img_url'] = []

                    # 댓글은 삭제되었지만 대댓글(답글)은 존재하는 경우가 있음
                    try:
                        reply_num = cmt_bottom.find_element_by_xpath(
                            './/button[@class="reply-comment-btn"]/span[2]')
                    except:
                        pass
                    else:
                        if reply_num.text.strip() == '':
                            cmt_num_replys = '0'
                        else:
                            cmt_num_replys = reply_num.text.strip()
                else:
                    nickname = cmt_top.find_element_by_xpath('.//li[@class="writer-name"]')
                    create_time = cmt_top.find_element_by_xpath('.//span[@class="modify-time"]')
                    contents = cmt_bottom.find_element_by_xpath('.//div[@class="reply-content"]')

                    # 댓글 id
                    cmt['parent_comment_id'] = ''
                    cmt['comment_id'] = cmt_e.get_attribute('data-seq').strip()
                    cmt['is_reply'] = False

                    parent_comment_id = cmt['comment_id']

                    # 닉네임, 작성 일시, 내용
                    # 작성 일시의 경우 24시간이 지나지 않으면 'xx 시간전'으로 표기되어 다음 방법을 사용함)
                    when = create_time.text.strip()
                    ddd, hhh, mmm = 0, 0, 0
                    # 38분 전
                    if when == '방금 전':
                        mmm = int(1)
                    elif when.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', when)
                        mmm = int(mm)
                    elif when == '한 시간 전':
                        hhh = int(1)
                    # 5시간 전
                    elif when.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', when)
                        hhh = int(hh)
                    else:
                        cmt['create_ts'] = datetime.datetime.strptime(when, '%Y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    if not cmt['create_ts']:
                        d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                        cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                    cmt['nickname'] = nickname.text.strip()
                    cmt['contents'] = contents.text.strip()

                    try:
                        reply_num = cmt_bottom.find_element_by_xpath('.//button[@class="reply-comment-btn"]/span[2]')
                    except:
                        pass
                    else:
                        if reply_num.text.strip() == '':
                            cmt_num_replys = '0'
                        else:
                            cmt_num_replys = reply_num.text.strip()

                    up_count = cmt_bottom.find_element_by_class_name('good-count')
                    down_count = cmt_bottom.find_element_by_class_name('bad-count')
                    cmt['like'] = int(up_count.text.strip())
                    cmt['dislike'] = int(down_count.text.strip())

                    cmt['comment_img'] = []
                    cmt['comment_img_url'] = []
                    inner_html = cmt_e.get_attribute('innerHTML') # 이미지 추출용
                    if inner_html.find('attach-multi-btn') > 0 or inner_html.find('attach-image-btn') > 0:
                        cmt_img_list = cmt_bottom.find_elements_by_xpath('.//button[@class="attach-multi-btn"] \
                                                                        | .//button[@class="attach-image-btn"]')
                        for x, img in enumerate(cmt_img_list):
                            img_src = img.find_element_by_xpath('./span | ./img')
                            cmt['comment_img'].append(f'{cmt["comment_id"]}_{x}.png')
                            cmt['comment_img_url'].append(img_src.get_attribute('data-src'))
                cmt_count += 1
                self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{cmt_count}]')
                msg['comment_list'].append(cmt)

            # 답글 부분
            # 답글 여부 확인
            if cmt_num_replys == '0':
                continue
            else:
                # 존재하는 대댓글(답글) 처리
                reply_module= cmt_bottom.find_element_by_xpath('.//div[@class="child-reply"]')
                reply_list = reply_module.find_elements_by_xpath('.//div[@class="reply-wrapper"]')
                for j, reply_e in enumerate(reply_list):

                    self.move_to_element(reply_e)
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
                    try:
                        reply_top, reply_bottom = reply_e.find_elements_by_xpath('./div')
                        nickname = reply_top.find_element_by_xpath('.//li[@class="writer-name"]')
                        create_ts = reply_top.find_element_by_xpath('.//span[@class="modify-time"]')
                        contents = reply_bottom.find_element_by_xpath('.//div[@class="reply-content"]')
                    except:
                        pass
                    else:
                        # 닉네임, 작성 일시, 내용, id
                        # 작성 일시의 경우 24시간이 지나지 않으면 'xx 시간전'으로 표기되어 다음 방법을 사용함)
                        reply['comment_id'] = reply_e.get_attribute('data-seq').strip()
                        reply['is_reply'] = True
                        reply['parent_comment_id'] = parent_comment_id
                        when = create_ts.text.strip()
                        ddd, hhh, mmm = 0, 0, 0
                        if when == '방금 전':
                            mmm = int(1)
                        # 38분 전
                        elif when.find('분') > 0:
                            mm = re.sub(r'[^0-9]', '', when)
                            mmm = int(mm)
                        elif when == '한 시간 전':
                            hhh = int(1)
                        # 5시간 전
                        elif when.find('시간') > 0:
                            hh = re.sub(r'[^0-9]', '', when)
                            hhh = int(hh)
                        else:
                            reply['create_ts'] = datetime.datetime.strptime(when, '%Y.%m.%d %H:%M').strftime(
                                '%Y.%m.%d %H:%M:%S')
                        if not reply['create_ts']:
                            d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                            reply['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                        reply['nickname'] = nickname.text.strip()
                        reply['contents'] = contents.text.strip()

                        up_count = cmt_bottom.find_element_by_class_name('good-count')
                        down_count = cmt_bottom.find_element_by_class_name('bad-count')
                        reply['like'] = int(up_count.text.strip())
                        reply['dislike'] = int(down_count.text.strip())

                        reply['comment_img'] = []
                        reply['comment_img_url'] = []
                        inner_html = reply_bottom.get_attribute('innerHTML')  # 이미지 추출용
                        if inner_html.find('attach-multi-btn') > 0 or inner_html.find('attach-image-btn') > 0:
                            reply_img_list = reply_bottom.find_elements_by_xpath('.//button[@class="attach-multi-btn"] \
                                                                            | .//button[@class="attach-image-btn"]')
                            for x, img in enumerate(reply_img_list):
                                img_src = img.find_element_by_xpath('./span | ./img')
                                reply['comment_img'].append(f'{reply["comment_id"]}_{x}.png')
                                reply['comment_img_url'].append(img_src.get_attribute('data-src'))
                    cmt_count += 1
                    self.logger.info(f'\t\t   대댓글 [{msg["num_comments"]}/{cmt_count}]')
                    msg['comment_list'].append(reply)
        self.cmt_done = True
        self.switch_from_iframe()
        if len(msg['comment_list']) != 1:
            del msg['comment_list'][0]
        return

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.implicitly_wait(after_wait=1)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            e = self.get_by_xpath('//div[@class="article-head"]')
            # 수집 영역
            try:
                sb = e.find_element_by_xpath('.//strong/a')
                msg['board_name'] = sb.text.strip()
            except:
                msg['board_name'] = ''

            # 작성자(기자 혹은 기관) : 간혹 없는 경우 발생
            try:
                se = e.find_element_by_xpath('.//div[@class="kiza-info"]/div[@class="name"]')
            except:
                msg['author'] = ''
            else:
                author = se.text.strip().split('기자')[0]
                msg['author'] = author

            # # 등록일
            # se = e.find_element_by_xpath('./p[@class="date-time"]/span[1]')
            # create_ts = re.match('등록 :(\d+-\d+-\d+ \d+:\d+)', se.text.strip()).group(1)
            # msg['create_ts'] = create_ts.replace('-', '.') + ":00"

            # 내용 (= 부제목 + 내용)
            try:
                article_subtitle = self.get_by_xpath('//div[@class="article-text"]//div[@class="subtitle"]')
                article_body = self.get_by_xpath('//div[@class="article-text"]//div[@class="text"]')
            except:
                msg['contents'] = ''
            else:
                msg['contents'] = article_subtitle.text.strip() + "\n" +article_body.text.strip()

            # 본문 안의 이미지 주소 가져오기
            e = self.get_by_xpath('//div[@class="article-text"]')
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = e.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = e.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    msg['image_list'].append(f'{x}.png')
                    msg['image_url_list'].append(img_src_url)

            # 댓글 저장
            # msg['comment_list'] = []
            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt_reply(msg)
                if self.cmt_done:
                    break

        except Exception as err:
            raise
        finally:
            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                self.driver.execute_script("window.scrollTo(0, -(document.body.scrollHeight))")
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')

                self._screenshot(msg_capture_f)

            # self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//div[@class="search-list section-list-area"]')
            # e_a = e.find_elements_by_xpath('.//h3[@class="title"]//span//em')
            if e.text.find('에 대한 검색 결과가 없습니다.') >= 0:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return

            bil = [bi for bi in e.find_elements_by_xpath('./div[@class="list"]')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            for i in range(len(bil)):
                msg = {
                    'page': self.cur_page,
                    'row': i + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    'site_board': self.config['params']['site']['site_board'],
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

                    # 검색 결과물 페이지의 목록(List) 읽기
                    e = self.get_by_xpath('//div[@class="search-list section-list-area"]')
                    ail = [bi for bi in e.find_elements_by_xpath('./div')]
                    bi = ail[i]

                    #작성시간
                    e_t = bi.find_element_by_xpath('.//span[@class="date"]')
                    cerate_ts = e_t.text.strip()
                    msg['create_ts'] = cerate_ts.replace('-', '.')

                    if self.stop_article_older_than(msg):
                        title_a = bi.find_element_by_xpath('.//h4[@class="article-title"]//a')
                        t_a = title_a.text.strip()
                        self.logger.info(f'***** 최신 게시글 Title: {t_a} .....   ')
                        self.is_done = True
                        break

                    section = {'정치': 'politics', '사회': 'society' }
                    # 한겨레 기사의 section 찾기 (현재 section 값 = 사회)
                    # URL 정보에서 '사회' 면인지를 판단 : society
                    se = bi.find_element_by_xpath('.//h4/a[@href]')
                    category = se.get_attribute('href').strip().split('/')[4].strip()
                    if category != section[self.config['params']['site']['site_board']]:
                        # 다음 항목은 디버깅용과 속도 문제로 인한 오류 발생을 방지하기 위함
                        # 만약 제거한다면 time.sleep(1) 추가 필요
                        self.logger.info(f'***** SKIPing {category} .....   Page[{self.cur_page}:{i+1}]')
                        continue

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('.//h4/a')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        article_url = bi.find_element_by_xpath('.//h4/a[@href]')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = article_url.get_attribute('href')

                    # 게시글 id
                    msg['article_id'] = re.search('/(\d+)\.html$', msg['article_url']).group(1)

                    # 게시글 본문으로 이동
                    title_e = article_url
                    self.move_to_element(article_url)
                    self.get_article(title_e, msg, i+1)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

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
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="paginate"]')
            pa_list = ple.find_elements_by_xpath('./a')

            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.get_attribute('class') == 'selected':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'selected':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 다음 페이지 클릭후의 현재 페이지 번호 구하기
                    nple = self.get_by_xpath('//div[@class="paginate"]')
                    for npa in nple.find_elements_by_xpath('./a'):
                        if npa.get_attribute('class') == 'selected':
                            npa_pg_num = npa.text.strip()
                            if npa_pg_num == current_pg_num:
                                self.is_done = True
                                return
                            else:
                                break
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
                        # article['image_list'].append(f'{j}.png') 왜 들어가 있는지를 이해 하지 못함
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

        for cmt in article['comment_list']:
            if not('comment_img' in cmt and cmt['comment_img']):
                continue
            for k, c in enumerate(cmt['comment_img_url']):
                try:
                    cmt_img_f = self.get_safe_path(
                        self.config['target']['folder'],
                        article['article_id'],
                        f'{cmt["comment_id"]}_{k}.png'
                    )
                    urllib.request.urlretrieve(c, cmt_img_f)
                except Exception as err:
                    self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img"]}: {str(err)}')

    # ==========================================================================
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )

        # json 파일 생성
        self.save_d(at_js_f, article)

        # save image
        # for j, sub_e_url in enumerate(article['image_url_list']):
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{j}.png'
        #     )
        #     urlretrieve(sub_e_url, cmt_img_f)
        #
        # for cmt in article['comment_list']:
        #     if not('comment_img' in cmt and cmt['comment_img']):
        #         continue
        #     for k, c in enumerate(cmt['comment_img_url']):
        #         try:
        #             cmt_img_f = self.get_safe_path(
        #                 self.config['target']['folder'],
        #                 article['article_id'],
        #                 f'{cmt["comment_id"]}_{k}".png'
        #             )
        #             urlretrieve(c, cmt_img_f)
        #         except Exception as err:
        #             self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img"]}: {str(err)}')

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

            # 검색어 입력 및 리턴키
            e = self.get_by_xpath('//*[@id="search_form"]/div/form/input[3]')
            search_key = self.config['params']['site']['search']
            self.send_keys(e, search_key + Keys.RETURN)
            self.implicitly_wait(after_wait=3)

            #500 server error 새로고침
            try:
                e = self.get_by_xpath('//div[@class="px-4 text-lg text-gray-500 border-r border-gray-400 tracking-wider"]')
            except:
                pass
            else:
                self.driver.refresh()

            # '뉴스 검색 더보기' 클릭
            try:
                e = self.get_by_xpath('(//div[@class="search-list section-list-area"]/div/a)[1]')
            except:
                pass
            else:
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

            # 기간 설정하기 (페이지 처리부에서 섹션면 판단하므로 여기서 미리 해 주어야 함)
            search_period = self.config['params']['site']['stop_article_older_than']['datetime']
            ymd, etc = search_period.split(' ')
            # self.get_by_xpath('//input[@name="startdate"]').clear()
            e = self.get_by_xpath('//input[@name="startdate"]')
            e.clear()
            self.send_keys(e, ymd)
            self.implicitly_wait(after_wait=1)

            # 버턴 ('확인') 누르기
            e = self.get_by_xpath('//button[@id="submitbtn"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=3)

            # 게시글 미노출 새로고침
            try:
                e = self.get_by_xpath('//div[@class="search-list section-list-area"]')
                if e.text.find('에 대한 검색 결과가 없습니다.') >= 0:
                    self.driver.refresh()
            except:
                pass

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.implicitly_wait(after_wait=2) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                self.next_page()
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()

################################################################################
def do_start(**kwargs):
    with HaniSearch(kwargs['config_f']) as ws:
        ws.start()

################################################################################
if __name__ == '__main__':
    _config_f = 'hani.yaml'
    do_start(config_f=_config_f)
