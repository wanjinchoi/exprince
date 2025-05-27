"""
====================================
 :mod:`mof`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for mof (해양수산부)
"""
# Authors
# ===========
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/06/01]
#     - 사이트 UI 변경으로 next_page 수정
#  * [2023/03/23]
#     - 변경된 URL로 인한 사이트 UI 변경
#  * [2023/02/12]
#     - 게시글 이미지 가져오는 부분 수정
#  * [2022/06/10] Kyobong An
#     - 보도자료 첨부파일 xpath가 변경됨 추가완료
#  * [2022/04/04] Kyobong An
#     - 사이트 업데이트로 인한 로직 수정
#  * [2022/03/10]
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
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
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
class MofSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'MofSearch.log'),
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
        self.logger.info(f'Starting Mof Crawling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        self.safe_click(title_e)
        self.implicitly_wait(after_wait=1)

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 내용
            msg['contents'] = ''
            try:
                contents = self.get_by_xpath('//div[@class="sub-content"]/div[1]/div[2]')
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
                    e_heads = self.driver.find_elements_by_xpath('//button[@class="top-btn action"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_head)
                    self.full_screenshot(msg_capture_f)

            # 본문 안의 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = contents.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = contents.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{x}.png')
                    img.screenshot(cmt_img_f)
                    msg['image_url_list'].append(img_src_url)
                    msg['image_list'].append(f'{x}.png')

            # 첨부파일
            msg['attachment_name'] = []
            msg['attachment_url'] = []
            try:
                e = self.get_by_xpath('//div[@class="board-wrap"]/div[1]//ul[@class="attach-list"]')
                afs = e.find_elements_by_xpath('./li/a[1]')
            except:
                pass
            else:
                # for af in afs:
                #     attachment_name = af.text.strip()
                #     attachment_url = af.get_attribute('href')
                #
                #     msg['attachment_name'].append(attachment_name)
                #     msg['attachment_url'].append(attachment_url)
                for sub_k in afs:
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('href')
                    sub_k_n = sub_k.text.strip()
                    sub_k_name = re.sub(r'[\/:*?"<>|]', '', sub_k_n)
                    # 다운로드폴더에 다운 받음
                    set1 = set(os.listdir(self.get_download_path()))
                    self.safe_click(sub_k)
                    self.implicitly_wait(after_wait=1)
                    download_wait(self.get_download_path(), 10)
                    set2 = set(os.listdir(self.get_download_path()))
                    # 실제로 다운 받는 파일의 이름이 다를수 있음.
                    if sub_k_name != list(set1 ^ set2)[0]:
                        sub_k_name = list(set1 ^ set2)[0]
                    msg['attachment_url'].append(sub_k_url)
                    msg['attachment_name'].append(sub_k_name)
                    src = "\\".join([self.get_download_path(), sub_k_name])
                    dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
                    # 파일 이동
                    shutil.move(src, dst)

        except Exception as err:
            raise
        finally:
            self.driver.back()

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
            e = self.get_by_xpath('//div[@class="board-wrap"]/div[2]/table/tbody')
            bil = [bi for bi in e.find_elements_by_xpath('./tr')]
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
                    e = self.get_by_xpath('//div[@class="board-wrap"]/div[2]/table/tbody')
                    ail = [bi for bi in e.find_elements_by_xpath('./tr')]
                    bi = ail[i]

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('./td[2]')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        url = bi.find_element_by_xpath('./td[2]/a').get_attribute('href')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = url

                    # 게시글 id
                    try:
                        id = bi.find_element_by_xpath('./td[1]')
                    except:
                        msg['article_id'] = ''
                    else:
                        msg['article_id'] = id.text.strip()
                    # try:
                    #     href = bi.find_element_by_xpath('./td[2]/a').get_attribute('href')
                    # except:
                    #     msg['article_id'] = ''
                    # else:
                    #     article_id = re.search(r'docSeq=(\d+)\&',  href).group(1)
                    #     if article_id == '':
                    #         msg['article_id'] = ''
                    #     else:
                    #         msg['article_id'] = article_id.strip()

                    # 작성자
                    try:
                        author = bi.find_element_by_xpath('./td[3]')
                    except:
                        msg['author'] = ''
                    else:
                        if author.text.strip() == '':
                            msg['author'] = ''
                        else:
                            msg['author'] = author.text.strip()

                    # 등록일
                    try:
                        create_ts = bi.find_element_by_xpath('./td[5]')
                    except:
                        msg['create_ts'] = '0000.00.00 00:00:00'
                    else:
                        if create_ts.text.strip() == '':
                            msg['create_ts'] = '0000.00.00 00:00:00'
                        else:
                            msg['create_ts'] = create_ts.text.rstrip('.').replace(' ', '') + " " + "00:00:00"
                    msg['create_ts'] = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                    # 조회수
                    try:
                        view_count = bi.find_element_by_xpath('./td[6]')
                    except:
                        msg['view_count'] = 0
                    else:
                        if view_count.text.strip() == '':
                            msg['view_count'] = 0
                        else:
                            msg['view_count'] = int(view_count.text.strip())

                    # 게시글 본문으로 이동
                    title_e = bi.find_element_by_xpath('./td[2]/a')
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
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="paging-wrap"]')
            is_current = False
            for pa in ple.find_elements_by_xpath('./a'):
                if pa.get_attribute('title') == '현재 페이지':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
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
                        # article['image_list'].append(f'{j}.png') 왜 들어가 있는지를 이해 하지 못함
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

        # # 첨부파일 저장
        # crawling_dir = self.get_safe_path(self.config['target']['folder'], article['article_id'])
        # for x, download_file in enumerate(article['attachment_url']):
        #     save_loc_fn = self.get_safe_path(crawling_dir, article['attachment_name'][x])
        #     urlretrieve(article['attachment_url'][x], save_loc_fn)

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

            # 검색 대상
            # 1. 알림뉴스 > 보도자료
            # 2. 알림뉴스 > 설명자료
            # 3. 정책자료 > 법령정보 > 입법예고
            # 4. 정책자료 > 법령정보 > 행정예고

            # 1. 알림뉴스 > 보도자료
            if self.config['params']['site']['site_board'] == '보도자료':

                # first_menu = self.get_by_xpath('//*[@id="hd"]/div[1]/div/div[2]/a[2]')
                # self.safe_click(first_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # second_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/a')
                # self.safe_click(second_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # third_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/ul/li[2]/a')
                # self.safe_click(third_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # fourth_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/ul/li[2]/ul/li[1]/a')
                # self.safe_click(fourth_level_menu)
                # self.implicitly_wait(after_wait=1)

                # 검색 결과물인 각 페이지 처리
                while not self.is_done:
                    self.get_page()
                    if self.is_done:
                        break
                    self.implicitly_wait(after_wait=1) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                    self.next_page()

            # 2. 알림뉴스 > 설명자료
            elif self.config['params']['site']['site_board'] == '설명자료':

                # first_menu = self.get_by_xpath('//*[@id="hd"]/div[1]/div/div[2]/a[2]')
                # self.safe_click(first_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # second_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/a')
                # self.safe_click(second_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # third_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/ul/li[2]/a')
                # self.safe_click(third_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # fourth_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[3]/ul/li[2]/ul/li[2]/a')
                # self.safe_click(fourth_level_menu)
                # self.implicitly_wait(after_wait=1)

                # 검색 결과물인 각 페이지 처리
                while not self.is_done:
                    self.get_page()
                    if self.is_done:
                        break
                    self.implicitly_wait(after_wait=1) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                    self.next_page()

            # 3. 정책자료 > 법령정보 > 입법예고
            elif self.config['params']['site']['site_board'] == '입법예고':

                # first_menu = self.get_by_xpath('//*[@id="hd"]/div[1]/div/div[2]/a[2]')
                # self.safe_click(first_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # second_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/a')
                # self.safe_click(second_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # third_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/ul/li[4]/a')
                # self.safe_click(third_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # fourth_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/ul/li[4]/ul/li[3]/a')
                # self.safe_click(fourth_level_menu)
                # self.implicitly_wait(after_wait=1)

                # 검색 결과물인 각 페이지 처리
                while not self.is_done:
                    self.get_page()
                    if self.is_done:
                        break
                    self.implicitly_wait(after_wait=1) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                    self.next_page()

            # 4. 정책자료 > 법령정보 > 행정예고
            elif self.config['params']['site']['site_board'] == '행정예고':

                # first_menu = self.get_by_xpath('//*[@id="hd"]/div[1]/div/div[2]/a[2]')
                # self.safe_click(first_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # second_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/a')
                # self.safe_click(second_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # third_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/ul/li[4]/a')
                # self.safe_click(third_level_menu)
                # self.implicitly_wait(after_wait=1)
                #
                # fourth_level_menu = self.get_by_xpath('//*[@id="hd"]/div[2]/ul[2]/li[4]/ul/li[4]/ul/li[4]/a')
                # self.safe_click(fourth_level_menu)
                # self.implicitly_wait(after_wait=1)

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
    with MofSearch(kwargs['config_f']) as ws:
        ws.start()

################################################################################
if __name__ == '__main__':
    _config_f = 'mof.yaml'
    do_start(config_f=_config_f)
