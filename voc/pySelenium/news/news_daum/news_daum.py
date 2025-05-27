"""
====================================
 :mod:`news/news_daum`
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
# *
#
# Change Log
# --------
#  * [2024/08/01]
#     - 전체 스크린샷에 본문만 포함되도록 수정
#  * [2024/07/29]
#     - 작성자 부분 비어있는 게시글 존재하여 수정
#  * [2024/04/08]
#     - 감정수 로딩 확인(3회)
#     - 감정수 로딩안되면 페이지 새로고침
#  * [2023/11/24]
#     - 뉴스 검색 설정 변경 -> 전체
#     - 최신순 정렬 XPath 수정
#  * [2023/06/26]
#     - 댓글 작성시간 변경 (조금전 --> 방금전)
#  * [2023/06/13]
#     - 기존 댓글이 삭제되고 타임톡이 생성되면서 모듈 수정 작업 진행
#  * [2023/05/30] sebin
#     - 다음 페이지 넘어가는 부분의 로직 수정
#  * [2023/05/26] sebin
#     - 검색 부분 xpath 수정
#  * [2023/04/18] sebin
#     - 스크린샷에 댓글 부분 포함
#  * [2022/12/06] sebin
#     - 로그 메세지에 게시글 url 추가
#  * [2022/11/21]
#     - 사이트 태그 XPath 변경으로 인해 수정
#  * [2022/11/01]
#     - 기사 내용의 밑부분의 불필요한 부분 제외
#  * [2022/10/25]
#     - 댓글의 작성일 xpath 수정
#     - 윈도우 창 개수 확인하는 로직 추가
#  * [2022/10/13]
#     - 사이트 UI 변경으로 인해 수정, 댓글창이 없는 기사들 존재
#  * [2022/9/28]
#     - 사이트 UI 변경으로 인해 수정, time 포멧 수정
#  * [2022/4/26]
#     - 대댓글 작성일자 포맷 변경
#  * [2022/1/10]
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
# import timedelta
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from PIL import Image
from io import BytesIO

################################################################################
class DaumNewsSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'DaumNewsSearch.log'),
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
        self.logger.info(f'Starting Daum News Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        #검색 아이콘 클릭 -> 검색어 입력 -> 검색 단추(엔터 같은 것) -> 뉴스 더보기 -> 최신순

        # 상단 "검색" 아이콘 클릭
        e = self.get_by_xpath('.//input[@id="q"]',
                              cond='element_to_be_clickable', timeout=1)
        self.implicitly_wait(after_wait=2)
        self.safe_click(e)

        # 검색어 입력
        e = self.get_by_xpath('.//input[@id="q"]', timeout=1)
        self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@id="daumBtnSearch"]', timeout=1)
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

        # 최신순
        self.switch_to_window(1)
        e = self.get_by_xpath('//div[@class = "c-option"]//div[1]//div//a[2]', timeout=1)
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

        # 뉴스 검색 설정
        e = self.get_by_xpath('//*[@id="dnsColl"]/div[1]/div[2]/div/button',
                              cond='element_to_be_clickable', timeout=1)
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

        # 전체 선택
        e = self.get_by_xpath('//*[@id="inpAll"]',
                              cond='element_to_be_clickable', timeout=1)
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

    # ===========================================================================
    def get_comments(self, news):
        # 댓글 있는지 확인(뉴스/연예) -> 뉴스면 진행 -> 댓글 개수 수집 -> 댓글 수집 -> 대댓글 여부 확인 -> 대댓글 있으면 진행 -> 대댓글 수집(이름, 시간, 내용) -> 더보기 있는지 확인 -> 더보기 있으면 다시 댓글 수집으로 돌아가서 수집 -> 댓글 총 개수와 일치하는지 확인? -> 일치시 종료

        try:
            self.switch_to_iframe_by_name('timetalkFrame')
            e = self.get_by_xpath('//div[@class="body_timetalk"]//ul/li[1]')
            if e.get_attribute('class') == 'safebot':
                news['num_comments'] = 0
                return
            else:
                news['comment_list'] = []
            # 댓글 수집
            self.logger.debug(f'Starting Comment processing')
            # 기사 본문과 댓글의 상위 element 선언
            d_ce = self.get_by_xpath('//div[@class="body_timetalk"]//ul', timeout=1)
            self.move_to_element(d_ce)
            offset = 0

            # # 만약 완료되지 않았다면
            # while not self.is_done:
                # c_e 댓글 리스트
            c_e = self.driver.find_elements_by_xpath('//div[@class="body_timetalk"]//ul/li')

            for i in range(offset, len(c_e)):
                # 댓글 리스트
                c_e = self.get_by_xpath(f'(//div[@class="body_timetalk"]//ul/li)[{i + 1}]',
                                        cond="visibility_of_element_located",
                                        move_to_element=True)

                self.move_to_element(c_e)
                inner_html = c_e.get_attribute('innerHTML')
                comment = {
                    'comment_id': str(len(news['comment_list'])),
                    'is_reply': False,
                    'parent_comment_id': None,
                    'create_ts': None,
                    'nickname': None,
                    'contents': None,
                    'like': None,
                    'dislike': None,
                    'comment_img': [],
                    'comment_img_url': [],
                }

                # 작성자 닉네임
                if inner_html.find('chat_nick') < 0:
                    continue
                e = c_e.find_element_by_xpath('.//em[@class="chat_nick"]')
                comment['nickname'] = e.text.strip()

                # 작성시각 (2022.01.01 01:22:00) 4분전  # 변경
                if inner_html.find('txt_time') >= 0:
                    # 숫자만
                    e = c_e.find_element_by_xpath('.//span[@class="txt_time"]')
                    com_time = e.text
                    now = datetime.datetime.now()
                    if "방금 전" in com_time:
                        comment['create_ts'] = datetime.datetime.now().strftime('%Y.%m.%d %H:%M:%S')
                        pass
                    else:
                        comment_num = int(re.sub('[^(0-9)]', '', com_time))
                        if "분" in com_time:
                            comment_min = now - datetime.timedelta(minutes=comment_num)
                            comment['create_ts'] = comment_min.strftime('%Y.%m.%d %H:%M:%S')
                            pass
                        elif "시간" in com_time:
                            comment_hour = now - datetime.timedelta(hours=comment_num)
                            comment['create_ts'] = comment_hour.strftime('%Y.%m.%d %H:%M:%S')
                            pass
                        else:
                            create_t = com_time.strip().rpartition('.')
                            comment['create_ts'] = create_t[0].replace(' ','') + create_t[2] + ':00'
                # 댓글 내용
                # comment['contents'] = []
                if inner_html.find('txt_message') >= 0:
                    e = c_e.find_element_by_xpath('.//p[@class="txt_message"]')
                    comment['contents'] = e.text.strip()

                # 추천 개수
                # e = c_e.find_element_by_xpath('(.//span[@class="num_txt"])[1]')
                # comment['like'] = int(e.text.strip())

                # 비추천 개수
                # e = c_e.find_element_by_xpath('(.//span[@class="num_txt"])[2]')
                # comment['dislike'] = int(e.text.strip())

                # # 이모티콘
                # comment['emoticon'] = []
                # if inner_html.find('k_emoticon thumb_append') >= 0:
                #     e = c_e.find_element_by_xpath('.//span[@class="k_emoticon thumb_append"]/img')
                #     cmt_img_f = self.get_safe_path(self.config['target']['folder'], news['article_id'], f'{comment["nickname"]+ "_0"}.png')
                #     comment['emoticon'] = cmt_img_f
                #     e.screenshot(cmt_img_f)
                news['comment_list'].append(comment)

            # 댓글 수
            news['num_comments'] = int(len(news['comment_list']))

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            # self.driver.close()
            if len(news['comment_list']) != news['num_comments']:
                pass

    # ==========================================================================
    def get_news(self, news):

        # new tab
        self.switch_to_window(1)
        try:
            self.logger.info(f'Page[{news["page"]}:{news["row"]}] title="{news["title"]}"')
            # news 마다 delay.news.min ~ delay.news.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['news']['min'],
                self.config['params']['site']['delay']['news']['max'],
            )
            time.sleep(delay_a)
            # 감정수 로딩 3회 확인. 로딩중이면 페이지 새로고침
            for _ in range(3):
                try:
                    load_e = self.get_by_xpath('//span[@class="jsx-2157231875 🎬_count_label"]', timeout=5)
                    break
                except:
                    self.driver.refresh()

            # 화면 캡쳐
            self.driver.set_window_size(1600, 768)
            self.driver.switch_to.default_content()  # iframe 다시 전환
            self.driver.execute_script("window.scrollTo(0, 0)")
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], news['article_id'],
                                                   f'{news["article_id"]}.png')
                e_heads = self.driver.find_elements_by_xpath(
                    '//div[@id="kakaoHead"]|//div[@id="mAside"]|//header[@id="kakaoHead"]')
                for e_head in e_heads:
                    self.driver.execute_script("""
                                                            var element = arguments[0];
                                                            element.parentNode.removeChild(element);
                                                            """, e_head)
                # self.full_screenshot(msg_capture_f)
                self.full_screenshot_article(msg_capture_f)
            head_e = self.get_by_xpath('//div[@class="main-content"]', timeout=1)
            # //div[@data-cloud="pc_article_title_and_util"] 기사 헤드라인

            # 원본 언론사 링크
            # e = head_e.find_element_by_xpath('.//em[@class="info_cp"]/a')
            # news['press_url'] = e.get_attribute('href')

            # 원본 언론사 이름 및 아이콘 url
            # e = self.get_by_xpath('.//a[@class="link_cp"]/img')
            # news['site_name'] = e.get_attribute('alt')
            # news['press_icon_url'] = e.get_attribute('src')

            # 기사 입력 시각 (2022.01.01 01:22:00)
            e = head_e.find_element_by_xpath('.//span[@class="num_date"]')
            c_time = e.text.strip().replace(' ', '', 2).rpartition('.')
            a = datetime.datetime.strptime(c_time[0], "%Y.%m.%d")
            date = a.date().strftime("%Y.%m.%d")
            news['create_ts'] = date + c_time[2] + ':00'

            # 작성자 & 날짜 있는 부분(작성자는 없고 날짜만 있는 케이스 존재하여 수정)
            if len(head_e.find_elements_by_xpath('//div[@class="info_view"]/span[@class="txt_info"]')) == 1:
                if news['create_ts'] is not None:
                    news['author'] = None
                else:
                    e = head_e.find_element_by_xpath('.//div[@class="info_view"]/span[@class="txt_info"][1]')
                    news['author'] = e.text.strip()
            else:
                e = head_e.find_element_by_xpath('.//div[@class="info_view"]/span[@class="txt_info"][1]')
                news['author'] = e.text.strip()

            # 기사 원본 URL
            # news['daum_news_url'] 와 같음

            # 기사 본문
            e = self.get_by_xpath('//*[@id="mArticle"]/div[2]')
            contents = e.text.strip()
            news['contents'] = contents
            inner_html = e.get_attribute('innerHTML')

            # 감정
            e_s = head_e.find_elements_by_xpath('.//span[@class="jsx-2157231875 🎬_count_label"]')
            news['good'] = int(re.sub(r'[^0-9]', '', e_s[0].text))
            news['like'] = int(re.sub(r'[^0-9]', '', e_s[1].text))
            news['great'] = int(re.sub(r'[^0-9]', '', e_s[2].text))
            news['angry'] = int(re.sub(r'[^0-9]', '', e_s[3].text))
            news['sad'] = int(re.sub(r'[^0-9]', '', e_s[4].text))

            # inner_html = e.get_attribute('innerHTML')

            # 이미지 주소 가져오기
            if inner_html.find('thumb_g_article') > 0:
                img_e = e.find_elements_by_xpath('.//img[@class="thumb_g_article"]')
                for j, sub_e in enumerate(img_e):
                    sub_e_url = sub_e.get_attribute('src')
                    news['image_url_list'].append(sub_e_url)

            # 댓글 : 댓글이 없는 경우 있음

            # 기사의 링크에 news가 들어있으면 진행 (없으면 댓글 자체가 없음)
            # e = self.get_by_xpath('//meta[@property="og:url"]', timeout=1)
            # c_link = e.get_attribute('content')
            # if not "news" in c_link:
            #     self.logger.debug('News with comments closed')
            #     return

            try:
                # 타임톡 선택
                e = head_e.find_element_by_xpath('.//div[@class="inner_ttalk"]/a')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            except:
                news['num_comments'] = 0
                return

            # 댓글 수집
            self.get_comments(news)
            if len(news['comment_list']) != news['num_comments']:
                if len(news['comment_list']) == 1:
                    pass
                else:
                    news['num_comments'] = len(news['comment_list'])

        except Exception as err:
            raise

        finally:
            # 이전 페이지
            self.close_tab()
            self.implicitly_wait(after_wait=2)
            self.switch_to_main_window()

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2021.12.28. 오전 9:05' '2022.01.18' '13:21:00'
            create_ts = msg['create_ts']
            create_ts = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format'],
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because news create_ts "{create_ts}"'
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        # 페이지를 이동하며 '다음뉴스'가 존재하면 클릭 없으면 넘어가는 형식임
        try:
            self.switch_to_window(0)
            self.cur_page += 1
            # 페이지 테이블 구해오기
            for i, d_e in enumerate(self.driver.find_elements_by_xpath('//ul[@class="list_news"]/li')):
                news = {
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
                    # 윈도우창 갯수 체크로직
                    for _ in self.driver.window_handles:
                        if len(self.driver.window_handles) == 1:
                            break
                        self.switch_to_window(1)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_main_window()
                    # 현재 뉴스가 보이도록 이동
                    d_es = self.driver.find_elements_by_xpath('//ul[@class="list_news"]/li')
                    d_e = d_es[i]
                    # d_e = d_e.find_element_by_xpath(f'(.//li){[i+1]}')
                    self.move_to_element(d_e)
                    # self.safe_click(d_e)
                    # self.implicitly_wait(after_wait=1)
                    # self.get_article(news, i + 1)

                    # 내부 뉴스 html을 구함
                    # inner_html = d_e.get_attribute('innerHTML')

                    # 기사 제목
                    e = d_e.find_element_by_xpath('./div/a[@class="tit_main fn_tit_u"]')
                    title = e.text
                    news['title'] = title

                    # "뉴스1 25분 전 다음뉴스" 와 같이 다음뉴스 링크가 있는 것인지 체크
                    e = d_e.find_element_by_xpath('.//span[@class="cont_info"]')
                    e_str = e.text.strip().split(' ')
                    news['site_name'] = e_str[0]
                    if not e_str[-1] == '다음뉴스':
                        self.logger.debug(f'get_page[{self.cur_page}:{i + 1}]:{title} have no daum contents')
                        continue

                    # http://v.media.daum.net/v/20220105150343992?f=o
                    e = d_e.find_element_by_xpath('.//span[@class="cont_info"]/a[@class="f_nb"][2]')
                    daum_news_url = e.get_attribute('href')
                    aid = daum_news_url[daum_news_url.find('&aid=')+5:]
                    news['article_url'] = daum_news_url
                    news_id = re.sub('[^(0-9)]', '', aid)
                    news['article_id'] = news_id

                    self.safe_click(e)
                    self.implicitly_wait(after_wait=2)
                    self.get_news(news)

                except Exception as err:
                    if news['article_id'] is None:
                        self.logger.error(f'Cannot find Result!')
                        self.is_done = True
                        break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    news['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{news["error_backtrace"]}')
                    self.logger.error(f'뉴스 url: {news["article_url"]}')
                    self.logger.error(str(err))

                if self.stop_article_older_than(news):
                    if os.path.isdir("/".join([self.config['target']['folder'], news['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], news['article_id']]))
                    self.is_done = True
                    break
                self.save_image(news)
                self.output['article_list'].append(news)
                if self.config['target']['is_separate_news']:
                    self.save_news(news)

                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = news['create_ts']
                if len(self.output['article_list']) >= \
                        self.config['params']['site']['max_articles'] > 0:
                    self.is_done = True
                    break

        except Exception as err:
            raise
        finally:
            pass

    # ==========================================================================
    def next_page(self):
        try:
            # 페이지 목록
            self.switch_to_main_window()
            ple = self.get_by_xpath('//div[@class="compo-paging ty_research"]', timeout=1)
            self.move_to_element(ple)
            is_on = False
            for pa in ple.find_elements_by_xpath(
                    './div[@class="inner_paging"]/em|./div[@class="inner_paging"]/a'):
                if pa.get_attribute('href') == None:
                    is_on = True
                    continue
                if is_on:
                    self.safe_click(pa)
                    self.implicitly_wait(after_wait=2)
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
    def full_screenshot_article(self, output_file):
        xpath ='//div[@class="main-content"]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)

        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size

        # 현재 페이지의 전체 크기와 뷰포트 크기 가져오기
        original_window_size = self.driver.get_window_size()
        original_scroll_position = self.driver.execute_script("return window.pageYOffset;")

        # 페이지의 높이와 뷰포트 높이 가져오기
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")

        # 스크롤 위치와 전체 페이지 높이에 따라 이미지 병합을 위한 리스트 초기화
        images = []
        scroll_position = 0

        # 페이지를 스크롤하면서 스크린샷 찍기
        while scroll_position < page_height:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)  # 페이지가 로드되도록 잠시 대기

            # 스크린샷 찍기
            png = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(png))
            images.append(image)

            # 스크롤 위치를 업데이트
            scroll_position += viewport_height

        # 페이지 원래 상태로 복원
        self.driver.set_window_size(original_window_size['width'], original_window_size['height'])
        self.driver.execute_script(f"window.scrollTo(0, {original_scroll_position});")

        # 이미지 병합
        total_height = len(images) * images[0].height
        merged_image = Image.new('RGB', (images[0].width, total_height))

        current_height = 0
        for image in images:
            merged_image.paste(image, (0, current_height))
            current_height += image.height

        # 원하는 영역만 잘라내기
        left = location['x']
        top = location['y']
        right = left + size['width']
        bottom = top + size['height']

        cropped_image = merged_image.crop((left, top, right, bottom))

        # 최종 이미지 저장
        cropped_image.save(output_file)

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

    # ==========================================================================
    def save_news(self, news):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            news['article_id'],
            news['article_id'],
        )
        self.save_d(at_js_f, news)

    # ==========================================================================
    def save(self):
        self.output['num_articles'] = len(self.output['article_list'])
        if self.config['target']['is_separate_news']:
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
    with DaumNewsSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'news_daum.yaml'
    do_start(config_f=_config_f)
