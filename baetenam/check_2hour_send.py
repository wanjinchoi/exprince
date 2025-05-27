from datetime import datetime, timedelta
import sqlite3
def main(yaml_path):
    # DB 경로 설정
    db_path = r'C:\ARGOSRPA\Master Service\GeneralService\database.db'

    # DB 연결 및 최신 date와 time 가져오기
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = "SELECT date, time FROM files ORDER BY date DESC, time DESC LIMIT 1"
    cursor.execute(query)
    latest_record = cursor.fetchone()
    conn.close()

    # 현재 시간 가져오기
    current_time = datetime.now()

    # 최신 기록을 datetime 형식으로 변환
    record_time = datetime.strptime(f"{latest_record[0]} {latest_record[1]}",'%Y-%m-%d %H:%M:%S')

    # 시간 차이 계산
    time_difference = current_time - record_time
    two_hours = timedelta(hours=2)

    # 2시간 이상 차이나는지 확인
    difference_is_more_than_2_hours = time_difference > two_hours
    if time_difference > two_hours:



if __name__ == "__main__":
    main(r'C:\ARGOSRPA\ARGOS.yaml')

