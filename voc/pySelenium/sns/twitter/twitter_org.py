"""
====================================
 :mod:`twitter`
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
#
#  * [2021/01/05]
#     - 포맷 적용, 캡처시 상단바가 가리는 현상 해결, 로그인 최소화 적용, create_ts 수정
#  * [2021/01/05]
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
import pickle
import tarfile
import datetime
import traceback
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from selenium.webdriver.common.keys import Keys
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, webdriver


################################################################################
class TwitterSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # 로그인할때는 Headless를 사용하면 안됨
        self.headless_yaml = self.config['params']['kwargs']['headless']
        if i == 0 and self.config['params']['kwargs']['headless']:
            self.config['params']['kwargs']['headless'] = False
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'TWITTERSearch.log'),
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
        self.logger.info(f'Starting TWITTER Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            # 로그인 클릭 (구글 로그인 미완)
            # self.switch_to_iframe('//iframe[@title="Google 계정으로 로그인 버튼"]')
            # e = self.get_by_xpath('//div[@aria-labelledby="button-label"]',
            #                       cond='element_to_be_clickable')
            # e = self.get_by_xpath('//a[@data-testid="loginButton"]',
            #                       cond='element_to_be_clickable')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=2)

            # login 화면
            # 사용자 입력
            # window = self.driver.window_handles[1]
            # self.driver.switch_to.window(window)
            # e = self.get_by_xpath('//input[@type="email"]')
            self.driver.get('https://twitter.com/i/flow/login')
            self.implicitly_wait(after_wait=1)
            e = self.get_by_xpath('//input[@autocomplete="username"]')
            self.send_keys(e, self.config['params']['site']['userid']+Keys.ENTER)
            self.implicitly_wait(after_wait=3)

            # 암호 입력
            e = self.get_by_xpath('//input[@type="password"]')
            self.send_keys(e, self.config['params']['site']['passwd']+Keys.ENTER)
            self.implicitly_wait(after_wait=3)

            # 로그인창이 꺼지면서 메인 윈도우로 스위치
            window = self.driver.window_handles[0]
            self.driver.switch_to.window(window)

            # 로그인 쿠키를 담아둠
            pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def search(self):

        # 검색
        e = self.get_by_xpath('//input[@aria-label="검색어"]|//input[@aria-label="Search query"]')
        self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
        self.implicitly_wait(after_wait=1)

        # latest 클릭 최신순
        e = self.get_by_xpath('//div[@role="tablist"]/div[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comments(self, msg, cmt_e, cmt_num, parent_comment_id):
        try:
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
            # 트윗을 아무나 읽지 못하게 제한한 글이 있슴.
            self.switch_to_window(0)
            try:
                head_e = cmt_e.find_element_by_xpath('.//div[@class="css-1dbjc4n r-1d09ksm r-18u37iz r-1wbh5a2"]')
            except:
                return parent_comment_id
            # 댓글 id 아이디가 따로없어 번호로 ex) 000001
            cmt['comment_id'] = str(cmt_num).zfill(6)
            # 대댓글인지 확인
            e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]')
            is_reply = e.get_attribute('class') != 'css-1dbjc4n r-4qtqp9 r-zl2h9q'
            cmt['is_reply'] = is_reply
            if not is_reply:
                parent_comment_id = cmt['comment_id']
                cmt['parent_comment_id'] = ""
            else:
                cmt['parent_comment_id'] = parent_comment_id

            # 댓글 작성자 닉네임
            e = head_e.find_element_by_xpath('./div/a/div/div[2]|./div/div/div')
            cmt['nickname'] = e.text.strip()

            # 댓글 작성 시간
            c_t = head_e.find_element_by_tag_name('time').get_attribute('datetime')
            cmt['create_ts'] = c_t.rpartition('.')[0].replace('-', '.').replace('T', ' ').strip()

            # 댓글 likes, Retweets
            likes, retweets = 0, 0
            cs_info = cmt_e.find_element_by_xpath(
                './/div[@class="css-1dbjc4n r-1ta3fxp r-18u37iz r-1wtj0ep r-1s2bzr4 r-1mdbhws"]')
            for c_info in cs_info.get_attribute('aria-label').split(','):
                if c_info is None:
                    break
                c_info = c_info.strip().partition(' ')
                if c_info[2] in ['likes', '마음에 들어요', '마음에 들어요 님', '마음에 들어요 님 님']:
                    likes = int(c_info[0])
                elif c_info[2] in ['Retweets', '리트윗']:
                    retweets = int(c_info[0])
                # elif c_info[2] in ['reply', '답글']:
                #     reply = int(c_info[0])
            cmt['contents_like'] = likes
            cmt['contents_retweets'] = retweets

            #  부모 댓글과,대댓글의 내용 xpath의 경로가 다름.
            # 댓글 내용 text
            if is_reply:
                e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]')
                contents = e.text.strip()
            else:
                e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[1]')
                mention_e = e.text.strip()
                e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[2]')
                cmt_text = e.text.strip()
                contents = "\n".join([mention_e, cmt_text])
            cmt['contents'] = contents

            #  부모 댓글과,대댓글의 이미지 xpath의 경로가 다름.
            # 댓글 이미지
            cmt['comment_img_url'] = []
            cmt['comment_img'] = []
            if is_reply:
                e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[2]')
            else:
                e = cmt_e.find_element_by_xpath('./div/div/article/div/div/div/div[2]/div[2]/div[2]/div[3]')
            inner_html = e.get_attribute('innerHTML')
            if inner_html.find("Image") > 0:
                for i, re_img in enumerate(e.find_elements_by_tag_name('img')):
                    img_url = re_img.get_attribute('src')
                    if img_url.endswith('.svg'):
                        continue
                    cmt['comment_img_url'].append(img_url)
                    cmt['comment_img'].append(f'{cmt["comment_id"] + "_"+ str(i)}.png')
            # 댓글 목록에 추가
            msg['comment_list'].append(cmt)
            # self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
            self.logger.info(f'{cmt["comment_id"]}')
            return parent_comment_id
        except Exception as err:
            raise

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}]"')

            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            self.switch_to_window(0)
            content_e = \
                self.get_by_xpath('//article[@class="css-1dbjc4n r-18u37iz r-1ny4l3l r-1udh08x r-1qhn6m8 r-i023vh"]')
            # 게시판이름
            e = content_e.find_element_by_xpath('//h2[@dir="auto"]')
            msg['board_name'] = e.text.strip()
            # 게시글 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_head = self.driver.find_element_by_xpath(
                        '//div[@class="css-1dbjc4n r-aqfbo4 r-gtdqiz r-1gn8etr r-1g40b8q"]')
                    self.driver.execute_script("""
                                            var element = arguments[0];
                                            element.parentNode.removeChild(element);
                                            """, e_head)
                    self.full_screenshot(msg_capture_f)

            # 작성자 이름
            e = content_e.find_element_by_xpath('.//a[@role="link"]/div/div[2]|.//a[@role="link"]/div/div[@dir="auto"]')
            msg['author'] = e.text.strip()

            # 작성일시 오후 3:34 · 2022년 1월 7일 -> 년.월.일 시:분:초
            e = content_e.find_element_by_xpath('.//div[@class="css-1dbjc4n r-1r5su4o"]/div/div/a[1]')
            if e.text.find('M') > 0:
                create_ts = str(datetime.datetime.strptime(e.text, '%I:%M %p · %b %d, %Y')).replace('-', '.')
            else:
                c_t = datetime.datetime.strptime(e.text.replace('오후', 'PM').replace('오전', 'AM'), '%p %I:%M · %Y년 %m월 %d일')
                create_ts = str(c_t).replace('-', '.')
            msg['create_ts'] = create_ts
            # retweets, quote tweets, like
            a_like = 0
            a_quote_tweets = 0
            a_retweets = 0
            inner_html = content_e.get_attribute('innerHTML')
            if inner_html.find('css-1dbjc4n r-1dgieki r-1efd50x r-5kkj8d r-13awgt0 r-18u37iz r-tzz3ar r-s1qlax r-1yzf0co') > 0:
                for a_int in content_e.find_elements_by_xpath('.//a[@class="css-4rbku5 css-18t94o4 css-901oao r-18jsvk2 r-1loqt21 r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-qvutc0"]'):
                    if a_int.get_attribute('href') is None:
                        break
                    w_a = a_int.get_attribute('href')
                    if w_a.endswith('retweets'):
                        a_retweets = int(a_int.find_element_by_xpath('./div').text.strip().replace(',', ''))
                    elif w_a.endswith('with_comments'):
                        a_quote_tweets = int(a_int.find_element_by_xpath('./div').text.strip().replace(',', ''))
                    elif w_a.endswith('likes'):
                        a_like = int(a_int.find_element_by_xpath('./div').text.strip().replace(',', ''))
            self.move_to_element(e)
            content_e = \
                self.get_by_xpath('//article[@class="css-1dbjc4n r-18u37iz r-1ny4l3l r-1udh08x r-1qhn6m8 r-i023vh"]')

            msg['like'] = a_like
            msg['quote_tweets'] = a_quote_tweets
            msg['retweets'] = a_retweets


            # 본문 경로로 찾아야함. 멘션된 경우 경로가 바뀜.
            mention = False
            e = content_e.find_element_by_xpath('./div/div/div/div[3]/div[1]')
            if e.get_attribute('class') != "css-1dbjc4n":
                mention_e = e.text.strip()
                e = content_e.find_element_by_xpath('./div/div/div/div[3]/div[2]')
                contents_e = e.text.strip()
                msg['contents'] = "\n".join([mention_e, contents_e])
                mention = True
            else:
                msg['contents'] = e.text.strip()
            # 본문 이미지는 경로로 찾아야함.
            if mention:
                e = content_e.find_element_by_xpath('./div/div/div/div[3]/div[3]')
            else:
                e = content_e.find_element_by_xpath('./div/div/div/div[3]/div[2]')
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = e.get_attribute('innerHTML')
            if inner_html.find('css-1dbjc4n') > 0:
                img_e = e.find_elements_by_xpath('//div/img')
                for j, img in enumerate(img_e):
                    sub_e_url = img.get_attribute('src')
                    if sub_e_url.endswith('.svg'):
                        continue
                    msg['image_url_list'].append(sub_e_url)

            # 댓글이 계속 렌더링 되는 형식 6000px 만큼만 보여줌
            msg['comment_list'] = []
            e = content_e.find_element_by_xpath('./../../..')
            coments_px = re.findall(r'\(([^)]+)', e.get_attribute('style'))[0]
            more_coments = True
            cmt_num = 0
            parent_comment_id = ""
            while more_coments:
                e = self.get_by_xpath('//div[@aria-label="Timeline: Conversation"]|//div[@aria-label="타임라인: 대화"]')
                cmt_es = e.find_elements_by_xpath('./div/div')
                for cmt_e in cmt_es:
                    cmt_e_px = re.findall(r'\(([^)]+)', cmt_e.get_attribute('style'))[0]
                    if int(coments_px[:-2]) < int(cmt_e_px[:-2]):
                        inner_html = cmt_e.get_attribute('innerHTML')
                        # 댓글의 끝
                        if inner_html.find('css-1dbjc4n r-o52ifk') > 0:
                            more_coments = False
                            break
                        elif inner_html.find('tabindex') < 0:
                            continue
                        # Show replies 버튼. 클릭하면 다시 처음부터 체크
                        elif inner_html.find(
                                'css-18t94o4 css-1dbjc4n r-16y2uox r-19u6a5r r-1ny4l3l r-m2pi6t r-o7ynqc r-6416eg') > 0:
                            e = cmt_e.find_element_by_xpath(
                                './/div[@class="css-18t94o4 css-1dbjc4n r-16y2uox r-19u6a5r r-1ny4l3l r-m2pi6t r-o7ynqc r-6416eg"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=1)
                            break
                        # Show more replies 버튼. 클릭하면 다시 처음부터 체크
                        elif inner_html.find(
                                'css-18t94o4 css-1dbjc4n r-1777fci r-1pl7oy7 r-1ny4l3l r-o7ynqc r-6416eg r-13qz1uu') > 0:
                            e = cmt_e.find_element_by_xpath(
                                './/div[@class="css-18t94o4 css-1dbjc4n r-1777fci r-1pl7oy7 r-1ny4l3l r-o7ynqc r-6416eg r-13qz1uu"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=1)
                            break
                        else:
                            cmt_num += 1
                            # 부모아이디는 댓글 최상위댓글로 지정.
                            parent_comment_id = self.get_comments(msg, cmt_e, cmt_num, parent_comment_id)
                            coments_px = cmt_e_px
                            self.move_to_element(cmt_e)
                            break
            # 댓글수
            msg['num_comments'] = len(msg['comment_list'])
            # 댓글이 없을 경우 기본 포맷은 유지시켜야함
            if msg['num_comments'] == 0:
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
                msg['comment_list'].append(cmt)
        except Exception as err:
            raise
        finally:
            self.driver.back()
            # 처음 페이지로 스위치 해줘야함.
            self.switch_to_window(0)

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
            # 페이지 테이블 구해오기
            self.switch_to_window(0)
            for i in range(self.config['params']['site']['max_articles']):
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
                    ae = self.get_by_xpath('//body')
                    self.implicitly_wait(after_wait=1)
                    if i == 0:
                        self.send_keys(ae, 'k' + Keys.ENTER)
                    else:
                        self.send_keys(ae, 'j')
                        self.send_keys(ae, 'j'+Keys.ENTER)
                    self.implicitly_wait(after_wait=2)
                    # 1) 게시글 URL:  article_url
                    msg['article_url'] = a_url = self.driver.current_url
                    # 2) 게시글id : article_id
                    #  twitter의 경우 고유 id개념이 없지만 링크에 게시글의 고유 넘버가 있음
                    a_id = a_url[20:].partition('/status/')
                    msg['article_id'] = a_id[2] + '_' + a_id[0]
                    self.get_article(msg, i+1)
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    self.is_done = True
                    break
                self.save_image(msg)
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    self.save_article(msg)
                if len(self.output['article_list']) >= \
                        self.config['params']['site']['max_articles'] > 0:
                    self.is_done = True
                    break
                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = msg['create_ts']
        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
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
    def w_headless(self):
        pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("disable-gpu")

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['params']['kwargs']['url'])
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        # 새로고침
        self.driver.refresh()
        self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def a_cookie(self):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        # 새로고침
        self.driver.refresh()
        self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            if self.search_index == 0:
                self.login()
                if self.headless_yaml:
                    self.w_headless()
            else:
                self.a_cookie()
            self.search()
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
            return 0
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
            with TwitterSearch(kwargs['config_f'], keyword, i) as ws:
                ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'twitter.yaml'
    do_start(config_f=_config_f)
