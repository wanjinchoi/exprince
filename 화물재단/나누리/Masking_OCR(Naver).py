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

########### Log Setting ##################
NOW = datetime.today().strftime("%Y%M%d")
logger = logging.getLogger()
formatter = logging.Formatter('[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] >> %(message)s')
file_handler = logging.FileHandler('C:/storage/RPA/화물복지재단' + NOW + '.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.setLevel(level=logging.DEBUG)

# ########### path Setting ##################
path = 'C:/UserDummy'

def get_all_files_and_folders(root_dir):
    path_list = []

    for root, dirs, files in os.walk(root_dir):
        for name in files:
            modpath = os.path.join(root, name)
            modpath = modpath.replace('C:/backup\\','')
            modpath = modpath.replace('\\', '/')
            path_list.append(modpath)

    return path_list

def get_all_files_and_folders1(root_dir):
    path_list = []

    for root, dirs, files in os.walk(root_dir):
        for name in files:
            modpath = os.path.join(root, name)
            modpath = modpath.replace('C:/UserDummy\\','')
            modpath = modpath.replace('\\', '/')
            path_list.append(modpath)

    return path_list

def getdb(dbpath):
    if not os.path.exists(dbpath):
        conn = sqlite3.connect(dbpath)
        cursor = conn.cursor()
        cursor.execute('''
                    CREATE TABLE hwamool (
                        file_name TEXT,
                        maskingstatus TEXT,
                        date TEXT
                    )
                ''')
        conn.commit()
        conn.close()
    else:
        pass

def insert_paths_into_db(path_list, db_path, old_str, new_str):

    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            # 경로 문자열을 삽입합니다.
            for path in path_list:
                modified_path = path.replace(old_str, new_str, 1)
                modified_path = modified_path.replace('\\','/')
                query = "INSERT INTO hwamool (file_name, maskingstatus, date) VALUES (?, ?, ?)"
                maskingstatus = 1
                date = "20240808"
                cur.execute(query, (modified_path, maskingstatus, date))
            conn.commit()
    except sqlite3.Error as e:
        print(f"오류가 발생했습니다: {e}")

# 메인 실행 부분
backup_dir = 'C:/backup'
db_path = 'C:/storage/RPA/hwamool.db'
old_str = 'C:/backup'
new_str = 'C:/UserDummy'

paths = get_all_files_and_folders(backup_dir)
paths1 = get_all_files_and_folders1(new_str)

newpath = set(paths1) - set(paths)

# # ########### paritynumsetting ##################
def is_resident_registration_number(text):
    text = text.replace(' ', '')
    pattern1 = re.compile(r'\d{2}([0][1-9]|[1][0-2])([0][1-9]|[1-2]\d|[3][0-1])[-]*([1-4](\d|[*]){6}|[*]{7})')
    pattern2 = re.compile(r'[1-4](\d|[*]){6}')

    if bool(pattern1.match(text)):
        """
        990102-1234567
        990102-1******
        990102-*******
        """
        return True
    elif bool(pattern2.match(text)):
        """
        1234567
        1******
        """
        return 'half'
    else:
        return False

def highlight_resident_registration_number(image_path):
    image = cv2.imread(image_path)
    return image

# ########### DB Setting ##################

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
    go_path = file_path.replace('UserDummy','backup')
    folderpath = go_path.rfind('/')
    folderpath = go_path[:folderpath + 1]
    try:
        os.makedirs(folderpath)
    except:
        pass
    shutil.copy2(file_path, go_path)
    print("go_path", go_path)
    return file_path

def resultexcel(date):
    conn = sqlite3.connect('C:/storage/RPA/hwamool.db')
    df = pd.read_sql_query("SELECT * FROM hwamool", conn)
    hwamool = 'hwamool'+date
    df.to_excel('C:/storage/RPA/'+hwamool+'.xlsx',index=False)


def callAPI(file_path):
    api_url = 'https://hgy0v6wlvy.apigw.ntruss.com/custom/v1/13705/2cdaf3c233bced7e239d268ad566234a9a89e392b3eb9bb849e1fd58c1b75555/general'
    secret_key = 'dlR4WmRGVE1LZnRNSWdNRE1YS1ZQWEZPWGFwaHd6VXo='

    # 파일 읽기
    try:
        with open(file_path, 'rb') as f:
            file_data = f.read()
    except FileNotFoundError:
        print("File not found.")
        return 0

    # OCR 요청 데이터 생성
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
    headers = {
        'X-OCR-SECRET': secret_key,
        'Content-Type': 'application/json'
    }

    # OCR 요청
    try:
        response = requests.post(api_url, headers=headers, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("RequestException:", e)
        return 0

    # 응답 처리
    res_data = response.json()
    if res_data.get('images') is None:
        print("No OCR results found.")
        return 0

    ocr_results = res_data['images'][0].get('fields', [])
    maxtry = len(ocr_results)

    # 이미지에 OCR 결과 표시
    image = highlight_resident_registration_number(file_path)
    rectangle_count = 0

    for i in range(maxtry):
        text = ocr_results[i].get('inferText', '')
        points = ocr_results[i].get('boundingPoly', {}).get('vertices', [])

        ocrtext = is_resident_registration_number(text)
        if ocrtext == True:
            x_min = min(point['x'] for point in points)
            x_max = max(point['x'] for point in points)
            y_min = min(point['y'] for point in points)
            y_max = max(point['y'] for point in points)
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
            pts = [(point['x'], point['y']) for point in points]
            pts = np.array(pts, np.int32)
            pts = pts.reshape((-1, 1, 2))
            cv2.fillPoly(image, [pts], color=(255, 0, 0))
            rectangle_count += 1

    # 이미지 저장
    cv2.imwrite(file_path, image)

    return rectangle_count

def contains_korean(text):
    korean_pattern = re.compile("[\u3131-\u3163\uac00-\ud7a3]")
    return korean_pattern.search(text) is not None

def process_image_file(file_path, backup_date):
    print("file_path : ", file_path)
    file_path = 'C:/UserDummy/' + file_path
    print("new_file_path : ", file_path)

    findvalue = find_value(file_path)
    print("findValue", findvalue)
    if len(findvalue) == 0:
        try:
            x = backupfile(file_path)
            print("x", x)
            if contains_korean(os.path.basename(file_path)):
                file_name, file_extension = os.path.splitext(file_path)
                y = file_path.replace(file_name, 'sample2')
                try:
                    os.remove('sample2.jpg')
                    os.remove('sample2.jpeg')
                    os.remove('sample2.png')
                    os.remove('sample2.PNG')
                    os.remove('sample2.bmp')
                except:
                    pass
                os.rename(x, y)
                response = callAPI(y)
                insert_value(x, response, backup_date)
                os.rename(y, x)
            elif contains_korean(x):
                replaced_text = re.sub(r'[가-힣]+', 'sample2', x)
                shutil.move(x, replaced_text)
                response = callAPI(replaced_text)
                shutil.move(replaced_text, x)
                insert_value(x, response, backup_date)
            else:
                response = callAPI(x)
                insert_value(x, response, backup_date)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

def process_images_in_folder(__):
    backup_date = datetime.today().strftime("%Y%m%d%H%M")

    for i in newpath:
        process_image_file(i, backup_date)
    resultexcel(backup_date)

#############################################################
getdb(dbpath='C:/storage/RPA/hwamool.db')

try:
    os.makedirs('C:/UserDummy/sample')
except:
    pass

process_images_in_folder(newpath)
time.sleep(3)
os.rmdir('C:/UserDummy/sample')