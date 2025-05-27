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
    def __init__(self, file_path):

        PySelenium.__init__(self, headless=True, url='https://www.google.com/',
                            browser='Chrome',
                            width='1200', height='800')
        # current_day = datetime.datetime.now().strftime('%Y-%m-%d')
        # timestamp 시작 시간
        self.start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        # PDF 저장 위치
        self.PDF_path = rf'C:\work\NST\1.Computer\output\sunil\{self.start_ts}'
        # VBA 모듈 위치
        self.vba_path = r'C:\work\NST\python\print_sunil.bas'
        # 출력 데이터 저장 파일
        self.save_path = r'C:\work\NST\1.Computer\save_data\Sunil_save_data.xlsx'
        #요청사항 폴더 삭제
        #요청사항 폴더 삭제
        self.result_path = r'C:\work\NST\선일'
        self.move_path = r'C:\work\NST\선일\endfile'
        today = datetime.datetime.now()
        yesterday = today - timedelta(days=1)

        # PDF 저장 폴더가 없으면 생성
        if not os.path.exists(self.PDF_path):
            os.makedirs(self.PDF_path)

        # sunil data 시간
        # self.data_time = data_time

        self.file_path = file_path
        file_list = sorted(glob.glob('C:\\work\\NST\\선일\\' + '*.xlsx'),key=os.path.getmtime)
        if len(file_list)==0:
            print('None')
        else:
            self.data_file = file_list[0]
            log_path = r'C:\work\NST\1.Computer\log\output\taeyang'
            if not os.path.exists(os.path.dirname(log_path)):
                os.makedirs(os.path.dirname(log_path))
            self.logger = get_logger(self.get_safe_path(log_path, 'output.log'),
                                     logsize=1024 * 1024 * 10)

    # ==============================================
    # 기존의 엑셀 파일에 데이터를 추가하는 함수 정의
    def append_to_excel(self, filtered_data,data,cutoff_time):
        # 새로운 데이터 프레임 생성
        df = pd.DataFrame(filtered_data)
        df2 = pd.DataFrame(data)
        # 엑셀 파일 읽기
        wb = openpyxl.load_workbook('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm',keep_vba=True)
        ws = wb['저장']
        #이전 품번
        previous_pum_number= None
        for (index1, row1), (index2, row2) in zip(df.iterrows(),df2.iterrows()):
            start_row = max((a.row for a in ws['D'] if a.value is not None)) + 1
            a = row1['선일 출고 일자']
            # 주어진 형식의 문자열을 datetime 객체로 변환
            date_object = datetime.datetime.strptime(str(a), '%Y%m%d')
            # 원하는 형식으로 출력
            formatted_date = date_object.strftime('%y/%#m/%d')
            #품명
            pum_name = row1['품명']
            #품번
            pum_number = row2['전 Lot 정보 - 품번']
            #규격
            standard = row1['규격']
            ###lot 번호
            lot_num = row2['업체 로트 번호']
            if pum_number == previous_pum_number:
                # 품번이 중복된 경우, I열에만 lot 번호 추가
                existing_value = ws['I' + str(start_row - 1)].value
                ws['I' + str(start_row - 1)].value = existing_value + '\n' + lot_num
                # I열의 개수를 계산하여 H열에 입력
                lot_count = len(ws['I' + str(start_row - 1)].value.split('\n'))
                ws['H' + str(start_row - 1)].value = lot_count
            else:
                # 품번이 중복되지 않은 경우, 새로운 행에 입력
                ws['A' + str(start_row)].value = formatted_date
                ws['B' + str(start_row)].value = '선일'
                # 품명
                ws['C' + str(start_row)].value = pum_name
                # 품번
                ws['D' + str(start_row)].value = pum_number
                # 규격
                ws['E' + str(start_row)].value = standard
                # lot 번호
                ws['I' + str(start_row)].value = lot_num
                # I열의 개수를 계산하여 H열에 입력 (새로 입력된 경우는 항상 1개)
                ws['H' + str(start_row)].value = 1

            # 현재 품번을 이전 품번으로 저장
            previous_pum_number = pum_number

        # 변경 사항 저장
        try:
            wb.save('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm')
        except Exception as e:
            print(f"Error occurred: {e}")
        # for (index1, row1), (index2, row2) in zip(df.iterrows(),df2.iterrows()):
        #     date_value = datetime.datetime.strptime(str(row1['선일 출고 일자']), '%Y%m%d').date()
        #     format_date = date_value.strftime('%y/%#m/%d')
        #     #중복없이 품번당 포트번호 묶기
        #     count_per_lot_number = df2.groupby("전 Lot 정보 - 품번")['업체 로트 번호'].nunique()
        #     if index2>0:
        #         a = df2.at[index2-1,'NST LOT No.']
        #         b = row2['NST LOT No.']
        #     else:
        #         a = 1
        #         b = 1
        #     #날짜형식 전환
        #     row_time = row1['선일 출고 시간'].strftime('%H:%M')
        #     #열의 최대치 구하기
        #     start_row = max((a.row for a in ws['A'] if a.value is not None)) + 1
        #     if index2 > 0 and str(ws.cell(row=start_row-1, column=4).value) == str(row2['전 Lot 정보 - 품번']) and a == b:
        #         ws.cell(row=start_row - 1, column=7).value = ws.cell(row=start_row - 1, column=7).value + '\r' + row2['업체 로트 번호']
        #         count = ws.cell(row=start_row - 1, column=7).value.split('\r')
        #         l_count = len(count)
        #         ws.cell(row=start_row - 1, column=6).value = l_count
        #         wb.save(self.save_path)
        #         wb.close()
        #     else:
        #         ws.cell(row=start_row, column=1).value = date_value
        #         ws.cell(row=start_row, column=2).value = '선일'
        #         ws.cell(row=start_row, column=3).value = row1['품명']
        #         ws.cell(row=start_row, column=4).value = row1['품번']
        #         ws.cell(row=start_row, column=5).value = row1['표면처리사양']
        #         ws.cell(row=start_row, column=6).value = 1
        #         ws.cell(row=start_row, column=7).value = row2['업체 로트 번호']
        #         wb.save(self.save_path)
        #         wb.close()
        #
        # # for pum, chel in count_per_lot_number.iteritems():
        # #         for i in range(2,start_row+1):
        # #             if str(ws['D'+str(i)].value) == str(pum):
        # #                 ws['F'+str(i)].value = str(chel)
        #
        #
        #
        # wb.save(self.save_path)
        flist = sorted(glob.glob(self.result_path +'\\' +'*.xlsx'), key=os.path.getmtime)
        if len(flist)>0:
            r_file=flist[0]
            a = r_file.split('\\')
            file_name = a[4]
            shutil.move(os.path.join(self.result_path,file_name), os.path.join(self.move_path,file_name))


    # ==============================================
    def csv_read(self):
        # sunil 데이터 excel 파일 읽기
        data_list = pd.read_excel(self.data_file, engine='openpyxl', header=1)

        # 서식표 Excel 파일 경로
        excel_file_path = self.file_path

        # 현재 시간 구하기
        #now = datetime.datetime.now()
        now = datetime.time(6, 17, 0)
        # 출고 시간 기준 설정 (예: 오전 10시)
        cutoff_time = datetime.time(23, 0, 0)
        cutoff_time2 = datetime.time(23, 0, 0)
        lunch_time = datetime.time(12, 0, 0)
        # 선일 출고 시간을 datetime 객체로 변환
        data_list['선일 출고 시간'] = pd.to_datetime(data_list['선일 출고 시간'], format='%H:%M').dt.time


        # 현재 시간이 오전 10시 이전인 경우
        if now < cutoff_time:
            filtered_data = data_list[data_list['선일 출고 시간'] < cutoff_time]

        #현재 시간이 오전 10시 이후인 경우
        else:
            #현재 시간이 14시 이전은 12시 이후부터
            if lunch_time < now< cutoff_time2:
                 filtered_data = data_list[data_list['선일 출고 시간'] < cutoff_time2]
            #현재 시간이 14시 이후
            elif now>= cutoff_time2:
                filtered_data = data_list[data_list['선일 출고 시간'] >= cutoff_time2]
            #10시 이후는
            else:
                filtered_data = data_list[data_list['선일 출고 시간'] > cutoff_time]



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


        df_result = pd.DataFrame(all_data, columns=fields_to_extract + ['업체 로트 번호'])
        df_result['NST LOT No.'] = df_result.groupby('전 Lot 정보 - 품번')['업체 로트 번호'].apply(lambda x: (x.str.split().str[0] != x.str.split().str[0].shift()).cumsum())
        grouped_data = df_result[['전 Lot 정보 - 품번', '업체 로트 번호','선일 출고 시간' ,'NST LOT No.']]


        #식별표 서식에 데이터 넣기
        for index, row in grouped_data.iterrows():
            # 파일 복사
            copy_path = self.PDF_path + f'\\{index}.xlsm'
            flist = sorted(glob.glob(self.PDF_path +'\\'+'*.xlsm'),key=os.path.getmtime)
            if len(flist)>0:
                previous_path = flist[len(flist)-1]
            #이전 파일 품번과 비교하기 위해

            #처음 한번은 입력
            if index == 0:
                shutil.copy(excel_file_path, copy_path)
                wb = openpyxl.load_workbook(copy_path, keep_vba=True)
                ws = wb['5대업체 식별표서식 (사용)']
                # 품번입력
                non_pattern = re.compile(r'\D')
                if ws['BI12'].value and '\n' in ws['BI12'].value:
                    ws['BI12'].value = None
                    # ws['AI23'].value = None
                if non_pattern.search(str(row['전 Lot 정보 - 품번'])):
                    ws['BE12'].value = row['전 Lot 정보 - 품번']
                else:
                    ws['BE12'].value = int(row['전 Lot 정보 - 품번'])

                # 데이터 회사명
                ws['BD12'] = '선일'

                # 그룹으로 묶여있는 업체 로트 번호 가져옴
                row_values = row['업체 로트 번호']
                # 업체 로트 번호 개수 저장
                # lot_num = row['lot_num']

                # ws['BE13'] = int(row['전 Lot 정보 - 품번'])
                # 철통 수량 - 업체 로트 번호의 개수
                # ws['BH12'].value = lot_num

                # 포트번호에 하나씩 쌓기
                if (ws['BI12'].value is not None):
                    ws['BI12'].value = ws['BI12'].value + '\n' + row_values
                    # ws['AI23'].value = ws['AI23'].value + '\n' + row_values
                else:
                    ws['BI12'].value = row_values
                    # ws['AI23'].value = row_values
                ws['BG12'].value = row['NST LOT No.']
                ws['BH12'].value = '1'
                wb.save(copy_path)

            else:
                #이전 입력 품번이랑 같은지 판단
                previous_value = grouped_data.at[index - 1, '전 Lot 정보 - 품번']
                previous_lot_no = grouped_data.at[index - 1, 'NST LOT No.']
                #조건 1 품번이 같냐?
                if (str(row['전 Lot 정보 - 품번']) == str(previous_value)) and (str(previous_lot_no) == str(row['NST LOT No.'])):
                        wb = openpyxl.load_workbook(previous_path, keep_vba=True)
                        ws = wb['5대업체 식별표서식 (사용)']
                        row_values = row['업체 로트 번호']
                        #로트번호 입력
                        ws['BI12'].value = ws['BI12'].value + '\n' + row_values
                        # ws['AI23'].value = ws['AI23'].value + '\n' + row_values
                        #로트번호 수 파악
                        lines = ws['BI12'].value.split('\n')
                        #철통수
                        ws['BH12'].value = str(len(lines))
                        wb.save(previous_path)
                        wb.close()
                # 이전 파일과 품번 및 LOT넘버가 같지 않을 때
                else:
                    shutil.copy(excel_file_path, copy_path)
                    wb = openpyxl.load_workbook(copy_path, keep_vba=True)
                    ws = wb['5대업체 식별표서식 (사용)']
                    previous_value = grouped_data.at[index - 1, '전 Lot 정보 - 품번']
                    previous_lot_no = grouped_data.at[index - 1, 'NST LOT No.']
                    non_pattern = re.compile(r'\D')
                    # 품번입력
                    if non_pattern.search(str(row['전 Lot 정보 - 품번'])):
                        ws['BE12'].value = row['전 Lot 정보 - 품번']
                    else:
                        ws['BE12'].value = int(row['전 Lot 정보 - 품번'])
                    #
                    ws['BD12'] = '선일'
                    row_values = row['업체 로트 번호']
                    ws['BI12'].value = row_values
                    # ws['AI23'].value = row_values
                    ws['BG12'].value = row['NST LOT No.']
                    #포트번호수
                    lines = ws['BI12'].value.split('\n')
                    # 철통수
                    ws['BH12'].value = str(len(lines))
                    wb.save(copy_path)


        self.file_print(self.PDF_path)
        self.append_to_excel(filtered_data,grouped_data,cutoff_time)
        #excel 닫기
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
            self.logger.error(e)
            print(e)
            return 1


# ==============================================
def do_start(file_path):
    with Output(file_path=file_path) as ws:
        ws.start()


# ==============================================
def main(file_path):
    do_start(file_path)

# ==============================================
def folder_remove():
    path = r"C:\work\NST\1.Computer\output\sunil"

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
    file_path = 'C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm'
    folder_remove()
    main(file_path)