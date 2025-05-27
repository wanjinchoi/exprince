"""
====================================

====================================

Description
===========
식별표 서식 프린트 출력
"""
## Authors
# ===========
#
# yong seok Lee
#
#
#  * [2024/01/29]
#     - starting
####################################################

import shutil
import pandas as pd
import openpyxl
import os
import win32com.client
import math
import re
import datetime
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys
from openpyxl.styles import Alignment
from datetime import timedelta


####################################################
class Output(PySelenium):

    # ==============================================
    def __init__(self, file_path, data_time):

        PySelenium.__init__(self, headless=True, url='https://www.google.com/',
                            browser='Chrome',
                            width='1200', height='800')

        # timestamp 시작 시간
        self.start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        # PDF 저장 위치
        self.PDF_path = rf'C:\work\NST\1.Computer\output\{self.start_ts}'
        # VBA 모듈 위치
        self.vba_path = r'C:\work\NST\python\print_sunil.bas'
        # 출력 데이터 저장 파일
        self.save_path = r'C:\work\NST\1.Computer\save_data\Sunil_save_data.xlsx'
        # PDF 저장 폴더가 없으면 생성
        if not os.path.exists(self.PDF_path):
            os.makedirs(self.PDF_path)

        # sunil data 시간
        self.data_time = data_time

        self.file_path = file_path
        self.data_file = rf'C:\work\NST\1.Computer\sunil_data\{data_time}\SUNILDYFAS_IMGAGONG_LIST.xlsx'
        log_path = r'C:\work\NST\1.Computer\log\output'
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        self.logger = get_logger(self.get_safe_path(log_path, 'output.log'),
                                 logsize=1024 * 1024 * 10)

    # ==============================================
    # 기존의 엑셀 파일에 데이터를 추가하는 함수 정의
    def append_to_excel(self, data):
        # 새로운 데이터 프레임 생성
        df = pd.DataFrame(data)

        # 엑셀 파일 읽기
        wb = openpyxl.load_workbook(self.save_path)
        ws = wb.active

        # 엑셀 파일에 데이터 쓰기
        start_row = ws.i + 1  # 다음 빈 행 시작 지점
        for index, row in df.iterrows():
            date_value = datetime.datetime.strptime(str(row['선일 출고 일자'][0]), '%Y%m%d').date()
            ws.cell(row=start_row + index, column=1).value = date_value
            ws.cell(row=start_row + index, column=2).value = row['전 Lot 정보 - 품번']
            ws.cell(row=start_row + index, column=3).value = row['NST LOT No.']
            ws.cell(row=start_row + index, column=4).value = row['lot_num']
            lot_data = '\n'.join(map(str, row['업체 로트 번호']))
            # ws.cell(row=start_row + index, column=5).value = lot_data
            cell = ws.cell(row=start_row + index, column=5)
            cell.value = lot_data
            cell.alignment = Alignment(wrap_text=True)

        # 엑셀 파일 저장 - 파일 오픈 시 에러남
        wb.save(self.save_path)

    # ==============================================
    def csv_read(self):
        # sunil 데이터 excel 파일 읽기
        data_list = pd.read_excel(self.data_file, engine='openpyxl', header=1)

        # 서식표 Excel 파일 경로
        excel_file_path = self.file_path

        # 현재 시간 구하기
        now = datetime.datetime.now()
        # 출고 시간 기준 설정 (예: 오전 10시)
        cutoff_time = datetime.time(10, 0, 0)

        # 선일 출고 시간을 datetime 객체로 변환
        data_list['선일 출고 시간'] = pd.to_datetime(data_list['선일 출고 시간'], format='%H:%M').dt.time

        # 현재 시간이 오전 10시 이전인 경우
        if now.time() < cutoff_time:
            filtered_data = data_list[data_list['선일 출고 시간'] < cutoff_time]
        # 현재 시간이 오전 10시 이후인 경우
        else:
            filtered_data = data_list[data_list['선일 출고 시간'] >= cutoff_time]

        # 가져올 필드들의 열 이름 리스트
        fields_to_extract = ['선일 출고 일자', '선일 출고 시간', '전 Lot 정보 - 품번']
        all_data = []

        # 서식표 범위
        print_range = 'B1:AU32'

        # 업체 LOT 정보에 들어가는 필드 데이터 합치기
        for index, row in filtered_data.iterrows():
            # 3가지 필드 합침
            com_lot = f"{row['공정 정보 - Lot No']}    {row['전 Lot 정보 - 철통No']}    {int(row['전 Lot 정보 - 출고 중량'])}"

            # 합친 데이터
            ex_data = [row[field] for field in fields_to_extract]
            ex_data.append(com_lot)

            all_data.append(ex_data)

        # 저장 데이터 DataFrame 생성
        df_result = pd.DataFrame(all_data, columns=fields_to_extract + ['업체 로트 번호'])

        # 전 Lot 정보 - 품번이 동일한 경우 묶어서 데이터를 저장
        grouped_data = df_result.groupby('전 Lot 정보 - 품번').agg({
            '업체 로트 번호': lambda x: x.unique().tolist(),
            '선일 출고 일자': lambda x: x.unique().tolist()
        }).reset_index()

        # NST LOT No. 열 추가
        grouped_data['NST LOT No.'] = 0
        # lot_num 열 추가
        grouped_data['lot_num'] = grouped_data['업체 로트 번호'].apply(lambda x: len(x))
        # 좌표 지정
        coordinates = ['BE12', 'BH12', 'BI12']

        # 식별표 서식에 데이터 넣기
        for index, row in grouped_data.iterrows():
            # 파일 복사
            copy_path = self.PDF_path + f'\\{index}.xlsm'
            shutil.copy(excel_file_path, copy_path)
            wb = openpyxl.load_workbook(copy_path, keep_vba=True)
            ws = wb['5대업체 식별표서식 (사용)']

            # 데이터 회사명
            ws['BD12'] = '선일'
            # 그룹으로 묶여있는 업체 로트 번호 가져옴
            row_values = row['업체 로트 번호']
            # 업체 로트 번호 개수 저장
            lot_num = row['lot_num']
            # 로트 번호를 한 변수에 줄바꿈을 추가해서 저장
            combined_value = '\n'.join(map(str, row_values))

            # 정규 표현식을 사용하여 숫자 이외의 문자를 찾는다
            non_pattern = re.compile(r'\D')

            # 품번
            if non_pattern.search(str(row['전 Lot 정보 - 품번'])):
                ws['BE12'] = row['전 Lot 정보 - 품번']
            else:
                ws['BE12'] = int(row['전 Lot 정보 - 품번'])
            # ws['BE13'] = int(row['전 Lot 정보 - 품번'])
            # 철통 수량 - 업체 로트 번호의 개수
            ws['BH12'] = lot_num
            # 업체 로트 번호
            ws['BI12'] = combined_value

            # 데이터 하나 씩 넣어주는 방식
            # for col_num, field_value in enumerate(row, start=0):
            #     cell_coord = coordinates[col_num]
            #     ws[cell_coord] = field_value

            # 수식 활성화 - excel 함수 활성화
            ws_formula = wb['5대업체 식별표서식 (사용)']

            # Excel 파일 저장
            wb.save(excel_file_path)

            if lot_num > 0:
                # 한 면에 서식표 2개가 있어서 한 장 인쇄시에 서식표 2장 출력됨. 프린트 개수 계산하는 변수
                print_quantity = math.ceil(lot_num / 2)
                # 서식표 파일 인쇄
                self.file_print(print_quantity)

        self.append_to_excel(grouped_data)
        # excel 닫기
        wb.close()

    # ==============================================
    def file_print(self, print_quantity):
        excel_path = self.file_path
        vba_path = self.vba_path
        # Excel 애플리케이션 시작
        excel_app = win32com.client.Dispatch("Excel.Application")
        # excel_app.Visible = False  # Excel 창을 보이게 하려면 True로 설정
        # 새로운 워크북 생성 또는 기존의 워크북 열기
        workbook = excel_app.Workbooks.Open(excel_path)
        # excel 새로 고침
        # workbook.RefreshAll()
        # workbook.Save()

        # 매크로 실행 - 서식표 인쇄 VBA 매크로
        for _ in range(print_quantity):
            excel_app.Run('print_sunil.print_sunil')

        workbook.Close(SaveChanges=False)

        # Excel 어플리케이션 종료
        excel_app.Quit()

    # ==============================================
    def start(self):
        try:
            # csv 파일 읽기
            self.csv_read()

        except Exception as e:
            self.logger.error(e)
            return 1


# ==============================================
def do_start(file_path, data_time):
    with Output(file_path=file_path, data_time=data_time) as ws:
        ws.start()


# ==============================================
def main(file_path, data_time):
    do_start(file_path, data_time)


# ==============================================
if __name__ == '__main__':
    file_path = r'C:\work\NST\1.Computer\standard_form\5대업체 식별표서식2023.xlsm'
    data_time = '2024-02-05'
    main(file_path, data_time)
