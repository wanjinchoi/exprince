"""
====================================
 :mod:`board/clien`
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
#  * [2024/10/14]
#     -  게시글 작성일자 xpath가 변경되어 수정
#  * [2024/08/08]
#     -  게시글 전체 캡쳐 시 게시글(제목, 내용, 댓글) 외 불필요한 이미지 제외. HTML에서 제거
#  * [2024/03/20]
#     -  에러 코드 세분화
#     -  에러 로그 세분화
#  * [2023/04/14]
#     - 게시글 목록 xpath 수정
#  * [2023/02/13]
#     - num_comments 저장하는 부분 수정
#  * [2022/10/20]
#     - 삭제된 게시글 회피 로직 추가
#  * [2022/03/22]
#     - 포맷적용
#  * [2021/12/20]
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
from alabslib.selenium import PySelenium
from PIL import Image
from io import BytesIO
################################################################################

class CLIENSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'CLIENSearch.log'),
                            logsize=1024 * 1024 * 10)
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
        self.logger.info(f'Starting CLIEN Crawaling... with '
                         f'config:\n{out_config}')

    # ========================================================================
    def remove_html(self):
        try:
            # 파워 링크
            power_link = self.get_by_xpath("//div[@class='view_button_area']")
            # 게시글 목록 리스트
            article_list = self.get_by_xpath('//div[@id="naverAd"]')
            # 하단 광고
            btm_area = self.get_by_xpath('//div[@class="viewListArea"]')
            # footer
            # ft = self.get_by_xpath('//div[@class="footer_inner"]')

            # HTML 제거
            self.driver.execute_script("arguments[0].remove();", power_link)
            self.driver.execute_script("arguments[0].remove();", article_list)
            self.driver.execute_script("arguments[0].remove();", btm_area)
            # self.driver.execute_script("arguments[0].remove();", ft)

        except Exception as err:
            self.logger.error(f'스크린샷 제거 대상의 UI 변경')
            pass
    # ==========================================================================

    def _screenshot(self, f):
        self.remove_html()
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        height = self.driver.execute_script('return document.body.scrollHeight')
        width = self.driver.execute_script('return document.body.scrollWidth')
        self.driver.set_window_size(S('Width') + width / 2, S('Height'))  # May need manual adjustment
        # self.driver.find_element_by_tag_name('body').screenshot(f)
        # self.driver.find_element_by_xpath('//div[@class="article_wrap"]').screenshot(f)
        self.driver.find_element_by_xpath('//div[@class="content_view"]').screenshot(f)

    # ==========================================================================
    def search(self):
        try:
            # 검색어 입력
            e = self.get_by_xpath('//div[@class="search ad_banner"]/input')
            self.send_keys(e, self.config['params']['site']['search'])

            # 검색 단추
            e = self.get_by_xpath('//div[@class="search ad_banner"]/button/span',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
        except Exception as err:
            self.logger.error(f'search: error: {str(err)}')
            raise

    # ==========================================================================
    def get_comment(self, msg):
        try:
            e = self.get_by_xpath('//div[@class="comment ad_banner"]')

            comments = e.find_elements_by_xpath('./div')
            parent_comment_id = ''

            msg['comment_list'] = []
            # 댓글이 없는 경우
            if len(comments) == 0:
                return
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
                # 삭제된 댓글,대댓글 하지만 댓글수에 포함되는 경우도 있음.
                if cmt_e.get_attribute('class') in ['comment_row blocked ', 'comment_row blocked re']:
                    continue

                # 댓글 nickname (이미지인 경우도 있고 text로 안나오는 경우도 있음)
                e = cmt_e.find_element_by_xpath('.//span[@class="contact_name"]/span')
                nickname = e.text.strip()
                if nickname == '':
                    try:
                        e = e.find_element_by_xpath('./img')
                        nickname = e.get_attribute('alt')
                    except:
                        nickname = e.get_attribute('innerHTML').strip()
                cmt['nickname'] = nickname
                self.move_to_element(e)

                # 댓글 공감수
                e = cmt_e.find_element_by_xpath('.//div[@class="comment_content_symph"]/button/strong')
                cmt['like'] = int(e.get_attribute('innerHTML').strip())

                # 댓글 작성자 ip
                e = cmt_e.find_element_by_xpath('.//div[@data-role="comment-time"]|.//div[@dhata-role="comment-time"]')
                # cmt['contents_ip'] = e.text.strip()

                # 댓글 작성 시간
                e = e.find_element_by_xpath('./span')
                cmt['create_ts'] = e.get_attribute('innerHTML').strip().replace("-", '.').partition(' / ')[0].strip()

                # 댓글 내용 1
                e = cmt_e.find_element_by_xpath('.//div[@class="comment_content"]/div')
                cmt['contents'] = e.text.strip()

                # 댓글 아이디
                cmt['comment_id'] = cmt_e.get_attribute('data-comment-sn')

                # 대댓글인지 확인
                is_reply = cmt_e.get_attribute('class') != "comment_row  "
                cmt['is_reply'] = is_reply
                if not is_reply:
                    parent_comment_id = cmt['comment_id']
                    cmt['parent_comment_id'] = ""
                else:
                    cmt['parent_comment_id'] = parent_comment_id

                # 댓글 이미지
                inner_html = cmt_e.get_attribute('innerHTML')
                cmt['comment_img_url'] = []
                cmt['comment_img'] = []
                if inner_html.find('comment-img') > 0:
                    re_img = cmt_e.find_element_by_xpath('.//div[@class="comment-img"]/img')
                    cmt['comment_img_url'].append(re_img.get_attribute('src'))   # src가 이미지 주소
                    cmt['comment_img'].append(f'{cmt["comment_id"]+"_0"}.png')

                # 댓글 목록에 추가
                msg['comment_list'].append(cmt)
                self.logger.info(f'   [{len(msg["comment_list"])}/{msg["num_comments"]}]: {cmt["comment_id"]}')
        finally:
            self.switch_to_window(1)

        # ========================================================================

    def get_article(self, msg, ndx):
        try:
            self.logger.info(f'Page[{self.cur_page}:{ndx}],article_id[{msg["article_id"]}],title="{msg["title"]}"')
            # article 마다 delay.article.min ~ delay.article.max 사이에 멈춤
            delay_a = random.uniform(
                self.config['params']['site']['delay']['article']['min'],
                self.config['params']['site']['delay']['article']['max'],
            )
            time.sleep(delay_a)

            content_e = self.get_by_xpath('//div[@class="content_view"]')
            # 커뮤니티 이름
            e = content_e.find_element_by_xpath('.//div[@class="board_name"]/h2/a')
            msg['board_name'] = e.text.strip()
            # 작성자
            e = content_e.find_element_by_xpath('.//div[@class="post_info"]/div/span/span[@class="nickname"]')
            author = e.text.strip()
            if author == '':
                e = content_e.find_element_by_xpath('.//div[@class="post_info"]/div/span/span[@class="nickname"]/img')
                author = e.get_attribute('alt').strip()
            msg['author'] = author

            # 작성일시
            e = content_e.find_element_by_xpath('.//div[@class="post_author"]/span[2]')
            if "-" in e.text.partition('수정일')[0].strip():
                msg['create_ts'] = e.text.partition('수정일')[0].strip().replace("-", ".")
            else:
                e = content_e.find_element_by_xpath('.//div[@class="post_author"]/span[1]')
                msg['create_ts'] = e.text.partition('수정일')[0].strip().replace("-", ".")
            # 작성자 ip
            # e = content_e.find_element_by_xpath('//div[@class="post_author"]/span[2]')
            # msg['author_ip'] = e.text.strip()

            # 게시글 공감수
            e = content_e.find_element_by_xpath('.//a[@class="symph_count"]|.//a[@class="symph_count disable"]')
            msg['like'] = int(re.sub(r'[^0-9]', '', e.text.strip()))

            # 조회수
            e = content_e.find_element_by_xpath('.//span[@class="view_count"]/strong')
            msg['view_count'] = int(e.text.strip().replace(',', ''))
            # 게시글에 달린 댓글수
            e = content_e.find_element_by_xpath(
                './/div[@class="comment_head"]/a/strong|.//div[@class="comment_head"]/span/strong')
            msg['num_comments'] = int(e.text.strip())
            # e = self.get_by_xpath('//div[@class="comment_head"]/span/strong')
            # msg['num_comments'] = int(e.text.strip())
            # 게시글 내용
            e = content_e.find_element_by_xpath('//div[@class="post_content"]')
            # 여기에서 일반 글은 p, 표는 table로 나온다 그래서 table을 가지고 오지 못함.
            msg['contents'] = e.text.strip()

            inner_html = e.get_attribute('innerHTML')
            # 이미지 주소 가져오기
            msg['image_list'] = []
            msg['image_url_list'] = []
            if inner_html.find('data-role="attach-image"') > 0:
                for j, sub_e in enumerate(e.find_elements_by_xpath('.//img[@data-role="attach-image"]')):
                    sub_e_url = sub_e.get_attribute('src')
                    msg['image_url_list'].append(sub_e_url)
            # 캡쳐
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], msg['article_id'],
                                                   f'{msg["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot(msg_capture_f)

            # 댓글창이 누르면 늘어남 (단축키 'r')
            while True:
                e = self.get_by_xpath('//div[@data-role="comment-link"]/button[@class="comment_more"]/em')
                cmt_count = e.text.partition(' / ')
                self.move_to_element(e)
                if cmt_count[0] == cmt_count[2]:
                    break
                else:
                    self.send_keys(e, 'r')
                    self.implicitly_wait(after_wait=1)

            self.get_comment(msg)
            # 삭제된 댓글중에 댓글수에 카운트 되는 경우가 있음. (사이트 오류)
            msg['num_comments'] = len(msg['comment_list'])

        except Exception as err:
            self.logger.error(f'get_article: error: {str(err)}')
            raise
        finally:
            # 이전 페이지
            self.driver.back()
            self.implicitly_wait(after_wait=2)
            try:
                self.switch_to_window(0)
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
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_window(1)
            # 페이지 테이블 구해오기
            e = self.get_by_xpath('//div[@class="contents_jirum total_search"]')
            es = e.find_elements_by_xpath('./div')

            # 한번 게시a9556글로 갔다가 되돌아 오면 다음의 tr 태그가 attach 안되어 있다고 나와서
            # 매번 다시 구하도록 함
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
                    e = self.get_by_xpath('//div[@class="contents_jirum total_search"]')
                    es = e.find_elements_by_xpath('./div')
                    ea = es[i]

                    # 삭제된 게시글 넘어가도록
                    if ea.text == '관리자 삭제된 게시물입니다.':
                        continue
                    # 1) 게시글id : article_id  300143_55268553
                    e_url = ea.find_element_by_xpath('.//span[@class="list_subject"]/a[@href]')
                    a_url = e_url.get_attribute('href')
                    v = a_url.partition('?combine')[0].partition('/board/')[2].partition('/')
                    id = v[2] + '_' + v[0]
                    msg['article_id'] = id
                    # 2) 게시글 주소: article_url
                    msg['article_url'] = a_url
                    # 3) 제목: title
                    e = ea.find_element_by_xpath('.//span[@class="list_subject"]/a')
                    msg['title'] = e.text.strip()
                    # 4) 게시판 이름: board_name
                    e = ea.find_element_by_xpath('.//span[@class="list_subject"]/button')
                    msg['board_name'] = e.text.strip()
                    self.move_to_element(e)
                    # 가끔 e_url의 빈공간을 누르기에 클릭을 제대로 못 해서 에러가 나는 경우가 있다.
                    # click의 에러가 난다면 이 이유 때문이다.
                    # e_url 말고 클릭할 수 있는 xpath가 없다
                    self.safe_click(e_url)
                    self.implicitly_wait(after_wait=5)
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
            self.logger.error(f'get_page: error: {str(err)}')
            raise
        finally:
            self.switch_from_iframe()

    # ==========================================================================
    def next_page(self):
        try:
            # np = self.cur_page + 1
            # "카페 메인 (cafe_main)" iFrame으로 이동
            self.switch_to_window(0)
            # 페이지 목록
            # 패스가 변한다. # 현 2번째 바꾸는 중 [03/18]
            e = self.get_by_xpath('//div[@class="nav_container"]')
            ple = e.find_element_by_xpath('.//div[@class="board-pagination"]/div')
            self.move_to_element(ple)
            is_on = False
            for pa in ple.find_elements_by_xpath('.//a'):
                if pa.get_attribute('class') == 'board-nav-page active':
                    is_on = True
                    continue
                if is_on or pa.get_attribute('class') == 'board-nav-next':
                    self.safe_click(pa)
                    self.implicitly_wait()
                    return
            self.is_done = True
        except Exception as err:
            self.logger.error(f'next_page: error: {str(err)}')
            raise
        finally:
            self.switch_from_iframe()

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
            if not('comment_img' in cmt and cmt['comment_img']):
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
            return 1
        finally:
            print(self.output['latest_create_article_ts'])
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    try:
        with CLIENSearch(kwargs['config_f']) as ws:
            ws.start()
    except Exception as err:
        print(err)
        return 11


################################################################################
if __name__ == '__main__':
    _config_f = 'clien.yaml'
    do_start(config_f=_config_f)
