import os
import re
import time
import shutil
import openpyxl
import pandas as pd
from datetime import datetime
import win32com.client as win32
from dateutil.relativedelta import relativedelta
from distutils.dir_util import copy_tree



today = datetime.today()
amonth_ago = today - relativedelta(months=1)
two_month_ago = today - relativedelta(months=2)

root_path ='C:\\RPA\\학원\\'
folder_path = 'C:\\RPA\\학원\\' + today.strftime('%Y') + '년\\' + str(today.month) + '월'
folder_xlsx_path = folder_path + '\\xlsx'
today_xls_path = folder_path  + '\\' +today.strftime('%m%d') + today.strftime('. %y%m%d') + ' 학원계산서 (' + str(today.month) + '월 서비스이용료).xls'
fail_xls = folder_path + '\\' + today.strftime('%m') + '99. ' + today.strftime('%y%m') + '99 학원계산서 (★' + str(today.month) + '월 서비스이용료)- 출금실패.xls'
today_fail_xlsx = folder_path + '\\' + today.strftime('%m') + '99. ' + today.strftime('%y%m') + '99 학원계산서 (★' + str(today.month) + '월 서비스이용료)- 출금실패.xlsx'
backup_path = 'C:\\RPA\\백업'
#3###############################################
#실패 파일의 마지막행 구하기

def get_i(ws_fail):
    cnt = 0
    max_r = 7
    for i in range(6, ws_fail.i + 1):
        if (ws_fail["M" + str(i+1)].value is None) and (ws_fail["M" + str(i + 2)].value is None) and (ws_fail["M" + str(i + 3)].value is None) and (ws_fail["M" + str(i + 4)].value is None):
            max_r = i+1
            break
    return max_r


def xls2xlsx(xls_path):
    if os.path.isfile(xls_path + "x"):
        os.remove(xls_path + "x")

    wb = win32.gencache.EnsureDispatch('Excel.Application').Workbooks.Open(xls_path)

    wb.SaveAs(xls_path + "x", FileFormat=51)
    wb.Close()

    win32.gencache.EnsureDispatch('Excel.Application').Application.Quit()
    time.sleep(3)

    xlsx_path = xls_path + "x"

    return xlsx_path


def xlsx2xls(xlsx_path):
    for z in xlsx_path:
        if "이용료" not in z:
            pass
        else:
            p = re.compile('\d{6}')
            a_a = p.findall(z)
            a_a = a_a[0]
            yy = a_a[:2]
            mm = a_a[2:4]
            y_m = int(mm)-1
            file_name = os.path.basename(z)
            if y_m == 0:
                xls2_path = folder_path+'\\'+f'{file_name[:-1]}'
            else:
                xls2_path = root_path+'20'+yy+'년'+'\\'+mm+'월'+'\\'+f'{file_name[:-1]}'
            xls_wb = openpyxl.load_workbook(folder_xlsx_path+'\\'+z)
            xls_ws = xls_wb.active
            xls_save = xls_wb.save(xls2_path)
    return xlsx_path


# 필요한 엑셀 파일 xlsx 형식으로 변환하여 xlsx 폴더로 이동: return fail_xlsx_list xlsx 폴더 내 실패 엑셀 리스트
#  cms를 파일을 불러오는 함수
def init_xlsx_folder(cms_xls):
    #xlsx폴더가 있으면 삭제하는 코드
    if os.path.exists(folder_xlsx_path):
      shutil.rmtree(folder_xlsx_path)
    else:
        pass
    os.makedirs(folder_xlsx_path)
    # 결제실패 파일 xls을 xlsx로 변환하기 위한 함수 호출
    fail_xlsx_list = make_fail_xlsx()

    cms_xlsx_path = xls2xlsx(cms_xls)
    cms_xlsx_path = shutil.move(cms_xlsx_path, folder_xlsx_path)

    # cms파일에서 결제일 가져오기
    temp = []
    payment_xlsx_path_list = []
    df = pd.read_excel(cms_xls)
    payment_date_list = list(df.dropna(axis=0, subset=['결제일'])['결제일'].unique())

    for i in payment_date_list:
        payment_date = datetime.strptime(i, '%Y/%m/%d')
        payment_date_a = payment_date.strftime('%m%d')
        payment_date_b = payment_date.strftime('%y%m%d')
        jtt_xslx_path = folder_xlsx_path+'\\'+payment_date.strftime('%m')+payment_date.strftime('%d')+'. '+ payment_date_b+' 학원계산서 '+'(' +str(payment_date.month)+'월 서비스이용료).xlsx'
        #일반 xls파일
        payment_xls_path_a = root_path + f'{payment_date.year}년\\{payment_date.month}월\\{payment_date_a}. {payment_date_b} 학원계산서 ({payment_date.month}월 서비스이용료).xls'
        #100건 초과 xls파일
        payment_xls_path_b = root_path + f'{payment_date.year}년\\{payment_date.month}월\\{payment_date_a}. {payment_date_b} 100건이상 학원계산서 ({payment_date.month}월 서비스이용료).xls'

        print(payment_xls_path_a)
        print(payment_xls_path_b)

        if os.path.exists(payment_xls_path_a):
            print("a")
            temp.append(payment_xls_path_a)
        elif os.path.exists(payment_xls_path_b):
            print("b")
            temp.append(payment_xls_path_b)
        else:
            if len(payment_date_list) >= 100 :
                wb_jtt = openpyxl.load_workbook(r'C:\ARGOSRPA\code\template 100.xlsx')
            else:
                wb_jtt = openpyxl.load_workbook(r'C:\ARGOSRPA\code\template.xlsx')

        ws_jtt = wb_jtt.active
        wb_jtt.save(jtt_xslx_path)
        payment_xlsx_path_list.append(jtt_xslx_path)

    for xlsx in temp:
        #해당 결제일 파일을 xlsx파일로 변환
        payment_xlsx_path = xls2xlsx(xlsx)

        payment_xlsx_path = shutil.move(payment_xlsx_path, folder_xlsx_path)
        payment_xlsx_path_list.append(payment_xlsx_path)

    print("aa")

    # cms.xls -> xlsx로 변환
    # cms_xlsx_path = xls2xlsx(cms_xls)
    # cms_xlsx_path = shutil.move(cms_xlsx_path, folder_xlsx_path)

    # template -> xlsx로 변환
    # template_path_a = xls2xlsx('C:/Users/vivans/PycharmProjects/ts-python/JTTS/file/template.xls')
    # template_path_a = shutil.move(template_path_a, folder_xlsx_path)
    #
    # template_path_b = xls2xlsx('C:/Users/vivans/PycharmProjects/ts-python/JTTS/file/template 100.xls')
    # template_path_b = shutil.move(template_path_b, folder_xlsx_path)

    backup(backup_path)

    return fail_xlsx_list, payment_xlsx_path_list, cms_xlsx_path, payment_date


def backup(xlsx_path):
    print("xlsx 폴더를 백업 폴더로 옮겨주세요")
    if not os.path.exists(f'C:/RPA/백업/{today.month}{today.day}'):
        os.makedirs(f'C:/RPA/백업/{today.month}{today.day}/xlsx')
        copy_tree(folder_xlsx_path, f'C:/RPA/백업/{today.month}{today.day}/xlsx/')
    if os.path.exists(f'C:/RPA/백업/{today.month}{today.day}'):
        shutil.rmtree(f'C:/RPA/백업/{today.month}{today.day}/xlsx')
        os.makedirs(f'C:/RPA/백업/{today.month}{today.day}/xlsx')
        copy_tree(folder_xlsx_path, f'C:/RPA/백업//{today.month}{today.day}/xlsx/')
    return xlsx_path

# 최근 3개월 실패 파일 전부 //당월/xlsx 폴더에 저장
def make_fail_xlsx():
    # 당월, 전월, 전전월 실패 파일 찾기
    amonth_ago_fail_xls = root_path+ amonth_ago.strftime('%Y') + '년\\' + amonth_ago.strftime('%m') + '월\\' + amonth_ago.strftime('%m') + '99. ' + amonth_ago.strftime('%y%m') + '99 학원계산서 (★' + amonth_ago.strftime('%m') + '월 서비스이용료)- 출금실패.xls'
    two_month_ago_fail_xls = root_path + two_month_ago.strftime('%Y') + '년\\' + two_month_ago.strftime('%m') + '월\\' + two_month_ago.strftime('%m') + '99. ' + two_month_ago.strftime('%y%m') + '99 학원계산서 (★' + two_month_ago.strftime('%m') + '월 서비스이용료)- 출금실패.xls'

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
def monthly_excel_append(cms_xlsx_path, payment_date):
    print("월별추가")
    # m = payment_date.month
    # ago_m = m - 1
    # monthly_template_path = 'C:\\RPA\\★월별출금내역\\2023년\\2023년 0월 출금내역.xlsx'
    # if ago_m == 0 :
    #     m = 12
    #     monthly_excel_path = 'C:\\RPA\\★월별출금내역\\' + amonth_ago.strftime('%Y') + '년\\' +amonth_ago.strftime('%Y')+'년 ' + str(m) + '월 출금내역.xlsx'
    # else:
    #     monthly_excel_path = 'C:\\RPA\\★월별출금내역\\' + today.strftime('%Y') + '년\\' + today.strftime('%Y') + '년 ' + str(ago_m) + '월 출금내역.xlsx'
    #
    # if os.path.isfile(monthly_excel_path):
    #     wb_monthly = openpyxl.load_workbook(monthly_excel_path)
    #     df = pd.read_excel(monthly_excel_path)
    # else:
    #     wb_monthly = openpyxl.load_workbook(monthly_template_path)
    #     df = pd.read_excel(monthly_template_path)
    #
    # ws_monthly = wb_monthly.active
    # wb_cms = openpyxl.load_workbook(cms_xlsx_path)
    # ws_cms = wb_cms.active
    #
    # success_list = []
    # # 반복하며 데이터 리스트에 넣기
    # for i in range(1, ws_cms.i):
    #     tmp = []
    #     payment_date_list = list(df.dropna(axis=0, subset=["결제일"])["결제일"].unique())
    #     member_name_list = list(df.dropna(axis=0, subset=["회원명"])["회원명"].unique())
    #     supply_value_list = list(df.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())
    #     supply_int = list(map(int, supply_value_list))
    #     try:
    #         if (ws_cms['B'+str(i+1)].value in payment_date_list) and (ws_cms['D'+str(i+1)].value in member_name_list) and (ws_cms['O'+str(i+1)].value in supply_int):
    #             print("중복이거나 재결제실패 상태입니다.")
    #             break
    #         else:
    #             for j in range(1, 21):
    #                 tmp.append(ws_cms.cell(i + 1, j).value)
    #             success_list.append(tmp)
    #     except TypeError as e:
    #         print("e")
    #
    # # 출금내역 붙여넣기
    # # 중복값 제거
    # for i in success_list:
    #     ws_monthly.append(i)
    #
    # # wb_monthly.save('월별출금금액.xlsx')
    # wb_monthly.save(monthly_excel_path)


# 서비스 이용료 엑셀과 cms 엑셀의 결제상태 비교
def cms_check(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list, payment_date):
    m = payment_date.month
    d = payment_date.day
    str_m = str(m)
    str_d = str(d)
    jtt_xlsx = jtt_xlsx_list[0]
    fail_xlsx = fail_xlsx_list[0]
    xlsx_to_convert = []
    if '100건초과' in jtt_xlsx:
        over_hundred(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list, payment_date)
        xlsx_to_convert.append(jtt_xlsx)
        return xlsx_to_convert
    else:
        pass
        # jtt_xlsx = pay_mentxls_path_a
        if os.path.exists(jtt_xlsx):
            wb_jtt = openpyxl.load_workbook(jtt_xlsx)
        else:
            wb_jtt = openpyxl.load_workbook('C:\\ARGOSRPA\\code\\template.xlsx')
        ws_jtt = wb_jtt.active
        #main xls을 xlsx로 바꾼 파일 경로 cms_xlsx_path
        wb_cms = openpyxl.load_workbook(cms_xlsx_path)
        ws_cms = wb_cms.active
        data_to_append_jtt = []
        data_to_append_fail = []
        row_to_delete_jtt = []
        row_to_delete_fail = []
        df = pd.read_excel(jtt_xlsx, header=5)
        member_name_jtt = list(df.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
        supply_value_jtt = list(df.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())

        for i in range(1, ws_cms.i+1):
            status = ws_cms['J' + str(i+1)].value
            cms_date = ws_cms['B' + str(i+1)].value
            member_name = ws_cms['D' + str(i+1)].value
            supply_value = ws_cms['O' + str(i+1)].value
            number = ws_cms['A' + str(i+1)].value

            if number == "합계":
                break
            elif status == "결제성공":
                pass
            elif status == "재결제성공":
                print("재결제성공")
                # 당월 실패 파일에서 건수 찾기: 결제금액과 개수 비교하기!라고 되어있으나 개수가 없어서 회원명과 공급가액 비교
                for fail_xlsx in fail_xlsx_list:
                    wb_fail = openpyxl.load_workbook(fail_xlsx)
                    ws_fail = wb_fail.active
                    ws_jtt = wb_jtt.active
                    df = pd.read_excel(jtt_xlsx, header=5)
                    member_name_jtt = list(df.dropna(axis=0, subset=['공급받는자 상호'])["공급받는자 상호"].unique())
                    supply_value_jtt = list(df.dropna(axis=0, subset=['공급가액'])["공급가액"].unique())
                    for j in range(6, ws_fail.i+1):
                        row_to_delete_fail = []
                        row = ''
                        member_store_fail = ws_fail['M' + str(j+1)].value
                        supply_value_fail = ws_fail['T' + str(j+1)].value
                        if (member_name == member_store_fail) and (supply_value == supply_value_fail):
                            retry_success_list = []
                            # 실패파일에서 정보 가져오기
                            kind = ws_fail['A' + str(j+1)].value
                            create_date = ws_fail['B' + str(j+1)].value
                            registration_number = ws_fail['K' + str(j+1)].value
                            member_name_fail = ws_fail['N' + str(j+1)].value
                            member_address_fail = ws_fail['O' + str(j+1)].value
                            member_email_fail = ws_fail['R' + str(j+1)].value
                            tax_fail = ws_fail['U' + str(j+1)].value
                            remark_fail = ws_fail['V' + str(j+1)].value  # 계좌번호
                            day_fail = ws_fail['W' + str(j+1)].value
                            product_fail = ws_fail['X' + str(j+1)].value

                            retry_success_list = [
                                '01',
                                str(payment_date.strftime('%Y%m%d')),
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
                                str(payment_date.day),
                                "아이알리미(전자출결 시스템 서비스)_" + str(payment_date.month) + "월",
                                "개",
                                '', '',
                                supply_value_fail
                            ]

                            data_to_append_jtt.append(retry_success_list)

                            # 실패파일에서 지울 row
                            row_to_delete_fail.append(j+1)

                            break

                        # 실패파일에서 데이터 지우기
                    for row in row_to_delete_fail:
                        if row == '':
                            pass
                        else:
                            ws_fail.delete_rows(int(row))
                        wb_fail.save(fail_xlsx)
            elif "재결제실패" in status:
                print("재결제실패")
                for fail_xlsx in fail_xlsx_list:
                    if str_m in fail_xlsx:
                        fail_df = pd.read_excel(fail_xlsx, header=5)
                        store_name_list_fail = list(fail_df.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())

                        wb_cms = openpyxl.load_workbook(cms_xlsx_path)
                        ws_cms = wb_cms.active

                        wb_fail = openpyxl.load_workbook(fail_xlsx)
                        ws_fail = wb_fail.active

                        if member_name in store_name_list_fail:
                            pass
                        else:
                            print("실패파일에 내용 추가")
                            row_mx = get_i(ws_fail)
                            cd3 = payment_date.strftime('%Y-%m-%d')
                            ws_fail["B" + str(row_mx)].value = cd3
                            ws_fail["M" + str(row_mx)].value = ws_cms["D" + str(i+1)].value
                            ws_fail["T" + str(row_mx)].value = ws_cms["O" + str(i+1)].value
                            ws_fail["U" + str(row_mx)].value = ws_cms["P" + str(i+1)].value
                            ws_fail["AB" + str(row_mx)].value = ws_cms["O" + str(i+1)].value
                            ws_fail["AC" + str(row_mx)].value = ws_cms["P" + str(i+1)].value
                            ws_fail["W" + str(row_mx)].value = str_d
                            wb_fail.save(fail_xlsx)
            else:
                print("당월 결제 실패 파일에 추가하기")
                print("결제일 파일에서 삭제")
                # 서비스 이용료 엑셀에서 정보 가져오기
                for fail_xlsx in fail_xlsx_list:
                    if today.strftime('%m')+'99' in fail_xlsx:
                        data_to_append_jtt = []
                        row_to_delete_fail = []
                        row = ''
                        wb_fail = openpyxl.load_workbook(fail_xlsx)
                        ws_fail = wb_fail.active
                        df2 = pd.read_excel(fail_xlsx, header=5)
                        member_name_fail = list(df2.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
                        man_fail = list(df2.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())
                        for j in range(7, ws_jtt.i+1):
                            member_store_jtt = ws_jtt['M' + str(j)].value
                            supply_value_jtt = ws_jtt['T' + str(j)].value
                            # 공급자 이름과 공급가액이 같으면
                            if member_store_jtt == member_name and supply_value == supply_value_jtt:
                                # 서비스 이용료 엑셀에서 삭제할 row: row_to_delete_jtt에 row 추가
                                row_to_delete_jtt.append(j)
                                # 결제실패인 정보 담기기
                                fail_list = []
                                for k in range(1, ws_jtt.max_column+1):
                                    fail_list.append(ws_jtt.cell(row=j, column=k).value)

                                data_to_append_fail.append(fail_list)
                                for data in data_to_append_fail:
                                    if (data[12] not in member_name_fail) and (data[13] not in man_fail):
                                        if data[12] not in member_name_fail:
                                            ws_fail.append(data)
                                wb_fail.save(fail_xlsx)

                            elif (member_store_jtt is None) and (supply_value_jtt is None):
                                break

                        df2 = pd.read_excel(fail_xlsx, header=5)
                        member_name_fail = list(df2.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
                        supply_value_fail = list(df2.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())

                        # 중복을 피함
                        if (ws_cms["D" + str(i + 1)].value not in member_name_fail) and ( ws_cms["O" + str(i + 1)].value not in supply_value_fail):
                            print("실패파일에 내용 추가")
                            row_mx = get_i(ws_fail)
                            cd3 = payment_date.strftime('%Y%m%d')
                            ws_fail["B" + str(row_mx)].value = cd3
                            ws_fail["E" + str(row_mx)].value = ws_cms["D" + str(i + 1)].value
                            ws_fail["L" + str(row_mx)].value = ws_cms["O" + str(i + 1)].value
                            ws_fail["M" + str(row_mx)].value = ws_cms["P" + str(i + 1)].value
                            ws_fail["T" + str(row_mx)].value = ws_cms["O" + str(i + 1)].value
                            ws_fail["U" + str(row_mx)].value = ws_cms["P" + str(i + 1)].value
                            ws_fail["O" + str(row_mx)].value = str_d
                            wb_fail.save(fail_xlsx)

            for row in row_to_delete_jtt:
                if row == '':
                    pass
                else:
                    ws_jtt.delete_rows(int(row))
                    wb_jtt.save(jtt_xlsx)

            # 재결제성공 데이터, 결제일 엑셀에 추가
            for data in data_to_append_jtt:
                df = pd.read_excel(jtt_xlsx, header=5)
                create_date_jtt = list(df.dropna(axis=0, subset=['작성일자'])["작성일자"].unique())
                member_name_jtt = list(df.dropna(axis=0, subset=['공급받는자 상호'])["공급받는자 상호"].unique())
                supply_value_jtt = list(df.dropna(axis=0, subset=['공급가액'])["공급가액"].unique())
                supply_int = list(map(int, supply_value_jtt))
                if (data[12] not in member_name_jtt) or (data[19] not in supply_int) and (data[2] not in create_date_jtt) :
                    ws_jtt.append(data)
            wb_jtt.save(jtt_xlsx)
            print(member_name_jtt)
        print("cms 파일 비교 완료")
        xlsx2xls(os.listdir(folder_xlsx_path))
        return xlsx_to_convert


def over_hundred(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list, payment_date):
    print("100건 이상")
    m = payment_date.month
    d = payment_date.day
    str_m = str(m)
    str_d = str(d)
    jtt_xlsx = jtt_xlsx_list[0]
    fail_xlsx = fail_xlsx_list[0]
    xlsx_to_convert = []

    df = pd.read_excel(cms_xlsx_path)
    payment_date_list = list(df.dropna(axis=0, subset=["상태"])["상태"].unique())

    if (len(payment_date_list) == 1) and payment_date_list[0] == "결제성공":
        pass
    else:
        pass
        # jtt_xlsx = pay_mentxls_path_a
        if os.path.exists(jtt_xlsx):
            wb_jtt = openpyxl.load_workbook(jtt_xlsx)
        else:
            wb_jtt = openpyxl.load_workbook('C:\\ARGOSRPA\\code\\template 100.xlsx')
        ws_jtt = wb_jtt.active
        #main xls을 xlsx로 바꾼 파일 경로 cms_xlsx_path
        wb_cms = openpyxl.load_workbook(cms_xlsx_path)
        ws_cms = wb_cms.active

        data_to_append_jtt = []
        data_to_append_fail = []
        row_to_delete_jtt = []
        row_to_delete_fail = []
        member_name_jtt = list(df.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
        supply_value_jtt = list(df.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())
        df2 = pd.read_excel(fail_xlsx, header=5)
        member_name_fail = list(df2.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
        supply_value_fail = list(df2.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())

        for i in range(1, ws_cms.i+1):
            status = ws_cms['J' + str(i+1)].value
            cms_date = ws_cms['B' + str(i+1)].value
            member_name = ws_cms['D' + str(i+1)].value
            supply_value = ws_cms['O' + str(i+1)].value
            number = ws_cms['A' + str(i+1)].value

            if number == "합계":
                break
            elif status == "결제성공":
                pass
            elif status == "재결제성공":
                print("재결제성공")
                # 당월 실패 파일에서 건수 찾기: 결제금액과 개수 비교하기!라고 되어있으나 개수가 없어서 회원명과 공급가액 비교
                for fail_xlsx in fail_xlsx_list:
                    wb_fail = openpyxl.load_workbook(fail_xlsx)
                    ws_fail = wb_fail.active
                    for j in range(6, ws_fail.i+1):
                        row_to_delete_fail = []
                        row = ''
                        member_store_fail = ws_fail['E' + str(j+1)].value
                        supply_value_fail = ws_fail['L' + str(j+1)].value
                        if (member_name == member_store_fail) and (supply_value == supply_value_fail):
                            retry_success_list = []
                            # 실패파일에서 정보 가져오기
                            kind = ws_fail['A' + str(j+1)].value
                            create_date = ws_fail['B' + str(j+1)].value
                            registration_number = ws_fail['C' + str(j+1)].value
                            member_name_fail = ws_fail['F' + str(j+1)].value
                            member_address_fail = ws_fail['G' + str(j+1)].value
                            member_email_fail = ws_fail['J' + str(j+1)].value
                            tax_fail = ws_fail['M' + str(j+1)].value
                            size = ws_fail['Q' + str(j+1)].value  # 계좌번호
                            amount = ws_fail['R' + str(j+1)].value
                            danga = ws_fail['S' + str(j+1)].value

                            retry_success_list = [
                                '01',
                                str(payment_date.strftime('%Y%m%d')),
                                registration_number,
                                '',
                                member_store_fail,
                                member_name_fail,
                                member_address_fail,
                                "",
                                "",
                                member_email_fail,
                                "",
                                supply_value_fail,
                                tax_fail,
                                "(기업은행) 333-048573-01-028 (주)제이티통신",
                                str(payment_date.day),
                                "아이알리미(전자출결 시스템 서비스)_" + str(amonth_ago.month) + "월",
                                size,
                                amount,
                                danga,
                                supply_value_fail,
                                tax_fail,
                            ]

                            data_to_append_jtt.append(retry_success_list)

                            # 실패파일에서 지울 row
                            row_to_delete_fail.append(j+1)
                            #변환할 실패파일 추가

                            break

                        # 실패파일에서 데이터 지우기
                        for row in row_to_delete_fail:
                            if row == '':
                                pass
                            else:
                                ws_fail.delete_rows(int(row))
                            wb_fail.save(fail_xlsx)
            elif "재결제실패" in status:
                print("재결제실패")
                for fail_xlsx in fail_xlsx_list:
                    if str_m in fail_xlsx:
                        fail_df = pd.read_excel(fail_xlsx, header=5)
                        store_name_list_fail = list(fail_df.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())

                        wb_cms = openpyxl.load_workbook(cms_xlsx_path)
                        ws_cms = wb_cms.active

                        wb_fail = openpyxl.load_workbook(fail_xlsx)
                        ws_fail = wb_fail.active

                        if member_name in store_name_list_fail:
                            pass
                        else:
                            print("실패파일에 내용 추가")
                            row_mx = get_i(ws_fail)
                            cd3 = payment_date.strftime('%Y-%m-%d')
                            ws_fail["B" + str(row_mx)].value = cd3
                            ws_fail["E" + str(row_mx)].value = ws_cms["D" + str(i+1)].value
                            # ws_fail["N" + str(row_mx)].value = ws_cms["L" + str(i+1)].value
                            ws_fail["L" + str(row_mx)].value = ws_cms["O" + str(i+1)].value
                            ws_fail["M" + str(row_mx)].value = ws_cms["P" + str(i+1)].value
                            ws_fail["T" + str(row_mx)].value = ws_cms["O" + str(i+1)].value
                            ws_fail["U" + str(row_mx)].value = ws_cms["P" + str(i+1)].value
                            ws_fail["O" + str(row_mx)].value = str_d
                            # 재결제실패 데이터 처리 후, 리스트에 경로 담기
                            wb_fail.save(fail_xlsx)
            else:
                print("당월 결제 실패 파일에 추가하기")
                print("결제일 파일에서 삭제")
                # 서비스 이용료 엑셀에서 정보 가져오기
                for fail_xlsx in fail_xlsx_list:
                    if today.strftime('%m')+'99' in fail_xlsx:
                        data_to_append_jtt = []
                        row_to_delete_fail = []
                        row = ''
                        wb_fail = openpyxl.load_workbook(fail_xlsx)
                        ws_fail = wb_fail.active
                        df2 = pd.read_excel(fail_xlsx, header=5)
                        member_name_fail = list(df2.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
                        man_fail = list(df2.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())
                        for j in range(6, ws_jtt.i+1):
                            member_store_jtt = ws_jtt['M' + str(j)].value
                            supply_value_jtt = ws_jtt['T' + str(j)].value
                            # 공급자 이름과 공급가액이 같으면
                            if member_store_jtt == member_name and supply_value == supply_value_jtt:
                                # 서비스 이용료 엑셀에서 삭제할 row: row_to_delete_jtt에 row 추가
                                row_to_delete_jtt.append(j)
                                # 결제실패인 정보 담기기
                                fail_list = []
                                for k in range(1, ws_jtt.max_column+1):
                                    fail_list.append(ws_jtt.cell(row=j, column=k).value)

                                data_to_append_fail.append(fail_list)
                                for data in data_to_append_fail:
                                    if (data[12] not in member_name_fail) and (data[13] not in man_fail):
                                        if data[12] not in member_name_fail:
                                            ws_fail.append(data)
                                wb_fail.save(fail_xlsx)

                            elif (member_store_jtt is None) and (supply_value_jtt is None):
                                break
                        df2 = pd.read_excel(fail_xlsx, header=5)
                        member_name_fail = list(df2.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
                        supply_value_fail = list(df2.dropna(axis=0, subset=["공급가액"])["공급가액"].unique())
                        supply_value_int = list(map(int, supply_value_fail))

                        #중복을 피함
                        if (ws_cms["D" + str(i + 1)].value not in member_name_fail) and (ws_cms["O" + str(i + 1)].value not in supply_value_int):
                            print("실패파일에 내용 추가")
                            row_mx = get_i(ws_fail)
                            cd3 = payment_date.strftime('%Y%m%d')
                            ws_fail["B" + str(row_mx)].value = cd3
                            ws_fail["E" + str(row_mx)].value = ws_cms["D" + str(i + 1)].value
                            ws_fail["L" + str(row_mx)].value = ws_cms["O" + str(i + 1)].value
                            ws_fail["M" + str(row_mx)].value = ws_cms["P" + str(i + 1)].value
                            ws_fail["T" + str(row_mx)].value = ws_cms["O" + str(i + 1)].value
                            ws_fail["U" + str(row_mx)].value = ws_cms["P" + str(i + 1)].value
                            ws_fail["O" + str(row_mx)].value = str_d
                            wb_fail.save(fail_xlsx)

                            # 서비스 이용료 엑셀에서 삭제할 row
                            # row_to_delete_jtt.append(j)

                        print("결제실패")

            for row in row_to_delete_jtt:
                if row == '':
                    pass
                else:
                    ws_jtt.delete_rows(int(row))
                    wb_jtt.save(jtt_xlsx)

            # 재결제성공 데이터, 결제일 엑셀에 추가
            for data in data_to_append_jtt:
                df = pd.read_excel(jtt_xlsx, header=5)
                create_date_jtt = list(df.dropna(axis=0, subset=['작성일자'])["작성일자"].unique())
                member_name_jtt = list(df.dropna(axis=0, subset=['공급받는자 상호'])["공급받는자 상호"].unique())
                supply_value_jtt = list(df.dropna(axis=0, subset=['공급가액'])["공급가액"].unique())
                supply_int = list(map(int, supply_value_jtt))
                if (data[12] not in member_name_jtt) or (data[19] not in supply_int) and (
                        data[2] not in create_date_jtt):
                    ws_jtt.append(data)
            wb_jtt.save(jtt_xlsx)

        print("cms 파일 비교 완료")
        xlsx2xls(os.listdir(folder_xlsx_path))
        return xlsx_to_convert

def main(cms_xls):
    if '학원' in cms_xls:
        print(cms_xls)
        if ('2022' in cms_xls) or ('2023' in cms_xls):
            print("해당연도있음")
            if (str(today.year)+today.strftime('%m') in cms_xls):
                print("1월용")
                fail_xlsx_list, jtt_xlsx_list, cms_xlsx_path, payment_date = init_xlsx_folder(cms_xls)
                # 월별내역에 추가하는 함수
                monthly_excel_append(cms_xlsx_path, payment_date)
                # 재결제성공과 결재실패시에 처리하는 파일
                xlsx_to_convert = cms_check(fail_xlsx_list, cms_xlsx_path, jtt_xlsx_list, payment_date)
            else:
                print("3검증에서 탈락")
                pass

    else:
        print(cms_xls +" 학원차례")

if __name__ == "__main__":
    start_time = datetime.now()
    print(start_time)
    main()
    print(datetime.now() - start_time)


    # 방법1. 변수로 받고 -> 정규식으로 처리해요
    # 방법2. 변수로 받아요 -> datetime으로 변환 한 후, month만 ge