"""
====================================
 :mod:`thinkfood`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for thinkfood (식품음료신문)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/04/20]
#     - 팝업창 처리 로직 추가
#  * [2023/04/10]
#     - 수집 범위 헤드라인인 경우, 수집 범위에 해당하는 모든 게시글 수집
#     - 수집 영역(board_name) 수집
#  * [2022/02/16]
#     - 1차 버전 완료

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
# import subprocess # 박제영 추가
# from Screenshot import Screenshot_Clipping
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################
class ThinkfoodSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'ThinkfoodSearch.log'),
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
        self.cmt_done = False
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
        self.logger.info(f'Starting Thinkfood Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_cmt(self, msg, cmt_page_unit):

        # 최대 5개의 댓글로만 구성된 페이지 형태
        e = self.get_by_xpath('//article[@class="article-reply"]')
        cmt_list = e.find_elements_by_xpath('.//section[@class="container"]/article')

        # 답글(대댓글) '항목' 펼치기 : 5개의 댓글에 달린 답글을 모두 펼치기
        for i, cmt_e in enumerate(cmt_list):
            try:
                cmt_footer = cmt_e.find_element_by_tag_name('footer')
            except:
                pass
            else:
                self.move_to_element(cmt_e)
                if cmt_footer.text.find('답글쓰기') >=0: # 답글이 없는 경우
                    continue
                else:  # 답글이 있는 경우
                    # 답글(대댓글) 펼치기 작업 필요
                    button = cmt_footer.find_element_by_tag_name('button')
                    self.safe_click(button)
                    self.implicitly_wait(after_wait=1)

        # 댓글과 답글(대댓글)이 같은 계위로 펼쳐져 있음
        # 댓글 하나에 상응하는 답글(대댓글) 그룹이 짝을 맺고 있음
        # 댓글 tag = article <-> 답글(대댓글) tag = div
        e = self.get_by_xpath('//article[@class="article-reply"]//section[@class="container"]')
        cmt_list = e.find_elements_by_xpath('./article')
        reply_list = e.find_elements_by_xpath('./div')
        for i, cmt_e in enumerate(cmt_list): # 확보된 댓글 리스트를 하나씩 처리하기

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
            try:
                cmt_header = cmt_e.find_element_by_tag_name('header')
                cmt_section = cmt_e.find_element_by_tag_name('section')
                cmt_footer = cmt_e.find_element_by_tag_name('footer')
            except:
                pass
            else:
                self.move_to_element(cmt_e)
                # 댓글 작성자와 작성 일시, cmt id, 댓글 내용
                cmt_user = cmt_header.find_element_by_tag_name('strong')
                cmt_date = cmt_header.find_element_by_tag_name('small')
                cmt['nickname'] = cmt_user.text.strip()
                cmt['create_ts'] = cmt_date.text.strip().replace('-', '.')
                cmt['comment_id'] = cmt_e.get_attribute('data-idxno')
                cmt['contents'] = cmt_section.text.strip()
                # 댓글 반응
                good, bad = cmt_footer.find_elements_by_xpath('./div[@class="comments-vote"]/button')
                cmt['good'] = good.text.strip()
                cmt['bad'] = bad.text.strip()
                self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{cmt_page_unit+i+1}] {cmt["contents"]} ')

                # 답글(대댓글) 여부와 댓글에 대한 반응
                if cmt_footer.text.find('답글쓰기') >=0:
                    msg['comment_list'].append(cmt)
                    continue
                else:
                    # 답글(대댓글) 처리
                    # 답글(대댓글)이 플랫 구조임
                    reply_element_list = reply_list[i].find_elements_by_xpath('./article')
                    reply_element_length = len(reply_element_list)
                    cmt['reply_list'] = []
                    for j, reply_e in enumerate(reply_element_list):

                        reply = {}
                        try:
                            reply_header = reply_e.find_element_by_tag_name('header')
                            reply_section = reply_e.find_element_by_tag_name('section')
                            reply_footer = reply_e.find_element_by_tag_name('footer')
                        except:
                            pass
                        else:
                            self.move_to_element(cmt_e)

                            # 답글(대댓글) 작성자와 작성 일시, reply id, 답글(대댓글) 내용
                            reply_user = reply_header.find_element_by_tag_name('strong')
                            reply_date = reply_header.find_element_by_tag_name('small')
                            reply['nickname'] = reply_user.text.strip()
                            reply['create_ts'] = reply_date.text.strip().replace('-', '.')
                            reply['comment_id'] = reply_e.get_attribute('data-idxno')
                            reply['contents'] = reply_section.text.strip()

                            #  답글(대댓글) 반응
                            good, bad = reply_footer.find_elements_by_xpath('./div[@class="comments-vote"]/button')
                            reply['good'] = good.text.strip()
                            reply['bad'] = bad.text.strip()
                        self.logger.info(
                                f'\t\t   대댓글(답글) [{reply_element_length}/{j+1}] {reply["contents"][:80]}')
                        # 답글(대댓글) 목록에 추가
                        cmt['comment_list'].append(reply)
                msg['comment_list'].append(cmt)
        return

    # ==========================================================================
    def next_cmt(self):
        try:
            # 댓글 페이지 목록 구하기
            ple = self.get_by_xpath('//ul[@class="pagination text-center"]')
            pa_list = ple.find_elements_by_tag_name('li')
        except Exception as err:
            raise
        else:
            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.get_attribute('class') == 'current user-bg':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'current user-bg':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 댓글 다음 페이지 클릭후의 결과 댓글 페이지 번호 구하기
                    nple = self.get_by_xpath('//ul[@class="pagination text-center"]')
                    for npa in nple.find_elements_by_tag_name('li'):
                        if npa.get_attribute('class') == 'current user-bg':
                            npa_pg_num = npa.text.strip()
                            if npa_pg_num == current_pg_num:
                                self.cmt_done = True
                                return
                            else:
                                break
                    return
            self.cmt_done = True
        finally:
            pass

    # ==========================================================================
    def check_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.implicitly_wait(after_wait=1)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        # 페이지 오류 발생 처리
        urling = self.driver.current_url
        if urling != msg['article_url']:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            return

        # self.logger.info(f'checking.... Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
        # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
        delay_a = random.uniform(
            self.config['params']['site']['delay']['article']['min'],
            self.config['params']['site']['delay']['article']['max'],
        )
        time.sleep(delay_a)

        e = self.get_by_xpath('//div[@class="info-text"]/ul')
        lis = e.find_elements_by_xpath('./li')

        # 작성자(기자)
        if lis[0].text.find('기자') >= 0:
            author = lis[0].text.partition('기자')[0].strip()
            msg['author'] = author

        # 등록일
        if lis[1].text.find('승인') >= 0:
            create_ts = lis[1].text.partition('승인')[2].strip()
            msg['create_ts'] = create_ts + ":" + "00"

        e = self.get_by_xpath('//div[@class="info-text"]/ul')
        # 내용
        try:
            head_content = e.find_element_by_xpath('//div[@class="article-head-sub"]')
            se = e.find_elements_by_xpath('//div[@id="article-view-content-div"]/p')
        except:
            msg['contents'] = ''
        else:
            contents = head_content.text.strip()
            for i in se:
                contents += i.text.strip()
            msg['contents'] = contents

        search_key = self.config['params']['site']['search']
        if search_key in msg['title'] or search_key in msg['contents']:
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            return True
        else:
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            return False

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.implicitly_wait(after_wait=1)
        # 팝업창 처리 로직
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)
        e = self.driver.current_url
        if 'popup' in e:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.implicitly_wait(after_wait=1)

        # 페이지 오류 발생 처리
        urling = self.driver.current_url
        if urling != msg['article_url']:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)
            return

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 수집 영역
            e = self.get_by_xpath('//header[@class="article-view-header"]//a[last()]')
            msg['board_name'] = e.text.strip()

            e = self.get_by_xpath('//div[@class="info-text"]/ul')
            lis = e.find_elements_by_xpath('./li')

            # 작성자(기자)
            if lis[0].text.find('기자') >= 0:
                author = lis[0].text.partition('기자')[0].strip()
                msg['author'] = author

            # 등록일
            if lis[1].text.find('승인') >= 0:
                create_ts = lis[1].text.partition('승인')[2].strip()
                msg['create_ts'] = create_ts + ":" + "00"

            # 내용
            try:
                head_content = e.find_element_by_xpath('//div[@class="article-head-sub"]')
                se = e.find_elements_by_xpath('//div[@id="article-view-content-div"]/p')
            except:
                msg['contents'] = ''
            else:
                contents = head_content.text.strip()
                for i in se:
                    contents += i.text.strip()

                msg['contents'] = contents

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    # 상단바와 하단버튼 삭제
                    e_heads = self.driver.find_elements_by_xpath('//div[@id="article-header-title"]|'
                                                                 '//button[@id="back-to-top"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                        var element = arguments[0];
                        element.parentNode.removeChild(element);
                        """, e_head)
                    self.full_screenshot(msg_capture_f)
            # 본문 안의 이미지 주소 가져오기
            se = e.find_element_by_xpath('//div[@id="article-view-content-div"]')
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = se.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = se.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    if 'default-user.png' in img_src_url:
                        continue
                    else:
                        msg['image_url_list'].append(img_src_url)
                        msg['image_list'].append(f'{x}.png')

            # 댓글
            if lis[2].text.find('댓글') >= 0:
                cmt_num = lis[2].text.partition('댓글')[2].strip()
                msg['num_comments'] = int(cmt_num)

            if msg['num_comments'] == 0:
                pass
            elif msg['num_comments'] <= 5:
                cmt_page_unit = 0
                msg['comment_list'] = []
                self.get_cmt(msg, cmt_page_unit)
            elif msg['num_comments'] > 5:
                msg['comment_list'] = []
                # 댓글 '항목' 펼치기 ( 이 기능은 단 한번만 하면 됨 )
                try:
                    e = self.get_by_xpath('//article[@class="article-reply"]')
                    self.move_to_element(e)
                    more_button = e.find_element_by_xpath('.//footer[@class="reply-footer"]/a')
                except:
                    pass
                else:
                    self.safe_click(more_button)
                    self.implicitly_wait(after_wait=1)

                    cmt_page_unit = 0
                    self.cmt_done = False
                    while not self.cmt_done:
                        self.get_cmt(msg, cmt_page_unit)
                        cmt_page_unit += 5 # 댓글 한 페이지 처리했으면 5개의 댓글 처리한 것임
                        self.next_cmt()

        except Exception as err:
            raise
        finally:
            self.driver.switch_to_window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.21. 21:48:00'
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

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//section[@class="article-list-content text-left"]')
            bil = [bi for bi in e.find_elements_by_xpath('./div')]
            # 한번 게시글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
            for i in range(len(bil)):
                msg = {
                    'page': self.cur_page,
                    'row': i + 1,
                    'user_type': self.config['params']['site']['user_type'],
                    'site': self.config['params']['site']['site'],
                    'site_name': self.config['params']['site']['site_name'],
                    'site_board': self.config['params']['site']['site_board'],
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
                    # 검색 결과물 페이지의 목록(List) 읽기
                    e = self.get_by_xpath('//section[@class="article-list-content text-left"]')
                    ail = [bi for bi in e.find_elements_by_xpath('./div')]
                    bi = ail[i]

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('.//div[@class="list-titles table-cell"]/a')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        article_url = bi.find_element_by_tag_name('a').get_attribute('href')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = article_url

                    # 게시글 id
                    msg['article_id'] = re.search('\?idxno=(.+?)$', msg['article_url']).group(1)

                    # 게시글 본문으로 이동
                    se = bi.find_element_by_xpath('.//a[@href]')
                    title_e = se
                    self.move_to_element(se)
                    # if self.config['params']['site']['site_board'] == '헤드라인':
                    #     if not self.check_article(title_e, msg, i+1):
                    #         continue
                    # else:
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
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//ul[@class="pagination text-center"]')
            pa_list = ple.find_elements_by_tag_name('li')

            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.get_attribute('class') == 'current user-bg':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.get_attribute('class') == 'current user-bg':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 다음 페이지 클릭후의 현재 페이지 번호 구하기
                    nple = self.get_by_xpath('//ul[@class="pagination text-center"]')
                    for npa in nple.find_elements_by_tag_name('li'):
                        if npa.get_attribute('class') == 'current user-bg':
                            npa_pg_num = npa.text.strip()
                            if npa_pg_num == current_pg_num:
                                self.is_done = True
                                return
                            else:
                                break
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
                        # article['image_list'].append(f'{j}.png') 왜 들어가 있는지를 이해 하지 못함
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
        # json 파일 생성
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

            search_section = self.config['params']['site']['site_board']
            if search_section == '해외정보'\
                or search_section == '정책'\
                or search_section == '핫!이슈':

                # 상세 검색 열기
                e = self.get_by_xpath('//*[@id="nav-header"]/div/div/div[3]/div[1]/span/a')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

                # section 선택
                if search_section == '해외정보':
                    e = self.get_by_xpath('//*[@id="search-tabs1"]/form/fieldset[1]/div[2]/div/label[3]')
                elif search_section == '정책':
                    e = self.get_by_xpath('//*[@id="search-tabs1"]/form/fieldset[1]/div[2]/div/label[7]')
                elif search_section == '핫!이슈':
                    e = self.get_by_xpath('//*[@id="search-tabs1"]/form/fieldset[1]/div[2]/div/label[5]')

                self.safe_click(e)
                self.implicitly_wait(after_wait=1)

                # # 제목 및 내용 검색 선택
                # if self.config['params']['site']['search_filter'] == '제목':
                #     e = self.get_by_xpath('//*[@id="search-tabs1"]/form/fieldset[2]/div[2]/div/label[2]')
                # elif self.config['params']['site']['search_filter'] == '내용':
                #     e = self.get_by_xpath('//*[@id="search-tabs1"]/form/fieldset[2]/div[2]/div/label[3]')
                # self.safe_click(e)
                # self.implicitly_wait(after_wait=1)

                # 검색어 입력 및 리턴키
                e = self.get_by_xpath('//*[@id="sc_word"]')
                search_key = self.config['params']['site']['search']
                self.send_keys(e, search_key + Keys.RETURN)
                self.implicitly_wait(after_wait=1)

            elif search_section == '헤드라인':
                e = self.get_by_xpath('//*[@id="mega-menu"]/li[2]/a')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            else:
                self.logger.error(f'Stop crawling because of section value error "{search_section}" ')

            # 출력 결과 리스트 형식 바꾸기(단순하게)
            e = self.get_by_xpath('//*[@id="user-container"]/div[3]/div[2]/section/article/div[2]/header/div[2]/a[1]/i')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            search_result = self.get_by_xpath('//*[@id="user-container"]/div[3]/div[2]/section/article/div[2]/header/div[1]/small')
            search_result_num= re.search('\((.+?)\)$', search_result.text.strip()).group(1).split('건')[0]
            self.logger.info(f" >>> 검색 섹션 : {search_section} || 검색 단어: {self.config['params']['site']['search']} || 검색 결과 갯수: {search_result_num}")

            if search_result_num == '0':
                return

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
                self.implicitly_wait(after_wait=1) # 다음 루틴에서 간혹 오류 발생하여 넣어줌
                self.next_page()
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with ThinkfoodSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'thinkfood_all.yaml'
    do_start(config_f=_config_f)
