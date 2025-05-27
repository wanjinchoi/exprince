"""
====================================
 :mod:`app/app_store`
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
#  * [2023/05/23] Sebin
#     - 업데이트 내용 xpath 변경
#  * [2023/05/11] Sebin
#     - 등록일/업데이트 날짜 포멧 변경
#  * [2021/06/28] Kyobong
#     - 이미지 제거
#  * [2021/06/23] Kyobong
#     - app 정보 page 캡쳐 파일 이름 변경 메타 json과 동일
#  * [2022/06/07]
#     - 이미지 srcset 변경
#  * [2022/06/03]
#     - 이미지 에러해결코드 삽입.
#  * [2022/01/27]
#     - starting
################################################################################
import os
import re
import sys
import yaml
import json
import shutil
import tarfile
import traceback
import datetime
import urllib.request
from pathlib import Path
from copy import deepcopy
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium


################################################################################

class AppStoreSearch(PySelenium):
    # ==========================================================================
    def __init__(self, config_f):
        if not os.path.exists(config_f):
            raise IOError(f'Cannot read config file "{config_f}"')
        with open(config_f, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        log_d = self.config['target']['log_folder']
        if not os.path.exists(log_d):
            os.makedirs(log_d)
        logger = get_logger(self.get_safe_path(log_d, 'AppStoreSearch.log'),
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
             self.config['params']['site']['site_name'],
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
            }
        }
        self.logger.info(f'Starting App Store Crawaling... with '
                         f'config:\n{out_config}')

    # ==========================================================================
    def _screenshot(self, f):
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll' + X)
        self.driver.set_window_size(S('Width'), S('Height'))  # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot(f)

    # ==========================================================================
    def get_app_info(self):
        msg = {
            'title': self.config['params']['site']['site_name'],
            'article_url': self.config['params']['kwargs']['url'],
            'star_like': None,
            'num_reviews': None,
            'contents': None,
            'version': None,
            'num_download': None,
        }
        try:

            msg['article_id'] = re.sub(r'[^0-9]', '', self.config['params']['kwargs']['url'].rpartition('/')[2])
            # id 출력
            print(msg['article_id'])

            app_e = self.get_by_xpath('//div[@class="animation-wrapper is-visible"]')

            # 등록일 release_date
            e = self.get_by_xpath('//script[@name="schema:software-application"]')
            date = e.get_attribute('outerHTML').partition('datePublished":"')[2].partition('","')[0]
            msg['release_date'] = datetime.datetime.strptime(date, '%Y년 %m월 %d일').strftime('%Y.%m.%d 00:00:00')

            # 개발자(작성자)
            e = app_e.find_element_by_xpath('.//h2[@class="product-header__identity app-header__identity"]')
            msg['author'] = e.text.strip()

            # 앱 본문 (본문 클릭하고 캡처
            e = app_e.find_element_by_xpath('.//div/button[@class="link we-truncate__button"]')
            self.safe_click(e)
            if self.config['params']['site']['capture_article']:
                msg_capture_f = self.get_safe_path(self.config['target']['folder'], f'{self.output["start_ts"]}.png')
                # self.full_screenshot(msg_capture_f)
                self._screenshot(msg_capture_f)
            e = app_e.find_element_by_xpath('.//div[@class="l-row"]/div[@dir]')
            msg['contents'] = e.text.strip()

            # 버전
            e = app_e.find_element_by_xpath('.//p[@class="l-column small-6 medium-12 whats-new__latest__version"]')
            msg['version'] = e.text.strip().replace('버전 ', '')

            # 업데이트 날짜
            e = app_e.find_element_by_xpath('.//div[@class="l-row"]/time')
            date_e = e.get_attribute('aria-label')
            msg['update_date'] = datetime.datetime.strptime(date_e, '%Y년 %m월 %d일').strftime('%Y.%m.%d 00:00:00')

            # 업데이트 내용
            e = app_e.find_element_by_xpath('.//div[@class="we-truncate we-truncate--multi-line we-truncate--interactive "]|.//div[@class="we-truncate we-truncate--multi-line we-truncate--interactive  we-truncate--truncated"]')
            msg['update_contents'] = e.text.strip()

            # 평점 star_like
            e = app_e.find_element_by_xpath('.//span[@class="we-customer-ratings__averages__display"]')
            msg['star_like'] = float(e.text.strip())

            # 전체 리뷰작성수
            e = app_e.find_element_by_xpath('.//div[@class="we-customer-ratings__count small-hide medium-show"]')
            msg['num_reviews'] = self.get_num_from_str(e.text.replace('개의 평가', ''))

            # 이미지 주소
            msg['image_list'] = []
            msg['image_url_list'] = []
            # for j, sub_e in enumerate(app_e.find_elements_by_xpath('.//ul[@class="l-row l-row--peek we-screenshot-viewer__screenshots-list"]/li/picture/source[1]')):
            #     sub_e_url = sub_e.get_attribute('srcset').partition(' ')[0]
            #     msg['image_url_list'].append(sub_e_url)
            # self.save_image(msg)
            self.output['app_info'] = msg
        except Exception as err:
            self.logger.error(str(err))
            raise

    # ==========================================================================
    def get_num_from_str(self, s):
        # s = 1.5만개 or 1.4천회
        _s = s
        try:
            times = 1
            if _s.endswith('천'):
                times = 1000
                _s = _s[:-1]
            elif _s.endswith('만'):
                times = 10000
                _s = _s[:-1]
            f = float(_s)
            f *= times
            return int(f)
        except Exception as err:
            self.logger.error(f'in _get_num_from_str: Cannot parse into int for "{s}"')
            raise

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
    def save_article(self, article):
        at_js_f = self.get_safe_path(
            self.config['target']['folder'],
            article['article_id'],
            article['article_id']
        )
        self.save_d(at_js_f, article)

    # ==========================================================================
    def save(self):
        # self.output['num_articles'] = len(self.output['article_list'])
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
            self.get_app_info()
            return 0
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 9
        finally:
            print(self.config['target']['folder'])
            self.output['end_ts'] = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            if self.config['target']['is_save']:
                self.save()
            self.clean()


################################################################################
def do_start(**kwargs):
    with AppStoreSearch(kwargs['config_f']) as ws:
        ws.start()
        return 0


################################################################################
if __name__ == '__main__':
    _config_f = 'app_store.yaml'
    do_start(config_f=_config_f)
