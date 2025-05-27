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
####################################################
import mysql.connector
import shutil
import os
import sqlite3
import datetime
import requests
import json
import time
import yaml
from datetime import datetime
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException,NoSuchElementException

def extract_text(row, css1, css2):
    try:
        return row.find_element(By.CSS_SELECTOR, css1).text.strip()
    except:
        try:
            return row.find_element(By.CSS_SELECTOR, css2).text.strip()
        except:
            return ""



def getdb():
    if not os.path.exists('C:/work/newone/python/newone1.db'):
        conn = sqlite3.connect('C:/work/newone/python/newone1.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE newone1
        (id_no STRING,
        date STRING,
        status STRING)''')
        conn.commit()
        conn.close()
    else:
        pass

def find_value(pk):
    conn = sqlite3.connect('C:/work/newone/python/newone1.db')
    cur = conn.cursor()
    cur.execute("SELECT id_no FROM newone1 WHERE id_no = ?", (pk,))
    result = cur.fetchone()
    conn.close()
    return 1 if result else 2


def insert_value(id_no, date, response):
    conn = sqlite3.connect('C:/work/newone/python/newone1.db')
    cur = conn.cursor()
    query = "INSERT INTO newone1 VALUES(?,?,?)"
    cur.execute(query, (id_no, date, response))
    conn.commit()
    conn.close()

####################################################
class Release(PySelenium):

    # ==============================================
    def __init__(self, config_l):

        PySelenium.__init__(self, headless=False, url='https://login.ecount.com/Login/',
                            browser='Chrome',
                            width='1920', height='1080')
        # yaml 파일 로드
        with open(config_l, encoding='utf-8') as ifp:
            self.config = yaml.load(ifp, yaml.SafeLoader)
        # 초기화 코드 작성
        # self.com_code = com_code
        # self.user_id = user_id
        # self.user_pwd = user_pwd

        # 수집 on/off
        self.is_done = False

        log_path = r'C:\work\newone\1.RegisterOrder\log_release\Release'
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        self.logger = get_logger(self.get_safe_path(log_path, 'Release.log'),
                                 logsize=1024 * 1024 * 10)

        # start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        # self.folder_name = f'C:\\work\\newone\\1.RegisterOrder\\data\\Release\\{start_ts}'
        # if not os.path.exists(self.folder_name):
        #     # 폴더 생성
        #     os.makedirs(self.folder_name)

    # ==============================================
    def search(self):
        e = self.get_by_xpath('//*[@id="inputFavMSearch"]', cond='element_to_be_clickable')
        e.click()
        time.sleep(0.5)

        for ch in "주문서조회":
            e.send_keys(ch)
            time.sleep(0.1)

        time.sleep(1)
        e.send_keys(Keys.ARROW_DOWN)
        e.send_keys(Keys.ENTER)

        # 납품택배 클릭
        time.sleep(4)
        # e = self.get_by_xpath('/html/body/div[4]/div[5]/div[2]/div/div/div[1]/div[1]/div[3]/div[1]/ul/li[9]/a', cond='element_to_be_clickable')
        e = self.get_by_xpath('(//li[@id="Y∬4"])[3]//a', cond='element_to_be_clickable')
        self.safe_click(e)
        # 6페이지 클릭
        try:
            e = self.get_by_xpath('//a[@data-role="6"]',cond='element_to_be_clickable')
            self.safe_click(e)
            time.sleep(4)
        except Exception:
            print('6페이지 없음')

    # ==============================================
    def get_order(self, data, idx):
        try:
            # 상단 XPath
            top_e = self.get_by_xpath('//ul[@class="wrapper-form wrapper-form-state-3"]')

            # 거래처명
            e = top_e.find_element_by_xpath('.//li[@data-listid="cust"]//div[@class="form"]//div//div//input[2]')
            data['customerName'] = e.get_attribute('value')

            # 거래처 코드
            e = top_e.find_element_by_xpath('.//li[@data-listid="cust"]//div[@class="form"]//div//div//input[1]')
            data['customerCode'] = e.get_attribute('value')

            # 주문 No.
            e = top_e.find_element_by_xpath('.//li[@data-listid="doc_no"]//input[@class="form-control form-control first-child last-child"]')
            data['linkOrderNumber'] = e.get_attribute('value')

            # 현장 담당자
            e = top_e.find_element_by_xpath('.//li[@data-listid="u_memo4"]//div[@class="form"]//div//div//input[1]')
            data['siteManager'] = e.get_attribute('value')

            # 현장 연락처
            e = top_e.find_element_by_xpath('.//li[@data-listid="u_memo5"]//div[@class="form"]//div//div//input[1]')
            data['siteContact'] = e.get_attribute('value')

            # 현장 주소
            e = top_e.find_element_by_xpath('.//li[@data-listid="u_memo3"]//div[@class="form"]//div//div//input[1]')
            data['siteAddress'] = e.get_attribute('value')

            # 명세서 출력용 비고
            e = top_e.find_element_by_xpath(
                './/li[@data-listid="u_memo2"]//input[@class="form-control form-control first-child last-child"]')
            data['statementRemarks'] = e.get_attribute('value')

            # 내부관리용 비고
            e = top_e.find_element_by_xpath(
                './/li[@data-listid="u_txt1"]//textarea[@class="form-control first-child last-child"]')
            data['insiteRemarks'] = e.text.strip()

            # 승인업체
            e = top_e.find_element_by_xpath('.//li[@data-listid="ADD_LTXT_01_T"]//textarea[@class="form-control first-child last-child"]')
            data['approvedCompany'] = e.text.strip()

            # 수정 사항
            e = top_e.find_element_by_xpath('.//li[@data-listid="ADD_TXT_02_T"]//input[@class="form-control form-control first-child last-child"]')
            data['modifyRemarks'] = e.get_attribute('value')

            # 출고 담당
            e = self.get_by_xpath('//input[@class="form-control last-child" and @data-cid="emp_cd"]')
            data['outputManager'] = e.get_attribute('value')

            # 하단 XPath ----------------------------------------------------------------------------
            bottom_e = self.get_by_xpath('//div[@id="fixed_bottom"]//table[@id="grid-main"]//tbody')
            btm_e = [be_e for be_e in bottom_e.find_elements_by_xpath('.//tr')]

            # 품목 데이터 초기화
            data['outputScheduleItemList'] = []

            # 품목코드
            for i in range(len(btm_e)):
                btm = {
                    'amountPerUnit': None,
                    'itemDeliveryType': None,
                    'forwardingStatus': None,
                    'itemCode': None,
                    'itemLocation': None,
                    'itemName': None,
                    'itemOutNumber': None,
                    'itemQuantity': None,
                    'itemStandard': None,
                    'outputItemIdx': None,
                    'partiallyOutYn': None,
                    'relatedMatter': None,
                    'serialNumber': None,
                    'unit': None,
                    'useYn': None
                }

                # if i == 2:
                #     break
                bottom_e = self.get_by_xpath('//div[@id="fixed_bottom"]//table[@id="grid-main"]//tbody')
                btm_e = [be_e for be_e in bottom_e.find_elements_by_xpath('.//tr')]
                b_e = btm_e[i]

                time.sleep(1)

                # 품목 코드
                e = b_e.find_element_by_xpath('.//td[@data-columnid="prod_cd"]//span')
                if e.text.strip() == '':
                    break
                else:
                    btm['itemCode'] = e.text.strip()

                # 출고 유형 - 유형에 따라 코드로 저장
                e = b_e.find_element_by_xpath('.//td[@data-columnid="ADD_TXT_02"]//span')
                if e.text.strip() == '재':
                    btm['itemDeliveryType'] = 'DTML'
                elif e.text.strip() == '입':
                    btm['itemDeliveryType'] = 'DTCD'
                else:
                    btm['itemDeliveryType'] = 'DTOW'

                # 물류팀 전달사항
                e = b_e.find_element_by_xpath('.//td[@data-columnid="p_remarks3"]//span')
                btm['relatedMatter'] = e.text.strip()

                if btm['relatedMatter'].startswith("z") or btm['relatedMatter'].startswith("Z") or btm['relatedMatter'].startswith("직"):
                    btm['itemDeliveryType'] = 'DTOW'
                elif btm['relatedMatter'].startswith("a") or btm['relatedMatter'].startswith("A") or btm['relatedMatter'].startswith("입"):
                    btm['itemDeliveryType'] = 'DTCD'
                else:
                    btm['itemDeliveryType'] = 'DTML'

                # 품목명
                e = b_e.find_element_by_xpath('.//td[@data-columnid="prod_des"]//span')
                btm['itemName'] = e.text.strip()

                # 규격
                e = b_e.find_element_by_xpath('.//td[@data-columnid="size_des"]//span')
                btm['itemStandard'] = e.text.strip()

                # 단위 당 수량
                e = b_e.find_element_by_xpath('.//td[@data-columnid="p_remarks2"]//span')
                btm['amountPerUnit'] = e.text.strip()

                # 단위
                e = b_e.find_element_by_xpath('.//td[@data-columnid="unit"]//span')
                btm['unit'] = e.text.strip()

                # 수량
                e = b_e.find_element_by_xpath('.//td[@data-columnid="qty"]//span')
                btm['itemQuantity'] = int(e.text.strip().replace(',',''))

                data['outputScheduleItemList'].append(btm)

            e_b = self.get_by_xpath(
                '//button[@class="ui-button ui-widget ui-state-default ui-corner-all ui-button-text-only ui-dialog-titlebar-close btn btn-primary"]')
            self.safe_click(e_b)
            self.implicitly_wait(after_wait=1)

        except Exception as err:
            self.logger.error(err)
            self.logger.info('release-1')
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
            data['itemOutNumber']
        )
        self.save_d(at_js_f, data)

    # ==========================================================================
    def stop_collection(self, data):
        try:
            # '2021.12.21 21:48:00'
            create_ts = datetime.datetime.strptime(data['deliveryExpectDay'], '%Y-%m-%d %H:%M:%S').date()
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
            self.logger.info('release-1')
            print(err)
            return False

    # ==============================================
    def get_page(self):
        try:
            rows = self.driver.find_elements(By.XPATH,'/html/body/div[2]/div[5]/div[3]/div[1]/div[2]/div[2]/div/div/table/tbody/tr')
            if len(rows) == 0:
                pass
            #원래메인페이지 저장
            else:
                # 오늘날짜 폴더만들기
                today_str = datetime.now().strftime('%Y%m%d%H%M%S')
                folder_path = os.path.join('C:\\work\\newone\\1.RegisterOrder\\data\\Release\\', today_str)
                os.makedirs(folder_path, exist_ok=True)
                for i in range(1, len(rows)+1):
                    main_handle = self.driver.current_window_handle
                    #DB에 해당 주문번호 있는지 확인하기
                    xpath = f'//*[@id="grid-main"]/tbody/tr[{i}]/td[9]'
                    elem = self.get_by_xpath(xpath)
                    db_check_num = elem.get_attribute('textContent').strip()
                    check_num = find_value(db_check_num)
                    #번호가 있으면 1 없으면 2
                    if check_num == 1:
                        print(f"[{i}] ✅ 이미 처리된 번호: {db_check_num} → SKIP")
                        continue
                    else:
                        print(f"[{i}] 🚀 신규 처리 시작: {db_check_num}")
                        #순서대로 출력번호 클릭
                        xpath = f'//*[@id="grid-main"]/tbody/tr[{i}]/td[9]'
                        self.get_by_xpath(xpath).click()
                        print('출력no클릭')
                        try:
                            #팝업창 선택해서 내부정보 가져오기
                            popup = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR,'div[data-popup-id^="ESD004M_"]')))
                            print("✅ 팝업 감지됨")

                            #승인업체
                            textarea = self.driver.find_element(By.CSS_SELECTOR,"textarea[data-cid='ADD_LTXT_01_T']")
                            approvedCompany = textarea.get_attribute("value")
                            if approvedCompany == '승인업체':
                                approvedCompany =None
                            print('approvedCompany')

                            #거래처 코드
                            textarea2 = self.driver.find_element(By.CSS_SELECTOR, "input[data-cid='cust'][data-index='0']")
                            customerCode = textarea2.get_attribute("value")
                            print(customerCode)

                            # 거래처명(상호명)
                            textarea3 = self.driver.find_element(By.CSS_SELECTOR, "input[data-cid='cust'][data-index='1']")
                            customerName = textarea3.get_attribute("value")
                            print(customerName)

                            #출고예정일자
                            textarea4 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='doc_no']")
                            deliveryExpectDay_orgin = textarea4.get_attribute("value")
                            dt_str = deliveryExpectDay_orgin.split('-')[0]  # '202505150507'
                            dt = datetime.strptime(dt_str, "%Y%m%d%H%M")
                            deliveryExpectDay = dt.strftime("%Y-%m-%d %H:%M:%S")
                            print(deliveryExpectDay)

                            #내부관리용 비고
                            textarea5 = self.driver.find_element(By.CSS_SELECTOR,"textarea[data-cid='u_txt1']")
                            insiteRemarks = textarea5.get_attribute("value")
                            if insiteRemarks == '내부관리용 비고':
                                insiteRemarks =None
                            print(insiteRemarks)

                            #출고 번호 작성일자
                            #textarea6 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='doc_no']")
                            itemOutNumber = db_check_num
                            print(itemOutNumber)

                            #w주문번호
                            textarea7 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='doc_no']")
                            linkOrderNumber = textarea7.get_attribute("value")
                            print(linkOrderNumber)

                            #수정사항
                            textarea8 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='ADD_TXT_02_T']")
                            modifyRemarks = textarea8.get_attribute("value")
                            if modifyRemarks == '수정사항':
                                modifyRemarks =None
                            print(modifyRemarks)

                            #출고담당자
                            textarea9 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='emp_cd']")
                            outputManager = textarea9.get_attribute("value")
                            print(outputManager)

                            #현장주소
                            textarea10 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='u_memo3']")
                            siteAddress = textarea10.get_attribute("value")
                            print(siteAddress)

                            #현장연락처 siteContact
                            textarea11 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='u_memo5']")
                            siteContact = textarea11.get_attribute("value")
                            print(siteContact)

                            #현장담당자 siteManager
                            textarea12 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='u_memo4']")
                            siteManager = textarea12.get_attribute("value")
                            print(siteManager)

                            #명세서출력용비고 statementRemarks
                            textarea13 = self.driver.find_element(By.CSS_SELECTOR,"input[data-cid='u_memo2']")
                            statementRemarks = textarea13.get_attribute("value")
                            print(statementRemarks)

                            # 3) 테이블에서 항목별 리스트 추출
                            popup_tbody = popup.find_element(By.CSS_SELECTOR,'#grid-main tbody')
                            rows = popup_tbody.find_elements(By.TAG_NAME, 'tr')
                            output_items=[]
                            for idx, row in enumerate(rows):
                                elem =row.find_element(By.XPATH,'.//td[contains(@data-columnid, "p_remarks2")]/span')
                                #단위당 수량
                                amount_per_unit = elem.text.strip()
                                print(f"[{idx}] 단위당 수량: { amount_per_unit}")
                                #품목코드
                                elem2 = row.find_element(By.XPATH,'.//td[contains(@data-columnid, "prod_cd")]/span')
                                item_code = elem2.text.strip()
                                #품목명
                                elem3= row.find_element(By.XPATH,'.//td[contains(@data-columnid, "prod_des")]/span')
                                item_name = elem3.text.strip()
                                if not item_name:
                                    continue
                                #수량
                                elem4 = row.find_element(By.XPATH,'.//td[@data-columnid="qty"]')
                                quantity_text = elem4.text.strip()
                                quantity_text = quantity_text.replace(',','')
                                quantity_text = '0' if quantity_text in ['','.'] else quantity_text
                                #물류팀 전달사항
                                elem5 = row.find_element(By.XPATH,'.//td[contains(@data-columnid, "p_remarks3")]/span')
                                item_delivery_type_orgin = elem5.text.strip()
                                #입으로 시작하는지 여부
                                if item_delivery_type_orgin.startswith("입"):
                                    item_delivery_type = "DTCD"
                                elif item_delivery_type_orgin.startswith("직"):
                                    item_delivery_type = "DTOW"
                                else:
                                    item_delivery_type = "DTML"
                                #단위
                                elem6 = row.find_element(By.XPATH,'.//td[contains(@data-columnid, "unit")]/span')
                                unit = elem6.text.strip()

                                output_items.append({
                                    "amountPerUnit": amount_per_unit,
                                    "forwardingStatus": None,  # 값입력 x
                                    "itemCode": item_code,
                                    "itemDeliveryType": item_delivery_type,
                                    # 로직 반영 필요
                                    "itemLocation": None,
                                    "itemName": item_name,
                                    "itemOutNumber": None,  # 값입력 x
                                    "itemQuantity": quantity_text,
                                    "itemStandard": None,
                                    "outItemSerialList": [{
                                        "outSerialIdx": None,
                                        "outputCount": None,
                                        "outputItemIdx": None,
                                        "serialInventory": None,
                                        "serialNumber": None,
                                        "useYn": None,
                                    }],
                                    "outputItemIdx": idx,
                                    "partiallyOutYn": None,
                                    "unit": unit,
                                    "useYn": None
                                })

                            # 4) 최종 JSON 구조 생성
                            data = {
                                "approvedCompany": approvedCompany,
                                "companyCode": "newone",
                                "confirmationStatus": None,
                                "customerCode": customerCode,
                                "customerName": customerName,
                                "deliveryExpectDay": deliveryExpectDay,
                                "deliveryStatus": None,
                                "deliveryType": None,
                                "etcDesc": None,
                                "insiteRemarks": insiteRemarks,
                                "itemOutDay": None,
                                "itemOutNumber": itemOutNumber,
                                "linkOrderNumber": linkOrderNumber,
                                "locationCode": None,
                                "modifyDate": None,
                                "modifyId": None,
                                "modifyRemarks": modifyRemarks,
                                "outputManager": outputManager,
                                "outputScheduleItemList": output_items,
                                "registrantDate": None,
                                "siteAddress": siteAddress,
                                "siteContact": siteContact,
                                "siteManager": siteManager,
                                "statementItemCount": len(output_items),
                                "statementRemarks": statementRemarks,
                                "useYn": None,
                                "warehouseCode": None,
                                "zoneCode": None
                            }

                            # 5) 파일로 저장
                            file_name = f"{itemOutNumber}.json"
                            file_path = os.path.join(folder_path, file_name)
                            self.logger.info('파일생성완료')
                            with open(file_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, ensure_ascii=False, indent=4)

                            #팝업창 클릭
                            self.driver.find_element(By.CSS_SELECTOR,"button.ui-dialog-titlebar-close").click()
                            #메인페이지로 다시 돌아가기
                            self.driver.switch_to.window(main_handle)
                            print('메인페이지로 다시옴 다음꺼로넘어감')

                            #json파일 전송
                            api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0b2tlbkNyZWF0ZSIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNzMxMjk5Nzk3LCJleHAiOjE4MjU5MDc3OTd9.N9byMbOV9LdM1az6MB9e65rftdx8GT2f3uF0V9UJTtI'
                            # 헤더 설정
                            headers = {
                                'Content-Type': 'application/json',
                                'Authorization': f'Bearer {api_key}'
                            }
                            # API 요청 URL
                            base_url = 'http://211.34.80.36:23301/platform/v1/product/item_schedule_output_register'
                            with open(file_path, 'r', encoding='utf-8') as f:
                                json_data = json.load(f)
                            try:
                                response = requests.post(base_url,json=json_data,headers=headers)
                                response.raise_for_status()  # HTTP 에러 발생 시 예외 발생
                                print(f"Status Code: {response.status_code}")
                                print(f"Response Body: {response.text}")
                            except requests.exceptions.HTTPError as errh:
                                print(f"HTTP Error: {errh}")
                                print(f"Status Code: {response.status_code}")
                                print(f"Response Body: {response.text}")
                            except requests.exceptions.ConnectionError as errc:
                                print(f"Connection Error: {errc}")
                            except requests.exceptions.Timeout as errt:
                                print(f"Timeout Error: {errt}")
                            except requests.exceptions.RequestException as err:
                                print(f"Unexpected Error: {err}")

                            #DB삽입
                            insert_value(db_check_num,json_data['deliveryExpectDay'],response.status_code)
                            self.logger.info(f'API 응답 코드: "{response}", 파일명: "{file_path}" ')
                            self.logger.info('DB삽입완료')

                        except TimeoutException:
                            print("❌ 팝업을 찾지 못했음 (TimeoutException)")
                        except NoSuchElementException:
                            print("❌ input[2] 요소를 팝업 내에서 찾지 못했음")
                        except Exception as e:
                            print(f"⚠️ 예외 발생: {e}")

        except Exception as err:
            self.logger.error(err)
            self.logger.info('release-1')
            print(err)
            raise

    # ==============================================
    def set_WMS(self):

        # api 키
        # api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNjk5NTc3MDM4LCJleHAiOjE3MzExMTMwMzh9.uIF3yaiXGpmjvopj2AR6J7P61yqCee2_iYypV-Jx8ho'
        api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0b2tlbkNyZWF0ZSIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNzMxMjk5Nzk3LCJleHAiOjE4MjU5MDc3OTd9.N9byMbOV9LdM1az6MB9e65rftdx8GT2f3uF0V9UJTtI'

        # API 요청 URL
        # base_url = 'http://211.34.80.56:23301/platform/v1/product/item_schedule_output_register'
        base_url = 'http://211.34.80.36:23301/platform/v1/product/item_schedule_output_register'

        # Json 데이터 저장 리스트
        data_list = []

        # 테스트 폴더 네임
        # self.folder_name = r'C:\work\newone\1.RegisterOrder\data\Release\20240221-162755'

        # 헤더 설정
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        #빈폴더 삭제
        base_path = r"C:\work\newone\1.RegisterOrder\data\Release"

        for folder_name in os.listdir(base_path):
            folder_path = os.path.join(base_path, folder_name)

            if os.path.isdir(folder_path):
                has_file = False
                for root, dirs, files in os.walk(folder_path):
                    if files:
                        has_file = True
                        break
                if not has_file:
                    shutil.rmtree(folder_path)
        # # 폴더 내부의 파일을 읽어옴
        # for filename in os.listdir(self.folder_name):
        #     filepath = os.path.join(self.folder_name, filename)
        #
        #     # 폴더 내부의 파일이 JSON 파일인 경우에만 처리
        #     if filename.endswith('.json'):
        #         with open(filepath, 'r', encoding='utf-8') as file:
        #             # JSON 파일을 읽어와서 파이썬 객체로 변환
        #             json_data = json.load(file)
        #             response = requests.post(base_url, json=json_data, headers=headers)
        #             insert_value(json_data['itemOutNumber'],json_data['deliveryExpectDay'],response.status_code)
        #             self.logger.info(f'API 응답 코드: "{response}", 파일명: "{filename}" ')
        #             self.logger.info('release-1')
                    # data_list.append(json_data)

    # ==============================================
    def next_page(self):
        try:
            time.sleep(2)
            # 페이지 목록
            e = self.get_by_xpath('//ul[@class="pagination"]//li[@class="next-page"]/a')
            self.move_to_element(e)
            ple = e.find_element_by_xpath('.//ul[@class="pagination"]')
            is_on = False
            self.move_to_element(ple)
            for pa in ple.find_elements_by_xpath('./li'):
                if 'active' in pa.get_attribute('class'):
                    is_on = True
                    continue
                elif is_on == True:
                    click_c = pa.find_element_by_xpath('.//a')
                    self.safe_click(click_c)
                    self.implicitly_wait(after_wait=1)
                    return
            self.is_done = True
        except Exception as err:
            self.logger.error(err)
            logger.info('release-1')
            print(err)
            pass
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

            # 판매 조회 검색
            self.search()
            print('납품택배조회 끝')
            self.get_page()

            self.set_WMS()

        except Exception as err:

            self.logger.error(err)
            self.logger.info('release-1')
            print(err)
            return 1


# ==============================================
def do_start(**kwargs):
    with Release(kwargs['config_l']) as ws:
        ws.start(kwargs['config_l'])


# ==============================================
if __name__ == '__main__':
    config_l = r'C:\work\newone\python\login.yaml'
    do_start(config_l=config_l)