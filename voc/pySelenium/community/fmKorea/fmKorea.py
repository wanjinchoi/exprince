"""
====================================
 :mod:`fmKorea`
====================================
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
# lee yong seok
# --------
#  * [2024/09/30]
#     - 대댓글의 본문 내용에 부모 댓글 작성자명 제외 수집하도록 변경
#  * [2024/08/08]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. 이미지 자르는 방식
#  * [2024/07/04]
#     - 댓글 페이지 변경 로직 전, 댓글 개수(100개) 확인 조건 변경
#  * [2024/05/21]
#     - 게시글 내부 이미지 가져오는 로직 수정(보완 작업)
#  * [2024/05/20]
#     - 게시글 내부 이미지 가져오는 로직 수정
#  * [2024/03/19]
#     - 에러 코드 세분화
#     - 에러 로그 세분화
#  * [2024/02/28]
#     - 삭제된 게시글인 경우 스킵하는 로직 추가(article_id 확인)
#  * [2023/11/30]
#     - 게시글 내부 이미지 수집 오류 회피 로직 버그 수정
#  * [2023/07/17]
#     - 제목 부분 xpath 변경
#  * [2023/06/30]
#     - 게시글 내부 이미지 수집 중 오류가 발생하여 해당 로직 수정
#  * [2023/04/25]
#     - starting

################################################################################
# import re
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
import urllib.request
from pathlib import Path
from copy import deepcopy
# from PIL import Image
# from urllib.request import urlretrieve
from datetime import timedelta
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

################################################################################
# 이미지 다운(403 에러 해결코드)


opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)


################################################################################

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
class fmKoreaSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'fmKoreaSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # self.config['params']['site']['search'] = self.config['params']['site']['search'].strip()

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
        # del out_config['params']['site']['passwd']
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
        self.logger.info(f'Starting Dogdrip Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:
            # 검색 어 입력
            e = self.get_by_xpath('//*[@id="IS_SEARCH"]')
            self.send_keys(e, self.config['params']['site']['search'])
            # 검색 단추 클릭
            e = self.get_by_xpath('//*[@id="header"]/div/div[3]/form/span/input',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 게시물 검색 클릭
            e = self.get_by_xpath('//*[@id="sphinx_search_tabs"]/li[2]/a',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

        except Exception as err:
            self.logger.error(f'search: Error: "{str(err)}"')
            raise

    # ==========================================================================
    def save_e_img(self, re_img, msg, cmt):
        cmt_img_f = self.get_safe_path(
            self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"] + "_0"}.png')
        re_img.screenshot(cmt_img_f)

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
                        self.logger.info(f'save_img: {j}.png : retry{count + 1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

    # ==========================================================================
    def get_comments(self, msg):
        try:
            comments_e = self.get_by_xpath('//ul[@class="fdb_lst_ul "]')
            comments = comments_e.find_elements_by_xpath('./li')
            parent_comment_id = None
            while True:
                for i, cmt_e in enumerate(comments):
                    comments_es = self.get_by_xpath('//ul[@class="fdb_lst_ul "]')
                    comments_e = comments_es.find_elements_by_xpath('./li')
                    cmt_e = comments_e[i]
                    # 광고
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
                    delay_c = random.uniform(
                        self.config['params']['site']['delay']['comment']['min'],
                        self.config['params']['site']['delay']['comment']['max'],
                    )
                    time.sleep(delay_c)

                    # 댓글 작성 시간
                    create_time = cmt_e.find_element_by_xpath('.//div[@class="meta"]//span[@class="date"]')
                    when = create_time.text.strip()
                    ddd, hhh, mmm = 0, 0, 0
                    # 38분 전
                    if when.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', when)
                        mmm = int(mm)
                    # 5시간 전
                    elif when.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', when)
                        hhh = int(hh)
                    elif when.find('일') > 0:
                        mm = re.sub(r'[^0-9]', '', when)
                        mmm = int(mm)
                    else:
                        wh = when + ':00'
                        cmt['create_ts'] = datetime.datetime.strptime(wh, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                    if not cmt['create_ts']:
                        d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                        cmt['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')

                    # 댓글 닉네임
                    e = cmt_e.find_element_by_xpath('.//div[@class="meta"]//a[@data-comment_srl]')
                    ea = e.text.strip()
                    cmt['nickname'] = ea
                    self.move_to_element(e)

                    # 대댓글 여부 확인
                    e_re = cmt_e.get_attribute('class')
                    if e_re.find('re bg') >= 0:
                        is_reply = True
                    else:
                        is_reply = False
                    cmt['is_reply'] = is_reply
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ""
                    else:
                        cmt['parent_comment_id'] = parent_comment_id

                    if is_reply == True:
                        try:
                            parent_name = cmt_e.find_element_by_xpath('.//div[2]//div//a')
                            self.driver.execute_script("arguments[0].remove();", parent_name)
                        except:
                            pass

                    # 댓글 ID
                    e_c = cmt_e.find_element_by_xpath('.//div[2]//div')
                    cmt_id = e_c.get_attribute('class')
                    c = cmt_id.split('_')[1]  # 확인
                    cmt['comment_id'] = c

                    # 댓글 내용
                    cmt['contents'] = e_c.text.strip()

                    # 댓글 좋아요
                    li_e = cmt_e.find_element_by_xpath('//div[@class="fdb_nav img_tx"]/span/a[1]/em/span')
                    if li_e.text.strip() == '':
                        cmt['like'] = '0'
                    else:
                        cmt['like'] = li_e.text.strip()

                    # 댓글 싫어요
                    dis_e = cmt_e.find_element_by_xpath('//div[@class="fdb_nav img_tx"]/span/a[2]/span')
                    if dis_e.text.strip() == '':
                        cmt['dislike'] = '0'
                    else:
                        cmt['dislike'] = dis_e.text.strip()

                    # 댓글 이미지X
                    # inner_html = cmt_e.get_attribute('innerHTML')
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    # if inner_html.find('mid=sticker') > 0:
                    #     re_img = e_c.find_element_by_xpath('.//a')
                    #     c = re_img.get_attribute('style')
                    #     c_sr = c.split('(".')[1].partition('")')[0]
                    #     url = self.config['params']['kwargs']['url'] + c_sr
                    #     cmt['comment_img_url'].append(url)  # src가 이미지 주소
                    #     self.save_e_img(re_img, msg, cmt)
                    #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
                    index = len(msg['comment_list'])
                    self.logger.info(f'   [{index}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                    if msg['num_comments'] <= len(msg['comment_list']):
                        break

                    # 댓글 페이지 넘기기
                    if index % 100 == 0:
                        self.next_page_article()
                if msg['num_comments'] <= len(msg['comment_list']):
                    break

        except Exception as err:
            raise

    # ==========================================================================
    def _screenshot(self, output_file):

        xpath = '/html/body/div[1]/div/div/div/div[3]/div/div[2]/div[3]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)

        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size

        # 현재 페이지의 크기 가져오기
        original_window_size = self.driver.get_window_size()
        original_scroll_position = self.driver.execute_script("return window.pageYOffset;")

        # 페이지의 높이 가져오기
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")

        # 리스트 초기화
        images = []
        scroll_position = 0

        # 페이지를 스크롤하면서 스크린샷 찍기
        while scroll_position < page_height:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)

            # 스크린샷 찍기
            png = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(png))
            images.append(image)

            # 스크롤 위치를 업데이트
            scroll_position += viewport_height

        # 페이지 원래 상태로 복원
        self.driver.set_window_size(original_window_size['width'], original_window_size['height'])
        self.driver.execute_script(f"window.scrollTo(0, {original_scroll_position});")

        # 이미지 병합
        total_height = len(images) * images[0].height
        merged_image = Image.new('RGB', (images[0].width, total_height))

        current_height = 0
        for image in images:
            merged_image.paste(image, (0, current_height))
            current_height += image.height

        # 원하는 영역만 잘라내기
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']

        cropped_image = merged_image.crop((left, top, right, bottom))

        cropped_image.save(output_file)

    # ==========================================================================
    def enable_download_headless(self, download_dir):
        self.browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
        self.browser.execute("send_command", params)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]')

            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            try:
                timeout = 30  # 초 단위
                element_present = EC.presence_of_element_located((By.XPATH, "//div[@class='rd rd_nav_style2 clear']"))
                WebDriverWait(self.driver, timeout).until(element_present)
            except:
                return

            e = self.get_by_xpath('//div[@class="rd rd_nav_style2 clear"]')
            # 1) 제목
            title_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[1]/h1/span[last()]')
            msg['title'] = title_e.text.strip()
            # 2) 작성일
            create_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[1]/span')
            create_ts = create_e.text.strip() + ':00'
            msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
            # 3) 작성자
            author_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[2]/div[1]/a')
            msg['author'] = author_e.text.strip()

            # 조회수
            view_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[2]/div[2]/span[1]/b')
            msg['view_count'] = int(view_e.text.strip())

            # 추천수 - 싫어요 없음
            f_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[2]/div[2]/span[2]/b')
            like_e = int(f_e.text.strip())
            if like_e >= 0:
                msg['like'] = like_e
                msg['dislike'] = None
            else:
                msg['like'] = None
                msg['dislike'] = like_e

            # 댓글 수
            com_e = e.find_element_by_xpath('./div[1]/div[1]/div[1]/div[2]/div[2]/span[3]/b')
            msg['num_comments'] = int(com_e.text.strip())

            # 본문 content
            content_e = e.find_element_by_xpath('./div[1]/div[2]/article')
            inner_html = content_e.get_attribute('innerHTML')
            # 본문 text
            msg['contents'] = content_e.text.strip()
            # 본문 이미지
            msg['image_list'] = []
            if inner_html.find('img') > 0:
                img_e = content_e.find_elements_by_tag_name('img')
                for j, img in enumerate(img_e):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{j}.png')
                    try:
                        self.move_to_element(img)
                        urllib.request.urlretrieve(img.get_attribute('src'), cmt_img_f)
                        msg['image_list'].append(f'{j}.png')
                    except:
                        img.screenshot(cmt_img_f)
                        time.sleep(1)
                        msg['image_list'].append(f'{j}.png')

            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self.full_screenshot(msg_capture_f)
                else:
                    self._screenshot(msg_capture_f)

            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            # 댓글 수가 100개 이상이면 댓글 첫 페이지 클릭
            if msg['num_comments'] > 100:
                page_e = self.get_by_xpath('//*[@id="cmtPosition"]/div[1]/div/a[1]',
                                           cond='element_to_be_clickable')
                self.safe_click(page_e)
                self.implicitly_wait(after_wait=1)
            self.get_comments(msg)

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            self.close_tab()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_main_window()

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
    def get_user_type(self, boardname):
        if boardname in ["배민커넥트", "배달", "배달대행 기사들 모임"]:
            return "라이더"
        else:
            return "소비자"

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            try:
                e = self.get_by_xpath('//ul[@class="searchResult"]')
            except:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return

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
                    'author': None,  # 변경
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()

                    e = self.get_by_xpath('//ul[@class="searchResult"]')
                    es = e.find_elements_by_xpath('./li')
                    ea = es[i]

                    # 이미지 에러
                    self.image_error = False
                    # e_url = ae.get_attribute('href')
                    ae = ea.find_element_by_xpath('.//dl//dt//a')
                    e_url = ae.get_attribute('href')
                    # 1) 게시글 URL:  article_url
                    msg['article_url'] = e_url
                    # 2) 게시글id : article_id
                    msg['article_id'] = e_url.split('/')[3]
                    # 삭제된 게시글 처리 로직 - 삭제된 게시글인 경우 https://www.fmkorea.com/ 로 받아서 article_id 가 없음
                    if msg['article_id'] == '':
                        self.logger.info('삭제된 게시글입니다.')
                        continue
                    msg['board_name'] = '에펨코리아'

                    self.driver.execute_script(f"window.open('{e_url}')")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True
                    break
                self.output['article_list'].append(msg)
                # self.save_image(msg)
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
            self.logger.error(f'get_page: error: {str(err)}')
            raise
        finally:
            pass

    # ==========================================================================
    def next_page_article(self):
        ple = None
        e_pa = None
        try:
            # np = self.cur_page + 1
            # 목록으로 이동
            self.switch_to_window(1)
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="clear cmt_pg"]', timeout=2)
            is_on = False
            # 현재 페이지 번호 구하기
            st_num = ple.find_element_by_xpath('.//strong[@class="this"]')
            tt = int(st_num.text.strip())

            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == '':
                    continue
                if int(pa.text.strip()) > tt:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
        except Exception as err:
            if ple is None:
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
            raise

    # ==========================================================================
    def next_page(self):
        ple = None
        e_pa = None
        try:
            # 목록으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            ple = self.get_by_xpath('//*[@id="content"]/div/div[4]', timeout=2)
            # ple_e = ple.find_element_by_xpath('.//ul[@class="ed pagination pagewide"]')
            is_on = False
            # 현재 페이지 번호 구하기
            st_num = ple.find_element_by_xpath('.//strong')
            tt = int(st_num.text.strip())

            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == '첫 페이지':
                    continue
                if int(pa.text.strip()) > tt:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            if ple is None:
                self.logger.error(f'Cannot find Result!')
                self.is_done = True
            raise
        finally:
            self.switch_to_main_window()

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
            f'{article["article_id"]}'
            # f'{self.output["start_ts"]}'
        )
        self.save_d(at_js_f, article)
        # save image dcinside는 이미지 다운로드가 안됨
        # for j, sub_e_url in enumerate(article['image_list']):
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{j + 1}.png'
        #     )
        #     urlretrieve(sub_e_url, cmt_img_f)
        # for cmt in article['comment_list']:
        #     if not('comment_img_url' in cmt and cmt['comment_img_url']):
        #         continue
        #     cmt_img_f = self.get_safe_path(
        #         self.config['target']['folder'],
        #         article['article_id'],
        #         f'{cmt["comment_id"]}.png'
        #     )
        #     urlretrieve(cmt['comment_img_url'], cmt_img_f)

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
            # self.login()
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
            return 1
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    try:
        with fmKoreaSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'fmKorea.yaml'
    do_start(config_f=_config_f)
