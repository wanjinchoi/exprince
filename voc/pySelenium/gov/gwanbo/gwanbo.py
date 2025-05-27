"""
====================================
 :mod:`gov/ GwanBo : 오늘 관보
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
#  * [2023/02/27]
#     - 팝업창 닫기 추가
#  * [2023/01/31]
#     - 사이트 UI 변경
#  * [2022/06/24]
#     - 게시글 오픈시 자동으로 다운로드 받는 케이스가 존재
#  * [2022/06/14]
#     - 게시글 url 추가
#     - 게시글 url을 attachment_url에도 추가
#     - 첨부파일 내용을 본문(contents)에 추가
#     - 게시글 누르면 pdf가 같이 다운받아짐.
#  * [2022/02/25]
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
# pdf
from io import StringIO
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser


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

class GwanBo(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'GwanBo.log'),
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
        self.logger.info(f'Starting GwanBo Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색창 비워준 이후, 날짜 입력
        self.get_by_xpath('//div[@class="inner"]/input').clear()
        # 닐짜 입력
        e = self.get_by_xpath('//div[@class="inner"]/input')
        self.send_keys(e, self.config['params']['site']['stop_article_older_than']['datetime'].partition(' 00:')[0])

        # 검색 단추
        e = self.get_by_xpath('//div[@class="inner"]/button[1]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=3)

    # ========================================================================
    def get_contents(self, pdf_file):
        output_string = StringIO()
        with open(pdf_file, 'rb') as in_file:
            parser = PDFParser(in_file)
            doc = PDFDocument(parser)
            rsrcmgr = PDFResourceManager()
            device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
            interpreter = PDFPageInterpreter(rsrcmgr, device)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)

        return output_string.getvalue()

    # ========================================================================
    def get_article(self, msg, ndx, set1, down_f):
        try:

            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            # 게시글 url
            msg['article_url'] = self.driver.current_url
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.full_screenshot(msg_capture_f)

            e_ab = self.get_by_xpath('//nav[@id="cbp-hrmenu"]', timeout=1)

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []

            e_down = e_ab.find_element_by_xpath('//ul[@class="tool-wrap"]/li/a[@title="다운로드"]')
            sub_k_name = e_down.get_attribute('id')
            # 게시글 누르기전에 가져오는데 혹시 없다면 안에서 다운로드 버튼을 누름.
            if not down_f:
                set1 = set(os.listdir(self.get_download_path()))
                self.safe_click(e_down)
                self.implicitly_wait(after_wait=1)
                try:
                    self.driver.switch_to.alert.accept()
                except:
                    download_wait(self.get_download_path(), 30)
            set2 = set(os.listdir(self.get_download_path()))
            if sub_k_name != list(set1 ^ set2)[0]:
                sub_k_name = list(set1 ^ set2)[0]
            if len(list(set1 ^ set2)) != 1:
                return
            msg['attachment_name'].append(sub_k_name)
            msg['attachment_url'].append(msg['article_url'])
            src = "\\".join([self.get_download_path(), sub_k_name])
            dst = "\\".join([self.config['target']['folder'], msg['article_id'], sub_k_name])
            # 파일 이동
            shutil.move(src, dst)
            # 혹시 다운로드 폴더에 남아있다면 제거 하기위함.
            if os.path.isfile(dst) and os.path.isfile(src):
                os.remove(src)
            # 게시글 본문이 없기때문에 pdf 파일에서 text 추출함
            msg['contents'] = self.get_contents(dst)

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
    def get_page(self):
        try:
            self.cur_page += 1
            self.switch_to_window(0)
            # 게시글수
            e_a = self.get_by_xpath('//li[@class="on"]/a/span', timeout=1)
            if e_a.text == '0':
                self.logger.error('Stop crawling because there are no articles!!')
                self.is_done = True
                return
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="table_contents_list"]', timeout=1)
            es = e.find_elements_by_xpath('.//ul[@class="list"]/li')

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
                    e = self.get_by_xpath('//div[@class="table_contents_list"]')
                    es = e.find_elements_by_xpath('.//ul[@class="list"]/li')
                    ea = es[i]

                    # 1) 분류 :
                    e = ea.find_element_by_xpath('./span')
                    e_c = e.get_attribute('onclick')
                    msg['board_name'] = e_c.rpartition("',")[0].rpartition("',")[0].rpartition(",'")[2]
                    # 2) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./span')
                    a_url = e_url.get_attribute('onclick')
                    v = a_url.partition('tocId=')[2].partition('&')[0]
                    msg['article_id'] = v
                    # 3) 작성자
                    # msg['author'] = ""
                    # 4) 제목: title
                    e_t = ea.find_element_by_xpath('./span')
                    msg['title'] = e_t.text.strip()
                    # 5) 작성 시간
                    msg['create_ts'] = self.config['params']['site']['stop_article_older_than']['datetime']
                    # 클릭하는 순간 pdf도 같이 다운받음....  추후 사이트 변경될 수 있을듯.
                    set1 = set(os.listdir(self.get_download_path()))
                    self.safe_click(e_url)
                    download_wait(self.get_download_path(), 30)
                    set2 = set(os.listdir(self.get_download_path()))
                    down_f = list(set1 ^ set2)
                    self.move_to_element(e_t)
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1, set1, down_f)
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

                # 하루치 전부 읽음
                # if self.stop_article_older_than(msg):
                #     if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                #         shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                #     self.is_done = True  # 동시성 런타임
                #     break
                # self.save_attachment(msg)
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
        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            self.switch_to_window(0)
            # 페이지 목록
            e = self.get_by_xpath('//div[@id="contBoard"]')
            ple = e.find_element_by_xpath('.//div[@class="paginate1"]')
            e = ple.find_element_by_xpath('.//strong')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('class') == 'next':
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.get_attribute('class') in ['nextE', 'preE', 'pre']:
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
                self.is_done = True
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
    with GwanBo(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
def main(**kwargs):
    with GwanBo(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'gwanbo.yaml'
    do_start(config_f=_config_f)
