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
from PIL import Image


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
            modpath = modpath.replace('\\', '/')
            path_list.append(modpath)

    return path_list

def backupfile(file_path):
    go_path = file_path.replace('UserDummy','backup')
    folderpath = go_path.rfind('/')
    folderpath = go_path[:folderpath + 1]
    try:
        os.makedirs(folderpath)
    except:
        pass

    shutil.copy2(i, go_path)
    print(go_path)


# HEIC 파일을 JPG로 변환하는 함수
def convert_heic_to_jpg(heic_path):
    heif_file = pillow_heif.read_heif(heic_path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    output_path = heic_path.replace('.heic', '.jpg')
    image.save(output_path, 'JPEG')
    print(f'Converted {heic_path} to {output_path}')
    converted_files.append(output_path)


# PDF 파일을 JPG로 변환하는 함수
def convert_pdf_to_jpg(pdf_path):
    images = convert_from_path(pdf_path, poppler_path='C:/Release-22.07.0-0/poppler-24.07.0/Library/bin')
    for i, image in enumerate(images):
        output_path = f'{os.path.splitext(pdf_path)[0]}.jpg'
        image.save(output_path, 'JPEG')
        print(f'Converted {pdf_path} to {output_path}')
        converted_files.append(output_path)


# JFIF 파일을 JPG로 변환하는 함수
def convert_jfif_to_jpg(jfif_path):
    image = Image.open(jfif_path)
    output_path = jfif_path.replace('.jfif', '.jpg')
    image.save(output_path, 'JPEG')
    print(f'Converted {jfif_path} to {output_path}')
    converted_files.append(output_path)


# 파일을 JPG로 변환하는 메인 함수
def convert_to_jpg(file_path):
    _, file_ext = os.path.splitext(file_path)

    if file_ext.lower() == '.pdf':
        convert_pdf_to_jpg(file_path)
    elif file_ext.lower() == '.heic':
        convert_heic_to_jpg(file_path)
    elif file_ext.lower() == '.jfif':
        convert_jfif_to_jpg(file_path)
    else:
        print(f'Unsupported file type: {file_path}')



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

def highlight_resident_registration_number(image_path):
    image = cv2.imread(image_path)
    return image



def is_resident_registration_number(text):
    text = text.replace(' ', '')
    pattern = re.compile(r'\d+')
    text = ''.join(pattern.findall(text))  # 모든 숫자를 추출하여 하나의 문자열로 만듦

    if len(text) == 13:
        if 1 <= int(text[6]) <= 4 and int(text[10]+text[11]) <= 32 :
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







########################작업해야하는파일구하기
backup_dir = 'C:/backup'
db_path = 'C:/storage/RPA/hwamool.db'
old_str = 'C:/backup'
new_str = 'C:/UserDummy'
paths = get_all_files_and_folders(backup_dir)
paths1 = get_all_files_and_folders1(new_str)
newpath = set(paths1)-set(paths)
newpath = list(newpath)



def start(newpath):
    ###백업
    backupfile(newpath)
    ###변환
    convert_to_jpg(newpath)

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

    ###ocr
    callAPI(newpath)
########################



for i in newpath:
    start(i)

data = {'extension' : newpath,'afterextension' : converted_files}
df = pd.DataFrame(data)
df.to_excel('C:/storage/extensionlist.xlsx',index=False)