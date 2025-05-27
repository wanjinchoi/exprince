"""
====================================
 :mod:`public_institutions/ftc`
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
#  * [2023/07/25]
#     - 입법/행정예고 수정 (작성일 부분 수정)
#  * [2022/07/04] MinJung
#     - 입법/행정예고 수정 (게시글 url 삭제, 게시글 id의 xpath 변경)
#  * [2022/01/18]
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
from alabslib.selenium import Keys
# from bs4 import BeautifulSoup


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
class FtcSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'FtcSearch.log'),
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
        self.logger.info(f'Starting Ftc Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 내용으로 검색
        if self.config['params']['site']['search_filter'] in ['내용', '제목']:
            e = self.get_by_xpath('//div[@class="bbs_search"]')
            e_s = e.find_elements_by_xpath('.//select[@name="searchKey"]/option')
            for e_f in e_s:
                if e_f.text.find(self.config['params']['site']['search_filter']) >= 0:
                    self.safe_click(e_f)
                    break
            self.implicitly_wait(after_wait=1)

        # 검색어 입력
        e = self.get_by_xpath('//input[@name="searchVal"]')
        self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
        # # 검색 단추
        # e = self.get_by_xpath('//div[@class]/input[@type="submit"]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

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
                self.full_screenshot(msg_capture_f)

            e_ab = self.get_by_xpath('//tbody', timeout=1)
            e_a = e_ab.find_elements_by_xpath('./tr')
            for e_li in e_a:
                if e_li.text.find('전화번호') >= 0:
                    msg['contact_number'] = e_li.text.partition('전화번호')[2].strip()
                elif e_li.text.find('조회') >= 0:
                    view_count = e_li.text.partition('조회')[2]
                    msg['view_count'] = int(view_count)
                    if e_li.text.find('등록일') >= 0:
                        ex_ts = e_li.text.partition('조회')[0].partition('등록일')[2]
                        msg['create_ts'] = ex_ts.replace(' ', '').replace('-', '.').strip() + " 00:00:00"

            if '입법' in self.config['params']['site']['site_board']:
                # 게시글 url - 입법/행정예고는 없음
                pass
            else:
                # 게시글 url - 보도, 해명
                e = e_ab.find_element_by_xpath('//p[@class="warning_text"]')
                msg['article_url'] = e.text.partition(' : ')[2]

            # 게시글 내용
            e = e_ab.find_element_by_xpath('.//td[@title="내용"]')
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

            # 첨부파일 href의 값이 javascript로 되어있음
            inner_html = e_ab.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            if inner_html.find('view_attach') > 0 or inner_html.find('첨부파일 다운로드') > 0:
                if inner_html.find('view_attach') > 0:
                    attachs = e_ab.find_elements_by_xpath('.//ul[@class="view_attach"]/li/a')
                else:
                    attachs = e_ab.find_elements_by_xpath('.//a[@href]')
                for k, sub_k in enumerate(attachs):
                    if sub_k.get_attribute('title') == '바로보기':
                        continue
                    self.move_to_element(sub_k)
                    msg['attachment_url'].append(sub_k.get_attribute('href'))
                    sub_k_name = sub_k.find_element_by_xpath('./..').text.rpartition(' (')[0]
                    # 다운로드폴더에 다운 받음
                    set1 = set(os.listdir(self.get_download_path()))
                    self.safe_click(sub_k)
                    self.implicitly_wait(after_wait=1)
                    download_wait(self.get_download_path(), 30)
                    set2 = set(os.listdir(self.get_download_path()))
                    # 실제로 다운 받는 파일의 이름이 다를수 있음.
                    if sub_k_name != list(set1 ^ set2)[0]:
                        sub_k_name = list(set1 ^ set2)[0]
                    msg['attachment_name'].append(sub_k_name)
                    src = "\\".join([self.get_download_path(), sub_k_name])
                    dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
                    # 파일 이동
                    shutil.move(src, dst)

            msg['num_comments'] = 0
            # msg['comment_list'] = []

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            self.driver.back()
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
            e = self.get_by_xpath('//table[@class="bbs_default list"]')
            es = e.find_elements_by_xpath('./tbody/tr')

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
                    e = self.get_by_xpath('//table[@class="bbs_default list"]')
                    es = e.find_elements_by_xpath('./tbody/tr')
                    self.move_to_element(es[i])
                    ea = es[i]
                    e_a = ea.find_elements_by_xpath('./td')
                    if '입법' in self.config['params']['site']['site_board']:
                        # 게시글 id : article_id - 입법/행정예고
                        e_u = ea.find_element_by_xpath('.//td[@class="subject"]/span/a')
                        sub_e_url = e_u.get_attribute('onclick')
                    else:
                        # 게시글 id : article_id - 보도, 해명
                        e_u = ea.find_element_by_xpath('.//td[@class="subject"]/a')
                        sub_e_url = e_u.get_attribute('href')
                    e_url = sub_e_url.partition("('")[2].rpartition("')")[0]
                    msg['article_id'] = e_url.strip()
                    # if msg['article_id'] in self.output['article_list'][-1]:
                    #     break
                    if e_a[0].text == '1':
                        self.is_done = True
                    for ea_li in e_a:
                        if not ea_li.get_attribute('data-cell-header'):
                            continue
                        # elif ea_li.get_attribute('data-cell-header').find('구분') >= 0:
                        #     msg['sortation'] = ea_li.text.strip()
                        elif ea_li.get_attribute('data-cell-header').find('제목') >= 0:
                            msg['title'] = ea_li.text.strip()
                        elif ea_li.get_attribute('data-cell-header').find('담당부서') >= 0:
                            msg['author'] = ea_li.text.strip()
                        elif ea_li.get_attribute('data-cell-header').find('등록일') >= 0:
                            msg['create_ts'] = ea_li.text.replace('-', '.') + ' 00:00:00'

                    # href안에 javascript:doView('9329');로 되어 있음.
                    # self.safe_click(e_t)
                    e_t = ea.find_element_by_xpath('.//td[@class="subject"]')
                    e_t.find_element_by_link_text(e_t.text).click()
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
            ple = self.get_by_xpath('//span[@class="page_wrap"]')
            self.move_to_element(ple)
            pages = ple.find_elements_by_xpath('./*')
            is_on = False
            for i, pa in enumerate(pages):
                if pa.tag_name == 'strong' and i+1 == len(pages):
                    next_page = self.get_by_xpath('//span[@class="page_btn next_group"]/a[@class="next"]')
                    self.safe_click(next_page)
                    self.implicitly_wait(after_wait=1)
                    return
                elif pa.tag_name == 'strong':
                    is_on = True
                    continue
                if is_on:
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
            file = requests.get(attach_url, stream=True)
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
            # self.search()
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
    with FtcSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'ftc.yaml'
    do_start(config_f=_config_f)
