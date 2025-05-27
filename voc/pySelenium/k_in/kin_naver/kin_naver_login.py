"""
====================================
 :mod:`cafe/cafe_naver`
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
#  * [2024/06/10]
#     - 지식인용 쿠키 생성 스크립트

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
class NaverCafeLogin(PySelenium):
    # ==========================================================================
    def __init__(self, id, pw):
        self.id = id
        self.pw = pw
        self.config = {
            'url': 'https://kin.naver.com/',
            'browser': 'Chrome',
            'width': 1200,
            'height': 800,
        }
        # 컨피그 파일 path로 접근. 파이썬 모듈 실행하는 위치가 다름.
        self.cookie_path = r"C:\work\voc\yaml\카페\네이버\cookies.pkl"
        self.log_d = 'C:/work/voc_data/logs/cafe/naver/login_cookie'
        self.c_filepath = self.log_d + f"/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.png"
        self.l_filepath = self.log_d + f"/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_로그인 전.png"
        if not os.path.exists(self.log_d):
            os.makedirs(self.log_d)
        logger = get_logger(self.get_safe_path(self.log_d, 'NaverCafe_cookie.log'),
                            logsize=1024*1024*10)
        self.config['logger'] = logger
        PySelenium.__init__(self, **self.config)

        self.logger.info(f'Starting Naver Cafe Login... making cookie ')

    # ==========================================================================
    def login(self):
        try:
            bef_page = self.driver.current_url
            e = self.get_by_xpath('//body')
            inner_html = e.get_attribute('innerHTML')
            # 바로 로그인 되는 경우 처리 : https://cafe.naver.com/jbads
            if inner_html.find('gnb_login_button') > 0:
                # 로그인 클릭
                e = self.get_by_xpath('//*[@id="gnb_login_button"]',
                                      cond='element_to_be_clickable')
                self.safe_click(e)
                self.implicitly_wait(after_wait=1)
            else:
                self.logger.info('login: Directly login page shows up!')

            # login 화면
            #새로고침, 캡쳐 추가
            self.driver.refresh()
            self.driver.find_element_by_tag_name('body').screenshot(self.l_filepath)
            # 사용자 입력
            e = self.get_by_xpath('//*[@id="id"]')
            self.send_keys_clipboard(e, self.id)
            time.sleep(2)

            # 암호 입력
            e = self.get_by_xpath('//*[@id="pw"]')
            self.send_keys_clipboard(e, self.pw)
            time.sleep(2)

            # 로그인 상태유지 클릭
            # e = self.get_by_xpath('//div[@class="keep_check"]/input')
            # if e.get_attribute('value') == 'off':
            #     e = e.find_element_by_xpath('./../label[@for="keep"]')
            #     self.safe_click(e)
            #     self.implicitly_wait(after_wait=1)

            # 로그인 단추 누름
            e = self.get_by_xpath('//*[@id="log.login"]',
                                  cond='element_to_be_clickable')
            self.safe_click(e)
            self.implicitly_wait(after_wait=1)
            # 비밀번호 잘못 입력한 경우
            es = self.driver.find_elements_by_xpath(
                '//div[@id="err_common"]/div[@class="error_message"] ')
            for _ in es:
                print(1)
                return self.logger.error('login Fail: 잘못된 로그인정보 입력')
            # 자동입력 방지 문자 체크 있으면 에러.
            es = self.driver.find_elements_by_xpath(
                '//form[@id="frmNIDLogin"]/ul/li/div/div/span[@class="message_text"]')
            for _ in es:
                print(2)
                return self.logger.error('login Fail: 자동입력 방지 문자')

            # 계정 보호조치
            es = self.driver.find_elements_by_xpath(
                '//div[@id="divWarning"]/span/a[@class="btn"]')
            for e in es:
                if e.get_attribute('innerHTML') == '보호조치 해제':
                    print(4)
                    return self.logger.error('login Fail: 계정보호조치')

            # 동시 접속자 수가 많은 경우
            es = self.driver.find_elements_by_xpath(
                '//body/div[@class="cont_err"]/p[@class="dsc_err2"]')
            for e in es:
                if e.text.strip().startswith('동시에 접속하는 이용자 수가'):
                    print(5)
                    # //body/div/div[@class="btn_area"]/a/img[@alt="새로 고침"]
                    return self.logger.error('login Fail: 동시 접속자 수가 많음')

            # 나머지 에러
            if self.driver.current_url != bef_page:
                print(3)
                return self.logger.error('login Fail: 로그인 실패')

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
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
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
    with NaverCafeLogin(kwargs['id'], kwargs['pw']) as ws:
        return ws.start()


################################################################################
def main(**kwargs):
    with NaverCafeLogin(kwargs['id'], kwargs['pw']) as ws:
        return ws.start()


################################################################################
if __name__ == '__main__':
    id = 'brm00000@naver.com'
    pw = '*******'
    do_start(id=id, pw=pw)