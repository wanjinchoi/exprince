import yaml
from datetime import datetime, timedelta
import os
import sqlite3


def query_db(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        ('files',))
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return [result[0] for result in results]

def main(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        yesterday_date = datetime.strptime(current_date_str,"%Y-%m-%d") - timedelta(days=1)
        yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
        data = yaml.safe_load(file)

        def ensure_time_format(time_value):
            if isinstance(time_value, int):
                return f"{time_value // 60:02}:{time_value % 60:02}"
            return time_value

        report_time_start = ensure_time_format(data['report_time_start'])
        report_time_end = ensure_time_format(data['report_time_end'])
        report_sendtime = ensure_time_format(data['report_sendtime'])

        start_time = datetime.strptime(report_time_start, "%H:%M").time()
        end_time = datetime.strptime(report_time_end, "%H:%M").time()
        send_time = datetime.strptime(report_sendtime, "%H:%M").time()
        # 리포트 받는 시간이 데이터 수집 시간보다 짧은경우 리포트 받는 시간에 맞춰서 데이터 조회
        if send_time < end_time:
            query = lambda field: f"""
                       SELECT {field}
                       FROM files
                       WHERE datetime(date || ' ' || time) >= '{yesterday_date_str} {data['report_time_start']}'
                       AND datetime(date || ' ' || time) <= '{current_date_str} {data['report_sendtime']}'
                       ORDER BY datetime(date || ' ' || time) ASC;
                       """
        # 하루
        elif start_time >= end_time:
            # 쿼리 수정: date와 time을 결합하여 정렬
            query = lambda field: f"""
                SELECT {field}
                FROM files
                WHERE datetime(date || ' ' || time) >= '{yesterday_date_str} {data['report_time_start']}'
                AND datetime(date || ' ' || time) <= '{current_date_str} {data['report_time_end']}'
                ORDER BY datetime(date || ' ' || time) ASC;
                """

        ##당일
        elif start_time < end_time:
            query = lambda field: f"""
                SELECT {field}
                FROM files
                WHERE datetime(date || ' ' || time) >= '{current_date_str} {data['report_time_start']}'
                AND datetime(date || ' ' || time) <= '{current_date_str} {data['report_time_end']}'
                ORDER BY datetime(date || ' ' || time) ASC;
                """
        data2 = {
            'screens': query_db('C:\\ARGOSRPA\\AROGS_DMS\\Master Service\\GeneralService\\database.db', query('screen')),
        }

        # 스크린수 알기
        unique_screens = list(set(data2['screens']))
        result_folder_path = os.path.join('C:\\ARGOSRPA\\report\\', current_date_str)
        if len(unique_screens) < 3:
            result_path = result_folder_path + '\\' + current_date_str + '_ARGOS_MDS_Report.xlsx'
        else:
            result_path = result_folder_path + '\\' + current_date_str + '_ARGOS_MDS_Report_monitor3.xlsx'


        type_change_report_sendtime = datetime.strptime(report_sendtime, "%H:%M").time()

        # 현재 날짜를 기준으로 report_sendtime의 datetime 객체 생성
        report_sendtime_datetime = datetime.combine(datetime.today(),type_change_report_sendtime)

        # report_sendtime의 5분 후 시간을 계산
        five_minutes_after_report_sendtime = report_sendtime_datetime + timedelta(minutes=5)

        # 현재 시간을 가져옴
        now = datetime.now()
        # 리포트 타임에서 5분사이에 현재시간이 있는 경우
        if report_sendtime_datetime <= now < five_minutes_after_report_sendtime:
            file_path = 'C:\\ARGOSRPA\\form\\send_report_list.txt'
            content = result_path
            try:
                with open(file_path, 'r') as file:
                    lines = [line.strip() for line in file.readlines()]
                    if content in lines:
                        print("exist")
            except FileNotFoundError:
                lines = []

            with open(file_path, 'a') as file:
                file.write(content + '\n')
        else:
            print('nottime')

if __name__ == "__main__":
    main('C:\\ARGOSRPA\\ARGOS.yaml')
