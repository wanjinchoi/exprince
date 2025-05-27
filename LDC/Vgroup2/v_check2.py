import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import glob

today = datetime.today()
oneday_ago = today -relativedelta(days=1)
twoday_ago = today - relativedelta(days=2)


form_path = 'C:\\ArgosRPA\\vgroup\\form2\\'
load_path = 'C:\\ArgosRPA\\vgroup\\form2\\' + today.strftime('%m%d') + 'V_Name2.xlsx'
oneday_ago_path = 'C:\\ArgosRPA\\vgroup\\form2\\'+oneday_ago.strftime('%m%d')+'V_Name2.xlsx'
twoday_ago_path = 'C:\\ArgosRPA\\vgroup\\form2\\' + twoday_ago.strftime('%m%d') + 'V_Name2.xlsx'


def main(checklist):
    list = sorted(glob.glob(form_path + '*.xlsx'), key=os.path.getmtime)
    #[os.remove(f) for f in glob.glob('C:\\ArgosRPA\\vgroup\\excel\\*.csv')]
    form_path_file =list[-1]
    wb_ck = openpyxl.load_workbook(form_path_file)
    ws_ck = wb_ck.active
    #if os.path.isfile(twoday_ago_path) == True:
        #os.remove(twoday_ago_path)
    a =[]
    b= []
    for i in range(2, ws_ck.max_row+2):
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
    main('aa')

