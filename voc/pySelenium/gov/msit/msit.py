"""
====================================
 :mod:`Msit`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for msit (과학기술정보통신부)
"""
# Authors
# ===========
#
# * JeYoung Park, Jerry Chae
#
# Change Log
# --------
#
#  * [2023/06/05]
#     - 첨부파일명이 다른 경우 존재하여 비교 로직 추가
#  * [2023/01/31]
#     - 사이트 UI 변경
#  * [2022/01/07]
#     - 1차 버전 완료
#     - 화면 캡쳐 기능 미동작 : 향후 해결
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
import datetime
import traceback
# import olefile # 박제영 추가
# import zlib # 박제영 추가
# import struct # 박제영 추가
import subprocess # 박제영 추가
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from alabslib.selenium import Select


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
class MsitSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'MsitSearch.log'),
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
        self.cmt_done = False
        self.article_num = 0
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
        self.logger.info(f'Starting Msit Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        self.safe_click(title_e)
        self.implicitly_wait(after_wait=1)

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 게시글 URL
            msg['article_url'] = self.driver.current_url

            # 조회수 (조회수가 없음)
            # msg['view_count'] = ''

            # 본문 (hwp 첨부파일로 대체함)
            msg['contents'] = ''

            # 첨부파일 이름 추출과 임시 다운로드
            msg['attachment_name'] = []
            msg['attachment_url'] = []
            try:
                e = self.get_by_xpath('//ul[@class="down_file"]')
                se = e.find_elements_by_xpath('.//li')
            except:
                # 첨부파일이 없거나 추출 불가능
                msg['attachment_name'] = ''
                msg['attachment_url'] = ''
            else:
                for down_link in se:
                    # 첨부파일 이름
                    af = down_link.find_element_by_xpath('./a')
                    af_name = af.text.split('\n')[0]

                    # 첨부파일 다운로드(파일명이 다른 경우 존재하여 비교)
                    set1 = set(os.listdir(self.get_download_path()))
                    file_downlink = down_link.find_element_by_class_name('down')
                    self.safe_click(file_downlink)
                    self.implicitly_wait(after_wait=1)
                    download_wait(self.get_download_path(), 20)
                    set2 = set(os.listdir(self.get_download_path()))
                    if af_name != list(set1 ^ set2)[0]:
                        af_name = list(set1 ^ set2)[0]
                    if len(list(set1 ^ set2)) != 1:
                        return
                    # 다운로드 부분이 자바코드로 구성되어 있어서 파일에 관한 링크 정보를 얻을 수 없음
                    download_file_fullpath = self.get_safe_path(self.get_download_path(), af_name)
                    msg['attachment_name'].append(af_name)
                    msg['attachment_url'].append(download_file_fullpath)  # 서버의 다운로드 디렉토리 위치와 파일명 정보

            # 본문 안의 이미지 주소 가져오기 (이미지를 가진 문서를 아직 찾지 못했음)
            msg['image_list'] = []
            msg['image_url_list'] = []

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                           f'{msg["article_id"]}.png')
                # self._screenshot(msg_capture_f)
                self.full_screenshot(msg_capture_f)

        except Exception as err:
            raise
        finally:
            # 이전 페이지로 이동
            self.driver.back()

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
                                  f'is older than "{old_ts}"' f'\n\n')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//div[@class="board_list"]')
            # 검색 결과물 페이지의 목록(List) 읽기
            bil = [bi for bi in e.find_elements_by_xpath('./div')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 li가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            for i in range(len(bil)):
                msg = {
                    'page': self.cur_page,
                    'row': i + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'site_board': self.config['params']['site']['site_board'],
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
                    e = self.get_by_xpath('//div[@class="board_list"]')
                    ail = [bi for bi in e.find_elements_by_xpath('./div')]
                    bi = ail[i]

                    se = bi.find_element_by_xpath('.//a[@href]')
                    title_e = se # 게시글 본문 이동용 argument
                    self.move_to_element(se)

                    # 제목: title
                    sub_se = se.find_element_by_class_name('title')
                    msg['title'] = sub_se.text.strip()

                    # 게시글 id : article_id
                    onclick_value = se.get_attribute("onclick")
                    msg['article_id'] = re.search('fn_detail\((.+?)\)', onclick_value).group(1)

                    sub_ses = se.find_elements_by_class_name('date')
                    # 등록일
                    create_date = sub_ses[0].text.strip()
                    msg['create_ts'] = create_date.replace('-', '.') + " " + "00:00:00"

                    sub_xpath = se.find_element_by_xpath('.//div[2]//div//dl[2]')
                    sub_ses = sub_xpath.find_element_by_class_name('con')
                    # 작성자(담당자)
                    msg['author'] = sub_ses.text.strip()

                    # 게시글 본문의 내용 채취
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
            ple = self.get_by_xpath('//div[@class="board_paging"]')

            is_current = False
            for pa in ple.find_elements_by_xpath('.//strong | .//a'):
                if pa.tag_name == 'strong':
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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )

        # 첨부파일 저장
        for af_name in article['attachment_name']:
            src_file = self.get_safe_path(self.get_download_path(), af_name)
            dst_dir = self.get_safe_path(self.config['target']['folder'], article['article_id'])
            # subprocess.run(['move', src_file, dst_dir], shell=True, check=True)
            shutil.move(src_file, dst_dir)
        # article['attachment_url'].clear()

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

            # if self.config['params']['site']['search_filter'] == '전체' or \
            #         self.config['params']['site']['search_filter'] == '제목' or \
            #         self.config['params']['site']['search_filter'] == '부서' or \
            #         self.config['params']['site']['search_filter'] == '담당자':
            #     pass
            # else:
            #     self.logger.error(f'***** 검색 항목 종류 입력 오류 : 전체/제목/부서/담당자 중 하나가 필요  ***** ')
            #     return

            # 검색어 입력
            # e = self.get_by_xpath('//*[@id="searchTxt"]')
            # self.send_keys(e, self.config['params']['site']['search'])

            # 제목 검색 선택 (과학기술정보통시부 msit은 내용 선택이 없음)
            # select = Select(self.driver.find_element_by_id("searchOpt"))
            # select.select_by_visible_text(self.config['params']['site']['search_filter'])
            # self.implicitly_wait(after_wait=1)
            #
            # # 검색 단추
            # e = self.get_by_xpath('//*[@id="btn_search"]',
            #                           cond='element_to_be_clickable')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)

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
    with MsitSearch(kwargs['config_f']) as ws:
        ws.start()
        # ws.pre_start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'msit.yaml'
    do_start(config_f=_config_f)
