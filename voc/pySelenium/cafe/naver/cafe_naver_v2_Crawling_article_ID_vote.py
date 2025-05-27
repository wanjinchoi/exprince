"""
====================================
 :mod:`cafe/cafe_naver`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
# * SEBIN EUN
#
# Change Log
# --------
#  * [2024/10/28]
#     - 투표 수집중 팝업이 뜰 경우 제거
#  * [2024/09/02]
#     - starting

################################################################################
import os
import re
import sys
import yaml
import json
import sqlite3
import time
import pickle
import requests
import random
import tarfile
import datetime
import traceback
from pathlib import Path
from copy import deepcopy
import urllib.request
from bs4 import BeautifulSoup
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from datetime import timedelta


################################################################################
# 이미지 다운(403 에러 해결코드)


opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)

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
class LOGINERROR(Exception):
    pass


################################################################################
class NaverCafeSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        self.config_f = config_f
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # 컨피그 파일 path로 접근. 파이썬 모듈 실행하는 위치가 다름.
        config_f_path = os.path._getfullpathname(config_f)
        # self.search_index = i
        # 컨피그 파일 path로 접근. 파이썬 모듈 실행하는 위치가 다름.
        log_d = "C:\\work\\voc_data\\logs\\vote_data"
        self.cookie_path = "C:\\work\\voc\\yaml\\카페\\네이버" + "\\cookies.pkl"
        # 로그인할때는 Headless를 사용하면 안됨
        # if i == 0 and self.config['params']['kwargs']['headless']:
        #     self.config['params']['kwargs']['headless'] = False
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'Navervote_data.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # 카페id
        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.cafe_domain = self.config['params']['kwargs']['url']
        self.save_a = True
        self.is_done = False
        self.cur_page = 0
        out_config = deepcopy(self.config)
        del out_config['params']['site']['passwd']
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
        self.logger.info(f'Starting Naver Cafe Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def yaml_extraction(self, article):
        if not os.path.exists(self.config_f):
            raise IOError(f'Cannot read config file "{self.config_f}"')
        with open(self.config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 특정 키워드는 키워드의 성격을 바꿔줌
        self.config['params']['site']['user_type'] = article[0]
        self.config['params']['site']['search_type'] = article[4]
        self.config['params']['site']['service'] = article[5]
        self.config['params']['site']['search'] = article[7]
        self.save_d(self.config_f, self.config)
        # 카페id
        self.cafe_id = self.config['params']['kwargs']['url'].rpartition('/')[2]
        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.is_done = False
        self.cur_page = 0
        out_config = deepcopy(self.config)
        del out_config['params']['site']['passwd']
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
        self.logger.info(f'Starting Naver Cafe Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            e = self.get_by_xpath('//body')
            inner_html = e.get_attribute('innerHTML')
            # 바로 로그인 되는 경우 처리 : https://cafe.naver.com/jbads
            if inner_html.find('gnb_login_button') > 0:
                # 로그인 클릭
                e = self.get_by_xpath('//*[@id="gnb_login_button"]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            else:
                self.logger.info('login: Directly login page shows up!')

            # login 화면
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="id"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//*[@id="pw"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="log.login"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 로그인 쿠키를 담아둠
            pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def get_cafe_info(self):
        cafe_info = {
            'name': None,
            'url': None,
            'since': None,
            'category': None,
            'register_type': None,
            'write_condition': None,
            'num_members': None,
            'num_visitors': None,
        }
        app_info = {
            'star_like': None,
            'num_reviews': None,
            'title': None,
            'contents': None,
            'version': None,
            'num_download': None,
        }
        try:
            e = self.get_by_xpath('//div[@class="info-view"]/a',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait()

            # 해당 iFrame으로 이동
            self.switch_to_iframe_by_name('cafe_main')
            for tr_e in self.driver.find_elements_by_xpath('//table[@class="tbl_cafe_info"]/tbody/tr'):
                try:
                    e = tr_e.find_element_by_xpath('.//th[@scope="row"]')
                    title = e.text.strip()
                    if title == '카페 이름':
                        e = tr_e.find_element_by_xpath('.//strong[@class="cafe_name"]')
                        cafe_info['name'] = e.text.strip()
                    elif title == '카페 주소':
                        # e = tr_e.find_element_by_xpath('.//*[@id="main-area"]/div/table[1]/tbody/tr[2]/td/a')
                        # cafe_info['url'] = e.text.strip()
                        cafe_info['url'] = self.config['params']['kwargs']['url']
                    elif title.startswith('모바일카페명'):
                        # 모바일카페 이름
                        e = tr_e.find_element_by_xpath('.//div[@class="mcafe_name"]')
                        cafe_info['mobile_name'] = e.text.strip()
                        # 모바일카페 아이콘
                        e = tr_e.find_element_by_xpath('.//div[@class="mcafe_icon cafe_thumb_70"]/img')
                        cafe_info['mobile_icon_src'] = e.get_attribute('src')
                    elif title == '카페 매니저':
                        e = tr_e.find_element_by_xpath('.//td[@class="p-nick"]/a[@class="m-tcol-c"]')
                        cafe_info['manager'] = e.text.strip()
                    elif title == '카페 스탭':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_staff"]')
                        cafe_info['staff'] = e.text.strip()
                    elif title == '카페 설립일':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_history"]')
                        cafe_info['since'] = e.text.split()[-1]
                    # elif title == '주제':
                    #     e = tr_e.find_element_by_xpath('.//td[@class="invite-padd02 m-tcol-c"]')
                    #     cafe_info['category'] = e.text.strip()
                    elif title == '카페 설명':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['category'] = e.text.strip()
                    elif title == '카페 검색어':
                        cafe_info['keywords'] = []
                        for ae in tr_e.find_elements_by_xpath('.//a[@class="keyword"]'):
                            cafe_info['keywords'].append(ae.text.strip())
                    elif title == '카페 성격':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['character'] = e.text.strip()
                    elif title == '가입 방식':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['register_type'] = e.text.strip()
                    elif title == '카페 가입 조건':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['register_condition'] = e.text.strip()
                    elif title == '글쓰기 조건':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['write_condition'] = e.text.strip()
                    elif title == '카페 활동':
                        # 카페 활동 : 멤버수  //*[@id="main-area"]/div/table/tbody/tr[17]/td/span[1]
                        e = tr_e.find_element_by_xpath('.//td/span[1]')
                        cafe_info['num_members'] = int(e.text.strip().replace(',',''))
                        # 카페 활동 : 전체 게시글
                        e = tr_e.find_element_by_xpath('.//td/span[2]')
                        cafe_info['num_articles'] = int(e.text.strip().replace(',',''))
                        # 카페 활동 : 총 방문자
                        e = tr_e.find_element_by_xpath('.//td/span[3]')
                        cafe_info['num_visitors'] = int(e.text.strip().replace(',',''))
                    elif title == '카페 랭킹':
                        e = tr_e.find_element_by_xpath('.//span[@class="txt_rank"]')
                        cafe_info['rank'] = e.text.strip()
                    elif title == '멤버 관리':
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['member_manage'] = e.text.strip()
                    elif title.startswith('카페 활동정보'):
                        e = tr_e.find_element_by_xpath('.//td')
                        cafe_info['knowledge_in'] = e.text.strip()
                except:
                    try:
                        e = tr_e.find_element_by_xpath('.//td[1]/strong')
                        _title = e.text.strip()
                        if _title == '주제':
                            e = tr_e.find_element_by_xpath('.//td[2]')
                            cafe_info['subject'] = e.text.strip()
                        elif _title == '지역':
                            e = tr_e.find_element_by_xpath('.//td[2]')
                            cafe_info['local'] = e.text.strip()
                    except:
                        pass
        except Exception as err:
            self.logger.error(f'get_cafe_info: Error {str(err)}')
        finally:
            self.output['cafe_info'] = cafe_info
            self.output['app_info'] = app_info
            self.switch_from_iframe()
            # 이전 페이지
            self.driver.back()

    # ==========================================================================
    def get_article(self, article):
        try:
            self.output['article_list'] = []
            self.output['config']['params']['site']['user_type'] = article[0]
            self.output['config']['params']['site']['search_type'] = article[4]
            self.output['config']['params']['site']['service'] = article[5]
            self.output['config']['params']['site']['search'] = article[7]
            self.output['config']['params']['site']['site_name'] = article[2]
            self.output['config']['params']['site']['site_number'] = article[8]
            self.output['config']['params']['kwargs']['url'] = article[9].split('/')[0] + '//' + article[9].split('/')[2] + '/' + article[9].split('/')[3]
            real_url = article[9].split('/')[0] + '//' + article[9].split('/')[2] + '/' + article[9].split('/')[5]
            self.driver.get(real_url)
            self.implicitly_wait(after_wait=1)
            self.site_num = article[8]
            start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            folder_name = "_".join([str(self.site_num), article[7], start_ts])
            self.config['target']['folder'] = f'C:/work/voc_data/latest/{article[3]}/{article[1]}' + '/' + folder_name
            self.output['config']['target']['folder'] = self.config['target']['folder']
            msg = {
                'page': self.cur_page,
                'row': 1,
                'user_type': article[0],
                'site': article[1],
                'site_name': article[2],
                # 'site_board': self.config['params']['site']['site_board'],
                'channel': article[3],
                'search_type': article[4],
                'service': article[5],
                'article_id': article[6],
                'create_ts': None,
                'board_name': None,
                'title': None,
                'contents': None,
                'tag_list': [],
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
                'article_url': article[9],
                'image_list': [],
                'image_url_list': [],
                'attachment_name': [],
                'attachment_url': [],
                'screenshot_error': None,
                'headless_option': None,
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
                'vote': [],
            }
            # 데이터 저장 여부 True
            self.save_data = True
            # delay_a = 1
            self.logger.info(f'article_id[{msg["article_id"]}]')
            self.implicitly_wait(after_wait=2)
            try:
                self.switch_to_iframe_by_name('cafe_main')
            except:
                self.logger.error(f'{msg["title"]} is cannot find iframe - pass')
                self.save_data = False
                # 이전 페이지
                self.switch_to_iframe_by_name('cafe_main')
                return

            # 게시글 URL로 HTML 소스 가져오기
            article_source = self.driver.page_source

            # BeautifulSoup을 사용하여 HTML 파싱
            soup = BeautifulSoup(article_source, 'html.parser')
            # 상단 - 게시판명, 제목, 작성자, 등록시간, 조회수
            top_e = soup.find('div', class_='article_header')
            # 게시판명
            board_name = top_e.find('a', class_='link_board')
            msg['board_name'] = board_name.text.strip()
            # 간편게시판인 경우 XPath가 달라서 분리
            if '간편게시판' in msg['board_name']:
                msg['title'] = None
                # 등록시간
                c_e = top_e.find('span', class_='date')
                create_t = c_e.text.strip().rpartition('.')
                create_ts = create_t[0] + create_t[2] + ':00'
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                    '%Y.%m.%d %H:%M:%S')
                # 중단 - 본문
                middle_e = soup.find('div', class_='article_viewer')
                msg['contents'] = middle_e.text.strip()
                # 해시태그 보류
                msg['tag_list'] = []
                hash_tag = soup.find('div', class_='ArticleTagList')
                if hash_tag:
                    for tag in hash_tag.find_all('li'):
                        msg['tag_list'].append(tag.text.strip())

                # 이미지 주소 갖고 오기
                middle_i = soup.find('div', class_='article_container')
                msg['image_list'] = []
                msg['image_url_list'] = []
                img_tags = middle_i.find_all('article_img ATTACH_IMAGE')
                for img in img_tags:
                    if 'src' in img.attrs:  # 이미지 태그에 'src' 속성이 있는지 확인
                        msg['image_url_list'].append(img['src'])

                        # 첨부파일, 현재 수집 안하는중
                msg['attachment_url'] = []
                msg['attachment_name'] = []
            else:
                # 상단
                top_e = soup.find('div', class_='article_header')
                # 제목
                title = top_e.find('h3', class_='title_text')
                msg['title'] = title.text.strip()
                # 등록시간
                c_e = top_e.find('span', class_='date')
                create_t = c_e.text.strip().rpartition('.')
                create_ts = create_t[0] + create_t[2] + ':00'
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime(
                    '%Y.%m.%d %H:%M:%S')
                # 조회수
                view_c = top_e.find('span', class_='count')
                view_cnt_num = view_c.text.strip()
                if '만' in view_cnt_num:
                    view_cnt = view_cnt_num.replace('만', '0000').replace('.', '')
                else:
                    view_cnt = view_cnt_num.replace(',', '')
                msg['view_count'] = int(re.sub(r'[^0-9]', '', view_cnt))
                # 작성자
                nick = top_e.find('div', class_='nick_box')
                msg['author'] = nick.text.strip()
                # 하단
                bottom_e = soup.find('div', class_='ArticleTool')
                # 댓글
                num_comm = bottom_e.find('a', class_='button_comment')
                num_comm_e = num_comm.text.partition('댓글 ')[2].partition('\n')[0]
                msg['num_comments'] = int(num_comm_e)
                # 중단 - 본문
                # 일반 게시글
                middle_e = soup.find('div', class_='se-main-container')
                if not middle_e:
                    # 참조 게시글(https://cafe.naver.com/nds07/3962833)
                    middle_e = soup.find('div', class_='ArticleSources') or soup.find('div', class_='article_viewer')
                msg['contents'] = middle_e.text.strip()
                # 투표
                vote_area = soup.find_all('div', class_='cafe_vote_wrap')
                if vote_area:
                    self.vote_data = True
                    self.get_vote_data(msg)
                else:
                    pass
                # 해시태그 보류
                msg['tag_list'] = []
                hash_tag = soup.find('div', class_='ArticleTagList')
                if hash_tag:
                    for tag in hash_tag.find_all('li'):
                        msg['tag_list'].append(tag.text.strip())

                # 이미지 주소 갖고 오기
                msg['image_list'] = []
                msg['image_url_list'] = []
                img_tags = middle_e.find_all('img')
                for img in img_tags:
                    if 'src' in img.attrs:  # 이미지 태그에 'src' 속성이 있는지 확인
                        msg['image_url_list'].append(img['src'])

                        # 첨부파일, 현재 수집 안하는중
                msg['attachment_url'] = []
                msg['attachment_name'] = []

            # 스크린샷
            if self.config['params']['site']['capture_article']:
                try:
                    # 댓글 작성 부분 제거
                    cmt_write = self.driver.find_element_by_xpath("//div[@class='CommentWriter']")
                    self.driver.execute_script("arguments[0].remove();", cmt_write)
                except:
                    pass
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                try:
                    self._screenshot(msg_capture_f)
                    msg['screenshot_error'] = False
                except:
                    msg['screenshot_error'] = True
                self.save_a = True
            # 댓글 : 댓글이 없는 경우 있음
            if msg['num_comments'] == 0:
                pass
            else:
                msg['comment_list'] = []
                comments = self.driver.find_elements_by_xpath('//div[@class="CommentBox"]//ul[@class="comment_list"]/li')
                parent_comment_id = ''
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
                    cmt['comment_id'] = cmt_e.get_attribute('id')
                    # 대댓글?
                    is_reply = cmt_e.get_attribute('class') == 'CommentItem CommentItem--reply'
                    cmt['is_reply'] = is_reply
                    if not is_reply:
                        parent_comment_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ''
                    else:
                        cmt['parent_comment_id'] = parent_comment_id
                    # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
                    try:
                        e = cmt_e.find_element_by_xpath('.//a[@class="comment_nickname"]')
                        cmt['nickname'] = e.text.strip()
                    except:
                        continue
                    # 댓글 내용
                    try:
                        e = cmt_e.find_element_by_xpath('.//span[@class="text_comment"]')
                        self.move_to_element(e)
                        comment = e.text.strip()
                    except:
                        e = cmt_e.find_element_by_xpath('.//span[@class="text_blind"]')
                        self.move_to_element(e)
                        comment = e.text.strip()
                    cmt['contents'] = comment
                    # # 댓글 내용중에 멘션이 있을 경우 포함 - 멘션 제외 요청(EXTVOCGE-1613)
                    # inner_html = cmt_e.get_attribute('innerHTML')
                    # if inner_html.find("text_nickname") > 0:
                    #     tag = cmt_e.find_element_by_xpath('.//a[@class="text_nickname"]').text
                    #     cmt['contents'] = tag + ' ' + comment
                    # else:
                    #     cmt['contents'] = comment
                    # 댓글 작성 시각
                    e = cmt_e.find_element_by_xpath('.//span[@class="comment_info_date"]')
                    create_t = e.text.strip().rpartition('.')
                    create_ts = create_t[0] + create_t[2] + ':00'
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')

                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    # 댓글 스티커 or 이미지
                    inner_html = cmt_e.get_attribute('innerHTML')
                    if inner_html.find('CommentItemSticker') > 0 or inner_html.find('CommentItemImage') > 0:
                        s = cmt_e.find_element_by_xpath('.//img[@class="image"]')
                        cmt['comment_img_url'].append(s.get_attribute('src'))
                        cmt_img_f = self.get_safe_path(
                            self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"] + "_0"}.png')
                        s.screenshot(cmt_img_f)
                        cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
                    self.logger.info(f'   [{i + 1}/{msg["num_comments"]}]: {cmt["comment_id"]}')

            if self.save_data:
                self.save_attachment(msg)
                self.save_image(msg)
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    self.save_article(msg)
                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = msg['create_ts']
        except Exception as err:
            raise
        finally:
            # print(self.output["latest_create_article_ts"])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()
            try:
                self.switch_to_iframe_by_name('cafe_main')
            except:
                # selenium.common.exceptions.WebDriverException: Message: unknown error:
                # cannot determine loading status
                pass

    # ==========================================================================
    def get_vote_data_db(self):
        try:
            vote_data_path = r'C:\work\voc_data\logs\vote_db'
            if not os.path.exists(vote_data_path):
                self.logger.info('Vote_DB_file is not exist in this PC')
                return
            else:
                # SQLite 데이터베이스 연결 및 커서 생성
                conn = sqlite3.connect(r'C:\work\voc_data\logs\vote_db' + '/' + 'vote_data.db')
                cursor = conn.cursor()
                # 현재 시간 구하기
                current_time = datetime.datetime.now()
                current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')

                # 1일 전 날짜 구하기 strp
                previous_day = current_time - timedelta(days=30)
                previous_day_str = previous_day.strftime('%Y-%m-%d %H:%M:%S')

                # DB 쿼리문
                query = """
                                SELECT *
                                FROM vote_Articles
                                WHERE collection_date >= ?
                                ORDER BY collection_date DESC;
                            """
                cursor.execute(query, [previous_day_str])

                # 결과 가져오기
                rows = cursor.fetchall()
                # self.logger.info(f'DB 쿼리문: {query}\n 조회한 날짜: {previous_day_str} ~ {current_time_str}, 키워드: {keyword}')
                self.logger.info(f'조회한 날짜: {previous_day_str} ~ {current_time_str}')

                # 연결 종료
                cursor.close()
                conn.close()

                self.article_list = rows

            self.logger.info("투표 게시글 추출 완료")

        except Exception as err:
            self.logger.error(f'get_vote_data: error: {str(err)}')
            raise

    # ==========================================================================
    def get_vote_data(self, msg):
        try:
            self.vote_not_end = True
            msg['vote'] = []
            vote_list = self.driver.find_elements_by_xpath('//div[@class="cafe_vote_wrap"]')

            for i, vote_e in enumerate(vote_list):
                # 딜레이
                delay_c = random.uniform(
                    self.config['params']['site']['delay']['comment']['min'],
                    self.config['params']['site']['delay']['comment']['max'],
                )
                time.sleep(delay_c)
                vote = {
                    'vote_id': i,
                    'vote_title': None,
                    'vote_start': None,
                    'vote_end': None,
                    'vote_involve_cnt': None,
                    'vote_complete': None,
                    'vote_item': [],
                }
                # 투표 종료 여부 확인
                vote_status = vote_e.find_element_by_xpath('.//span[@class="cafe_vote_status"]').text.strip()
                if vote_status == '투표 완료':
                    self.vote_not_end = False
                    vote['vote_complete'] = True
                    # 투표 제목 수집
                    vo_title = vote_e.find_element_by_xpath('.//strong[@class="cafe_vote_title_text"]')
                    vote['vote_title'] = vo_title.text.strip()
                    # 투표 항목 & 결과 수집
                    re_list = vote_e.find_elements_by_xpath('.//div[@class="cafe_vote_list"]/ul/li')
                    for j, vote_list_a in enumerate(re_list):
                        vote_item = {
                            'vote_num': j,  # 투표항목 넘버링
                            'vote_text': None,  # 투표항목
                            'vote_cnt': None,  # 투표 득표수
                            'vote_rate': None,  # 투표 득표퍼센트
                        }
                        e = vote_list_a.find_element_by_xpath('.//div[@class="label_box"]')
                        e_a = e.text.strip()
                        vote_item['vote_text'] = e_a.split('\n')[1]
                        vote_item['vote_cnt'] = e_a.split('\n')[2].split(', ')[0].replace('표', '')
                        vote_item['vote_rate'] = e_a.split('\n')[2].split(', ')[1].replace('%', '')
                        vote['vote_item'].append(vote_item)
                else:
                    vote['vote_complete'] = False
                    # 투표 종료일 존재 여부 확인 (xpath가 분리되어있지 않음)
                    # e = vote_e.find_element_by_xpath('//div[@class="cafe_vote_date"]')
                    # self.vote_end_date = e.text.strip()
                    # for option in e.find_elements_by_xpath('./span[@class="maximum"]'):
                    #     self.vote_end_date = self.vote_end_date.replace(option.text.strip(), '')
                    # if not self.vote_end_date:
                    # 투표 선택
                    if vote_e.find_element_by_xpath('.//input[@class="input_check"][1]').is_selected():
                        pass
                    else:
                        # 첫번째 옵션 선택
                        vote_click_a = vote_e.find_element_by_xpath('.//input[@class="input_check"][1]')
                        self.safe_click(vote_click_a)
                        self.implicitly_wait(after_wait=1)
                        # 투표하기 선택
                        vote_click_b = vote_e.find_element_by_xpath('.//button[1]')
                        self.safe_click(vote_click_b)
                        self.implicitly_wait(after_wait=1)
                    # 투표 제목 수집
                    vo_title = vote_e.find_element_by_xpath('.//strong[@class="cafe_vote_title_text"]')
                    vote['vote_title'] = vo_title.text.strip()
                    # 투표 항목 & 결과 수집
                    re_list = vote_e.find_elements_by_xpath('.//div[@class="cafe_vote_list"]/ul/li')
                    for j, vote_list_a in enumerate(re_list):
                        vote_item = {
                            'vote_num': j,  # 투표항목 넘버링
                            'vote_text': None,  # 투표항목
                            'vote_cnt': None,  # 투표 득표수
                            'vote_rate': None,  # 투표 득표퍼센트
                        }
                        e = vote_list_a.find_element_by_xpath('.//div[@class="label_box"]')
                        e_a = e.text.strip()
                        vote_item['vote_text'] = e_a.split('\n')[0]
                        vote_item['vote_cnt'] = e_a.split('\n')[1].split(', ')[0].replace('표', '')
                        vote_item['vote_rate'] = e_a.split('\n')[1].split(', ')[1].replace('%', '')
                        vote['vote_item'].append(vote_item)
                # 투표 목록에 추가
                msg['vote'].append(vote)
                # 팝업창이 떠 있을 경우 닫기
                try:
                    vote_click_a = self.driver.find_elements_by_xpath('//div[@class="layer_wrap"]//div[@class="layer_footer"]/a')
                    self.safe_click(vote_click_a[0])
                    self.implicitly_wait(after_wait=1)
                except:
                    pass
        except Exception as err:
            self.logger.error(f'get_vote_data: error: {str(err)}')
            raise

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
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        height = self.driver.execute_script('return document.body.scrollHeight')
        width = self.driver.execute_script('return document.body.scrollWidth')
        self.driver.set_window_size(S('Width') + width/2, S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        # self.driver.find_element_by_xpath('//div[@class="article_wrap"]').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="ArticleContentBox"]').screenshot(f)
        # self.driver.save_screenshot(f)

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
                        urllib.request.urlretrieve(sub_e_url, article_img_p)
                        article['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count+1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

        # 댓글 이미지
        # for cmt in article['comment_list']:
        #     if not('comment_img' in cmt and cmt['comment_img']):
        #         continue
        #     for k, cmt_url in enumerate(cmt['comment_img_url']):
        #         try:
        #             cmt_img_f = self.get_safe_path(
        #                 self.config['target']['folder'],
        #                 article['article_id'],
        #                 f'{cmt["comment_id"] + "_" + str(k)}.png'
        #             )
        #             urlretrieve(cmt_url, cmt_img_f)
        #         except Exception as err:
        #             self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img_url"]}: {str(err)}')

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
        if 'site_sequence' in self.output['config']['params']['site']:
            del self.output['config']['params']['site']['site_sequence']
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
    def w_headless(self):
        pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
        options = webdriver.ChromeOptions()
        # options.add_argument('headless')
        options.add_argument("disable-gpu")

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['params']['kwargs']['url'])
        cookies = pickle.load(open(self.cookie_path, "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

    # ==========================================================================
    def a_cookie(self):
        try:
            if not os.path.isfile(self.cookie_path):
                # print("no cookie")
                self.logger.error('The cookie file could not be found.')
                raise
            cookies = pickle.load(open(self.cookie_path, "rb"))
            for cookie in cookies:
                self.driver.add_cookie(cookie)
            self.driver.refresh()
            self.implicitly_wait(after_wait=1)
            e = self.get_by_xpath('//*[@id="gnb_login_button"]/..')
            if e.get_attribute('style') != 'display: none;':
                self.logger.error('Cookie file need to be update.')
                raise
        except Exception as e:
            raise LOGINERROR(e)

        # ==========================================================================
    def check_login(self):

        # "카페 메인 (cafe_main)" iFrame으로 이동
        # self.switch_to_iframe_by_name('cafe_main')

        # 로그인 클릭
        e = self.get_by_xpath('//span[@class="gnb_txt"]')
        if e.text.strip() == '로그인':
            self.a_cookie()

    # ==========================================================================
    def start(self):
        try:
            self.a_cookie()
            # 로그인 체크 로직
            self.check_login()
            # 쿼리
            if os.path.isfile(f'C:\\work\\voc_data\\logs\\vote_db\\vote_data.db'):
                self.get_vote_data_db()
                for article in self.article_list:
                    # 수집
                    self.get_article(article)
                return 0
            else:
                self.logger.info('Vote_DB_file is not exist in this PC')
                return
        except LOGINERROR as e:
            self.logger.error(e)
            return 1
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9


################################################################################
def do_start(**kwargs):
    with NaverCafeSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'cafe_naver.yaml'
    do_start(config_f=_config_f)
