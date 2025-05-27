"""
====================================
 :mod:`cafe/cafe_daum`
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
#
#  * [2023/07/13]
#     - starting

################################################################################
import os
import sys
import yaml
import pickle
import datetime
import time
import traceback
from pathlib import Path
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium
from user_agent import generate_user_agent


################################################################################
class DaumCafeLogin(PySelenium):
    # ==========================================================================
    def __init__(self, id, pw):
        self.id = id
        self.pw = pw
        self.config = {
            'url': 'https://logins.daum.net/accounts/loginform.do?url=https%3A%2F%2Fcafe.daum.net%2F_c21_%2Fhome%3Fgrpid%3DmEr9&category=cafe&t__nil_navi=login',
            'browser': 'Chrome',
            'width': 1200,
            'height': 800,
        }
        # 컨피그 파일 path로 접근. 파이썬 모듈 실행하는 위치가 다름.
        self.cookie_path = r"C:\work\voc\yaml\카페\다음\cookies.pkl"
        self.log_d = 'C:/work/voc_data/logs/cafe/daum/login_cookie'
        self.c_filepath = self.log_d + f"/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        if not os.path.exists(self.log_d):
            os.makedirs(self.log_d)
        logger = get_logger(self.get_safe_path(self.log_d, 'DaumCafe_cookie.log'),
                            logsize=1024 * 1024 * 10)
        self.config['logger'] = logger
        PySelenium.__init__(self, **self.config)

        self.logger.info(f'Starting Daum Cafe Login... making cookie ')

    # ==========================================================================
    def login(self):
        try:
            # 바로 로그인창이 뜨는 경우가 존재함. http://cafe.daum.net/Tlwkftlqkftlldlqkf
            # 로그인 클릭
            # e = self.get_by_xpath('//a[@id="btnMinidaumLogin"]',
            #                       cond='element_to_be_clickable')
            # self.safe_click(e)
            # self.implicitly_wait(after_wait=1)

            # login 화면

            # 카카오계정으로 로그인
            e = self.get_by_xpath('//a[@class="link_login link_klogin"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)

            # 사용자 입력
            e = self.get_by_xpath(
                '//input[@class="tf_g tf_email"]|//input[@id="id"]|//input[@id="input-loginKey"]|//input[@id="loginKey--1"]|(//div[@class="box_tf"]/input)[1]')
            # self.send_keys_clipboard(e, self.config['params']['site']['userid'])
            self.send_keys(e, self.id)
            time.sleep(1)

            # 암호 입력
            e = self.get_by_xpath(
                '//input[@data-type="password"]|//input[@name="pw"]|//input[@id="input-password"]|//input[@id="password--2"]|(//div[@class="box_tf"]/input)[2]')
            # self.send_keys_clipboard(e, self.config['params']['site']['passwd'])
            self.send_keys(e, self.pw)
            time.sleep(1)

            # 로그인 단추 누름
            e = self.get_by_xpath(
                '//button[@class="btn_g btn_confirm submit"]|//button[@class="btn_g highlight"]|//button[@class="btn_g highlight submit"]',
                cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 쿠키 생성
            pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
            print(0)
        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            raise RuntimeError(f'login Error: {str(e)}')

    # ==========================================================================
    def random_user_agent(self):
        options = webdriver.ChromeOptions()
        options.add_argument("disable-gpu")
        # options.add_argument('--incognito')
        options.add_argument(f'--user-agent={generate_user_agent(device_type="desktop")}')
        options.add_argument('--kiosk-printing')

        self.driver.start_session(options.to_capabilities())
        self.driver.get(self.config['url'])
        time.sleep(2)

    # ==========================================================================
    def clean(self):
        for path in Path(self.log_d).rglob('*.png'):
            cts_ut = os.path.getctime(str(path))
            cts = datetime.datetime.fromtimestamp(cts_ut)
            diff_t = datetime.datetime.now() - cts
            if diff_t.days >= 7:
                os.remove(str(path))

    # ==========================================================================
    def start(self, i=None):
        try:
            # self.random_user_agent()
            self.login()
            self.driver.find_element_by_tag_name('body').screenshot(self.c_filepath)
            return 0

        except Exception as e:
            _exc_info = sys.exc_info()
            _out = traceback.format_exception(*_exc_info)
            del _exc_info
            self.logger.error(''.join(_out))
            self.logger.error(str(e))
            return 1

        finally:
            # 이미지로그 7일만 보관
            self.clean()


################################################################################
def do_start(**kwargs):
    with DaumCafeLogin(kwargs['id'], kwargs['pw']) as ws:
        return ws.start()


################################################################################
def main(**kwargs):
    with DaumCafeLogin(kwargs['id'], kwargs['pw']) as ws:
        return ws.start()


################################################################################
if __name__ == '__main__':
    id = '*******'
    pw = '*******'
    do_start(id=id, pw=pw)
