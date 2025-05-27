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
import warnings
import glob
warnings.simplefilter("ignore")

####################################################
class Output(PySelenium):

    # ==============================================
    def __init__(self, file_path, data_time):
        PySelenium.__init__(self, headless=True, url='https://www.google.com/',
                            browser='Chrome',
                            width='1200', height='800')
        current_day = datetime.datetime.now().strftime('%Y-%m-%d')
        # timestamp 시작 시간
        self.start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        # PDF 저장 위치
        self.PDF_path = rf'C:\work\NST\1.Computer\output\taeyang\{self.start_ts}'
        # VBA 모듈 위치
        self.vba_path = r'C:\work\NST\python\print_sunil.bas'
        # 출력 데이터 저장 파일
        self.save_path = r'C:\work\NST\1.Computer\save_data\Sunil_save_data.xlsx'
        #요청사항 폴더 삭제
        self.result_path = r'C:\work\NST\태양'
        self.move_path = r'C:\work\NST\태양\endfile'

        today = datetime.datetime.now()
        yesterday = today - timedelta(days=1)

        # PDF 저장 폴더가 없으면 생성
        if not os.path.exists(self.PDF_path):
            os.makedirs(self.PDF_path)

        # sunil data 시간
        self.data_time = data_time

        self.file_path = file_path
        file_list = sorted(glob.glob('C:\\work\\NST\\태양\\' + '*.xlsx'),key=os.path.getmtime)
        self.data_file = file_list[0]
        log_path = r'C:\work\NST\1.Computer\log\output\taeyang'
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
        wb = openpyxl.load_workbook('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm',keep_vba=True)
        ws = wb['저장']
        previous_index = None
        for index, row in df.iterrows():
            start_row = max((a.row for a in ws['D'] if a.value is not None)) + 1
            a = row['발주일자']
            # 주어진 형식의 문자열을 datetime 객체로 변환
            date_object = datetime.datetime.strptime(a, '%Y/%m/%d')
            # 원하는 형식으로 출력
            formatted_date = date_object.strftime('%y/%#m/%d')

            if previous_index is None:
                ws['A' + str(start_row)].value = formatted_date
                ws['B' + str(start_row)].value = '태양'
                ws['C' + str(start_row)].value = row['품목명']
                ws['D' + str(start_row)].value = row['품목코드']
                ws['E' + str(start_row)].value = row['규격']
                ws['I' + str(start_row)].value = row['com_lot']
            else:
                code = row['품목코드']
                previous_code = data.at[previous_index, '품목코드']
                if code == previous_code:
                    # 기존 행에 'com_lot' 값 추가
                    ws['I' + str(start_row - 1)].value = ws['I' + str(start_row - 1)].value + '\n' + row['com_lot']
                    x = ws['I' + str(start_row - 1)].value.split('\n')
                    ws['H' + str(start_row - 1)].value = str(len(x))
                else:
                    ws['A' + str(start_row)].value = formatted_date
                    ws['B' + str(start_row)].value = '태양'
                    ws['C' + str(start_row)].value = row['품목명']
                    ws['D' + str(start_row)].value = row['품목코드']
                    ws['E' + str(start_row)].value = row['규격']
                    ws['I' + str(start_row)].value = row['com_lot']
            previous_index = index
        # 엑셀 파일 저장
        wb.save('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm')

        flist = sorted(glob.glob(self.result_path +'\\' +'*.xlsx'), key=os.path.getmtime)
        if len(flist)>0:
            r_file=flist[0]
            a = r_file.split('\\')
            file_name = a[4]
            shutil.move(os.path.join(self.result_path,file_name), os.path.join(self.move_path,file_name))
    # ==============================================
    def csv_read(self):
        # sunil 데이터 excel 파일 읽기
        excel_file_path = self.file_path

        # 엑셀 파일 읽기 (제목 행을 4번째 행으로 설정)
        data_list = pd.read_excel(self.data_file, header=3)

        # '품목코드', '품 목 명', '규    격', '작지번호', '발주중량', '발주일자' 열만 선택
        selected_columns = data_list[
            ['품목코드', '품 목 명', '규    격', '작지번호', '발주중량', '발주일자']]

        # '발주중량' 열을 float형으로 변환, 변환 불가능한 값은 NaN으로 처리
        selected_columns['발주중량'] = pd.to_numeric(selected_columns['발주중량'],errors='coerce')

        # com_lot 값을 저장할 빈 리스트 생성
        com_lot_list = []

        # Iterate over the rows and concatenate '로트번호' and '출고중량'
        for index, row in selected_columns.iterrows():
            com_lot = f"{row['작지번호']}    {row['발주중량']}"
            com_lot_list.append(com_lot)

        # Create a new DataFrame with '제품명', '제품코드', '규격', and 'com_lot' columns
        new_df = pd.DataFrame({
            '품목코드': selected_columns['품목코드'],
            '품목명': selected_columns['품 목 명'],
            '규격': selected_columns['규    격'],
            '작지번호':selected_columns['작지번호'],
            'com_lot': com_lot_list,
            '발주중량' : selected_columns['발주중량'],
            '발주일자' : selected_columns['발주일자']
        })

        filtered_df = new_df[new_df['품목코드'].notna()]
        print(filtered_df)
        new_df = filtered_df

        # for i in range(len(new_df['작지번호'])):
        #     if i == 0:  # 첫 번째 값인 경우
        #         lot_no.append(current_lot)
        #     elif new_df['작지번호']['발주중량'][i] == new_df['작지번호']['발주중량'][i - 1]:  # 이전 값과 같은 경우
        #         lot_no.append(
        #             lot_no[-2] if i >= 2 and new_df['작지번호'][i] == new_df['작지번호'][i - 2] else lot_no[-1])
        #     else:  # 이전 값과 다른 경우
        #         current_lot = 1  # 다시 1로 초기화
        #         lot_no.append(current_lot)

        # new_df['lot_no'] = lot_no

        # # 식별표 서식에 데이터 넣기
        for index, row in new_df.iterrows():
            # 파일 복사
            copy_path = self.PDF_path + f'\\{index}.xlsm'
            flist = sorted(glob.glob(self.PDF_path +'\\'+'*.xlsm'),key=os.path.getmtime)
            if len(flist)>0:
                previous_path = flist[len(flist)-1]
            #최초한번
            if index == 0:
                #처음 한번은 입력
                shutil.copy(excel_file_path, copy_path)
                wb = openpyxl.load_workbook(copy_path, keep_vba=True)
                ws = wb['5대업체 식별표서식 (사용)']
                # 업체이름
                ws['BD12'].value = '태양'
                x = row['품목코드'].replace(' ', '')
                #품번
                ws['BE12'].value = x
                #NST LOT No.
                ws['BG12'].value = '1'
                #철통수량
                ws['BH12'].value = '1'
                #업체로트번호 ==(작지번호+발주중량)
                ws['BI12'].value = row['com_lot']
                wb.save(copy_path)
                wb.close()
            else:
                #이전품목코드
                previous_product_code =new_df.at[index - 1, '품목코드']
                now_porduct_code = row['품목코드']
                #품목코드가 같으면 이전 파일 오픈
                if previous_product_code == now_porduct_code:
                    wb = openpyxl.load_workbook(previous_path, keep_vba=True)
                    ws = wb['5대업체 식별표서식 (사용)']
                    #작지번호랑 발주번호 입력
                    ws['BI12'].value = ws['BI12'].value + '\n' + row['com_lot']
                    lines = ws['BI12'].value.split('\n')
                    # 철통수
                    ws['BH12'].value = str(len(lines))
                    wb.save(previous_path)
                    wb.close()
                else:
                    shutil.copy(excel_file_path, copy_path)
                    wb = openpyxl.load_workbook(copy_path, keep_vba=True)
                    ws = wb['5대업체 식별표서식 (사용)']
                    # 업체이름
                    ws['BD12'].value = '태양'
                    x = row['품목코드'].replace(' ', '')
                    # 품번
                    ws['BE12'].value = x
                    # NST LOT No.
                    ws['BG12'].value = '1'
                    # 철통수량
                    ws['BH12'].value = '1'
                    # 업체로트번호 ==(작지번호+발주중량)
                    ws['BI12'].value = row['com_lot']
                    wb.save(copy_path)
        self.file_print(self.PDF_path)
        self.append_to_excel(new_df)
        # excel 닫기
        wb.close()

    # ==============================================
    def file_print(self,flist):
        flist = sorted(glob.glob(self.PDF_path+'\\' + '*.xlsm'),key=os.path.getmtime)
        for i in range(len(flist)):
            wb = openpyxl.load_workbook(flist[i], keep_vba=True)
            ws = wb['5대업체 식별표서식 (사용)']
            if int(ws['BH12'].value) > 0:
                # 한 면에 서식표 2개가 있어서 한 장 인쇄시에 서식표 2장 출력됨. 프린트 개수 계산하는 변수
                print_quantity = math.ceil(int(ws['BH12'].value) / 2)

                vba_path = self.vba_path
        # Excel 애플리케이션 시작
                excel_app = win32com.client.DispatchEx("Excel.Application")
        # excel_app.Visible = False  # Excel 창을 보이게 하려면 True로 설정
        # 새로운 워크북 생성 또는 기존의 워크북 열기
                workbook = excel_app.Workbooks.Open(flist[i])
        # # excel 새로 고침
        # # workbook.RefreshAll()
        # # workbook.Save()
        #
                # # 매크로 실행 - 서식표 인쇄 VBA 매크로
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
            print(e)
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
def folder_remove():
    path = r"C:\work\NST\1.Computer\output\taeyang"

    #폴더 정보 가져오기
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    #전체 폴더길이
    length = len(folders)
    if length > 1:
        # 1씩 감소
        for i in range(length):
            #폴더
            folder_path = os.path.join(path, folders[i])
            shutil.rmtree(folder_path)

    print("폴더삭제완료")

# ==============================================
if __name__ == '__main__':
    file_path = r'C:\work\NST\1.Computer\standard_form\5대업체 식별표서식2023.xlsm'
    data_time = '2024-02-28'
    folder_remove()
    main(file_path, data_time)