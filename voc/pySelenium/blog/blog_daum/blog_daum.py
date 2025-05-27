"""
====================================
 :mod:`blog/blog_daum`
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
#  * [2023/07/13]
#     - 다음 블로그 검색부분의 사이트 UI 변경
#  * [2022/12/09]
#     - 사이트명 첫 부분에 공백이 있을 경우 제거
#  * [2022/11/21]
#     - 티스토리 이전
#  * [2022/05/11]
#     - 적합도 반영 끄는 추가, 작성글 xpath 수정
#  * [2022/04/05]
#     - 다음블로그 포멧적용, excluded_blogs 에러나는 블로거의 아이디 리스트 형식으로 입력
#  * [2022/01/10]
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
import traceback
import requests
import datetime
from datetime import timedelta
from pathlib import Path
from copy import deepcopy
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
class DaumBlogSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DaumBlogearch.log'),
                            logsize=1024 * 1024 * 10)
        self.config['params']['kwargs']['logger'] = logger
        PySelenium.__init__(self, **self.config['params']['kwargs'])

        # 제외 블로거
        self.excluded_blogs = self.config['params']['site']['excluded_blogs'].split(',')

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
        del out_config['params']['site']['excluded_blogs']
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
        self.logger.info(f'Starting Daum Blog Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    @staticmethod
    def _get_safe_next_filename(fn):
        fn, ext = os.path.splitext(fn)
        for n in range(1, 1000000):
            nfn = f'{fn} ({n})' + ext
            if not os.path.exists(nfn):
                return nfn

    # ==========================================================================
    def search(self):
        # 검색어 입력
        e = self.get_by_xpath('//div[@class="inner_searchbar"]/input')
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@id="daumBtnSearch"]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 블로그 선택
        e = self.get_by_xpath('//div[@class="card_comp"]//div[@class="c-sub-sort"]/a[1]',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 최신순 클릭
        e = self.get_by_xpath('//div[@class="c-comp-sort"]/a[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 적합도 반영 끄기 (최신순 정렬에 영향을 줌)
        # e = self.get_by_xpath('//label[@class="lab_suitable checked"]')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

        # 옵션 선택
        e = self.get_by_xpath('//div[@class="layer_opt"]/button[@class="btn_more"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 기간 설정: 최근 1일
        e = self.get_by_xpath('//div[@class="opt_comp"][2]//a[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        e = self.get_by_xpath('//div[@class="layer_opt"]/button')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_comment(self, msg):
        # //div[@class="area-reply"]//ul[@class='list-reply']/li[@class]
        try:
            comment_list_xpath = '//div[@class="comments"]//div/ul/li'    \
                                 '|//div[@class="area-reply"]/div//ul/li' \
                                 '|//div[@class="area-reply"]//ul[@class="list-reply"]/li[@class]' \
                                 '|//div[@class="area_reply"]/div//ul/li' \
                                 '|//div[@class="area_reply "]/div//ul/li[@class]'    \
                                 '|//div[@class="comment_area"]//ul/li[@class]'

            comments = self.driver.find_elements_by_xpath(comment_list_xpath)
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
                # 댓글 nickname
                nickname_list = '//span[@class="nickname"]'     \
                                '|//div//strong/a'              \
                                '|//div[@class="author"]'
                e = cmt_e.find_element_by_xpath(nickname_list)
                cmt['nickname'] = e.text.strip()

                # 댓글 작성 일시
                e = cmt_e.find_element_by_xpath('//div/span[@class="date"]')
                a = e.text.strip()
                if '신고' in a:
                    e_a = a.partition('신고')[0]
                    e_b = e_a.rpartition(' ')[0] + ':00'
                else:
                    e_b = a + ':00'
                cmt['create_ts'] = datetime.datetime.strptime(e_b, '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                # 댓글 내용
                e = cmt_e.find_element_by_xpath('//p')
                cmt['contents'] = e.text.strip()

                # 댓글 아이디
                try:
                    eid = cmt_e.find_element_by_xpath('.//div/span[@class="control"]/div/a')
                    eid_a = eid.get_attribute('href')
                    e = eid_a.partition('#comment')[2]
                except:
                    eid = cmt_e.get_attribute('id')
                    e = eid.partition('comment')[2]
                cmt['comment_id'] = e
                cmt['is_reply'] = False

                cmt['comment_img_url'] = []
                cmt['comment_img'] = []

                msg['comment_list'].append(cmt)
                self.logger.info(f'{cmt["comment_id"]}')

                # 대댓글인지 확인
                try:
                    e = cmt_e.find_elements_by_xpath('./ul/li')
                    for j, rc_e in enumerate(e):
                        self.move_to_element(rc_e)
                        reply = {
                            'comment_id': None,
                            'is_reply': True,
                            'parent_comment_id': None,
                            'create_ts': None,
                            'nickname': None,
                            'contents': None,
                            'like': None,
                            'dislike': None,
                            'comment_img': [],
                            'comment_img_url': [],
                        }
                        # 대댓글의 닉네임
                        a = rc_e.find_element_by_xpath('.//span[1]')
                        reply['nickname'] = a.text.strip()

                        reply['parent_comment_id'] = cmt['comment_id']
                        # 작성일
                        e = rc_e.find_element_by_xpath('.//span[2]')
                        a = e.text.strip()
                        if '신고' in a:
                            e_a = a.partition('신고')[0]
                            e_b = e_a.rpartition(' ')[0] + ':00'
                            cmt['create_ts'] = datetime.datetime.strptime(e_b, '%Y.%m.%d %H:%M:%S').strftime(
                                '%Y.%m.%d %H:%M:%S')
                        else:
                            e_a = a + ':00'
                            cmt['create_ts'] = datetime.datetime.strptime(e_a, '%Y.%m.%d %H:%M:%S').strftime(
                                '%Y.%m.%d %H:%M:%S')
                        # ID
                        e_b = e.find_element_by_xpath('./a')
                        b = e_b.get_attribute('href')
                        reply['comment_id'] = b.partition('commentId=')[2]
                        # 내용
                        b = rc_e.find_element_by_xpath('.//p')
                        reply['contents'] = b.text.strip()
                        msg['comment_list'].append(reply)
                except:

                    continue
        except Exception as err:
            raise
        finally:
            self.switch_to_window(1)

        # ========================================================================

    def get_article(self, msg, ndx):
        try:
            self.switch_to_window(1)
            content_e = self.get_by_xpath('//html/head')
            # 제목 : title
            e = content_e.find_element_by_xpath('./meta[@property="og:title"]')
            eg = e.get_attribute('content')
            msg['title'] = eg
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                self.full_screenshot(msg_capture_f)

            # 블로그 이름 : blog_name
            e = content_e.find_element_by_xpath('//meta[@property="og:site_name"]')
            eg = e.get_attribute('content')
            if eg.startswith(' '):
                msg['site_name'] = eg.replace(' ', '', 1)
            else:
                msg['site_name'] = eg
            # 작성자 : author
            e = content_e.find_element_by_xpath('//meta[@name="by"]')
            eg = e.get_attribute('content')
            msg['author'] = eg
            # 댓글 수
            try:
                num_comments_xpath = '//div[@class="article-reply"]//span/span'         \
                                      '|//div[@class="area_reply"]//span'               \
                                      '|//div[@class="comments"]/h2/span/span'          \
                                      '|//div[@class="area_reply"]//span/span'          \
                                      '|//div[@class="comment_info"]//em/span'          \
                                      '|//div[@class="article-reply"]//span/span'       \
                                      '|//div[@class="area_reply "]//strong//span[1]'   \
                                      '|//div[@class="post-reply"]//span/span'
                e = self.get_by_xpath(num_comments_xpath)
                msg['num_comments'] = int(e.text.strip())
            except:
                msg['num_comments'] = 0
            # 게시글 공감수 : like
            # 없는 경우 0으로 표시
            e_a = self.get_by_xpath('//div[@class="wrap_btn"]//span[2]')
            a = e_a.text.strip()
            if '공감' in a:
                msg['like'] = 0
            else:
                msg['like'] = a
            # 게시글 본문
            contents_xpath = '//div[@class="entry-content"]'     \
                             '|//div[@id="content"]//div[@class="e-content post-content"]'           \
                             '|//div[@class="area_view"]'           \
                              '|//div[@id="content"]//div[@class="article"]'     \
                             '|//div[@class="article-view"]'        \
                             '|//div[@class="article_view"]'        \
                             '|//div[@class="content-article"]'     \
                             '|//div[@class="box_article"]'

            e = self.get_by_xpath(contents_xpath)
            e_a = e.text.strip()
            if '좋아요공감\n공유하기' in e_a:
                msg['contents'] = e_a.partition('좋아요공감\n공유하기')[0]
            elif '좋아요' + a + '\n공유하기' in e_a:
                msg['contents'] = e_a.partition('좋아요' + a + '\n공유하기')[0]
            else:
                msg['contents'] = e_a

            # if re.sub(r'[^0-9]', '', e_a.text.strip()) == '':
            #     like_e = 0
            # else:
            #     like_e = int(re.sub(r'[^0-9]', '', e_a.text.strip()))
            # 게시글 내용: 블로그 구조에 따라 xpath 형식이 다름.
            # comments_xpath = '//div[@class="article-view"]' \
            #                  '|//div[@id="cContentBody"]'
            # e = self.get_by_xpath(comments_xpath, timeout=1)

            # 이미지 주소 갖고 오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            try:
                e_a = e.find_elements_by_xpath('.//span/img')
                for j, sub_k in enumerate(e_a):
                    self.move_to_element(sub_k)
                    sub_k_url = sub_k.get_attribute('src')
                    msg['image_url_list'].append(sub_k_url)
                    art_img_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{j}.png')
                    sub_k.screenshot(art_img_f)
                    msg['image_list'].append(f'{j}.png')

            except:
                return
            # 첨부파일
            # inner_html = e.get_attribute('innerHTML')
            msg['attachment_url'] = []
            msg['attachment_name'] = []
            # try:
            #     e_a = e.find_elements_by_xpath('.//span/img')
            #     for k, sub_k in enumerate(e_a):
            #         self.move_to_element(sub_k)
            #         sub_k_url = sub_k.get_attribute('src')
            #         if sub_k_url.find('https://') < 0:
            #             continue
            #
            #         sub_k_url = sub_k.get_attribute('href')
            # if sub_k_url.find('https://') < 0:
            #     continue
            # if inner_html.find('fileblock') > 0 or inner_html.find(
            #         'another_category another_category_color_gray another_category_custom') > 0:
            #     attachment_xpath = './/figure[@class="fileblock"]/a' \
            #                        '|.//td/a[@href]' \
            #                        '|.//p/a[@title]/img[@alt="첨부파일"]/..' \
            #                        '|.//div[@class="another_category another_category_color_gray another_category_custom"]//th/a'
            #     for k, sub_k in enumerate(e.find_elements_by_xpath(attachment_xpath)):
            #         self.move_to_element(sub_k)
            #         sub_k_url = sub_k.get_attribute('href')
            #         if sub_k_url.find('https://') < 0:
            #             continue
            #         msg['attachment_url'].append(sub_k_url)
            #         sub_k_name = sub_k.text.strip().partition('\n')[0]
            #         if sub_k_name.find('.') < 0:
            #             sub_k_name += sub_k_url[sub_k_url.rfind('.'):]
            #         msg['attachment_name'].append(sub_k_name)

            # 댓글 처리
            if msg['num_comments'] == 0:
                return
            msg['comment_list'] = []
            self.get_comment(msg)

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            self.driver.close()
            self.implicitly_wait(after_wait=1)
            try:
                self.switch_to_main_window()
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
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//c-container[@class="hydrated"]')
            es = e.find_elements_by_xpath('./c-card')

            # 한번 게시a9556글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함0
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
                    e = self.get_by_xpath('//c-container[@class="hydrated"]')
                    es = e.find_elements_by_xpath('./c-card')
                    ea = es[i]
                    self.move_to_element(ea)
                    # 1) 게시글id : article_id  300143_55268553
                    v = ea.get_attribute('data-docid')
                    id = v.split('tstory-')[1]
                    msg['article_id'] = id
                    if 'tstory' not in v:
                        self.logger.info(
                            f'Page[{self.cur_page}:{i+1}],article_id[{msg["article_id"]}] is not daum blog *******')
                        continue
                    e_url = ea.find_element_by_xpath('.//c-title[@slot="title"]')
                    a_url = e_url.get_attribute('data-href')

                    # 제외 블로거
                    if id.rpartition('_')[0] in self.excluded_blogs:
                        self.logger.info(
                            f'Page[{self.cur_page}:{i+1}],article_id[{msg["article_id"]}] is excluded_blogs *******')
                        continue

                    # 1) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 2) 작성시간: article_ts
                    e = ea.find_element_by_xpath('.//c-frag[@slot="info"]')
                    et = e.text
                    hhh, mmm = 0, 0
                    msg['create_ts'] = ""
                    if et.find('분') > 0:
                        mm = re.sub(r'[^0-9]', '', et)
                        mmm = int(mm)
                    elif et.find('시간') > 0:
                        hh = re.sub(r'[^0-9]', '', et)
                        hhh = int(hh)
                    else:
                        msg['create_ts'] = et + ' 00:00:00'
                    if msg['create_ts'] == "":
                        d = datetime.datetime.now() - timedelta(hours=hhh, minutes=mmm)
                        msg['create_ts'] = d.strftime('%Y.%m.%d %H:%M:%S')
                    msg['create_ts'] = datetime.datetime.strptime(msg['create_ts'], '%Y.%m.%d %H:%M:%S').strftime('%Y.%m.%d %H:%M:%S')
                    e = ea.find_element_by_xpath('.//strong[@class="tit-g clamp-g"]/a')
                    self.safe_click(e)
                    self.implicitly_wait(after_wait=1)
                    self.get_article(msg, i + 1)
                except Exception as err:
                    if 'article_id' not in msg:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i + 1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(msg):
                    if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    self.is_done = True  # 동시성 런타임
                    break
                self.save_attachment(msg)
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
            self.switch_to_window(0)
            # 다음 페이지만 눌러도 이동
            e = self.get_by_xpath('//div[@id="blogColl"]')
            ple = e.find_element_by_xpath('.//div[@id="pagingArea"]')
            self.move_to_element(ple)
            e_b = e.find_element_by_xpath('.//a[@class="ico_comm1 btn_page btn_next"]')
            self.safe_click(e_b)

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
    def save_attachment(self, article):
        for i, attach_url in enumerate(article['attachment_url']):
            article_attach_p = self.get_safe_path(
                self.config['target']['folder'],
                article['article_id'],
                article['attachment_name'][i]
            )
            # 중복된 이름일경우 다르게 저장
            if os.path.exists(article_attach_p):
                article_attach_p = self._get_safe_next_filename(article_attach_p)
                article['attachment_name'][i] = os.path.basename(article_attach_p)
            file = requests.get(attach_url, stream=True)
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
    with DaumBlogSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'blog_daum.yaml'
    do_start(config_f=_config_f)
