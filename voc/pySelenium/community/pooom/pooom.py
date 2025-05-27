"""
====================================
 :mod:`community/pooom`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for poooom
"""
# Authors
# ===========
#
# * Sebin Eun
#
# Change Log
# --------
#
#  * [2023/05/16]
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
import traceback
import urllib.request
import datetime
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
class pooomSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'PooomSearch.log'),
                            logsize=1024*1024*10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 이미지 다운(403 에러 해결코드)
        opener = urllib.request.build_opener()
        opener.addheaders = [('User-Agent',
                              'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
        urllib.request.install_opener(opener)

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
        self.cmt_done = False
        self.article_num = 0
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
        self.logger.info(f'Starting Nate Pann Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def login(self):
        try:
            # 로그인 클릭
            e = self.get_by_xpath('//*[@id="GnbWrap"]/div[2]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # login 화면
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="uid"]')
            self.send_keys_clipboard(e, self.config['params']['site']['userid'])

            # 암호 입력
            e = self.get_by_xpath('//*[@id="upw"]')
            self.send_keys_clipboard(e, self.config['params']['site']['passwd'])

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="f_login"]/fieldset/input',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def search(self):
        # 팝업창 끄기
        try:
            a = self.get_by_xpath('//div[@class="free-sticker-wrap"]')
            # if a:
            # 일주일 보지 않기
            # a_e = self.get_by_xpath('//div[@id="__next"]//div[@class="Popup_root__Mc_me"]//div[@class="slick-slider slick-initialized"]',
            #     cond='element_to_be_clickable')
            # 창 닫기
            a_e = a.find_element_by_xpath('.//button')
            self.safe_click(a_e)
        except:
            pass
        # 검색어 입력
        e = self.get_by_xpath('//*[@name="keyword"]')
        self.send_keys(e, self.config['params']['site']['search'])
        # 검색 단추
        e = self.get_by_xpath('//button[@class="btn btn-red btn-search"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
        # 날짜순 정렬
        e = self.get_by_xpath('(//div[@class="range-wrapper"]/div[1]/span)[1]', cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def next_cmt(self):

        # 역할
        # 1. 대댓글 페이지를 넘기는 기능과
        # 2. 더 이상 페이지가 없는 경우 대댓글이 없음을 알려주는 기능 수행 self.reply_done = true
        # 참고 : 최문창님의 코드 인용하여 적용

        # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
        # 따라서 두 가지 종류의 태그를 모두 구해야 함
        # 현재의 게시글이 포함된 페이지는 class가 current이다.
        try:
           cmtPagePart = self.get_by_xpath('//div[@class="paginate-reple"]')
           is_current = False # 다음 페이지로 넘기기 위해 사용하는 플래그
           for cmtPage in cmtPagePart.find_elements_by_xpath('.//strong | .//a'):
               if cmtPage.get_attribute('class') == 'current':
                   is_current = True
                   continue
               if is_current:
                   self.safe_click(cmtPage)
                   self.implicitly_wait()
                   return
           self.cmt_done = True
        except Exception as err:
           raise
        finally:
           return

    # ==========================================================================
    def get_cmt(self, msg):
        try:
            # 문의
            if self.num_ques != 0:
                comments = self.driver.find_elements_by_xpath('//div[@class="comment"]/ul/li')
                for i, cmt_e in enumerate(comments):
                    comments_es = self.get_by_xpath('//div[@class="comment"]/ul')
                    comments_e = comments_es.find_elements_by_xpath('./li')
                    cmt_e = comments_e[i]
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

                    # 댓글 연도 구하기
                    e = cmt_e.find_element_by_xpath('./span[@class="date"]')
                    date = e.text.strip()
                    cmt['create_ts'] = date.replace('-', '.') + ':00'
                    # 댓글 id
                    e = cmt_e.find_element_by_xpath('./strong')
                    self.move_to_element(e)
                    cmt['comment_id'] = e.get_attribute('data-btn-open-user-deal-reviews-modal')
                    # 댓글 작성자 닉네임
                    e = cmt_e.find_element_by_xpath('./strong')
                    cmt['nickname'] = e.text.strip()
                    # 댓글 내용 text
                    e = cmt_e.find_element_by_xpath('./p')
                    cmt['contents'] = e.text.strip()
                    # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                    # inner_html = e.get_attribute('innerHTML')
                    # if inner_html.find('video') > 0:
                    #     re_img = e.find_element_by_tag_name('video')
                    #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    #     self.save_e_img(re_img, msg, cmt)
                    #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                    # elif inner_html.find('img') > 0:
                    #     re_img = e.find_element_by_tag_name('img')
                    #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    #     self.save_e_img(re_img, msg, cmt)
                    #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
            else:
                pass
            if self.num_app != 0:
                # 지원
                comments = self.driver.find_elements_by_xpath('//div[@class="employee"]/ul/li')
                for i, cmt_e in enumerate(comments):
                    comments_es = self.get_by_xpath('//div[@class="employee"]')
                    comments_e = comments_es.find_elements_by_xpath('./ul/li')
                    cmt_e = comments_e[i]
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

                    # 댓글 연도 구하기
                    e = cmt_e.find_element_by_xpath('./span[@class="date"]')
                    date = e.text.strip()
                    cmt['create_ts'] = date.split('지원일 ')[1].replace('-', '.') + ':00'
                    # 댓글 id
                    e = cmt_e.find_element_by_xpath('./strong')
                    self.move_to_element(e)
                    cmt['comment_id'] = e.get_attribute('data-btn-open-user-deal-reviews-modal')
                    # 댓글 작성자 닉네임
                    e = cmt_e.find_element_by_xpath('./strong')
                    cmt['nickname'] = e.text.strip()
                    # 댓글 내용 text
                    e = cmt_e.find_element_by_xpath('./p[@class="description"]')
                    cmt['contents'] = e.text.strip()
                    # 댓글 내용에 img나 gif 확인(댓글에는 디시콘만 사용가능)
                    # inner_html = e.get_attribute('innerHTML')
                    # if inner_html.find('video') > 0:
                    #     re_img = e.find_element_by_tag_name('video')
                    #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    #     self.save_e_img(re_img, msg, cmt)
                    #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                    # elif inner_html.find('img') > 0:
                    #     re_img = e.find_element_by_tag_name('img')
                    #     cmt['comment_img_url'].append(re_img.get_attribute('src'))
                    #     self.save_e_img(re_img, msg, cmt)
                    #     cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')
                    # 댓글 목록에 추가
                    msg['comment_list'].append(cmt)
            else:
                pass
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
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            for popup in self.driver.find_elements_by_xpath('//div[@class="modal fade in"]//div[@class="modal-footer"]'):
                self.logger.info('접수된 신고가 존재하는 게시글')
                e = popup.find_element_by_xpath('./button')
                self.safe_click(e)
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//header[@class="sub_header"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                                                    var element = arguments[0];
                                                                                    element.parentNode.removeChild(element);
                                                                                    """, e_head)
                    self.implicitly_wait(after_wait=1)
                    self.full_screenshot(msg_capture_f)
            e_ab = self.get_by_xpath('//div[@class="content_wrap"]')
            # 1) 작성자
            e = e_ab.find_element_by_xpath('.//div[@class="employer_info"]/div[@class="photo"]/strong')
            msg['author'] = e.text.strip()
            # 3) 작성일
            e = e_ab.find_element_by_xpath('.//div[@class="employer_info"]/div[@class="info"]//span[@class="time"]')
            date = e.text.strip()
            msg['create_ts'] = date.split('등록일 ')[1].replace('-', '.') + ':00'
            # 8) 본문
            e = e_ab.find_element_by_xpath('.//div[@class="employer_text"]/div')
            msg['contents'] = e.text.strip()

            # 이미지
            e = self.get_by_xpath('//div[@class="content_wrap"]')
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('사진') > 0:
                img_e = e.find_elements_by_tag_name('img')
                for j, img in enumerate(img_e):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{j}.png')
                    img.screenshot(cmt_img_f)
                    msg['image_list'].append(f'{j}.png')

            # 첨부파일
            msg['attachment_url'] = []
            msg['attachment_name'] = []

            # 댓글 없는 경우
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            self.get_cmt(msg)

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
            # '2021.12.21 21:48'
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
            self.switch_to_window(0)
            # 검색결과 존재 여부 확인
            for i in self.driver.find_elements_by_xpath('//div[@class="modal fade in"]//div[@class="modal-body"]'):
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return
            count_a = 0
            while True:
                # 페이지 테이블 구하기
                e_s = self.driver.find_elements_by_xpath('//ul[@id="search-result-list"]/li')
                e_a = e_s[count_a]
                msg = {
                    'page': self.cur_page,
                    'row': count_a + 1,
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
                    # 0) 게시글 카테고리: board_name
                    a = e_a.find_element_by_xpath('./div/strong/em')
                    board_name = a.text.strip()
                    msg['board_name'] = board_name
                    # 1) 게시글 주소: article_url
                    e_url = e_a.find_element_by_xpath('./div/strong/a')
                    a_url = e_url.get_attribute('href')
                    msg['article_url'] = a_url
                    # 2) 게시글 id : article_id  300143_55268553
                    v = a_url.rpartition('&id=')[2]
                    # v_a = re.sub(r'[^0-9]', '', v)
                    msg['article_id'] = v
                    # 3) 게시글 문의
                    self.num_ques = 0
                    for ques in e_a.find_elements_by_xpath('./div/span[@class="questions-inline"]'):
                        ques = ques.text.strip()
                        if len(ques) == 1:
                            self.num_ques = int(ques.split('문의 ')[1][0])
                        else:
                            self.num_ques = int(ques.split('문의 ')[1])
                    # 3) 게시글 지원
                    self.num_app = 0
                    for app in e_a.find_elements_by_xpath('./div/span[@class="offers-inline"]'):
                        app = app.text.strip()
                        if len(app) == 1:
                            self.num_app = int(app.split('지원 ')[1][0])
                        else:
                            self.num_app = int(app.split('지원 ')[1])
                    msg['num_comments'] = self.num_ques + self.num_app
                    # 3) 게시글 제목 : title
                    e = e_a.find_element_by_xpath('./div/strong/a')
                    msg['title'] = e.text.strip()
                    self.driver.execute_script(f"window.open('{a_url}');")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, count_a + 1)
                except Exception as err:
                    if 'article_id' not in msg:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'게시글의 url: {msg["article_url"]}')
                    self.logger.error(f'게시글의 title: {msg["title"]}')
                    self.logger.error(f'get_page[{self.cur_page}:{count_a + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
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
                # bi = self.get_by_xpath('//div[@id="app"]//div/strong[@class="tit_guide"]')
                # # 비공개 게시글
                # if bi:
                #     self.logger.debug('멤버에게만 공개된 게시글 입니다.')
                #     continue
                self.move_to_element(e_a)
                count_a += 1

        except Exception as err:
            raise
        finally:
            self.switch_to_main_window()

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="paginate"]')

            # 다음 페이지로 넘기기 위해 사용하는 플래그
            is_current = False

            # 네이버와 달리 현재 페이지에는 태그가 a 가 아닌 strong 이 사용됨
            # 따라서 두 가지 종류의 태그를 모두 구해야 함
            # 현재의 게시글이 포함된 페이지는 class가 current이다.
            # 따라서 다음 페이지를 클릭하기 위해 is_current 플래그를 True로 전환하고
            # for 문을 통해 다음 페이지 정보를 추출후
            # 두번 째 if 문에서 클릭을 통해 다음 페이지로 넘어간다.
            for pa in ple.find_elements_by_xpath('.//a | .//strong'):
                if pa.get_attribute('class') == 'current':
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
        for cmt in article['comment_list']:
            if not ('comment_img' in cmt and cmt['comment_img']):
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
        myLen = len(self.output['article_list'])  # 디버깅
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
            # if self.config['params']['site']['get_cafe_info']:
            #     self.get_cafe_info()
            self.search()
            # 페이지 읽어오기
            self.is_done = False
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.next_page()

            # 팬톡 게시글 리스트를 수집
            # if(ftalk_count != '0'):
            #     e = self.get_by_xpath('//*[@id="container"]/div[2]/div[1]/div[1]/ul/li[3]/a/span',
            #                           cond='element_to_be_clickable')
            #     self.safe_click(e)
            #     self.implicitly_wait(after_wait=1)
            #
            #     while not self.is_done:
            #         self.get_page()
            #         if self.is_done:
            #             break
            #         self.next_page()
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
    with pooomSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'pooom.yaml'
    do_start(config_f=_config_f)
