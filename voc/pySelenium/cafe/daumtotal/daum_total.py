"""
====================================
 :mod:`cafe/cafe_daum`
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
#  * [2024/06/04]
#     - 첫번째 댓글에 포함된 "첫댓글"제거 로직 추가
#  * [2024/05/17]
#     - 이미지 확인 로직 수정(innerHTML -> img 태그 확인)
#  * [2023/07/10]
#     - 작성자가 익명인 경우 존재하여 모듈 수정
#  * [2022/02/09]
#     - 다음 카페 투표 수집 로직 추가
#  * [2022/06/20]Kyobong An
#     - 기존 article_id 앞에 카페id를 붙임 (분석팀 요청)
#  * [2022/02/13]
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
import urllib.request
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################

# 이미지 다운(403 에러 해결코드)
opener = urllib.request.build_opener()
opener.addheaders = [('User-Agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1941.0 Safari/537.36')]
urllib.request.install_opener(opener)


################################################################################
class DaumCafeSearchAll(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DaumCafeSearchAll.log'),
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
        self.logger.info(f'Starting Daum Cafe Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        try:
            # 해당 iFrame으로 이동
            # self.switch_to_iframe_by_name('down')

            # # 검색 아이콘 누름
            # e = self.get_by_xpath('//button[@class="btn_search_top btn_search_open"]')
            # self.safe_click(e)

            # 검색어 입력
            e = self.get_by_xpath('//input[@class="tf_keyword inp_search"]')
            if self.config['params']['site']['search_complex']:
                self.send_keys(e, self.config['params']['site']['search_complex'] + Keys.ENTER)
            else:
                self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
            self.implicitly_wait(after_wait=1)

            # 카페글 최신 누름 : 'link_option date '
            e = self.get_by_xpath('//a[@class="link_option date "]')
            self.safe_click(e)


            # # 검색어 필터
            # e = self.get_by_xpath('//select[@name="item"]')
            # e_s = e.find_elements_by_xpath('./option')
            # for i, e_filter in enumerate(e_s):
            #     if e_filter.text.find(self.config['params']['site']['search_filter']) >= 0:
            #         self.safe_click(e_filter)
            #         self.implicitly_wait(after_wait=1)
            #         e = self.get_by_xpath('//img[@alt="검색"]')
            #         self.safe_click(e)
            #         self.implicitly_wait(after_wait=1)
            #         break
        finally:
            # self.switch_from_iframe()
            pass

    # ==========================================================================
    def get_comments(self, msg):
        try:
            # self.switch_to_iframe_by_name('down')
            try:
                e = self.get_by_xpath('//ul[@class="list_comment"]')
            except:
                return
            comments = e.find_elements_by_xpath('./li[@class]')
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
                is_reply = cmt_e.get_attribute('data-parseq') != '0'
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id
                is_deleted = False
                # 댓글작성자 닉네임: 삭제된 댓글인 경우 해당 엘리먼트 발견 안됨
                inner_html = cmt_e.get_attribute('innerHTML')
                if inner_html.find('opt_more_g') > 0:
                    e = cmt_e.find_element_by_xpath('.//div[@class="opt_more_g"]')
                    cmt['nickname'] = e.text.strip()
                else:
                    is_deleted = True
                if not is_deleted:
                    # 댓글 내용
                    e = cmt_e.find_element_by_xpath('.//div[@class="box_post"]')
                    self.move_to_element(e)
                    if i == 0:
                        cmt_contents = e.text.strip().replace('첫댓글 ', '')
                    else:
                        cmt_contents = e.text.strip()
                    cmt['contents'] = cmt_contents
                    # 댓글에 이모티콘 혹은 이미지
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    try:
                        img_elements = e.find_element_by_tag_name('img')
                    except:
                        img_elements = False
                    if img_elements:
                        # 댓글 이미지의 경우 축소되어있는경우 클릭해줘야함.
                        # if inner_html.find("img_thumb zoom_in") > 0:
                        #     e.find_element_by_xpath('//img[@class="img_thumb zoom_in"]').click()
                        #     self.implicitly_wait(after_wait=1)
                        img_e = e.find_element_by_tag_name('img')
                        cmt['comment_img_url'].append(img_e.get_attribute('src'))
                        # 이모티콘은 이미지를 가져올수 없음. 바로 캡쳐
                        cmt_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                       f'{cmt["comment_id"] + "_0"}.png')
                        try:
                            urlretrieve(cmt['comment_img_url'], cmt_img_f)
                        except:
                            img_e.screenshot(cmt_img_f)
                        cmt['comment_img'].append(f'{cmt["comment_id"] + "_0"}.png')

                    # 댓글 작성 시각
                    e = cmt_e.find_element_by_xpath('.//span[@class="txt_date"]')
                    create_ts = e.text.strip()
                    if len(create_ts.split()) == 1:
                        doday_ts = datetime.datetime.today().strftime("%Y.%m.%d")
                        create_ts = f'{doday_ts[2:]} ' + create_ts
                    cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                else:
                    cmt['comment_id'] = None
                    cmt['contents'] = cmt_e.text.strip()
                    cmt['comment_img_url'] = []
                    cmt['comment_img'] = []
                    cmt['nickname'] = ""
                    # 댓글 작성 시각 작성자와 운영자만 보는 경우에도 가져올수 있음
                    inner_html = cmt_e.get_attribute('innerHTML')
                    if inner_html.find('txt_date') > 0:
                        e = cmt_e.find_element_by_xpath('.//span[@class="txt_date"]')
                        create_ts = e.text.strip()
                        if len(create_ts.split()) == 1:
                            doday_ts = datetime.datetime.today().strftime("%Y.%m.%d")
                            create_ts = f'{doday_ts[2:]} ' + create_ts
                        cmt['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    else:
                        cmt['create_ts'] = ""
                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
                if len(msg['comment_list']) >= msg['num_comments']:
                    break
        finally:
            self.switch_to_iframe_by_name('down')

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):
        self.safe_click(title_e)
        self.implicitly_wait(after_wait=1)
        click_count = 1
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            # 새로운 탭으로 이동
            self.switch_to_window(1)
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_iframe_by_name('down')
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                # e_body.screenshot(msg_capture_f)
                self.full_screenshot(msg_capture_f)
            try:
                e = self.get_by_xpath('//a[@class="link_item"]')
                msg['author'] = e.get_attribute('data-nickname')
            except:
                content_e = self.get_by_xpath('//div[@class="primary_content"]')
                e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_name"]')
                msg['author'] = e.text.strip()
            content_e = self.get_by_xpath('//div[@class="primary_content"]')
            # 게시판 이름
            e = content_e.find_element_by_xpath('.//a[@class="txt_subhead"]')
            msg['board_name'] = e.text.strip()
            # 추천 : "추천 0"
            e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][1]')
            msg['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 조회수 : "조회 93"
            e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][2]')
            msg['view_count'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 작성일시
            e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][3]')
            create_ts = e.text.strip()
            msg['create_ts'] = datetime.datetime.strptime(create_ts, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
            # 댓글수
            e = content_e.find_element_by_xpath('.//div[@class="cover_info"]/span[@class="txt_item"][4]/a')
            msg['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 본문
            e = content_e.find_element_by_xpath('.//div[@id="user_contents"]')
            msg['contents'] = e.text.strip()
            # 투표
            msg['vote'] = []
            for vote in e.find_elements_by_xpath('.//div[@class="figure-poll"]'):
                self.move_to_element(vote)
                e = vote.find_element_by_xpath('.//iframe[@id="pollFrame"]')
                self.driver.switch_to_frame(e)
                # self.driver.switch_to.default_content()
                # self.move_to_element(e)
                title = self.get_by_xpath('html//div[@class="title_vote"]/strong[@class="tit_subject"]')
                title_t = title.text.strip()
                result_list = []
                for result in self.driver.find_elements_by_xpath('//div[@class="box_vote"]/ul/li'):
                    result_e = result.find_element_by_xpath('.//span[@class="txt_subject"]')
                    result_list.append(result_e.text.strip())
                vote_e = str(title_t) + str(result_list)
                msg['vote'].append(vote_e)
                self.switch_to_iframe_by_name('down')
            self.switch_to_iframe_by_name('down')
            e = content_e.find_element_by_xpath('.//div[@id="user_contents"]')
            # 아래의 이미지나 링크는 없는 경우도 많은데 이런 경우 find_elements_by_xpath 하기 전에
            # 미리 HTML에서 해당 class를 찾는게 시간이 훨씬 적게 걸림
            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('txc-image') > 0:
                # for sub_e in e.find_elements_by_xpath('.//img[@class="txc-image"]'):
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)

            # 댓글 : 댓글이 없는 경우 있음
            if msg['num_comments'] <= 0:
                return
            msg['comment_list'] = []

            # 코멘트 페이징이 있는 경우
            e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
            coments_es = e.find_elements_by_xpath('./ul/li')
            if coments_es[1].get_attribute('class') == 'active':
                self.get_comments(msg)
                return
            # 1을 클릭하기위함.
            self.safe_click(coments_es[1])
            self.implicitly_wait(after_wait=1)
            click_count += 1
            while True:
                e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
                coments_es = e.find_elements_by_xpath('./ul/li')
                is_next = False
                for coments_e in coments_es:
                    if coments_e.text.find('다음') >= 0:
                        is_next = False
                        break
                    elif coments_e.get_attribute('class') == 'active':
                        self.get_comments(msg)
                        is_next = True
                        continue
                    if is_next:
                        self.safe_click(coments_e)
                        self.implicitly_wait(after_wait=1)
                        click_count += 1
                        break
                if not is_next:
                    break
            # 속도 개선전 코드
            # for page_cnt in range(1, 11):
            #     self.switch_to_iframe_by_name('down')
            #     e = self.get_by_xpath('//div[@id="comment-paging"]', timeout=1)
            #     b_page_found = False
            #     for k, cp_e in enumerate(e.find_elements_by_xpath('.//a[@class="page-link"]')):
            #         if cp_e.text.strip() == str(page_cnt):
            #             b_page_found = True
            #             self.safe_click(cp_e)
            #             self.implicitly_wait()
            #             self.get_comments(msg)
            #             break
            #     if not b_page_found:
            #         if page_cnt == 1:
            #             i = self.get_comments(msg)
            #         break
            # # 다음은 디버깅 용도!
            # if len(msg['comment_list']) != msg['num_comments']:
            #     j = i
        except Exception as err:
            raise
        finally:
            # 뒤로 돌아감 댓글
            # for _ in range(click_count):
            #     self.driver.back()
            self.driver.close()
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
        except:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            # # "카페 메인 (cafe_main)" iFrame으로 이동
            # self.switch_to_iframe_by_name('down')
            # 페이지 테이블 구해오기
            bil = self.driver.find_elements_by_xpath('//ul[@class="list_scafe"]/li')
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            # for i, bi in enumerate(bil):
            for i in range(len(bil)):
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
                    'vote': [],
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
                    # # "카페 메인 (cafe_main)" iFrame으로 이동
                    # self.switch_to_iframe_by_name('down')
                    bi = self.driver.find_element_by_xpath(f'(//ul[@class="list_scafe"]/li)[{i+1}]')

                    # 1) 게시글 link
                    title_e = bi.find_element_by_xpath('.//a[@class="link_tit"]')
                    # 2) 제목: title
                    msg['title'] = title_e.text.strip()
                    # 3) 게시글 URL:  article_url
                    msg['article_url'] = href = title_e.get_attribute('href')
                    # 4) ID
                    href = href[:href.find('?q=')].split('/')
                    msg['article_id'] = href[-3]+'_'+href[-1]
                    # 5) 카페이름
                    se = bi.find_element_by_xpath('.//a[@class="link_cafe"]')
                    msg['site_name'] = se.text.strip()

                    # # 4) 작성자: author 링크를 못 찾으면 "(익명)"
                    # try:
                    #     se = bi.find_element_by_xpath('.//td[@class="search_nick"]')
                    #     msg['author'] = se.text.strip()
                    # except:
                    #     msg['author'] = ''
                    self.get_article(title_e, msg, i+1)
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
            # self.switch_from_iframe()
            pass

    # ==========================================================================
    def next_page(self):
        try:
            # # "카페 메인 (cafe_main)" iFrame으로 이동
            # self.switch_to_iframe_by_name('down')
            # 페이지 목록
            next_page_str = str(self.cur_page + 1)
            ple = self.get_by_xpath('//span[@class="paging_inner"]', timeout=2)
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.text.strip() == next_page_str:
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
        except Exception as err:
            self.logger.error(f'Cannot find Result!')
            self.is_done = True
        finally:
            # self.switch_from_iframe()
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
                        self.logger.info(f'save_img: {j}.png : retry{count+1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

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
    with DaumCafeSearchAll(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'daum_total.yaml'
    do_start(config_f=_config_f)
