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
# * Kyobong  An
#
# Change Log
# --------
#
#  * [2022/11/18]
#     - starting

################################################################################
import os
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
from urllib.request import urlretrieve
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


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

        # user 정보담긴 폴더는 voc 모듈로 설정.
        self.user_data_path = self.config['target']['user_data_path']

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
            self.switch_to_iframe_by_name('cafe_main')
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self._screenshot(msg_capture_f)
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
            e = self.get_by_xpath('//a[@class="link_board"]')
            msg['board_name'] = e.text.strip()
            # 작성일시
            e = self.get_by_xpath('//span[@class="date"]')
            create_t = e.text.strip().rpartition('.')
            create_ts = create_t[0] + create_t[2] + ':00'
            msg['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
            # 조회수
            e = self.get_by_xpath('//span[@class="count"]')
            msg['view_count'] = int(e.text.split()[1].replace(',', ''))
            # 내용 : 비어 있는 경우도 있음 (사진만)
            try:
                e = self.get_by_xpath('//div[@class="content CafeViewer"]')
                msg['contents'] = e.text.strip()
            except:
                msg['contents'] = ''

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
                    msg['image_url_list'].append(sub_e_url)
                    art_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{j}.png')
                    sub_e.screenshot(art_img_f)
                    msg['image_list'].append(f'{j}.png')
            # 첨부파일  Todo:headless시 클릭으로 다운받지못함
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
                # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
                delay_a = random.uniform(
                    self.config['params']['site']['delay']['article']['min'],
                    self.config['params']['site']['delay']['article']['max'],
                )
                time.sleep(delay_a)
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
                    # # 8) 조회수
                    # se = bi.find_element_by_xpath('.//td[@class="td_view"]')
                    # view_count = int(se.text.strip())
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
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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
    def a_user_data(self):
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument('headless')
            options.add_argument("disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            options.add_argument(f"--user-data-dir={self.user_data_path}")
            options.add_argument('headless')

            self.driver.start_session(options.to_capabilities())
            self.driver.get(self.config['params']['kwargs']['url'])
            self.driver.refresh()
            self.implicitly_wait(after_wait=1)
            e = self.get_by_xpath('//*[@id="gnb_login_button"]/..')
            if e.get_attribute('style') != 'display: none;':
                self.logger.error('userData dir need to be update.')
                raise
        except Exception as e:
            raise LOGINERROR(e)

    # ==========================================================================
    def start(self, i=None):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])

            self.a_user_data()
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
