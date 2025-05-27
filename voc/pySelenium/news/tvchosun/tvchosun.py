"""
====================================
 :mod:`tvchosun`
====================================
.. moduleauthor::  Kyobong An <akb0930@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for tvchosun(tv조선뉴스)
"""
# Authors
# ===========
#
# * JeYoung Park, Kyobong An, Jerry Chae
#
# Change Log
# --------
#
#  * [2023/06/28]
#     - 더보기가 없는 경우도 존재, 댓글 영역이 존재하지 않는 경우도 존재하야 회피 로직 추가
#  * [2023/04/18]
#     - 스크린샷에 댓글 부분 포함
#  * [2023/03/09]
#     - 시간 비교가 아닌 max_article로 제한
#     - 게시글내부에서 작성일 가져오도록 수정
#  * [2023/03/08]
#     - 게시글 목록 스크린샷 추가
#  * [2023/03/02]
#     - 키워드 검색하여 수집하는 방식으로 수정
#  * [2022/03/16]
#     - 1차 버전 완료


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
class TvchosunSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'TvchosunSearch.log'),
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
        self.logger.info(f'Starting Tvchosun Crawling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):

        # 검색어 입력
        e_b = self.get_by_xpath('//div[@class="head_gnb"]//div[@class="s_util_mn"]/a')
        self.safe_click(e_b)
        self.implicitly_wait(after_wait=1)

        e = self.get_by_xpath('//input[@type="text"]')
        self.send_keys(e, self.config['params']['site']['search'] + Keys.ENTER)
        self.implicitly_wait(after_wait=1)

        # 더보기가 존재하지 않는 경우도 존재
        # 더보기 선택
        try:
            e = self.get_by_xpath('//div[@class="se_cont"]/a[@class="btn_more"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=0.5)
        except:
            pass

        # 최신순 선택
        e = self.get_by_xpath('//div[@class="srh_sort"]/ul/li[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=0.5)

    # ==========================================================================
    def get_cmt_reply(self, msg):

        e = self.get_by_xpath('//div[@class="comment_area"]')
        self.move_to_element(e)
        # 댓글 영역이 존재하지 않는 경우도 존재
        try:
            cmt_num = e.find_element_by_xpath('.//strong')
            # 댓글이 없으면 다음 게시글로 돌아간다
            if cmt_num.text.strip() == '0':
                msg['num_comments'] = 0
                self.cmt_done = True
                return

            # 댓글 처리
            # 댓글이 달린 경우 마지막 댓글 리스트 항목은 데이타가 아닌 메세지이므로 사전에 제거

            cmt_list = e.find_elements_by_xpath('.//ul[@class="cmtList_area"]/li')
            cmt_count = 0
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
                self.move_to_element(cmt_e)
                try:
                    cmt_top, cmt_bottom, cmt_eval, reply_module = cmt_e.find_elements_by_xpath('./p | ./div')
                except:
                    pass
                else:
                    nickname = cmt_top.find_element_by_xpath('./span[@class="name"]')
                    create_time = cmt_top.find_element_by_xpath('./span[@class="date"]')

                    # 댓글 id
                    cmt['parent_comment_id'] = ''
                    cmt['comment_id'] = cmt_bottom.get_attribute('id')
                    cmt['is_reply'] = False

                    parent_comment_id = cmt['comment_id']

                    # 닉네임, 작성 일시, 내용
                    cmt['create_ts'] = create_time.text.strip()
                    cmt['nickname'] = nickname.text.strip()
                    cmt['contents'] = cmt_bottom.text.strip()

                    like = cmt_eval.find_element_by_xpath('./button[@class="btn good"]')
                    like_text = like.text.split('찬성')
                    if like_text[-1] != '':
                        cmt['like'] = int(like_text[-1].split())
                    else:
                        cmt['like'] = 0

                    dislike = cmt_eval.find_element_by_xpath('./button[@class="btn bad"]')
                    dislike_text = dislike.text.split('반대')
                    if dislike_text[-1] != '':
                        cmt['dislike'] = int(dislike_text[-1].split())
                    else:
                        cmt['dislike'] = 0

                    cmt['comment_img'] = []
                    cmt['comment_img_url'] = []
                    inner_html = cmt_e.get_attribute('innerHTML') # 이미지 추출용
                    if inner_html.find('attach-multi-btn') > 0 or inner_html.find('attach-image-btn') > 0:
                        cmt_img_list = cmt_bottom.find_elements_by_xpath('.//button[@class="attach-multi-btn"] \
                                                                        | .//button[@class="attach-image-btn"]')
                        for x, img in enumerate(cmt_img_list):
                            img_src = img.find_element_by_xpath('./span | ./img')
                            cmt['comment_img'].append(f'{cmt["comment_id"]}_{x}.png')
                            cmt['comment_img_url'].append(img_src.get_attribute('data-src'))
                    cmt_count += 1
                    self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{cmt_count}] {cmt["contents"]} ')
                    msg['comment_list'].append(cmt)

                # 답글 부분
                # 답글 여부 확인

                e = cmt_e.find_element_by_xpath('.//button[@class="btn reply"]')
                if e.text == '답글':
                    continue
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
                # 존재하는 대댓글(답글) 처리
                reply_list = cmt_e.find_elements_by_xpath('.//ul[@class="replyList"]/li')
                for j, reply_e in enumerate(reply_list):
                    self.move_to_element(reply_e)
                    reply = {
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
                    try:
                        nickname = reply_e.find_element_by_xpath('.//span[@class="name"]')
                        create_time = reply_e.find_element_by_xpath('.//span[@class="date"]')
                        contents = recmment_id = reply_e.find_element_by_xpath('.//p[@class="cmt"]')
                    except:
                        pass
                    else:
                        # 닉네임, 작성 일시, 내용, id
                        # 작성 일시의 경우 24시간이 지나지 않으면 'xx 시간전'으로 표기되어 다음 방법을 사용함)
                        reply['comment_id'] = recmment_id.get_attribute('id')

                        reply['create_ts'] = create_time.text.strip()
                        reply['nickname'] = nickname.text.strip()
                        reply['contents'] = contents.text.strip()

                        reply['comment_img'] = []
                        reply['comment_img_url'] = []
                        inner_html = reply_e.get_attribute('innerHTML')  # 이미지 추출용
                        if inner_html.find('attach-multi-btn') > 0 or inner_html.find('attach-image-btn') > 0:
                            reply_img_list = reply_e.find_elements_by_xpath('.//button[@class="attach-multi-btn"] \
                                                                            | .//button[@class="attach-image-btn"]')
                            for x, img in enumerate(reply_img_list):
                                img_src = img.find_element_by_xpath('./span | ./img')
                                reply['comment_img'].append(f'{reply["comment_id"]}_{x}.png')
                                reply['comment_img_url'].append(img_src.get_attribute('data-src'))
                    cmt_count += 1
                    self.logger.info(f'\t\t   대댓글 [{msg["num_comments"]}/{cmt_count}')
                    msg['comment_list'].append(reply)
            self.cmt_done = True
            return
        except:
            msg['num_comments'] = 0
            self.cmt_done = True
            return

    # ==========================================================================
    def get_article(self, title_e, msg, ndx):

        title_e.send_keys(Keys.CONTROL + Keys.RETURN)
        self.implicitly_wait(after_wait=1)
        self.driver.switch_to_window(self.driver.window_handles[-1])
        self.implicitly_wait(after_wait=1)

        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            # 등록일
            e = self.get_by_xpath('//div[@class="article_tit"]/p')
            se = e.text.strip()
            if '수정' in se:
                create_ts = se.split(' /')[0].replace('등록 ', '')
            else:
                create_ts = se.replace('등록 ', '')
            msg['create_ts'] = create_ts + ":00"

            # 작성자(기자 혹은 기관) : 간혹 없는 경우 발생
            try:
                se = self.get_by_xpath('//*[@id="wrap"]/div/div[1]/div[6]/div[1]/a/span')
                author = re.search(r'(.+?)\s+기자', se.text.strip()).group(1).strip()
            except:
                msg['author'] = ''
            else:
                msg['author'] = author

            # 내용
            msg['contents'] = ''
            try:
                article_body = self.get_by_xpath('//div[@class="article_detail_body"]')
            except:
                msg['contents'] = ''
            else:
                msg['contents'] = article_body.text.strip()

            # 본문 안의 이미지 주소 가져오기
            article_body = self.get_by_xpath('//div[@class="article_detail_body"]')
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = article_body.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('img') > 0:
                img_list = article_body.find_elements_by_tag_name('img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    msg['image_list'].append(f'{x}.png')
                    msg['image_url_list'].append(img_src_url)

            # 댓글 저장
            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt_reply(msg)
                if self.cmt_done:
                    break
            if len(msg['comment_list']) > 1 and msg['comment_list'][0]['comment_id'] is None:
                del msg['comment_list'][0]
                msg['num_comments'] = len(msg['comment_list'])

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    # 상단바와 하단바 삭제
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="simple"]|'
                                                                 '//div[@class="pieceBanner"]|'
                                                                 '//div[@class="randomBanner"]|'
                                                                 '//div[@class="top_btn resize"]')
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
            e = self.get_by_xpath('//div[@class="se_cont"]/div/ul')
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
                    # 게시글 목록 스크린샷
                    self.driver.set_window_size(self.config['params']['kwargs']['width'], 2500)
                    s_shot = self.config['target']['folder'].replace('latest', 'logs') + f'_{self.cur_page}.png'
                    s_shot = s_shot[:s_shot.rfind('/')] + '/list_capture' + s_shot[s_shot.rfind('/'):]
                    self.driver.find_element_by_tag_name('body').screenshot(self.get_safe_path(s_shot))

                    # 검색 결과물 페이지의 목록(List) 읽기
                    e = self.get_by_xpath('//div[@class="se_cont"]/div/ul')
                    ail = [bi for bi in e.find_elements_by_xpath('./li')]
                    bi = ail[i]
                    self.move_to_element(bi)

                    # 등록일
                    # se = bi.find_element_by_xpath('.//p[@class="date"]')
                    # create_ts = se.text.strip()
                    # msg['create_ts'] = create_ts + ":00"

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('.//p[@class="article_tit"]/a')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        article_url = bi.find_element_by_xpath('.//p[@class="article_tit"]/a')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = article_url.get_attribute('href')

                    # 게시글 id
                    msg['article_id'] = re.search('(\d+)\.html$', msg['article_url']).group(1).strip()

                    # if self.stop_article_older_than(msg):
                    #     if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                    #         shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                    #     self.is_done = True
                    #     break
                    # 1) 카테고리 : board_name
                    e = bi.find_element_by_xpath('.//p[@class="tag"]/span[1]')
                    board_name = e.text.strip()
                    if board_name in ["사회"]:
                        msg['board_name'] = board_name
                    else:
                        self.logger.info('pass')
                        continue

                    # 게시글 본문으로 이동
                    title_e = article_url
                    self.move_to_element(article_url)
                    self.get_article(title_e, msg, i+1)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                self.save_image(msg)
                self.output['article_list'].append(msg)
                if self.config['target']['is_separate_article']:
                    self.save_article(msg)

                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = msg['create_ts']

                # tv조선의 경우 시간으로만 제어함
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
            try:
                ple = self.get_by_xpath('//ul[@class="pagination"] | //div[@class="pagination"]')
                pa_list = ple.find_elements_by_xpath('./a | ./span/span | ./span/a')
            except:
                # 페이지가 없는 경우
                self.is_done = True
                return

            # 현재 페이지 번호 구하기
            for pa in pa_list:
                if pa.tag_name == 'span':
                    current_pg_num = pa.text.strip()
                    break

            is_current = False
            for pa in pa_list:
                if pa.tag_name == 'span':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)

                    # 다음 페이지 클릭후의 현재 페이지 번호 구하기
                    nple = self.get_by_xpath('//ul[@class="pagination"] | //div[@class="pagination"]')
                    for npa in nple.find_elements_by_xpath('./a | ./span/span | ./span/a'):
                        if npa.tag_name == 'span':
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

        for cmt in article['comment_list']:
            if not('comment_img' in cmt and cmt['comment_img']):
                continue
            for k, c in enumerate(cmt['comment_img_url']):
                try:
                    cmt_img_f = self.get_safe_path(
                        self.config['target']['folder'],
                        article['article_id'],
                        f'{cmt["comment_id"]}_{k}.png'
                    )
                    urllib.request.urlretrieve(c, cmt_img_f)
                except Exception as err:
                    self.logger.error(f'save_img: {cmt["comment_id"], cmt["comment_img"]}: {str(err)}')

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
    def prev_day(self):

        self.is_done = False
        try:
            # 7일 목록 구하기
            try:
                current_day = self.get_by_xpath('//div[@class="date_list"]/ul')
                date_list = current_day.find_elements_by_xpath('./li')
            except:
                # 페이지가 없는 경우
                self.is_done = True
                return

            is_current = False
            for pa in date_list:
                if pa.get_attribute('class') == 'active':
                    is_current = True
                    continue
                if is_current:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=1)
                    return
            self.is_done = True
        except Exception as err:
            raise
        finally:
            pass

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            # 키워드 검색
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
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()

################################################################################
def do_start(**kwargs):
    with TvchosunSearch(kwargs['config_f']) as ws:
        ws.start()

################################################################################
if __name__ == '__main__':
    _config_f = 'tvchosun.yaml'
    do_start(config_f=_config_f)
