import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# SQLite DB 연결
db_path = r"C:\ARGOSRPA\Master Service\GeneralService\modbus.db"
conn = sqlite3.connect(db_path)

# 어제 날짜
yesterday = datetime.now() - timedelta(days=1)

# 어제 날짜 기준으로 그 주의 일요일과 토요일 구하기
start_of_week = (yesterday - timedelta(days=yesterday.weekday() + 1)).replace(hour=0, minute=0, second=0, microsecond=0)
end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

# SQL 쿼리 실행하여 그 주의 데이터만 가져오기
query = f"""
SELECT register_time, type, id, room, min_value, max_value, avg_value 
FROM min_max
WHERE register_time BETWEEN '{start_of_week}' AND '{end_of_week}';
"""
df = pd.read_sql_query(query, conn)

# 날짜 형식으로 변환
df['register_time'] = pd.to_datetime(df['register_time'])

# type, id, room 별로 그룹화하여 최소, 최대, 평균 계산
result = df.groupby(['type', 'id', 'room']).agg({
    'min_value': 'min',
    'max_value': 'max',
    'avg_value': lambda x: round(x.mean(), 1)  # 평균값 소숫점 첫째 자리까지
}).reset_index()

# 결과를 변수로 저장
grouped_data = {}

for _, row in result.iterrows():
    key = (row['type'], row['id'], row['room'])
    grouped_data[key] = {
        'min_value': row['min_value'],
        'max_value': row['max_value'],
        'avg_value': row['avg_value']
    }

# 데이터베이스 연결 종료
conn.close()

# 결과 출력 (필요시 사용 가능)
print(grouped_data)
