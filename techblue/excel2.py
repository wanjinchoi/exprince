from openpyxl import Workbook
import openpyxl
import pandas as pd
import datetime
import os


# 파일명에 날짜 붙이기 위한 설정
today = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
#엑셀파일 경로
excel_file_path = r'C:\Users\vivans\Desktop\테크제닉블루'
# 최종 엑셀 파일명
excel_file_name = f"{excel_file_path}\\주식거래자료_{today}.xlsx"
#로그파일 경로
log_file_path = os.path.join(excel_file_path, '변환로그.txt')

#양식경로
form_path = r'C:\Users\vivans\Desktop\테크제닉블루'

# 로그 기록 함수
def write_log(message):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file_path, 'a', encoding='utf-8') as log:
        log.write(f"[{timestamp}] {message}\n")




#기존에 만들었던 양식파일 가져오기
wb2 = openpyxl.load_workbook(f"{form_path}\\form.xlsx")
ws2 = wb2.active

#데이터 읽어오기
orgin_excel_path = f"{excel_file_path}\\주식거래자료.xlsx"
df = pd.read_excel(orgin_excel_path, engine='openpyxl')
write_log("기존 데이터 읽기 완료")
# 2행씩 묶어서 하나의 행으로 정리
merged_rows = []


### 엑셀 가공 2줄을 1줄로 만드는 코드
# 2씩 증가한다는 뜻
for i in range(1, len(df), 2):
    try:
        #특정행을 불러오는 코드
        #1행
        row1 = df.iloc[i]
        #2행
        row2 = df.iloc[i + 1]

        merged = [
            row1.get('구분', ''),
            row1.get('종목명', ''),
            row1.get('거래수량', ''),
            row1.get('매수일자', ''),
            row2.get('구분', ''),
            row2.get('종목명', ''),
            row2.get('거래수량', ''),
            row2.get('매수일자', ''),
            "대한민국증권" # 처리 칼럼
        ]
        merged_rows.append(merged)
    except Exception as e:
        write_log(f"병합 실패 at index {i}: {str(e)}")

# 병합된 데이터 한줄씩 엑셀에 추가
start_row = 2  # 2행부터 시작
for i, row in enumerate(merged_rows):
    for j, value in enumerate(row):
        ws2.cell(row=start_row + i, column=j + 1, value=value)
wb2.save(excel_file_name)
write_log("병합 데이터 엑셀 저장 완료")

