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
        try:
            PySelenium.__init__(self, headless=True, url='https://www.google.com/',
                                browser='Chrome',
                                width='1200', height='800')
            current_day = datetime.datetime.now().strftime('%Y-%m-%d')
            # timestamp 시작 시간
            self.start_ts = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
            # PDF 저장 위치
            self.PDF_path = rf'C:\work\NST\1.Computer\output\chengwoo\{self.start_ts}'
            # VBA 모듈 위치
            self.vba_path = r'C:\work\NST\python\print_sunil.bas'
            # 출력 데이터 저장 파일
            self.save_path = r'C:\work\NST\1.Computer\save_data\Sunil_save_data.xlsx'
            #요청사항 폴더 삭제
            self.result_path = r'C:\work\NST\청우'
            self.move_path = r'C:\work\NST\청우\endfile'
            today = datetime.datetime.now()
            yesterday = today - timedelta(days=1)

            # PDF 저장 폴더가 없으면 생성
            if not os.path.exists(self.PDF_path):
                os.makedirs(self.PDF_path)

            # sunil data 시간
            self.data_time = data_time

            self.file_path = file_path
            file_list = sorted(glob.glob('C:\\work\\NST\\청우\\' + '*.xls'),key=os.path.getmtime)
            self.data_file = file_list[0]
            log_path = r'C:\work\NST\1.Computer\log\output'
            if not os.path.exists(os.path.dirname(log_path)):
                os.makedirs(os.path.dirname(log_path))
            self.logger = get_logger(self.get_safe_path(log_path, 'output.log'),
                                     logsize=1024 * 1024 * 10)
        except Exception as e:
            print(f"Error during initialization: {e}")

    # ==============================================
    # 기존의 엑셀 파일에 데이터를 추가하는 함수 정의
    def append_to_excel(self, data):
        try:
            # 새로운 데이터 프레임 생성
            df = pd.DataFrame(data)
            # 엑셀 파일 읽기
            wb = openpyxl.load_workbook('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm',keep_vba=True)
            ws = wb['저장']
            previous_index = None
            for index, row in df.iterrows():
                start_row = max((a.row for a in ws['D'] if a.value is not None)) + 1
                a = row['출고일']
                # 주어진 형식의 문자열을 datetime 객체로 변환
                date_object = datetime.datetime.strptime(a, '%Y-%m-%d')
                # 원하는 형식으로 출력
                formatted_date = date_object.strftime('%y/%#m/%d')
                if previous_index is None:
                    ws['A' + str(start_row)].value = formatted_date
                    ws['B' + str(start_row)].value = '청우'
                    ws['C' + str(start_row)].value = row['제품명']
                    ws['D' + str(start_row)].value = row['제품코드']
                    ws['E' + str(start_row)].value = row['규격']
                    ws['H' + str(start_row)].value = '1'
                    ws['I' + str(start_row)].value = row['com_lot']
                else:
                    code = row['제품코드']
                    prievious_code = df.at[previous_index, '제품코드']
                    if code == prievious_code:
                        ws['I' + str(start_row - 1)].value = ws['I' + str(start_row - 1)].value + '\n' + row['com_lot']
                        x = ws['I' + str(start_row - 1)].value.split('\n')
                        ws['H' + str(start_row - 1)].value = str(len(x))
                    else:
                        ws['A' + str(start_row)].value = formatted_date
                        ws['B' + str(start_row)].value = '청우'
                        ws['C' + str(start_row)].value = row['제품명']
                        ws['D' + str(start_row)].value = row['제품코드']
                        ws['E' + str(start_row)].value = row['규격']
                        ws['H' + str(start_row)].value = '1'
                        ws['I' + str(start_row)].value = row['com_lot']
                # 현재 인덱스를 이전 인덱스로 저장
                previous_index = index
            wb.save('C:\\work\\NST\\1.Computer\\standard_form\\5대업체 식별표서식2023.xlsm')
            wb.close()
            flist = sorted(glob.glob(self.result_path + '\\' + '*.xls'),key=os.path.getmtime)
            if len(flist) > 0:
                r_file = flist[0]
                a = r_file.split('\\')
                file_name = a[4]
                shutil.move(os.path.join(self.result_path, file_name),
                            os.path.join(self.move_path, file_name))
        except Exception as e:
            print(f"Error in append_to_excel: {e}")

    # ==============================================
    def csv_read(self):
        try:
            # sunil 데이터 excel 파일 읽기
            data_list = pd.read_excel(self.data_file)

            # 서식표 Excel 파일 경로
            excel_file_path = self.file_path

            # Select only the desired columns: '로트번호', '제품명', '제품코드', '규격', '출고중량'
            selected_columns = data_list[['로트번호', '제품명', '제품코드', '규격', '출고중량','출고일']]

            # Create an empty list to store com_lot values
            com_lot_list = []

            # Iterate over the rows and concatenate '로트번호' and '출고중량'
            for index, row in selected_columns.iterrows():
                com_lot = f"{row['로트번호']}    {row['출고중량']}"
                com_lot_list.append(com_lot)

            # Create a new DataFrame with '제품명', '제품코드', '규격', and 'com_lot' columns
            new_df = pd.DataFrame({
                '제품명': selected_columns['제품명'],
                '제품코드': selected_columns['제품코드'],
                '규격': selected_columns['규격'],
                'com_lot': com_lot_list,
                '출고일' : selected_columns['출고일'],
                '로트번호': selected_columns['로트번호']
            })
            # '규격'에 'M6*1.0P-L16'가 포함된 행과 '제품명'이 nan인 행을 필터링하여 제외
            pattern = 'M6\\*1\\.0P\\-L16'
            filtered_df = new_df[~new_df['규격'].str.contains(pattern, na=False) & new_df['제품명'].notna()]

            # 필터링된 데이터프레임 표시
            print(filtered_df)


            #식별표 서식에 데이터 넣기
            for index, row in filtered_df.iterrows():
                try:
                    # 파일 복사
                    copy_path = self.PDF_path + f'\\{index}.xlsm'
                    flist = sorted(glob.glob(self.PDF_path +'\\'+'*.xlsm'),key=os.path.getmtime)
                    if len(flist) > 0:
                        previous_path = flist[len(flist) - 1]
                    else:
                        previous_path = None

                    if index == 0 or previous_path is None:
                        #처음 한번은 입력
                        shutil.copy(excel_file_path, copy_path)
                        wb = openpyxl.load_workbook(copy_path, keep_vba=True)
                        ws = wb['5대업체 식별표서식 (사용)']
                        ws['BD12'].value = '청우'
                        #품번
                        try:
                            z = int(row['제품코드'])
                        except:
                            z = row['제품코드']
                        ws['BE12'].value = z
                        #NST LOT No.
                        ws['BG12'].value = '1'
                        ##철통수량
                        ws['BH12'].value = '1'
                        #업체 로트번호
                        ws['BI12'].value = row['com_lot']
                        wb.save(copy_path)
                        wb.close()
                    else:
                        previous_index = filtered_df.index[filtered_df.index.get_loc(index) - 1]
                        previous_product_code = filtered_df.loc[previous_index]['제품코드']
                        now_porduct_code = row['제품코드']
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
                            ws['BD12'].value = '청우'
                            # 품번
                            # product_code = row['제품코드']
                            # product_code = product_code.replace('FL','')
                            try:
                                z = int(row['제품코드'])
                            except:
                                z = row['제품코드']
                            ws['BE12'].value = z
                            # NST LOT No.
                            ws['BG12'].value = '1'
                            ##철통수량
                            ws['BH12'].value = '1'
                            # 업체 로트번호
                            ws['BI12'].value = row['com_lot']
                            wb.save(copy_path)
                except Exception as e:
                    print(f"Error processing row {index}: {e}")
            # self.file_print(self.PDF_path)
            self.append_to_excel(filtered_df)
            # # excel 닫기
            # wb.close()
        except Exception as e:
            print(f"Error in csv_read: {e}")

    # ==============================================
    def file_print(self,flist):
        try:
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
        except Exception as e:
            print(f"Error in file_print: {e}")

    # ==============================================
    def start(self):
        try:
            # csv 파일 읽기
            self.csv_read()
        except Exception as e:
            print(f"Error in start: {e}")
            self.logger.error(e)
            return 1

# ==============================================
def do_start(file_path, data_time):
    try:
        with Output(file_path=file_path, data_time=data_time) as ws:
            ws.start()
    except Exception as e:
        print(f"Error in do_start: {e}")

# ==============================================
def main(file_path, data_time):
    do_start(file_path, data_time)

# ==============================================
def folder_remove():
    try:
        path = r"C:\work\NST\1.Computer\output\chengwoo"

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
    except Exception as e:
        print(f"Error in folder_remove: {e}")

# ==============================================
if __name__ == '__main__':
    try:
        file_path = r'C:\work\NST\1.Computer\standard_form\5대업체 식별표서식2023.xlsm'
        data_time = '2024-02-28'
        folder_remove()
        main(file_path, data_time)
    except Exception as e:
        print(f"Error in __main__: {e}")
