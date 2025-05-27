import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

today = datetime.today()
oneday_ago = today -relativedelta(days=1)
twoday_ago = today - relativedelta(days=2)
#form_path = 'C:\\work\\LDC\\m_name.xlsx'
#load_path = 'C:\\work\\LDC\\meps\\' + today.strftime('%m%d') + 'm_name.xlsx'
#twoday_ago_path = 'C:\\work\\LDC\\meps\\' + twoday_ago.strftime('%m%d') + 'm_name.xlsx'


form_path='C:\\ArgosRPA\\form\\Name.xlsx'
load_path ='C:\\ArgosRPA\\meps\\form\\'+today.strftime('%m%d')+'m_name.xlsx'
oneday_ago_path = 'C:\\ArgosRPA\\meps\\form\\'+oneday_ago.strftime('%m%d')+'m_name.xlsx'
twoday_ago_path ='C:\\ArgosRPA\\meps\\form\\'+twoday_ago.strftime('%m%d')+'m_name.xlsx'



def main(checklist):
    if os.path.isfile(load_path) == True:
        wb_ck = openpyxl.load_workbook(load_path)
        ws_ck = wb_ck.active
    else:
        wb_ck = openpyxl.load_workbook(oneday_ago_path)
        ws_ck = wb_ck.active
        wb_ck.save(load_path)
    if os.path.isfile(twoday_ago_path) == True:
        os.remove(twoday_ago_path)
    a =[]
    b= []
    for i in range(2, ws_ck.i+2):
        complete = ws_ck["A"+str(i)].value
        a.append(complete)
        doit = ws_ck["B"+str(i)].value
        b.append(doit)

    if checklist in a:
        result = checklist
        return result
    else:
        if checklist not in b:
            ws_ck["B2"].value = checklist
            wb_ck.save(load_path)
            result ="doit"
            return result










if __name__ == "__main__":
    main()

