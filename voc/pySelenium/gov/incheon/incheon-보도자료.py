"""
====================================
 :mod:`gov/incheon`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for incheon (인천광역시청)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/03/06]
#     - Content가 없는 경우 넘어가는 로직 추가
#  * [2022/03/21]
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

from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Select, Keys


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
class IncheonSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'IncheonSearch.log'),
                            logsize=1024*1024*10)
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
        self.logger.info(f'Starting Incheon Crawling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
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

            e = self.get_by_xpath('//div[@class="board-view-meta"]')
            se = e.find_elements_by_xpath('./dl')

            # 작성자
            try:
                author = se[0].find_element_by_xpath('./dd')
            except:
                msg['author'] = ''
            else:
                if author.text.strip() == '':
                    msg['author'] = ''
                else:
                    msg['author'] = author.text.strip().split('/')[-1].split('(')[0].strip()

            # 등록일
            try:
                create_ts = se[1].find_element_by_xpath('./dd')
            except:
                msg['create_ts'] = '0000.00.00 00:00:00'
            else:
                if create_ts.text.strip() == '':
                    msg['create_ts'] = '0000.00.00 00:00:00'
                else:
                    msg['create_ts'] = create_ts.text.strip().replace('-', '.') + ' 00:00:00'

            # 조회수
            try:
                view_count = se[2].find_element_by_xpath('./dd')
            except:
                msg['view_count'] = ''
            else:
                if view_count.text.strip() == '':
                    msg['view_count'] = ''
                else:
                    msg['view_count'] = int(view_count.text.strip())

            # 내용
            try:
                contents = self.get_by_xpath('//div[@class="board-view-contents cms_content"]')
            except:
                msg['contents'] = ''
            else:
                msg['contents'] = contents.text.strip()

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot(msg_capture_f)

            # 본문 안의 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            try:
                inner_html = contents.get_attribute('innerHTML')  # 이미지 추출용
            except:
                pass
            else:
                img_list = contents.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    msg['image_list'].append(f'{x}.png')
                    msg['image_url_list'].append(img_src_url)

            # 첨부파일
            msg['attachment_name'] = []
            msg['attachment_url'] = []
            try:
                e = self.get_by_xpath('//div[@class="board-view board-item-group-wrap"]')
                se = e.find_elements_by_xpath('.//div[@class="board-item-group"]')
            except:
                pass
            else:
                for group in se:

                    if '공공누리' in group.text.strip() :
                        continue
                    else:
                        try:
                            af_se = group.find_element_by_xpath('.//div[@class="file-preview-down-group"]')
                            afs = af_se.find_elements_by_xpath('./p')
                        except:
                            pass
                        else:
                            for af in afs:

                                tag_a = af.find_elements_by_xpath('./a')
                                attachment_name = af.find_element_by_xpath('./span').text.strip()
                                if '미리보기' in af.text.strip():
                                    attachment_url = tag_a[1].get_attribute('href')
                                else:
                                    attachment_url = tag_a[0].get_attribute('href')

                                msg['attachment_name'].append(attachment_name)
                                msg['attachment_url'].append(attachment_url)

        except Exception as err:
            raise
        finally:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])

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
            e = self.get_by_xpath('//div[@class="board-blog-list"]/ul')
            bil = [bi for bi in e.find_elements_by_xpath('./li')]
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
                    e = self.get_by_xpath('//div[@class="board-blog-list"]/ul')
                    ail = [bi for bi in e.find_elements_by_xpath('./li')]
                    bi = ail[i]

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('.//strong[@class="subject"]')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        url = bi.find_element_by_xpath('./a')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = url.get_attribute('href')

                    # 게시글 id
                    if msg['article_url'] == '':
                        msg['article_id'] = ''
                    else:
                        msg['article_id'] = re.search(r'DOM_(\d+)&', msg['article_url']).group(1)

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
                ple = self.get_by_xpath('//div[@class="pagination"]')
                pa_list = ple.find_elements_by_xpath('./a')
            except:
                # 페이지가 없는 경우
                self.is_done = True
                return

            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.get_attribute('class') == 'active':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'active':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 다음 페이지 클릭후의 현재 페이지 번호 구하기
                    nple = self.get_by_xpath('//div[@class="pagination"]')
                    for npa in nple.find_elements_by_xpath('./a'):
                        if npa.get_attribute('class') == 'active':
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

            # 인천소식 클릭
            e = self.get_by_xpath('//*[@id="gnbmain"]/li[1]/a')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 보도/해명 클릭
            e = self.get_by_xpath('//*[@id="snb"]/div/div[2]/nav/ul/li[3]/a')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 보도자료 클릭
            e = self.get_by_xpath('//*[@id="snb"]/div/div[2]/nav/ul/li[3]/div/ul/li[1]/a')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.implicitly_wait(after_wait=1) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
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
    with IncheonSearch(kwargs['config_f']) as ws:
        ws.start()

################################################################################
if __name__ == '__main__':
    _config_f = 'incheon.yaml'
    do_start(config_f=_config_f)
