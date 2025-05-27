"""
====================================
 :mod:`imnews`
====================================
.. moduleauthor:: Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for imnews (MBC 뉴스)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An
#
# Change Log
# --------
#
#  * [2023/04/18]
#     - 스크린샷 부분에 댓글 포함
#     - board_name에 값 추가
#  * [2022/03/08]
#     - 기본 포맷 적용
#  * [2022/02/08]
#     - 일부 코드 수정
#  * [2022/01/30]
#     - 1차 버전 완료
#     - 화면 캡쳐 기능 미동작 : 향후 해결
#     - starting
#  TODO: 동영상 추출 현재 사이트에는 .m3u8(스트리밍)형식으로 되어있음.
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
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################
class ImnewsSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'ImnewsSearch.log'),
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
        self.logger.info(f'Starting Imnews Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def get_cmt(self, msg):

        # 댓글이 없으면 다음 게시글로 돌아간다 : return
        e = self.get_by_xpath('//*[@id="commentBox"]/div[1]')
        self.move_to_element(e)
        msg['num_comments'] = int(e.text.strip())
        if msg['num_comments'] == 0:
            self.cmt_done = True
            return
        # 댓글
        msg['comment_list'] = []
        # 댓글 전부를 펼치기
        while True:
            e = self.get_by_xpath('//*[@id="commentBox"]/div[4]')
            se = e.find_element_by_class_name('wrap_more')
            style = se.get_attribute('style')
            if style == 'display: none;':
                break
            else:
                self.safe_click(se)
                self.implicitly_wait(after_wait=1)
                self.move_to_element(e)

        # 댓글 처리
        e = self.get_by_xpath('//div[@class="list_comment"]/ul')
        cmt_list = e.find_elements_by_xpath('./li')
        for i, cmt in enumerate(cmt_list):   # 확보된 댓글 리스트를 하나씩 처리하기

            cmt_e = cmt.find_element_by_class_name('u_comment_box') # 댓글
            reply_e = cmt.find_element_by_class_name('u_wrap_reply') # 대댓글

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
                user = cmt_e.find_element_by_xpath('.//div[@class="user"]')
                comment = cmt_e.find_element_by_xpath('.//div[@class="user_content"]')
                user_ui_btn = cmt_e.find_element_by_xpath('.//div[@class="user_ui_btn"]')
            except:
                pass    # 추후 처리
            else:
                # 댓글 작성자 정보
                user_info = user.find_elements_by_tag_name('span')
                cmt['nickname'] = user_info[0].text.strip()
                cmt['create_ts'] = user_info[1].text.strip().replace('-', '.')
                id_from = user_info[0].get_attribute('class')
                # cmt['id_from'] = id_from.split()[-1]
                cmt['is_reply'] = False
                cmt['parent_comment_id'] = ''
                # commet_id가 없음.
                cmt['comment_id'] = cmt['nickname'].replace('*', '') + re.sub(r'([^0-9])', '', cmt['create_ts'])
                parent_comment_id = cmt['comment_id']
                # 댓글 내용
                cmt['contents'] = comment.text.strip()

                # 댓글에 대한 반응
                like_hate = user_ui_btn.find_elements_by_tag_name('button')
                like = like_hate[1]
                hate = like_hate[2]
                cmt['like'] = int(like.text.strip())
                cmt['dislike'] = int(hate.text.strip())
            finally:
                self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{i+1}]')
                msg['comment_list'].append(cmt)

            # 대댓글 처리
            # cmt['reply_list'] = list()
            try:
                reply_info = user_ui_btn.find_element_by_class_name('btn_reply')
                reply_status = reply_info.text.strip()
            except:
                pass
            else:
                if reply_status != '답글 작성':  # 즉 답글이 있다면

                    reply_num = reply_status.split()[-1].strip()
                    reply_btn = user_ui_btn.find_element_by_class_name('btn_reply')
                    self.safe_click(reply_btn)
                    self.implicitly_wait(after_wait=1)

                    reply_list = reply_e.find_elements_by_class_name('u_comment_reply')
                    reply_num = len(reply_list) - 1
                    reply_count = 0
                    # 여기서부터 대댓글 처리
                    for x, reply_e in enumerate(reply_list):

                        reply_count = x
                        # 대댓글의 마지막 항목은 대댓글 접기임.따라서 처리 완료임을 의미
                        if x == len(reply_list) - 1:
                            break
                        reply = {
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
                            reply_user = reply_e.find_element_by_xpath('.//div[@class="user"]')
                            reply_comment = reply_e.find_element_by_xpath('.//div[@class="user_content"]')
                            reply_user_ui_btn = reply_e.find_element_by_xpath('.//div[@class="user_ui_btn"]')
                        except:
                            pass
                        else:
                            # 대댓글 작성자 정보
                            reply_user_info = reply_user.find_elements_by_tag_name('span')
                            reply['nickname'] = reply_user_info[0].text.strip()
                            reply['create_ts'] = reply_user_info[1].text.strip().replace('-', '.')
                            id_from = reply_user_info[0].get_attribute('class')
                            # reply['id_from'] = id_from.split()[-1]
                            reply['is_reply'] = True
                            reply['parent_comment_id'] = parent_comment_id
                            # 대댓글 내용
                            reply['contents'] = reply_comment.text.strip()
                            reply['comment_id'] = reply['nickname'].replace('*', "") + re.sub(r'([^0-9])', '',
                                                                                              cmt['create_ts'])

                            # 대댓글에 대한 반응
                            like_hate = reply_user_ui_btn.find_elements_by_tag_name('button')
                            like = like_hate[0]
                            hate = like_hate[1]
                            reply['like'] = int(like.text.strip())
                            reply['dislike'] = int(hate.text.strip())

                            # 대댓글 목록에 추가
                            # cmt['reply_list'].append(reply)
                            msg['comment_list'].append(reply)
                            # self.logger.info(f'\t\t   대댓글 [{len(reply_list)-1}/{len(cmt["reply_list"])}] {reply["contents"][:80]}')
                    if reply_count != reply_num:
                        self.logger.error(f' ****** 대댓글 수: {reply_num} / 처리된 대댓글 수: {reply_count}')
                        # 댓글 목록에 추가

        self.cmt_done = True
        return

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        # 동일 윈도우탭에서 처리시 지연문제 발생 따라서 별도 탭으로 분리하여 처리함
        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        # 페이지 오류 발생 처리
        urling = self.driver.current_url
        if urling != msg['article_url']:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])
            return

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            e = self.get_by_xpath('//*[@id="content"]/div/section[1]/article/div[1]/div[3]/div[1]/span[2]')
            create_date = e.text.strip()
            create_ts = re.search('수정\s+(.+?)$', create_date).group(1)
            msg['create_ts'] = create_ts.replace('-', '.') + ":" + "00"

            e = self.get_by_xpath('//div[@class="news_txt"]')
            # 내용
            try:
                msg['contents'] = e.text
            except:
                msg['contents'] = ''

            # # 화면 캡쳐
            # if self.config['params']['site']['capture_article']:
            #     msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
            #                                        f'{msg["article_id"]}.png')
            #     if self.config['params']['kwargs']['headless']:
            #         self._screenshot(msg_capture_f)
            #     else:
            #         e_heads = self.driver.find_elements_by_xpath('//div[@class="wrap_pc_nav"]')
            #         for e_head in e_heads:
            #             self.driver.execute_script("""
            #                                     var element = arguments[0];
            #                                     element.parentNode.removeChild(element);
            #                                     """, e_head)
            #         self.full_screenshot(msg_capture_f)

            # 본문 안의 이미지 주소 가져오기
            msg['image_url_list'] = []
            try:
                img_src = e.find_elements_by_tag_name('img')
            except:
                pass
            else:
                for x, img in enumerate(img_src):
                    msg['image_url_list'].append(img.get_attribute('src'))
                    msg['image_list'].append(f'{x}.png')

            # 기사 평가
            opinion_dict = {'좋아요': 'good',
                            '훌륭해요': 'great',
                            '슬퍼요': 'sad',
                            '화나요': 'angry',
                            '후속요청': 'news'}
            msg['good'] = 0
            msg['great'] = 0
            msg['sad'] = 0
            msg['angry'] = 0
            msg['news'] = 0
            e = self.get_by_xpath('//*[@id="commentLoc"]')
            se = e.find_elements_by_tag_name('li')
            for x, opinion in enumerate(se):
                key_value = opinion.text.split('\n', 2)
                msg[opinion_dict[key_value[0]]] = int(key_value[1])

            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt(msg)
                if self.cmt_done:
                    break
            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="wrap_pc_nav"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                    var element = arguments[0];
                                                    element.parentNode.removeChild(element);
                                                    """, e_head)
                    self.full_screenshot(msg_capture_f)
        except Exception as err:
            raise
        finally:
            self.driver.close()
            self.driver.switch_to_window(self.driver.window_handles[0])

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
            e = self.get_by_xpath('//*[@id="result"]/div[2]/div/div[3]/ul')
            bil = [bi for bi in e.find_elements_by_xpath('./li')]
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
                    e = self.get_by_xpath('//*[@id="result"]/div[2]/div/div[3]/ul')
                    ail = [bi for bi in e.find_elements_by_xpath('./li')]
                    bi = ail[i]

                    # 기사제목, 게시글 id, 등록일, 조회수,

                    mySpans = bi.find_elements_by_tag_name('span')
                    for x , span in enumerate(mySpans):

                        # 게시글 제목
                        if span.get_attribute('class') == "tit ellipsis2":
                            msg['title'] = span.text.strip()
                        # 기자: 'reporter'->'author'
                        elif span.get_attribute('class') == "reporter":
                            msg['author'] = span.text.strip()
                        # 수집 영역: 사회 카테고리 선택할 경우, 사회/뉴스데스크/뉴스투데이 등 노출
                        elif span.get_attribute('class') == "category":
                            msg['board_name'] = span.text.strip()
                        # 등록일
                        elif span.get_attribute('class') == "date":
                            create_date = span.text.strip()
                            msg['create_ts'] = create_date.replace('-', '.') + " " + "00:00:00"

                    # 게시글 URL
                    myURL = bi.find_element_by_tag_name('a').get_attribute('href')
                    msg['article_url'] = myURL

                    # 게시글 id
                    msg['article_id'] = myURL.split('/')[-1].split('.')[0]

                    # 게시글 본문으로 이동
                    se = bi.find_element_by_xpath('.//a[@href]')
                    title_e = se
                    self.move_to_element(se)
                    self.get_article(title_e, msg, i+1)
                    time.sleep(1)

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
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    pass
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
            ple = self.get_by_xpath('//div[@class="paging_area"]')

            is_current = False
            for pa in ple.find_elements_by_tag_name('a'):
                if pa.get_attribute('class') == 'page_num on':
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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )

        # save image
        for j, sub_e_url in enumerate(article['image_url_list']):
            cmt_img_f = self.get_safe_path(
                self.config['target']['folder'],
                article['article_id'],
                f'{j}.png'
            )
            urllib.request.urlretrieve(sub_e_url, cmt_img_f)

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

            # 검색란 보이기
            e = self.get_by_xpath('//*[@id="header"]/div[1]/div[2]/div[1]/div[3]/button')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색어 입력
            e = self.get_by_xpath('//*[@id="kwd"]')
            search_key = self.config['params']['site']['search']
            self.send_keys(e, search_key)

            # 검색 단추
            e = self.get_by_xpath('//*[@id="header"]/div[1]/div[2]/div[2]/div/div/button',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색 선택사양 보이기
            e = self.get_by_xpath('//*[@id="result"]/div[1]/div[1]/form/fieldset/div[2]/button[1]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 검색 선택사양 '사회' 선택
            e = self.get_by_xpath('//*[@id="result"]/div[1]/div[2]/form/fieldset/div[1]/ul/li[3]/label/span[1]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            search_result = self.get_by_xpath('//*[@id="result"]/div[1]/div[2]/form/fieldset/div[1]/ul/li[3]/label/span[2]/span')
            search_result_num = re.search('\((.+?)\)', search_result.text).group(1)
            self.logger.info(f" >>>>> 검색 단어: {self.config['params']['site']['search']} || 검색 결과 갯수: {search_result_num}")
            if search_result_num == '0':
                return

            # 검색 결과물인 각 페이지 처리
            while not self.is_done:
                self.get_page()
                if self.is_done:
                    break
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
    with ImnewsSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'imnews.yaml'
    do_start(config_f=_config_f)
