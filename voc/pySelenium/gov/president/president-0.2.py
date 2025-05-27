"""
====================================
 :mod:`gov/president`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for president (국민청원)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/05/22]
#     - meta json 포멧 맞추기
#  * [2022/03/28]
#     - 1차 버전 완료


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
import re
import requests
import calendar
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from alabslib.selenium import Keys
from alabslib.selenium import Select
from datetime import date

from dateutil.relativedelta import relativedelta

################################################################################
class PresidentSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'PresidentSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        self.config['params']['site']['search'] = self.config['params']['site']['search'].strip()

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
        self.logger.info(f'Starting President Crawling... with '
                         f'config:\n{out_config}')

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

            # 게시글 URL
            msg['article_url'] = self.driver.current_url

            # 작성자
            try:
                e = self.get_by_xpath('//ul[@class="petitionsView_info_list"]/li[4]')
                author = e.text.strip().split('\n')
            except:
                msg['author'] = ''
            else:
                msg['author'] = author[-1]

            # 내용
            try:
                contents = self.get_by_xpath('//div[@class="View_write"]')
            except:
                msg['contents'] = ''
            else:
                msg['contents'] = contents.text.strip()

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self._screenshot(msg_capture_f)

            # 본문 안의 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = contents.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = contents.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    msg['image_list'].append(f'{x}.png')
                    msg['image_url_list'].append(img_src_url)

            # 첨부파일
            msg['attachment_link'] = []
            try:
                e = self.get_by_xpath('//ul[@class="View_write_link"]')
                afs = e.find_elements_by_xpath('./li/a')
            except:
                pass
            else:
                for af in afs:
                    attachment_link = af.get_attribute('href')
                    msg['attachment_link'].append(attachment_link)
        except Exception as err:
            raise
        finally:
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

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//div[@class="PG_contens_pd"]')
            bil = [bi for bi in e.find_elements_by_class_name("PG_contens_pd_list")]
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
                    'searvice': self.config['params']['site']['service'],
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
                    'attachment_link': [],
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
                    e = self.get_by_xpath('//div[@class="PG_contens_pd"]')
                    ail = [bi for bi in e.find_elements_by_class_name("PG_contens_pd_list")]
                    bi = ail[i]

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('./a/h2')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 id
                    if msg['title'] == '':
                        msg['article_id'] = ''
                    else:
                        article_id = bi.find_element_by_xpath('./a').get_attribute('href')
                        msg['article_id'] = re.search('/(\d+)$', article_id).group(1)

                    items = bi.find_elements_by_tag_name('span')
                    # 등록일
                    try:
                        create_ts = items[0].text.strip()
                    except:
                        msg['create_ts'] = '0000.00.00 00:00:00'
                    else:
                        msg['create_ts'] = create_ts.replace('-', '.') + ' 00:00:00'

                    # 청원인원
                    try:
                        num_comments = items[2].text.strip()
                    except:
                        msg['num_comments'] = ''
                    else:
                        msg['num_comments'] = int(num_comments.replace(',',''))

                    # 게시글 본문으로 이동
                    title_e= bi.find_element_by_xpath('./a')
                    self.move_to_element(title_e)
                    self.get_article(title_e, msg, i+1)

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
            try:
                ple = self.get_by_xpath('//div[@class="paging"]/div[@class="p_wrap"]')
                pa_list = ple.find_elements_by_xpath('.//a')
            except:
                # 페이지가 없는 경우
                self.is_done = True
                return

            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.get_attribute('class') == 'on':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'on':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 다음 페이지 클릭후의 현재 페이지 번호 구하기
                    nple = self.get_by_xpath('//div[@class="paging"]/div[@class="p_wrap"]')
                    for npa in nple.find_elements_by_xpath('.//a'):
                        if npa.get_attribute('class') == 'on':
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
                        urlretrieve(sub_e_url, article_img_p)
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

        # 첨부파일 저장
        cwd = os.getcwd()
        crawling_dir = self.get_safe_path(self.config['target']['folder'], article['article_id'])
        os.chdir(crawling_dir)
        for x, download_file in enumerate(article['attachment_url']):
            try:
                save_loc_fn = self.get_safe_path(crawling_dir, article['attachment_name'][x])
                response = requests.get(article['attachment_url'][x], verify=False)
            except Exception as e:
                pass
            else:
                count = 0
                data = response.content
                with open(save_loc_fn, "wb") as output_file:
                    output_file.write(data)
                while not os.path.isfile(article['attachment_name'][x]):
                    self.implicitly_wait(after_wait=1)
                    count += 1
                    if count > 20:  # 20초 이상 지연시 실패로 간주하고 빠져나감
                        self.logger.error(f'save_article: {x, download_file} download failed')
                        break
                response.close()
        os.chdir(cwd)

        # json 파일 생성
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

            # 국민청원 및 제안 선택
            select = Select(self.driver.find_element_by_id("color"))
            select.select_by_value('petitions')
            self.implicitly_wait(after_wait=1)

            # 검색 날짜 범위 설정
            today = date.today()
            delta_month = datetime.timedelta(days=calendar.monthrange(today.year, today.month - 1)[1])
            a_month_before = today - delta_month

            # a_month_before = date.today() - relativedelta(months=1) + relativedelta(days=1)
            start_date = str(a_month_before).replace('-', '/')
            e = self.get_by_xpath('//*[@id="start_Date"]')
            self.send_keys(e, start_date + "\n")

            end = str(date.today())
            end_date = end.replace('-', '/')
            e = self.get_by_xpath('//*[@id="end_Date"]')
            self.send_keys(e, end_date + "\n")

            # 검색어 입력
            e = self.get_by_xpath('//*[@id="query"]')
            self.send_keys(e, '"' + self.config['params']['site']['search'] + '"' +  "\n")
            self.implicitly_wait(after_wait=1)

            # 검색결과 판단 및 진행여부 선택
            e = self.get_by_xpath('//*[@id="contents"]/div[2]/div/div[1]/span[2]')
            search_result_num = re.search('\((.+?)건\)', e.text.strip()).group(1)
            if search_result_num == '0':
                return

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
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
    with PresidentSearch(kwargs['config_f']) as ws:
        ws.start()

################################################################################
if __name__ == '__main__':
    _config_f = 'president.yaml'
    do_start(config_f=_config_f)
