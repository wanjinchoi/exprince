"""
====================================
 :mod:`dogdrip`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
# lee yong seok
# --------
#  * [2023/03/10]
#     - starting

################################################################################
# import re
import os
import re
import sys
import yaml
import json
import time
import shutil
import random
import tarfile
import datetime
import traceback
from pathlib import Path
from copy import deepcopy
# from PIL import Image
# from urllib.request import urlretrieve
from datetime import timedelta
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
def download_wait(directory, timeout, nfiles=None):
    seconds = 0
    dl_wait = True
    while dl_wait and seconds < timeout:
        time.sleep(1)
        dl_wait = False
        files = os.listdir(directory)
        if nfiles and len(files) != nfiles:
            dl_wait = True

        for fname in files:
            if fname.endswith('.crdownload'):
                dl_wait = True

        seconds += 1
    return seconds


################################################################################
class DogdripSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DogdripSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # self.config['params']['site']['search'] = self.config['params']['site']['search'].strip()

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
        self.logger.info(f'Starting Dogdrip Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        # 검색 단추 클릭
        e = self.get_by_xpath('//*[@id="ed-search-toggle"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 검색 단추
        e = self.get_by_xpath('//*[@id="ed-search"]/div[1]/div[2]/form/div[1]/input')
        self.send_keys(e, self.config['params']['site']['search'])
        self.implicitly_wait(after_wait=1)
        # 게시물 검색 클릭
        e = self.get_by_xpath('//*[@id="ed-search"]/div[1]/div[2]/form/div[2]/button[1]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def save_e_img(self, re_img, msg, cmt):
        cmt_img_f = self.get_safe_path(
            self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"]+"_0"}.png')
        re_img.screenshot(cmt_img_f)

    # ==========================================================================
    def get_comments(self, msg):
        try:
            comments_e = self.get_by_xpath('//div[@class="ed comment-list"]')
            comments = comments_e.find_elements_by_xpath('./div')
            parent_comment_id = None
            while True:
                for i, cmt_e in enumerate(comments):
                    comments_es = self.get_by_xpath('//div[@class="ed comment-list"]')
                    comments_e = comments_es.find_elements_by_xpath('./div')
                    cmt_e = comments_e[i]
                    # 광고
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

                    # 댓글 작성 시간
                    create_time = cmt_e.find_element_by_xpath('.//div[@class="ed flex flex-right"]//span')
                    when = create_time.text.strip()
                    ddd, hhh, mmm = 0, 0, 0
                    # 38분 전
                    if when.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', when)
                        mmm = int(mm)
                    # 5시간 전
                    elif when.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', when)
                        hhh = int(hh)
                    elif when.find('일') > 0:
                        mm = re.sub(r'[^0-9]', '', when)
                        mmm = int(mm)
                    else:
                        cmt['create_ts'] = datetime.datetime.strptime(when, '%Y.%m.%d').strftime('%Y.%m.%d %H:%M:%S')
                    if not cmt['create_ts']:
                        d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                        cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')

                    # 댓글 닉네임
                    e = cmt_e.find_element_by_xpath('.//div[@class="ed inline-flex flex-middle margin-right-small"]/h6/span')
                    ea = e.text.strip()
                    cmt['nickname'] = ea
                    self.move_to_element(e)
                    # 댓글 ID
                    e_c = cmt_e.find_element_by_xpath('.//div[@class="ed margin-bottom-xxsmall margin-left-xsmall"]//div')
                    cmt_id = e_c.get_attribute('class')
                    c = cmt_id.split('_')[1]
                    cmt['comment_id'] = c

                    #댓글 내용
                    cmt['contents'] = e_c.text.strip()

                    # 대댓글 여부 확인
                    e_re = cmt_e.get_attribute('class')
                    if e_re.find('depth') >= 0:
                        is_reply = True
                    else:
                        is_reply = False
                    cmt['is_reply'] = is_reply
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ""
                    else:
                        cmt['parent_comment_id'] = parent_comment_id

                    # 댓글 좋아요
                    e_g = cmt_e.find_element_by_xpath('//div[@class="action ed flex flex-right flex-middle margin-remove"]/span/span[1]')
                    cmt['like'] = e_g.text.strip()

                    # 댓글 이미지X 스티커 O
                    #https://www.dogdrip.net/dogdrip/dvs/d/21/12/19/c4124d0aa4a7e498777cb087c1016ef5.jpg
                    inner_html = cmt_e.get_attribute('innerHTML')
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    if inner_html.find('mid=sticker') > 0:
                        re_img = e_c.find_element_by_xpath('.//a')
                        c = re_img.get_attribute('style')
                        c_sr = c.split('(".')[1].partition('")')[0]
                        url = self.config['params']['kwargs']['url'] + c_sr
                        cmt['comment_img_url'].append(url)  # src가 이미지 주소
                        self.save_e_img(re_img, msg, cmt)
                        cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
                    index = len(msg['comment_list'])
                    self.logger.info(f'   [{index}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                    if msg['num_comments'] <= len(msg['comment_list']):
                        break

                    #댓글 페이지 넘기기
                    if (index/50) == 1:
                        self.next_page_article()
                if msg['num_comments'] <= len(msg['comment_list']):
                    break

        except Exception as err:
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def enable_download_headless(self, download_dir):
        self.browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        self.browser.execute("send_command", params)

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
                    self.full_screenshot(msg_capture_f)

            e = self.get_by_xpath('//div[@class="ed article-wrapper inner-container"]')
            # 1) 제목
            title_e = e.find_element_by_xpath('./div/div[1]/h4/a')
            msg['title'] = title_e.text.strip()
            # 2) 작성자
            author_e = e.find_element_by_xpath('./div/div[1]/div[1]/div[1]/span[1]/a|./div[1]/div[1]/div[1]/div[1]/span[1]/span/span')
            msg['author'] = author_e.text.strip()
            # 닉네임, 작성 일시, 내용
            # 작성 일시의 경우 24시간이 지나지 않으면 'xx 시간전'으로 표기되어 다음 방법을 사용함)
            # 3) 작성일
            create_time = e.find_element_by_xpath('./div/div[1]/div[1]/div[1]/span[2]/span[2]')
            when = create_time.text.strip()
            ddd, hhh, mmm = 0, 0, 0
            # 38분 전
            if when.find('분') > 0:
                mm = re.sub(r'[^0-9]', '', when)
                mmm = int(mm)
            # 5시간 전
            elif when.find('시간') > 0:
                hh = re.sub(r'[^0-9]', '', when)
                hhh = int(hh)
            elif when.find('일') > 0:
                mm = re.sub(r'[^0-9]', '', when)
                mmm = int(mm)
            else:
                msg['create_ts'] = datetime.datetime.strptime(when, '%Y.%m.%d').strftime('%Y.%m.%d %H:%M:%S')
            if not msg['create_ts']:
                d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
            #조회수
            e_v = e.find_elements_by_xpath('./div[1]/div[1]/div[1]/div[1]/span[3]/span[2]')[0]
            msg['view_count'] = int(e_v.text.strip())
            # 추천수
            content_v = self.get_by_xpath('//div[@class="wgtRv addon_addvote"]')
            e = content_v.find_element_by_xpath('.//span[@class="btnRv btnRo"]//button//span[2]')
            # msg['like'] = int(e.text.split()[1].replace(',', ''))
            msg['like'] = int(e.text.strip())
            # 비추천이 없음.
            msg['dislike'] = None

            # 본문(write_div 아래 모든 형식이 있슴.) content
            content_e = self.get_by_xpath('//div[@class="ed article-wrapper inner-container"]')
            e = content_e.find_element_by_xpath('./div[1]/div[2]')
            inner_html = e.get_attribute('innerHTML')
            # 본문 text (글이 없으면 알아서 ''로 나옴.)
            msg['contents'] = e.text.strip()
            # 본문 이미지는 tagname으로 찾아야함.
            msg['image_list'] = []
            if inner_html.find('img') > 0:
                img_e = e.find_elements_by_tag_name('img')
                for j, img in enumerate(img_e):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{j}.png')
                    img.screenshot(cmt_img_f)
                    msg['image_list'].append(f'{j}.png')

            # 댓글수
            e = self.get_by_xpath('//*[@id="commentbox"]')
            if e.text.strip() == '':
                msg['num_comments'] = 0
                return
            else:
                num_c = e.find_element_by_xpath('./h4')
                msg['num_comments'] = int(num_c.text.split()[0].replace('개의', ''))

            msg['comment_list'] = []

            #댓글 수가 50개 이상이면 댓글 첫 페이지 클릭
            if msg['num_comments'] > 50:
                e = self.get_by_xpath('//ul[@class="ed pagination pagewide"]//li[1]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            self.get_comments(msg)

        except Exception as err:
            raise
        finally:
            self.close_tab()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_main_window()

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
    def get_user_type(self, boardname):
        if boardname in ["배민커넥트", "배달", "배달대행 기사들 모임"]:
            return "라이더"
        else:
            return "소비자"

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            e = self.get_by_xpath('//tbody')
            es = e.find_elements_by_xpath('./tr')
            for i, ea in enumerate(es):
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
                    'author': None,      # 변경
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()

                    e = self.get_by_xpath('//tbody')
                    es = e.find_elements_by_xpath('./tr')
                    ea = es[i]

                    # 공지 게시글 건너뛰기
                    e = ea.get_attribute('class')
                    if e == 'notice':
                        continue

                    # e_url = ae.get_attribute('href')
                    ae = ea.find_element_by_xpath('./td[@class="title"]/span/a')
                    e_url = ae.get_attribute('href')
                    # 1) 게시글 URL:  article_url
                    msg['article_url'] = e_url
                    # 2) 게시글id : article_id
                    msg['article_id'] = e_url.split('/')[4].partition('?')[0]

                    self.driver.execute_script(f"window.open('{e_url}')")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
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
        finally:
            pass

    # ==========================================================================
    def next_page_article(self):
        ple = None
        e_pa = None
        try:
            # np = self.cur_page + 1
            # 목록으로 이동
            self.switch_to_window(1)
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="ed pagination-container"]//ul[1]', timeout=2)
            is_on = False
            # 현재 페이지 번호 구하기
            for pa in ple.find_elements_by_xpath('.//li'):
                if pa.get_attribute('class') == 'active':
                    e_pa = int(pa.text.strip())
                    break

            for pa in ple.find_elements_by_xpath('.//li'):
                if int(pa.text.strip()) > e_pa:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            if ple is None:
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
            raise

    # ==========================================================================
    def next_page(self):
        ple = None
        e_pa = None
        try:
            # np = self.cur_page + 1
            # 목록으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="ed pagination-container padding-horizontal-small@s"]//ul[1]', timeout=2)
            # ple_e = ple.find_element_by_xpath('.//ul[@class="ed pagination pagewide"]')
            is_on = False
            # 현재 페이지 번호 구하기
            for pa in ple.find_elements_by_xpath('.//li'):
                if pa.get_attribute('class') == 'active':
                    e_pa = int(pa.text.strip())
                    break

            for pa in ple.find_elements_by_xpath('.//li'):
                if int(pa.text.strip()) > e_pa:
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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            f'{article["article_id"]}'
            # f'{self.output["start_ts"]}'
        )
        self.save_d(at_js_f, article)
        # save image dcinside는 이미지 다운로드가 안됨
        # for j, sub_e_url in enumerate(article['image_list']):
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{j + 1}.png'
        #     )
        #     urlretrieve(sub_e_url, cmt_img_f)
        # for cmt in article['comment_list']:
        #     if not('comment_img_url' in cmt and cmt['comment_img_url']):
        #         continue
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{cmt["comment_id"]}.png'
        #     )
        #     urlretrieve(cmt['comment_img_url'], cmt_img_f)

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
            # self.login()
            # if self.config['params']['site']['get_cafe_info']:
            #     self.get_cafe_info()
            # 첨부파일 다운로드 옵션
            # self.enable_download_headless(self.get_download_path())
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
    with DogdripSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'dogdrip_free.yaml'
    do_start(config_f=_config_f)
