"""
====================================
 :mod:`news/ SBS_news
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
# * Yeonhee Ji
#
# Change Log
# --------
#  * [2023/06/08]
#     - 게시글 작성시간, 조회수 XPath 수정, 작성자
#  * [2023/05/02]
#     - board_name의 xpath 수정
#  * [2023/04/17]
#     - 댓글 더보기의 xpath 변경
#     - 스크린샷에 댓글 부분 포함
#     - board_name에 값 추가
#  * [2023/04/03]
#     - 댓글 수집 전에 5초 기다리도록 추가
#  * [2023/03/28]
#     - 조회수가 존재하지 않는 게시글이 존재하여 해당 게시글은 null값으로 입력
#  * [2023/03/07]
#     - 댓글 create_ts 가져오는 로직 수정
#  * [2023/02/21]
#     - 댓글 필드명 변경 'comment_nick' -> 'nickname'
#  * [2022/11/28]
#     - 비디오 추출 주석 처리
#     - 댓글 부분의 iframe 변경
#     - 게시글 내용 추출 부분 xpath 수정
#  * [2022/04/26]
#     - search_type 주석 해지.
#  * [2022/02/23]
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
import requests
import datetime
import urllib.request
# from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# from bs4 import BeautifulSoup


################################################################################

class SbsNewsSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'SbsNewsSearch.log'),
                            logsize=1024 * 1024 * 10)
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
        self.logger.info(f'Starting SbsNews Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e = self.get_by_xpath('//div[@class="w_snb"]//input[@name="query"]')
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//div[@class="w_snb"]//button[@class="comSearchBtn"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 사회만 체크 해서 재 검색
        # 정치
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[1]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 경제
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[2]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 국제
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[4]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 생활 문화
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[5]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 연예
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[6]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 스포츠
        e = self.get_by_xpath('//fieldset//div[@class="nse_sort_w"][2]/ul/li[7]/input')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 검색
        e = self.get_by_xpath('//fieldset//button[@class="sbtn psearch_btn"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        try:
            self.implicitly_wait(after_wait=5)
            e_a = self.get_by_xpath('//div[@id="wrapper"]/div[@id="list"]')
            comments = e_a.find_elements_by_xpath('.//div[@class="reply-wrapper"]')
            # '|.//div[@class="reply-wrapper reply-best-wrapper"]
            parent_comment_id = ''

            for i, cmt_e in enumerate(comments):
                delay_c = random.uniform(
                    self.config['params']['site']['delay']['comment']['min'],
                    self.config['params']['site']['delay']['comment']['max'],
                )
                time.sleep(delay_c)
                cmt = {}

                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath('.//div[@class="reply-history-time"]/span[@class="modify-time"]')
                # 닉네임, 작성 일시, 내용
                # 작성 일시의 경우 24시간이 지나지 않으면 'xx 시간전'으로 표기되어 다음 방법을 사용함)
                when = e.get_attribute('title').strip()
                chronos = re.match(r'(\d+)년\s+(\d+)월\s+(\d+)일\s+(.+?)\s+(\d+):(\d+)', when).groups()
                if chronos[3] == '오후' and chronos[4] != '12':
                    create_ts = chronos[0] + '.' + chronos[1] + '.' + chronos[2] \
                                + ' ' + str(int(chronos[4]) + 12) + ':' + chronos[5] + ':00'
                else:
                    create_ts = chronos[0] + '.' + chronos[1] + '.' + chronos[2] \
                                + ' ' + chronos[4] + ':' + chronos[5] + ':00'
                cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                    '%Y.%m.%d %H:%M:%S')

                # 댓글 아이디
                e = cmt_e.find_element_by_xpath('.//div[@class="writer"]')
                ea = e.get_attribute('data-seq')
                cmt['comment_id'] = ea
                self.move_to_element(e)

                # 대댓글 확인
                e = cmt_e.find_element_by_xpath('./..')
                e_re = e.get_attribute('class')
                if e_re.find('child-reply') == 0:
                    is_reply = True
                else:
                    is_reply = False
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id

                # 댓글 nickname
                e = cmt_e.find_element_by_xpath('.//button[@class="writer-name-text"]/span')
                cmt['nickname'] = e.text.strip()

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('.//div[@class="reply-content-wrapper"]/div[1]')
                cmt['contents'] = e.text.strip()

                # 댓글 좋아요, 싫어요
                e = cmt_e.find_element_by_xpath('.//button[@title="공감"]/span[2]')
                cmt['like'] = int(e.text.strip())
                e = cmt_e.find_element_by_xpath('.//button[@title="반대"]/span[2]')
                cmt['dislike'] = int(e.text.strip())

                # 댓글 이미지
                # 이미지 달은 경우 생각 해서 다시 해 보기
                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find('reply-sticker  ') > 0:
                    re_img = cmt_e.find_element_by_xpath('.//div[@class="reply-sticker  "]/img')
                    cmt['comment_img_url'].append(re_img.get_attribute('src'))  # src가 이미지 주소
                    cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except:
            ...

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
            # if self.config['params']['site']['capture_article']:
            #     # save capture
            #     # e_body = self.get_by_xpath('//body')
            #     msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
            #                                        f'{msg["article_id"]}.png')
            #     # self.full_screenshot(msg_capture_f)
            #     self._screenshot(msg_capture_f)
            # 수집 영역
            e = self.get_by_xpath('//div[@class="w_top_cs"]//li[last()]/a')
            msg['board_name'] = e.text.strip()

            e_ab = self.get_by_xpath('//div[@class="w_article"]', timeout=1)

            # 4) 작성 시간
            e = e_ab.find_element_by_xpath('.//div[@class="date_area"]/span[1]')
            msg['create_ts'] = e.text.strip() + ':00'
            # 5) 조회수: view_count
            e = e_ab.find_element_by_xpath('.//div[@class="date_area"]/span[@class="view viewcnt"]')
            e_a = e.text.strip()
            if e_a is '':
                msg['view_count'] = None
            else:
                msg['view_count'] = int(e.text.replace(',', '').strip())
            # 6) 작성자
            try:
                e = e_ab.find_element_by_xpath('.//a[@class="name"]')
                msg['author'] = e.text.strip().rpartition('\n')[0]
            except:
                msg['author'] = ""

            # 1) 게시글 내용 :
            e = e_ab.find_element_by_xpath('.//div[@class="article_cont_area"]/div[@class="main_text"]')
            msg['contents'] = e.text.strip()

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            e = e_ab.find_element_by_xpath('.//div[@class="article_cont_area"]/div[@class][1]')
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    if sub_e.get_attribute('alt') in ['네이버 채널 구독']:
                        continue
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)
            # 비디오 가지고 오기
            # msg['video_url_list'] = []
            # if inner_html.find('video') > 0:
            #     self.switch_to_iframe('//div[@class="article_cont_area"]//iframe[@loading="lazy"]')
            #     e = self.get_by_xpath('//video')
            #     self.move_to_element(e)
            #     sub_v_url = e.get_attribute('src')
            #     if sub_v_url.find('blob:') == 0:
            #         sub_v_url = e.get_attribute('src').partition('blob:')[2]
            #     msg['video_url_list'].append(sub_v_url)
            #     msg['video_list'].append('')

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []

            # 댓글 수
            # 댓글이 없는 경우 창이 없음 무조건 0으로 표시

            # 댓글에 iframe이 있음. 하지만 스크롤 내려야 생겨남 : 영상이 있으면 스크롤이 안 내려가서 못 찾음
            self.switch_to_window(1)
            self.driver.execute_script("window.scrollTo(0, 5000);")
            self.implicitly_wait(after_wait=1)
            #
            self.switch_to_iframe('//iframe[@title="라이브리 - 댓글영역"]')
            e_c = self.get_by_xpath('//div[@id="wrapper"]', timeout=1)

            # 댓글 개수
            try:
                e = self.get_by_xpath('//div[@class="reply-count"]//span[@class="count-text"]')
                msg['num_comments'] = int(e.text.strip())
            except:
                msg['num_comments'] = 0

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                self.driver.switch_to.default_content()
                return
            msg['comment_list'] = []
            self.implicitly_wait(after_wait=5)
            e_a = self.get_by_xpath('//div[@id="wrapper"]/div[@id="list"]')
            comments = e_a.find_elements_by_xpath('.//div[@class="reply-wrapper"]')
            # 댓글 더 보기가 있는 경우
            while len(comments) != 0:
                fold_flag = False

                # 두 번째 : 펼쳐야 하는 경우가 없는 경우는 빠져 나가기
                for more in e_a.find_elements_by_xpath('.//div[@class="more-wrapper"]/button'):
                    self.safe_click(more)
                    self.implicitly_wait(after_wait=1)
                    fold_flag = True

                # 세 번째 : 펼쳐야 하는 경우
                for more in self.driver.find_elements_by_xpath('//div[@class="list-reduce"]/button'):
                    self.safe_click(more)
                    self.implicitly_wait(after_wait=1)
                    break

                # while 문 빠져나가기
                if fold_flag == False:
                    break
            # try:
            #     self.implicitly_wait(after_wait=5)
            #     e = e_c.find_element_by_xpath('.//div[@class="more-wrapper"]')
            #     b_ple = e.find_elements_by_xpath('./button')
            #     for pa, cmt_page in enumerate(b_ple):
            #         self.safe_click(cmt_page)
            #         self.implicitly_wait(after_wait=1)
            #     # 댓글 전체 보기 창 : 더 보기를 다 누르면 뜬다, 안 뜨는 경우도 있음
            #     e = self.get_by_xpath('//div[@class="list-reduce"]', timeout=1)
            #     c_ple = e.find_elements_by_xpath('./button')
            #     for ca in c_ple:
            #         self.safe_click(ca)
            #         self.implicitly_wait(after_wait=1)
            # except:
            #     pass
            self.get_comment(msg)
        except Exception as err:
            raise
        finally:
            # 스크린샷
            self.driver.switch_to.default_content()  # iframe 다시 전환
            self.driver.execute_script("window.scrollTo(0, 0)")
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.driver.execute_script("window.scrollTo(0, -(document.body.scrollHeight))")
                self._screenshot(msg_capture_f)
            # 이전 페이지
            self.driver.close()
            self.implicitly_wait(after_wait=1)

            try:
                self.switch_to_main_window()
            except:
                # selenium.common.exceptions.WebDriverException: Message: unknown error:
                # cannot determine loading status
                pass

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21. 21:48:00'
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
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//ul[@class="psearch_result_list"]')
            es = e.find_elements_by_xpath('./li')

            for i, ea in enumerate(es):
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
                    # 'video_url_list': [],
                    # 'video_list': [],
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
                    e = self.get_by_xpath('//ul[@class="psearch_result_list"]')
                    es = e.find_elements_by_xpath('./li')
                    ea = es[i]

                    # 2) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('.//a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('id=')[2].partition('&')[0]
                    msg['article_id'] = v
                    # 2) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 3) 제목: title
                    e_t = ea.find_element_by_xpath('.//a/p/strong[@class="psil_tit"]')
                    msg['title'] = e_t.text.strip()

                    self.safe_click(e_url)
                    self.implicitly_wait(after_wait=1)
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
                # self.save_attachment(msg)
                self.save_image(msg)
                # self.save_video(msg)
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
            e = self.get_by_xpath('//div[@id="container"]')
            ple = e.find_element_by_xpath('.//div[@class="mdp_inner"]')
            e = ple.find_element_by_xpath('.//strong')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('./a'):
                # 여기 다시 하기 다음으로 넘어가는 거 안 된다
                if pa.get_attribute('class') == 'fncpn next':
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.get_attribute('class') == 'fncpn prev':
                    continue
                elif int(pa.text.strip()) > is_on:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
            self.is_done = True
        except Exception as err:
            raise
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
    def save_video(self, article):
        for i, video_url in enumerate(article['video_url_list']):
            article_video_p = self.get_safe_path(
                self.config['target']['folder'],
                article['article_id'],
                f'{i}.mp4'
            )
            file = requests.get(video_url, stream=True)
            with open(article_video_p, 'wb') as f:
                print("Donloading chunck")
                for chunk in file.iter_content(chunk_size=255):
                    if chunk:
                        f.write(chunk)

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
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with SbsNewsSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'sbs_news.yaml'
    do_start(config_f=_config_f)
