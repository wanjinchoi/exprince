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

        if task_result_data['task_status'] == 'SUCCESS':
            task_result_text = task_result_data['task_result']['text']
            print(task_result_text)
            break
        else:
            print(task_result_data['task_status'])
            time.sleep(3)


    return task_result_data

def satisfies_condition(text):
    if '-' in text and text.count('-') == 1:
        replace_num = text.replace('-', '')
        if replace_num.isdigit() and len(replace_num) == 13:
            return True
    return False

def redactImage(task_result_data, path):
    success_check = 0
    try:
        maxtry = len(task_result_data['task_result']['results']['ocr_results'])
        for i in range(maxtry):
            ocrnum = task_result_data['task_result']['results']['ocr_results'][i]['text']
            print(ocrnum)
        pass


    except Exception as e:
        logger.info(e, coordinates)
        pass
    return success_check


def contains_korean(text):
    korean_pattern = re.compile("[\u3131-\u3163\uac00-\ud7a3]")
    return korean_pattern.search(text) is not None

def process_images_in_folder(folder_path):
    BACKUP_DATE = datetime.today().strftime("%Y%m%d%H%M")
    for root, dirs, files in os.walk(folder_path):
        if dirs == []:
            for file in files:
                if file.endswith(('.jpg', '.png', '.JPG', '.jpeg', '.PNG', '.JPEG', '.GIF', '.gif')):
                    file_path = os.path.join(root, file)
                    original_path = file_path.replace('\\', '/')
                    findvalue = find_value(original_path)
                    if len(findvalue) == 0:
                        x = backupfile(file_path)
                        response = callAPI(file_path)
                        check = redactImage(response, file_path)
                        insert_value(x, check, BACKUP_DATE)
                    else:
                        pass
            pass
        else:
            for dir in dirs:
                if contains_korean(dir) :
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


getdb(dbpath='C:/storage/RPA/hwamool.db')



process_images_in_folder(path)

