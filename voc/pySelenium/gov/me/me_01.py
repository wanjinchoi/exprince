"""
====================================
 :mod:`gov/ Me_01 : 입법 행정 예고
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
#  * [2023/03/16]
#     - 변경된 사이트 url로 수집하도록 모듈 수정
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
class Me01(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'Me01.log'),
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
        self.logger.info(f'Starting Me01 Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e = self.get_by_xpath('//input[@title="검색어 입력"]')
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 필터
        if self.config['params']['site']['search_filter'] in ['내용', '제목', '기관명']:
            e = self.get_by_xpath('//select[@title="분류선택"]')
            e_s = e.find_elements_by_xpath('./option')
            for e_f in e_s:
                if e_f.text.find(self.config['params']['site']['search_filter']) >= 0:
                    self.safe_click(e_f)
                    break
            self.implicitly_wait(after_wait=1)

        # 검색 단추
        e = self.get_by_xpath('//div[@class="bt_box"]/button[1]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        try:
            try:
                e_a = self.get_by_xpath('//ul[@class="opn_area pecu"]')
                comments = e_a.find_elements_by_xpath('./li')
                parent_comment_id = ''
                msg['comment_list'] = []
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

                    # 댓글 id
                    cmt['comment_id'] = int(i)
                    # 대댓글
                    is_reply = False
                    cmt['is_reply'] = False
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ''
                    else:
                        cmt['parent_comment_id'] = parent_comment_id
                    # 댓글 nickname : 삭제된 댓글인 경우 발견 불가
                    e = cmt_e.find_element_by_xpath('./span[1]')
                    e_a = e.text.strip()
                    e_ab = e_a.split(' | ')
                    cmt['nickname'] = e_ab[0]

                    # 댓글 작성 시각
                    create_t = e_ab[1].split(' 제출')[0].rpartition('.')
                    create_ts = create_t[0].replace(' ', '') + create_t[2] + ':00'
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')

                    # 댓글 좋아요 / 싫어요
                    # e = cmt_e.find_element_by_xpath('./..//div[@class="bot_r"]/a[1]/span')
                    # cmt['like'] = int(e.text.strip())
                    # e = cmt_e.find_element_by_xpath('./..//div[@class="bot_r"]/a[1]/span')
                    # cmt['dislike'] = int(e.text.strip())

                    # 댓글 내용
                    e = e = cmt_e.find_element_by_xpath('./div[@name="txt_origin"]')
                    self.move_to_element(e)
                    cmt['contents'] = e.text.strip()

                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []

                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
                    self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
            except:
                self.driver.back()
                pass
        except:
            ...

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    # e_heads = self.driver.find_elements_by_xpath('//div[@class="page_topBtn"]')
                    # for e_head in e_heads:
                    #     self.driver.execute_script("""
                    #                             var element = arguments[0];
                    #                             element.parentNode.removeChild(element);
                    #                             """, e_head)
                    self.full_screenshot(msg_capture_f)

            e_ab = self.get_by_xpath('//div[@id="contents"]', timeout=1)

            # 2) 좋아요
            # e = e_ab.find_element_by_xpath('.//div[@class="ov_wrap"]/ul/li[2]/a')
            # msg['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))

            # 2) 게시글 내용 :
            e = e_ab.find_element_by_xpath('.//div[@class="bodReadBodyMk"]')
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
            inner_html = e_ab.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            if inner_html.find('file_link') > 0:
                for k, sub_k in enumerate(e_ab.find_elements_by_xpath('.//table[@class="tbl_typeD"]/tbody/tr//div/a')):
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('data-href')
                    msg['attachment_url'].append(sub_k_url)
                    # 다운로드폴더에 다운 받음
                    set1 = set(os.listdir(self.get_download_path()))
                    self.safe_click(sub_k)
                    self.implicitly_wait(after_wait=1)
                    download_wait(self.get_download_path(), 30)
                    set2 = set(os.listdir(self.get_download_path()))
                    # 실제로 다운 받는 파일의 이름이 다를수 있음.
                    sub_k_name = list(set1 ^ set2)[0]
                    msg['attachment_name'].append(sub_k_name)
                    src = "\\".join([self.get_download_path(), sub_k_name])
                    dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
                    # 파일 이동
                    shutil.move(src, dst)

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return

            # 댓글 페이지가 있는 경우 : 없으면 일반으로 들어가기
            try:
                c_more = e_ab.find_element_by_xpath('.//ul[2]/li[last()]/a')
                self.safe_click(c_more)
                self.implicitly_wait(after_wait=1)
                c = self.get_by_xpath('//div[@class="paging"]')
                e = c.find_element_by_xpath('./ol/li[@class="on"]')
                is_on = int(e.text.strip())
                self.move_to_element(e)
                # 답글이 1이상이면 클릭하기
                c_d = c.find_elements_by_xpath('./ol/li')
                for cd in c_d:
                    if int(cd.text) > 0:
                        self.safe_click(cd)
                        self.implicitly_wait(after_wait=1)
                    self.get_comment(msg)
                self.driver.back()

            except:
                self.get_comment(msg)

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
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="dbody"]')
            es = e.find_elements_by_xpath('./ul')

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
                    e = self.get_by_xpath('//div[@class="dbody"]')
                    es = e.find_elements_by_xpath('./ul')
                    ea = es[i]

                    # 0) 게시글 번호 : article_number
                    e = ea.find_element_by_xpath('./li[1]')
                    msg['article_number'] = e.text.strip()
                    # 2) 게시글 id : article_id
                    e_url = ea.find_element_by_xpath('./li[2]/a')
                    a_url = e_url.get_attribute('href')
                    v = a_url.rpartition('/')[2]
                    if '?' in v:
                        v_e = v.partition('?')[0]
                    else:
                        v_e = v
                    msg['article_id'] = v_e
                    # 2) 게시글 주소: article_url
                    # msg['article_url'] = a_url
                    # 3) 제목: title
                    e_t = ea.find_element_by_xpath('./li[2]/a')
                    msg['title'] = e_t.text.strip()
                    # 4) 작성 시간
                    e = ea.find_element_by_xpath('./li[5]')
                    e_a = e.text.partition('~')[0]
                    e_ab = e_a.rpartition('.')[0]
                    create_ts = e_ab.replace(' ', '') + ' 00:00:00'
                    msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                    # 5) 작성자
                    e = ea.find_element_by_xpath('./li[4]/p[1]')
                    msg['author'] = e.text.strip()
                    # 6) 댓글 수
                    e = ea.find_element_by_xpath('./li[6]/a')
                    msg['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))

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
            ple = self.get_by_xpath('//div[@class="paging"]')
            is_current = False
            for pa in ple.find_elements_by_xpath('./ol/li'):
                if pa.get_attribute('class') == 'on':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait()
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
    with Me01(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'me_01.yaml'
    do_start(config_f=_config_f)
