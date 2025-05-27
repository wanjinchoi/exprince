"""
====================================
 :mod:`gov/ FoodToday
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
#  * [2023/04/18]
#     - 스크린샷에 댓글 부분 포함
#     - board_name에 값 추가
#  * [2023/01/31]
#     - 댓글 xpath 수정
#  * [2022/10/26]
#     - 댓글 iframe 수정
#  * [2022/04/15]
#     - 댓글 날짜형식수정
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
import requests
import datetime
import urllib.request
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# from bs4 import BeautifulSoup


################################################################################

class FoodTodaySearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'FoodTodaySearch.log'),
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
        self.logger.info(f'Starting FoodToday Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색 조건
        e = self.get_by_xpath('//ul[@class="rdo_list"]/li[2]/span/div')
        self.safe_click(e)
        # 검색어 입력
        e = self.get_by_xpath('//dd/input[@type="text"]')
        self.send_keys(e, self.config['params']['site']['search'])

        # 섹션 분류
        e = self.get_by_xpath('//div[@class="select_box"]/select')
        self.safe_click(e)
        e_op = e.find_element_by_xpath('./option[@value="74"]')
        self.safe_click(e_op)
        # 검색 단추
        e = self.get_by_xpath('//input[@value="찾기"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 페이지 목록 1페이지를 눌러줘야함.
        ple = self.driver.find_element_by_xpath('.//div[@class="btn_pagenum"]/a')
        self.move_to_element(ple)
        self.safe_click(ple)
        self.implicitly_wait(after_wait=1)
    # ==========================================================================

    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_comment(self, msg):
        try:

            e_a = self.get_by_xpath('//div[@id="wrapper"]/div[@id="list"]')
            comments = e_a.find_elements_by_xpath('.//div[@class="reply-wrapper"]')
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

                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath('.//div[@class="reply-history-time"]/span[@class="modify-time"]')
                et = e.text
                hhh, mmm = 0, 0
                cmt['create_ts'] = ""
                if et.find('분') > 0:
                    mm = re.sub(r'[^0-9]', '', et)
                    mmm = int(mm)
                elif et.find('시간') > 0:
                    hh = re.sub(r'[^0-9]', '', et)
                    hhh = int(hh)
                elif et.find('방금') > 0:
                    e_now = datetime.datetime.now()
                    cmt['create_ts'] = e_now.strftime('%Y.%m.%d %H:%M:%S')
                else:
                    e_re = datetime.datetime.strptime(et, '%Y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    cmt['create_ts'] = e_re
                try:
                    if cmt['create_ts'] == "":
                        d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                        cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                except:
                    pass

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
            self.switch_to_window(0)
            # self.driver.execute_script("window.scrollTo(0, 5000);")
            # if self.config['params']['site']['capture_article']:
            #     # save capture
            #     # e_body = self.get_by_xpath('//body')
            #     msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
            #                                        f'{msg["article_id"]}.png')
            #     e_heads = self.driver.find_elements_by_xpath('//div[@class="fix_art_top fix"]|'
            #                                                  '//a[@class="btn_top"]')
            #     for e_head in e_heads:
            #         self.driver.execute_script("""
            #                                 var element = arguments[0];
            #                                 element.parentNode.removeChild(element);
            #                                 """, e_head)
            #     self.full_screenshot(msg_capture_f)
            # 수집 영역
            e = self.get_by_xpath('//div[@class="wrapper"]//ul[@class="art_top_nav"]/li[last()]/a')
            msg['board_name'] = e.text.strip()

            e_ab = self.get_by_xpath('//div[@class="column sublay"]/div[1]', timeout=1)

            # 1) 게시글 내용 :
            e = e_ab.find_element_by_xpath('.//div[@class="cnt_view news_body_area"]')
            msg['contents'] = e.text.strip()

            # 이미지
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []

            # 댓글 iframe
            self.switch_to_window(1)
            self.driver.execute_script("window.scrollTo(0, 5000);")
            self.implicitly_wait(after_wait=1)
            #
            # self.switch_to_iframe('//iframe[@title="라이브리 - 댓글영역"]')

            e = self.get_by_xpath('//div[@class="reply_wrap"]' , timeout=1)
            # 댓글 개수
            try:
                e_c = e.find_element_by_xpath('.//h4/b/span')
                msg['num_comments'] = int(e_c.text.strip())
            except:
                msg['num_comments'] = 0

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            # 댓글 더 보기가 있는 경우
            try:
                e = e_c.find_element_by_xpath('.//div[@class="more-wrapper"]')
                b_ple = e.find_elements_by_xpath('./button')
                for pa, cmt_page in enumerate(b_ple):
                    self.safe_click(cmt_page)
                    self.implicitly_wait(after_wait=1)
                # 댓글 전체 보기 창 : 더 보기를 다 누르면 뜬다, 안 뜨는 경우도 있음
                e = self.get_by_xpath('//div[@class="list-reduce"]', timeout=1)
                c_ple = e.find_elements_by_xpath('./button')
                for ca in c_ple:
                    self.safe_click(ca)
                    self.implicitly_wait(after_wait=1)
            except:
                pass
            self.get_comment(msg)

        except Exception as err:
            raise
        finally:
            # 스크린샷
            self.driver.execute_script("window.scrollTo(0, 5000);")
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # save capture
                # e_body = self.get_by_xpath('//body')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="fix_art_top fix"]|'
                                                                 '//a[@class="btn_top"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                    var element = arguments[0];
                                                    element.parentNode.removeChild(element);
                                                    """, e_head)
                    self.full_screenshot(msg_capture_f)

            # 이전 페이지
            self.driver.back()
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
            e = self.get_by_xpath('//ul[@class="art_list_all"]')
            es = e.find_elements_by_xpath('./li')

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
                    e = self.get_by_xpath('//ul[@class="art_list_all"]')
                    es = e.find_elements_by_xpath('./li')
                    ea = es[i]

                    # 1) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('?no=')[2]
                    msg['article_id'] = v
                    # 2) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 3) 제목: title
                    e_t = ea.find_element_by_xpath('.//h2[@class="clamp c2"]')
                    msg['title'] = e_t.text.strip()
                    # 4) 작성 시간
                    e = ea.find_element_by_xpath('.//li[@class="date"]')
                    msg['create_ts'] = e.text.replace('-', '.').strip() + ':00'
                    # 5) 작성자
                    e = ea.find_element_by_xpath('.//li[@class="name"]')
                    msg['author'] = e.text.partition('기자')[0].strip()

                    self.safe_click(e_t)
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
            ple = self.driver.find_element_by_xpath('.//div[@class="btn_pagenum"]')
            self.move_to_element(ple)
            e = ple.find_element_by_xpath('./a[@class="on"]')
            now_page = e.text.strip()
            is_on = False

            for pa in ple.find_elements_by_xpath('./a|//a[@class="btn_p next"]'):
                if pa.text.strip() == now_page:
                    is_on = True
                    continue
                elif is_on:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return

            self.is_done = True
        except Exception as err:
            raise
        finally:
            self.switch_to_window(0)

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
    with FoodTodaySearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'foodtoday.yaml'
    do_start(config_f=_config_f)
