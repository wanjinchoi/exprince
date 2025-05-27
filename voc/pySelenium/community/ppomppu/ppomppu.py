"""
====================================
 :mod:`ppomppu`
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
#
# * Kyobong An
#
# Change Log
# --------
#  * [2024/09/30]
#     - 게시판명 UI 변경으로 인해 XPath 변경
#  * [2024/08/20]
#     - 댓글 상단 xpath 수정
#  * [2024/08/09]
#     - 댓글 내용이 길거나 이미지가 2개 이상인 경우 2번째 이미지 수집하지 못하는 현상 확인. 가장 하단인 작성 시간으로 이동해서 수집
#  * [2024/07/16]
#     - 스크린샷 순서 변경
#  * [2024/07/15]
#     - 댓글 수집 로직 오류 수정
#  * [2024/07/12]
#     - 스크린샷 전에 마지막 부분으로 스크롤하는 로직 추가
#  * [2024/07/11]
#     - 게시글 스크린샷 찍기 전 맨위로 이동 로직 추가
#  * [2024/05/21]
#     - 댓글 수집 로직 수정
#  * [2024/05/20]
#     - 게시글 내부 이미지 가져오는 로직 수정
#  * [2024/04/24]
#     - 작성자, 조회수, 작성일 xpath 변경
#  * [2024/03/19]
#     - 에러 코드 세분화
#     - 에러 로그 세분화
#     - 검색결과 존재 여부 확인 로직 추가
#  * [2023/08/25]
#     - 이벤트 게시글인 경우 게시글 등록 시간 처리 로직 추가
#  * [2023/07/06]
#     - 댓글수에 빈값이 들어가있는 경우 존재하여 해당 부분 수정
#  * [2022/10/26]
#     - 조회수 xpath 수정
#     - 추천수 xpath 수정
#  * [2022/08/03]
#     - 댓글 xpath 변경
#  * [2022/07/08]
#     - 비회원 게시글 존재 
#  * [2022/05/18]
#     - add timeout decorator 추가. (무한로딩) - timeout 데코레이터가 봇에서 에러남
#  * [2022/05/16]
#     - 작성자이름, 댓글 닉네임 수정.
#     - 게시글 open시 최대 timeout시간 60초로 설정. (무한로딩)
#  * [2022/04/14]
#     - 댓글이 페이징 되어있슴. 대댓글 댓글 구분 수정
#  * [2022/03/02] MinJung
#     - def get_page 에서 msg 부분에 추가
#     - def get_commen에 comment_list 재선언 및 cmt 선언 수정
#  * [2022/03/02] MinJung
#     - yaml 내용 수정
#     - def __init__(self, config_f): 내용 변경
#     - def get_page 에서 msg부분 수정
#     - def save_image 생성
#     - emoticon을 comment_img으로 변경
#     - def get_page의 첫번째 크롤링 게시그의 작성 시간 추가
#     - def start의 finally에서 print문 추가
#     - def start에 return 0 추가
#     - 게시글 캡쳐 이름 f'{msg["article_id"]}.png'으로 변경
#     - def get_page에서 각 게시글별 json 파일 이름을 f'{msg["article_id"]}'으로 변경
#     - def get_page에서if self.stop_article_older_than(msg): 부분 변경
#  * [2022/01/03]
#     - article_url 추가. 각 게시글 별로 url추출
#  * [2021/12/28]
#     - starting

################################################################################
import re
import os
import sys
import yaml
import json
import time
import shutil
import random
import tarfile
import datetime
import urllib.request
import traceback
from pathlib import Path
from copy import deepcopy
# from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
# from threading import Thread
# import functools


# ################################################################################
# def timeout(time_out):
#     def deco(func):
#         @functools.wraps(func)
#         def wrapper(*args, **kwargs):
#             res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (func.__name__, timeout))]
#
#             def newFunc():
#                 try:
#                     res[0] = func(*args, **kwargs)
#                 except Exception as e:
#                     res[0] = e
#             t = Thread(target=newFunc)
#             t.daemon = True
#             try:
#                 t.start()
#                 t.join(time_out)
#             except Exception as je:
#                 print('error starting thread')
#                 raise je
#             ret = res[0]
#             if isinstance(ret, BaseException):
#                 raise ret
#             return ret
#         return wrapper
#     return deco


################################################################################
class PPOMPPUSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'PPOMPPUSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
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
        self.logger.info(f'Starting PPOMPPU Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:
            # 검색 어 입력
            e = self.get_by_xpath('//input[@name="keyword"]')
            e.clear()
            self.send_keys(e, self.config['params']['site']['search'])
            # 검색 단추
            e = self.get_by_xpath('//button[@class="btn btn-search"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            # 커뮤니티 선택
            e = self.get_by_xpath('//div[@class="result2"]/ul/li[2]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        except Exception as err:
            self.logger.error(f'search: Error: "{str(err)}"')
            raise

    # ==========================================================================
    def get_comments(self, msg):
        parent_comment_id = None
        try:
            # 댓글 list 없는 경우도 있슴
            comments_e = self.get_by_xpath('//div[@id="quote"]')

            comments = comments_e.find_elements_by_xpath('./div[@id]//table[@class="info_bg"]/..')
            for i, cmt_e in enumerate(comments):
                # 딜레이
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
                cmt_re_c = 0
                # 댓글에 대댓글이 모두 한 테이블 안에 잇는 구조 경로로 찾아야함.
                # 댓글 id
                self.move_to_element(cmt_e)
                # 댓글 ID
                e_id = cmt_e.find_element_by_xpath('./..')
                comm_id = e_id.get_attribute('id')
                cmt['comment_id'] = re.findall(r'\d+', comm_id)[0]

                # 대댓글인지 확인
                is_reply = cmt_e.get_attribute('class') != "comment_line   comment_template_depth1_comment_line"
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                else:
                    cmt['parent_comment_id'] = parent_comment_id

                # 댓글 작성자 이름
                e = cmt_e.find_element_by_xpath('.//b')
                if e.get_attribute('innerHTML').find('img') > 0:
                    nick = e.find_element_by_xpath('.//img')
                    nickname = nick.get_attribute('alt')
                else:
                    nickname = e.text.strip()
                cmt['nickname'] = nickname

                # 댓글 작성 시간
                e = cmt_e.find_element_by_xpath('.//font[@class="eng-day"]')
                create_ts = e.text.replace('*', '').strip()
                if create_ts.find(':') > 0:
                    cmt['create_ts'] = datetime.date.today().strftime('%Y.%m.%d ') + create_ts
                else:
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%Y-%m-%d').strftime('%Y.%m.%d %H:%M:%S')
                # 댓글 내용이 길거나 이미지가 2개 이상인 경우 2번째 이미지 수집하지 못하는 현상 확인. 가장 하단인 작성 시간으로 이동해서 수집
                self.move_to_element(e)
                # 댓글 추천수
                e = cmt_e.find_element_by_xpath('.//span[2]//span')
                cmt['like'] = int(e.text.strip())
                # 댓글 비추천수
                e = cmt_e.find_element_by_xpath('.//span[1]//span')
                cmt['dislike'] = int(e.text.strip())
                # 댓글 내용 text
                e = cmt_e.find_element_by_xpath('.//div[@class="over_hide link-point mid-text-area"]')
                cmt['contents'] = e.text.strip()
                # 댓글 이미지
                cmt['comment_img_url'] = []
                inner_html = e.get_attribute('innerHTML')
                if inner_html.find('<img src') > 0:
                    re_imgs = e.find_elements_by_xpath('.//img')
                    for k, re_img in enumerate(re_imgs):
                        cmt_img_f = self.get_safe_path(
                            self.config['target']['folder'],
                            msg['article_id'],
                            f'{cmt["comment_id"]+"_"+str(k)}.png'
                        )
                        re_img.screenshot(cmt_img_f)
                        cmt['comment_img_url'].append(re_img.get_attribute('src'))
                        cmt['comment_img'].append(f'{cmt["comment_id"]+"_"+str(k)}.png')
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except Exception as err:
            self.logger.error(f'get_comments: error: {str(err)}')
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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

            # (//div[@class="sub-top-text-box"]/br)[2]

            content_e = self.get_by_xpath('//div[@align="center"]')
            # 게시판이름
            e = content_e.find_element_by_xpath('//div[@class="bbs_title"]/span/a')
            msg['board_name'] = e.text.strip()
            # 작성자 이름 이미지 형식인 경우도 존재.
            try:
                e = content_e.find_element_by_xpath('.//ul[@class="topTitle-mainbox"]/li[@class="topTitle-name"]')
            except:
                e = content_e.find_element_by_xpath('.//div[@class="sub-top-text-box"]')
                box_text_author = e.text.strip()
                if box_text_author.find('익명') > 0:
                    author = '익명'
                else:
                    raise
            else:
                innerhtml = e.get_attribute('innerHTML')
                if innerhtml.find('img') > 0 and innerhtml.find('alt') > 0:
                    # 손자노드의 가장마지막 노드
                    author = e.find_element_by_xpath('descendant::*[position()=last()]').get_attribute('alt')
                else:
                    author = e.text.strip()
            msg['author'] = author
            # 작성일시 년-월-일 시:분
            e = content_e.find_element_by_xpath('//ul[@class="topTitle-mainbox"]')
            info = e.text.partition('등록일 ')[2].partition('\n조회수 ')
            if '이벤트종료일' in info[0]:
                c_ts = info[0].partition('   이벤트종료일')
                msg['create_ts'] = (c_ts[0] + ':00').replace('-', '.')
            else:
                msg['create_ts'] = (info[0] + ':00').replace('-', '.')

            # 조회수
            if '\n' in info[2]:
                msg['view_count'] =int(info[2].partition('\n')[0])
            else:
                msg['view_count'] = int(info[2].partition(' / ')[0])
            # 추천수
            e = self.get_by_xpath('//span[@id="vote_list_btn_txt"]')
            msg['like'] = int(e.text.strip())
            # msg['like'] = int(re.sub(r'[^0-9]', '', info[2].partition(' / ')[2].splitlines(True)[0]))
            # # 작성자 이미지
            # e = content_e.find_element_by_xpath(
            #     '/html/body/div/div[2]/div[5]/div/table[2]/tbody/tr[3]/td/table/tbody/tr/td[1]/img')
            # msg['author_img'] = e.get_attribute('src')

            # 본문
            e = content_e.find_element_by_xpath('//td[@class="board-contents"]')
            inner_html = e.get_attribute('innerHTML')
            # 본문 text (글이 없으면 알아서 ''로 나옴.)
            msg['contents'] = e.text.strip()
            # 본문 이미지는 tagname으로 찾아야함.
            msg['image_list'] = []
            # if inner_html.find('position:relative;') > 0:
            if inner_html.find('img') > 0:
                img_e = e.find_elements_by_xpath('.//div/img|.//p/img')
                for j, img in enumerate(img_e):
                    self.move_to_element(img)
                    article_img_p = self.get_safe_path(
                        self.config['target']['folder'],
                        msg['article_id'],
                        f'{j}.png'
                    )
                    sub_e_url = img.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)
                    urllib.request.urlretrieve(img.get_attribute('src'), article_img_p)
                    msg['image_list'].append(f'{j}.png')

            if msg['num_comments'] == 0:
                pass
            else:
                msg['comment_list'] = []
                c_p = self.get_by_xpath('//font[@class="pagelist_han"]')
                if c_p.text == '':
                    self.get_comments(msg)
                else:
                    c_pages = c_p.find_elements_by_xpath('./*')
                    for p, c_page in enumerate(c_pages):
                        c_p = self.get_by_xpath('//font[@class="pagelist_han"]')
                        c_ps = c_p.find_elements_by_xpath('./*')
                        c_page = c_ps[p]
                        if c_page.tag_name == 'font':
                            if c_page.text == '..':
                                p_next = c_p.find_element_by_xpath('./a[@class="page_next"]')
                                self.safe_click(p_next)
                                continue
                            self.get_comments(msg)
                        else:
                            self.safe_click(c_page)
                            self.implicitly_wait(after_wait=1)
                            self.get_comments(msg)
            # 게시글 스크린샷
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
                self.implicitly_wait(after_wait=1)
                self.driver.execute_script("window.scrollTo(0, 0);")
                self.implicitly_wait(after_wait=1)
                self._screenshot(msg_capture_f)
                # self.full_screenshot(msg_capture_f)
        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # self.driver.back()
            self.driver.close()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_main_window()

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
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            try:
                e = self.get_by_xpath('//div[@class="results_board"]/div')
            except:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return

            ae_list = self.driver.find_elements_by_xpath('//div[@class="results_board"]/div')
            for i in range(len(ae_list)):
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
                try:
                    # xpath가 사라짐 다시 구해주어야함
                    ae_list = self.driver.find_elements_by_xpath('//div[@class="results_board"]/div')
                    ae = ae_list[i]
                    self.move_to_element(ae)
                    bi = ae.find_elements_by_xpath('.//span/strike')
                    # 블라인드 글
                    if bi:
                        self.logger.debug('운영자에 의해 블라인드 처리된 글입니다.')
                        continue

                    # 1) 게시글id : article_id
                    #  ppomppu의 경우 고유 id개념이 없지만 링크에 개시판의 고유번호와 게시글의 고유번호가 있음. 게시판_넘버
                    e = ae.find_element_by_xpath('.//span[@class="title"]/a')
                    e_url = e.get_attribute('href')
                    id = e_url.partition('id=')[2].partition('&keyword')[0].partition('&no=')
                    msg['article_id'] = id[2] + '_' + id[0]
                    # 2) 게시글 url : article_url
                    msg['article_url'] = e_url

                    e = ae.find_element_by_xpath('.//span[@class="title"]/a')
                    a = ae.find_element_by_xpath('.//span[@class="title"]/a/font')
                    # 3) 댓글수 : num_comments
                    if a.text.strip() == '':
                        msg['num_comments'] = 0
                    else:
                        msg['num_comments'] = int(a.text.strip())
                    # 4) 게시글이름 : title 게시글 옆에 댓글 숫자가 붙음.
                    msg['title'] = e.text[:e.text.rfind(a.text)]
                    # self.safe_click(ae)
                    try:
                        self._open_url(e_url)
                    except Exception as err:
                        self.logger.error(f"Timeout error!! page_url : {msg['article_url']}")
                        # 처음 페이지로 스위치 해줘야함.
                        if len(self.driver.window_handles) > 1:
                            self.switch_to_window(1)
                            self.driver.close()
                        self.switch_to_main_window()
                        continue
                    
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i+1)

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
            self.logger.error(f'get_page: error: {str(err)}')
            raise

    # ==========================================================================
    # @timeout(60)
    def _open_url(self, url):
        # element 찾는 시간 설정
        self.driver.set_page_load_timeout(60)
        # 스크립트 시간 설정
        self.driver.set_script_timeout(60)
        self.driver.execute_script(f"window.open('{url}')")
        return

    # ==========================================================================
    def next_page(self):
        ple = None
        try:
            # 목록으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            ple = self.get_by_xpath('//div[@class="page"]', timeout=2)

            self.move_to_element(ple)

            active_page = int(ple.find_element_by_xpath('.//font[@class="page_inert"]').text.strip())
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == '다음':
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
                elif pa.text.isalpha():
                    continue
                elif int(pa.text.strip()) == active_page+1:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            if active_page is None:
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
        with PPOMPPUSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'ppomppu.yaml'
    do_start(config_f=_config_f)
