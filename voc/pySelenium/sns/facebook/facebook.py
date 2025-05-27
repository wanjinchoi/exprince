"""
====================================
 :mod:`sns/facebook`
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
#  * [2022/04/22]
#     - 검색 부분에서 셀레니움이 죽어버림..  로그인후 쿠키저장 ->  새로운 창에서 url로 검색결과 페이지 호출 후 크롤링 작업시작
#     - create_ts 년.월.일 논리에러 수정
#  * [2022/04/06]
#     - delay_article로 로그인과 검색어 입력할때 시간통제
#  * [2022/04/06]
#     - 오전, 오후 시간 계산 수정
#  * [2022/03/31]
#     - 로그인 최소화, 포맷 적용 완료. 댓글, 대댓글, 대대댓글 까지만 수집.
#  * [2022/01/18]
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
import traceback
import datetime
import urllib.request
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys, ActionChains, webdriver


################################################################################
class FacebookSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f, keyword, i):
        self.search_index = i
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'FacebookSearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        # 로그인할때는 Headless를 사용하면 안됨
        if i == 0 and self.config['params']['kwargs']['headless']:
            self.config['params']['kwargs']['headless'] = False
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)


        # 랜덤시간
        self.delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max']-0.7,
            )

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

        self.comment_num = 0
        self.pass_article_count = 0
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
        self.logger.info(f'Starting Facebook Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            e = self.get_by_xpath('//input[@type="text"]')
            for i_key in self.config['params']['site']['userid']:
                self.send_keys(e, i_key)
                time.sleep(self.delay_a)

            # 암호 입력
            e = self.get_by_xpath('//input[@type="password"]')
            for i_key in self.config['params']['site']['passwd']:
                self.send_keys(e, i_key)
                time.sleep(self.delay_a)
            self.send_keys(e, Keys.ENTER)
            self.implicitly_wait(after_wait=2)

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
        # 검색 단추 클릭
        self.implicitly_wait(after_wait=4)
        # e = self.get_by_xpath('//div[@class="k4urcfbm j83agx80 bp9cbjyn"]/label/input')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=2)
        # pyautogui.moveTo(140, 160)
        # pyautogui.click()

        # 검색어 입력
        # e = self.get_by_xpath('//div[@class="k4urcfbm j83agx80 bp9cbjyn"]/label/input')
        # for key in self.config['params']['site']['search']:
        #     self.send_keys(e, key)
        #     time.sleep(self.delay_a)
        # self.send_keys(e, Keys.ENTER)
        # pyperclip.copy(self.config['params']['site']['search'])
        # pyautogui.hotkey('ctrl', 'v', interval=0.15)
        # self.implicitly_wait(after_wait=1)
        # pyautogui.hotkey('enter')
        # self.implicitly_wait(after_wait=2)

        # 필터 선택
        e = self.get_by_xpath('//div[@class="rq0escxv l9j0dhe7 du4w35lb j83agx80 cbu4d94t pfnyh3mw d2edcug0 aahdfvyu tvmbv18p"][2]/div[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=3)

        # 최신순 클릭 (방법이 바뀌는 경우가 있음.)
        # 1번
        # self.driver.find_element_by_xpath('//body').send_keys(Keys.TAB)
        # self.driver.find_element_by_xpath('//body').send_keys(Keys.TAB)
        # self.driver.find_element_by_xpath('//body').send_keys(Keys.TAB + Keys.SPACE + Keys.ARROW_DOWN + Keys.SPACE)
        # 2번
        e = self.driver.find_element_by_xpath('//input[@aria-label="최근 게시물"]')
        self.safe_click(e)
        self.implicitly_wait(imp_wait=5, after_wait=4)

        # 상단 배너 삭제
        e = self.driver.find_element_by_xpath('//div[@role="banner"]')
        self.driver.execute_script("""
                                var element = arguments[0];
                                element.parentNode.removeChild(element);
                                """, e)

    # ==========================================================================
    def get_re_recomment(self, msg, re_cmt_e, parent_comment_id):
        try:
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            re_re_cmt = {
                'comment_id': None,
                'is_reply': True,
                'parent_comment_id': parent_comment_id,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': [],
            }
            e_y = re_cmt_e.find_element_by_xpath('.//ul/li/a[@tabindex]/span')
            re_re_cmt['create_ts'] = self.get_create_datetime(e_y.text)

            # 대댓글 nickname
            e = re_cmt_e.find_element_by_xpath('.//div/span/a[@tabindex]/span/span')
            self.move_to_element(e)
            re_re_cmt['nickname'] = e.text.strip()

            # 대댓글 아이디 댓글 넘버링 + 닉네임
            re_re_cmt['comment_id'] = "_".join([str(self.comment_num), re_re_cmt['nickname']])
            self.comment_num += 1

            # 대댓글 내용 (더보기 존재)
            inner_html = re_cmt_e.get_attribute('innerHTML')
            if inner_html.find('kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql') > 0:
                e = re_cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                if e.get_attribute('innerHTML').find(">더보기<") > 0:
                    self.safe_click(e.find_element_by_xpath('.//div[@role="button"]'))
                    e = re_cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                re_re_cmt['contents'] = e.text.strip()

            # 대댓글 공감
            inner_html = re_cmt_e.get_attribute('innerHTML')
            if inner_html.find('du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1') > 0:
                e = re_cmt_e.find_element_by_xpath('.//div[@class="du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1"]')
                re_re_cmt['like'] = self.get_num_from_str(e.text.strip())
            else:
                re_re_cmt['like'] = 0

            # 대댓글 이미지
            re_re_cmt['comment_img_url'] = []
            re_re_cmt['comment_img'] = []
            e = re_cmt_e.find_element_by_xpath('.//div[@class="rj1gh0hx buofh1pr ni8dbmo4 stjgntxs hv4rvrfc"]')
            inner_html = e.get_attribute('innerHTML')
            if inner_html.find('j83agx80 bvz0fpym c1et5uql') > 0:
                re_img = re_cmt_e.find_element_by_xpath('.//div[@class="j83agx80 bvz0fpym c1et5uql"]//img')
                re_re_cmt['comment_img_url'].append(re_img.get_attribute('src'))  # src가 이미지 주소
                re_re_cmt['comment_img'].append(f'{re_re_cmt["comment_id"] + "_0"}.png')
                if self.config['params']['kwargs']['headless']:
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{re_re_cmt["comment_id"]+"_0"}.png')
                    re_img.screenshot(msg_capture_f)
            # 댓글 목록에 추가
            msg['comment_list'].append(re_re_cmt)

            self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {re_re_cmt["comment_id"]} 대대댓글')
        except:
            ...

    # ==========================================================================
    def get_recomment(self, msg, re_cmt_e, parent_comment_id):
        try:
            delay_c = random.uniform(
                self.config['params']['site']['delay']['comment']['min'],
                self.config['params']['site']['delay']['comment']['max'],
            )
            time.sleep(delay_c)
            re_cmt = {
                'comment_id': None,
                'is_reply': True,
                'parent_comment_id': parent_comment_id,
                'create_ts': None,
                'nickname': None,
                'contents': None,
                'like': None,
                'dislike': None,
                'comment_img': [],
                'comment_img_url': [],
            }
            e_y = re_cmt_e.find_element_by_xpath('.//ul/li/a[@tabindex]/span')
            re_cmt['create_ts'] = self.get_create_datetime(e_y.text)

            # 대댓글 nickname
            e = re_cmt_e.find_element_by_xpath('.//div/span/a[@tabindex]/span/span')
            self.move_to_element(e)
            re_cmt['nickname'] = e.text.strip()

            # 대댓글 아이디 댓글 넘버링 + 닉네임
            re_cmt['comment_id'] = "_".join([str(self.comment_num), re_cmt['nickname']])
            self.comment_num += 1

            # 대댓글 내용 (더보기 존재)
            inner_html = re_cmt_e.get_attribute('innerHTML')
            if inner_html.find('kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql') > 0:
                e = re_cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                if e.get_attribute('innerHTML').find(">더보기<") > 0:
                    self.safe_click(e.find_element_by_xpath('.//div[@role="button"]'))
                    e = re_cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                re_cmt['contents'] = e.text.strip()

            # 대댓글 공감
            inner_html = re_cmt_e.get_attribute('innerHTML')
            if inner_html.find('du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1') > 0:
                e = re_cmt_e.find_element_by_xpath('.//div[@class="du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1"]')
                re_cmt['like'] = self.get_num_from_str(e.text.strip())
            else:
                re_cmt['like'] = 0
            # 대댓글 이미지
            re_cmt['comment_img_url'] = []
            re_cmt['comment_img'] = []
            e = re_cmt_e.find_element_by_xpath('.//div[@class="rj1gh0hx buofh1pr ni8dbmo4 stjgntxs hv4rvrfc"]')
            inner_html = e.get_attribute('innerHTML')
            if inner_html.find('j83agx80 bvz0fpym c1et5uql') > 0:
                re_img = re_cmt_e.find_element_by_xpath('.//div[@class="j83agx80 bvz0fpym c1et5uql"]//img')
                re_cmt['comment_img_url'].append(re_img.get_attribute('src'))  # src가 이미지 주소
                re_cmt['comment_img'].append(f'{re_cmt["comment_id"] + "_0"}.png')
                if self.config['params']['kwargs']['headless']:
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{re_cmt["comment_id"]+"_0"}.png')
                    re_img.screenshot(msg_capture_f)

            # 댓글 목록에 추가
            msg['comment_list'].append(re_cmt)

            # 대대댓글 찾기, 답글이 있는지 우선 클릭
            e = re_cmt_e.find_element_by_xpath("./div[2]")
            if e.text.find("답글") >= 0:
                self.safe_click(e)
                self.implicitly_wait(after_wait=2)
            re_es = re_cmt_e. find_elements_by_xpath('./div')
            del re_es[0]
            if len(re_es) != 0:
                rre_es = re_cmt_e.find_elements_by_xpath('./div/ul/li')
                for rre_e in rre_es:
                    self.get_re_recomment(msg, rre_e, re_cmt['comment_id'])
                    self.driver.execute_script("""
                     var element = arguments[0];
                     element.parentNode.removeChild(element);
                     """, rre_e)
                    if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                        self.is_done = True
                        return

            self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {re_cmt["comment_id"]} 대댓글')
        except:
            ...

    # ==========================================================================
    def get_comment(self, msg, cmt_e, parent_comment_id=""):
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
            # 댓글 작성 시간
            # e_y = cmt_e.find_element_by_xpath('.//ul/span/a[@tabindex]/span/span')
            e_y = cmt_e.find_element_by_xpath('.//ul/li/a[@tabindex]/span')
            cmt['create_ts'] = self.get_create_datetime(e_y.text)

            # 댓글 nickname
            e = cmt_e.find_element_by_xpath('.//div/span/a[@tabindex]/span/span|.//span/span/a[@tabindex]/span/span')
            self.move_to_element(e)
            cmt['nickname'] = e.text.strip()

            # 댓글 아이디 댓글 넘버링 + 닉네임
            cmt['comment_id'] = "_".join([str(self.comment_num), cmt['nickname']])
            self.comment_num += 1

            # 대댓글인지 댓글인지
            cmt['parent_comment_id'] = parent_comment_id
            if parent_comment_id == "":
                cmt['is_reply'] = False
                parent_comment_id = cmt['comment_id']
            else:
                cmt['is_reply'] = True

            # 댓글 내용 (더보기 존재, xpath가 없을 수도 있음...)
            inner_html = cmt_e.get_attribute('innerHTML')
            if inner_html.find('kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql') > 0:
                e = cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                if e.get_attribute('innerHTML').find(">더보기<") > 0:
                    self.safe_click(e.find_element_by_xpath('.//div[@role="button"]'))
                    e = cmt_e.find_element_by_xpath('.//div[@class="kvgmc6g5 cxmmr5t8 oygrvhab hcukyx3x c1et5uql"]')
                cmt['contents'] = e.text.strip()

            # 댓글 공감
            like_num = 0
            e = cmt_e.find_element_by_xpath('.//div[@class="k4urcfbm sf5mxxl7 l9j0dhe7 pq6dq46d"]')
            if e.get_attribute('innerHTML').find('du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1') > 0:
                e = cmt_e.find_element_by_xpath('.//div[@class="du4w35lb pmk7jnqg lthxh50u ox23h4wi kr9hpln1"]')
                like_num = self.get_num_from_str(e.text.strip())
            cmt['like'] = like_num

            # 댓글 이미지
            cmt['comment_img_url'] = []
            cmt['comment_img'] = []
            # inner_html = cmt_e.get_attribute('innerHTML')
            if inner_html.find('j83agx80 bvz0fpym c1et5uql') > 0:
                re_img = cmt_e.find_element_by_xpath('.//div[@class="j83agx80 bvz0fpym c1et5uql"]//img')
                cmt['comment_img_url'].append(re_img.get_attribute('src'))  # src가 이미지 주소
                cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')
                if self.config['params']['kwargs']['headless']:
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{cmt["comment_id"]+"_0"}.png')
                    re_img.screenshot(msg_capture_f)

            # 댓글 목록에 추가
            msg['comment_list'].append(cmt)

            # 대댓글이 있는지 확인
            e = cmt_e.find_element_by_xpath("./div[2]")
            if e.text.find("답글") >= 0:
                self.safe_click(e)
                self.implicitly_wait(after_wait=2)
                while True:
                    re_cmt_es = cmt_e.find_elements_by_xpath('./div/div/ul/li')
                    if len(re_cmt_es) == 0:
                        break
                    for re_cmt_e in re_cmt_es:
                        self.get_recomment(msg, re_cmt_e, parent_comment_id)
                        # 댓글 크롤링후 element삭제
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, re_cmt_e)
                        if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                            self.is_done = True
                            return
                    a = cmt_e.find_element_by_xpath('./div/div/div[@class="ni8dbmo4 stjgntxs l9j0dhe7 d0szoon8"][2]|'
                                                    './/div/div/div[@class="rj1gh0hx buofh1pr ni8dbmo4 stjgntxs rz4wbd8a"]')
                    if a.text == '' or a.text.find('글을 게시하려면 Enter 키를 누르세요.') > 0:
                        break
                    self.safe_click(a)
                    self.implicitly_wait(after_wait=1)

            self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        except:
            ...

    # # ==========================================================================
    # def _screenshot(self, f):
    #     S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
    #     self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
    #     self.driver.find_element_by_tag_name('body').screenshot(f)

    # ========================================================================
    def get_article(self, msg, ndx, e_ab):
        try:
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            # self.switch_to_main_window()
            self.switch_to_window(0)
            self.move_to_element(e_ab)
            # 작성자
            e = e_ab.find_element_by_xpath('.//a[@tabindex="0"]/strong/span|.//a[@tabindex="0"]/span')
            msg['author'] = e.text.strip()
            # 아이티에 특수문자제거 파일 이름으로 사용
            article_id = re.sub(r'[^0-9]', '', msg['create_ts']) + '_' + msg['author'] + '_' + str(ndx)
            msg['article_id'] = re.sub(r'[\/:*?"<>|]', '', article_id)

            self.logger.info(f'Page[{self.cur_page}:{ndx+1}],article_id[{msg["article_id"]}],url={msg["article_url"]}')

            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                e_ab.screenshot(msg_capture_f)

                # # 새로고침 본문의 xpath 테이블이 첫번째로 정렬됨 가비지 게시글이 사라짐.
            # self.driver.refresh()
            # self.implicitly_wait(after_wait=1)
            # 가비지 게시글들은 걸러내기 위함. 내용이있는 게시글을 가져옴(첫번째)
            # e_as = self.driver.find_elements_by_xpath('//div[@class="rq0escxv l9j0dhe7 du4w35lb hybvsw6c io0zqebd m5lcvass fbipl8qg nwvqtn77 k4urcfbm ni8dbmo4 stjgntxs sbcfpzgs"]')
            # e_ab = e_as[ndx]

            # # 공유 수 : 없으면 창 자체가 없기에 0으로 줌
            # try:
            #     e = e_ab.find_element_by_xpath('.//div/span/div[@tabindex="0"]/span[@dir="auto"]')
            #     e_s = e.text.partition(' ')[2].strip()
            #     msg['share'] = self.get_num_from_str(e_s)
            # except:
            #     msg['share'] = 0
            # 댓글 수
            # 댓글 수가 없으면 창 자체가 없기에 0으로 줌 / 댓글 1.2천개로 표시 확인
            try:
                e = e_ab.find_element_by_xpath('.//div[@class="gtad4xkn"]/div/span')
                e_n = e.text.partition(' ')[2].strip()
                msg["num_comments"] = self.get_num_from_str(e_n)
            except:
                msg["num_comments"] = 0

            # 게시글 내용(사진만 있는경우도 존재)
            try:
                e = e_ab.find_element_by_xpath('.//div[@data-ad-comet-preview="message"]')
                msg['contents'] = e.text.strip()
            except:
                msg['contents'] = ''
            # 3) 감정 (공감수만 체크)
            try:
                e = e_ab.find_element_by_xpath('.//span[@class="gpro0wi8 cwj9ozl2 bzsjyuwj ja2t1vim"]/span/span')
                msg['like'] = self.get_num_from_str(e.text.strip())
            except:
                msg['like'] = 0

            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e_ab.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('origin-when-cross-origin') > 0:
                for j, sub_e in enumerate(e_ab.find_elements_by_xpath('.//div/img[@referrerpolicy="origin-when-cross-origin"]')):
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 댓글이 있는지 여부
            if msg["num_comments"] == 0:
                return
            msg['comment_list'] = []
            # 댓글 달기 클릭 (댓글달기가 없는 경우가 있음. 그 경우 댓글 갯수 클릭)
            e = e_ab.find_element_by_xpath('.//div[@aria-label="댓글 남기기"]|.//div[@class="gtad4xkn"]/div/span')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 날짜별 내림차순으로 댓글 보기, 댓글수가 적으면 없을 수도....

            try:
                e = e_ab.find_element_by_xpath('.//div[@class="j83agx80 bkfpd7mw jb3vyjys hv4rvrfc qt6c0cv9 dati1w0a l9j0dhe7"]/div')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
                e_ms = self.driver.find_elements_by_xpath('//div[@role="menuitem"]')
                for j, e_m in enumerate(e_ms):
                    if e_m.text.find('날짜 내림차순') >= 0 or e_m.text.startswith('최신 댓글'):
                        self.safe_click(e_m)
                        self.implicitly_wait(after_wait=1)
                        break
                    elif j == len(e_ms)-1 and e_m.text.startswith('모든 댓글'):
                        self.safe_click(e_m)
                        self.implicitly_wait(after_wait=1)
                        break

            except:
                ...
            # 댓글 n개 더 보기
            # 답글 더 보기도 누름
            # element 지우는 것
            # self.driver.execute_script("""
            # var element = arguments;
            # element.parentNode.removeChild(element);
            # """, e)
            self.comment_num = 0
            # 이전댓글 클릭은 우선 눌러줘야함.
            try:
                e = e_ab.find_element_by_xpath('.//div[@class="cwj9ozl2 tvmbv18p"]/div/div/div/span')
                if e.text.find('이전') >= 0:
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=0.5)
            except:
                pass
            try:
                while True:
                    # 더보기
                    e = self.get_by_xpath('//div[@class="d2edcug0 o7dlgrpb"]')
                    e_a = e.find_elements_by_xpath('./div')[ndx]
                    e_s = e_a.find_elements_by_xpath('.//div[@class="cwj9ozl2 tvmbv18p"]/ul/li')
                    if len(e_s) == 0:
                        break
                    for e in e_s:
                        self.get_comment(msg, e)
                        # 댓글 크롤링후 element삭제
                        self.driver.execute_script("""
                        var element = arguments[0];
                        element.parentNode.removeChild(element);
                        """, e)
                        # 댓글 개수 제한.
                        if self.config['params']['site']['max_comment'] == len(msg['comment_list']):
                            self.is_done = True
                            return

                    # 더보기 체크(이전 댓글보기로 표기되는 경우도 존재 이전댓글...누르니까 이상해짐.)
                    cmt_p = e_a.find_element_by_xpath(
                        './/div[@class="cwj9ozl2 tvmbv18p"]/*[6]|.//div[@class="cwj9ozl2 tvmbv18p"]/div/div/div/span')
                    if cmt_p.text == '':
                        break
                    self.safe_click(cmt_p)
                    self.implicitly_wait(imp_wait=10, after_wait=2)
            except:
                pass
            # e = self.get_by_xpath('//div[@class="d2edcug0 o7dlgrpb"]')
            # e_s = e.find_elements_by_xpath('./div')
            # e_a = e_s[ndx]
            # self.get_comment(msg)

        except Exception as err:
            raise
        finally:
            if msg["num_comments"] != 0:
                self.logger.info(f'댓글수 {msg["num_comments"]} /  수집 댓글수 {len(msg["comment_list"])}')
                msg["num_comments"] = len(msg["comment_list"])

        #     # 이전 페이지
        #     self.driver.back()
        #     self.implicitly_wait(after_wait=1)
        #     try:
        #         self.switch_to_window(0)
        #     except:
        #         # selenium.common.exceptions.WebDriverException: Message: unknown error:
        #         # cannot determine loading status
        #         pass

    # ==========================================================================
    def get_create_datetime(self, t):
        _t = t
        www, ddd, hhh, mmm = 0, 0, 0, 0
        d_time = ""
        if _t.find('분') > 0:
            mm = re.sub(r'[^0-9]', '', _t)
            mmm = int(mm)
        elif _t.find('시간') > 0:
            hh = re.sub(r'[^0-9]', '', _t)
            hhh = int(hh)
        elif _t.find('일') > 0:
            dd = re.sub(r'[^0-9]', '', _t)
            ddd = int(dd)
        elif _t.find('주') > 0:
            ww = re.sub(r'[^0-9]', '', _t)
            www = int(ww)
        elif _t.find('년') > 0:
            yy = re.sub(r'[^0-9]', '', _t)
            ddd = int(yy) * 365
        else:
            e_re = datetime.datetime.strptime(_t, '%b %d. %Y').strftime('%Y.%m.%d')
            d_time = e_re + ' 00:00:00'
        try:
            if d_time == "":
                d = datetime.datetime.now() - timedelta(weeks=www, days=ddd, hours=hhh, minutes=mmm)
                d_time = d.strftime('%Y.%m.%d %H:%M:%S')
        except:
            pass
        return d_time

    # ==========================================================================
    def get_num_from_str(self, s):
        # s = 1.5만개 or 1.4천회
        if s == '':
            s = '1'
        _s = s
        try:
            if _s.endswith(('개', '회')):
                _s = _s[:-1]
            times = 1
            if _s.endswith('천'):
                times = 1000
                _s = _s[:-1]
            elif _s.endswith('만'):
                times = 10000
                _s = _s[:-1]
            f = float(_s)
            f *= times
            return int(f)
        except Exception as err:
            self.logger.error(f'in _get_num_from_str: Cannot parse into int for "{s}"')
            raise

    # ==========================================================================
    def get_emotion(self, msg):
        try:
            # 3) 감정
            like = 'https://scontent.xx.fbcdn.net/m1/v/t6/An-tsvy1nZCAfjJDq_e9hwhgJ_ouDg6GOHdVQtc31Lh3B13GEFJ0N3wRI6j2_Lz8icCyU4RkVsKbJckG5NMDv5TxxWie8OqB_kcvCNizVjn7sw.png?ccb=10-5&oh=00_AT-dIXDyFR8OyrsMIzXano6Xy1AWr_QQz0dmpSzQhlUqjw&oe=61F3CE6D&_nc_sid=55e238'
            # best = 'https://scontent.xx.fbcdn.net/m1/v/t6/An8KxJw0TdKA0hIHqkw35xWvBGYLLbtgD5y14_K8iN_zaDhCWgixktWzvqA45BTxHACGktnPMx_lkq1uE66153QNE58NZp59iYz6MDdtqgcTZw.png?ccb=10-5&oh=00_AT_dpzUxZDBLvF-y5Mt4vLG_ezk_FrFhBDNc_4ICEk7cag&oe=61F23095&_nc_sid=55e238'
            best = 'https://scontent.xx.fbcdn.net/m1/v/t6/An8KxJw0TdKA0hIHqkw35xWvBGYLLbtgD5y14_K8iN_zaDhCWgixktWzvqA45BTxHACGktnPMx_lkq1uE66153QNE58NZp59iYz6MDdtqgcTZw.png?ccb=10-5&oh=00_AT9vzXwJyIeBjY1tq37vutiypnUXtJK65Ptx9UPVlAQSoQ&oe=61F42AD5&_nc_sid=55e238'
            cheer_up = 'https://scontent.xx.fbcdn.net/m1/v/t6/An-zbifsrGonJXBikRGgj1txFJUkRG3aCN5900mzKo6dVL8tKCuWwF6D9Ov6XB3JJZ7pT1FSxuFsETOjkjZ08b5AyPU0z_GsxZH2nWiW2ScJT4p3rQ.png?ccb=10-5&oh=00_AT-naILguCDbJCZ6sZhjj7Lfk9UStT16conaOpOaHO2ovQ&oe=61F415A3&_nc_sid=55e238'
            # fun = 'https://scontent.xx.fbcdn.net/m1/v/t6/An9yRlv3tqyIsDTiKV0WfMgtabNG9VPyvNiv5USdzPe0Cbp2FdNMvbGH1mvTvI8TczUcd9kED-M5Q1z9-fVK3zAMCRSiYtsWTpWSid0DJlPasg.png?ccb=10-5&oh=00_AT_x1_67RIoI1cMRn-6ZS5lg0CNMxlzj-al2vv0DnWT-PQ&oe=61F3421D&_nc_sid=55e238'
            fun = 'https://scontent.xx.fbcdn.net/m1/v/t6/An9yRlv3tqyIsDTiKV0WfMgtabNG9VPyvNiv5USdzPe0Cbp2FdNMvbGH1mvTvI8TczUcd9kED-M5Q1z9-fVK3zAMCRSiYtsWTpWSid0DJlPasg.png?ccb=10-5&oh=00_AT9veCcnbYJJ8KvcsRjmJvmYtZuLYRYmIteaiC1joReAEw&oe=61F53C5D&_nc_sid=55e238'
            cool = 'https://scontent.xx.fbcdn.net/m1/v/t6/An_f5KryEO3JdbkuRbEs1ixj8HC8itKTXvZ3Hl1c-zaREaiMDPCRTNw6CSwRUjKkq_YXEuxmsqBu06WIeteZ7MBZ2WKuJXvOK6WdOQfGi2Ixg9Sd.png?ccb=10-5&oh=00_AT94B9g-euffWJ0_fRC3EtzSnOazKJOjcRLgjWM3ezi62Q&oe=61F3C254&_nc_sid=55e238'
            sad = 'https://scontent.xx.fbcdn.net/m1/v/t6/An9Yzzh8CoEGqeWIfY5w6zR3VdPbG5X1fHXZdMfftnoomx3ObysBj145G99ZhM1T6DcU_ZAH2bEdiOj8sUAQvplVo0cYKS_GprBBJlcwiBHomFx7hQ.png?ccb=10-5&oh=00_AT-5uFTr-QyRo7875l3iM5XaS925paePxM6jLLbeyJgfeQ&oe=61F31ACF&_nc_sid=55e238'
            angry = 'https://scontent.xx.fbcdn.net/m1/v/t6/An-mj0uPEZ5b6GVy3OC-_ZMV1AGoboZI3SG9P2r3WElt054OlpAmUSq9QPU0i9RdhF07UwCRHIsC06i-w4_VCrnJnBEent1vmcy8MXOQt0msew.png?ccb=10-5&oh=00_AT-yEqPJmbHph3oN9o8nTuQmhr2h2R6ohLHauofQBB7OhA&oe=61F3ACC1&_nc_sid=55e238'

            msg['like'] = 0
            msg['Best'] = 0
            msg['cheer_up'] = 0
            msg['fun'] = 0
            msg['cool'] = 0
            msg['sad'] = 0
            msg['angry'] = 0

            e_emotion = self.get_by_xpath('//div[@aria-label="공감"]//div[@class="ni8dbmo4 stjgntxs kr9hpln1"]', timeout=1)
            emotion_es = e_emotion.find_elements_by_xpath('.//img')

            for emotion_e in emotion_es:
                emotion_img = emotion_e.get_attribute('src')
                emotion_count = emotion_e.find_element_by_xpath('./../../span').get_attribute('innerHTML')
                # (모두 포함) 감정들 각각의 개수
                if emotion_img == like:
                    msg['like'] = self.get_num_from_str(emotion_count)
                elif emotion_img == best:
                    msg['Best'] = self.get_num_from_str(emotion_count)
                elif emotion_img == cheer_up:
                    msg['cheer_up'] = self.get_num_from_str(emotion_count)
                elif emotion_img == fun:
                    msg['fun'] = self.get_num_from_str(emotion_count)
                elif emotion_img == cool:
                    msg['cool'] = self.get_num_from_str(emotion_count)
                elif emotion_img == sad:
                    msg['sad'] = self.get_num_from_str(emotion_count)
                elif emotion_img == angry:
                    msg['angry'] = self.get_num_from_str(emotion_count)
        except:
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
                # self.logger.error(f'Stop crawling because article create_ts "{create_ts}" '
                #                   f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

        # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            self.switch_to_window(0)

            count_a = 0
            while True:
                # 페이지 테이블 구하기
                try:
                    e = self.get_by_xpath('//div[@class="d2edcug0 o7dlgrpb"]', timeout=1)
                except:
                    search_e = self.get_by_xpath(
                        '//div[@class="gm7ombtx jbae33se gpl4oick bjjx79mm taijpn5t cbu4d94t j83agx80 bp9cbjyn"]',
                        timeout=1)
                    self.logger.info(search_e.text.split('\n')[0])
                    self.is_done = True
                    return
                e_s = e.find_elements_by_xpath('./div')
                e_a = e_s[count_a]
                msg = {
                    'page': self.cur_page,
                    'row': count_a,
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
                    # 1) 게시물 주소: article_url, 특정 동작을 주어야 url이 보임
                    try:
                        e_url = e_a.find_element_by_xpath('.//span[@class="jpp8pzdo"]/../span[2]/span/a')
                    except :
                        # 결과 끝
                        search_e = self.get_by_xpath('//div[@class="l9j0dhe7 du4w35lb rq0escxv j83agx80 cbu4d94t pfnyh3mw d2edcug0 pybr56ya"]', timeout=1)
                        self.logger.info(search_e.text)
                        self.is_done = True
                        return
                    action = ActionChains(self.driver)
                    action.click_and_hold(e_url).perform()
                    action.click_and_hold(e_a).perform()
                    self.implicitly_wait(after_wait=1)
                    e_url = e_a.find_element_by_xpath('.//span[@class="jpp8pzdo"]/../span[2]/span/a')
                    a_url = e_url.get_attribute('href')
                    msg['article_url'] = a_url
                    self.move_to_element(e_url)
                    # if a_url.find('/posts') > 0:
                    #     # v = a_url.partition('/posts/')[0].rpartition('/')[2]
                    #     # n = a_url.partition('/posts/')[2].partition('?')[0].replace('/', '')
                    #     msg['article_id'] = 'post_' + str(msg['row'])
                    # elif a_url.find('_fbid') > 0:
                    #     v = a_url.partition('fbid=')[2].partition('&id=')[0]
                    #     n = a_url.partition('fbid=')[2].partition('&id=')[2].partition('&_')[0]
                    #     msg['article_id'] = v + '_' + n
                    # else:
                    #     continue

                    # 2) 게시글 작성시간 : create_ts (종류가 다양함.)
                    a_ts = e_url.get_attribute('aria-label')
                    ddd, hhh, mmm = 0, 0, 0
                    msg['create_ts'] = ""
                    # 38분
                    if a_ts.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', a_ts)
                        mmm = int(mm)
                    # 5시간
                    elif a_ts.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', a_ts)
                        hhh = int(hh)
                    # 3일
                    elif a_ts.find('일') > 0 > a_ts.find('월'):
                        dd = re.sub(r'[^0-9]', '', a_ts)
                        ddd = int(dd)
                    # 3월 15일 오전 1:12
                    elif a_ts.find('오전') > 0 or a_ts.find('오후') > 0:
                        t = str(datetime.datetime.strptime(a_ts.replace('오후', 'PM').replace('오전', 'AM'),'%m월 %d일 %p %I:%M')).replace('-','.')[4:]
                        tl = str(datetime.datetime.now().year) + t
                        msg['create_ts'] = tl
                    #  2월 12일
                    elif a_ts.find('일') > 0 < a_ts.find('월') and a_ts.find('년') == -1:
                        msg['create_ts'] = str(datetime.datetime.now().year) + '.' + a_ts.replace('월 ', '.')[:-1] + ' 00:00:00'
                    # 2021년 3월 2일
                    else:
                        msg['create_ts'] = a_ts.replace('년 ', '.').replace('월 ', '.').replace('일', '') + ' 00:00:00'

                    if msg['create_ts'] == "":
                        d = datetime.datetime.now() - timedelta(days=ddd, hours=hhh, minutes=mmm)
                        msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                    # 작성시간체크
                    if self.stop_article_older_than(msg):
                        # self.logger.error(f'Stop crawling because article create_ts "{create_ts}" '
                        #                   f'is older than "{old_ts}"')
                        self.logger.debug(f"Page[{self.cur_page}:{count_a}]"
                                          f", Pass article  because article create_ts '{msg['create_ts']}'"
                                          f"is older than {self.config['params']['site']['stop_article_older_than']['datetime']}.")
                        # 두번째 게시물로 이동.
                        count_a += 1
                        self.pass_article_count += 1
                        if self.pass_article_count == 5:
                            self.logger.debug(f'Stop crawling with {self.pass_article_count} old articles')
                            self.is_done = True
                            return
                        continue

                    # self.safe_click(e_url)
                    # self.implicitly_wait(after_wait=2)
                    self.get_article(msg, count_a, e_a)

                except Exception as err:
                    # 페이스북에는 필요없을지...
                    # if msg['article_id'] is None:
                    #     self.logger.error(f'Cannot find Result!')
                    #     self.is_done = True
                    #     break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

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
                # 두번째 게시물로 이동.
                count_a += 1
                e = self.get_by_xpath('//div[@class="d2edcug0 o7dlgrpb"]')
                e_s = e.find_elements_by_xpath('./div')
                e_a = e_s[count_a]
                self.move_to_element(e_a)
                self.implicitly_wait(after_wait=2)

        except Exception as err:
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
                        self.logger.info(f'save_img: {j}.png : retry{count}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

        # 댓글 이미지
        # 헤드리스일경우 댓글이미지를 캡쳐함.
        if self.config['params']['kwargs']['headless']:
            return
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
                    urllib.request.urlretrieve(cmt_url, cmt_img_f)
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
        # pickle.dump(self.driver.get_cookies(), open("cookies.pkl", "wb"))
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument("disable-gpu")

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['params']['kwargs']['url']+'/search/top?q='+self.config['params']['site']['search'])
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)

        self.driver.set_window_size(self.config['params']['kwargs']['width'],
                                    self.config['params']['kwargs']['height'])

        # 새로고침
        self.driver.refresh()
        self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def a_cookie(self):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            self.driver.add_cookie(cookie)
        # 새로고침
        # self.driver.refresh()
        self.driver.get(
            self.config['params']['kwargs']['url'] + '/search/top?q=' + self.config['params']['site']['search'])
        self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            if self.search_index == 0:
                self.login()
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
            print(self.output['latest_create_article_ts'])
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
            with FacebookSearch(kwargs['config_f'], keyword, i) as ws:
                ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'facebook.yaml'
    do_start(config_f=_config_f)
