"""
====================================
 :mod:`app/google_playstore`
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
#  * [2024/03/27]
#     - 에러코드 세분화
#  * [2023/02/10]
#     - title부분에 사이트명으로 변경
#  * [2022/12/5]
#     - 앱정보 내용 xpath 변경
#  * [2022/10/25] Kyobong
#     - 작성자이름에 특이 케이스 발생. article_id에 양쪽 공백제거
#  * [2022/10/12] Kyobong
#     - 에러 return이 정상적으로 안되는 문제발생 raise로 return을 대신함. 플러그인 리턴에러는 1
#  * [2022/10/07] Kyobong
#     - api error날 경우 return 9
#  * [2022/06/28] Kyobong
#     - 이미지 제거
#  * [2022/06/23] Kyobong
#     - app 정보 page 캡쳐 파일 이름 변경 메타 json과 동일
#  * [2022/06/14] Kyobong
#     - appid 설정
#  * [2022/06/10] Kyobong
#     - title value ''로 수정
#  * [2022/06/09] Kyobong
#     - 앱리뷰 api로 변경.  기존 가져오던 url이 변경됨
#  * [2022/04/21] Kyobong
#     - 앱 정보창 닫는 xpath가 변경됨.
#  * [2022/04/18] Kyobong
#     - "update_date"의 xpath추가 업데이트 되면서 형식이 변경된듯.
#  * [2022/02/14] Kyobong
#     - Code Clearing. 수집에 필요없는 내용 주석처리, (값, file, folder)이름 수정.
#  * [2021/12/24]
#     - GooglePlaystoreReview 을 이용하여 최신 순 가져오기
#     - 리뷰의 하단으로 내려가면서 동적으로 늘려가는 경우 처리
#     - review 별로 별도 저장 시점 조종, save_review()
#     - start() 에서 save()를 finally 블락으로 이동
#     - 입력에 stop_review_older_than 조건 추가, stop_review_older_than() 에서 처리
#     - 리뷰 별 delay/review 적용
#  * [2021/12/13]
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
from pathlib import Path
from copy import deepcopy, copy
from urllib.request import urlretrieve
from google_play_scraper import Sort, reviews
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
class GooglePlaystoreReview_API(object):
    # https://play.google.com/store/apps/details?id=com.sampleapp&hl=ko&gl=US
    # URL = 'https://play.google.com/store/apps/details?id={appid}&hl=ko&gl=US'

    # ==========================================================================
    def __init__(self, config):
        self.config = config
        kwargs = copy(config['params']['kwargs'])
        self.logger = kwargs['logger']
        p_url = kwargs['url']
        self.appid = p_url[p_url.find('?id=')+4:]

        # for output
        self.review_list = list()
        self.is_done = False
        self.logger.info(f'Starting Google Playstore Review Crawaling...')
        self.latest_create_article_ts = None

    # ==========================================================================
    @staticmethod
    def get_safe_path(*_args):
        if sys.platform == 'win32':
            args = []
            for i in range(len(_args)):
                args.append(_args[i].replace('/', '\\'))
        else:
            args = _args
        p = os.path.join(*args)
        d = os.path.dirname(p)
        if not os.path.exists(d):
            os.makedirs(d)
        return p

    # ==========================================================================
    def get_review_api(self):
        try:
            review_data_list, _ = reviews(self.appid,
                                          lang="ko",
                                          country="us",
                                          sort=Sort.NEWEST,
                                          count=self.config['params']['site']['max_articles']
                                          )
            for i, review_data in enumerate(review_data_list):
                is_reply = None
                if review_data['replyContent']:
                    comment_id = nickname = 'developer'
                    dev_create_ts = review_data['repliedAt'].strftime('%Y.%m.%d %H:%M:%S')
                    is_reply = False
                else:
                    comment_id = nickname = None
                    dev_create_ts = None
                review = {
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    # 'site_board': self.config['params']['site']['site_board'],
                    'channel': self.config['params']['site']['channel'],
                    'search_type': self.config['params']['site']['search_type'],
                    'service': self.config['params']['site']['service'],
                    'article_id': review_data['at'].strftime('%Y%m%d%H%M%S')+'_'+re.sub(r'[\/:*?"<>|]',
                                                                                        '', review_data['userName']).strip(),
                    'create_ts': review_data['at'].strftime('%Y.%m.%d %H:%M:%S'),
                    'board_name': None,
                    'title': self.config['params']['site']['site_name'],
                    'contents': review_data['content'],
                    'author': review_data['userName'],
                    'view_count': None,
                    'good': None,
                    'great': None,
                    'sad': None,
                    'angry': None,
                    'news': None,
                    'like': None,
                    'dislike': None,
                    'star_like': review_data['score'],
                    'num_comments': None,
                    'article_url': None,
                    'image_list': [],
                    'image_url_list': [],
                    'attachment_name': [],
                    'attachment_url': [],
                    'comment_list': [
                        {
                            'comment_id': comment_id,
                            'is_reply': is_reply,
                            'parent_comment_id': None,
                            'create_ts': dev_create_ts,
                            'nickname': nickname,
                            'contents': review_data['replyContent'],
                            'like': None,
                            'dislike': None,
                            'comment_img': [],
                            'comment_img_url': [],
                        }
                    ],
                }
                if self.stop_review_older_than(review):
                    if os.path.isdir("/".join([self.config['target']['folder'], review['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], review['article_id']]))
                    self.is_done = True
                    break
                if self.latest_create_article_ts is None:
                    self.latest_create_article_ts = review['create_ts']
                self.review_list.append(review)
                if self.config['target']['is_separate_review']:
                    self.save_review(review)
                self.logger.info(f'[{i + 1}] review={review["article_id"]}')
                if len(self.review_list) >= self.config['params']['site']['max_articles']:
                    self.is_done = True
                    break
        except Exception as err:
            raise

    # ==========================================================================
    def stop_review_older_than(self, msg):
        try:
            # "2021년 12월 23일"
            create_ts = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because review create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def save_d(self, fn, d):
        fn += '.yaml' if self.config['target']['is_yaml'] else '.json'
        with open(fn, 'w', encoding='utf-8') as ofp:
            if self.config['target']['is_yaml']:
                yaml.dump(d, ofp, allow_unicode=True)
            else:
                ofp.write(json.dumps(d, ensure_ascii=False))

    # ==========================================================================
    def save_review(self, review):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            review['article_id'],
            review['article_id']
        )
        self.save_d(at_js_f, review)

    # ==========================================================================
    def start(self):
        try:
            self.get_review_api()
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            raise


################################################################################
class GooglePlaystoreReview(PySelenium):
    # https://play.google.com/store/apps/details?id=com.sampleapp&hl=ko&gl=US
    URL = 'https://play.google.com/store/apps/details?id={appid}&hl=ko&gl=US'

    # ==========================================================================
    def __init__(self, config, start_ts):
        self.config = config
        self.start_ts = start_ts
        kwargs = copy(config['params']['kwargs'])
        self.logger = kwargs['logger']
        p_url = kwargs['url']
        appid = p_url[p_url.find('?id=')+4:]
        kwargs['url'] = self.URL.format(appid=appid)
        PySelenium.__init__(self, **kwargs)
        # for output
        self.review_list = list()
        self.review_count_list = list()
        self.is_done = False
        self.logger.info(f'Starting Google Playstore Review Crawaling...')
        self.latest_create_article_ts = None

    # ==========================================================================
    def stop_review_older_than(self, msg):
        try:
            # "2021년 12월 23일"
            create_ts = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because review create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def save_d(self, fn, d):
        fn += '.yaml' if self.config['target']['is_yaml'] else '.json'
        with open(fn, 'w', encoding='utf-8') as ofp:
            if self.config['target']['is_yaml']:
                yaml.dump(d, ofp, allow_unicode=True)
            else:
                ofp.write(json.dumps(d, ensure_ascii=False))

    # ==========================================================================
    def save_review(self, review):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            review['article_id'],
            review['article_id']
        )
        self.save_d(at_js_f, review)

    # ==========================================================================
    def start(self):
        rec = re.compile(r'별표 5개 만점에 (\d+)개를 받았습니다.')
        try:
            # "리뷰 모두 보기" 누름
            e = self.get_by_xpath('//div[@jsname="wmgIXe"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # "리뷰>" 누름
            # d9BH4c CWE1Id
            e = self.get_by_xpath('(//div[@jsname="CWE1Id"])[1]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            se = e.find_element_by_xpath('(.//div[@jsname="V68bde"]/div[@jsname="wQNmvb"])[1]')
            self.safe_click(se)
            # se.set_attribute('aria-selected', 'true')
            self.implicitly_wait(after_wait=1)

            offset = 0
            while not self.is_done:
                for i, rv_e in enumerate(self.driver.find_elements_by_xpath('//div[@jsname="fk8dgd"]/div')):
                    if i < offset:
                        continue
                    delay_a = random.uniform(
                        self.config['params']['site']['delay']['review']['min'],
                        self.config['params']['site']['delay']['review']['max'],
                    )
                    time.sleep(delay_a)
                    review = {
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
                    inner_html = rv_e.get_attribute('innerHTML')
                    # reviewer icon
                    # e = rv_e.find_element_by_xpath('.//img[@class="T75of ZqMJr"]')
                    # review['reviewer_icon_url'] = e.get_attribute('src')
                    # reviewer
                    e = rv_e.find_element_by_xpath('.//span[@class="X43Kjb"]')
                    review['author'] = e.text.strip()
                    # rank
                    e = rv_e.find_element_by_xpath('.//div[@class="pf5lIe"]/div')
                    rank_s = e.get_attribute('aria-label')
                    m = rec.match(rank_s)
                    if m is not None:
                        review['star_like'] = int(m.group(1))
                    # create date : "2021년 12월 23일"
                    e = rv_e.find_element_by_xpath('.//span[@class="p2TkOb"]')
                    create_ts = e.text.strip()
                    a = create_ts.replace('년 ', '.').replace('월 ', '.').replace('일', ' 00:00:00')
                    review['create_ts'] = datetime.datetime.strptime(a, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                    # contents
                    if inner_html.find('gxjVle') > 0:
                        e = rv_e.find_element_by_xpath('.//button[@jsname="gxjVle"]')
                        self.safe_click(e)
                        time.sleep(1)
                        e = rv_e.find_element_by_xpath('.//span[@jsname="fbQN7e"]')
                        review['contents'] = e.text.strip()
                    else:
                        e = rv_e.find_element_by_xpath('.//span[@jsname="bN97Pc"]')
                        review['contents'] = e.text.strip()

                    # # 유용 count
                    # e = rv_e.find_element_by_xpath('.//div[@jscontroller="SWD8cc"]')
                    # review['useful_count'] = int(e.get_attribute('data-original-thumbs-up-count'))
                    # review['review_id'] = "{:08d}".format(i + 1)
                    review['article_id'] = "{:08d}".format(i + 1)

                    if inner_html.find('LVQB0b') >= 0:
                        review['comment_list'] = []
                        reply = {
                                'comment_id': review['article_id']+'_1',
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
                        # 응답이 있는 경우
                        re_e = rv_e.find_element_by_xpath('.//div[@class="LVQB0b"]')

                        # 응답자
                        e = re_e.find_element_by_xpath('.//span[@class="X43Kjb"]')
                        reply['nickname'] = e.text.strip()
                        # 응답일
                        e = re_e.find_element_by_xpath('.//span[@class="p2TkOb"]')
                        a = e.text.strip().replace('년 ', '.').replace('월 ', '.').replace('일', ' 00:00:00')
                        reply['create_ts'] = datetime.datetime.strptime(a, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                        # 응답내용
                        contents = re_e.text.strip()
                        reply['contents'] = '\n'.join(contents.split('\n')[1:])

                        # review['reply'] = reply
                        review['comment_list'].append(reply)
                    msg_capture_f = self.get_safe_path(self.config['target']['folder'], review['article_id'],
                                                       f'{review["article_id"]}.png')
                    rv_e.screenshot(msg_capture_f)
                    # 다음 댓글을 위한 이동.
                    self.move_to_element(rv_e)
                    if self.stop_review_older_than(review):
                        if os.path.isdir("/".join([self.config['target']['folder'], review['article_id']])):
                            shutil.rmtree("/".join([self.config['target']['folder'], review['article_id']]))
                        self.is_done = True
                        break
                    self.review_count_list.append(review)
                    if self.latest_create_article_ts is None:
                        self.latest_create_article_ts = review['create_ts']
                    # # 본문에 검색키워드가 있는지 체크
                    # if review['contents'].find(self.config['params']['site']['search']) < 0:
                    #     continue
                    self.review_list.append(review)
                    if self.config['target']['is_separate_review']:
                        self.save_review(review)
                    self.logger.info(f'[{i+1}] review={review["article_id"]}')
                    if len(self.review_list) >= self.config['params']['site']['max_articles']:
                        self.is_done = True
                        break
                self.implicitly_wait(after_wait=2)
                # 더보기 클릭
                e = self.get_by_xpath('//div[@jsname="lYU69"]')
                inner_html = e.get_attribute('innerHTML')
                if inner_html.find('class="PFAhAf"') > 0:
                    e = e.find_element_by_xpath(
                        './/div[@class="PFAhAf"]/div[@class="U26fgb O0WRkf oG5Srb C0oVfc n9lfJ M9Bg4d"]')
                    self.move_to_element(e)
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=1)

                offset = len(self.review_count_list)
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9


################################################################################
class GooglePlaystoreSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'GooglePlaystoreSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])
        # for output
        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        folder_name = "_".join(
            [str(self.config['params']['site']['site_number']),
             self.config['params']['site']['site_name'],
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
        }
        self.logger.info(f'Starting Google Playstore Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def _get_num_from_str(self, s):
        _s = s
        try:
            _s = _s.split()[-1]
            if _s.endswith('개'):
                _s = _s[:-1]
            else:
                return 0
            # "21.5만"
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
    def _get_dev_info(self, developer):
        try:
            e = self.get_by_xpath('//button[@class="VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ VxpoF"]',
                                  cond="element_to_be_clickable")
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            for fe in self.driver.find_elements_by_xpath('//div[@class="VfPpkd-WsjYwc VfPpkd-WsjYwc-OWXEXe-INsAgc KC1dQ Usd1Ac AaN0Dd  VVmwY"]'):
                te = fe.find_element_by_xpath('.//div[@class="xFVDSb"]')
                self.move_to_element(te)
                title = te.text.strip()
                e = fe.find_element_by_xpath('.//div[@class="pSEeg"]')
                if title == '웹사이트':
                    developer['website'] = e.text.strip()
                elif title == '이메일':
                    developer['email'] = e.text.strip()
                elif title == '주소':
                    developer['address'] = e.text.strip()
                elif title == '개인정보처리방침':
                    developer['personal_info'] = e.text.strip()

        finally:
            self.logger.info(f'dev_info={developer}')
            e = self.get_by_xpath('//button[@class="VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ VxpoF"]',
                                  cond="element_to_be_clickable")
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def _get_popup_app_info(self, popup_info):
        # 앱 정보 띄움
        e = self.get_by_xpath('(//div[@class="VMq4uf"])[1]/.//button',
                              cond="element_to_be_clickable")
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 아이콘
        e = self.get_by_xpath('//img[@class="T75of CepEHc AZIq5b"]',
                              cond="visibility_of_element_located")
        popup_info['icon_url'] = e.get_attribute('src')

        # 앱 이름
        e = self.get_by_xpath('//h5[@class="xzVNx"]')
        popup_info['title'] = e.text.strip()

        # 앱 정보 내용
        e = self.get_by_xpath('//div[@class="fysCi"]/div[1]')
        popup_info['contents'] = e.text.strip().replace('\n', '\\n')

        # 항목이 고정되어 있지 않아 다음의 loop 안에서 타이틀을 보고 결정
        for ai_e in self.driver.find_elements_by_xpath('//div[@class="sMUprd"]'):
            t_e = ai_e.find_element_by_xpath('.//div[@class="q078ud"]')
            self.move_to_element(t_e)
            title = t_e.text.strip()
            e = ai_e.find_element_by_xpath('.//div[@class="reAt0"]')
            if title == '버전':
                popup_info['version'] = e.text.strip()
            elif title == '업데이트 날짜':
                popup_info['update_date'] = e.text.strip()
            elif title == '필요한 Android 버전':
                popup_info['req_android_version'] = e.text.strip()
            elif title == '다운로드':
                popup_info['num_download'] = e.text.strip().split()[0]
            # elif title == '콘텐츠 등급':
            #     app_info['contents_age'] = e.text.strip()
            elif title == '상호작용 요소':
                popup_info['interaction'] = e.text.strip()
            elif title == '출시일':
                popup_info['release_date'] = e.text.strip().replace(' ', '')[:-1] + ' 00:00:00'

        # 권한
        try:
            e = self.get_by_xpath('//span[@class="TCqkTe Vvn1K"]',
                                  cond="element_to_be_clickable")
            self.safe_click(e)
            # popup_info['permission'] = {}
            pe_list = self.driver.find_elements_by_xpath('//div[@class="BlLrjc"]')
            for pe in pe_list:
                pe_n = pe.find_element_by_xpath('.//span[@class="aPeBBe"]')
                p_name = pe_n.text.strip()
                # popup_info['permission'][p_name] = list()
                # for li_e in pe.find_elements_by_xpath('.//li'):
                #     popup_info['permission'][p_name].append(li_e.text.strip())
        except:
            pass
        finally:
            self.logger.info(f'popup_info={popup_info}')
            # 닫기
            e = self.get_by_xpath('//button[@class="VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ a8Z62d"]|'
                                  '//button[@class="VfPpkd-Bz112c-LgbsSe yHy1rc eT1oJ DiOXab a8Z62d"]|'
                                  '//button[@aria-label="앱 정보 대화상자 닫기"]',
                                  cond="element_to_be_clickable")
            self.safe_click(e)

    # ==========================================================================
    def _get_other_apps(self, parent_e, app_info):
        inner_html = inner_html = parent_e.get_attribute('innerHTML')
        if inner_html.find('XfZNbf') < 0:
            return False
        title_e = parent_e.find_element_by_xpath('.//h2[@class="XfZNbf"]')
        title = title_e.text.strip()
        if title.endswith('앱 더보기'):
            app_info['same_apps'] = list()
            app_list = app_info['same_apps']
        elif title == '유사한 앱':
            app_info['similar_apps'] = list()
            app_list = app_info['similar_apps']
        else:
            return False
        for i, ae in enumerate(parent_e.find_elements_by_xpath('.//div[@class="VfPpkd-EScbFb-JIbuQc fUtUMc"]')):
            app = {}
            # 앱 아이콘
            e = ae.find_element_by_xpath('.//img[@class="T75of stzEZd"]')
            self.move_to_element(e)
            app['icon_url'] = e.get_attribute('src')
            # 앱 설명
            e = ae.find_element_by_xpath('.//span[@class="DdYX5"]')
            app['desc'] = e.text.strip()
            # 앱 개발사
            e = ae.find_element_by_xpath('.//span[@class="wMUdtb"]')
            app['creator'] = e.text.strip()
            # 앱 점수
            e = ae.find_element_by_xpath('.//span[@class="w2kbF"]')
            app['rank'] = float(e.text.strip())
            self.logger.info(f'[{i+1}] app={app}')
            app_list.append(app)
        return True

    # ==========================================================================
    def _get_app_images(self, app_images):
        for i, de in enumerate(self.driver.find_elements_by_xpath('//div[@class="ULeU3b Utde2e"]')):
            ie = de.find_element_by_xpath('.//img[@class="T75of B5GQxf"]')
            self.move_to_element(ie)
            img_src = ie.get_attribute('src')
            self.logger.info(f'[{i+1}] app_image={img_src}')
            app_images['image_url_list'].append(img_src)

    # ==========================================================================
    def _get_categories(self, categories):
        for ie in self.driver.find_elements_by_xpath('//div[@class="VfPpkd-XPtOyb-FCjw3e  kz2bF"]/div/*'):
            categories.append(ie.text.strip())
        self.logger.info(f'categories={categories}')

    # ==========================================================================
    def _get_new_function(self, new_function):
        e = self.driver.find_element_by_xpath('//div[@class="aJ3edd"]|//div[@class="xg1aie"]')
        new_function['update_date'] = e.text.strip().replace(' ', '')[:-1] + ' 00:00:00'
        e = self.driver.find_element_by_xpath('(//div[@class="SfzRHd"])[3]')
        new_function['update_contents'] = e.text.strip()
        self.logger.info(f'new_function={new_function}')

    # ==========================================================================
    def get_app_info(self):
        app_info = {
            'star_like': None,
            'num_reviews': None,
            'title': None,
            'contents': None,
            'version': None,
            'num_download': None,
        }
        try:
            # 2.9 star
            e = self.get_by_xpath('(//div[@class="ClM7O"])[1]')
            app_info['star_like'] = float(e.text.strip().split('\n')[0])

            # 리뷰 21.5만개
            e = self.get_by_xpath('(//div[@class="g1rdde"])[1]')
            app_info['num_reviews'] = self._get_num_from_str(e.text.strip())

            # # 다운로드 "1000만+"
            # e = self.get_by_xpath('(//div[@class="ClM7O"])[2]')
            # app_info['num_download'] = e.text.strip()

            # age "만 3세 이상"
            e = self.get_by_xpath('(//div[@class="g1rdde"])[3]')
            app_info['contents_age'] = e.text.strip().split('\n')[0]

            # app 캡쳐 이미지 가져오기
            app_info['image_list'] = list()
            app_info['image_url_list'] = list()
            # self._get_app_images(app_info)

            # 개발자 연락처
            # app_info['developer'] = {}
            # self._get_dev_info(app_info['developer'])

            # 개발사 앱 더보기 또는 유사한 앱 (순서가 랜덤임), 둘 중에 하나만 있을 수도 있음

            # for parent_e in self.driver.find_elements_by_xpath('//section[@class="HcyOxe"]'):
            #     self._get_other_apps(parent_e, app_info)
            # parent_e = self.driver.find_element_by_xpath('(//div[@class="o45e4d"])[2]')
            # app_info['similar_apps'] = list()
            # self._get_other_apps(parent_e, app_info['similar_apps'] )

            # 앱정보 팝업
            # app_info['popup'] = {}
            # self._get_popup_app_info(app_info['popup'])
            self._get_popup_app_info(app_info)

            # 카테고리 정보
            app_info['categories'] = list()
            self._get_categories(app_info['categories'])

            # 새로운 기능
            # app_info['new_function'] = {}
            # self._get_new_function(app_info['new_function'])
            self._get_new_function(app_info)
            self.save_image(app_info)
            self.get_reviews()

        finally:
            self.output['app_info'] = app_info

    # ==========================================================================
    def get_reviews(self):
        # with GooglePlaystoreReview(self.config, self.output["start_ts"]) as ws:
        #     ws.start()
        #     self.output['article_list'] = ws.review_list
        #     self.output["latest_create_article_ts"] = ws.latest_create_article_ts
        ws = GooglePlaystoreReview_API(self.config)
        ws.start()
        self.output['article_list'] = ws.review_list
        self.output["latest_create_article_ts"] = ws.latest_create_article_ts

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def page_screenshot(self):
        ss_f = self.get_safe_path(
            self.config['target']['folder'],
            f'{self.output["start_ts"]}.png'
        )
        if self.config['params']['kwargs']['headless']:
            self._screenshot(ss_f)
        else:
            # 상단바 제거
            e = self.get_by_xpath('//header[@role="banner"]', timeout=3, wait_until_valid_text=True)
            self.driver.execute_script("""
                                            var element = arguments[0];
                                            element.parentNode.removeChild(element);
                                            """, e)
            self.full_screenshot(ss_f)

    # ==========================================================================
    def make_tgz(self):
        src_d = self.config['target']['folder']
        tgz_f = self.config['target']['folder'] + '.tgz'
        with tarfile.open(tgz_f, "w:gz") as tar:
            tar.add(src_d, arcname=os.path.basename(src_d))

    # ==========================================================================
    def save_image(self, msg):
        for j, sub_e_url in enumerate(msg['image_url_list']):
            try:
                article_img_p = self.get_safe_path(
                    self.config['target']['folder'],
                    f'{j}.png'
                )
                # 가끔 에러 나는 경우가 있슴
                for count in range(10):
                    try:
                        urlretrieve(sub_e_url, article_img_p)
                        msg['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count+1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

    # ==========================================================================
    def save_d(self, fn, d):
        fn += '.yaml' if self.config['target']['is_yaml'] else '.json'
        with open(fn, 'w', encoding='utf-8') as ofp:
            if self.config['target']['is_yaml']:
                yaml.dump(d, ofp, allow_unicode=True)
            else:
                ofp.write(json.dumps(d, ensure_ascii=False))

    # ==========================================================================
    def save(self):
        self.output['num_articles'] = len(self.output['article_list'])
        if self.config['target']['is_separate_review']:
            # review_list = self.output['article_list']
            del self.output['article_list']
            # for review in article_list:
            #     at_js_f = self.get_safe_path(
            #         self.config['target']['folder'],
            #         review['comment_id'],
            #         f'{self.output["start_ts"]}'
            #     )
            #     self.save_d(at_js_f, review)
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

            if self.config['params']['site']['capture_main']:
                self.page_screenshot()
            self.get_app_info()
            print(0)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            raise e
        finally:
            # print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()

#
# ################################################################################
# def do_start(**kwargs):
#     with GooglePlaystoreSearch(kwargs['config_f']) as ws:
#         ws.start()
#         return 0


################################################################################
def main(**kwargs):
    try:
        with GooglePlaystoreSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(11)


################################################################################
if __name__ == '__main__':
    _config_f = 'google_playstore.yaml'
    main(config_f=_config_f)
