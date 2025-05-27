import os
import shutil
from datetime import datetime

import openpyxl
import pandas as pd
import win32com.client as win32
from dateutil.relativedelta import relativedelta

today = datetime.today()
amonth_ago = today - relativedelta(months=1)
two_month_ago = today - relativedelta(months=2)

# folder_path = 'C:\\RPA\\백업\\지역아동센터\\' + today.strftime('%Y') + '년\\' + today.strftime('%m') + '월\\'
root_path = 'C:\\Users\\vivans\\PycharmProjects\\ts-python\\JTTS\\file\\test\\지역아동센터\\'
folder_path = 'C:\\Users\\vivans\\PycharmProjects\\ts-python\\JTTS\\file\\test\\지역아동센터\\' + today.strftime(
    '%Y') + '년\\' + today.strftime('%m') + '월'
folder_xlsx_path = folder_path + '\\xlsx'
today_xls_path = folder_path + today.strftime('%m%d') + today.strftime('. %y%m%d') + ' 지역아동센터계산서 (' + str(
    today.month) + '월 서비스이용료).xls'
fail_xls = folder_path + '\\' + today.strftime('%m') + '99. ' + today.strftime('%y%m') + '99 지역아동센터계산서 (' + str(
    today.month) + '월 서비스이용료) - 출금실패.xls'
today_fail_xlsx = folder_path + today.strftime('%m') + '99. ' + today.strftime('%y%m') + '99 지역아동센터계산서 (' + str(
    today.month) + '월 서비스이용료) - 출금실패.xls'

template_path_a = 'C:/Users/vivans/PycharmProjects/ts-python/JTTS/file/template.xls'
template_path_b = 'C:/Users/vivans/PycharmProjects/ts-python/JTTS/file/template 100.xls'


# 100건 미만: template.xls''''''''''''''
# 100건 이상: template 100.xls

def xls2xlsx(xls_path):
    if os.path.isfile(xls_path + "x"):
        os.remove(xls_path + "x")

    wb = win32.gencache.EnsureDispatch('Excel.Application').Workbooks.Open(xls_path)

    wb.SaveAs(xls_path + "x", FileFormat=51)
    wb.Close()

    win32.gencache.EnsureDispatch('Excel.Application').Application.Quit()

    xlsx_path = xls_path + "x"

    return xlsx_path


# 필요한 엑셀 파일 xlsx 형식으로 변환하여 xlsx 폴더로 이동: return fail_xlsx_list xlsx 폴더 내 실패 엑셀 리스트
def init_xlsx_folder(cms_xls):
    if os.path.exists(folder_xlsx_path):
        shutil.rmtree(folder_xlsx_path)
        os.makedirs(folder_xlsx_path)
    else:
        pass

    fail_xlsx_list = make_fail_xlsx()

    # cms파일에서 결제일 가져오기
    temp = []
    df = pd.read_excel(cms_xls)
    payment_date_list = list(df.dropna(axis=0, subset="결제일")["결제일"].unique())

    for i in payment_date_list:
        payment_date = datetime.strptime(i, '%Y/%m/%d')
        payment_date_a = payment_date.strftime('%m%d')
        payment_date_b = payment_date.strftime('%y%m%d')

        payment_xls_path_a = root_path + f'{payment_date.year}년\\{payment_date.month}월\\{payment_date_a}. {payment_date_b} 지역아동센터계산서 ({payment_date.month}월 서비스이용료).xls'
        payment_xls_path_b = root_path + f'{payment_date.year}년\\{payment_date.month}월\\{payment_date_a}. {payment_date_b} 100건초과 지역아동센터계산서 ({payment_date.month}월 서비스이용료).xls'

        print(payment_xls_path_a)
        print(payment_xls_path_b)

        if os.path.exists(payment_xls_path_a):
            print("a")
            temp.append(payment_xls_path_a)
        elif os.path.exists(payment_xls_path_b):
            print("b")
            temp.append(payment_xls_path_b)
        else:
            print("pass: 결제일 엑셀 없음")

    payment_xlsx_path_list = []
    for xlsx in temp:
        payment_xlsx_path = xls2xlsx(xlsx)

        payment_xlsx_path = shutil.move(payment_xlsx_path, folder_xlsx_path)
        payment_xlsx_path_list.append(payment_xlsx_path)

    print("aa")

    # cms.xls -> xlsx로 변환
    cms_xlsx_path = xls2xlsx(cms_xls)
    cms_xlsx_path = shutil.move(cms_xlsx_path, folder_xlsx_path)

    # xlsx_path = xls2xlsx(today_xls_path)
    # jtt_xlsx = shutil.move(xlsx_path, folder_xlsx_path)

    return fail_xlsx_list, payment_xlsx_path_list, cms_xlsx_path


# 최근 3개월 실패 파일 전부 //당월/xlsx 폴더에 저장
def make_fail_xlsx():
    # //당월/xlsx 폴더 삭제 후, 새로 생성: 폴더 초기화 시키기 위함
    try:
        shutil.rmtree(folder_xlsx_path)
    except FileNotFoundError:
        pass
    os.makedirs(folder_xlsx_path)

    # 당월, 전월, 전전월 실패 파일 찾기
    amonth_ago_fail_xls = r'C:\work\JTCMM\test\test\지역아동센터' + amonth_ago.strftime(
        '%Y') + '년\\' + amonth_ago.strftime('%m') + '월\\' + amonth_ago.strftime('%m') + '99. ' + amonth_ago.strftime(
        '%y%m') + '99 지역아동센터계산서 (' + amonth_ago.strftime('%m') + '월 서비스이용료) - 출금실패.xls'
    two_month_ago_fail_xls = 'C:\\Users\\vivans\\PycharmProjects\\ts-python\\JTTS\\file\\test\\지역아동센터\\' + two_month_ago.strftime(
        '%Y') + '년\\' + two_month_ago.strftime('%m') + '월\\' + two_month_ago.strftime(
        '%m') + '99. ' + two_month_ago.strftime('%y%m') + '99 지역아동센터계산서 (' + two_month_ago.strftime(
        '%m') + '월 서비스이용료) - 출금실패.xls'

    fail_xls_list = [fail_xls, amonth_ago_fail_xls, two_month_ago_fail_xls]
    fail_xlsx_list = []

    # 실패.xls 파일 xlsx로 변환 후, xlsx 폴더로 이동(fail_xlsx_list: 실패.xlsx 리스트)
    for xls in fail_xls_list:
        if os.path.isfile(xls):
            xlsx = xls2xlsx(xls)
            xlsx = shutil.move(xlsx, folder_xlsx_path)
            fail_xlsx_list.append(xlsx)
        else:
            pass

    return fail_xlsx_list


# 전월 월별출금내역에 cms 결제 내역 추가하기: C:\RPA\★월별출금내역\2022년\2022년 1월 출금내역.xlsx
def monthly_excel_append(cms_xlsx_path):
    monthly_excel_path = 'C:\\Users\\vivans\\PycharmProjects\\ts-python\\JTTS\\file\\test\\★월별출금내역\\' + amonth_ago.strftime(
        '%Y') + '년\\' + amonth_ago.strftime('%Y년 ') + str(amonth_ago.month) + '월 출금내역.xlsx'

    wb_monthly = openpyxl.load_workbook(monthly_excel_path)
    ws_monthly = wb_monthly.active

    wb_cms = openpyxl.load_workbook(cms_xlsx_path)
    ws_cms = wb_cms.active

    success_list = []
    # 반복하며 데이터 리스트에 넣기
    for i in range(1, ws_cms.i):
        tmp = []
        try:
            if "성공" in ws_cms['J' + str(i + 1)].value or "결제실패" in ws_cms['J' + str(i + 1)].value:
                for j in range(1, 21):
                    tmp.append(ws_cms.cell(i + 1, j).value)
                success_list.append(tmp)
        except TypeError as e:
            print("e")

    # 출금내역 붙여넣기
    for i in success_list:
        ws_monthly.append(i)

    wb_monthly.save('tt.xlsx')
    # wb_monthly.save(monthly_excel_path)


# 서비스 이용료 엑셀과 cms 엑셀의 결제상태 비교
def cms_check(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list):
    jtt_xlsx = jtt_xlsx_list[0]
    if '100건초과' in jtt_xlsx:
        over_hundred(fail_xlsx_list, cms_xlsx_path, jtt_xlsx)
    else:
        pass
        # jtt_xlsx = './file/테스트_jtt.xlsx'
        if os.path.exists(jtt_xlsx):
            wb_jtt = openpyxl.load_workbook(jtt_xlsx)
            ws_jtt = wb_jtt.active
        else:
            wb_jtt = openpyxl.load_workbook()

        wb_cms = openpyxl.load_workbook(cms_xlsx_path)
        ws_cms = wb_cms.active

        # fail_xlsx = './file/테스트_실패.xlsx'
        # wb_fail = openpyxl.load_workbook(fail_xlsx)
        # ws_fail = wb_fail.active

        data_to_append_jtt = []
        data_to_append_fail = []
        row_to_delete_jtt = []
        row_to_delete_fail = []
        for i in range(1, ws_cms.i + 1):
            status = ws_cms['J' + str(i + 1)].value
            payment_date = ws_cms['A' + str(i + 1)].value
            member_name = ws_cms['D' + str(i + 1)].value
            supply_value = ws_cms['O' + str(i + 1)].value
            if payment_date == "합계":
                break
            elif status == "결제성공":
                pass
            elif status == "재결제성공":
                print("재결제성공")
                # 당월 실패 파일에서 건수 찾기: 결제금액과 개수 비교하기!라고 되어있으나 개수가 없어서 회원명과 공급가액 비교
                for fail_xlsx in fail_xlsx_list:
                    wb_fail = openpyxl.load_workbook(fail_xlsx)
                    ws_fail = wb_fail.activeF
                    for j in range(6, ws_fail.i + 1):
                        member_store_fail = ws_fail['M' + str(j + 1)].value
                        supply_value_fail = ws_fail['T' + str(j + 1)].value


if (member_name == member_store_fail) and (supply_value == supply_value_fail):
    retry_success_list = []
    # 실패파일에서 정보 가져오기
    kind = ws_fail['A' + str(j + 1)].value
    create_date = ws_fail['B' + str(j + 1)].value
    registration_number = ws_fail['K' + str(j + 1)].value
    member_name_fail = ws_fail['N' + str(j + 1)].value
    member_address_fail = ws_fail['O' + str(j + 1)].value
    member_email_fail = ws_fail['R' + str(j + 1)].value
    tax_fail = ws_fail['U' + str(j + 1)].value
    remark_fail = ws_fail['V' + str(j + 1)].value  # 계좌번호
    day_fail = ws_fail['W' + str(j + 1)].value
    product_fail = ws_fail['X' + str(j + 1)].value

    retry_success_list = [
        '01',
        today.strftime('%Y%m%d'),
        "1198678994",
        '',
        '㈜제이티통신',
        '이정태',
        "경기도 광명시 하안로 108,9층1호 에이스광명타워",
        "정보서비스",
        "컴퓨터시스템 통합 자문 및 구축",
        "jtc16444265@daum.net",
        registration_number,
        '',
        member_store_fail,
        member_name_fail,
        member_address_fail,
        '', '',
        member_email_fail,
        '',
        supply_value_fail,
        tax_fail,
        "(기업은행) 333-048573-01-028 (주)제이티통신",
        today.strftime('%d'),
        "아이알리미(전자출결 시스템 서비스)_" + str(today.month) + "월",
        "개",
        '', '',
        supply_value_fail,
        tax_fail
    ]

    data_to_append_jtt.append(retry_success_list)

    # 실패파일에서 지울 row
    row_to_delete_fail.append(j + 1)

    break

    # 실패파일에서 정보 삭제
    # ws_fail.delete_rows(j + 1)

elif "결제실패" in status:
    if "재결제" in status:
        print("재결제실패")
        # 실패파일에 추가: 혹시 전월, 전전월까지 찾아야 하나?
    else:
        # 서비스 이용료 엑셀에서 정보 가져오기
        for j in range(6, ws_jtt.i + 1):
            member_store_jtt = ws_jtt['M' + str(j)].value
            supply_value_jtt = ws_jtt['T' + str(j)].value
            # 공급자 이름과 공급가액이 같으면
            if member_store_jtt == member_name and supply_value == supply_value_jtt:
                # 서비스 이용료 엑셀에서 삭제할 row: row_to_delete_jtt에 row 추가
                row_to_delete_jtt.append(j)
                # 결제실패인 정보 담기기
                fail_list = []
                for k in range(1, ws_jtt.max_column + 1):
                    fail_list.append(ws_jtt.cell(row=j, column=k).value)

                data_to_append_fail.append(fail_list)

                break

        # 서비스 이용료 엑셀에서 삭제할 row
        row_to_delete_jtt.append(j)

        print("결제실패")

    # 서비스 이용료 엑셀에서 데이터 지우기
cnt = 0
for row in row_to_delete_jtt:
    ws_jtt.delete_rows(row - cnt)
    cnt += 1

# 실패파일에서 데이터 지우기
cnt = 0
for row in row_to_delete_fail:
    ws_fail.delete_rows(row - cnt)
    cnt += 1

# 재결제성공 데이터 서비스 이용료 엑셀에 추가
for data in data_to_append_jtt:
    ws_jtt.append(data)

# 실패 데이터, 실패 엑셀에 추가
for data in data_to_append_fail:
    ws_fail.append(data)

# wb_jtt.save(jtt_xlsx)
# wb_fail.save(wb_fail)
print("cms 파일 비교 완료")


def over_hundred(fail_xlsx_list, cms_xlsx_path, jtt_xlsx):
    # jtt_xlsx = './file/테스트_jtt.xlsx'
    wb_jtt = openpyxl.load_workbook(jtt_xlsx)
    ws_jtt = wb_jtt.active

    wb_cms = openpyxl.load_workbook(cms_xlsx_path)
    ws_cms = wb_cms.active

    # fail_xlsx = './file/테스트_실패.xlsx'
    # wb_fail = openpyxl.load_workbook(fail_xlsx)
    # ws_fail = wb_fail.active

    data_to_append_jtt = []
    data_to_append_fail = []
    row_to_delete_jtt = []
    row_to_delete_fail = []
    for i in range(1, ws_cms.i + 1):
        status = ws_cms['J' + str(i + 1)].value

    print("100건 초과")


def main(cms_xls):
    fail_xlsx_list, jtt_xlsx_list, cms_xlsx_path = init_xlsx_folder(cms_xls)
    # monthly_excel_append(cms_xlsx_path)
    cms_check(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list)


if __name__ == "__main__":
    main(r'C:\Users\vivans\PycharmProjects\ts-python\JTTS\file\20221115_20221115_지역아동센터.xls')
