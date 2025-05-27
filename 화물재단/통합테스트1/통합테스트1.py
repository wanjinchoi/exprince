from dateutil.relativedelta import relativedelta
from selenium.common.exceptions import NoSuchElementException, \
    NoAlertPresentException
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from openpyxl import load_workbook, Workbook
from datetime import date, timedelta
from selenium import webdriver
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
import re
import os
import pandas as pd

# ########### Log Setting ##################
NOW = datetime.today().strftime("%Y%M%d")
logger = logging.getLogger()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
file_handler = logging.FileHandler(r'C:\ARGOSRPA\log\\' + NOW + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(level=logging.DEBUG)

# ########## Sqlite Setting ##################
def resultexcel(date):
    conn = sqlite3.connect('C:/ARGOSRPA/db/fordriver.db')
    df = pd.read_sql_query("SELECT * FROM success", conn)
    success = 'success'+date
    df.to_excel('C:/ARGOSRPA/db/'+success+'.xlsx',index=False)

# SQLite DB 위치
DB_PATH = r"C:\ARGOSRPA\db\fordriver.db"


# 처리한 List는 DB에 저장
def insert_value(pk, name, phone, inert_date, login_id, maskingstatus,getimage):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    query = "INSERT INTO success VALUES(?, ?, ?, ?, ?,?)"
    cur.execute(query, (pk, name, phone, inert_date, login_id,maskingstatus,getimage))
    conn.commit()
    conn.close()
    logger.info("DB Insert Complete", name, phone)


# 검색한 List가 DB에 있는지 조회
def find_value(pk):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM success s WHERE s.pk =:pk", {"pk": pk})
    rows = cur.fetchall()
    conn.close()
    return rows


# 재업로드한 List를 처리한 뒤 DB업데이트
def update_value(pk):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE success SET success_date = '" + str(
        datetime.now().date()) + "' WHERE success.pk =:pk", {"pk": pk})
    conn.commit()
    conn.close()
    logger.info("DB Update Complete!", pk)


def folder_init(init_path):
    list_folder = os.listdir(init_path)
    for i in list_folder:
        os.remove(init_path + "\\" + i)
    logger.info("Download Folder init!")


# ########### Selenium Setting #################
warnings.filterwarnings("ignore", category=DeprecationWarning)
chromeOptions = webdriver.ChromeOptions()
prefs = {"download.default_directory": r"C:\ARGOSRPA\backup\download"}
chromeOptions.add_experimental_option("prefs", prefs)
# driver = webdriver.Chrome('C:/Users/user/Downloads/chromedriver.exe')
driver = webdriver.Chrome()
# ############ Variable Setting ################
yesterday = date.today() - timedelta(1)
SITE_ID = 'ber072'
SITE_PASSWORD = 'q654321@!'
SITE_ANNOUNCE = '건강검진사업'


# 두 개의 List를 diff 하여 중복되지 않는 리스트를 반환
def compareList(in_1, in_2):
    for i in in_1:
        for j in in_2:
            if i == j:
                in_2.remove(j)
    return in_2


# 이미지의 해상도가 떨어져 인식field가 적거나, 13자리의 숫자가 패리티체크에 실패한 경우
# 아래 엑셀에 정리하여 반환
def insertExcel(file_path, name, birth, Unreconize):
    try:
        workbook = load_workbook(file_path)
    except FileNotFoundError:
        workbook = Workbook()
    ws = workbook['Sheet1']
    i = 1
    while True:
        i += 1
        if ws.cell(row=i, column=1).value is not None:
            pass
        else:
            ws.cell(row=i, column=1).value = name
            ws.cell(row=i, column=2).value = birth
            ws.cell(row=i, column=3).value = Unreconize
            break
    try:
        workbook.save(file_path)
        return 0
    except Exception as e:
        print(e)
        return 1


# 폴더 내 .xlsx 확장자를 제외한 모든 파일을 리스트에 담어 반환
def findImage(folder_path):
    today = datetime.today().date()
    filtered_files = []
    listdir = os.listdir(folder_path)
    for i in listdir:
        file_path = os.path.join(folder_path, i)
        if os.path.isfile(file_path) and i.endswith(('.jpg', '.png','JPEG','JPG')):
            created_timestamp = os.path.getctime(file_path)
            created_date = datetime.fromtimestamp(created_timestamp).date()
            if created_date == today:
                filtered_files.append(i)
    return filtered_files


# 마스킹할 파일을 특정 폴더에 백업
def backupImage(path, key, filename, FOLDER_NAME):
    split_ = "/".join(path.split("\\")[:-2])
    try:
        listdir = os.listdir(
            split_ + "/" + key.replace("/", "_") + "_" + FOLDER_NAME + "/")
        for i in listdir:
            if i == filename + "." + path.split("\\")[-1].split(".")[-1]:
                raise FileExistsError
    except FileNotFoundError as e:
        os.makedirs(
            split_ + "/" + key.replace("/", "_") + "_" + FOLDER_NAME + "/")
        logger.warning(e, "Folder Generate")
    time.sleep(4)
    shutil.copy2(path, split_ + "/" + key.replace("/", "_") + "_" + FOLDER_NAME + "/" + filename + "." + path.split("\\")[-1].split(".")[-1])
    logger.info(key, filename, "Image Backup Complete")


# Json으로 받은 이미지 정보 중 하이픈을 포함한 문자열을 검사
# 숫자가 아닐 경우 -> Pass
# 13자리가 아닐 경우 -> Pass
# 주민등록번호 패리티 검사 로직
# 13자리의 숫자이며 패리티 검사에 성공 -> 숫자열의 가로, 세로 길이를 판단하여 서류가 세로인지 가로인지 판단/
# 총 길이의 30% 두께로 50%의 길이만 마스킹처리 (RPA를 이용한 마스킹은 파란색으로 처리 요청)
def redactImage(json_data, path, file_key, FOLDER_NAME):
    success_check = 0
    BACKUP_NAME = datetime.today().strftime("%y%m%d%H%M%S")
    for i in range(len(json_data['images'][0]['fields'])):
        id_num = json_data['images'][0]['fields'][i]['inferText']
        if '-' in id_num and id_num.count('-') == 1:
            coordinates = []
            replace_num = id_num.replace("-", "")
            if replace_num.isdigit():
                if len(replace_num) != 13:
                    continue
            else:
                continue
            s_i_n = list(replace_num)
            multiple = 2
            total = 0
            if int(s_i_n[2]+s_i_n[3]) > 12:
                continue
            for j in range(len(s_i_n) - 1):
                total = total + (int(s_i_n[j]) * multiple)
                multiple += 1
                if multiple > 9:
                    multiple = 2
            parity_check = 11 - (total % 11)
            if int(s_i_n[6]) == 5 or int(s_i_n[6]) == 6:
                parity_check = parity_check + 2
            if parity_check >= 10:
                parity_check = parity_check - 10
            if (int(s_i_n[-1]) == parity_check and 0 < int(s_i_n[6]) < 7 and int(
                    s_i_n[4] + s_i_n[
                        5]) < 32) or (int(s_i_n[0]) == 2 and int(s_i_n[6]) < 2):  # 패리티체크에 성공하고, 7번째 자리수가 6이하(외국인 주민번호 포함), 5~6번째 값이 31일 이하 인경우 주민번호로 판단
                try:
                    backupImage(path, file_key, BACKUP_NAME, FOLDER_NAME)
                except FileExistsError:
                    logger.warning(file_key, "Backup Image exist")
                    pass
                logger.info(id_num[:6], "ID detected")
                coordinates = [json_data['images'][0]['fields'][i]['boundingPoly']['vertices']]
            else:
                raise ValueError
            if abs(coordinates[0][0]['x'] - coordinates[0][2]['x']) > abs(
                    coordinates[0][0]['y'] - coordinates[0][2]['y']):
                coordinates_50_percentage = (coordinates[0][0]['x'] +
                                             coordinates[0][2]['x']) / 2
                logger.info("isVertical", coordinates)

                time.sleep(2)
                im = cv2.imread(path)
                cv2.rectangle(im, (
                int(coordinates_50_percentage), int(coordinates[0][0]['y'] - 10)), (
                              int(coordinates[0][2]['x']),
                              int(coordinates[0][2]['y'] + 10)), (255, 0, 0), -1)
                try:
                    cv2.imwrite(path, im)
                    logger.info(path, "Image Masking Complete")
                    success_check += 1
                except cv2.error as e:
                    logger.warning(e, "파일 경로에 한글은 입력할 수 없습니다.")
                    return 1
            elif abs(coordinates[0][0]['x'] - coordinates[0][2]['x']) < abs(coordinates[0][0]['y'] - coordinates[0][2]['y']):
                coordinates_50_percentage = (coordinates[0][0]['y'] +
                                             coordinates[0][2]['y']) / 2
                logger.info("isNotVertical", coordinates)
                time.sleep(2)
                im = cv2.imread(path)
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
                    cv2.imwrite(path, im)
                    logger.info(path, "Image Masking Complete")
                    success_check += 1
                except cv2.error as e:
                    logger.warning(e, "파일 경로에 한글은 입력할 수 없습니다.")
                    return 1
            else:
                pass
    return success_check


# OCR API에 이미지와 함께  요청, 이미지 인식하여 응답
def callAPI(file_path):
    api_url = 'https://hgy0v6wlvy.apigw.ntruss.com/custom/v1/13705/2cdaf3c233bced7e239d268ad566234a9a89e392b3eb9bb849e1fd58c1b75555/general'
    secret_key = 'dlR4WmRGVE1LZnRNSWdNRE1YS1ZQWEZPWGFwaHd6VXo='
    image_file = file_path
    try:
        with open(image_file, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
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

def crawlingPage(folder_path, login_id, login_pw, announce, announce_date):
    folder_init(folder_path)
    # 화물복지재단 접속 및 로그인
    driver.get("http://117.52.162.109/admin")  # 페이지 접속
    driver.find_element(By.XPATH, '//*[@id="id"]').send_keys(login_id)  # 아이디 입력 선택
    driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(login_pw)  # 패스워드 입력 선택
    driver.find_element(By.XPATH, '//*[@id="btnId"]').click()  # 로그인
    driver.implicitly_wait(10)  # 로딩 완료 대기

    # ################## Step 1: 화물 복지 재단 로그인  #####################

    driver.find_element(By.XPATH, '/html/body/div[2]/div[1]/div[4]/a[4]').click()  # 사업공고 및 마감 선택

    driver.find_element(By.XPATH,'/html/body/div[2]/div[2]/div[1]/div[2]/ul/li[6]/a').click()  # 신청서 이미지앨범 선택
    time.sleep(2)
    driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/div[1]/table/tbody/tr[1]/td[1]/img').click()  # 공고조회클릭
    driver.switch_to.window(driver.window_handles[1])  # 세컨드 윈도우 포커싱


    driver.find_element(By.XPATH,'/html/body/div[3]/form/div/table/tbody/tr[1]/td[1]/select').click()    #공고조회팝업-사업명
    driver.find_element(By.XPATH, '/html/body/div[3]/div/table/tbody/tr[3]/td[1]').click()


    driver.switch_to.window(driver.window_handles[0])
    driver.implicitly_wait(10)


    # ################## Step 1.5: 날짜 조회 기능  #####################

    select = Select(driver.find_element(By.XPATH, '//*[@id="docuRegist"]'))
    select.select_by_visible_text('등록')
    select = Select(driver.find_element(By.XPATH, '//*[@id="acceptStat"]'))
    select.select_by_visible_text('접수완료')

    start_date = datetime.strptime(announce_date, '%Y-%m-%d').date()
    # 시나리오는 공고일 ~ 실행일까지 실행
    # 실행 시간은 고려하지 않음
    driver.find_element(By.XPATH, '//*[@id="btnSearch"]').click()  # 조회
    # ################## Step 2: 사업공고 선택  #####################
    page_num = 1
    if successdb != 0:
        page_num = page_num + successdb * 10
        for i in range(successdb):
            driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/a[12]/img').click()
            time.sleep(2)
    else:
        pass

    while True:
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select('#tblAnnounce > tbody > tr')
        if len(table) < 2:  # 접수내역이 없을 시 시나리오 종료
            driver.implicitly_wait(10)  # 로딩 완료 대기
            logger.info("처리할 리스트 없음 시나리오 종료")
            break
        for i in range(len(table)):
            try:
                time.sleep(1)
                driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div[3]/form/div[2]/table/tbody/tr[' + str( i + 1) + ']/td[9]/img').click()
            except NoSuchElementException:
                continue

            # ################ Step 3: 팝업선택 및 이미지 다운로드 #####################
            driver.switch_to.window(driver.window_handles[1])
            popup = driver.page_source
            soup = BeautifulSoup(popup, "html.parser")
            image_count = soup.select(".photo > a > img")
            tr_count = soup.select("#userTable > tbody > tr")
            popup_name = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[1]/td[1]/span').text
            # popup_name = soup.select('#userTable > tbody > tr:nth-child(2) > td > span')[0].get_text()
            # temp_birth = \
            #     soup.select('#userTable > tbody > tr:nth-child(2) > td')[
            #         0].get_text()
            if len(tr_count) == 8:
                popup_license = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[8]/td[2]').text.replace(" (검증성공)", "")
                popup_phone = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[2]/td[1]').text.replace("-", "")
            else:
                popup_license = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[8]/td[2]').text.replace(" (검증성공)", "")
                popup_phone = driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[2]/td[1]').text.replace("-", "")
            # temp_birth = re.findall("\\d+", temp_birth)
            # popup_birth = "".join(temp_birth)

            isInsert = find_value(popup_license + popup_phone[3:])
            if len(isInsert) == 0:  # DB에 저장된적 없거나, 검색일이 DB기준일 보다 큰 경우 재업로드라 판단하여 재시작
                for j in range(len(image_count)):
                    list_1 = findImage('C:\\Users\\user\\Downloads')
                    driver.find_element(By.XPATH,'/html/body/form/div/table[2]/tbody/tr/td/div['+str(j+1)+']/span/a').click()
                    time.sleep(4)
                    list_2 = findImage('C:\\Users\\user\\Downloads')
                    compare_list = compareList(list_1, list_2)
                    try:
                        os.rename('C:\\Users\\user\\Downloads' + "\\" + compare_list[0],folder_path + "\\" + str(image_count[j]['alt']))
                    except IndexError as e:
                        print(e, "이미지 URL이 올바르지 않습니다.")
                        try:
                            alert = driver.switch_to.alert
                            alert.accept()
                        except NoAlertPresentException as e:
                            print(e)
                            continue
                driver.switch_to.window(driver.window_handles[1])

                # ############### Step 4: 이미지 OCR 및 Redact #####################
                time.sleep(5)
                images = findImage(folder_path)  # 파일 리스트 습득
                alert_list = []
                upload_list = []
                FOLDER_NAME = BACKUP_NAME = datetime.today().strftime("%y%m%d%H%M%S")
                for o in range(len(images)):
                    response = callAPI(folder_path + "\\" + images[o])
                    try:
                        if len(response.json()['images'][0]['fields']) < 6:  # 해상도 낮은 이미지 읽었을 경우
                            alert_list.append(images[o])
                            continue
                    except KeyError as e:
                        print("OCR 실패")
                        alert_list.append(images[o])
                        continue
                    else:
                        os.rename(folder_path + "\\" + images[o],
                                  folder_path + "\\image" + str(o) + ".jpg")
                        try:
                            sucess_check = redactImage(response.json(),
                                                       folder_path + "\\image" + str(
                                                           o) + ".jpg",
                                                       popup_name + "_" + popup_phone,
                                                       FOLDER_NAME)
                        except ValueError as e:
                            print(e, "패리티체크 실패")
                            alert_list.append(images[o])
                            os.rename(
                                folder_path + "\\image" + str(o) + ".jpg",
                                folder_path + "\\" + images[o])
                            continue
                        os.rename(folder_path + "\\image" + str(o) + ".jpg",
                                  folder_path + "\\" + images[o])
                    if sucess_check > 0:
                        upload_list.append(images[o])

                    # ############### Step 5: 이미지 업로드  #####################
                for k in upload_list:
                    print(os.path.splitext(k)[0], k)
                    select = Select(driver.find_element(By.XPATH, '//*[@id="ordrNo"]'))
                    try:
                        select.select_by_visible_text(os.path.splitext(k)[0])
                    except NoSuchElementException:
                        select.select_by_visible_text('재학증명서 (03월 21일 이후 발급분)')
                    try:
                        # driver.find_element(By.XPATH,'//*[@id="userTable"]/tbody/tr[8]/td/input[2]').send_keys(folder_path + "\\" + k)
                        driver.find_element(By.XPATH,'/html/body/form/div/table[1]/tbody/tr[9]/td/input[2]').send_keys(folder_path + "\\" + k)
                    except NoSuchElementException:
                        driver.find_element(By.XPATH,'//*[@id="userTable"]/tbody/tr[7]/td/input[2]').send_keys(folder_path + "\\" + k)
                    driver.find_element(By.XPATH,'//*[@id="btnSave"]').click()
                    time.sleep(2)
                    alert = driver.switch_to.alert
                    alert.accept()
                images = findImage(folder_path)
                getimage = len(images)
                for p in images:
                    os.remove(folder_path + "\\" + p)
                driver.switch_to.window(driver.window_handles[1])
                driver.implicitly_wait(10)  # 로딩 완료 대기
                driver.close()
                if len(isInsert) == 0:
                    insert_value(popup_license + popup_phone[3:],
                                 popup_name, popup_phone,
                                 str(datetime.now()), login_id,sucess_check,getimage)
                else:
                    update_value(popup_license + popup_phone[3:])
            driver.switch_to.window(driver.window_handles[0])


        # ############### Step 7: 다음 페이지 이동 ###################
        page_num += 1
        driver.execute_script('fn_list_pagging(' + str(page_num) + ');')
    driver.close()


def main(login_id, login_pw, announce, announce_date,successdb):
    FILE_PATH = r"C:\ARGOSRPA\backup\download"  # 이미지 파일 저장 경로
    crawlingPage(FILE_PATH, login_id, login_pw, announce, announce_date)

def getdb(dbpath):
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
    else:
        pass

getdb("C:/ARGOSRPA/db/fordriver.db")
connection = sqlite3.connect("C:/ARGOSRPA/db/fordriver.db")
query = "SELECT COUNT(*) FROM success"
order = pd.read_sql(query, connection)
successdb = order['COUNT(*)'][0]
successdb = int(successdb/100)


FILE_PATH = r"C:\ARGOSRPA\backup\download"  # 이미지 파일 저장 경로
login_id = 'ber072'
login_pw = 'q654321@!'
announce = '건강검진사업'
announce_date = '2024-01-24'
main( login_id, login_pw, announce, announce_date,successdb)
resultexcel(NOW)
