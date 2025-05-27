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
#  * [2022/05/06]Kyobong
#     - 이미지에서 404에러나는 이미지들이 존재(에러 이미지 혹은 모바일에서만 보임)
#  * [2022/04/14]Kyobong
#     - 게시글 목록을 못찾음. 새탭으로 게시글을 여는 방식 사용.
#     - 이미지 가져올때 403에러 해결코드 __init__ 부분에 추가 함
#  * [2022/03/24]
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
from copy import deepcopy, copy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


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
            while True:
                for c_e in self.driver.find_elements_by_xpath('//ul[@id="cmt_reply"]/li'):
                    delay_c = random.uniform(
                        self.config['params']['site']['delay']['comment']['min'],
                        self.config['params']['site']['delay']['comment']['max'],
                    )
                    time.sleep(delay_c)
                    self.move_to_element(c_e)
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
                    # 삭제된 댓글이 존재 댓글수에는 카운트됨.
                    try:
                        e = c_e.find_element_by_xpath('./dl/dd')
                    except:
                        cmt['contents'] = c_e.text.strip()
                        arc['comment_list'].append(cmt)
                        continue
                    cmt['comment_id'] = e.get_attribute('id').strip()
                    if c_e.get_attribute('class') == 're':
                        cmt['parent_comment_id'] = parent_id
                        cmt['is_reply'] = True
                    else:
                        parent_id = cmt['comment_id']
                        cmt['parent_comment_id'] = ''
                    # 작성자 레벨
                    # e = c_e.find_element_by_xpath('.//img[@class="level"]')
                    # cmt['level'] = e.get_attribute('alt')
                    # 작성자 닉네임
                    e = c_e.find_element_by_xpath('.//span[@class="name"]')
                    cmt['nickname'] = e.text.strip()
                    # 작성일시 04/11 10:01
                    e = c_e.find_element_by_xpath('.//span[@class="date"]')
                    c_datetime = str(datetime.datetime.now().year) + '/' + e.text.strip()
                    cmt['create_ts'] = datetime.datetime.strptime(c_datetime, '%Y/%m/%d %H:%M').strftime('%Y.%m.%d %H:%M:%S')
                    # 추천수
                    e = c_e.find_element_by_xpath('.//dd[@class="fl first"]')
                    cmt['like'] = int(e.text.strip().split()[-1])
                    # 반대수
                    e = c_e.find_element_by_xpath('.//dd[@class="fl last"]')
                    cmt['dislike'] = int(e.text.strip().split()[-1])
                    # 내용
                    e = c_e.find_element_by_xpath('.//dl/dd')
                    cmt['contents'] = e.text.strip()

                    self.logger.info(f'Comment: {len(arc["comment_list"]) + 1}/{arc["num_comments"]}')
                    arc['comment_list'].append(cmt)
                try:
                    p_e = self.get_by_xpath('//div[@class="paginate"]/a[@class="pre"]')
                    self.safe_click(p_e)
                    self.implicitly_wait(after_wait=1)
                except Exception as err:
                    break
        except:
            ...
        finally:
            pass

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

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
            if self.config['params']['site']['capture_article']:
                # save capture
                # e_body = self.get_by_xpath('//body')
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], arc['article_id'],
                                                   f'{arc["article_id"]}.png')
                if self.config['params']['kwargs']['headless']:
                    self._screenshot(msg_capture_f)
                else:
                    self.full_screenshot(msg_capture_f)
            # 제목
            e = self.get_by_xpath('//div[@class="writerProfile"]/dl/dt')
            arc['title'] = e.get_attribute('title')
            # 작성일 : '조회 1,357 | 추천 3 | 2022.01.02 (일) 22:56' 뒤엣부분만
            cnt_e = self.get_by_xpath('//span[@class="countGroup"]')
            create_ts = cnt_e.text.strip()
            create_ts = create_ts.split('|')[-1].strip()
            create_ts = re.sub(r'\([^)]*\)', '', create_ts).replace('  ', ' ') + ':00'
            arc['create_ts'] = create_ts
            # 조회수
            e = cnt_e.find_element_by_xpath('(.//em[@class="txtType"])[1]')
            arc['view_count'] = int(e.text.strip().replace(',', ''))
            # 추천수
            e = cnt_e.find_element_by_xpath('(.//em[@class="txtType"])[2]')
            arc['like'] = int(e.text.strip().replace(',', ''))
            # 댓글수
            e = self.driver.find_element_by_xpath('.//span[@class="comm2"]')
            arc['num_comments'] = int(re.sub(r'[^0-9]', '', e.text.strip()))
            # 작성자 프로파일 이미지
            # e = self.get_by_xpath('//div[@class="writerProfile"]//dd[@class="profileImg"]/img')
            # arc['profile_img_url'] = e.get_attribute('src')
            # # 작성자 정보
            for r_e in self.driver.find_elements_by_xpath('//div[@class="writerProfile"]//dd[@class="proflieInfo"]/ul/li'):
                e = r_e.find_element_by_xpath('.//span[@class="proTit"]')
                title = e.text.strip()
                if title == '글쓴이':
                    # e = r_e.find_element_by_xpath('.//span[@class="proCont"]/img[@class="level"]')
                    # arc['level_img_url'] = e.get_attribute('src')
                    e = r_e.find_element_by_xpath('.//span[@class="proCont"]/a[@class="nickName"]')
                    arc['author'] = e.text.strip()
                    break
                # elif title == '가입일':
                #     e = r_e.find_element_by_xpath('.//span[@class="proCont"]')
                #     arc['join_date'] = e.text.strip()
                # elif title == '활동지수':
                #     e = r_e.find_element_by_xpath('.//span[@class="proCont02"]')
                #     arc['activity'] = e.text.strip()
                # elif title == '작성글':
                #     e = r_e.find_element_by_xpath('(.//em[@class="dtTxtDeco03"]/a)[1]')
                #     arc['num_articles_by_user'] = int(e.text.strip().replace(',', ''))
                #     e = r_e.find_element_by_xpath('(.//em[@class="dtTxtDeco03"]/a)[2]')
                #     arc['num_comments_by_user'] = int(e.text.strip().replace(',', ''))
            # 게시글 내용
            e = self.get_by_xpath('//div[@class="bodyCont"]')
            arc['contents'] = e.text.strip()
            # 이미지 목록
            for k, e in enumerate(self.driver.find_elements_by_xpath('//div[@class="bodyCont"]//img')):
                arc['image_url_list'].append(e.get_attribute('src'))

            # # 추천수
            # e = self.get_by_xpath('//span[@id="tempPublic"]')
            # arc['num_recommend'] = int(e.text.strip())

            # 댓글 정보
            if arc['num_comments'] == 0:
                return
            self.get_comments(arc)
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
            len_li = len(self.driver.find_elements_by_xpath('//div[@class="search_Community"]/ul/li'))
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
                    self.implicitly_wait(after_wait=1)
                    li_es = self.driver.find_elements_by_xpath('//div[@class="search_Community"]/ul/li')
                    li_e = li_es[i]
                    self.move_to_element(li_e)
                    a_e = li_e.find_element_by_xpath('.//a')
                    link_url = a_e.get_attribute('href')
                    article_id = link_url[link_url.find('&No=')+4:]
                    arc['article_url'] = link_url
                    arc['article_id'] = article_id
                    # self.safe_click(a_e)
                    self.driver.execute_script(f"window.open('{link_url}')")
                    self.implicitly_wait(after_wait=1)
                    self.get_article(arc, i+1)
                except Exception as err:
                    # if 'article_id' not in msg:
                    #     self.logger.error(f'Cannot find Result!')
                    #     self.is_done = True
                    #     break
                    _exc_info = sys.exc_info()
                    _out = traceback.format_exception(*_exc_info)
                    del _exc_info
                    arc['error_backtrace'] = "".join(_out)
                    self.logger.error(f'get_page[{self.cur_page}:{i+1}]:{arc["error_backtrace"]}')
                    self.logger.error(str(err))

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
            raise
        finally:
            self.switch_from_iframe()

    # ==========================================================================
    def next_page(self):
        try:
            e = self.get_by_xpath('//div[@class="paginate pt19"]/a[@class="next"]')
            self.safe_click(e)
        except Exception as err:
            self.is_done = True
        finally:
            ...

    # ==========================================================================
    def search(self):
        try:
            # 상단 "커뮤니티" 누름
            e = self.get_by_xpath('//*[@id="bobaeHead"]/div[2]/div/div[1]/ul/li[6]/a',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 검색 아이콘 누름
            e = self.get_by_xpath('//button[@class="square-util btn-search js-btn-srch"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            # 검색어 입력
            e = self.get_by_xpath('//span[@class="inp-srch"]/input[@type="search"]')
            e.send_keys(self.config['params']['site']['search'])
            time.sleep(1)
            e.send_keys(Keys.ENTER)
            self.implicitly_wait(after_wait=2)
        except Exception as err:
            self.logger.error(f'in search: Error: "{str(err)}"')
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
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with BobaeDreamSearch(kwargs['config_f']) as ws:
        ws.start()


################################################################################
if __name__ == '__main__':
    _config_f = 'bobaedream.yaml'
    do_start(config_f=_config_f)
