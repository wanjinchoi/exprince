"""
====================================
 :mod:`gov/ law`
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
#  * [2023/04/03]
#     - 수집 영역 변경(제정·개정이유)
#  * [2023/02/07]
#     - 수집 이미지 alt(필터링) 추가
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
class LawSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'LawSearch.log'),
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
        self.logger.info(f'Starting Law Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # # 검색어 입력
        # e = self.get_by_xpath('//div[@class="srch_inp"]/input')
        # self.send_keys(e, self.config['params']['site']['search'])
        #
        # # 검색 단추
        # e = self.get_by_xpath('//div[@class="srch_bx"]//button[@class="btn_srch"]',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

        # 최신 법령 클릭하기 : 처음에 안 눌러주면 형식이 자꾸 변한다
        e = self.get_by_xpath('//div[@class="sub_menu"]/div/input[5]')
        self.safe_click(e)
        # 시행 법령 클릭하기
        e = self.get_by_xpath('//ul[@class="sub_tab"]/li[2]')
        self.safe_click(e)
        # 새창(목록) 클릭하기
        e = self.get_by_xpath('//p[@id="dpInSchDiv1"]/input')
        self.safe_click(e)

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
            e = self.get_by_xpath('//div[@class="l_bx"]/a[@id="lsRvsDocInfo"]', cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            self.switch_to_window(1)
            if self.config['params']['site']['capture_article']:
                # save
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.full_screenshot(msg_capture_f)


            e_ab = self.get_by_xpath('//div[@id="bodySideContent"]', timeout=1)

            # 1) 게시글 내용 :
            e = e_ab.find_element_by_xpath('.//div[@id="rvsConBody"]')
            msg['contents'] = e.text.strip()

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('img') > 0:
                for j, sub_e in enumerate(e.find_elements_by_tag_name('img')):
                    # 버튼 img 까지 가지고 와서 제한 두기
                    if sub_e.get_attribute('alt') in ['연혁', '조문체계도버튼', '위임행정규칙', '규제', '판례', '닫기', '별표',
                                                      '파일 다운로드', '부칙보기', '관련규제버튼', '위임행정규칙버튼', '부칙', '법령별표 한글주소', '생활법령버튼'
                                                      ,'파일 다운로드hwp','파일 다운로드hwpx','파일 다운로드pdf','제정·개정이유보기', '전체 제정·개정문보기', '제정·개정문보기', '제정·개정이유보기']:
                        continue
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 첨부파일
            inner_html = e_ab.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            if inner_html.find('pconfile pb30 pcf_sec01') > 0:
                for k, sub_k in enumerate(e_ab.find_elements_by_xpath('.//ul[@class="pconfile pb30 pcf_sec01"]/li/span/a[4]')):
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('href')
                    msg['attachment_url'].append(sub_k_url)
                    sub_k_n = sub_k.find_element_by_xpath('./../a[3]')
                    sub_k_name = sub_k_n.text.partition('<')[0].strip() + '.hwp'
                    msg['attachment_name'].append(sub_k_name)

            # 파일 전체 저장
            # 저장 버튼
            e = self.get_by_xpath('//div[@class="r_bx"]/a[5]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # hwp 파일 저장
            e_file = self.get_by_xpath('//label[@for="saveHWP"]')
            self.safe_click(e_file)
            self.implicitly_wait(after_wait=1)
            # 저장 클릭
            # e = self.get_by_xpath('//div[@id="infoSaveLayerLoding"]//div[@class="ly_btn_bx"]/a[1]')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)
            # # 부칙 저장 설정 클릭
            # e_file = self.get_by_xpath('//div[@class="ui-dialog ui-widget ui-widget-content ui-corner-all ui-draggable"]')
            # e_f = e_file.find_element_by_xpath('.//form[@id="outPutFrm"]//div[@class="stab"]/a[2]')
            # self.safe_click(e_f)
            # self.implicitly_wait(after_wait=1)
            # e_fa = e_file.find_element_by_xpath('.//form[@id="outPutFrm"]//div[@id="lsOutArUl"]/ul/li[1]/input')
            # self.safe_click(e_fa)
            # self.implicitly_wait(after_wait=1)
            # # 별표 저장 설정 클릭
            # e_f = e_file.find_element_by_xpath('.//form[@id="outPutFrm"]//div[@class="stab"]/a[3]')
            # self.safe_click(e_f)
            # self.implicitly_wait(after_wait=1)
            # e_fa = e_file.find_element_by_xpath('.//form[@id="outPutFrm"]//div[@id="lsOutBylUl"]/ul/li[1]/input')
            # self.safe_click(e_fa)
            # self.implicitly_wait(after_wait=1)
            # # pdf 파일 선택
            # e_pdf = e_file.find_element_by_xpath('.//div[@id="noticeDiv"]/div[@class="inctn5"]/div[2]/input')
            # self.safe_click(e_pdf)
            # self.implicitly_wait(after_wait=1)

            # 다운
            set1 = set(os.listdir(self.get_download_path()))
            e = self.get_by_xpath('//div[@id="infoSaveLayerLoding"]//div[@class="ly_btn_bx"]/a[1]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            download_wait(self.get_download_path(), 30)
            set2 = set(os.listdir(self.get_download_path()))
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

            # 페이지 테이블 구해오기
            e = self.get_by_xpath('.//div[@id="viewHeightDiv"]/table/tbody')
            es = e.find_elements_by_xpath('./tr')

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
                    e = self.get_by_xpath('.//div[@id="viewHeightDiv"]/table/tbody')
                    es = e.find_elements_by_xpath('./tr')
                    ea = es[i]

                    # 0) 게시글 번호 : article_number
                    # e = ea.find_element_by_xpath('./td[1]')
                    # msg['article_number'] = e.text.strip()
                    # 1) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./td/a')
                    a_url = e_url.get_attribute('onclick')
                    v = a_url.partition("('")[2].partition("',")[0]
                    msg['article_id'] = v
                    # 2) 제목: title
                    e = ea.find_element_by_xpath('./td/a')
                    msg['title'] = e.text.strip()
                    # 3) 작성 시간
                    e = ea.find_element_by_xpath('./td[3]')
                    e_ts = e.text.strip().replace(' ', '')
                    date_e = e_ts.split('.')
                    ts = str(datetime.date(int(date_e[0]), int(date_e[1]), int(date_e[2]))).replace('-','.')
                    msg['create_ts'] = ts + ' 00:00:00'
                    # # 4) 분야 / 종류
                    # e = ea.find_element_by_xpath('./td[4]/p')
                    # msg['sortation'] = e.text.strip()
                    # 5) 공포번호
                    # e = ea.find_element_by_xpath('./td[5]/p')
                    # msg['number'] = e.text.strip()
                    # 6) 작성자 : 공백인 경우가 있다
                    try:
                        e = ea.find_element_by_xpath('./td[8]/p')
                        msg['author'] = e.text.strip()
                    except:
                        msg['author'] = ''

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
            ple = self.get_by_xpath('.//*[@id="WideListDIV"]/div[1]/div[5]')
            e = ple.find_element_by_xpath('.//ol/li[@class]')
            is_on = int(e.text.strip())
            self.move_to_element(ple)
            ple_xpath = './/li/a' \
                        '|.//a/img'
            for pa, sub_pa in enumerate(ple.find_elements_by_xpath(ple_xpath)):
                if sub_pa.get_attribute('alt') == '다음으로':
                    self.safe_click(sub_pa)
                    self.implicitly_wait(after_wait=1)
                    return
                elif sub_pa.get_attribute('alt') == '마지막으로':
                    continue
                elif sub_pa.get_attribute('alt') == '처음으로':
                    continue
                elif sub_pa.get_attribute('alt') == '이전으로':
                    continue
                elif int(sub_pa.text.strip()) > is_on:
                    self.safe_click(sub_pa)
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
    with LawSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'law.yaml'
    do_start(config_f=_config_f)
