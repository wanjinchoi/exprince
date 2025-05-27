import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import glob



today = datetime.today()
aday_ago = today - relativedelta(day=1)
today_file = today.strftime('%m%d')

load_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\'+today.strftime('%m%d')+'V_Name(EU).xlsx'
file_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\'
# file_path = 'C:\\Users\\vivans\\Desktop\\제출전\\'
# load_path = 'C:\\Users\\vivans\\Desktop\\제출전\\'+today.strftime('%m%d')+'V_Name(EU).xlsx'

#name_path='C:\\ArgosRPA\\meps\\form\\m_name.xlsx'
#load_path = 'C:\\work\\LDC\\meps\\'+today.strftime('%m%d')+'m_name.xlsx'

def main(checklist):
    flist = sorted(glob.glob(file_path + '*.xlsx'), key=os.path.getmtime)
    x = len(flist)
    b = x-1
    excel_file = flist[b]
    file_exit = os.listdir(file_path)

    if today.strftime('%m%d')+'V_Name(EU).xlsx' in file_exit:
        pass
    else:
        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active
        wb.save(load_path)
        wb.close()

    wb_ck = openpyxl.load_workbook(load_path)
    ws_ck = wb_ck.active
    a =[]
    b= []


    for i in range(2,ws_ck.i+1):
        if ws_ck["B"+str(i)].value is None:
            pass

        if checklist == str(ws_ck['B'+str(i)].value):
           a = 'B'+str(i)
           # A열의 최대 로우 구하기
           i = max((a.row for a in ws_ck['A'] if a.value is not None))
           row = i+1
           a_row = row-i
           ws_ck.move_range(a, rows=a_row, cols=-1)
           wb_ck.save(load_path)
           if ws_ck['B'+str(i)].value is not None:
               a = 'B' + str(i)
               # A열의 최대 로우 구하기
               i = max((a.row for a in ws_ck['A'] if a.value is not None))
               row = i + 1
               a_row = row - i
               ws_ck.move_range(a, rows=a_row, cols=-1)
               wb_ck.save(load_path)

    i = max((a.row for a in ws_ck['A'] if a.value is not None))


    return str(ws_ck["B"+str(i)].value)




if __name__ == "__main__":
    main(3333)

