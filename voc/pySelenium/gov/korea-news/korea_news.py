"""
====================================
 :mod:`gov/ Korea_News : 정책 뉴스
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
#  * [2023/06/28]
#     - 검색 부분의 사이트 UI 변경
#  * [2023/05/04]
#     - 검색 부분의 사이트 UI 변경
#  * [2023/01/30]
#     - 사이트 UI 변경
#  * [2022/04/26]
#     - search_type 주석 해지.
#  * [2022/02/21]
#     - starting
################################################################################
import os
# import re
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
# from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# from bs4 import BeautifulSoup


################################################################################

class KoreaNewsSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'KoreaNewsSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['site_board'],
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
        self.logger.info(f'Starting KoreaNews Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        # 뉴스 선택
        e = self.get_by_xpath('//ul[@class="nav"]/li[1]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 정부 부처 선택
        e = self.get_by_xpath('//div[@class="sch_tab"]/ul/li[3]/a')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 부처 항목
        # e_ab = self.get_by_xpath('(//div[@class="box"])[1]/ul/li[1]')
        # e = e_ab.find_element_by_xpath('./label')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)
        e_ab = self.get_by_xpath('//div[@id="srchOutSite3"]')
        # 농림축산식품부
        e = e_ab.find_element_by_xpath('.//ul[1]/li[11]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 산업통산자원부
        e = e_ab.find_element_by_xpath('.//ul[1]/li[12]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 보건복지부
        e = e_ab.find_element_by_xpath('.//ul[1]/li[13]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 환경부
        e = e_ab.find_element_by_xpath('.//ul[1]/li[14]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 해양수산부
        e = e_ab.find_element_by_xpath('.//ul[1]/li[19]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 법제처
        e = e_ab.find_element_by_xpath('.//ul[1]/li[22]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 식품의약품안전처
        e = e_ab.find_element_by_xpath('.//ul[1]/li[23]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 청 항목
        # e_ab = self.get_by_xpath('(//div[@class="box"])[1]/ul/li[2]')
        # e = e_ab.find_element_by_xpath('./label')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)
        # 관세청
        e = e_ab.find_element_by_xpath('.//ul[2]/li[2]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 대검찰청
        e = e_ab.find_element_by_xpath('.//ul[2]/li[6]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 경찰청
        e = e_ab.find_element_by_xpath('.//ul[2]/li[9]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 질병관리청
        e = e_ab.find_element_by_xpath('.//ul[2]/li[15]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 해양경찰청
        e = e_ab.find_element_by_xpath('.//ul[2]/li[18]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 위원회 항목
        # e_ab = self.get_by_xpath('(//div[@class="box"])[1]/ul/li[3]')
        # e = e_ab.find_element_by_xpath('./label')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)
        # 공정거래위원회
        e = e_ab.find_element_by_xpath('.//ul[3]/li[4]/span/label')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 적용
        e = self.get_by_xpath('//button[@class="app"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        try:

            e_a = self.get_by_xpath('//div[@id="wrapper"]')
            comments = e_a.find_elements_by_xpath('.//div[@class="reply-top"]')
            parent_comment_id = ''

            for i, cmt_e in enumerate(comments):
                delay_c = random.uniform(
                    self.config['params']['site']['delay']['comment']['min'],
                    self.config['params']['site']['delay']['comment']['max'],
                )
                time.sleep(delay_c)
                cmt = {}

                # 댓글 id
                e = cmt_e.find_element_by_xpath('./..')
                cmt['comment_id'] = e.get_attribute('data-seq')
                # 대댓글
                e = cmt_e.find_element_by_xpath('./../..')
                is_reply = e.get_attribute('class') == 'child-reply'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ''
                else:
                    cmt['parent_comment_id'] = parent_comment_id

                # 댓글 nickname :
                e = cmt_e.find_element_by_xpath('.//li[@class="writer-name"]//span')
                cmt['nickname'] = e.text.strip()

                # 댓글 작성 시각
                e = cmt_e.find_element_by_xpath('.//span[@class="modify-time"]')
                cmt['create_ts'] = e.text.strip() + ':00'

                # 댓글 좋아요 / 싫어요 :
                e = cmt_e.find_element_by_xpath('./..//span[@class="good-count"]')
                cmt['like'] = int(e.text.strip())
                e = cmt_e.find_element_by_xpath('./..//span[@class="bad-count"]')
                cmt['dislike'] = int(e.text.strip())

                # 댓글 내용
                e = cmt_e.find_element_by_xpath('./..//div[@data-content]')
                self.move_to_element(e)
                cmt['contents'] = e.text

                cmt['comment_img_url'] = []
                cmt['comment_img'] = []

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
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self._screenshot(msg_capture_f)

                # self.full_screenshot(msg_capture_f)

            e_ab = self.get_by_xpath('//div[@class="article_wrap"]', timeout=1)
            # 1) 게시글 내용 :
            e = e_ab.find_element_by_xpath('.//div[2]//div[@class="view_cont"]')
            msg['contents'] = e.text.strip()

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
                    msg['image_url_list'].append(sub_e_url)

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []

            # msg['comment_list'] = []

            self.switch_to_iframe('//iframe[@title="라이브리 - 댓글영역"]')
            e_i = self.get_by_xpath('//*[@id="wrapper"]')
            # 댓글 수
            try:
                e = e_i.find_element_by_xpath('.//div[6]//div[1]//span')
                msg['num_comments'] = int(e.text.strip())
            except:
                msg['num_comments'] = 0
            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return

            # 댓글
            self.get_comment(msg)

            # 게시글 댓글 개수
            msg['num_comments'] = len(msg['comment_list'])

        except Exception as err:
            raise
        finally:
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
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="list_type"]/ul')
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
                    e = self.get_by_xpath('//div[@class="list_type"]/ul')
                    es = e.find_elements_by_xpath('./li')
                    ea = es[i]

                    # 2) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('Id=')[2]
                    msg['article_id'] = v
                    # 2) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 3) 제목: title
                    e_t = ea.find_element_by_xpath('.//span[@class="text"]/strong')
                    msg['title'] = e_t.text.strip()
                    # 4) 작성 시간
                    e = ea.find_element_by_xpath('.//span[@class="source"]/span[1]')
                    msg['create_ts'] = e.text.strip().replace('-', '.') + ' 00:00:00'
                    # 5) 작성자
                    e = ea.find_element_by_xpath('.//span[@class="source"]/span[2]')
                    msg['author'] = e.text.strip()

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
            e = self.get_by_xpath('//div[@class="article_wrap"]')
            ple = e.find_element_by_xpath('.//div[@class="paging"]')
            e = ple.find_element_by_xpath('.//span[@class="num on"]')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('.//a'):
                # 여기 다시 하기 다음으로 넘어가는 거 안 된다
                if pa.get_attribute('class') == 'next':
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.get_attribute('class') == 'last':
                    continue
                elif pa.get_attribute('class') == 'first':
                    continue
                elif pa.get_attribute('class') == 'prev':
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
    with KoreaNewsSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'korea_news.yaml'
    do_start(config_f=_config_f)
