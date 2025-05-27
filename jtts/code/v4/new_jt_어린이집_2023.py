import os
import re
import shutil
import time
from datetime import datetime
from distutils.dir_util import copy_tree

import openpyxl
import pandas as pd
import win32com.client as win32
from dateutil.relativedelta import relativedelta

today = datetime.today()
amonth_ago = today - relativedelta(months=1)
aday_ago = today - relativedelta(day=1)
two_month_ago = today - relativedelta(months=2)
three_month_ago = today - relativedelta(months=3)
f_month_ago = today - relativedelta(months=4)

root_path = 'C:\\RPA\\어린이집\\'
folder_path = 'C:\\RPA\\어린이집\\' + today.strftime('%Y') + '년\\' + today.strftime('%Y') + '.' + amonth_ago.strftime('%m')
folder_xlsx_path = folder_path + '\\xlsx'
today_xls_path = folder_path + '\\' + today.strftime('%m%d') + today.strftime('. %y%m%d') + ' 청구지역 CMS전자세금계산서발행★ (' + str(amonth_ago.month) + '월분이용료).xls'
fail_xls = folder_path + '\\' + today.strftime('%m') + '99. ' + today.strftime('%y')+ today.strftime('%m') + '99 100건이상 청구지역 CMS전자세금계산서발행★ (' + str(amonth_ago.month) + '월분이용료) - 출금실패.xls'
today_fail_xlsx = folder_path + '\\' + today.strftime('%m') + '99. ' + today.strftime('%y%m') + '99 100건이상 청구지역 CMS전자세금계산서발행★ (' + str(today.month) + '월분이용료) - 출금실패.xlsx'
backup_path = 'C:\\RPA\\백업'


# 3###############################################
# 실패 파일의 마지막행 구하기
def jttxlsx2xls(xlsx_path):
    if 'template' in xlsx_path:
        pass
    else:
        file_name = xlsx_path[:-1]
        jtt_xlsx_wb = openpyxl.load_workbook(xlsx_path)
        jtt_xlsx_ws = jtt_xlsx_wb.active
        jtt_xlsx_wb.save(file_name)
        os.remove(xlsx_path)

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


def xlsx2xls(fail_xlsx_list, cms_xlsx_path):
    payment_date_m= today.strftime('%m')
    payment_date_agom = amonth_ago.strftime('%#m')
    payment_date_tagom = two_month_ago.strftime('%#m')
    payment_date_fagom = three_month_ago.strftime('%#m')
    for fail_xlsx in fail_xlsx_list:
        if payment_date_agom+'월분이용료' in fail_xlsx:
            wb_xls = openpyxl.load_workbook(fail_xlsx)
            ws_xlsx = wb_xls.active
            xls_path = root_path+today.strftime('%Y')+'년\\'+amonth_ago.strftime('%Y.%m')
            file_name = fail_xlsx[:-1]
            r_filename = os.path.basename(file_name)
            dest = os.path.join(xls_path, r_filename)
            wb_xls.save(dest)
            wb_xls.close()
            os.remove(fail_xlsx)
        elif payment_date_tagom+'월분이용료' in fail_xlsx:
            wb_xls = openpyxl.load_workbook(fail_xlsx)
            ws_xlsx = wb_xls.active
            xls_path = root_path + amonth_ago.strftime('%Y') + '년\\' + two_month_ago.strftime('%Y.%m')
            file_name = fail_xlsx[:-1]
            r_filename = os.path.basename(file_name)
            dest = os.path.join(xls_path, r_filename)
            wb_xls.save(dest)
            wb_xls.close()
            os.remove(fail_xlsx)
        elif payment_date_fagom + '월분이용료' in fail_xlsx:
            wb_xls = openpyxl.load_workbook(fail_xlsx)
            ws_xlsx = wb_xls.active
            xls_path = root_path + two_month_ago.strftime('%Y') + '년\\' + three_month_ago.strftime('%Y.%m')
            file_name = fail_xlsx[:-1]
            r_filename = os.path.basename(file_name)
            dest = os.path.join(xls_path, r_filename)
            wb_xls.save(dest)
            wb_xls.close()
            os.remove(fail_xlsx)

    os.remove(cms_xlsx_path)

#  cms를 파일을 불러오는 함수
def init_xlsx_folder(cms_xls):
    # xlsx폴더가 있으면 삭제하는 코드
    if os.path.exists(folder_xlsx_path):
        shutil.rmtree(folder_xlsx_path)
    else:
        pass
    os.makedirs(folder_xlsx_path)
    # 결제실패 파일 xls을 xlsx로 변환하기 위한 함수 호출
    fail_xlsx_list = make_fail_xlsx(cms_xls)
    cms_xlsx_path = xls2xlsx(cms_xls)
    cms_xlsx_path = shutil.move(cms_xlsx_path, folder_xlsx_path)
    fail_xlsx_list, cms_xlsx_path = cms_check(fail_xlsx_list, cms_xlsx_path)
    xlsx2xls(fail_xlsx_list, cms_xlsx_path)

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
def make_fail_xlsx(cms_xls):
    # 당월, 전월, 전전월 실패 파일 찾기
    payment_xlsx_path_list = []
    # df = pd.read_excel(cms_xls)
    # payment_date_list = list(df.dropna(axis=0, subset=['결제일'])["결제일"].unique())
    payment_date = today.strftime('%Y%m%d')
    payment_date_y = today.strftime('%Y')
    payment_date_m = today.strftime('%m')
    payment_date_d = today.strftime('%d')
    payment_date_ago = amonth_ago
    payment_date_twoago = two_month_ago
    payment_date_three = three_month_ago

    amonth_ago_fail_xls = root_path + payment_date_twoago.strftime('%Y') + '년\\' + payment_date_twoago.strftime('%Y.')+ payment_date_twoago.strftime('%m') + '\\' + payment_date_ago.strftime('%m') + '99. ' + payment_date_ago.strftime('%y%m') + '99 100건이상 청구지역 CMS전자세금계산서발행★ (' + payment_date_twoago.strftime('%#m') + '월분이용료) - 출금실패.xls'
    two_month_ago_fail_xls = root_path + payment_date_twoago.strftime('%Y') + '년\\' + payment_date_three.strftime('%Y') + '.' + payment_date_three.strftime('%m') + '\\' + payment_date_twoago.strftime('%m') + '99. ' + payment_date_twoago.strftime('%y%m') + '99 100건이상 청구지역 CMS전자세금계산서발행★ (' + payment_date_three.strftime('%#m') + '월분이용료) - 출금실패.xls'

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
    m = payment_date.month
    payment_date_ago = payment_date - relativedelta(months=1)
    ago_m = m - 1
    monthly_template_path = 'C:\\work\\JTCMM\\test\\★월별출금내역\\2023년\\2023년 0월 출금내역.xlsx'
    if ago_m == 0 :
        m = 12
        monthly_excel_path = 'C:\\work\\JTCMM\\test\\★월별출금내역\\' + payment_date_ago.strftime('%Y') + '년\\' + payment_date_ago.strftime('%Y') + '년 ' + str(m) + '월 출금내역.xlsx'
    else:
        monthly_excel_path = 'C:\\work\\JTCMM\\test\\★월별출금내역\\' + payment_date.strftime('%Y') + '년\\' + payment_date.strftime('%Y') + '년 ' + str(ago_m) + '월 출금내역.xlsx'

    if os.path.isfile(monthly_excel_path):
        wb_monthly = openpyxl.load_workbook(monthly_excel_path)
        df = pd.read_excel(monthly_excel_path)
    else:
        wb_monthly = openpyxl.load_workbook(monthly_template_path)
        df = pd.read_excel(monthly_template_path)

    ws_monthly = wb_monthly.active
    wb_cms = openpyxl.load_workbook(cms_xlsx_path)
    ws_cms = wb_cms.active

    success_list = []
    # 반복하며 데이터 리스트에 넣기
    for i in range(1, ws_cms.i):
        tmp = []
        payment_date_list = list(df.dropna(axis=0, subset=["결제일"])["결제일"].unique())
        member_name_list = list(df.dropna(axis=0, subset=["회원명"])["회원명"].unique())
        try:
            for j in range(1, 21):
                if ws_cms.cell(i + 1, j).value =='합계':
                    break
                tmp.append(ws_cms.cell(i + 1, j).value)
            success_list.append(tmp)
        except TypeError as e:
            print("e")

    # 출금내역 붙여넣기
    # 중복값 제거
    for i in success_list:
        ws_monthly.append(i)

    # wb_monthly.save('월별출금금액.xlsx')
    wb_monthly.save(monthly_excel_path)

# 서비스 이용료 엑셀과 cms 엑셀의 결제상태 비교
def cms_check(fail_xlsx_list, cms_xlsx_path):
    xlsx_to_convert = []
    wb_cms = openpyxl.load_workbook(cms_xlsx_path)
    ws_cms = wb_cms.active

    for i in range(2, ws_cms.i + 1):
        status = ws_cms['I' + str(i)].value
        s_con = ws_cms['J' + str(i)].value
        r_pay = ws_cms['T' + str(i)].value
        sum = ws_cms['A'+str(i)].value

        if sum =='합계':
            break
        if s_con !='결제실패' and s_con !='결제완료':
            pass
        elif status !='미납' and status !='완납':
            pass
        elif (status =="미납") and (s_con=="결제실패") and (r_pay=='재결제'):
            pass
        elif (status == "미납") and (s_con == "결제실패") and (r_pay == '-'):

            #jtt 파일 가져오기
            x = ws_cms["O" + str(i)].value
            payment_date = datetime.strptime(x, '%Y-%m-%d')
            payment_date_a = payment_date.strftime('%m%d')
            payment_date_b = payment_date.strftime('%y%m%d')
            payment_date_ago = payment_date - relativedelta(months=1)
            payment_month = payment_date_ago.strftime('%m')
            jtt_xlsx_path_a = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            jtt_xlsx_path_b = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            # 일반 xls파일
            payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'
            # 100건 초과 xls파일
            payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'

            ex_payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            # 100건 초과 xls파일
            ex_payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'

            print(payment_xls_path_a)
            print(payment_xls_path_b)
            if os.path.exists(ex_payment_xls_path_a):
                print("a xslx파일 이미 있음")
                payment_xlsx_path = ex_payment_xls_path_a
                pass
            elif os.path.exists(ex_payment_xls_path_b):
                print("b xslx파일 이미 있음")
                payment_xlsx_path = ex_payment_xls_path_b
                pass
            elif os.path.exists(payment_xls_path_a):
                print("a")
                payment_xlsx_path = xls2xlsx(payment_xls_path_a)
            elif os.path.exists(payment_xls_path_b):
                print("b")
                payment_xlsx_path = xls2xlsx(payment_xls_path_b)
            else:
                if ws_cms.i >= 100:
                    payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template100.xlsx'
                else:
                    payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template.xlsx'

            df = pd.read_excel(payment_xlsx_path, header=5)
            sangho = list(df.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
            today_m = payment_date.strftime('%m')
            for ffail_xlsx in fail_xlsx_list:
                if today_m in ffail_xlsx:
                    fail_xlsx = ffail_xlsx
            print(ws_cms["D" + str(i)].value)

            df_fail = pd.read_excel(fail_xlsx, header=5)
            sangho2 = list(df_fail.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())

            #cms 파일 내용이 jtt에 있는지 확인
            if (ws_cms["D"+str(i)].value in sangho):
                print('jtt있는 내용을 fail로 옮기기' )
                #실패파일열기
                wb_fail = openpyxl.load_workbook(fail_xlsx)
                ws_fail = wb_fail.active
                e_row = max((a.row for a in ws_fail['E'] if a.value is not None))
                wb_jtt = openpyxl.load_workbook(payment_xlsx_path)
                ws_jtt = wb_jtt.active
                for j in range(7, ws_jtt.i + 1):
                    if ws_cms["D" + str(i)].value == ws_jtt.cell(row=j, column=5).value:
                        a = []
                        #jtt에 있는 내용 a에 담기
                        #52
                        for x in range(1,6):
                            a.append(ws_jtt.cell(row=j, column=x).value)
                        #list에 담고 그 내용 삭제하기
                        ws_jtt.delete_rows(j)
                        wb_jtt.save(payment_xlsx_path)
                        wb_jtt.close()
                        q=0
                        for w in range(1, ws_fail.max_column+1):
                            #53
                             if q == 5:
                                 break
                             else:
                                 ws_fail.cell(row=e_row+1, column=w).value =a[q]
                                 q +=1
                        wb_fail.save(fail_xlsx)
                        wb_fail.close()
                        xlsx2xls(payment_xlsx_path,payment_date)
                        break
            elif ws_cms["D" + str(i)].value in sangho2:
                jttxlsx2xls(payment_xlsx_path)
                pass
            else:
                wb_fail = openpyxl.load_workbook(fail_xlsx)
                ws_fail = wb_fail.active
                fail_row = max((a.row for a in ws_fail['E'] if a.value is not None))
                ws_fail["B"+str(fail_row+1)].value = payment_date.strftime('%Y%m%d')
                ws_fail["E"+str(fail_row+1)].value = ws_cms["D"+str(i)].value
                ws_fail["M" + str(fail_row+1)].value = ws_cms["V"+str(i)].value
                wb_fail.save(fail_xlsx)
                wb_fail.close()
                jttxlsx2xls(payment_xlsx_path)

        elif (status =="완납") and (s_con=="결제완료") and (r_pay=='-'):
            print('결제완료/ 완납 / -')
            x = ws_cms["O" + str(i)].value
            payment_date = datetime.strptime(x, '%Y-%m-%d')
            payment_date_a = payment_date.strftime('%m%d')
            payment_date_b = payment_date.strftime('%y%m%d')
            payment_date_ago = payment_date - relativedelta(months=1)
            payment_month = payment_date_ago.strftime('%m')
            jtt_xlsx_path_a = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            jtt_xlsx_path_b = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            # 일반 xls파일
            payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'
            # 100건 초과 xls파일
            payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'

            ex_payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
            # 100건 초과 xls파일
            ex_payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'

            print(payment_xls_path_a)
            print(payment_xls_path_b)
            if os.path.exists(ex_payment_xls_path_a):
                print("a xslx파일 이미 있음")
                payment_xlsx_path = ex_payment_xls_path_a
                pass
            elif os.path.exists(ex_payment_xls_path_b):
                print("b xslx파일 이미 있음")
                payment_xlsx_path = ex_payment_xls_path_b
                pass
            elif os.path.exists(payment_xls_path_a):
                print("a")
                payment_xlsx_path = xls2xlsx(payment_xls_path_a)
            elif os.path.exists(payment_xls_path_b):
                print("b")
                payment_xlsx_path = xls2xlsx(payment_xls_path_b)
            else:
                if ws_cms.i >= 100:
                    payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template100.xlsx'
                else:
                    payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template.xlsx'

            df_sucess = pd.read_excel(payment_xlsx_path, header=5)
            ssangho = list(df_sucess.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
            if ws_cms['D'+str(i)].value in ssangho:
                print("있음")
                jttxlsx2xls(payment_xlsx_path)
                pass
            else:
                print('없음')
                wb_jtt = openpyxl.load_workbook(payment_xlsx_path)
                ws_jtt = wb_jtt.active
                if '100건이상 ' in payment_xlsx_path:
                    jtt_row = max((a.row for a in ws_jtt['E'] if a.value is not None))
                    ws_jtt["B" + str(jtt_row + 1)].value = payment_date.strftime('%Y%m%d')
                    ws_jtt["E" + str(jtt_row + 1)].value = ws_cms["D" + str(i)].value
                    ws_jtt["M" + str(jtt_row + 1)].value = ws_cms["U" + str(i)].value
                    wb_jtt.save(payment_xlsx_path)
                    wb_jtt.close()
                    jttxlsx2xls(payment_xlsx_path)
                else:
                    jtt_row = max((a.row for a in ws_jtt['M'] if a.value is not None))
                    ws_jtt["B" + str(jtt_row + 1)].value = payment_date.strftime('%Y%m%d')
                    ws_jtt["B" + str(jtt_row + 1)].value = payment_date.strftime('%Y%m%d')
                    ws_jtt["M" + str(jtt_row + 1)].value = ws_cms["D" + str(i)].value
                    ws_jtt["T" + str(jtt_row + 1)].value = ws_cms["U" + str(i)].value
                    wb_jtt.save(payment_xlsx_path)
                    wb_jtt.close()
                    jttxlsx2xls(payment_xlsx_path)


        elif (status == "완납") and (s_con=="결제완료") and (r_pay=='재결제'):
             print("완납/ 결제완료 / 재결제")
             x = ws_cms["O" + str(i)].value
             payment_date = datetime.strptime(x, '%Y-%m-%d')
             payment_date_a = payment_date.strftime('%m%d')
             payment_date_b = payment_date.strftime('%y%m%d')
             payment_date_ago = payment_date - relativedelta(months=1)
             payment_month = payment_date_ago.strftime('%m')
             jtt_xlsx_path_a = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
             jtt_xlsx_path_b = root_path + payment_date_ago.strftime('%Y') + '년' + '\\' + payment_date_ago.strftime('%Y.') + payment_date_ago.strftime('%m') + '\\' + f'{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
             # 일반 xls파일
             payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'
             # 100건 초과 xls파일
             payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xls'

             ex_payment_xls_path_a = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'
             # 100건 초과 xls파일
             ex_payment_xls_path_b = root_path + f'{payment_date_ago.year}년\\{payment_date_ago.year}.{payment_month}\\{payment_date_a}. {payment_date_b} 100건이상 청구지역 CMS전자세금계산서발행★ ({payment_date_ago.month}월분이용료).xlsx'

             print(payment_xls_path_a)
             print(payment_xls_path_b)
             if os.path.exists(ex_payment_xls_path_a):
                 print("a xslx파일 이미 있음")
                 payment_xlsx_path = ex_payment_xls_path_a
                 pass
             elif os.path.exists(ex_payment_xls_path_b):
                 print("b xslx파일 이미 있음")
                 payment_xlsx_path = ex_payment_xls_path_b
                 pass
             elif os.path.exists(payment_xls_path_a):
                 print("a")
                 payment_xlsx_path = xls2xlsx(payment_xls_path_a)
             elif os.path.exists(payment_xls_path_b):
                 print("b")
                 payment_xlsx_path = xls2xlsx(payment_xls_path_b)
             else:
                 if ws_cms.i >= 100:
                     payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template100.xlsx'
                 else:
                     payment_xlsx_path = 'C:\\ARGOSRPA\\code\\template.xlsx'

             today_m = payment_date.strftime('%m')
             for ffail_xlsx in fail_xlsx_list:
                 if today_m in ffail_xlsx:
                     fail_xlsx = ffail_xlsx
             print(ws_cms["D" + str(i)].value)

             df_fail = pd.read_excel(fail_xlsx, header=5)
             sangho2 = list(df_fail.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())

             wb_fail = openpyxl.load_workbook(fail_xlsx)
             ws_fail = wb_fail.active
             wb_jtt = openpyxl.load_workbook(payment_xlsx_path)
             ws_jtt = wb_jtt.active
             df_fail = pd.read_excel(fail_xlsx)
             f_sangho = list(df_sucess.dropna(axis=0, subset=["공급받는자 상호"])["공급받는자 상호"].unique())
             if (ws_cms['D'+str(i)].value in f_sangho):
                 for j in range(7, ws_fail.i + 1):
                     if ws_cms['D'+str(i)].value == ws_fail.cell(row=j, column=5).value:
                         print('같음')
                         b = []
                         # 52
                         for x in range(1, 52):
                             a.append(ws_fail.cell(row=j, column=x).value)

                         ws_fail.delete_rows(j)
                         wb_fail.save(fail_xlsx)
                         wb_fail.close()

                         #jtt 최대로우 구하기
                         j_row = max((a.row for a in ws_jtt['E'] if a.value is not None))
                         e = 0
                         for w in range(1, ws_jtt.max_column + 1):
                             # 53
                             if e == 53:
                                 break
                             else:
                                 ws_jtt.cell(row=j_row + 1, column=w).value = a[e]
                                 e += 1
                         wb_jtt.save(payment_xlsx_path)
                         wb_jtt.close()
                         jttxlsx2xls(payment_xlsx_path)

             else:
                 jttxlsx2xls(payment_xlsx_path)
                 pass

    return fail_xlsx_list, cms_xlsx_path


def cmsfile_move(cms_xls):
    payment_date = today.strftime('%Y%m%d')
    payment_date_m = today.strftime('%m')
    payment_date_ago = amonth_ago.strftime('%#m')
    payment_date_twoago = two_month_ago.strftime('%#m')
    payment_date_three = three_month_ago.strftime('%#m')
    cms_name = os.path.basename(cms_xls)
    cmsfile_path ='C:\\ARGOSRPA\\세금계산서발행\\효성CMS엑셀\\2023\\'
    if '2023'+payment_date_m in cms_xls:
        cmsfile_move_path = cmsfile_path + payment_date_m + '월'
    elif '2023'+amonth_ago.strftime('%m') in cms_xls:
        cmsfile_move_path = cmsfile_path + payment_date_ago + '월'

    if not os.path.exists(cmsfile_move_path):
        os.makedirs(cmsfile_move_path)
    r_filename = os.path.basename(cms_xls)
    dest = os.path.join(cmsfile_move_path, r_filename)
    shutil.move(cms_xls,dest)
    print("cms파일 이동완료")

def main(cms_xls):
    if cms_xls not in '유치원':
        print("다음 차례로 이동합니다.")
    else:
        init_xlsx_folder(cms_xls)
        cmsfile_move(cms_xls)

if __name__ == "__main__":
    start_time = datetime.now()
    print(start_time)
    main(r'C:\Users\vivans\Desktop\stu_test\20230724_20230724_어린이집.xls')
    print(datetime.now() - start_time)

    # 방법1. 변수로 받고 -> 정규식으로 처리해요
    # 방법2. 변수로 받아요 -> datetime으로 변환 한 후, month만 get
