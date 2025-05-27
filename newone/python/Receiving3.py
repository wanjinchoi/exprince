"""
====================================

====================================

Description
===========
입고 정보 저장 처리
"""
## Authors
# ===========
#
# yong seok Lee
#
#
#  * [2023/12/14]
#     - starting
#  * [2024/01/04]
#     - next_page 추가
#     - excel로 수집 중복 처리
#  * [2024/03/15]
#     - 중복데이터 판별(db)
#
#
####################################################
import sqlite3
import os
import datetime
import requests
import json
import time
import yaml
import csv
from selenium import webdriver
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
# from datetime import datetime
import mysql.connector

####################################################
def getdb():
    if not os.path.exists('C:/work/newone/python/newone.db'):
        conn = sqlite3.connect('C:/work/newone/python/newone.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE newone
        (id_no STRING,
        date STRING,
        status STRING)''')
        conn.commit()
        conn.close()
    else:
        pass

def find_value(pk):
    conn = sqlite3.connect('C:/work/newone/python/newone.db')
    cur = conn.cursor()
    cur.execute("SELECT id_no FROM newone WHERE id_no = ?", (pk,))
    rows = cur.fetchall()
    conn.close()
    return rows


def insert_value(id_no, date, response):
    conn = sqlite3.connect('C:/work/newone/python/newone.db')
    cur = conn.cursor()
    query = "INSERT INTO newone VALUES(?,?,?)"
    cur.execute(query, (id_no, date, response))
    conn.commit()
    conn.close()

class Receiving(PySelenium):

    # ==============================================
    def __init__(self, config_l):

        PySelenium.__init__(self, headless=False, url='https://login.ecount.com/Login/',
                            browser='Chrome',
                            width='1920', height='1080')

        # yaml 파일 로드
        with open(config_l, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)

        # 수집 on/off
        self.is_done = False

        # 초기화 코드 작성
        # self.com_code = com_code
        # self.user_id = user_id
        # self.user_pwd = user_pwd

        log_path = r'C:\work\newone\1.RegisterOrder\log_receiving\Receiving'
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        self.logger = get_logger(self.get_safe_path(log_path, 'Receiving.log'),
                                 logsize=1024 * 1024 * 10)

        start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        self.folder_name = f'C:\\work\\newone\\1.RegisterOrder\\data\\Receiving\\{start_ts}'
        if not os.path.exists(self.folder_name):
            # 폴더 생성
            os.makedirs(self.folder_name)

    # ==============================================

    def search(self):
        e = self.get_by_xpath('//*[@id="inputFavMSearch"]', cond='element_to_be_clickable')
        menu = '발주서조회'
        self.send_keys(e, menu)
        self.implicitly_wait(after_wait=1)

        self.send_keys(e, Keys.ENTER)
        self.implicitly_wait(after_wait=1)

        # WMS 클릭
        e = self.get_by_xpath('//a[@id="state_60_2"]', cond='element_to_be_clickable')
        self.safe_click(e)

    # ==============================================
    def get_order(self, data, idx, findmemo):
        try:
            time.sleep(1)
            # 상단 XPath
            top_e = self.get_by_xpath('//ul[@class="wrapper-form wrapper-form-state-2"]')

            # 거래처 코드
            e = top_e.find_element_by_xpath('.//li[@data-listid="cust"]//div[@class="form"]//div//div//input[1]')
            data['customerCode'] = e.get_attribute('value')

            # 거래처명
            e = top_e.find_element_by_xpath('.//li[@data-listid="cust"]//div[@class="form"]//div//div//input[2]')
            data['customerName'] = e.get_attribute('value')

            # 담당자명
            e = top_e.find_element_by_xpath('.//li[@data-listid="emp_cd"]//div[@class="form"]//div//div//input[2]')
            data['managerName'] = e.get_attribute('value')

            # 창고명 본사창고(WM01), 나머지(SWM01) - 전표가 본사창고인 경우 품목에 고정으로 넣음
            e = top_e.find_element_by_xpath('.//li[@data-listid="wh_cd"]//div[@class="form"]//div//div//input[1]')
            wm = e.get_attribute('value')
            # 입고창고 담당자
            e = top_e.find_element_by_xpath('//*[@id="mainPage"]/div[2]/div[5]/div[1]/ul/li[13]/div[2]/div/div/input[2]')
            data['warehouseManager'] = e.get_attribute('value')

            # 구매처 전달사항
            e = top_e.find_element_by_xpath( './/li[@data-listid="u_txt1"]//div[@class="form"]//div//div//textarea[@class="form-control first-child last-child"]')
            data['etcDesc'] = e.text.strip()

            # 하단 XPath
            bottom_e = self.get_by_xpath('//div[@id="fixed_bottom"]//table[@id="grid-main"]//tbody')
            btm_e = [be_e for be_e in bottom_e.find_elements_by_xpath('.//tr')]

            # 품목 데이터 초기화
            data['inputScheduleItemList'] = []

            # 품목코드
            for i in range(len(btm_e)):
                btm = {
                    'itemCode': None,
                    'itemName': None,
                    'itemQuantity': None,
                    'itemStandard': None,
                    'orderForm': None,
                    'partiallyInputYn': None,
                    'quantityPerUnit': None,
                    'store': None,
                    'unit': None,
                    'updateQuantity': '0',
                    'warehouseCode': None,
                    'inputType': None
                }
                btm['inputType'] = findmemo

                # if i == 2:
                #     break
                bottom_e = self.get_by_xpath('//div[@id="fixed_bottom"]//table[@id="grid-main"]//tbody')
                btm_e = [be_e for be_e in bottom_e.find_elements_by_xpath('.//tr')]
                b_e = btm_e[i]

                time.sleep(1)

                # 품목 코드
                e = b_e.find_element_by_xpath('.//td[@data-columnid="prod_cd"]//span')
                if e.text.strip() == '':
                    continue
                else:
                    btm['itemCode'] = e.text.strip()

                # 품목명
                e = b_e.find_element_by_xpath('.//td[@data-columnid="prod_des"]//span')
                btm['itemName'] = e.text.strip()

                # 품목별 창고 코드
                if wm == '01':
                    btm['warehouseCode'] = 'WM01'
                else:
                    btm['warehouseCode'] = 'SWM01'

                # 발주서 비고
                e = b_e.find_element_by_xpath('.//td[@data-columnid="p_remarks1"]//span')
                btm['orderForm'] = e.text.strip()
                # 판매처 현장
                e = b_e.find_element_by_xpath('.//td[@data-columnid="remarks"]//span')
                btm['store'] = e.text.strip()

                # 규격
                e = b_e.find_element_by_xpath('.//td[@data-columnid="size_des"]//span')
                # if e.text.strip == '':
                #     btm['itemStandard'] = None
                # else:
                #     btm['itemStandard'] = e.text.strip()
                btm['itemStandard'] = e.text.strip()

                # 단위
                e = b_e.find_element_by_xpath('.//td[@data-columnid="unit"]//span')
                btm['unit'] = e.text.strip()

                # 수량
                e = b_e.find_element_by_xpath('.//td[@data-columnid="qty"]//span')
                btm['itemQuantity'] = float(e.text.strip().replace(',',''))

                data['inputScheduleItemList'].append(btm)

            e_b = self.get_by_xpath('//button[@class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only ui-dialog-titlebar-close btn btn-primary"]')
            self.safe_click(e_b)
            self.implicitly_wait(after_wait=1)

        except Exception as err:
            self.logger.error(err)
            print(err)
            raise

    # ==========================================================================
    def save_d(self, fn, data):
        fn = fn + '.json'
        with open(fn, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)

    # ==========================================================================
    def save_data(self, data, i):
        at_js_f = self.get_safe_path(
            self.folder_name,
            data['itemInputNumber']
        )
        self.save_d(at_js_f, data)

    # ==========================================================================
    def stop_collection(self, data):
        try:
            # '2021.12.21 21:48:00'
            create_ts = datetime.datetime.strptime(data['itemInputScheduleTs'], '%Y-%m-%d %H:%M:%S').date()
            old_ts = datetime.datetime.strptime(
                self.config['params']['kwargs']['stop_article_older_than']['datetime'],
                self.config['params']['kwargs']['stop_article_older_than']['format']
            ).date()
            if create_ts < old_ts:
                self.logger.error(f'Stop crawling because article create_ts "{create_ts}" '
                                  f'is older than "{old_ts}"')
                return True
            return False
        except Exception as err:
            self.logger.error(err)
            print(err)
            return False

    # ==============================================
    def get_page(self):
        try:
            time.sleep(5)
            try:
                self.get_by_xpath('/html/body/div[3]/div/div[1]/button').click()
            except:
                pass

            tap_check = self.get_by_xpath('//*[@id="state_60_2"]')
            if tap_check.get_attribute('class') == 'tab-group active':
                pass
            else:
                self.driver.close()
                self.logger.info("탭 선택 실패")

            self.get_by_xpath('/html/body/div[4]/div[5]/div[1]/div[4]/div[2]/div[3]/div[1]/div[1]/div/ul/li[4]/a').click()
            self.get_by_xpath('/html/body/div[4]/div[5]/div[1]/div[4]/div[2]/div[3]/table/thead/tr/th[1]/div').click()

            # 데이터 테이블 가져오기
            e = self.get_by_xpath('//*[@id="grid-main"]/tbody')
            bil = [bi for bi in e.find_elements_by_xpath('./tr')]
            for i in range(len(bil)):
                data = {
                    'companyCode': 'newone',
                    'customerName': None,
                    'customerCode': None,
                    'etcDesc': None,
                    'inputPurchaseNumber': None,
                    'inputScheduleItemList': [
                        {
                            'itemCode': None,
                            'itemName': None,
                            'itemQuantity': None,
                            'itemStandard': None,
                            'orderForm': None,
                            'partiallyInputYn': None,
                            'quantityPerUnit': None,
                            'store': None,
                            'unit': None,
                            'updateQuantity': '0',
                            'warehouseCode': None
                        }
                    ],
                    'itemInputNumber': None,
                    'itemInputRequestTs': None,
                    'itemInputScheduleTs': None,
                    'itemInputStatus': 'SSSD',
                    'itemInputType': 'STML',
                    'locationCode': None,
                    'managerName': None,
                    'zone_code': '01-wm-zone',
                    'warehouseManager': None
                }

                time.sleep(1)

                # if i == 1:
                #     self.is_done = True
                #     break

                try:
                    # 메모 내용 확인
                    findx = self.get_by_xpath(
                        '/html/body/div[4]/div[5]/div[1]/div[4]/div[2]/div[3]/table/tbody/tr[' + f"{i + 1}" + ']/td[2]').text
                    ######findx######


                    if 'Z' in findx:
                        findmemo = 'STCD'
                        data['itemInputType'] = 'STCD'
                    elif 'z' in findx:
                        findmemo = 'STCD'
                        data['itemInputType'] = 'STCD'
                    elif 'A' in findx:
                        findmemo = 'STML'
                        data['itemInputType'] = 'STML'
                    elif 'a' in findx:
                        findmemo = 'STML'
                        data['itemInputType'] = 'STML'
                    elif '반품' in findx:
                        data['itemInputType'] = 'STRT'
                    else:
                        findmemo = 'STIS'
                        data['itemInputType'] = 'STIS'
                    # 목록에서 데이터 가져오기
                    e = self.get_by_xpath('//*[@id="grid-main"]/tbody')
                    ail = [bi for bi in e.find_elements_by_xpath('./tr')]
                    bi = ail[i]

                    e = bi.find_element_by_xpath(
                        '//td[contains(@data-columnid, "sale040.p_des4")][@data-rowtype="line"]')
                    X = e.text.strip()
                    print(X)

                    # 주문서NO - 목록 오른쪽 끝
                    e = bi.find_element_by_xpath('.//td[@data-columnid="ADD_TXT_03_T"]//span')
                    data['inputPurchaseNumber'] = e.text.strip()

                    # 일자-NO
                    no_e = bi.find_element_by_xpath('.//td[@data-columnid="sale040.ord_date_no"]//a')
                    data['itemInputNumber'] = no_e.text.strip()

                    db_host = '211.34.80.36'
                    db_port = 23306
                    db_user = "newone"
                    db_password = "newone1!"
                    db_name = "newone"

                    connection = mysql.connector.connect(
                        host=db_host,
                        port=db_port,
                        user=db_user,
                        password=db_password,
                        database=db_name)
                    cursor = connection.cursor()

                    item_input_number = data['itemInputNumber']

                    query = f"SELECT * FROM item_schedule_output WHERE item_out_number = %s"
                    cursor.execute(query, (item_input_number,))

                    records = cursor.fetchall()
                    # # # ## # # ## # # ## # # #

                    if records:
                        column_names = [i[0] for i in cursor.description]

                        for row in records:
                            row_dict = {column_names[i]: row[i] for i in range(len(column_names))}
                            print(row_dict)
                            use_yn_value = row_dict.get('use_yn', 'N/Y')
                            print(use_yn_value)
                        if use_yn_value == 'N':

                            # 출고 예정일자 - 일자-NO에서 추출
                            e = bi.find_element_by_xpath('.//td[@data-columnid="sale040.time_date"]//span')
                            s_ts = e.text.strip()
                            data['itemInputScheduleTs'] = datetime.datetime.strptime(s_ts, '%Y-%m-%d').strftime(
                                '%Y-%m-%d %H:%M:%S')

                            no_e.click()
                            self.implicitly_wait(after_wait=3)
                            self.get_order(data, i)
                            pass
                        elif use_yn_value == 'Y':
                            continue

                  # 입고일자
                    e = bi.find_element_by_xpath('.//td[@data-columnid="sale040.time_date"]//span')
                    s_ts = e.text.strip()
                    data['itemInputScheduleTs'] = datetime.datetime.strptime(s_ts, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')

                    self.safe_click(no_e)
                    self.implicitly_wait(after_wait=1)
                    self.get_order(data, i, findmemo)

                except Exception as err:
                    self.logger.error(err)
                    print(err)
                    raise

                # if self.stop_collection(data):
                #     self.is_done = True
                #     break

                self.save_data(data, i)

        except Exception as err:
            self.logger.error(err)
            print(err)
            raise

    # ==============================================
    def set_WMS(self):

        # api 키
        # api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNjk5NTc3MDM4LCJleHAiOjE3MzExMTMwMzh9.uIF3yaiXGpmjvopj2AR6J7P61yqCee2_iYypV-Jx8ho'
        api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0b2tlbkNyZWF0ZSIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNzMxMjk5Nzk3LCJleHAiOjE4MjU5MDc3OTd9.N9byMbOV9LdM1az6MB9e65rftdx8GT2f3uF0V9UJTtI'

        # API 요청 URL
        # base_url = 'http://211.34.80.56:23301/platform/v1/product/item_schedule_input_register'
        base_url = 'http://211.34.80.36:23301/platform/v1/product/item_schedule_input_register'

        # 테스트 폴더 네임
        # self.folder_name = rf'C:\work\newone\1.RegisterOrder\data\Receiving\20240221-183330'

        # 헤더 설정
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }

        # 폴더 내부의 파일을 읽어옴
        for filename in os.listdir(self.folder_name):
            filepath = os.path.join(self.folder_name, filename)
            # 폴더 내부의 파일이 JSON 파일인 경우에만 처리
            if filename.endswith('.json'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    # JSON 파일을 읽어와서 파이썬 객체로 변환
                    json_data = json.load(file)
                    response = requests.post(base_url, json=json_data, headers=headers)
                    insert_value(json_data['itemInputNumber'],json_data['itemInputScheduleTs'],response.status_code)
                    self.logger.info(f'API 응답 코드: "{response}", 파일명: "{filename}" ')
                    self.logger.info('fine')

    # ==============================================
    def next_page(self):
        try:
            time.sleep(2)
            # self.switch_to_window(0)
            # 페이지 목록
            self.get_by_xpath('//button[contains(text(), "진행상태변경")]').click()
            time.sleep(1)
            # element = self.get_by_xpath('/html/body/div[7]/table/tbody/tr[2]/td[2]/div/div[1]/div/div[3]/a')
            element = self.get_by_xpath('//a[contains(text(),"2.확인중")]')
            element.click()
            time.sleep(3)


        except Exception as err:
            self.logger.error(err)
            print(err)
            raise
        finally:
            self.switch_from_iframe()

    # ==============================================
    def save_json(self, data, output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"Data saved to {output_file}")

    # ==============================================
    def login(self):
        getdb()
        com_code = self.config['params']['kwargs']['com_code']
        user_id = self.config['params']['kwargs']['user_id']
        user_pwd = self.config['params']['kwargs']['user_pwd']
        # 회사 코드
        e = self.get_by_xpath('//*[@id="com_code"]')
        self.send_keys(e, com_code)
        self.implicitly_wait(after_wait=1)

        # 계정 아이디
        e = self.get_by_xpath('//*[@id="id"]')
        self.send_keys(e, user_id)
        self.implicitly_wait(after_wait=1)

        # 계정 비밀번호
        e = self.get_by_xpath('//*[@id="passwd"]')
        self.send_keys(e, user_pwd)
        self.implicitly_wait(after_wait=1)

        # 로그인 단추 누름
        e = self.get_by_xpath('//*[@id="save"]', cond='element_to_be_clickable')
        self.safe_click(e)
        self.implicitly_wait(after_wait=1)

    # ==============================================
    def start(self, config_l):
        try:
            # Ecount 로그인
            self.login()

            # 구매 조회 검색
            self.search()

            self.get_page()

            self.next_page()


            # WMS에 정보 전송
            self.set_WMS()
        #
        except Exception as e:
            self.logger.error(e)
            print(e)
            return 1


# ==============================================
def do_start(**kwargs):
    with Receiving(kwargs['config_l']) as ws:
        ws.start(kwargs['config_l'])


# ==============================================
if __name__ == '__main__':
    config_l = 'login.yaml'
    do_start(config_l=config_l)
