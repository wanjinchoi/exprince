import glob
import os
from datetime import datetime, timedelta
import yaml

def load_config(yaml_path):
    # yaml 파일읽어서 경로랑 시간 가져오기
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    return {
        'report_time_start': data['report_time_start'],
        'report_time_end': data['report_time_end'],
        'report_sendtime': data['report_sendtime'],
    }




def main(yaml_path):
    config = load_config(yaml_path)
    type_change_report_sendtime = datetime.strptime(config['report_sendtime'],"%H:%M").time()
    # 현재 날짜를 기준으로 report_sendtime의 datetime 객체 생성
    report_sendtime_datetime = datetime.combine(datetime.today(), type_change_report_sendtime)

    # report_sendtime의 5분 후 시간을 계산
    five_minutes_after_report_sendtime = report_sendtime_datetime + timedelta( minutes=5)

    # 현재 시간을 가져옴
    now = datetime.now()

    # 리포트 타임에서 5분사이에 현재시간이 있는 경우
    if report_sendtime_datetime <= now < five_minutes_after_report_sendtime:
        result ='Y'
        return  result
    else:
        result ='N'
        return result


if __name__ == "__main__":
    main(r'C:\ArgosRpa\detection.yaml')

