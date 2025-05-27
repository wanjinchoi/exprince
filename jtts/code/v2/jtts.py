"""
 :ver`1.0` :date`2021.06.09`
====================================
 :mod:`jtts.py`
====================================
.. main moduleauthor:: MyeongKook Park <myeongkook@argos-labs.com>
.. moduleauthor:: MinJung Kim <kkiminjj@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
#
#
# * MyeongKook Park
#
# Change Log
# --------
#  * [2022/11/17] Jeong Sunbin
#     - make_excel_file에서 파일 이름 기존 걸로 수정
#     - paid_list에서 i == 0 일 때는 pass, date가 빈 값일 때는 break 추가
#     - failure_list_return_list에서 "주석: # 엑셀 파일의 마지막 row까지 반복" 밑에 for문 range를 last_row에서 last_row+1로 수정
#  * [2022/11/15] MinJung
#     - 결제 실패 시, 결제 성공 파일의 데이터 삭제 및 수정 (vprice 추가)
#  * [2022/10/28] MinJung
#     - 재결제성공이 결제실패 파일에 있을 때 엑셀 날짜 파일 찾기 추가
#  * [2022/10/20] MinJung
#     - log 추가
#  * [2022/10/20] MinJung
#     - 재결제성공 시, 이전 날짜의 폴더가 존재하지 않으면 건너뛰기
#  * [2022/10/06] MinJung
#     - 어린이집, 학원, 지역아동센터, 유치원 한 파일에서 사용하게 통합
#  * [2022/10/06] MinJung
#     - 데이터가 없으면 엑셀에 데이터 쓰게 추가
#     - 엑셀 파일 없으면 생성 추가
#  * [2022/08/00] MinJung
#     - xlsx 폴더 잔여하면 삭제 추가
#  * [2022/09/00] MinJung
#     - 폴더 확인하여 없으면 생성 구간 추가
#####################################################
import shutil
import time

from dateutil.relativedelta import relativedelta
from win32com.client import Dispatch
from openpyxl import load_workbook
from datetime import datetime
from xlrd import open_workbook
from xls2xlsx import XLS2XLSX
import os

#####################################################
# 경로
month_path = r"C:\RPA\★월별출금내역"
last_char_zip = r"C:\RPA"
# 회계팀 PC 경로 테스트용
# month_path = r"C:\RPA\백업"
# last_char_zip = r"C:\RPA\백업"
# 테스트용
# month_path = r"C:\ARGOSRPA\test\월별 출금 내역\rpa"
# last_char_zip = r"C:\ARGOSRPA\test\세금계산서 작성\rpa"
# txt 링크
txt_path = r"C:\ARGOSRPA\code\txt\log.txt"
data = '\n\n================================='


# =======================================================
# 효성CMS에서 받은 결과로 어떤 실행을 할지 분류하고 처리 함수를 호출
def paid_list(date_paid_list, runday, info):
    # 시간
    runday = str(runday)
    make_log(txt_path, f"{runday} {info}")
    # 성공 추출하기
    extract_success_to_cms(date_paid_list, runday)
    workbook = open_workbook(date_paid_list)
    ws = workbook.sheet_by_index(0)
    # 데이터 개수 확인 부분
    if ws.nrows >= 100:
        maxrows = '100'
    else:
        maxrows = '0'
    exrows = ws.nrows - 2
    txt_data = f"paid_list maxrows: {exrows}"
    make_log(txt_path, txt_data)
    # 엑셀 데이터 붙여넣기
    for i in range(ws.nrows):
        # 결제일, 회원명, 공급가액, 부가세
        date = ws.cell_value(i, 1)
        name = ws.cell_value(i, 3)
        price = ws.cell_value(i, 14)
        tax = ws.cell_value(i, 15)
        if i == 0:
            pass
        elif date == '':
            break
        else:
            try:
                if '재결제성공' == ws.cell_value(i, 9):
                    txt_data = f"재결제성공, {name}"
                    make_log(txt_path, txt_data)
                    failure_list_return_list(name, date, price, runday, info, tax, maxrows)
                elif '결제실패' in ws.cell_value(i, 9):
                    # 결제실패(월 사용한도액 초과), 결제실패(잔액부족), 결제실패(출금불가계좌), 결제실패(해지된계좌), 결제실패, 재결제실패
                    txt_data = f"결제실패, {name}"
                    make_log(txt_path, txt_data)
                    move_to_failurelist(name, date, price, runday, info, tax, maxrows)
                elif '결제성공' in ws.cell_value(i, 9) and '재결제성공' not in ws.cell_value(i, 9):
                    # 결제성공 파일 중에서 안 적혀있으면 데이터 붙여넣기
                    txt_data = f"결제성공, {name}"
                    make_log(txt_path, txt_data)
                    move_to_successlist(name, date, price, runday, info, tax, maxrows)
            except Exception as e:
                txt_data = f"paid_list: {name}, {e}"
                print(f"paid_list: {name}, {e}")
                make_log(txt_path, txt_data)
    # 엑셀 파일 형식 변환
    xlsx2xls_path(runday, info)
    time.sleep(2)
    # 엑셀 파일 이동
    move_xls_file(runday, info)
    txt_data = "paid_list END\n\n"
    print("paid_list END")
    make_log(txt_path, txt_data)


# =======================================================
# cms결제성공내역에서 "성공"키워드로 추출한 리스트 반환
# return List
def extract_success_to_cms(path, runday):
    # 엑셀 파일 열기
    wb = open_workbook(path)
    ws = wb.sheet_by_index(0)
    # 설정
    result_list = []
    # 반복하며 데이터 리스트에 넣기
    for i in range(ws.nrows - 1):
        tmp = []
        if "성공" in ws.cell(i + 1, 9).value or "결제실패" in ws.cell(i + 1, 9).value:
            for j in range(20):
                tmp.append(ws.cell(i + 1, j).value)
            result_list.append(tmp)
    txt_data = "extract_success_to_cms END"
    make_log(txt_path, txt_data)
    # 해당 월별출금내역에 데이터 쓰기
    write_success_list(result_list, runday)


# =======================================================
# 출금내역 찾고 붙여넣기
def write_success_list(success_list, runday):
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    month = str(NOW - relativedelta(months=1)).split(" ")[0].split("-")[1]
    year = str(NOW.year)
    # 경로
    MONTH_DIRECTORY = month_path + "\\" + year + "년"
    # 엑셀 파일 제목 찾기
    file_name = find_file_name(MONTH_DIRECTORY, month + "월")
    # 없으면 월 앞에 0 빼고 찾아보기
    if file_name is None:
        month = str((NOW - relativedelta(months=1)).month)
        file_name = find_file_name(MONTH_DIRECTORY, month + "월")
    # 한달 전도 없으면 새로 생성
    if file_name is None:
        make_excel_file_month(MONTH_DIRECTORY, month, year)
        file_name = find_file_name(MONTH_DIRECTORY, month + "월")
    # 해당 엑셀 파일 열기 - 이거 작업 중에 종료하면 다음 실행 때 오류남. 해당 엑셀 파일 삭제 후 시도해줘야됨.
    wb = load_workbook(MONTH_DIRECTORY + "\\" + file_name)
    ws = wb.active
    # 출금내역 붙여넣기
    for i in success_list:
        ws.append(i)
    # 저장
    wb.save(MONTH_DIRECTORY + "\\" + file_name)
    txt_data = f"write_success_list: 월별 출금내역, {file_name} Done"
    make_log(txt_path, txt_data)


# =======================================================
# xls 를 xlsx 로 변환
def xls2xlsx_path(full_path, runday, info, ck):
    # 어린이집 여부 확인
    rundate = datetime.strptime(runday, "%Y%m%d")
    if info == '어린이집':
        wol = ""
        month_folder = "%Y.%m"
        count = 1
    else:
        # 시간
        month_folder = "%m"
        wol = "월"
        count = 0
    NOW = rundate - relativedelta(months=count)
    if ck == "old":
        NOW = rundate
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    # 경로
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # xlsx 폴더 안에 있으면 변환
    try:
        test = XLSX_DIRECTORY + "\\" + full_path.split("\\")[-1] + "x"
        XLS2XLSX(full_path).to_xlsx(test)
    # 파일이 없으면 생성 후 재시도
    except Exception as e:
        txt_data = f"xls2xlsx_path: {e}"
        make_log(txt_path, txt_data)
        if not os.path.exists(XLSX_DIRECTORY):
            os.mkdir(XLSX_DIRECTORY)
        XLS2XLSX(full_path).to_xlsx(XLSX_DIRECTORY + "\\" + full_path.split("\\")[-1] + "x")
    txt_data = "xls2xlsx_path END"
    make_log(txt_path, txt_data)


# =======================================================
# xlsx 폴더 안의 xls 폴더를 저장하기?
def xlsx2xls_path(runday, info):
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        count = 1
    else:
        month_folder = "%m"
        wol = "월"
        count = 0
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate - relativedelta(months=count)
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    # 경로
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # xlsx 폴더 안의 파일 찾기
    try:
        listdir = os.listdir(XLSX_DIRECTORY)
    # 없으면 폴더 생성 후 재시도
    except Exception as e:
        txt_data = f"xlsx2xls_path: {e}"
        make_log(txt_path, txt_data)
        os.mkdir(XLSX_DIRECTORY)
        listdir = os.listdir(XLSX_DIRECTORY)
    # 엑셀 dispatch로 시도하기?
    dispatch = Dispatch('Excel.Application')
    # 목록의 개수만큼 반복
    for i in listdir:
        if i.endswith('xls'):
            os.remove(XLSX_DIRECTORY + "\\" + i)
            continue
        add = dispatch.Workbooks.Add(XLSX_DIRECTORY + "\\" + i)
        add.SaveAs(XLSX_DIRECTORY + "\\" + i[:-1], FileFormat=56)
        dispatch.Quit()
    txt_data = "xlsx2xls_path END"
    make_log(txt_path, txt_data)


# =======================================================
# xlsx 를 xls의 각 계산서의 월별 폴더로 이동하기
def move_xls_file(runday, info):
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        count = 1
    else:
        month_folder = "%m"
        wol = "월"
        count = 0
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate - relativedelta(months=count)
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    # 경로
    XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # 파일 찾기
    listdir = os.listdir(XLSX_DIRECTORY)
    # 파일 이동하기 - 수정 해당 월만
    for i in listdir:
        if i.endswith("xls"):
            shutil.move(XLSX_DIRECTORY + "\\" + i, XLS_DIRECTORY + "\\" + i)
    # 이동한 파일 삭제하기
    shutil.rmtree(XLSX_DIRECTORY)
    txt_data = "move_xls_file END"
    make_log(txt_path, txt_data)


# =======================================================
# 결제성공 엑셀에서 실패한 내역 리스트를 추출
def move_to_failurelist(name, date, price, runday, info, tax, maxrows):
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        count = 1
    else:
        month_folder = "%m"
        wol = "월"
        count = 0
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate - relativedelta(months=count)
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    day = datetime.strftime(NOW, "%d")
    run = year + month + day
    fname = str(month) + str(day)
    noexcel = False
    # 경로
    XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # 파일 이름 찾기 - 당일 날짜 (date)
    file_name = find_file_name(XLS_DIRECTORY, date.replace("/", "")[4:])
    # 파일을 찾을 수 없으면 생성
    if file_name is None:
        # goto) 엑셀 파일 생성
        make_excel_file(XLS_DIRECTORY, year, month, day, runday, fname, info, maxrows)
        # 파일 이름 찾기
        file_name = find_file_name(XLS_DIRECTORY, fname)
        noexcel = True
    # 엑셀 파일 열기
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    except Exception as e:
        print(f"move_to_failurelist: {e}")
        ck = "new"
        dir = XLS_DIRECTORY + "\\" + file_name
        xls2xlsx_path(dir, runday, info, ck)
        time.sleep(2)
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    ws = wb.active
    # 마지막 열 찾기
    last_row = find_last_row(ws)
    # 설정
    FORM_FLAG = False
    append_row = []
    # 엑셀 파일 종류 검사: BG6가 "영수(01), 청구(02)" 여부 검사
    if ws['BG6'].value is None:
        # None이면 100건 이상 엑셀 파일
        jnum = 3
        vname = 'E'
        vprice = 'L'
        count = 51
        FORM_FLAG = True
    else:
        # 100건 미만 엑셀 파일
        jnum = 11
        vname = 'M'
        vprice = 'T'
        count = 59
        FORM_FLAG = False
    # 데이터 여부 확인 변수
    ck = 0

    # 기존에 입력된 값인지 확인하는 반복 작업
    for i in range(last_row):
        # 엑셀 파일의 공급자 상호와 엑셀 파일에서 추출한 이름 비교
        if ws[vname + str(i + 1)].value == name and ws[vprice + str(i + 1)].value == price:
            for j in range(count):
                # 원래 있던 열의 데이터를 추가
                append_row.append(ws.cell(i + 1, j + jnum).value)
            # 기존 데이터 삭제
            ws.delete_rows(i + 1)
            ck = 1

    # 기존에 입력된 값이 없으면 데이터 붙여넣기
    if ck == 0:
        # 행 - 수정 필요 및 마지막 열 맞는지 확인
        num = last_row + 1
        # 100건 이상인지 아닌지 확인
        ws['A' + str(num)] = '01'
        ws['B' + str(num)] = run
        # 100건 이상 엑셀 파일
        if FORM_FLAG:
            ws['E' + str(num)] = name
            ws['L' + str(num)] = price
            ws['M' + str(num)] = tax
            ws['N' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
            ws['O' + str(num)] = day
            ws['P' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
            ws['Q' + str(num)] = "개"
        # 100건 이하 엑셀 파일
        else:
            ws['C' + str(num)] = "1198678994"
            ws['E' + str(num)] = "㈜제이티통신"
            ws['F' + str(num)] = "이정태"
            ws['G' + str(num)] = "경기도 광명시 하안로 108,9층1호 에이스광명타워"
            ws['H' + str(num)] = "정보서비스"
            ws['I' + str(num)] = "컴퓨터시스템 통합 자문 및 구축"
            ws['J' + str(num)] = "jtc16444265@daum.net"
            ws['M' + str(num)] = name
            ws['T' + str(num)] = price
            ws['U' + str(num)] = tax
            ws['V' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
            ws['W' + str(num)] = day
            ws['X' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
            ws['Y' + str(num)] = "개"
        # 데이터 다시 가져오기
        for j in range(count):
            # 원래 있던 열에 추가
            append_row.append(ws.cell(num, j + jnum).value)
        # 삭제
        ws.delete_rows(num)
    wb.save(XLSX_DIRECTORY + "\\" + file_name + "x")
    append_failurelist(append_row, date, runday, info, maxrows, name, price)
    # 빈 파일이면 삭제: 결제 성공 엑셀 파일 없는데, 새롭게 데이터 넣어야돼서 생성했을 때 사용
    if noexcel and ck == 0:
        if os.path.exists(XLS_DIRECTORY + "\\" + file_name):
            os.remove(XLS_DIRECTORY + "\\" + file_name)
        if os.path.exists(XLSX_DIRECTORY + "\\" + file_name + "x"):
            os.remove(XLSX_DIRECTORY + "\\" + file_name + "x")
    txt_data = "move_to_failurelist END"
    make_log(txt_path, txt_data)


# =======================================================
# 상위 함수에서 추출된 리스트를 xx99.xlsx 실패내역 엑셀에 붙여넣기
def append_failurelist(fail_list, date, runday, info, maxrows, name, price):
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        count = 1
    else:
        month_folder = "%m"
        wol = "월"
        count = 0
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate - relativedelta(months=count)
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    # 경로
    XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # 설정
    ck = 0
    # 파일 이름 찾기: 99 - 당일 날짜 (rundate)
    failure_file_name = find_file_name(XLS_DIRECTORY, str(rundate.month) + str(99))
    if failure_file_name is None:
        year = datetime.strftime(NOW, "%Y")
        month = datetime.strftime(NOW, month_folder)
        day = datetime.strftime(NOW, "%d")
        # 경로
        XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
        # XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
        # 파일 이름 다시 찾기: 99 - 당일 날짜 (NOW)
        fname = str(NOW.month) + str(99)
        # 엑셀 파일 생성
        make_excel_file(XLS_DIRECTORY, year, month, day, runday, fname, info, maxrows)
        # 파일 이름 다시 찾기: 99 - 당일 날짜 (NOW)
        failure_file_name = find_file_name(XLS_DIRECTORY, str(NOW.month) + str(99))
    # 엑셀 헤더
    header = ['01', date.replace("/", ""), '1198678994', '', '㈜제이티통신', '이정태',
              '경기도 광명시 하안로 108,9층1호 에이스광명타워', '정보서비스', '컴퓨터시스템 통합 자문 및 구축',
              'jtc16444265@daum.net']
    # 엑셀 파일 열기
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + failure_file_name + "x")
    except Exception as e:
        txt_data = f"append_failurelist: {e}"
        make_log(txt_path, txt_data)
        dir = XLS_DIRECTORY + "\\" + failure_file_name
        xls2xlsx_path(dir, runday, info, ck)
        time.sleep(2)
        wb = load_workbook(XLSX_DIRECTORY + "\\" + failure_file_name + "x")
    ws = wb.active
    # 마지막 행 찾기
    last_row = find_last_row(ws)
    # 엑셀 파일 종류 검사: BG6가 "영수(01), 청구(02)" 여부 검사
    if ws['BG6'].value is None:
        # None이면 100건 이상 엑셀 파일
        jnum = 3
        hnum = 2
        vname = 'E'
        vprice = 'L'
        template = r"C:\ARGOSRPA\code\template 100.xls"
        # FORM_FLAG = True
    else:
        # 100건 미만 엑셀 파일
        jnum = 11
        hnum = len(header)
        vname = 'M'
        vprice = 'T'
        template = r"C:\ARGOSRPA\code\template.xls"
        # FORM_FLAG = False
    # 엑셀 파일의 마지막 row까지 반복
    for i in range(last_row):
        if ws[vname + str(i + 1)].value == name and ws[vprice + str(i + 1)].value == price:
            ck = 1
    # 데이터 붙여넣기
    if ck == 0:
        for i in range(len(fail_list)):
            ws.cell(last_row, i + jnum).value = fail_list[i]
        # 헤더 붙여넣기
        for j in range(hnum):
            ws.cell(last_row, j + 1).value = header[j]
    # 저장
    wb.save(XLSX_DIRECTORY + "\\" + failure_file_name + "x")
    txt_data = "append_failurelist END"
    make_log(txt_path, txt_data)


# =======================================================
# 재결제성공한 리스트를 xx99.파일에서 추출 - 수정된 버전
def failure_list_return_list(name, date, price, runday, info, tax, maxrows):
    # 목록
    # 폴더용
    dirlst = []
    flst = []
    runs = []
    years = []
    months = []
    days = []
    isExistrow = 'False'
    append_row = []
    ymds = []
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        start = 1
        end = 4
    else:
        month_folder = "%m"
        wol = "월"
        start = 0
        end = 3
    # 경로 반복 찾기 - 3달 전까지만
    for count in range(start, end):
        if isExistrow == 'False':
            # 시간 - 폴더용
            NOW = rundate - relativedelta(months=count)
            year = datetime.strftime(NOW, "%Y")
            month = datetime.strftime(NOW, month_folder)
            day = datetime.strftime(NOW, "%d")
            run = year + month[-2:] + day
            fmonth = NOW.month
            ymd = datetime.strftime(NOW, "%Y%m%d")
            # 시간 - 어린이집 파일용
            if info == '어린이집':
                N = NOW + relativedelta(months=1)
                fmonth = datetime.strftime(N, "%m")
                ymd = datetime.strftime(N, "%Y%m%d")
            # 경로
            XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
            XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
            # 파일 이름 찾기 - 출금 실패 - 당일 날짜 (fmonth)
            fname = str(fmonth) + str(99)
            # 이전 날짜의 폴더가 존재하지 않으면 건너뛰기
            if not os.path.exists(XLS_DIRECTORY):
                continue
            file_name = find_file_name(XLS_DIRECTORY, fname)
            # 리스트에 추가
            years.append(year)
            months.append(month)
            days.append(day)
            runs.append(run)
            dirlst.append(XLS_DIRECTORY)
            flst.append(fname)
            ymds.append(ymd)
            # 파일을 찾을 수 없으면 생성
            if file_name is None:
                if count == start:
                    # goto) 엑셀 파일 생성
                    month = fmonth
                    make_excel_file(XLS_DIRECTORY, year, month, day, runday, fname, info, maxrows)
                    continue
                else:
                    continue
            # 엑셀 파일 경로
            path = XLS_DIRECTORY + "\\xlsx" + "\\" + file_name + "x"
            # 폴더 열기
            try:
                wb = load_workbook(path)
            except Exception as e:
                txt_data = f"failure_list_return_list: {e}"
                make_log(txt_path, txt_data)
                ck = "old"
                if os.path.exists(XLS_DIRECTORY):
                    xls2xlsx_path(XLS_DIRECTORY + "\\" + file_name, run, info, ck)
                    time.sleep(2)
                    wb = load_workbook(path)
                else:
                    txt_data = 'no'
                    make_log(txt_path, txt_data)
            ws = wb.active
            # 마지막 열 찾기
            last_row = find_last_row(ws)
            # BG6가 "영수(01), 청구(02)" 여부 검사
            if ws['BG6'].value is None:
                # None이면 100건 이상 엑셀 파일
                jnum = 2
                vname = 'E'
                vprice = 'L'
                template = r"C:\ARGOSRPA\code\template 100.xls"
                big = '100건이상 '
                # FORM_FLAG = True
            else:
                # 100건 미만 엑셀 파일
                jnum = 10
                vname = 'M'
                vprice = 'T'
                template = r"C:\ARGOSRPA\code\template.xls"
                big = ''
                # FORM_FLAG = False
            # 엑셀 파일의 마지막 row까지 반복
            for i in range(last_row+1):
                if ws[vname + str(i + 1)].value == name and ws[vprice + str(i + 1)].value == price:
                    isExistrow = 'True'
                    txt_data = f"isExistrow {name} {count}달 전 데이터 있음"
                    make_log(txt_path, txt_data)
                    # 리스트에 데이터 넣기
                    for j in range(jnum, ws.max_column):
                        append_row.append(ws.cell(i + 1, j + 1).value)
                    append_row[12] = date.split("/")[-1]
                    ws.delete_rows(i + 1)
                    wb.save(path)
                    # 재결제 성공 붙여넣기
                    paid_paste_excel(append_row, dirlst[0] + '\\xlsx', ymds[0], years[0], months[0], days[0], info, maxrows, runday, count, start)
                    break
            # 폴더 존재 확인 후, 이전 달이면 삭제
            if count != start:
                if os.path.exists(path):
                    os.remove(path)
                if os.path.isdir(XLS_DIRECTORY + "\\xlsx"):
                    shutil.rmtree(XLS_DIRECTORY + "\\xlsx")
    if isExistrow == 'False':
        txt_data = f'isExistrow 3달 전까지 {name}이 없음'
        make_log(txt_path, txt_data)
        # 어린이집의 월 구분용 데이터
        month = months[0]
        # 파일 이름 찾기 - 성공
        fname = str(ymds[0][-4:])
        file_name = find_file_name(dirlst[0] + '\\xlsx', fname)
        # 파일을 찾을 수 없으면 생성 - 수정
        if file_name is None:
            # 엑셀 파일 생성
            make_excel_file(dirlst[0] + '\\xlsx', years[0], months[0], days[0], runday, fname, info, maxrows)
            # 파일 이름 찾기
            file_name = find_file_name(dirlst[0] + '\\xlsx', fname)
            # file_name = find_file_name(dirlst[0], date.replace("/", "")[4:])
            # 엑셀 파일 변환하기
            ck = 'new'
            xls2xlsx_path(dirlst[0] + '\\' + file_name, runday, info, ck)
            time.sleep(2)
        # 폴더 열기
        path = dirlst[0] + '\\' + 'xlsx' + '\\' + file_name + 'x'
        wb = load_workbook(path)
        ws = wb.active
        # 파일 새로 생성하고 제목에 재결제 성공이라고 적고, 3달 전까지 못찾았다는 메세지 남기기
        # 마지막 열 찾기
        last_row = find_last_row(ws)
        num = last_row
        # BG6가 "영수(01), 청구(02)" 여부 검사
        if ws['BG6'].value is None:
            # None이면 100건 이상 엑셀 파일
            FORM_FLAG = True
            jnum = 2
            vname = 'E'
            vprice = 'L'
            template = r"C:\ARGOSRPA\code\template 100.xls"
            big = '100건이상 '
            # FORM_FLAG = True

        else:
            # 100건 미만 엑셀 파일
            FORM_FLAG = False
            jnum = 10
            vname = 'M'
            vprice = 'T'
            template = r"C:\ARGOSRPA\code\template.xls"
            big = ''
        # 중복된 이름 있는지 찾기
        ck = 0
        for i in range(last_row - 7):
            if ws[vname + str(i + 7)].value == name and ws[vprice + str(i + 7)].value == price:
                ck = 1
        # 없으면 데이터 붙여넣기
        if ck == 0:
            # 100건 이상인지 아닌지 확인
            ws['A' + str(num)] = '01'
            ws['B' + str(num)] = ymds[0]
            # 100건 이상 엑셀 파일
            if FORM_FLAG:
                ws['E' + str(num)] = name
                ws['L' + str(num)] = price
                ws['M' + str(num)] = tax
                ws['N' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
                ws['O' + str(num)] = days[0]
                ws['P' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
                ws['Q' + str(num)] = "개"
            # 100건 이하 엑셀 파일
            else:
                ws['C' + str(num)] = "1198678994"
                ws['E' + str(num)] = "㈜제이티통신"
                ws['F' + str(num)] = "이정태"
                ws['G' + str(num)] = "경기도 광명시 하안로 108,9층1호 에이스광명타워"
                ws['H' + str(num)] = "정보서비스"
                ws['I' + str(num)] = "컴퓨터시스템 통합 자문 및 구축"
                ws['J' + str(num)] = "jtc16444265@daum.net"
                ws['M' + str(num)] = name
                ws['T' + str(num)] = price
                ws['U' + str(num)] = tax
                ws['V' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
                ws['W' + str(num)] = days[0]
                ws['X' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
                ws['Y' + str(num)] = "개"
            # 저장
            wb.save(path)
    txt_data = "failure_list_return_list END"
    make_log(txt_path, txt_data)


# =======================================================
# 상위 함수에서 추출된 리스트를 재결제성공한 날짜의 파일형식 맞게 붙여넣기
def paid_paste_excel(result_list, dirlst, ymd, year, month, day, info, maxrows, runday, count, start):
    # 기본 header
    # date.replace("/", "")
    header = ['01', ymd, '1198678994', '', '㈜제이티통신', '이정태',
              '경기도 광명시 하안로 108,9층1호 에이스광명타워', '정보서비스', '컴퓨터시스템 통합 자문 및 구축',
              'jtc16444265@daum.net']

    # 경로
    XLSX_DIRECTORY = dirlst
    # 파일 이름 찾기 - 성공
    fname = str(ymd[-4:])
    file_name = find_file_name(dirlst, fname)
    # 파일을 찾을 수 없으면 생성
    if file_name is None:
        # goto) 엑셀 파일 생성
        make_excel_file(dirlst, year, month, day, runday, fname, info, maxrows)
        # 파일 이름 찾기
        file_name = find_file_name(dirlst, fname)
        time.sleep(2)
    ck = "new"
    # # 3달 전 데이터인지 판별
    # if count == start:
    #     ck = "new"
    # else:
    #     ck = "old"
    # 파일 여부
    if os.path.exists(dirlst + "\\" + file_name + "x"):
        pass
    else:
        dir = dirlst + "\\" + file_name
        xls2xlsx_path(dir, runday, info, ck)
        time.sleep(2)
    # 엑셀 파일 열기
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    except Exception as e:
        txt_data = f"move_to_successlist: {e}"
        make_log(txt_path, txt_data)
        dir = dirlst + "\\" + file_name
        xls2xlsx_path(dir, runday, info, ck)
        time.sleep(2)
        # 엑셀 파일 읽고 불러오기
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    ws = wb.active

    # 설정
    FORM_FLAG = False
    # result_list에서 숫자 부분에 일자만 남기기
    # date.split("/")[-1]
    if result_list[20] is not None:
        result_list[20] = day
    if result_list[23] is not None:
        result_list[23] = day
    # 마지막 열 찾기
    last_row = find_last_row(ws)
    # 100건 여부 판별하기
    if ws['BG6'].value is None:
        # 100건 이상
        jnum = 3
        hnum = 2
        # FORM_FLAG = True
    else:
        # 100건 미만
        jnum = 11
        hnum = len(header)
        # FORM_FLAG = False
    # 목록의 개수만큼 반복진행
    for j in range(len(result_list)):
        ws.cell(last_row, j + jnum).value = result_list[j]
    # header 입력
    for i in range(hnum):
        ws.cell(last_row, i + 1).value = header[i]
    # 저장
    wb.save(dirlst + "\\" + file_name + "x")
    txt_data = "paid_paste_excel END"
    make_log(txt_path, txt_data)


# =======================================================
# 엑셀의 행에서 빈 값 삭제하기?
def init_row(ws):
    # 최대 값 설정
    max = ws.i
    # 반복하여 잔여 데이터 삭제
    for i in range(1, max):
        # None인데 6 이상일 때
        if ws['E' + str(i)].value is None and i >= 6:
            # 해당 열 삭제
            ws.delete_rows(i)


# =======================================================
# 마지막 행 반환 - 수정 100건 여부에 따라서?
def find_last_row(ws):
    # 엑셀 빈 값 판단하기?
    init_row(ws)
    # 설정
    last_row = 0
    excel_end = len(ws['E'])
    start = 1
    end = excel_end + 2
    # E에서 적힌 것만큼 반복
    for i in range(start, end):
        # None인데 6 이상일 때, 왜 i+2 할까 상단 이름 때문에?
        if ws['E' + str(i)].value is None and i >= 6:
            last_row = i
            break
    if last_row == 0:
        last_row = 7
    return last_row


# =======================================================
# 해당 날짜로 시작하는 파일명을 반환
def find_file_name(directory, date):
    # 파일명 목록 불러오기
    listdir = os.listdir(directory)
    # 폐원과 직점이 아닌 것 중에서 해당 날짜 파일 가져오기
    for i in listdir:
        if str(date) in i and "폐원" not in i and "직접" not in i:
            if "출금내역" not in i and i.endswith('xlsx') is True:
                continue
            return i


# =======================================================
# 결제 성공 파일이 없어서 새로 생성하면, 데이터가 없음으로 결제 성공 데이터를 넣어주기
def move_to_successlist(name, date, price, runday, info, tax, maxrows):
    # 어린이집 여부 확인
    if info == '어린이집':
        month_folder = "%Y.%m"
        wol = ""
        count = 1
    else:
        month_folder = "%m"
        wol = "월"
        count = 0
    # 시간
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate - relativedelta(months=count)
    year = datetime.strftime(NOW, "%Y")
    month = datetime.strftime(NOW, month_folder)
    day = datetime.strftime(NOW, "%d")
    run = year + month[-2:] + day
    fname = str(month[-2:]) + str(day)
    # 경로
    XLS_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol
    XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + "년" + "\\" + month + wol + "\\xlsx"
    # 파일 이름 찾기
    file_name = find_file_name(XLS_DIRECTORY, date.replace("/", "")[4:])
    # 파일을 찾을 수 없으면 생성
    if file_name is None:
        # goto) 엑셀 파일 생성
        make_excel_file(XLS_DIRECTORY, year, month, day, runday, fname, info, maxrows)
        # 파일 이름 찾기
        file_name = find_file_name(XLS_DIRECTORY, fname)
    # 파일 여부
    if os.path.exists(XLSX_DIRECTORY + "\\" + file_name + "x"):
        pass
    else:
        ck = "new"
        dir = XLS_DIRECTORY + "\\" + file_name
        xls2xlsx_path(dir, runday, info, ck)
        time.sleep(2)
    # # 엑셀 파일 열기
    # try:
    #     wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    # except Exception as e:
    #     txt_data = f"move_to_successlist: {e}"
    #     make_log(txt_path, txt_data)
    #     ck = "new"
    #     dir = XLS_DIRECTORY + "\\" + file_name
    #     xls2xlsx_path(dir, runday, info, ck)
    #     time.sleep(2)
    #     wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    # ws = wb.active
    # 엑셀 파일 없을 때 데이터 생성하는 부분, 요청사항에 없어서 시간이 더 오래 걸리니 주석처리 진행
    # # 마지막 열 찾기
    # last_row = find_last_row(ws)
    # # 설정
    # FORM_FLAG = False
    # append_row = []
    # # ck = 0
    # # 엑셀 파일 종류 검사: BG6가 "영수(01), 청구(02)" 여부 검사
    # if ws['BG6'].value is None:
    #     # None이면 100건 이상 엑셀 파일
    #     # jnum = 3
    #     vname = 'E'
    #     # count = 51
    #     FORM_FLAG = True
    # else:
    #     # 100건 미만 엑셀 파일
    #     # jnum = 11
    #     vname = 'M'
    #     # count = 59
    #     FORM_FLAG = False
    # # 기존에 입력된 값인지 확인하는 반복 작업
    # ck = 0
    # for i in range(last_row - 7):
    #     # 엑셀 파일의 공급자 상호와 엑셀 파일에서 추출한 이름 비교
    #     if ws[vname + str(i + 7)].value == name:
    #         ck = 1
    #         txt_data = "move_to_successlist: name data O"
    #         make_log(txt_path, txt_data)
    # if ck == 0:
    #     # 행
    #     num = last_row
    #     # 100건 이상인지 아닌지 확인
    #     ws['A' + str(num)] = '01'
    #     ws['B' + str(num)] = run
    #     # 100건 이상 엑셀 파일
    #     if FORM_FLAG:
    #         ws['E' + str(num)] = name
    #         ws['L' + str(num)] = price
    #         ws['M' + str(num)] = tax
    #         ws['N' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
    #         ws['O' + str(num)] = day
    #         ws['P' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
    #         ws['Q' + str(num)] = "개"
    #     # 100건 이하 엑셀 파일
    #     else:
    #         ws['C' + str(num)] = "1198678994"
    #         ws['E' + str(num)] = "㈜제이티통신"
    #         ws['F' + str(num)] = "이정태"
    #         ws['G' + str(num)] = "경기도 광명시 하안로 108,9층1호 에이스광명타워"
    #         ws['H' + str(num)] = "정보서비스"
    #         ws['I' + str(num)] = "컴퓨터시스템 통합 자문 및 구축"
    #         ws['J' + str(num)] = "jtc16444265@daum.net"
    #         ws['M' + str(num)] = name
    #         ws['T' + str(num)] = price
    #         ws['U' + str(num)] = tax
    #         ws['V' + str(num)] = "(기업은행) 333-048573-01-028 (주)제이티통신"
    #         ws['W' + str(num)] = day
    #         ws['X' + str(num)] = f"아이알리미(전자출결 시스템 서비스)_{month[-2:]}월"
    #         ws['Y' + str(num)] = "개"
    #     txt_data = "move_to_successlist: name data X"
    #     make_log(txt_path, txt_data)
    # # 저장
    # wb.save(XLSX_DIRECTORY + "\\" + file_name + "x")
    txt_data = f'move_to_successlist END'
    make_log(txt_path, txt_data)


# =======================================================
# xlsx 폴더가 월 폴더 안에 존재하면 삭제
def delete_xlsx_folder(cms_file_path, runday, info):
    try:
        # 어린이집 여부 확인
        if info == '어린이집':
            # month_folder = "%Y.%m"
            # wol = ""
            count = 1
        else:
            # month_folder = "%m"
            # wol = "월"
            count = 0
        # 목록
        num = []
        # 시간
        runday = str(runday)
        rundate = datetime.strptime(runday, "%Y%m%d")
        NOW = rundate - relativedelta(months=count)
        num.append(str(NOW).split(" ")[0].split("-")[1])  # 08월
        num.append(str(NOW.month))  # 8월
        # 년도 폴더
        year = str(rundate.year) + "년"
        # xlsx 폴더 있으면 지우기
        for n in num:
            if info == '어린이집':
                month = str(NOW.year) + "." + str(n)
            else:
                month = str(n) + "월"
            path = last_char_zip + f"\\{info}" + '\\' + year + '\\' + month + '\\' + 'xlsx'
            # 폴더 존재 확인 후, 삭제
            if os.path.exists(path):
                shutil.rmtree(path)
        txt_data = "delete_xlsx_folder END"
        make_log(txt_path, txt_data)
    # 혹시 모를 예외 사항을 위해서
    except Exception as e:
        txt_data = f"delete_xlsx_folder: {e}"
        make_log(txt_path, txt_data)
        pass


# =======================================================
# 사용하려는 폴더가 없으면 생성 및 파일 생성
def check_folder(cms_file_path, runday, info):
    try:
        # 어린이집 여부 확인
        if info == '어린이집':
            month_folder = "%Y.%m"
            wol = ""
            count = 1
        else:
            month_folder = "%m"
            wol = "월"
            count = 0
        # 시간
        rundate = datetime.strptime(runday, "%Y%m%d")
        NOW = rundate - relativedelta(months=count)
        # 경로
        year = datetime.strftime(NOW, "%Y") + "년"
        month = datetime.strftime(NOW, month_folder)
        m = datetime.strftime(NOW, "%m")
        ypath = last_char_zip + f"\\{info}" + "\\" + year
        mpath = last_char_zip + f"\\{info}" + "\\" + year + '\\' + month + wol
        XLSX_DIRECTORY = last_char_zip + f"\\{info}" + "\\" + year + '\\' + month + wol + "\\" + "xlsx"
        # 월별출금내역의 경로
        paths = r"C:\ARGOSRPA\code\월별 출금내역.xlsx"
        MONTH_DIRECTORY = month_path + "\\" + year
        # 세금계산서의 폴더를 찾고 없으면 생성
        # 년
        if not os.path.exists(ypath):
            os.mkdir(ypath)
        # 월
        if not os.path.exists(mpath):
            os.mkdir(mpath)
        # xlsx
        if not os.path.exists(XLSX_DIRECTORY):
            os.mkdir(XLSX_DIRECTORY)
        # 월별 출금 내역의 폴더를 찾고 없으면 생성
        # 년
        if not os.path.exists(MONTH_DIRECTORY):
            os.mkdir(MONTH_DIRECTORY)
        # 전월, 당월 파일 검사
        # 월의 0 제거
        mlst = []
        if not m == 12 or not m == 11 or not m == 10:
            m = m.replace('0', '')
        mlst.append(m)
        m2 = int(m) - 1
        mlst.append(m2)
        # 반복
        for i in mlst:
            mname = f'{year} {i}월 출금내역'
            mpath = MONTH_DIRECTORY + '\\' + mname + '.xlsx'
            if not os.path.isfile(mpath):
                shutil.copyfile(paths, mpath)
        txt_data = "check_folder END"
        make_log(txt_path, txt_data)
    # 혹시 모를 예외 사항을 위해서
    except Exception as e:
        txt_data = f"check_folder: {e}"
        make_log(txt_path, txt_data)
        pass


# =======================================================
# 엑셀 파일이 없으면 알맞은 제목으로 생성
def make_excel_file(XLS_DIRECTORY, year, month, day, runday, fname, info, maxrows):
    # 학원, 지역센터, 유치원 / 어린이집은 서로 엑셀 제목이 살짝 다르다
    # 100건 이상 이하 구분
    if '100건' in fname or '100' in maxrows:
        over = "100건이상 "
        template = r"C:\ARGOSRPA\code\template 100.xls"
    else:
        over = ""
        template = r"C:\ARGOSRPA\code\template.xls"
    # 어린이집 별 월
    count = len(str(month))
    if count > 2:
        month = month[-2:]
    # 월의 0 제거
    m = month
    if info == '어린이집':
        if not month == 12 or not month == 11 or not month == 10:
            m = month.replace('0', '')
    # 출금실패
    year_two = str(datetime.today().year)[2:]
    if '99' in fname:
        name = f"{month}99. {year_two}{month}99 {over}{info}계산서 ({m}월 서비스이용료) - 출금실패"
        if info == '어린이집':
            name = f"{runday[-4:-2]}99. {runday[-6:]} {over}청구지역 CMS전자세금계산서발행★ ({m}월분이용료) - 출금실패"
    else:
        name = f"{month}{day}. {year_two}{month}{day} {over}{info}계산서 ({m}월 서비스이용료)"
        if info == '어린이집':
            name = f"{runday[-4:]}. {runday[-6:]} {over}청구지역 CMS전자세금계산서발행★ ({m}월분이용료)"
    # 엑셀 파일 경로
    path = XLS_DIRECTORY + '\\' + name + '.xls'
    # 파일이 없으면 생성
    if not os.path.isfile(path):
        shutil.copyfile(template, path)
    txt_data = f'make_excel_file {name} END'
    make_log(txt_path, txt_data)


# =======================================================
# 월별 파일 없으면 생성
def make_excel_file_month(MONTH_DIRECTORY, month, year):
    # 엑셀 파일 경로
    name = f"{year}년 {month}월 출금내역"
    path = MONTH_DIRECTORY + '\\' + name + '.xlsx'
    template = r"C:\ARGOSRPA\code\월별 출금내역.xlsx"
    # 년도 폴더 없으면 생성
    if not os.path.exists(MONTH_DIRECTORY):
        os.makedirs(MONTH_DIRECTORY)
    # 파일이 없으면 생성
    if not os.path.isfile(path):
        shutil.copyfile(template, path)
    txt_data = f"make_excel_file_month {name} END"
    make_log(txt_path, txt_data)


# =======================================================
def make_log(txt_path, txt_data):
    try:
        if os.path.exists(txt_path):
            mode = 'a'
        else:
            mode = 'w'
        f = open(f"{txt_path}", f"{mode}")
        f.write(txt_data)
        f.write("\n")
        f.close()
    except Exception as e:
        print(f"make_log: {e}")


# =======================================================
def main(*args):
    try:
        make_log(txt_path, data)
        delete_xlsx_folder(*args)
        check_folder(*args)
        return paid_list(*args)
    except Exception as e:
        print(f"main: except {e}")


#########################################################
if __name__ == '__main__':
    main()
    # # 테스트용
    # date = "20221031"
    # name = "어린이집"
    # # 효성CMS경로, 시간(20220920), 종류(학원)
    # # rf"C:\ARGOSRPA\세금계산서발행\효성CMS엑셀\{date}_{date}_{name}.xls", f"{date}", f"{name}"
    # main(rf"C:\ARGOSRPA\세금계산서발행\효성CMS엑셀\{date}_{date}_{name}.xls", f"{date}", f"{name}")
