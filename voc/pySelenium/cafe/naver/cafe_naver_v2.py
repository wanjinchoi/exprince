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
# * Jerry Chae
#
# Change Log
# --------
#
#  * [2023/06/27]
#     - 게시글내부 이미지 수집 중 오류가 발생하여 해당 로직 수정
#  * [2023/06/02]
#     - 스크린샷 에러 발생할 경우, 필드(screenshot_error)에 True로 표시
#  * [2023/05/23]
#     - '간편게시판' 처리 로직 추가
#  * [2023/05/22]
#     - 게시글 내부 이미지 중 url이 null인 경우 넘어가도록(동영상이 존재하여)
#  * [2023/02/20]
#     - 스크린샷 본문 내용만 찍도록 수정
#  * [2023/01/16]
#     - 스크린샷 찍는 범위 증가
#  * [2023/01/12]
#     - 스크린샷 찍기 전에 기다리는 시간 추가
#  * [2022/12/20]
#     - 스크린샷 찍는 부분 수정
#  * [2022/12/06]
#     - 해쉬태그 수집하는 로직 수정
#  * [2022/11/16]
#     - 해시태그 수집하도록 수정
#  * [2022/07/25]
#     - 쿠키 업데이트 문제 에러로그에 추가
#  * [2022/06/20]Kyobong An
#     - 기존 article_id 앞에 카페id를 붙임 (분석팀 요청)
#  * [2022/06/03]Kyobong An
#     - login 에러 return 1로 처리
#  * [2022/04/18]Kyobong An
#     - login 분리 해서 작업.
#  * [2022/04/12]Kyobong An
#     - 이미지 가져올 때 기존 url로 가져오는 방식 -> 캡쳐로 가져옴.
#  * [2022/03/21]Kyobong An
#     - 검색 여러번 할때 user_type, service, search_type 값을 야물에서 수정가능하도록 변경
#  * [2022/03/21]Kyobong An
#     - 다음카페처럼 로직수정 한번 로그인에 여러번 검색하도록 변경
#  * [2022/01/26]Kyobong An
#     - article_url 변경, 기존 방식으로 url을 가지고오면 해당 url로 못감. input yaml에서 cafe url을 앞에 추가시켜줌
#  * [2022/01/17]Kyobong An
#     - 게시글 캡처기능 수정. headless 사용. 로그인후에 쿠키를 가져와서 webdriver를 다시 실행후에 쿠키를 추가함.
#     - search_filter 수정 일부 카페의 경우. 검색필터의 내용이 다른경우가 있슴.
#  * [2022/01/14]Kyobong An
#     - save_img 추가. 사진을 저장하면서 에러가 안난 파일이름만 image_list에 추가하기위함
#     - search_complex 추가. 복합 검색어를 구분하기위함.
#  * [2022/01/10]JeongSunBin
#     - 검색부분에 search_filter추가 기본값은 게시글이고 제목, 댓글로 검색 가능하도록 변경
#     - yaml target/folder에 / 삭제 (Kyobong An)
#  * [2022/01/10]Kyobong An
#     - datetime 형식 변경 2021.12.01. 04:16:00 -> 2021.12.01 04:16:00
#     - info에 latest_create_article_ts 추가
#     - stu에서 outputvalue로 latest_create_article_ts를 출력
#  * [2022/01/07]Kyobong An
#     - 분석팀과의 협의 적용
#     - 기존 crawling 폴더를 사이트넘버_키워드_수집시작일로 변경 .tgz도 동인
#     - img_list에는 파일이름만 img_url_list따로 구분. 댓글에 이미지도 list 형식으로 변경.(다른 사이트와 통일성을 위함)
#     - img_list에는 파일의 인덱스를 이름으로 (0번부터시작). comment_img는 댓글id_인덱스(0번부터 시작)
#     - 게시글 폴더별로 json파일 이름을 게시글_id로 변경.게시글 캡처 이미지도 게시글_id로 변경
#     - 게시글 별로 대상(user_type),사이트, 사이트이름, 채널, 검색어 타입(경쟁사와 당사를 구분하기위함) 정보 추가
#  * [2022/01/06]
#     - # 바로 로그인 되는 경우 처리 : https://cafe.naver.com/jbads
#  * [2022/01/03]
#     - 검색 단추가 때때로 다른 엘리먼트로 구현되는 경우가 있어 엔터키로 변경
#     - article_url 추가. 각 게시글 별로 url추출(Kyobong)
#  * [2021/12/28]
#     - 카페 정보 가져오는 부분 수정 (경우에 따라 틀려지는 부분 제목으로 찾도록)
#  * [2021/12/22]
#     - article 별로 별도 저장 시점 조종, save_article()
#     - image_list 에 직접 저장하는 것, comment의 emoticon_url을 save_article로 옮김
#     - start() 에서 save()를 finally 블락으로 이동
#     - 입력에 stop_article_older_than 조건 추가, stop_article_older_than() 에서 처리
#     - 검색결과 없는 경우 처리
#  * [2021/12/15] Kyobong An
#     - 게시글에 borad_name(게시판이름) 추가, 댓글에 이미지나 사진이 있을 경우 해당 댓글 id이름으로 저장
#     - 댓글 내용에 맨션이 포함된 경우 댓글내용에 추가함
#  * [2021/12/12]
#     - add delay between reading articles and comments
#  * [2021/12/09]
#     - save as articles as separated folder
#     - is_yaml flag at target in config
#     - parent_comment_id add for comment is_reply
#     - add num_articles at self.output
#     - num_cmt => num_comments
#     - tar.gz compression
#  * [2021/12/02]
#     - config file
#  * [2021/12/01]
#     - starting

################################################################################
import os
import re
import sys
import yaml
import json
import time
import pickle
import shutil
import random
import tarfile
import datetime
import traceback
from pathlib import Path
from copy import deepcopy
import urllib.request
from urllib.request import urlretrieve
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
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
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # 컨피그 파일 path로 접근. 파이썬 모듈 실행하는 위치가 다름.
        config_f_path = os.path._getfullpathname(config_f)
        self.cookie_path = "C:\\work\\voc\\yaml\\카페\\네이버" + "\\cookies.pkl"
        # 로그인할때는 Headless를 사용하면 안됨
        # if i == 0 and self.config['params']['kwargs']['headless']:
        #     self.config['params']['kwargs']['headless'] = False
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverCafeSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 특정 키워드는 키워드의 성격을 바꿔줌
        if self.search_index == 0:
            n_user_type = len(self.config['params']['site']['user_type'].split(','))
            n_search = len(self.config['params']['site']['search'].split(','))
            n_search_type = len(self.config['params']['site']['search_type'].split(','))
            n_service = len(self.config['params']['site']['service'].split(','))
            if n_user_type != n_search_type or n_search != n_service or n_user_type != n_search:
                err_msg = 'the length of list of user_type, search, search_type, service is different'
                print(err_msg)
                self.logger.error(err_msg)
                raise ValueError(err_msg)
        self.config['params']['site']['user_type'] = self.config['params']['site']['user_type'].split(',')[i]
        self.config['params']['site']['search_type'] = self.config['params']['site']['search_type'].split(',')[i]
        self.config['params']['site']['service'] = self.config['params']['site']['service'].split(',')[i]
        self.config['params']['site']['search'] = keyword

        # 카페id
        self.cafe_id = self.config['params']['kwargs']['url'].rpartition('/')[2]

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
    def search(self):
        # 검색 어 입력
        # self.switch_to_window(0)
        e = self.get_by_xpath('//input[@id="topLayerQueryInput"]')

        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 아래와 같이 검색 단추가 때때로 다른 엘리먼트로 구현되는 경우가 있어 엔터키로 변경
        time.sleep(1)
        self.send_keys(e, Keys.ENTER)

        # 검색 단추
        # e = self.get_by_xpath('//*[@id="cafe-search"]/form/button',
        #                       cond='element_to_be_clickable')
        # self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 댓글 내용으로 검색
        if self.config['params']['site']['search_filter'] in ['댓글', '제목']:
            self.switch_to_iframe_by_name('cafe_main')

            e = self.get_by_xpath('//form[@name="frmSearchTop"]')
            e_a = e.find_element_by_xpath('//form[@name="frmSearchTop"]/div[3]')
            self.safe_click(e_a)

            e_s = e_a.find_elements_by_xpath('//ul[@id="sl_general"]/li')
            for e_filter in e_s:
                if e_filter.text.find(self.config['params']['site']['search_filter']) >= 0:
                    self.safe_click(e_filter)
                    self.implicitly_wait(after_wait=1)

            e = self.get_by_xpath('//button[@class="btn-search-green"]')
            self.safe_click(e)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # 카페에 main iframe으로 이동
            self.implicitly_wait(after_wait=2)
            self.switch_to_iframe_by_name('cafe_main')
            # if self.config['params']['site']['capture_article']:
            #     # save capture
            #     # e_body = self.get_by_xpath('//body')
            #     msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'], f'{msg["article_id"]}.png')
            #     self.full_screenshot(msg_capture_f)

            # # 회원레벨, (1:1 채팅)만 있는 경우 발견안될 수  있음
            # try:
            #     e = self.get_by_xpath('//em[@class="nick_level"]', timeout=1)
            #     msg['author_level'] = e.text.strip()
            # except:
            #     msg['author_level'] = ''
            # 게시판 이름
            try:
                e = self.get_by_xpath('//a[@class="link_board"]')
                msg['board_name'] = e.text.strip()
            except:
                msg['board_name'] = self.config['params']['site']['site_name'] + ' 간편게시판'

            # 간편게시판인 경우 XPath가 달라서 분리
            if msg['board_name'].find('간편게시판') > 0:
                # 간편게시판인 경우 게시글 수집
                # 제목 - 간편게시판은 제목 X
                msg['title'] = None

                # 작성일시 - 몇분 전, 몇시간 전, 어제, 그저께(2일 전)
                create_time = self.get_by_xpath('//span[@class="date"]')
                if msg['board_name'].find('간편게시판') > 0:
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
                    elif when.find('어제') == 0:
                        dd = 1
                        ddd = int(dd)
                        d = datetime.datetime.now() - timedelta(days=ddd)
                        msg['create_ts'] = d.strftime('%Y.%m.%d') + ' 23:30:00'
                    elif when.find('그저께') == 0:
                        dd = 2
                        ddd = int(dd)
                        d = datetime.datetime.now() - timedelta(days=ddd)
                        msg['create_ts'] = d.strftime('%Y.%m.%d') + ' 23:30:00'
                    else:
                        msg['create_ts'] = datetime.datetime.strptime(when, '%Y.%m.%d.').strftime('%Y.%m.%d %H:%M:%S')
                    if not msg['create_ts']:
                        d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                        msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')

                    # 해쉬태그
                    msg['tag_list'] = []
                    for tag in self.driver.find_elements_by_xpath('//div[@class="ArticleTagList"]/ul/li'):
                        msg['tag_list'].append(tag.text.strip())

                    # 내용 : 비어 있는 경우도 있음 (사진만)
                    try:
                        e = self.get_by_xpath('//div[@class="article_viewer"]')
                        contents = e.text.strip()
                    except:
                        contents = ''
                    msg['contents'] = contents

                    e = self.get_by_xpath('//div[@class="article_container"]')
                    # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
                    # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
                    inner_html = e.get_attribute('innerHTML')
                    # 이미지 주소 가져오기
                    msg['image_list'] = []
                    msg['image_url_list'] = []
                    if inner_html.find('article_img ATTACH_IMAGE') > 0:
                        for j, sub_e in enumerate(e.find_elements_by_xpath('.//img[@class="article_img ATTACH_IMAGE"]')):
                            sub_e_url = sub_e.get_attribute('src')
                            if not sub_e_url:
                                pass
                            else:
                                msg['image_url_list'].append(sub_e_url)
                                art_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                               f'{j}.png')
                                sub_e.screenshot(art_img_f)
                                time.sleep(1)
                                msg['image_list'].append(f'{j}.png')

                    # 댓글 : 댓글이 없는 경우 있음
            else:
                # 간편게시판이 아닌 경우
                # 작성일시
                e = self.get_by_xpath('//span[@class="date"]')
                create_t = e.text.strip().rpartition('.')
                create_ts = create_t[0] + create_t[2] + ':00'
                msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                # 조회수
                # e = self.get_by_xpath('//span[@class="count"]')
                # msg['view_count'] = int(e.text.split()[1].replace(',', ''))
                # 해쉬태그
                msg['tag_list'] = []
                for tag in self.driver.find_elements_by_xpath('//div[@class="ArticleTagList"]/ul/li'):
                    msg['tag_list'].append(tag.text.strip())
                # 내용 : 비어 있는 경우도 있음 (사진만)
                try:
                    e = self.get_by_xpath('//div[@class="content CafeViewer"]')
                    contents = e.text.strip()
                except:
                    contents = ''
                msg['contents'] = contents
                e = self.get_by_xpath('//div[@class="article_container"]')
                # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
                # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
                inner_html = e.get_attribute('innerHTML')
                # 이미지 주소 가져오기
                msg['image_list'] = []
                msg['image_url_list'] = []
                if inner_html.find('se-image-resource') > 0:
                    for j, sub_e in enumerate(e.find_elements_by_xpath('.//img[@class="se-image-resource"]')):
                        sub_e_url = sub_e.get_attribute('src')
                        if not sub_e_url:
                            pass
                        else:
                            msg['image_url_list'].append(sub_e_url)
                            try:
                                art_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                               f'{j}.png')
                                sub_e.screenshot(art_img_f)
                                time.sleep(1)
                                msg['image_list'].append(f'{j}.png')
                                self.image_error = False
                            except:
                                self.image_error = True
                # 첨부파일
                # if inner_html.find('data-linktype="file"') > 0:
                #     for sub_e in e.find_elements_by_xpath('.//div[@class="se-module se-module-file"]/a[@data-linktype="file"]'):
                #         self.move_to_element(sub_e)
                #         msg['attachment_url'].append(sub_e.get_attribute('href'))
                #         # 다운로드폴더에 다운 받음
                #         set1 = set(os.listdir(self.get_download_path()))
                #         self.safe_click(sub_e)
                #         self.implicitly_wait(after_wait=1)
                #         download_wait(self.get_download_path(), 30)
                #         set2 = set(os.listdir(self.get_download_path()))
                #         # 실제로 다운 받는 파일의 이름이 다를수 있음.
                #         sub_k_name = list(set1 ^ set2)[0]
                #         msg['attachment_name'].append(sub_k_name)
                #         src = "\\".join([self.get_download_path(), sub_k_name])
                #         dst = self.get_safe_path(self.config['target']['folder'], msg['article_id'], sub_k_name)
                #         # 파일 이동
                #         shutil.move(src, dst)

                # 링크 주소 가져오기
                # msg['link_list'] = []
                # if inner_html.find('se-link') > 0:
                #     for sub_e in e.find_elements_by_xpath('.//a[@class="se-link"]'):
                #         msg['link_list'].append(sub_e.get_attribute('href'))

            # 댓글 : 댓글이 없는 경우 있음
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            comments = e.find_elements_by_xpath('./div[@class="CommentBox"]/ul[@class="comment_list"]/li')
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
                e = cmt_e.find_element_by_xpath('.//span[@class="text_comment"]')
                self.move_to_element(e)
                comment = e.text
                # 댓글 내용중에 멘션이 있을 경우 포함
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find("text_nickname") > 0:
                    tag = cmt_e.find_element_by_xpath('.//a[@class="text_nickname"]').text
                    cmt['contents'] = tag + ' ' + comment
                else:
                    cmt['contents'] = comment
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
                        self.config['target']['folder'], msg['article_id'], f'{cmt["comment_id"]+"_0"}.png')
                    s.screenshot(cmt_img_f)
                    cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{i+1}/{msg["num_comments"]}]: {cmt["comment_id"]}')

        except Exception as err:
            raise
        finally:
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                try:
                    self._screenshot(msg_capture_f)
                    msg['screenshot_error'] = False
                except:
                    msg['screenshot_error'] = True
            # 이전 페이지
            self.driver.back()
            try:
                self.switch_to_iframe_by_name('cafe_main')
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

            # 게시글 목록 스크린샷
            self.driver.set_window_size(self.config['params']['kwargs']['width'], 1000)
            s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
            s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
            self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))
            # self._screenshot(s_shot)

            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_iframe_by_name('cafe_main')

            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//*[@id="main-area"]/div[5]/table/tbody')
            bil = [bi for bi in e.find_elements_by_xpath('./tr')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함

            for i in range(len(bil)):
                # 게시글별로 대상(user_type),사이트, 사이트이름, 채널, 검색어 타입(경쟁사와 당사를 구분하기위함) 정보추가
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
                    'tag_list': [],
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
                    'screenshot_error': None,
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
                # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
                delay_a = random.uniform(
                    self.config['params']['site']['delay']['article']['min'],
                    self.config['params']['site']['delay']['article']['max'],
                )
                time.sleep(delay_a)
                # 이미지 에러
                self.image_error = False
                try:
                    e = self.get_by_xpath('//*[@id="main-area"]/div[5]/table/tbody')
                    ail = [bi for bi in e.find_elements_by_xpath('./tr')]
                    bi = ail[i]

                    # 1) 게시글id : article_id
                    se = bi.find_element_by_xpath('.//div[@class="inner_number"]')
                    msg['article_id'] = self.cafe_id+'_'+se.text.strip()
                    # 2) 제목: title
                    title_e = se = bi.find_element_by_xpath('.//a[@class="article"]')
                    msg['title'] = se.text.strip()
                    # 3) 게시글 URL:  article_url
                    cafe_url = self.config['params']['kwargs']['url']
                    msg['article_url'] = title_e.get_attribute('href').replace('https://cafe.naver.com/', cafe_url+'/')
                    # 4) 댓글갯수: num_comments : 댓글 없는 경우 발견안됨
                    try:
                        se = bi.find_element_by_xpath('.//a[@class="cmt"]')
                        msg['num_comments'] = int(se.text[1:-1])
                    except:
                        msg['num_comments'] = 0
                    # 5) 작성자: author
                    se = bi.find_element_by_xpath('.//a[@class="m-tcol-c"]')
                    msg['author'] = se.text.strip()
                    # # 6) 작성자레벨: 이미지로 있음
                    # se = bi.find_element_by_xpath('.//span[@class="mem-level"]/img')
                    # msg['level_img'] = se.get_attribute('src')
                    # # 7) 작성일시: '13:00' or '2021.11.30'
                    # se = bi.find_element_by_xpath('.//td[@class="td_date"]')
                    # msg['create_date'] = se.text.strip()
                    # # 8) 조회수 - 간편게시판에 조회수가 안보여서 게시글 목록에서 확인
                    se = bi.find_element_by_xpath('.//td[@class="td_view"]')
                    if '만' in se.text.strip():
                        se_a = se.text.strip().replace('만', '0000').replace('.', '')
                    else:
                        se_a = se.text.strip().replace(',', '')
                    msg['view_count'] = int(se_a)

                    self.safe_click(title_e)
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i+1)

                except Exception as err:
                    if msg['article_id'] is None:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
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
                if self.image_error == True:
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

            self.switch_from_iframe()

    # ==========================================================================
    def next_page(self):
        try:
            # np = self.cur_page + 1
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_iframe_by_name('cafe_main')
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="prev-next"]')
            is_on = False
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('class') == 'on':
                    is_on = True
                    continue
                if is_on:
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
                print("no cookie")
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
    def start(self, i=None):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            # if i == 0:
            #     self.login()
            #     self.w_headless()
            # else:
            #     self.a_cookie()
            self.a_cookie()
            if self.config['params']['site']['get_cafe_info']:
                self.get_cafe_info()
            self.search()
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.next_page()
            return 0
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
        finally:
            print(self.output["latest_create_article_ts"])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with open(kwargs['config_f'], encoding='utf-8') as ifp:
        f_yaml = yaml.load(ifp, yaml.SafeLoader)
        for i, keyword in enumerate(f_yaml['params']['site']['search'].split(',')):
            with NaverCafeSearch(kwargs['config_f'], keyword, i) as ws:
                re_t = ws.start(i)
        return re_t


################################################################################
if __name__ == '__main__':
    _config_f = 'cafe_naver.yaml'
    do_start(config_f=_config_f)
