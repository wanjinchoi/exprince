"""
====================================
 :mod:`board/bobaedream`
====================================
.. moduleauthor:: Jerry Chae <mcchae@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS PySelenium module
"""
# Authors
# ===========
#
# * Jerry Chae
#
# Change Log
# --------
#
#  * [2024/08/08]
#     - 게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. 이미지 자르는 방식
#  * [2024/07/23]
#     - 스크린샷 수집 로직 순서 수정
#  * [2024/03/19]
#     - 댓글 수집 부분 페이지 넘어가는 로직 수정
#  * [2024/03/18]
#     - search 부분의 메뉴 xpath 수정
#     - 에러 코드 세분화(chrome에러:11, 나머지:1)
#     - 검색결과 존재 여부 확인 로직 수정
#     - 스크린샷 순서 수정(게시글 수집 마지막으로)
#  * [2022/12/26]
#     - 삭제된 게시글 회피 로직
#  * [2022/12/06]
#     - 실패할 경우 로그 메세지에 게시글 url
#  * [2022/05/13] Kyobong An
#     - 게시글 제목, 내용 에러 수정
#  * [2022/05/09] Kyobong An
#     - 검색결과가 없는 경우 에러처리.
#  * [2022/05/06] Kyobong An
#     - 모바일 버전으로 변경
#  * [2022/04/14] Kyobong An
#     - 게시글 목록을 못찾음. 새탭으로 게시글을 여는 방식 사용.
#     - 이미지 가져올때 403에러 해결코드 __init__ 부분에 추가 함
#  * [2022/03/24] Kyobong An
#     - 포맷적용
#  * [2021/12/28]
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
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys, webdriver
from PIL import Image
from io import BytesIO

################################################################################
class BobaeDreamSearch(PySelenium):

    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'BobaeDreamSearch.log'),
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
        self.logger.info(f'Starting Bobae Dream Crawaling... with '
                         f'config:\n{out_config}')

    # # ==========================================================================
    # def _get_num_from_str(self, s):
    #     _s = s
    #     try:
    #         _s = _s.split()[-1]
    #         if _s.endswith('개'):
    #             _s = _s[:-1]
    #         else:
    #             return 0
    #         # "21.5만"
    #         times = 1
    #         if _s.endswith('천'):
    #             times = 1000
    #             _s = _s[:-1]
    #         elif _s.endswith('만'):
    #             times = 10000
    #             _s = _s[:-1]
    #         f = float(_s)
    #         f *= times
    #         return int(f)
    #     except Exception as err:
    #         self.logger.error(f'in _get_num_from_str: Cannot parse into int for "{s}"')
    #         raise

    # ==========================================================================
    def get_comments(self, arc):
        try:
            # 댓글 목록 가져오기
            arc['comment_list'] = []
            parent_id = None
            # 댓글 최신순
            c_s = self.driver.find_elements_by_xpath('//div[@class="reply-area"]//ul[@class="box2"]/li/a')
            for t in c_s:
                if t.text.find('최신순') != -1:
                    self.safe_click(t)
                    self.implicitly_wait(after_wait=1)
                    self.switch_to_window(1)
                    break

            while True:
                for c_e in self.driver.find_elements_by_xpath('//div[@class="reply-area"]/div/ul[@class="list"]/li'):
                    delay_c = random.uniform(
                        self.config['params']['site']['delay']['comment']['min'],
                        self.config['params']['site']['delay']['comment']['max'],
                    )
                    time.sleep(delay_c)
                    self.move_to_element(c_e)
                    # 베플은 넘김
                    if c_e.get_attribute('class') == 'best':
                        continue
                    cmt = {
                        'comment_id': None,
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
                    # 별도 id 가 존재하지 않아 일련번호로
                    # cmt['comment_id'] = str(len(arc['comment_list']) + 1)
                    # 내용
                    e = c_e.find_element_by_xpath('.//div[@class ="reply"]|.//div[@class ="reply rere"]')
                    cmt['contents'] = e.text.strip()
                    # 삭제된 댓글이 존재 댓글수에는 카운트됨.
                    try:
                        # 작성자 닉네임
                        e = c_e.find_element_by_xpath('.//div[@class ="util"]/span[1]')
                        cmt['nickname'] = e.text.strip()
                    except:
                        arc['comment_list'].append(cmt)
                        continue
                    cmt['comment_id'] = str(len(arc['comment_list'])+1)
                    e = c_e.find_element_by_xpath('./div')
                    if e.get_attribute('class') == 'ico_area':
                        cmt['parent_comment_id'] = parent_id
                        cmt['is_reply'] = True
                    else:
                        parent_id = cmt['comment_id']
                    # 작성일시 22.05.11 10:01 or 08:01
                    e = c_e.find_element_by_xpath('.//div[@class ="util"]/span[2]')
                    c_datetime = e.text.strip()
                    if len(c_datetime.split(' ')) == 1:
                        today_dt = datetime.datetime.now().strftime('%Y.%m.%d ')
                        c_time = datetime.datetime.strptime(c_datetime, '%H:%M').time().strftime('%H:%M:%S')
                        create_ts = today_dt + c_time
                    else:
                        create_ts = datetime.datetime.strptime(c_datetime, '%y.%m.%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    cmt['create_ts'] = create_ts
                    # 추천수
                    e = c_e.find_element_by_xpath('.//div[@class ="util3"]/button[@class="good"]')
                    cmt['like'] = int(e.text.strip().split()[-1])
                    # 반대수
                    e = c_e.find_element_by_xpath('.//div[@class ="util3"]/button[@class="bad"]')
                    cmt['dislike'] = int(e.text.strip().split()[-1])

                    self.logger.info(f'Comment: {len(arc["comment_list"]) + 1}/{arc["num_comments"]}')
                    arc['comment_list'].append(cmt)

                if len(arc['comment_list']) >= arc['num_comments']:
                    break
                try:
                    ps_e = self.driver.find_elements_by_xpath('//div[@class="reply-area"]//div[@class="page"]/span/a')
                    n_page = False
                    for p, p_e in enumerate(ps_e):
                        if p_e.get_attribute('class') == 'on':
                            # 다음페이지로 넘어가야할 경우
                            if p == len(ps_e) + 1:
                                e = self.driver.find_element_by_xpath(
                                        '//div[@class="reply-area"]//div[@class="page"]/a[@class="next"]')
                                self.safe_click(e)
                                self.implicitly_wait(after_wait=1)
                            n_page = True
                        if n_page:
                            self.safe_click(ps_e[p+1])
                            self.implicitly_wait(after_wait=1)
                            break
                except Exception as err:
                    break
        except:
            ...
        finally:
            pass

    # ==========================================================================
    def _screenshot(self, output_file):
        xpath = '/html/body/div[1]/div[2]/article'
        adxpath1 = '//*[@id="reply-area"]'
        # 요소 찾기
        element = self.driver.find_element_by_xpath(xpath)
        element1 = self.driver.find_element_by_xpath(adxpath1)

        # 요소의 위치와 크기 가져오기
        location = element.location
        size = element.size

        location1 = element1.location
        size1 = element1.size

        # 현재 페이지의 크기 가져오기
        original_window_size = self.driver.get_window_size()
        original_scroll_position = self.driver.execute_script("return window.pageYOffset;")

        # 페이지의 높이 가져오기
        page_height = self.driver.execute_script("return document.body.scrollHeight")
        viewport_height = self.driver.execute_script("return window.innerHeight")

        # 리스트 초기화
        images = []
        scroll_position = 0

        # 페이지를 스크롤하면서 스크린샷 찍기
        while scroll_position < page_height:
            self.driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(1)

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

        left1 = location1['x']
        top1 = location1['y']
        right1 = left1 + size1['width']
        bottom1 = top1 + size1['height']

        cropped_image1 = merged_image.crop((left, top, right, bottom))
        cropped_image2 = merged_image.crop((left1, top1, right1, bottom1))

        total_width = max(cropped_image1.width, cropped_image2.width)
        total_height = cropped_image1.height + cropped_image2.height
        merged_image = Image.new('RGB', (total_width, total_height))

        merged_image.paste(cropped_image1, (0, 0))
        merged_image.paste(cropped_image2, (0, cropped_image1.height))

        merged_image.save(output_file)


    # ==========================================================================
    def get_article(self, arc, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{arc["article_id"]}]')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)
            self.switch_to_window(1)
            a_e = self.get_by_xpath('//article[@class="article"]')
            # 제목
            e = a_e.find_element_by_xpath('.//h3[@class="subject"]')
            arc['title'] = e.text.strip()
            # 작성일 : '조회 1,357 | 추천 3 | 2022.01.02 (일) 22:56' 뒤엣부분만
            cnt_e = a_e.find_element_by_xpath('//time')
            c_date = cnt_e.get_attribute('datetime').replace('-', '.')
            c_time = cnt_e.text.split('  ')[-1] + ':00'
            create_ts = c_date + ' ' + c_time
            arc['create_ts'] = create_ts
            # 조회수
            e = a_e.find_element_by_xpath('.//span[@class="data4"]')
            arc['view_count'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 추천수
            e = a_e.find_element_by_xpath('.//span[@class="data3"]')
            arc['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 댓글수
            e = self.driver.find_element_by_xpath('.//div[@class="reply-area"]//span[@class="data1"]')
            arc['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 작성자 정보
            e = a_e.find_element_by_xpath('.//div[@class="info"]/span')
            arc['author'] = e.text.strip()
            # 게시글 내용
            e_c = a_e.find_element_by_xpath('.//div[@class="article-body"]')
            arc['contents'] = e_c.text.strip()
            # 이미지 목록
            for k, e in enumerate(e_c.find_elements_by_xpath('.//p/img')):
                arc['image_url_list'].append(e.get_attribute('src'))

            # # 추천수
            # e = self.get_by_xpath('//span[@id="tempPublic"]')
            # arc['num_recommend'] = int(e.text.strip())

            # 댓글 정보
            if arc['num_comments'] == 0:
                pass
            else:
                self.get_comments(arc)
            if self.config['params']['site']['capture_article']:
                self.driver.execute_script('window.scrollTo(0,0)')
                self.implicitly_wait(after_wait=1)
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], arc['article_id'],
                                                   f'{arc["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self._screenshot(msg_capture_f)
        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # self.driver.back()
            self.driver.close()
            self.implicitly_wait(after_wait=2)
            self.switch_to_main_window()

    # ==========================================================================
    def stop_article_older_than(self, msg):
        try:
            # '2022.01.02 22:56'
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
            len_li = len(self.driver.find_elements_by_xpath('//ul[@class="imgList01"]/li'))
            if len_li == 1:
                e = self.get_by_xpath('//ul[@class="imgList01"]/li[1]//em[@class="title"]')
                if '검색 결과' in e.text.strip():
                    self.logger.error(f'Cannot find Result!')
                    self.is_done = True
                    return
            for i in range(len_li):
                arc = {
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
                    self.implicitly_wait(after_wait=1)
                    li_es = self.driver.find_elements_by_xpath('//ul[@class="imgList01"]/li')
                    li_e = li_es[i]
                    self.move_to_element(li_e)
                    a_e = li_e.find_element_by_xpath('./a')
                    innerhtml = a_e.get_attribute('innerHTML')
                    # 검색결과 없는경우.
                    if innerhtml.find('검색 결과가 없습니다.') > 0:
                        raise Exception
                    link_url = a_e.get_attribute('href')
                    article_id = link_url[link_url.find('view/')+4:].replace('/', '_')
                    arc['article_url'] = link_url
                    arc['article_id'] = article_id
                    # 제목: title
                    e = a_e.find_element_by_xpath('.//em[@class="title"]')
                    arc['title'] = e.text.strip()
                    a = e.text.strip()
                    out_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", a)
                    # self.safe_click(a_e)
                    self.driver.execute_script(f"window.open('{link_url}')")
                    self.implicitly_wait(after_wait=1)
                    try:
                        # 비공개글 회피로직
                        self.switch_to_window(1)
                        self.implicitly_wait(after_wait=2)
                        # self.switch_to_iframe_by_name('cafe_main')//div[@class="content community"]
                        self.get_by_xpath('//div[@class="content community"]')
                        # 게시글 제목 비교 띄어쓰기가 단락으로 인해 차이가 있을 수 있음
                        e = self.driver.find_element_by_xpath('//div[@class="title"]//h3').text.strip()
                        in_title = re.sub(r'[^ㄱ-ㅣ가-힣\w\s\d]', " ", e)
                        if not in_title.replace(' ', '').startswith(out_title.replace(' ', '')[:-3]):
                            self.logger.debug('비공개 게시글입니다.')
                            self.logger.debug(f'게시글의 url: {arc["article_url"]}')
                            self.logger.debug(f'게시글의 title: {arc["title"]}')
                            for _ in self.driver.window_handles:
                                if len(self.driver.window_handles) == 1:
                                    break
                                self.switch_to_window(1)
                                self.driver.close()
                            self.switch_to_main_window()
                            self.implicitly_wait(after_wait=1)
                            continue
                    except:
                        self.logger.debug('삭제된 게시글입니다.')
                        self.logger.debug(f'게시글의 url: {arc["article_url"]}')
                        self.logger.debug(f'게시글의 title: {arc["title"]}')
                        for _ in self.driver.window_handles:
                            if len(self.driver.window_handles) == 1:
                                break
                            self.switch_to_window(1)
                            self.driver.close()
                        self.switch_to_main_window()
                        self.implicitly_wait(after_wait=1)
                        continue
                    self.get_article(arc, i+1)
                except Exception as err:
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    arc['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{arc["error_backtrace"]}')
                    self.logger.error(f'게시글의 url: {arc["article_url"]}')
                    self.logger.error(str(err))
                    raise

                if self.stop_article_older_than(arc):
                    if os.path.isdir("/".join([self.config['target']['folder'], arc['article_id']])):
                        shutil.rmtree("/".join([self.config['target']['folder'], arc['article_id']]))
                    self.is_done = True
                    break
                self.save_image(arc)
                self.output['article_list'].append(arc)
                if self.config['target']['is_separate_article']:
                    self.save_article(arc)
                # 첫번째로 크롤링한 게시글의 작성시간을 저장
                if self.output["latest_create_article_ts"] is None:
                    self.output["latest_create_article_ts"] = arc['create_ts']
                if len(self.output['article_list']) >= \
                        self.config['params']['site']['max_articles'] > 0:
                    self.is_done = True
                    break
        except Exception as err:
            self.logger.error(f'get_page: error: {str(err)}')
            raise
        finally:
            self.switch_from_iframe()

    # ==========================================================================
    def next_page(self):
        try:
            p_t = self.driver.find_elements_by_xpath('//div[@class="paginate"]/span/a')
            e = self.get_by_xpath('//div[@class="paginate"]/span/strong')
            for p in p_t:
                if int(p.text.strip()) > int(e.text.strip()):
                    self.safe_click(p)
                    self.implicitly_wait(after_wait=1)
                    return
            e = self.get_by_xpath('//div[@class="paginate"]/a/img[@alt="다음 목록 보기"]', timeout=1)
            self.safe_click(e)
        except Exception as err:
            self.is_done = True
        finally:
            ...

    # ==========================================================================
    def search(self):
        try:
            # 상단 검색아이콘 누름
            e = self.get_by_xpath('//button[@class="btn-search js-btn-srch"]')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 검색어 입력
            e = self.get_by_xpath('//input[@type="search"]')
            e.send_keys(self.config['params']['site']['search'])
            time.sleep(1)
            e.send_keys(Keys.ENTER)
            self.implicitly_wait(after_wait=2)

            # 커뮤니티 더보기
            try:
                e = self.driver.find_elements_by_xpath('//div[@id="contents"]/ul[@class="Retrieval-tab"]/li//a')
                for i in e:
                    if i.text.strip() == '커뮤니티':
                        self.safe_click(i)
                        self.implicitly_wait(after_wait=1)
                    else:
                        pass
            except:
                ...

        except Exception as err:
            self.logger.error(f'search: Error: "{str(err)}"')
        finally:
            ...

    # ==========================================================================
    def screenshot(self):
        ss_f = self.get_safe_path(
            self.config['target']['folder'],
            f'{self.output["start_ts"]}.png'
        )
        self.full_screenshot(ss_f)

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
    def save_image(self, arc):
        # save image
        for j, sub_e_url in enumerate(arc['image_url_list']):
            try:
                cmt_img_f = self.get_safe_path(
                    self.config['target']['folder'],
                    arc['article_id'],
                    f'{j}.png'
                )
                urllib.request.urlretrieve(sub_e_url, cmt_img_f)
                arc['image_list'].append(f'{j}.png')
            except Exception as err:
                _exc_info = sys.exc_info()
                _out = traceback.format_exception(*_exc_info)
                self.logger.error(''.join(_out))
                self.logger.error(str(err))
                continue

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
    def mobile_mode(self):
        try:
            options = webdriver.ChromeOptions()
            if self.config['params']['kwargs']['headless']:
                options.add_argument('--headless')
            options.add_argument("disable-gpu")
            options.add_argument('--incognito')
            options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1')
            # options.add_argument(f'--user-agent={generate_user_agent(device_type="smartphone")}')
            # options.add_argument('--kiosk-printing')
            self.driver.start_session(options.to_capabilities())
            self.driver.get(self.config['params']['kwargs']['url'])
            time.sleep(5)
        except Exception as err:
            self.logger.error(f'mobile_mode: error: {str(err)}')
            raise

    # ==========================================================================
    def start(self):
        try:
            if self.config['target']['is_clear'] and \
                    os.path.exists(self.config['target']['folder']):
                shutil.rmtree(self.config['target']['folder'])
            self.mobile_mode()
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
            return 1
        finally:
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    try:
        with BobaeDreamSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11

################################################################################
if __name__ == '__main__':
    _config_f = 'bobaedream.yaml'
    do_start(config_f=_config_f)
