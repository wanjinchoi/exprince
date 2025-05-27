import requests
import json
import cv2
import shutil
import re
import os
import logging
from datetime import datetime
import base64
import uuid
import time
import sqlite3
import pandas as pd

# ########### Log Setting ##################
NOW = datetime.today().strftime("%Y%M%d")
logger = logging.getLogger()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
file_handler = logging.FileHandler('C:/storage/RPA/화물복지재단' + NOW + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(level=logging.DEBUG)

# ########### path Setting ##################
# path = 'C:/userdummy'
path = 'C:/storage/userdummy'



# ########### regex Setting ##################
korean_regex = re.compile('[ㄱ-ㅣ가-힣]+')

# ########### DB Setting ##################
def getdb(dbpath):
    if not os.path.exists(dbpath):
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE hwamool
        (file_name STRING,
        maskingstatus STRING,
        date STRING)''')
        conn.commit()
        conn.close()
    else:
        pass



def insert_value(file_name,  maskingstatus,date):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    cur = conn.cursor()
    query = "INSERT INTO hwamool VALUES(?,?,?)"
    cur.execute(query, (file_name,  maskingstatus, date))
    conn.commit()
    conn.close()

def find_value(pk):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    cur = conn.cursor()
    cur.execute("SELECT file_name FROM hwamool WHERE file_name = ?", (pk,))
    rows = cur.fetchall()
    conn.close()
    return rows

def backupfile(file_path):
    original_path = file_path.replace('\\','/')
    go_path = original_path.replace('userdummy','backup')
    folderpath = go_path.rfind('/')
    folderpath = go_path[:folderpath + 1]
    try:
        os.makedirs(folderpath)
    except:
        pass
    try:
        shutil.copy2(original_path, go_path)
    except:
        pass
    return original_path

def resultexcel(date):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    df = pd.read_sql_query("SELECT * FROM hwamool", conn)
    hwamool = 'hwamool'+date
    df.to_excel('C:/storage/RPA/'+hwamool+'.xlsx',index=False)


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

def redactImage(json_data, path):
    success_check = 0
    BACKUP_NAME = datetime.today().strftime("%y%m%d%H%M%S")
    for i in range(len(json_data['images'][0]['fields'])):
        id_num = json_data['images'][0]['fields'][i]['inferText']
        print(id_num)
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
            if int(s_i_n[2] + s_i_n[3]) > 12:
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
                        5]) < 32) or (int(s_i_n[0]) == 2 and int(
                s_i_n[6]) < 2):  # 패리티체크에 성공하고, 7번째 자리수가 6이하(외국인 주민번호 포함), 5~6번째 값이 31일 이하 인경우 주민번호로 판단
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
                coordinates_50_percentage = (coordinates[0][0]['x'] + coordinates[0][2]['x']) / 2
                logger.info("isVertical", coordinates)
                time.sleep(2)
                im = cv2.imread(path)
                cv2.rectangle(im, (int(coordinates_50_percentage), int(coordinates[0][0]['y'] - 10)), (int(coordinates[0][2]['x']),int(coordinates[0][2]['y'] + 10)), (255, 0, 0), -1)
                try:
                    cv2.imwrite(path, im)
                    logger.info(path, "Image Masking Complete")
                    success_check += 1
                except cv2.error as e:
                    logger.warning(e, "파일 경로에 한글은 입력할 수 없습니다.")
                    return 1
            elif abs(coordinates[0][0]['x'] - coordinates[0][2]['x']) < abs(
                    coordinates[0][0]['y'] - coordinates[0][2]['y']):
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
        pass
    return success_check
def backupdir(dir,root):
    original_path = root.replace('\\','/')
    go_path = original_path.replace('userdummy','backup')
    backupempty = go_path + '/' + dir
    os.makedirs(backupempty, exist_ok=True)
    return 0


def process_images_in_folder(folder_path):
    BACKUP_DATE = datetime.today().strftime("%Y%m%d%H%M")
    for root, dirs, files in os.walk(folder_path):
        if dirs == '':
            pass
        for dir in dirs:
            backupdir(dir,root)
        for file in files:

            if file.endswith(('.jpg', '.png','.JPG','.jpeg','.PNG','.JPEG','.GIF','.gif')):
                file_path = os.path.join(root, file)
                original_path = file_path.replace('\\', '/')
                findvalue = find_value(original_path)
                if len(findvalue) ==0:
                    x = backupfile(file_path)
                    response = callAPI(file_path)
                    check = redactImage(response.json(),file_path)
                    insert_value(x,check,BACKUP_DATE)
                else:
                    pass
    resultexcel(BACKUP_DATE)





getdb('C:/storage/RPA/hwamool.db')
process_images_in_folder(path)
#
# connection = sqlite3.connect("C:/Users/vivans/Desktop/화물복지재단/fordriver - backup240215.db")
# query = "SELECT COUNT(*) FROM success"
# order = pd.read_sql(query, connection)
# successdb = order['COUNT(*)'][0]
# successdb = int(successdb/100)






















