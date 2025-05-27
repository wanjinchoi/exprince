import shutil
import time

from dateutil.relativedelta import relativedelta
from win32com.client import Dispatch
from openpyxl import load_workbook
from datetime import datetime
from xlrd import open_workbook
from xls2xlsx import XLS2XLSX
import os


# last_char_zip = r"C:\Users\Myeongkook Park\PycharmProjects\ts-python\JTTS\tmp\excelFolder\RPA\학원"
# month_path = r"C:\Users\Myeongkook Park\PycharmProjects\ts-python\JTTS\tmp\excelFolder\월별결제\RPA"

month_path = r"C:\RPA\★월별출금내역"
last_char_zip = r"C:\RPA\학원"

# xls-> xlsx 로 변환
def xls2xlsx_path(full_path, runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"
    try:
        XLS2XLSX(full_path).to_xlsx(
            XLSX_DIRECTORY + "\\" + full_path.split("\\")[-1] + "x")
    except FileNotFoundError:
        os.mkdir(XLSX_DIRECTORY)
        XLS2XLSX(full_path).to_xlsx(
            XLSX_DIRECTORY + "\\" + full_path.split("\\")[-1] + "x")


def xlsx2xls_path(runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"
    try:
        listdir = os.listdir(XLSX_DIRECTORY)
    except FileNotFoundError:
        os.mkdir(XLSX_DIRECTORY)
        listdir = os.listdir(XLSX_DIRECTORY)
    dispatch = Dispatch('Excel.Application')
    for i in listdir:
        add = dispatch.Workbooks.Add(XLSX_DIRECTORY + "\\" + i)
        add.SaveAs(XLSX_DIRECTORY + "\\" + i[:-1], FileFormat=56)
        dispatch.Quit()


def move_xls_file(runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    XLS_DIRECTORY = last_char_zip + "\\" + datetime.strftime(
        NOW, "%Y") + "년" + "\\" + datetime.strftime(NOW, "%m") + "월"
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"
    listdir = os.listdir(XLSX_DIRECTORY)
    for i in listdir:
        if i.endswith("xls"):
            shutil.move(XLSX_DIRECTORY + "\\" + i, XLS_DIRECTORY + "\\" + i)
    shutil.rmtree(XLSX_DIRECTORY)


# 효성CMS에서 받은 결과로 어떤 실행을 할지 분류하고 처리 함수를 호출
def paid_list(date_paid_list, runday):
    extract_success_to_cms(date_paid_list, runday)
    workbook = open_workbook(date_paid_list)
    ws = workbook.sheet_by_index(0)
    for i in range(ws.nrows):
        date = ws.cell_value(i, 1)
        name = ws.cell_value(i, 3)
        price = ws.cell_value(i, 14)
        if ws.cell_value(i, 9) == '재결제성공':
            failure_list_return_list(name, date, price, runday)
        elif ws.cell_value(i, 9) == '결제실패(월 사용한도액 초과)' or\
                ws.cell_value(i,9) == '결제실패(잔액부족)' or\
                ws.cell_value(i, 9) == '결제실패(출금불가계좌)' or\
                ws.cell_value(i, 9) == '결제실패(해지된계좌)' or \
                ws.cell_value(i, 9) == '결제실패(잔액부족 )':
            move_to_failurelist(name, date, runday)
    xlsx2xls_path(runday)
    time.sleep(2)
    move_xls_file(runday)


# 결제성공 엑셀에서 실패한 내역 리스트를 추출
def move_to_failurelist(name, date, runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    XLS_DIRECTORY = last_char_zip + "\\" + datetime.strftime(
        NOW, "%Y") + "년" + "\\" + datetime.strftime(NOW, "%m") + "월"
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"

    file_name = find_file_name(XLS_DIRECTORY, date.replace("/", "")[4:])
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    except FileNotFoundError:
        xls2xlsx_path(XLS_DIRECTORY + "\\" + file_name, runday)
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    ws = wb.active
    last_row = find_last_row(ws)
    FORM_FLAG = False
    append_row = []
    if ws['BG6'].value is not None:
        FORM_FLAG = True
    for i in range(last_row - 7):
        if FORM_FLAG:
            if ws['M' + str(i + 7)].value == name:
                for j in range(49):
                    append_row.append(ws.cell(i + 7, j + 11).value)
                ws.delete_rows(i + 7)
        else:
            if ws['E' + str(i + 7)].value == name:
                for j in range(49):
                    append_row.append(ws.cell(i + 7, j + 3).value)
                ws.delete_rows(i + 7)
    wb.save(XLSX_DIRECTORY + "\\" + file_name + "x")
    append_failurelist(append_row, date, runday)


# 상위 함수에서 추출된 리스트를 xx99.xlsx 실패내역 엑셀에 붙여넣기
def append_failurelist(fail_list, date, runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    XLS_DIRECTORY = last_char_zip + "\\" + datetime.strftime(
        NOW, "%Y") + "년" + "\\" + datetime.strftime(NOW, "%m") + "월"
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"

    failure_file_name = find_file_name(XLS_DIRECTORY,
                                       str(rundate.month) + str(99))
    header = ["01", date.replace("/", "")]
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + failure_file_name + "x")
    except FileNotFoundError:
        xls2xlsx_path(XLS_DIRECTORY + "\\" + failure_file_name, runday)
        wb = load_workbook(XLSX_DIRECTORY + "\\" + failure_file_name + "x")
    ws = wb.active
    last_row = find_last_row(ws)
    for i in range(len(fail_list)):
        ws.cell(last_row, i + 3).value = fail_list[i]
    for j in range(len(header)):
        ws.cell(last_row, j + 1).value = header[j]
    wb.save(XLSX_DIRECTORY + "\\" + failure_file_name + "x")


# 재결제성공한 리스트를 xx99.파일에서 추출
def failure_list_return_list(name, date, price, runday):
    rundate = datetime.strptime(runday, "%Y%m%d")
    NOW = rundate
    NOW_1 = rundate - relativedelta(months=1)
    XLS_DIRECTORY_1 = last_char_zip + "\\" + datetime.strftime(
        NOW, "%Y") + "년" + "\\" + datetime.strftime(NOW_1, "%m") + "월"
    XLS_DIRECTORY = last_char_zip + "\\" + datetime.strftime(
        NOW, "%Y") + "년" + "\\" + datetime.strftime(NOW, "%m") + "월"
    XLSX_DIRECTORY = last_char_zip + "\\" +\
                     datetime.strftime(NOW, "%Y") + "년" + "\\" +\
                     datetime.strftime(NOW, "%m") + "월" + "\\xlsx"
    file_name = find_file_name(XLS_DIRECTORY,
                               str(rundate.month) + str(99))
    try:
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    except FileNotFoundError:
        xls2xlsx_path(XLS_DIRECTORY + "\\" + file_name, runday)
        wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
    ws = wb.active
    last_row = find_last_row(ws)
    append_row = []
    isExistrow = False
    for i in range(last_row):
        if ws['M' + str(i + 1)].value == name and ws['T' + str(i + 1)].value == price:
            isExistrow = True
            if ws['BG6'].value is None:
                for j in range(2, ws.max_column):
                    append_row.append(ws.cell(i + 1, j + 1).value)
                append_row[12] = date.split("/")[-1]
            else:
                for j in range(10, ws.max_column):
                    append_row.append(ws.cell(i + 1, j + 1).value)
                append_row[12] = date.split("/")[-1]
            ws.delete_rows(i + 1)
            wb.save(XLSX_DIRECTORY + "\\" + file_name + "x")
            target_file_name = find_file_name(XLSX_DIRECTORY,
                                              date.replace("/", "")[4:])
            if target_file_name is None:
                try:
                    xls2xlsx_path(
                        XLS_DIRECTORY + "\\" + find_file_name(XLS_DIRECTORY,
                                                              date.replace("/",
                                                                           "")[
                                                              4:]), runday)
                except TypeError:
                    shutil.copy(r"C:\ARGOSRPA\code\template.xls",
                                XLS_DIRECTORY + "\\" + date.replace("/", "")[
                                                       4:] + ". ""청구지역 CMS전자세금계산서 발생.xls")
                    xls2xlsx_path(
                        XLS_DIRECTORY + "\\" + find_file_name(XLS_DIRECTORY,
                                                              date.replace("/",
                                                                           "")[
                                                              4:]), runday)
                target_file_name = find_file_name(XLSX_DIRECTORY,
                                                  date.replace("/", "")[4:])
            paid_paste_excel(append_row,
                             XLSX_DIRECTORY + "//" + target_file_name, date)
            break
    if not isExistrow:
        file_name = find_file_name(XLS_DIRECTORY_1, str((rundate).month) + str(99))
        try:
            wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
        except FileNotFoundError:
            xls2xlsx_path(XLS_DIRECTORY_1 + "\\" + file_name, runday)
            wb = load_workbook(XLSX_DIRECTORY + "\\" + file_name + "x")
        ws = wb.active
        last_row = find_last_row(ws)
        append_row = []
        for i in range(last_row):
            if ws['M' + str(i + 1)].value == name and ws[
                'T' + str(i + 1)].value == price:
                if ws['BG6'].value is None:
                    for j in range(2, ws.max_column):
                        append_row.append(ws.cell(i + 1, j + 1).value)
                    append_row[12] = date.split("/")[-1]
                else:
                    for j in range(10, ws.max_column):
                        append_row.append(ws.cell(i + 1, j + 1).value)
                    append_row[12] = date.split("/")[-1]
                ws.delete_rows(i + 1)
                wb.save(XLSX_DIRECTORY + "\\" + file_name + "x")
                os.remove(XLSX_DIRECTORY + "\\" + file_name + "x")
                target_file_name = find_file_name(XLSX_DIRECTORY,
                                                  date.replace("/", "")[4:])
                if target_file_name is None:
                    try:
                        xls2xlsx_path(
                            XLS_DIRECTORY + "\\" + find_file_name(XLS_DIRECTORY,
                                                                  date.replace(
                                                                      "/", "")[
                                                                  4:]), runday)
                    except TypeError:
                        shutil.copy(r"C:\ARGOSRPA\code\template.xls",
                                    XLS_DIRECTORY + "\\" + date.replace("/",
                                                                        "")[
                                                           4:] + ". ""청구지역 CMS전자세금계산서 발생.xls")
                        xls2xlsx_path(
                            XLS_DIRECTORY + "\\" + find_file_name(XLS_DIRECTORY,
                                                                  date.replace(
                                                                      "/", "")[
                                                                  4:]), runday)
                    target_file_name = find_file_name(XLSX_DIRECTORY,
                                                      date.replace("/", "")[4:])
                paid_paste_excel(append_row,
                                 XLSX_DIRECTORY + "//" + target_file_name, date)
                break


# 상위 함수에서 추출된 리스트를 재결제성공한 날짜의 파일형식 맞게 붙여넣기
def paid_paste_excel(result_list, path, date):
    wb = load_workbook(path)
    header = ['01', date.replace("/", ""), '1198678994', '', '㈜제이티통신', '이정태',
              '경기도 광명시 하안로 108,9층1호 에이스광명타워', '정보서비스', '컴퓨터시스템 통합 자문 및 구축',
              'jtc16444265@daum.net']
    if result_list[20] is not None:
        result_list[20] = date.split("/")[-1]
    if result_list[23] is not None:
        result_list[23] = date.split("/")[-1]
    FORM_FLAG = False
    ws = wb.active
    last_row = find_last_row(ws)
    if ws['BG6'].value is not None:
        FORM_FLAG = True
    for j in range(len(result_list)):
        if FORM_FLAG:
            ws.cell(last_row, j + 11).value = result_list[j]
        else:
            ws.cell(last_row, j + 3).value = result_list[j]
    if FORM_FLAG:
        for i in range(len(header)):
            ws.cell(last_row, i + 1).value = header[i]
    else:
        for i in range(2):
            ws.cell(last_row, i + 1).value = header[i]
    wb.save(path)

def init_row(ws):
    for i in range(1, ws.i):
        if ws['E'+str(i)].value is None and i >= 6:
            ws.delete_rows(i)

# 마지막 row를 반환
def find_last_row(ws):
    init_row(ws)
    last_row = 0
    for i in range(len(ws['E'])):
        if ws['E' + str(i + 2)].value is None and i >= 6:
            last_row = i + 2
            break
    return last_row


# 해당 날짜로 시작하는 파일명을 반환
def find_file_name(directory, date):
    listdir = os.listdir(directory)
    for i in listdir:
        if str(date) in i and "폐원" not in i and "직접" not in i:
            return i


# cms결제성공내역에서 "성공"키워드로 추출한 리스트 반환
# return List
def extract_success_to_cms(path, runday):
    wb = open_workbook(path)
    ws = wb.sheet_by_index(0)
    result_list = []
    for i in range(ws.nrows - 1):
        tmp = []
        if "성공" in ws.cell(i + 1, 9).value or "결제실패" in ws.cell(i + 1, 9).value:
            for j in range(20):
                tmp.append(ws.cell(i + 1, j).value)
            result_list.append(tmp)
    write_success_list(result_list, runday)


def write_success_list(success_list, runday):
    NOW = datetime.strptime(runday, "%Y%m%d")
    month = str(NOW - relativedelta(months=1)).split(" ")[0].split("-")[1]
    MONTH_DIRECTORY = month_path + r"\\" + str(
        NOW.year) + "년"
    file_name = find_file_name(MONTH_DIRECTORY, month + "월")
    if file_name is None:
        month = str((NOW - relativedelta(months=1)).month)
        file_name = find_file_name(MONTH_DIRECTORY, month + "월")
    wb = load_workbook(MONTH_DIRECTORY + "\\" + file_name)
    ws = wb.active
    for i in success_list:
        ws.append(i)
        # failure_flag = False
        # if i[9] == '재결제성공':
        #     for j in range(ws.i - 1):
        #         if ws['D' + str(j + 2)].value == i[3]:
        #             ws['J' + str(j + 2)].value = i[9]
        #             ws['B' + str(j + 2)].value = i[1]
        #             ws['I' + str(j + 2)].value = i[8]
        # elif i[9] == '결제성공':
        #     ws.append(i)
        # elif '결제실패' in i[9]:
        #     for j in range(ws.i - 1):
        #         if ws['D' + str(j + 2)].value == i[3]:
        #             failure_flag = True
        #             break
        #     if failure_flag is False:
        #         ws.append(i)
    wb.save(MONTH_DIRECTORY + "\\" + file_name)


# xlsx 폴더가 월 폴더 안에 존재하면 삭제
def delete_xlsx_folder(runday):
    try:
        # 시간
        rundate = datetime.strptime(runday, "%Y%m%d")
        # 숫자 설정
        num = []
        num.append(str(rundate - relativedelta()).split(" ")[0].split("-")[1])  # 08월
        num.append(str((rundate - relativedelta()).month))  # 8월
        # 경로
        year = str(rundate.year) + "년"
        # 반복
        for n in num:
            month = str(n) + "월"
            path = last_char_zip + '\\' + year + '\\' + month + '\\' + 'xlsx'
            # 폴더 존재 확인 후, 삭제
            if os.path.exists(path):
                shutil.rmtree(path)
    except:
        # 혹시 모를 예외 사항을 위해서
        pass


def main(cms_file_path, runday):
    delete_xlsx_folder(runday)
    return paid_list(cms_file_path, str(runday))


if __name__ == '__main__':
    main()
