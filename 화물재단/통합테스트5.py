from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import requests
import warnings
import sqlite3
import shutil
import base64
import json
import time
import uuid
import cv2
import os
import pandas as pd


# ############ Variable Setting ################
TODAY = datetime.today().strftime("%Y%m%d")
LOGIN_ID = 'ber072'
LOGIN_PASSWORD = 'q654321@!'
SITE_ADDRESS = "http://117.52.162.109/admin"
SITE_ANNOUNCE_IDX = 2  # 셀레니움 크롬 드라이버로 접속했을 때 공고조회 창에서 몇번 째 항목인지 확인할 것
ANNOUNCE_DATE = '2024-01-24'

API_URL = 'https://hgy0v6wlvy.apigw.ntruss.com/custom/v1/13705/2cdaf3c233bced7e239d268ad566234a9a89e392b3eb9bb849e1fd58c1b75555/general'
SECRET_KEY = 'dlR4WmRGVE1LZnRNSWdNRE1YS1ZQWEZPWGFwaHd6VXo='

DOWNLOAD_PATH = "C:/ARGOSRPA/backup/download"  # 이미지 파일 저장 경로
DB_PATH = "C:/ARGOSRPA/db/fordriver.db"
COPIED_DB_PATH = f'C:/ARGOSRPA/db/fordriver_{datetime.today().strftime("%y%m%d%H%M%S")}.db'
ALERT_PATH = "C:/ARGOSRPA/log/alert.txt"
START_PAGE = 1  # 크롤링을 시작할 page

UNSUPPORTED_FORMAT = (".gif", )  # tuple

# ########### Log Setting ##################
logger = logging.getLogger()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
file_handler = logging.FileHandler('C:/ARGOSRPA/log/' + TODAY + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(level=logging.DEBUG)


# ########### Selenium Setting #################
warnings.filterwarnings("ignore", category=DeprecationWarning)
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": DOWNLOAD_PATH,  # 다운로드 기본 폴더 지정
    "download.prompt_for_download": False,  # 다운로드 시 확인 창 안 뜨게 설정
    "directory_upgrade": True  # 기존 폴더 변경
})
driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(10)


# 항상 "/"를 사용하여 경로를 출력하도록 변경
# "/"와 "\\"를 중구난방으로 사용하여 난잡해지는 것을 방지하기 위함
def path_join(*paths):
    return os.path.join(*paths).replace(os.sep, "/")


# ########## DB Setting ##################
def init_db(dbpath, copied_dbpath):  # db가 존재하지 않으면 생성
    if not os.path.exists(dbpath):
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE success
        (pk STRING,
        name STRING,
        Phone STRING,
        date STRING,
        login_id STRING,
        maskingstatus STRING,
        getimage STRING
        )''')
        conn.commit()
        conn.close()
    else:  # 원본 DB는 유지하고 카피한 DB에 작성함
        shutil.copy(dbpath, copied_dbpath)


def get_table_data(db_file, table_name):
    """ 주어진 테이블의 데이터를 리스트로 반환 """
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()

    conn.close()

    return columns, rows


def compare_databases(db_file1, db_file2):
    """ 두 SQLite DB 파일을 비교하여 동일한지 확인 """

    # 데이터 비교

    columns1, rows1 = get_table_data(db_file1, "success")
    columns2, rows2 = get_table_data(db_file2, "success")

    if columns1 != columns2:
        return False

    if rows1 != rows2:
        return False

    return True


# 처리한 List는 DB에 저장
def insert_value(pk, name, phone, inert_date, login_id, maskingstatus, getimage):
    conn = sqlite3.connect(COPIED_DB_PATH)
    cur = conn.cursor()
    insert_query = "INSERT INTO success VALUES(?, ?, ?, ?, ?, ?, ?)"
    cur.execute(insert_query, (pk, name, phone, inert_date, login_id, maskingstatus, getimage))
    conn.commit()
    conn.close()
    logger.info("DB Insert Complete", name, phone)


# 검색한 List가 DB에 있는지 조회
def find_value(pk):
    conn = sqlite3.connect(COPIED_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM success s WHERE s.pk =:pk", {"pk": pk})
    rows = cur.fetchall()
    conn.close()
    return rows


# 재업로드한 List를 처리한 뒤 DB업데이트
def update_value(pk):
    conn = sqlite3.connect(COPIED_DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE success SET success_date = '" + str(
        datetime.now().date()) + "' WHERE success.pk =:pk", {"pk": pk})
    conn.commit()
    conn.close()
    logger.info("DB Update Complete!", pk)


# DOWNLOAD_PATH 초기화
def folder_init(folder_path):
    list_folder = os.listdir(folder_path)
    for i in list_folder:
        os.remove(path_join(folder_path, i))
        

# main() 종료 후 db를 excel로 저장
def resultexcel():
    _time_stamp = datetime.today().strftime("%y%m%d%H%M%S")
    conn = sqlite3.connect(COPIED_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM success", conn)
    success = 'success' + _time_stamp
    df.to_excel('C:/ARGOSRPA/db/'+success+'.xlsx', index=False)


def write_alert_list(alert_context, page_num):
    with open(ALERT_PATH, 'a', encoding='utf-8') as file:
        file.write(f'{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} - page: {page_num}\n{alert_context}\n')


# 이미지의 해상도가 떨어져 인식field가 적거나, 13자리의 숫자가 패리티체크에 실패한 경우
# 아래 엑셀에 정리하여 반환
# Not used
# def insert_excel(file_path, name, birth, Unreconize):
#     try:
#         workbook = load_workbook(file_path)
#     except FileNotFoundError:
#         workbook = Workbook()
#     ws = workbook['Sheet1']
#     i = 1
#     while True:
#         i += 1
#         if ws.cell(row=i, column=1).value is not None:
#             pass
#         else:
#             ws.cell(row=i, column=1).value = name
#             ws.cell(row=i, column=2).value = birth
#             ws.cell(row=i, column=3).value = Unreconize
#             break
#     try:
#         workbook.save(file_path)
#         return 0
#     except Exception as e:
#         print(e)
#         return 1


# 폴더 내 파일을 리스트에 담아 반환
# 가장 오래된 파일부터
def find_image(folder_path):
    # 디렉토리 내의 모든 파일 목록 가져오기
    files = [path_join(folder_path, f) for f in os.listdir(folder_path) if os.path.isfile(path_join(folder_path, f))]

    # 파일들을 수정 시간 순으로 정렬
    sorted_files = sorted(files, key=os.path.getmtime)  # getmtime: 수정 시간 기준으로 정렬

    return sorted_files


# 마스킹할 파일을 특정 폴더에 백업
def backup_image(path, key, filename, folder_name):
    logger.info("start backup_image")
    logger.info(f"path: {path}")
    logger.info(f"key: {key}")
    logger.info(f"filename: {filename}")
    logger.info(f"folder_name: {folder_name}")

    parent_download_path = os.path.dirname(DOWNLOAD_PATH)
    logger.info(f"split_: {parent_download_path}")
    backup_dir = parent_download_path + "/" + key + "_" + folder_name + "/"  # backup이미지를 저장할 dir 명
    if os.path.isdir(backup_dir):
        logger.info(f"{backup_dir}이 존재함")
    else:
        os.makedirs(backup_dir)

    time.sleep(2)
    file_format = path.split("/")[-1].split(".")[-1]
    shutil.copy2(path, path_join(backup_dir, filename + "." + file_format))
    logger.info(str(key) + str(filename) + "Image Backup Complete")
    return backup_dir


# yymmdd 형식의 문자열이 valid한 날짜인지 체크
def is_valid_date(date_str):
    try:
        datetime.strptime(date_str,  "%y%m%d")
        return True
    except ValueError:
        return False
 

# 주민등록번호인지 체크
def check_jumin_num(text):
    if '-' in text and text.count('-') == 1:  # "-"이 하나만 포함되어 있어야 함
        logger.info(str(text))
    else:
        return False

    id_num = text.split("-")

    if len(id_num[0]) == 6 and len(id_num[1]) == 7:  # "-"을 기준으로 앞이 6자리, 뒤가 7자리가 아니면 False
        pass
    else:
        return False

    if id_num[0].isdigit() and id_num[1].isdigit():  # 13자리 숫자가 아니면 False
        pass
    else:
        return False

    if not is_valid_date(id_num[0]):  # valid한 날짜가 아니면 False
        return False

    sex = id_num[1][0]  # 주민번호 뒷자리의 첫번째 번호

    if sex == "9" or sex == "0":  # 뒷자리가 9, 0이면 1899년 이전 출생자임
        return False

    # #############패리티 체크 로직, 20년생 이후로는 작동하지 않음 ########################
    # multiple = 2
    # total = 0
    # for j in range(len(s_i_n) - 1):
    #     total += (int(s_i_n[j]) * multiple)
    #     multiple += 1
    #     if multiple > 9:
    #         multiple = 2
    # parity_check = 11 - (total % 11)
    # if int(s_i_n[6]) == 5 or int(s_i_n[6]) == 6:
    #     parity_check = parity_check + 2
    # if parity_check >= 10:
    #     parity_check = parity_check - 10
    # if (int(s_i_n[-1]) == parity_check and 0 < int(s_i_n[6]) < 7 and int(
    #        s_i_n[4] + s_i_n[
    #             5]) < 32) or (int(s_i_n[0]) == 2 and int(s_i_n[6]) < 2):  # 패리티체크에 성공하고, 7번째 자리수가 6이하(외국인 주민번호 포함), 5~6번째 값이 31일 이하 인경우 주민번호로 판단
    # #############패리티 체크 로직, 20년생 이후로는 작동하지 않음 ########################

    return True


def redact_image(json_data, temp_path, file_key, folder_name):
    logger.info("start redactImage")
    success_count = 0  # masking 횟수, 뒷자리 한번 masking 할 때마다 +1
    backup_name = datetime.today().strftime("%y%m%d%H%M%S")
    backup_dir = False
    is_backup_complete = False
    for i in range(len(json_data['images'][0]['fields'])):  # OCR 결괏값의 각 bbox
        ocr_text = json_data['images'][0]['fields'][i]['inferText']
        is_jumin_num = check_jumin_num(ocr_text)
        if is_jumin_num:
            logger.info("주민번호일 수도 있음")

            try:
                if not is_backup_complete:
                    temp = backup_image(temp_path, file_key, backup_name, folder_name)
                    is_backup_complete = True
                logger.info("redact_4")

                if not backup_dir:
                    backup_dir = temp
                    logger.info("redact_4.5")
            except Exception as e:
                logger.warning(str(e))
                pass
            logger.info("ID detected")
            coordinates = [json_data['images'][0]['fields'][i]['boundingPoly']['vertices']]
            if abs(coordinates[0][0]['x'] - coordinates[0][2]['x']) > abs(
                    coordinates[0][0]['y'] - coordinates[0][2]['y']):
                coordinates_50_percentage = (coordinates[0][0]['x'] +
                                             coordinates[0][2]['x']) / 2
                logger.info("isVertical")

                time.sleep(2)
                im = cv2.imread(temp_path)
                cv2.rectangle(im, (
                int(coordinates_50_percentage), int(coordinates[0][0]['y'] - 10)), (
                              int(coordinates[0][2]['x']),
                              int(coordinates[0][2]['y'] + 10)), (255, 0, 0), -1)
                try:
                    cv2.imwrite(temp_path, im)
                    logger.info(temp_path + "Image Masking Complete")
                    success_count += 1
                except Exception as e:
                    logger.warning(e)
                    return 1, backup_dir

            elif abs(coordinates[0][0]['x'] - coordinates[0][2]['x']) < abs(coordinates[0][0]['y'] - coordinates[0][2]['y']):
                coordinates_50_percentage = (coordinates[0][0]['y'] +
                                             coordinates[0][2]['y']) / 2
                logger.info("isNotVertical")
                time.sleep(2)
                im = cv2.imread(temp_path)
                if coordinates[0][0]['x'] - coordinates[0][2]['x'] > 0:
                    cv2.rectangle(im, (
                    int(coordinates[0][0]['x'] + 10), int(coordinates_50_percentage)), (
                                  int(coordinates[0][2]['x'] - 10),
                                  int(coordinates[0][2]['y'])), (255, 0, 0), -1)
                else:
                    cv2.rectangle(im, (
                    int(coordinates[0][0]['x'] - 10), int(coordinates_50_percentage)), (
                                  int(coordinates[0][2]['x'] + 10),
                                  int(coordinates[0][2]['y'])), (255, 0, 0), -1)
                try:
                    cv2.imwrite(temp_path, im)
                    logger.info(temp_path + "Image Masking Complete")
                    success_count += 1
                except Exception as e:
                    logger.warning(str(e))
                    return 1
            else:
                pass
    return success_count, backup_dir


# OCR API에 이미지와 함께 요청, 이미지 인식하여 응답
def call_api(file_path):
    api_url = API_URL
    secret_key = SECRET_KEY
    image_file = file_path
    try:
        with open(image_file, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        logger.info(f"{file_data} not found")
        return False
    request_json = {
        'images': [
            {
                'format': 'jpg',
                'name': 'demo',
                'data': base64.b64encode(file_data).decode()
            }
        ],
        'requestId': str(uuid.uuid4()),
        'version': 'V2',
        'timestamp': int(round(time.time() * 1000))
    }
    payload = json.dumps(request_json).encode('UTF-8')
    headers = {'X-OCR-SECRET': secret_key,'Content-Type': 'application/json'}
    response = requests.request("POST", api_url, headers=headers, data=payload)

    return response


# ######################################################
# ################### 시나리오 시작 #####################
# ######################################################


def crawling_page():
    # DOWNLOAD_PATH 초기화
    folder_init(DOWNLOAD_PATH)
    logger.info("Complete Folder init!")

    # 화물복지재단 접속 및 로그인
    driver.get(SITE_ADDRESS)  # 페이지 접속
    driver.find_element(By.XPATH, '//*[@id="id"]').send_keys(LOGIN_ID)  # 아이디 입력 선택
    driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(LOGIN_PASSWORD)  # 패스워드 입력 선택
    driver.find_element(By.XPATH, '//*[@id="btnId"]').click()  # 로그인

    # 사업 공고 선택
    driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[4]/a[4]').click()  # 사업공고 및 마감 선택
    driver.find_element(By.XPATH,'/html/body/div[2]/div[2]/div[1]/div[2]/ul/li[6]/a').click()  # 신청서 이미지앨범 선택
    time.sleep(5)
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/div[1]/table/tbody/tr[1]/td[1]/img').click()  # 공고조회클릭
    driver.switch_to.window(driver.window_handles[1])  # 세컨드 윈도우 포커싱

    # 원하는 공고 선택 (ex. 건강검진사업)
    driver.find_element(By.XPATH,'/html/body/div[3]/form/div/table/tbody/tr[1]/td[1]/select').click()    #공고조회팝업-사업명
    driver.find_element(By.XPATH, f'/html/body/div[3]/div/table/tbody/tr[{SITE_ANNOUNCE_IDX}]/td[1]').click()
    driver.switch_to.window(driver.window_handles[0])

    # 서류 등록 및 접수 완료 대상만 선택
    select = Select(driver.find_element(By.XPATH, '//*[@id="docuRegist"]'))
    select.select_by_visible_text('등록')
    select = Select(driver.find_element(By.XPATH, '//*[@id="acceptStat"]'))
    select.select_by_visible_text('접수완료')
    driver.find_element(By.XPATH, '//*[@id="btnSearch"]').click()  # 조회

    # START_PAGE
    page_num = START_PAGE

    # 맨끝자락 클릭
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/a[13]/img').click()
    # 마지막 숫자가져오기
    last_page = int(driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/strong').text)
    # 다시 첫번째 페이지로
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/a[1]/img').click()

    time.sleep(3)
    driver.execute_script('fn_list_pagging(' + str(page_num) + ');')  # START_PAGE로 이동
    time.sleep(3)

    # loop 시작
    while True:
        logger.info(f"page num: {page_num}")
        # 불량 리스트
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select('#tblAnnounce > tbody > tr')

        if len(table) < 2:  # 접수내역이 없을 시 리스트 추가
            logger.info(f"page num: {page_num} skipped")
            write_alert_list(f"page num: {page_num} skipped", page_num)

        for tbl_idx in range(len(table)):
            folder_init(DOWNLOAD_PATH)  # 한 명씩 DOWNLOAD_PATH를 비움
            try:
                time.sleep(1)
                driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/div[2]/table/tbody/tr[' + str(tbl_idx + 1) + ']/td[9]/img').click()
            except Exception as e:
                logger.info(f"{page_num} page 서류 접수 안되어 있음")
                continue

            # ################ Step 3: 팝업선택 및 이미지 다운로드 #####################
            driver.switch_to.window(driver.window_handles[1])  # popup창으로 이동
            popup = driver.page_source
            soup = BeautifulSoup(popup, "html.parser")
            image_count = soup.select(".photo > a > img")
            tr_count = soup.select("#userTable > tbody > tr")
            popup_name = driver.find_element(By.XPATH, '/html/body/form/div/table[1]/tbody/tr[1]/td[1]/span').text
            logger.info(f"driver name: {popup_name}")

            ###### 왜 있는지 모르겠는 부분 #######
            if len(tr_count) == 8:
                popup_license = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[8]/td[2]').text.replace("(검증성공)", "").strip()
                popup_phone = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[2]/td[1]').text.replace("-", "").strip()
            else:
                popup_license = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[8]/td[2]').text.replace("(검증성공)", "").strip()
                popup_phone = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[2]/td[1]').text.replace("-", "").strip()
            ###### 왜 있는지 모르겠는 부분 #######

            is_insert = find_value(popup_license + popup_phone[3:])
            if len(is_insert) == 0:  # DB에 저장되지 않음
                exist_image = False
                original_image_name = []  # 가족관계증명서, 사업자 등록증, etc

                # 각 이미지 다운로드
                for img_idx, img in enumerate(image_count):
                    logger.info("여기까지 왔음7.6")
                    try:
                        driver.find_element(By.XPATH, '/html/body/form/div/table[2]/tbody/tr/td/div['+str(img_idx+1)+']/span/a').click()
                        time.sleep(2)
                        original_image_name.append(img.get('alt'))
                        exist_image = True
                    except Exception as e:
                        logger.info(f"image download fail")
                        write_alert_list(f"image download fail {popup_name}", page_num)

                # 이미지가 존재하지 않을 시
                if not exist_image:
                    driver.switch_to.window(driver.window_handles[0])
                    write_alert_list(f"image not exist. name : {popup_name}", page_num)
                    logger.info(f"image not exist. name : {popup_name}")
                    continue  # 다음사람으로 넘어가기

                else:  # 정상 진행
                    driver.switch_to.window(driver.window_handles[1])
                # ############### Step 4: 이미지 OCR 및 Redact #####################
                # 한 사람이 업로드한 파일들을 모두 download한 후 실행
                images = find_image(DOWNLOAD_PATH)  # 파일 리스트 습득
                upload_list = []
                total_success_cnt = 0
                folder_name = datetime.today().strftime("%y%m%d%H%M%S")
                logger.info("여기까지 왔음7.8")
                logger.info(f"{images}")
                for img_idx, img in enumerate(images):
                    if img.endswith(UNSUPPORTED_FORMAT):
                        logger.info(f"{img} ocr 불가한 파일")
                        write_alert_list(f"{img} ocr 불가한 파일", page_num)
                        continue

                    logger.info("ocr api 시작")
                    response = call_api(path_join(DOWNLOAD_PATH, img))
                    logger.info("ocr api 끝")
                    try:
                        if len(response.json()['images'][0]['fields']) < 6:  # 해상도 낮은 이미지 읽었을 경우, OCR 인식된 text가 6개 미만
                            write_alert_list(img, page_num)
                            continue
                    except Exception as e:
                        logger.info(f"OCR 실패 {img}")
                        write_alert_list(img, page_num)
                        continue

                    original_path = path_join(DOWNLOAD_PATH, img)
                    temp_path = path_join(DOWNLOAD_PATH, f"image{img_idx}.jpg")
                    os.rename(original_path, temp_path)
                    try:
                        _file_key = popup_name + "_" + popup_phone
                        success_count, backup_dir = redact_image(response.json(), temp_path, _file_key, folder_name)
                        total_success_cnt += success_count
                    except Exception as e:
                        logger.info("fail redact_image")
                        logger.info(str(e))
                        write_alert_list(img, page_num)
                        if backup_dir:
                            os.rename(temp_path, backup_dir + original_image_name[img_idx])
                        continue
                    if backup_dir:
                        os.rename(temp_path, backup_dir + original_image_name[img_idx])

                    if success_count > 0:
                        logger.info(f"success_count: {success_count}")
                        upload_list.append(backup_dir + original_image_name[img_idx])

                    # ############### Step 5: 이미지 업로드  #####################
                for upload_idx, upload_file in enumerate(upload_list):
                    logger.info(str(os.path.splitext(upload_file)[0]) + " " + upload_file)
                    select = Select(driver.find_element(By.XPATH, '//*[@id="ordrNo"]'))

                    try:
                        select.select_by_index(upload_idx + 1)
                    except NoSuchElementException:
                        logger.info("can not upload")
                    try:
                        driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[9]/td/input[2]').send_keys(upload_file)
                    except NoSuchElementException:
                        logger.info("can not upload2")

                    driver.find_element(By.XPATH,'//*[@id="btnSave"]').click()
                    time.sleep(2)
                    alert = driver.switch_to.alert
                    alert.accept()

                driver.switch_to.window(driver.window_handles[1])
                driver.close()
                if len(is_insert) == 0:
                    if images:
                        try:
                            insert_value(popup_license + popup_phone[3:],
                                     popup_name, popup_phone,
                                     str(datetime.now()), LOGIN_ID, total_success_cnt, len(upload_list))
                        except Exception as e:
                            logger.info("insert error")
                    else:
                        write_alert_list(f"{popup_name} 이상한 파일 존재", page_num)
                else:
                    update_value(popup_license + popup_phone[3:])

            driver.switch_to.window(driver.window_handles[0])


        # ############### Step 7: 다음 페이지 이동 ###################
        page_num += 1
        if page_num > last_page:
            driver.close()
            break
        else:
            driver.execute_script('fn_list_pagging(' + str(page_num) + ');')  # 다음 page로 넘어가기

def main():
    init_db(DB_PATH, COPIED_DB_PATH)
    crawling_page()

    # 원본db와 copy가 같으면 copy 삭제
    is_equal = compare_databases(DB_PATH, COPIED_DB_PATH)
    if is_equal:
        os.remove(COPIED_DB_PATH)

    logger.info("Success")


main()
resultexcel()