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
import numpy as np

# ########### Log Setting ##################
NOW = datetime.today().strftime("%Y%M%d")
logger = logging.getLogger()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
file_handler = logging.FileHandler('C:/storage/RPA/화물복지재단' + NOW + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(level=logging.DEBUG)

# ########### path Setting ##################
path = 'C:/UserDummy'
# path = 'C:/storage/userdummy'



# ########### regex Setting ##################
korean_regex = re.compile('[ㄱ-ㅣ가-힣]+')

# ########### paritynumsetting ##################
def is_resident_registration_number(text):
    text = text.replace(' ', '')
    pattern = re.compile(r'\d+')
    text = ''.join(pattern.findall(text))  # 모든 숫자를 추출하여 하나의 문자열로 만듦

    if len(text) == 13:
        return True

    elif len(text) ==7:
        dd = int(text[4:6])
        # 성별 코드 검증
        if text[0] == '1' or '2' or '3' or '4':
            if (1 <= dd <= 31):  # 간단한 검증
                return 'half'
            else:
                return False
        return False
    else:
        return False


def highlight_resident_registration_number(image_path):
    image = cv2.imread(image_path)
    return image

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
    try:
        with sqlite3.connect('C:/storage/RPA/hwamool.db') as conn:
            # 커서 객체 생성
            cur = conn.cursor()
            query = "INSERT INTO hwamool (file_name, maskingstatus, date) VALUES (?, ?, ?)"
            cur.execute(query, (file_name, maskingstatus, date))
            # 트랜잭션 커밋
            conn.commit()
    except sqlite3.Error as e:
        print(e)

def find_value(pk):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    cur = conn.cursor()
    cur.execute("SELECT file_name FROM hwamool WHERE file_name = ?", (pk,))
    rows = cur.fetchall()
    conn.close()
    return rows

def backupfile(file_path):
    original_path = file_path.replace('\\','/')
    go_path = original_path.replace('UserDummy','backup')
    folderpath = go_path.rfind('/')
    folderpath = go_path[:folderpath + 1]
    try:
        os.makedirs(folderpath)
    except:
        pass

    shutil.copy2(original_path, go_path)
    print(go_path)

    return original_path

def resultexcel(date):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    df = pd.read_sql_query("SELECT * FROM hwamool", conn)
    hwamool = 'hwamool'+date
    df.to_excel('C:/storage/RPA/'+hwamool+'.xlsx',index=False)


def callAPI(file_path):
    API_URL = 'https://easyocr.argos-labs.com'
    TaskRequestUrl = '/ocr?api_token='
    TaskResultUrl = '/tasks/'
    Api_token = "eec91eda92ef8e1d1d176578df65f4a5"

    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(API_URL + TaskRequestUrl + Api_token, files=files)

    res_data = json.loads(response.text)
    task_id = res_data['task_id']
    while True:
        responseTask = requests.get(API_URL + TaskResultUrl + res_data['task_id'])
        task_result_data = json.loads(responseTask.text)
        waittime = 1
        if task_result_data['task_status'] == 'SUCCESS':
            task_result_text = task_result_data['task_result']
            print(task_result_text)
            break
        else:
            time.sleep(3)
            print(task_result_data['task_status'])
    maxtry = len(task_result_data['task_result']['results']['ocr_results'])

    image = highlight_resident_registration_number(file_path)
    rectangle_count = 0

    for i in range(maxtry):
        text = task_result_data['task_result']['results']['ocr_results'][i]['text']
        points = task_result_data['task_result']['results']['ocr_results'][i]['points']

        ocrtext = is_resident_registration_number(text)
        if ocrtext == True:
            x_min = min(point[0] for point in points)
            x_max = max(point[0] for point in points)
            y_min = min(point[1] for point in points)
            y_max = max(point[1] for point in points)
            front_length = int((x_max - x_min) * 0.5)

            pts = np.array([
                [x_min + front_length, y_min],
                [x_max, y_min],
                [x_max, y_max],
                [x_min + front_length, y_max]
            ], np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(image, [pts], color=(255, 0, 0))
            rectangle_count += 1
        elif ocrtext == 'half':
            pts = [(point[0], point[1]) for point in points]
            pts = np.array(pts, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(image, [pts], color=(255, 0, 0))
            rectangle_count += 1

        else:
            pass

    cv2.imwrite(file_path, image)

    return rectangle_count

def satisfies_condition(text):
    if '-' in text and text.count('-') == 1:
        replace_num = text.replace('-', '')
        if replace_num.isdigit() and len(replace_num) == 13:
            return True
    return False

def contains_korean(text):
    korean_pattern = re.compile("[\u3131-\u3163\uac00-\ud7a3]")
    return korean_pattern.search(text) is not None

def process_image_file(file_path, backup_date):
    original_path = file_path.replace('\\', '/')
    findvalue = find_value(original_path)
    print(findvalue)
    if len(findvalue) == 0:
        try:
            x = backupfile(file_path)
            print(x)
            if contains_korean(os.path.basename(file_path)):
                file_name, file_extension = os.path.splitext(file_path)
                y = file_path.replace(file_name, 'sample')
                try:
                    os.remove('sample.jpg')
                    os.remove('sample.jpeg')
                    os.remove('sample.png')
                    os.remove('sample.PNG')
                    os.remove('sample.bmp')
                except:
                    pass
                os.rename(x, y)
                response = callAPI(y)
                insert_value(x, response, backup_date)
                os.rename(y, x)
            elif contains_korean(x):
                replaced_text = re.sub(r'[가-힣]+', 'sample', x)
                shutil.move(x, replaced_text)
                response = callAPI(replaced_text)
                shutil.move(replaced_text, x)
                insert_value(x, response, backup_date)
            else:
                response = callAPI(x)
                insert_value(x, response, backup_date)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def process_images_in_folder(folder_path):
    backup_date = datetime.today().strftime("%Y%m%d%H%M")
    image_extensions = ('.jpg', '.png', '.jpeg', '.gif','.bmp')

    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith(image_extensions):
                file_path = os.path.join(root, file)
                process_image_file(file_path, backup_date)

        for dir in dirs:
            if contains_korean(dir):
                print(f"Directory contains Korean characters: {dir}")

            sub_dir_path = os.path.join(root, dir)
            for file in os.listdir(sub_dir_path):
                if file.lower().endswith(image_extensions):
                    file_path = os.path.join(sub_dir_path, file)
                    process_image_file(file_path, backup_date)

    resultexcel(backup_date)




#############################################################
getdb(dbpath='C:/storage/RPA/hwamool.db')

try:
    os.makedirs('C:/UserDummy/sample')
except:
    pass
process_images_in_folder(path)
time.sleep(3)
os.rmdir('C:/UserDummy/sample')

