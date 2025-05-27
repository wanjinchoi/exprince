import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os




today = datetime.today()
aday_ago = today - relativedelta(day=1)



#load_path = 'C:\\work\\LDC\\form\\'+today.strftime('%m%d')+'Name.xlsx'

#name_path='C:\\ArgosRPA\\meps\\form\\m_name.xlsx'
load_path = 'C:\\ArgosRPA\\form\\'+today.strftime('%m%d')+'Name.xlsx'

def main(checklist):
    wb_ck = openpyxl.load_workbook(load_path)
    ws_ck = wb_ck.active
    a =[]
    b= []

    for i in range(2,ws_ck.max_row+1):
        if ws_ck["B"+str(i)].value is None:
            pass

        if checklist == str(ws_ck['B'+str(i)].value):
           a = 'B'+str(i)
           # A열의 최대 로우 구하기
           max_row = max((a.row for a in ws_ck['A'] if a.value is not None))
           row = max_row+1
           a_row = row-i
           ws_ck.move_range(a, rows=a_row, cols=-1)
           wb_ck.save(load_path)
           if ws_ck['B'+str(i)].value is not None:
               a = 'B' + str(i)
               # A열의 최대 로우 구하기
               max_row = max((a.row for a in ws_ck['A'] if a.value is not None))
               row = max_row + 1
               a_row = row - i
               ws_ck.move_range(a, rows=a_row, cols=-1)
               wb_ck.save(load_path)

    max_row = max((a.row for a in ws_ck['A'] if a.value is not None))




if __name__ == "__main__":
    main()

