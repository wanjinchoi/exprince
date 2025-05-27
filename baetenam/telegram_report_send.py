import requests
import json
from datetime import datetime, timedelta
import glob
import os
import yaml



def main(checklist):
    today_str = datetime.now().strftime('%Y-%m-%d')
    yaml_path = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    db_path = r"C:\ARGOSRPA\Master Service\GeneralService\database.db"
    txt_path = r'C:\ARGOSRPA\form\send_report_list.txt'
    report_path = f"C:\\ARGOSRPA\\report\\f{today_str}\\"
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        report_telegram = data['report_telegram']
        #텔레그램 토큰값
        telegram_bot_token = data['telegram_bot_token']
        #텔레그램 채팅방 id
        telegram_chat_id = data['telegram_chat_id']
        # 회사이름
        company_name = data['company_name']
        #device_role
        device_role = data['device_role']
        # 사진폴더
        detect_image_folder = r"C:\ARGOSRPA\Master Service\Master_image\detection_screenshots"
        # full_screen 폴더
        full_screen_shot_path = r"C:\ARGOSRPA\Master Service\Master_image\Full screen"
        #리포트 전송 폴더
    #오늘 날짜 가져오기
    target_filename = f"{today_str}_ARGOS_MDS_Report.xlsx"
    target_filename_in_txt = None
    #중복전송을 피하기 위해 텍스트 파일에 리포트 보냈는지 여부를 적어놓음
    with open(txt_path, 'r') as file:
        lines = file.readline()
            #각 줄을 읽어서 오늘 날짜의 파일이 있는지 확인
        for line in lines:
            line = line.strip()
            if target_filename in line:
                target_filename_in_txt ='Y'
            else:
                target_filename_in_txt = 'N'

        #검증 1단계 리포트 보낼지여부확인, 보낸적있는지 확인
        if report_telegram =='Y' and target_filename_in_txt =='N':
            send_report(telegram_chat_id, telegram_bot_token)



if __name__ == "__main__":
    main('aa')
