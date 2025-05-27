"""
====================================
 :mod:`news/news_naver`
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
#  * [2023/01/05] 이용석
#     - 게시글 등록시간 12시에 시간 -12하도록 수정
#  * [2022/12/06] sebin
#     - 로그 메세지에 게시글 url 추가
#  * [2022/10/31] sebin
#     - 윈도우창 개수 확인하는 로직 수정
#  * [2022/10/27] sebin
#     - 윈도우창 개수 확인하는 로직 추가
#  * [2022/10/13] sebin
#     - 게시글 url 형식변경으로 인한 article_id 수정
#  * [2022/06/17] Kyobong
#     - 게시글 url 형식변경으로 인한 article_id 수정
#     - search_complex 추가
#  * [2022/05/13] Kyobong
#     - 감정수 신규 추가 10개(warm,cheer,congrats,expect,surprise,fan,useful,wow,touched,analytical)
#  * [2022/04/27] Kyobong
#     - xpath가 다른 게시글이 존재. 추가 완료
#  * [2022/04/21] Kyobong
#     - 상단바 제거
#  * [2022/02/17] MinJung
#     - news/entertain/sports 별로 본문 내용 읽는 xpath 변경.
#  * [2022/02/14] MinJung
#     - msg_capture_f의 f'{msg["article_id"]}.png' 변경.
#     - 각 게시글 별로 json 파일 이름을 article_id로 변경.
#      - get_comments 부분 댓글과 대댓글 따로 수집이 아닌 이어서 수집하게 변경.
#  * [2022/02/11] MinJung
#     - from alabslib.selenium import PySelenium 로 변경.
#     - def start 부분 finally 밑에 print 부분 추가. 첫 수집한 게시글의 작성 시간을 'latest_create_article_ts'에 추가되는 로직.
#     - def __init__ 부분의 for output 변경.
#     - def get_page에서 news = {} 의 내용 추가.
#     - def save_image 추가 및 def save_article 안에 있던 save_image 삭제.
#     - def start 부분 return 0 추가.
#     - news_naver.yaml 내용 수정. news 를 article이나 articles로 변경. site: site_name: 등등 추가.
#     - mapping table에 맞춰서 이름 수정.
#     - create_ts를 0000.00.00 00:00:00 형식대로 변경.
#     - 댓글과 대댓글을 나눠서 수집한 것을 모두 댓글로 합쳐서 수집.
#  * [2021/12/27]
#     - 댓글 늘어나면서 잘못되는 동적 내용 구해오기
#  * [2021/12/20]
#     - starting

################################################################################
import os
import sys
import yaml
import json
import time
import shutil
import random
import re
import tarfile
import datetime
import traceback
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################
class NaverNewsSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'NaverNewsSearch.log'),
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
        self.logger.info(f'Starting Naver News Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def search(self):
        # 우상 "검색" 아이콘 클릭
        e = self.get_by_xpath('//div[@class="Ngnb_tool"]/a',
                              cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 검색어 입력
        # e = self.get_by_xpath('//input[@name="msearch"]')
        e = self.get_by_xpath('//input[@type="search"]')
        if 'search_complex' in self.config['params']['site']:
            self.send_keys(e, f'"{self.config["params"]["site"]["search"]}"')
        else:
            self.send_keys(e, self.config['params']['site']['search'])

        # 검색 단추
        e = self.get_by_xpath('//button[@type="submit"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

        # "최신순" 으로 정렬 : //*[@id="snb"]/div[1]/div/div[1]
        # e = self.get_by_xpath('//*[@id="snb"]/div[1]/div/div[1]')
        # ae = e.find_elements_by_xpath('.//a[@role="option"]')

        self.switch_to_window(1)
        e = self.get_by_xpath('(.//div[@class="option_area type_sort"]/a[@role="option"])[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

    # ==========================================================================
    def get_comments(self, news):
        global comment_count, i
        try:
            self.logger.debug(f'Starting Comment processing')
            comment_count = {}
            # 전체 댓글 개수
            # e = self.get_by_xpath('//span[@class="u_cbox_count"]')
            # comment_count['total'] = int(e.text.strip().replace(',',''))
            # 현재 댓글 개수
            e = self.get_by_xpath('(//ul[@class="u_cbox_comment_count u_cbox_comment_count3"]/li/span)[1]')
            comment_count = int(e.text.strip().replace(',', ''))
            # comment_count['valid'] = int(e.text.strip().replace(',',''))
            # 작성자 삭제 댓글 개수
            # e = self.get_by_xpath('(//ul[@class="u_cbox_comment_count u_cbox_comment_count3"]/li/span)[2]')
            # comment_count['deleted'] = int(e.text.strip().replace(',',''))
            # 규정 미준수 댓글 개수
            # e = self.get_by_xpath('(//ul[@class="u_cbox_comment_count u_cbox_comment_count3"]/li/span)[3]')
            # comment_count['clean_bot'] = int(e.text.strip().replace(',',''))

            if comment_count < 0:
                return

            news['comment_list'] = []
            # # (남자,여자), (연령)별 비율 차트가 있는 경우
            # ratio_percent = {}
            # try:
            #     # 남자,여자 차트
            #     ct_e = self.get_by_xpath('//div[@class="u_cbox_chart_sex"]', timeout=1)
            #     # 댓글 남자 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[1]')
            #     ratio_percent['male'] = int(e.text.strip()[:-1])
            #     # 댓글 여자 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[2]')
            #     ratio_percent['female'] = int(e.text.strip()[:-1])
            #     # 연령별 차트
            #     ct_e = self.get_by_xpath('//div[@class="u_cbox_chart_age"]')
            #     # 10대 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[1]')
            #     ratio_percent['gen_10'] = int(e.text.strip()[:-1])
            #     # 20대 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[2]')
            #     ratio_percent['gen_20'] = int(e.text.strip()[:-1])
            #     # 30대 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[3]')
            #     ratio_percent['gen_30'] = int(e.text.strip()[:-1])
            #     # 40대 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[4]')
            #     ratio_percent['gen_40'] = int(e.text.strip()[:-1])
            #     # 50대 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[5]')
            #     ratio_percent['gen_50'] = int(e.text.strip()[:-1])
            #     # 60대 이상 비율
            #     e = ct_e.find_element_by_xpath('(.//span[@class="u_cbox_chart_per"])[6]')
            #     ratio_percent['gen_60'] = int(e.text.strip()[:-1])
            # except:
            #     pass
            # finally:
            #     if ratio_percent:
            #         self.logger.debug(f'Ratio Percent = {ratio_percent}')
            #     news['comment_ratio_percent'] = ratio_percent

            # 댓글 수집
            offset = 0
            rr_count = 0
            c_es = self.driver.find_elements_by_xpath('//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li')

            for i in range(offset, len(c_es)):
                c_e = self.get_by_xpath(f'(//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li)[{i+1}]',
                                        cond="visibility_of_element_located",
                                        move_to_element=True)
                # self.move_to_element(c_e)
                inner_html = c_e.get_attribute('innerHTML')
                comment = {
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
                    # 댓글 id : comment_id
                    try:
                        e = c_e.find_element_by_xpath('.//button[@class="u_cbox_btn_totalcomment"]')
                        c_id = e.get_attribute('data-param').split(',')
                        c_id_2 = re.sub('[^(0-9)]', '', c_id[2])
                        comment['comment_id'] = c_id_2
                    except:
                        self.logger.debug('Delete or Clean bot or Non-compliance comment')
                        raise
                    # 대댓글 false 설정
                    comment['is_reply'] = False
                    # 부모 댓글의 id
                    # comment['parent_comment_id'] = ''
                    # 댓글 작성자 프로필 이미지
                    # if inner_html.find('u_cbox_img_profile') >= 0:
                    #     e = c_e.find_element_by_xpath('.//img[@class="u_cbox_img_profile"]')
                    #     comment['profile_img_url'] = e.get_attribute('src')
                    # 작성자 닉네임 (esac****) 뒤에 네자리 **** 처리됨
                    if inner_html.find('u_cbox_nick') < 0:
                        continue
                    e = c_e.find_element_by_xpath('.//span[@class="u_cbox_nick"]')
                    comment['nickname'] = e.text.strip()
                    # 작성 시간 : 2022.01.02 00:00:00
                    if inner_html.find('u_cbox_date') >= 0:
                        e = c_e.find_element_by_xpath('.//span[@class="u_cbox_date"]')
                        r_time = e.get_attribute('data-value')
                        re_time = r_time.replace('-', '.').replace('T', ' ').replace('+0900', '')
                        comment['create_ts'] = re_time
                    # 클린봇이 탐지한 내용인 경우
                    if inner_html.find('u_cbox_cleanbot_contents') > 0:
                        self.logger.debug('Clean bot comment')
                        raise
                    # 삭제된 댓글인지 체크
                    else:
                        e = c_e.find_element_by_xpath('.//span[@class="u_cbox_delete_contents"]')
                        if e.get_attribute('style'):  # 삭제되지 않은 글
                            # 댓글 내용
                            if inner_html.find('u_cbox_contents') >= 0:
                                e = c_e.find_element_by_xpath('.//span[@class="u_cbox_contents"]')
                                comment['contents'] = e.text.strip()
                            # 추천 개수
                            e = c_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_recomm"]')
                            comment['like'] = int(e.text.strip())
                            # 비추천 개수
                            e = c_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_unrecomm"]')
                            comment['dislike'] = int(e.text.strip())
                        else:  # 삭제된 글이나 규정 미준수
                            self.logger.debug('Non-compliance comment')
                            raise
                    # news의 comment_list에 댓글 추가
                    news['comment_list'].append(comment)

                    # 대댓글
                    # reply_list = []
                    try:
                        e = c_e.find_element_by_xpath('.//a[@class="u_cbox_btn_reply"]')
                        rr_str = e.text.strip()
                        if rr_str == '답글0' or rr_str == '답글\n0':
                            self.logger.debug('No reply comments')
                            raise
                        # 대댓글 개수 : 찾아지면 대댓글이 있는 경우임
                        # "댓글 2" 눌러 대댓글 보이게 함
                        # 동적 컨텐츠라 다시 읽음
                        c_e = self.driver.find_element_by_xpath(
                            f'(//div[@class="u_cbox_content_wrap"]/ul[@class="u_cbox_list"]/li)[{i + 1}]')
                        e = c_e.find_element_by_xpath('.//a[@class="u_cbox_btn_reply"]')
                        self.safe_click(e)
                        # 동적으로 늘어남
                        self.implicitly_wait(after_wait=1)
                        rr_count += 1
                        rr_e = self.driver.find_element_by_xpath(f'(.//div[@class="u_cbox_reply_area"])[{i+1}]')
                        # 더보기 여부
                        try:
                            e = rr_e.find_element_by_xpath('.//span[@class="u_cbox_page_more"]')
                            e_txt = e.text
                            if e_txt == "더보기":
                                self.safe_click(e)
                                self.implicitly_wait(e)
                        except:
                            pass
                        # 대댓글 수집
                        for j, rc_e in enumerate(rr_e.find_elements_by_xpath('.//ul[@class="u_cbox_list"]/li')):
                            self.move_to_element(rc_e)
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
                            r_inner_html = rc_e.get_attribute('innerHTML')
                            # 대댓글 id : comment_id
                            try:
                                e = rc_e.find_element_by_xpath('.//button[@class="u_cbox_btn_totalcomment"]')
                                c_id = e.get_attribute('data-param').split(',')
                                c_id_2 = re.sub('[^(0-9)]', '', c_id[2])
                                reply['comment_id'] = c_id_2
                            except:
                                self.logger.debug('Delete or Clean bot or Non-compliance reply comment')
                                raise
                            # 대댓글 설정
                            reply['is_reply'] = True
                            # 부모 댓글의 id
                            reply['parent_comment_id'] = comment['comment_id']
                            # # 댓글 작성자 프로필 이미지
                            # if r_inner_html.find('u_cbox_img_profile') >= 0:
                            #     e = rc_e.find_element_by_xpath('.//img[@class="u_cbox_img_profile"]')
                            #     reply['profile_img_url'] = e.get_attribute('src')
                            # 작성자 닉네임 (esac****) 뒤에 네자리 **** 처리됨
                            if r_inner_html.find('u_cbox_nick') < 0:
                                continue
                            e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_nick"]')
                            reply['nickname'] = e.text.strip()
                            # 작성 시간 : 2021.12.02 00:00:00
                            if r_inner_html.find('u_cbox_date') >= 0:
                                e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_date"]')
                                r_time = e.get_attribute('data-value')
                                re_time = r_time.replace('-', '.').replace('T', ' ').replace('+0900', '')
                                reply['create_ts'] = re_time
                            # 클린봇이 탐지한 내용인 경우
                            if r_inner_html.find('u_cbox_cleanbot_contents') > 0:
                                self.logger.debug('Non-compliance comment')
                                raise
                            else:
                                # 삭제된 댓글인지 체크
                                e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_delete_contents"]')
                                if e.get_attribute('style'):  # 삭제되지 않은 글
                                    # 댓글 내용
                                    if r_inner_html.find('u_cbox_contents') >= 0:
                                        e = rc_e.find_element_by_xpath('.//span[@class="u_cbox_contents"]')
                                        reply['contents'] = e.text.strip()
                                    # 추천 개수
                                    e = rc_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_recomm"]')
                                    reply['like'] = int(e.text.strip())
                                    # 비추천 개수
                                    e = rc_e.find_element_by_xpath('.//em[@class="u_cbox_cnt_unrecomm"]')
                                    reply['dislike'] = int(e.text.strip())
                                else:  # 삭제된 글이나 규정 미준수
                                    self.logger.debug('Non-compliance reply comment')
                                    raise
                            # news의 comment_list에 대댓글 추가
                            news['comment_list'].append(reply)
                        self.logger.info(f'[{i}/{comment_count["total"]}] Comment="{comment["contents"][:80]}"')
                    except Exception as err:
                        pass
                except Exception as err:
                    pass
                finally:
                    pass
                offset = len(news['comment_list'])
        except Exception as err:
            raise
        finally:
            # 이전 페이지
            # self.driver.back()
            if len(news['comment_list']) != comment_count['total']:
                i = i
                pass

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_emotions(self, e_emotions, news):
        try:
            for e_emotion in e_emotions:
                emotion = e_emotion.get_attribute('data-type')
                emotion_count = e_emotion.find_element_by_xpath('./span[2]').get_attribute('innerHTML')
                # 좋아요
                if emotion == 'like':
                    news['good'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 훈훈해요
                elif emotion == 'warm':
                    news['warm'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 슬퍼요
                elif emotion == 'sad':
                    news['sad'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 화나요
                elif emotion == 'angry':
                    news['angry'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 팬이에요
                elif emotion == 'fan':
                    news['fan'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 응원해요
                elif emotion == 'cheer':
                    news['cheer'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 축하해요
                elif emotion == 'congrats':
                    news['congrats'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 기대해요
                elif emotion == 'expect':
                    news['expect'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 놀랐어요
                elif emotion == 'surprise':
                    news['surprise'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 쏠쏠정보
                elif emotion == 'useful':
                    news['useful'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 흥미진진
                elif emotion == 'wow':
                    news['wow'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 공감백배
                elif emotion == 'touched':
                    news['touched'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 분석탁월
                elif emotion == 'analytical':
                    news['analytical'] = int(re.sub(r'([^0-9])', '', emotion_count))
                # 후속기사 원해요, 후속 강추
                elif emotion in ['want', 'recommend']:
                    news['news'] = int(re.sub(r'([^0-9])', '', emotion_count))
        except Exception as err:
            self.logger.error(err)

    # ==========================================================================
    def get_news(self, naver_news_e, news):
        self.safe_click(naver_news_e)
        self.implicitly_wait(after_wait=2)
        # new tab
        self.switch_to_window(2)
        try:
            self.logger.info(f'Page[{news["page"]}:{news["row"]}] title="{news["title"]}"')
            # news 마다 delay.news.min ~ delay.news.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['news']['min'],
                self.config['params']['site']['delay']['news']['max'],
            )
            time.sleep(delay_a)
            if self.config['params']['site']['capture_article']:
                # save capture
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], news['article_id'],
                                                   f'{news["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    e_heads = self.driver.find_elements_by_xpath('//div[@class="lnb_area"]|'
                                                                 '//div[@class="floating_inner"]')
                    for e_head in e_heads:
                        self.driver.execute_script("""
                                                var element = arguments[0];
                                                element.parentNode.removeChild(element);
                                                """, e_head)
                    self.full_screenshot(msg_capture_f)
            # 게시글 수집
            # 현재 페이지 url
            now_url = self.driver.current_url
            # 상위 element 선언 : 뉴스, 스포츠, 엔터 순서
            if "entertain" in now_url:
                enter_e = self.get_by_xpath('//div[@class="end_ct_area"]')
                # 원본 언론사 링크
                # e = enter_e.find_element_by_xpath('.//div[@class="press_logo"]/a')
                # news['press_url'] = e.get_attribute('href')
                # 원본 언론사 이름 및 아이콘 url
                e = enter_e.find_element_by_xpath('.//img')
                # news['press_name'] = e.get_attribute('alt')
                news['site_name'] = e.get_attribute('alt')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는경우도 있음
                try:
                    e = enter_e.find_element_by_xpath('.//div[@class="journalistcard_summary_name"]')
                    news['author'] = e.text.strip()
                except:
                    ...
                # 감정수
                e_emotions = enter_e.find_elements_by_xpath('(.//ul[@class="u_likeit_layer _faceLayer"])[1]/li/a')
                self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    e = enter_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                    like = e.text.strip().replace(',', '')
                    news['like'] = 0 if like == '' else int(like)

                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = enter_e.find_element_by_xpath('.//span[@class="author"]/em')
                create_ts = e.text.strip().replace('오전', 'am').replace('오후', 'pm')
                news['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d. %p %I:%M').strftime(
                    '%Y.%m.%d %H:%M:%S')

                # 기사 원본 URL
                # e = self.get_by_xpath('(//div[@class="sponsor"]/a)[1]')
                # news['press_org_url'] = e.get_attribute('href')
                # 기사 본문
                e = enter_e.find_element_by_xpath('.//div[@class="end_body_wrp"]')
                contents = e.text.strip()
                contents = contents.replace('\n\n', '\n')
                news['contents'] = contents
                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    news['image_url_list'].append(sub_e_url)

            elif "sports" in now_url:
                sports_e = self.get_by_xpath('//div[@class="content"]')
                # 원본 언론사 링크
                # e = sports_e.find_element_by_xpath('.//span[@id="pressLogo"]/a')
                # news['press_url'] = e.get_attribute('href')
                # 원본 언론사 이름 및 아이콘 url
                e = sports_e.find_element_by_xpath('.//img')
                # news['press_name'] = e.get_attribute('alt')
                news['site_name'] = e.get_attribute('alt')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는 경우도 있음
                try:
                    e = sports_e.find_element_by_xpath('.//div[@class="journalistcard_summary_name"]')
                    news['author'] = e.text.strip()
                except:
                    ...
                # 감정수
                e_emotions = sports_e.find_elements_by_xpath('(.//ul[@class="u_likeit_layer _faceLayer"])[1]/li/a')
                self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    e = sports_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                    like = e.text.strip().replace(',', '')
                    news['like'] = 0 if like == '' else int(like)

                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = sports_e.find_element_by_xpath('//div[@class="news_headline"]/div[@class="info"]/span[1]|'
                                                   '//div[@class="media_end_head_info nv_notrans "]//div[@class="media_end_head_info_datestamp_bunch"]//span[1]')
                c_ts = e.text.replace('기사입력', '')
                c_ts = c_ts.split()
                c_ts_0 = c_ts[0].rstrip('.')
                t_ts = c_ts[2].split(':')
                hour = int(t_ts[0])
                if t_ts[0] == '12':
                    hour -= 12
                if c_ts[1] == '오후':
                    hour += 12
                create_ts = f'{c_ts_0} {hour:02}:{t_ts[1]}:00'
                news['create_ts'] = create_ts
                # 기사 원본 URL
                # e = self.get_by_xpath('(//div[@class="sponsor"]/a)[1]')
                # news['press_org_url'] = e.get_attribute('href')
                # 기사 본문
                e = sports_e.find_element_by_xpath('.//div[@class="news_end font1 size3"]')
                contents = e.text.strip()
                contents = contents.replace('\n\n', '\n')
                news['contents'] = contents
                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img')):
                    self.move_to_element(sub_e)
                    sub_e_url = sub_e.get_attribute('src')
                    news['image_url_list'].append(sub_e_url)

            else:
                # 뉴스
                news_e = self.driver.find_element_by_xpath('//div[@id="main_content"]|//div[@class="newsct_wrapper _GRID_TEMPLATE_COLUMN"]|//div[@class="newsct_wrapper _GRID_TEMPLATE_COLUMN _STICKY_CONTENT"]')
                # 원본 언론사 링크
                # e = news_e.find_element_by_xpath('.//div[@class="press_logo"]/a')
                # news['press_url'] = e.get_attribute('href')
                # 원본 언론사 이름 및 아이콘 url
                e = news_e.find_element_by_xpath('.//img')
                # news['press_name'] = e.get_attribute('title')
                news['site_name'] = e.get_attribute('title')
                # news['press_icon_url'] = e.get_attribute('src')

                # 작성자 없는 경우도 있음
                try:
                    e = news_e.find_element_by_xpath('.//div[@class="journalistcard_summary_name"]|'
                                                     './/div[@class="byline"]/p')
                    news['author'] = e.text.strip()
                except:
                    ...

                # 감정수
                e_emotions = news_e.find_elements_by_xpath('(.//ul[@class="u_likeit_layer _faceLayer"])[1]/li/a')
                self.get_emotions(e_emotions, news)

                # 추천수 (새로 바뀐 감정에는 추천수가 없음.)
                if news['useful'] is None:
                    e = news_e.find_element_by_xpath('.//a/em[@class="u_cnt _count"]')
                    like = e.text.strip().replace(',', '')
                    news['like'] = 0 if like == '' else int(like)

                # 기사 입력 시간 : 2022.02.02 00:00:00
                e = news_e.find_element_by_xpath(
                    './/div[@class="sponsor"]/span[@class="t11"]|'
                    './/span[@class="media_end_head_info_datestamp_time _ARTICLE_DATE_TIME"]')
                create_ts = e.text.strip().replace('오전', 'am').replace('오후', 'pm')
                news['create_ts'] = datetime.datetime.strptime(create_ts, '%Y.%m.%d. %p %I:%M').strftime('%Y.%m.%d %H:%M:%S')
                # 기사 원본 URL
                # e = self.get_by_xpath('(//div[@class="sponsor"]/a)[1]')
                # news['press_org_url'] = e.get_attribute('href')
                # 기사 본문
                e = news_e.find_element_by_xpath('.//div[@id="articleBodyContents"]|.//div[@id="newsct_article"]')
                contents = e.text.strip()
                # contents = contents.replace('\n\n', '\n')
                news['contents'] = contents

                # 이미지 주소 가져오기
                news['image_list'] = []
                news['image_url_list'] = []

                try:
                    # 이미지가 없을 수도 있음.
                    for j, sub_e in enumerate(e.find_elements_by_xpath('.//p/img|.//div[@id]/img')):
                        self.move_to_element(sub_e)
                        sub_e_url = sub_e.get_attribute('src')
                        news['image_url_list'].append(sub_e_url)
                # 댓글 : 댓글이 없는 경우 있음
                    # 댓글 개수 확인
                    e = news_e.find_element_by_xpath(
                        './/span[@class="lo_txt"]|.//div[@class="media_end_head_info_variety_cmtcount _COMMENT_HIDE"]')
                    e_txt = e.text
                    try:
                        e_tt = int(re.sub('[^(0-9)]', '', e_txt))
                    except:
                        e_tt = 0
                    news['num_comments'] = e_tt
                    # 만약 댓글이 0개 이상이면
                    if e_tt > 0:
                        # 상단 댓글 (카운트) 누름
                        e = news_e.find_element_by_xpath('.//a[@id="articleTitleCommentCount"]|.//div[@class="media_end_head_info_variety_cmtcount _COMMENT_HIDE"]/a')
                        self.safe_click(e)
                        self.implicitly_wait(after_wait=2)
                        # 상위 element 설정
                        cont_e = self.get_by_xpath('//td[@class="content"]|//div[@id="cbox_module"]', timeout=1)
                        # 클린봇 클릭하기
                        try:
                            e = cont_e.find_element_by_xpath('.//a[@class="u_cbox_cleanbot_setbutton"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=2)
                            # 만약 클린봇이 비활성화 되어있다는 걸 찾으면
                            clean_e = self.get_by_xpath('//div[@class="u_cbox_layer_cleanbot2"]', timeout=1)
                            try:
                                e = clean_e.find_element_by_xpath('.//input[@class="u_cbox_layer_cleanbot2_checkbox"]')
                            # 찾지 못하면 클린봇 설정이 켜졌으니 끄기
                            except:
                                e = clean_e.find_element_by_xpath(
                                    './/input[@class="u_cbox_layer_cleanbot2_checkbox is_checked"]')
                                self.safe_click(e)
                                self.implicitly_wait(after_wait=2)
                            # 클린봇 확인 누르기
                            e = clean_e.find_element_by_xpath('.//button[@class="u_cbox_layer_cleanbot2_extrabtn"]')
                            self.safe_click(e)
                            self.implicitly_wait(after_wait=2)
                        # 한 번 클린봇을 끄면 다시 안 꺼줘도 된다
                        except:
                            pass
                        # 최신순 클릭
                        e = cont_e.find_element_by_xpath('.//a[@data-param="new"]|//a[@data-param="new"]')
                        self.safe_click(e)
                        self.move_to_element(e)
                        self.implicitly_wait(after_wait=2)
                        # 하단의 "더보기" 가 있는 경우
                        try:
                            e = cont_e.find_element_by_xpath('.//span[@class="u_cbox_more_wrap"]'
                                                             '|.//a[@class="u_cbox_btn_view_comment"]')
                            e_txt = e.text
                            while e_txt in "더보기":
                                self.move_to_element(e)
                                self.safe_click(e)
                                self.implicitly_wait(after_wait=2)
                        except:
                            pass

                        # 댓글 수집
                        self.get_comments(news)
                        if len(news['comment_list']) != news['num_comments']:
                            news['num_comments'] = len(news['comment_list'])
                except:
                    pass

        except Exception as err:
            raise
        finally:
            # 이전 페이지
            self.close_tab()
            self.switch_to_window(1)

    # ==========================================================================
    def stop_article_older_than(self, news):
        try:
            create_ts = news['create_ts']
            create_ts = datetime.datetime.strptime(create_ts, '%Y.%m.%d %H:%M:%S')
            old_ts = datetime.datetime.strptime(
                self.config['params']['site']['stop_article_older_than']['datetime'],
                self.config['params']['site']['stop_article_older_than']['format']
            )
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because news create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            return False

    # ==========================================================================
    def get_page(self):
        try:
            self.cur_page += 1
            # 페이지 테이블 구해오기
            for i, n_e in enumerate(self.driver.find_elements_by_xpath('//ul[@class="list_news"]/li')):
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
                    # ----------------------------------------------------------------------
                    'warm': None,
                    'cheer': None,
                    'congrats': None,
                    'expect': None,
                    'surprise': None,
                    'fan': None,
                    'useful': None,
                    'wow': None,
                    'touched': None,
                    'analytical': None,
                    # ----------------------------------------------------------------------
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
                        if len(self.driver.window_handles) == 2:
                            break
                        self.switch_to_window(2)
                        self.driver.close()
                        self.implicitly_wait(after_wait=0.5)
                    self.switch_to_window(1)
                    # 현재 뉴스가 보이도록 이동
                    self.move_to_element(n_e)

                    e = n_e.find_element_by_xpath('.//a[@class="news_tit"]')
                    title = e.get_attribute('title')
                    news['title'] = title

                    # "뉴스1 25분 전 네이버뉴스" 와 같이 네이버뉴스 링크가 있는 것인지 체크
                    try:
                        e = n_e.find_element_by_xpath('.//div[@class="info_group"]')
                        e_str = e.text.strip()
                        if not e_str.endswith('네이버뉴스'):
                            raise Exception('No naver contents')

                        # https://news.naver.com/main/read.naver?mode=LSD&mid=sec&sid1=101&oid=023&aid=0003661894
                        # https://n.news.naver.com/mnews/article/018/0005244644?sid=102
                        e = n_e.find_element_by_xpath('.//div[@class="info_group"]/a[@class="info"]')
                        article_url = e.get_attribute('href')
                        if '&aid=' in article_url:
                            aid = article_url.rpartition('oid=')[2].replace('&aid=', '_')
                        else:
                            aid = article_url.rpartition('/')[2].replace('?sid=', '_')
                        # aid = article_url[article_url.find('&sid=')+5:]
                        # aid = article_url.rpartition('/')[2].replace('?sid=', '_')
                        news['article_url'] = article_url
                        news['article_id'] = aid
                    except:
                        self.logger.info(f'get_page[{self.cur_page}:{i + 1}]:{title} have no naver contents')
                        continue
                    self.get_news(e, news)

                except Exception as err:
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
                if self.config['target']['is_separate_article']:
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
            ple = self.get_by_xpath('//div[@class="sc_page_inner"]')
            is_on = False
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('aria-pressed') == 'true':
                    is_on = True
                    continue
                if is_on:
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
    def save_image(self, news):
        for j, sub_e_url in enumerate(news['image_url_list']):
            try:
                article_img_p = self.get_safe_path(
                    self.config['target']['folder'],
                    news['article_id'],
                    f'{j}.png'
                )
                # 가끔 에러 나는 경우가 있슴
                for count in range(10):
                    try:
                        urllib.request.urlretrieve(sub_e_url, article_img_p)
                        news['image_list'].append(f'{j}.png')
                        break
                    except:
                        self.logger.info(f'save_img: {j}.png : retry{count + 1}')
                        continue
            except Exception as err:
                self.logger.error(f'save_img: {j, sub_e_url}: {str(err)}')

    # ==========================================================================
    def save_news(self, news):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            news['article_id'],
            f'{news["article_id"]}'
        )
        self.save_d(at_js_f, news)

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
    with NaverNewsSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'news_naver.yaml'
    do_start(config_f=_config_f)
