"""
====================================

====================================

Description
===========
NST 전산 자동화
"""
# Authors
# ===========
#
# yong seok Lee
#
#
#  * [2024/01/26]
#     - starting
####################################################

import os
import datetime
import shutil
import yaml
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


####################################################
class Computer(PySelenium):

    # ==============================================
    def __init__(self, config_l):

        PySelenium.__init__(self, headless=False, url='http://partner.sunildyfas.com/',
                            browser='Chrome',
                            width='1200', height='800')

        # yaml 파일 로드
        with open(config_l, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)

        # 수집 on/off
        self.is_done = False

        # 초기화 코드 작성
        # self.com_code = com_code
        # self.user_id = user_id
        # self.user_pwd = user_pwd

        log_path = r'C:\work\NST\python\1.Computer\log'
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        self.logger = get_logger(self.get_safe_path(log_path, 'Computer.log'),
                                 logsize=1024 * 1024 * 10)

        start_ts = datetime.datetime.now().strftime('%Y%m%d')
        # 다운로드 폴더 위치
        # self.down_path = r'C:\Users\dydtj\Downloads'
        self.down_path = r'C:\Users\PC\Downloads'
        # sunil 데이터 옮기는 위치
        data_time = self.config['params']['check time']['datetime']
        self.sunil_path = f'C:\\work\\NST\\1.Computer\\sunil_data\\{data_time}'
        if not os.path.exists(self.sunil_path):
            # 폴더 생성
            os.makedirs(self.sunil_path)

    # ==============================================
    def search(self):
        start_date = self.config['params']['check time']['datetime']
        end_date = '2024-01-26'

        # 발주 출고 기간 날짜 입력
        e = self.get_by_xpath('//input[@id="searchFdate"]')
        e.clear()
        self.send_keys(e, start_date)
        self.implicitly_wait(after_wait=1)

        # 발주 출고 기간 마지막 날짜
        e = self.get_by_xpath('//input[@id="searchTdate"]')
        e.clear()
        self.send_keys(e, start_date)
        self.implicitly_wait(after_wait=1)

        # 거래명세서 출력 여부 - 미출력
        e = self.get_by_xpath('//select[@id="searchInvoice"]/option[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 실적 입력 여부
        e = self.get_by_xpath('//select[@id="searchQty"]/option[2]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

        # 조회 버튼 클릭
        e = self.get_by_xpath('//div[@class="form-group col-md-3 text-center"]//div[2]/a')
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

        # 엑셀 다운로드
        e = self.get_by_xpath('//div[@class="form-group col-md-8 text-center"]//button[@id="excelDown"]')
        self.safe_click(e)
        self.implicitly_wait(after_wait=2)

    # ==============================================
    def login(self):
        # 계정 정보
        user_id = self.config['params']['user_id']
        user_pwd = self.config['params']['user_pwd']

        # 계정 아이디
        e = self.get_by_xpath('//*[@id="id"]')
        self.send_keys(e, user_id)
        self.implicitly_wait(after_wait=1)

        # 계정 비밀번호
        e = self.get_by_xpath('//*[@id="password"]')
        self.send_keys(e, user_pwd)
        self.implicitly_wait(after_wait=1)

        # 로그인 단추 누름
        e = self.get_by_xpath('//button[@type="submit"]', cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==============================================
    def move_file(self):
        file_name = 'SUNILDYFAS_IMGAGONG_LIST.xlsx'

        # 다운로드 폴더에서 목표 폴더로 파일 이동
        source_path = os.path.join(self.down_path, file_name)
        target_path = os.path.join(self.sunil_path, file_name)

        try:
            shutil.move(source_path, target_path)
            self.logger.info('파일 옮기기 성공하였습니다!')
        except FileNotFoundError:
            self.logger.info('파일이 없습니다!')
        except shutil.Error as e:
            self.logger.info('파일 옮기기 실패했습니다.')
    # ==============================================
    def del_file(self):
        try:
            file_path = self.down_path + r'\SUNILDYFAS_IMGAGONG_LIST.xlsx'
            # 파일 존재 여부 확인
            if os.path.exists(file_path):
                # 파일 삭제
                os.remove(file_path)
                print(f"{file_path} 파일이 삭제되었습니다.")
            else:
                print(f"{file_path} 파일이 존재하지 않습니다.")
        except Exception as e:
            print(f"오류 발생: {e}")

    # ==============================================
    def start(self, config_l):
        try:
            # 선일 다운로드 파일 삭제
            self.del_file()

            # 선일다이파스 로그인
            self.login()

            # 검색 조건 검색
            self.search()

            # 다운로드 파일 옮기기
            self.move_file()

        except Exception as e:
            self.logger.error(e)
            return 1


# ==============================================
def do_start(**kwargs):
    with Computer(kwargs['config_l']) as ws:
        ws.start(kwargs['config_l'])


# ==============================================
if __name__ == '__main__':
    config_l = 'login.yaml'
    do_start(config_l=config_l)
