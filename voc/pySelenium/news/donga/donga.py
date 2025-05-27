"""
====================================
 :mod:`donga`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Web scraping module for donga (동아일보)
"""
# Authors
# ===========
#
# * JeYoung Park, Jerry Chae
#
# Change Log
# --------
#
#  * [2023/04/18]
#     - board_name 값 추가
#  * [2023/02/27]
#     - 게시글 없을 시 로그 추가
#  * [2023/01/06]
#     - 전체적인 사이트 UI 변경
#  * [2022/11/29]
#     - 전체적인 사이트 UI 변경
#     - 검색 필터 - (검색 기간: 1일 추가)
#  * [2022/04/13]
#     - 필요없는 Key제거, headless 캡처 추가 게시글 목록에서 create_ts 비교
#  * [2022/02/25]
#     - 1차 버전 완료

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
from urllib.request import urlretrieve
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


################################################################################
class DongaSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DongaSearch.log'),
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
        self.logger.info(f'Starting Donga Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        url = 'https://www.donga.com/news/search?sorting=1&check_news=1&search_date=6&v1=&v2=&more=1&query=' +\
              self.config['params']['site']['search']
        self.driver.get(url)

        # 동아일보 지면기사만
        # e = self.get_by_xpath('//div[@class="dongaArticle"]')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

        # 검색기간 설정
        # e = self.get_by_xpath('//div[@class="nav_cont"]/div[3]//button[@class="tag"]')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

        # 1일 선택
        # e = self.get_by_xpath('//div[@class="nav_cont"]/div[3]/div[@id="sort_layer"]//li[2]')
        # self.safe_click(e)
        # self.implicitly_wait(after_wait=1)

    # ==========================================================================
    def get_cmt_reply(self, msg):

        e = self.get_by_xpath('//div[@class="reply_top"]')
        cmt_num = e.find_element_by_xpath('.//em[@id="replyCnt"]')
        cmt_check_list = 0
        self.move_to_element(e)

        # 댓글이 없으면 다음 게시글로 돌아간다
        if cmt_num.text.strip() == '0':
            msg['num_comments'] = 0
            self.cmt_done = True
            return

        # 댓글이 3개 이하일 경우 다른 방식으로 수집
        # if cmt_num.text.strip() <= '3':
        #     msg['num_comments'] = int(cmt_num.text.strip())
        #     self.cmt_done = True
        #     return

        # 댓글 리스트를 다시 선언
        msg['comment_list'] = []

        # '전체 댓글 보기' 클릭 => 댓글 팝업창 열림
        try:
            more = self.get_by_xpath('//div[@class="right_box"]/span[@class="btn_reply reply_yes"]')
            self.safe_click(more)
            self.implicitly_wait(after_wait=1)
        except:
            pass
        else:
            if more.get_attribute('style') != 'display: none;':
                self.safe_click(more)
                self.implicitly_wait(after_wait=1)

            # 댓글 팝업 처리 + '더보기' 클릭
                while True:
                    try:
                        pop_up = self.get_by_xpath('//div[@id="replyLayerPopup"]')
                        more_button = pop_up.find_element_by_xpath('.//div[@class="more"]')
                        cmt_num = pop_up.find_element_by_xpath('.//span[@class="txt"]/em[@class="replyCnt"]')
                        msg['num_comments'] = int(cmt_num.text.strip())
                        cmt_list = pop_up.find_elements_by_xpath('.//ul[@class="commentList"]/li')
                        if cmt_check_list == cmt_list:
                            break
                    except:
                        break
                    else:
                        self.move_to_element(more_button)
                        if more_button.text.strip() == '더보기':
                            self.safe_click(more_button)
                            self.implicitly_wait(after_wait=1)
                            cmt_check_list = cmt_list
                        else:
                            break
            else:
                e = self.get_by_xpath('//div[@class="reply_wrap"]')
                cmt_num = e.find_element_by_xpath('.//em[@class="replyCnt"]')
                msg['num_comments'] = int(cmt_num.text.strip())
                cmt_list = e.find_elements_by_xpath('.//div[@id="replyLayerPopup"]//div[@class="spinTopLayerList"]//ul/li')

        # 댓글 처리
        cmt_count = 0
        for i, cmt_e in enumerate(cmt_list):  # 확보된 댓글 리스트를 하나씩 처리하기

            # 동아일보의 경우 눈에 보이지 않는 태그가 3개나 잡힘, 이를 제거하기 위한 루틴 필요
            # 다른 방법을 찾아야 함
            if cmt_e.text.strip() == '':
                continue

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

            # Best 댓글의 경우 일반 댓글과 달리 html 구조가 달라서 이 경우를 고려한 코드 필요
            # Best 댓글은 li 태그 밑에 3개의 div 태그 존재
            # 알반 댓글은 li 캐그 밑에 2개의 div 태그 존재
            div_count = len(cmt_e.find_elements_by_xpath('./div'))

            try:
                div_module = cmt_e.find_element_by_xpath('.//div[@class="module"]')
                div_5e = div_module.find_elements_by_xpath('./div')
                # inner_html = cmt_e.get_attribute('innerHTML') # 이미지 추출용
            except:
                pass
            else:
                # 닉네임, 작성 일시, 내용, id
                cmt['nickname'] = div_5e[0].text.strip()
                cmt['create_ts'] = div_5e[1].text.strip().replace('-', '.')
                cmt['contents'] = div_5e[2].text.strip()

                # 답글(대댓글) 여부와 댓글에 대한 반응 : div_5e[3]
                reply_num = div_5e[3].find_element_by_class_name('reply')
                if div_count == 2:
                    cmt['comment_id'] = div_5e[4].get_attribute('id').split('_')[-1]
                elif div_count == 3:
                    cmt['comment_id'] = div_5e[4].get_attribute('id').split('_')[-2]

                up_count = div_5e[3].find_element_by_class_name('agree')
                down_count = div_5e[3].find_element_by_class_name('disagree')
                num_replys = reply_num.text.strip().replace('(', '').replace(')', '')
                cmt['is_reply'] = False
                cmt['parent_comment_id'] = ''
                cmt['like'] = int(up_count.text.strip().replace('추천', ''))
                cmt['dislike'] = int(down_count.text.strip().replace('비추천', ''))

                cmt_count += 1
                self.logger.info(f'\t   댓글 [{msg["num_comments"]}/{cmt_count}]')
            # 답글 여부 확인
            if num_replys == '' or num_replys == '0':
                msg['comment_list'].append(cmt)
                continue
            else:

                # 답글(대댓글) 펼치기 작업 필요
                reply_display = div_5e[3].find_element_by_class_name('notify')
                self.safe_click(reply_display)
                self.implicitly_wait(after_wait=1)

                reply_module = cmt_e.find_element_by_xpath('.//div[@class="module"]/div[5]')
                reply_list = reply_module.find_elements_by_xpath('.//ul[@class="commentList"]/li')
                reply_count = 0
                for j, reply_e in enumerate(reply_list):

                    self.move_to_element(reply_e)
                    reply = {}
                    try:
                        e_module, e_op = reply_e.find_elements_by_xpath('./div')
                        e_module_div_5e = e_module.find_elements_by_xpath('./div')
                    except:
                        pass
                    else:
                        # 닉네임, 작성 일시, 내용, id
                        reply['nickname'] = e_module_div_5e[0].text.strip()
                        reply['create_ts'] = e_module_div_5e[1].text.strip().replace('-', '.')
                        reply['contents'] = e_module_div_5e[3].text.strip()
                        reply['is_reply'] = True
                        reply['parent_comment_id'] = e_module_div_5e[4].get_attribute('id').split('_')[-1]

                        # 답글(대댓글) 여부와 댓글에 대한 반응 : div_5e[3]
                        up_count = e_op.find_element_by_class_name('agree')
                        down_count = e_op.find_element_by_class_name('disagree')
                        reply['like'] = int(up_count.text.strip().replace('추천', ''))
                        reply['dislike'] = int(down_count.text.strip().replace('비추천', ''))

                        reply_count += 1
                        self.logger.info(f'\t\t   대댓글 [{num_replys}/{reply_count}] {reply["contents"]} ')
                    # 답글(대댓글) 목록에 추가
                    msg['comment_list'].append(reply)
                msg['comment_list'].append(cmt)
        self.cmt_done = True
        e = self.get_by_xpath('//*[@class="reply_top_wrap"]/span[@class="layer_close"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)
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

            # 동아일보 기사의 site_board 찾기 (현재 site_board 값 = 사회)
            se = self.get_by_xpath('//div[@class="article_title"]/div[@class="location"]/a')
            category = se.text.strip()
            msg['site_board'] = category
            msg['board_name'] = category
            if category != self.config['params']['site']['site_board']:
                # 다음 항목은 디버깅용과 속도 문제로 인한 오류 발생을 방지하기 위함
                # 만약 제거한다면 time.sleep(1) 추가 필요
                self.logger.info(f'***** SKIPing {category} ..... Page[{self.cur_page}:{ndx}], title="{msg["title"]}"')
                return

            e = self.get_by_xpath('//div[@class="article_title"]')

            # 작성자(기자 혹은 기관) : 간혹 없는 경우 발생
            try:
                se = e.find_element_by_xpath('./div[@class="report"]')
            except:
                msg['author'] = ''
            else:
                author = se.text.strip().split('|')[0]
                msg['author'] = author

            # 댓글 저장
            self.cmt_done = False
            while not self.cmt_done:
                self.get_cmt_reply(msg)
                if self.cmt_done:
                    break

            # # 등록일
            # se = e.find_element_by_xpath('./div[@class="title_foot"]/span')
            # create_ts = se.text.strip().split('입력')[-1]
            # msg['create_ts'] = create_ts.replace('-', '.').strip() + ":00"

            # 내용 (= 부제목 + 내용)
            try:
                e = self.get_by_xpath('//div[@class="article_txt"]')
                article_footer = e.find_element_by_xpath('.//div[@class="article_footer"]')
            except:
                msg['contents'] = ''
            else:
                all_text = e.text.strip()
                article_footer_text = article_footer.text.strip()
                msg['contents'] = all_text.replace(article_footer_text, '')

            # 화면 캡쳐
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@id="sub_header"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_head)
                    self.full_screenshot(msg_capture_f)

            e = self.get_by_xpath('//div[@class="article_txt"]')

            # 본문 안의 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            inner_html = e.get_attribute('innerHTML')  # 이미지 추출용
            if inner_html.find('articlePhotoC') > 0:
                img_list = e.find_elements_by_xpath('.//div[@class="articlePhotoC"]/span/img')
                for x, img in enumerate(img_list):
                    img_src_url = img.get_attribute('src')
                    if 'default-user.png' in img_src_url:
                        continue
                    elif 'journalist' in img_src_url:
                        continue
                    else:
                        msg['image_url_list'].append(img_src_url)
                        msg['image_list'].append(f'{x}.png')

            se = e.find_elements_by_xpath('.//ul[@class="feel_list"]/li')
            msg["good"] = int(se[0].find_element_by_tag_name('em').text.strip())
            msg["sad"] = int(se[1].find_element_by_tag_name('em').text.strip())
            msg["angry"] = int(se[2].find_element_by_tag_name('em').text.strip())
            # msg["news"] = int(se[3].find_element_by_tag_name('em').text.strip())

            se = e.find_element_by_xpath('.//div[@class="btn_recommend"]//em[@class="counter"]')
            msg['like'] = int(se.text.strip())

            # # 댓글 저장
            # self.cmt_done = False
            # while not self.cmt_done:
            #     self.get_cmt_reply(msg)
            #     if self.cmt_done:
            #         break

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

            # 검색 결과물 페이지 읽기
            e = self.get_by_xpath('//*[@id="content"]//div[@class="result_cont"]')
            # 검색 결과 없을 때
            if e.text.find('검색 결과가 없습니다.') >= 0:
                self.logger.info('검색 결과가 없습니다.')
                self.is_done = True
                return
            bil = [bi for bi in e.find_elements_by_xpath('./div[@class="articleList article_list"]')]
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
                    e = self.get_by_xpath('//*[@id="content"]//div[@class="result_cont"]')
                    ail = [bi for bi in e.find_elements_by_xpath('./div[@class="articleList article_list"]')]
                    bi = ail[i]

                    e = bi.find_element_by_xpath('.//div[@class="rightList"]/div/span[@class="date"]')
                    msg['create_ts'] = datetime.datetime.strptime(e.text.strip(), '%Y-%m-%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    if self.stop_article_older_than(msg):
                        title = bi.find_element_by_xpath('.//span[@class="tit"]/a[1]')
                        t_a = title.text.strip()
                        self.logger.info(f'***** 최신 게시글 Title: {t_a} .....   ')
                        self.is_done = True
                        break

                    # 게시글 제목
                    try:
                        title = bi.find_element_by_xpath('.//span[@class="tit"]/a[1]')
                    except:
                        msg['title'] = ''
                    else:
                        if title.text.strip() == '':
                            msg['title'] = ''
                        else:
                            msg['title'] = title.text.strip()

                    # 게시글 URL
                    try:
                        article_url = title.get_attribute('href')
                        # article_url = bi.find_element_by_xpath('.//p[@class="tit"]/a').get_attribute('href')
                    except:
                        msg['article_url'] = ''
                    else:
                        msg['article_url'] = article_url

                    # 게시글 id
                    ids = msg['article_url'].split('/')
                    msg['article_id'] = ids[-2] + ids[-1]

                    # 게시글 본문으로 이동
                    se = bi.find_element_by_xpath('.//span[@class="tit"]/a[@href]')
                    title_e = se
                    self.move_to_element(se)
                    self.get_article(title_e, msg, i+1)

                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    msg['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{msg["error_backtrace"]}')
                    self.logger.error(str(err))

                # if self.stop_article_older_than(msg):
                #     if os.path.isdir("/".join([self.config['target']['folder'], msg['article_id']])):
                #         shutil.rmtree("/".join([self.config['target']['folder'], msg['article_id']]))
                #     self.is_done = True
                #     break
                if msg['site_board'] == self.config['params']['site']['site_board']:
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
                else:
                    continue

        except Exception as err:
            raise
        finally:
            return

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록 구하기
            ple = self.get_by_xpath('//div[@class="page"]')
            pa_list = ple.find_elements_by_xpath('./a | ./strong')

            is_current = False
            for pa in pa_list:
                if pa.tag_name == 'strong':
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

            self.search()
            # # 사회 : 검색창 열기
            # e = self.get_by_xpath('//*[@id="nav_icon"]/button[2]')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)
            #
            # # 검색어 입력 및 리턴키
            # e = self.get_by_xpath('//*[@id="query"]')
            # search_key = self.config['params']['site']['search']
            # self.send_keys(e, search_key + Keys.RETURN)
            # self.implicitly_wait(after_wait=1)
            #
            # # 범위 : 동아일보 클릭 (밑에 항목보다 이 항목이 먼저 실행되어야 함)
            # e = self.get_by_xpath('//*[@id="sub_option"]/div/ul[2]/li[3]/a')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)

            # # 웹동아일보 더보기 클릭
            # try:
            #     e = self.get_by_xpath('//*[@id="content"]/div[3]/div/p')
            # except:
            #     pass
            # else:
            #     self.safe_click(e)
            #     self.implicitly_wait(after_wait=1)

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
    with DongaSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'donga.yaml'
    do_start(config_f=_config_f)
