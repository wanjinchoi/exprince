import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import glob

today = datetime.today()
oneday_ago = today -relativedelta(days=1)
twoday_ago = today - relativedelta(days=2)


form_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\'
load_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\' + today.strftime('%m%d') + 'V_Name(EU).xlsx'
oneday_ago_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\'+oneday_ago.strftime('%m%d')+'V_Name(EU).xlsx'
twoday_ago_path = 'C:\\ArgosRPA\\vgroup\\EU_form\\' + twoday_ago.strftime('%m%d') + 'V_Name(EU).xlsx'


def main(checklist):
    file = os.listdir(form_path)
    # 수정날짜 순으로 정리
    flist = sorted(glob.glob(form_path + '*.xlsx'), key=os.path.getmtime)
    r_len = len(flist) - 1
    r_file = flist[r_len]
    if os.path.isfile(load_path) == True:
        wb_ck = openpyxl.load_workbook(load_path)
        ws_ck = wb_ck.active
    else:
        file = os.listdir(form_path)
        # 수정날짜 순으로 정리
        flist = sorted(glob.glob(form_path + '*.xlsx'), key=os.path.getmtime)
        r_len = len(flist) - 1
        r_file = flist[r_len]
        wb_ck = openpyxl.load_workbook(r_file)
        ws_ck = wb_ck.active
    #if os.path.isfile(twoday_ago_path) == True:
        #os.remove(twoday_ago_path)
    a =[]
    b= []
    for i in range(2, ws_ck.i+2):
        complete = ws_ck["A"+str(i)].value
        a.append(complete)
        doit = ws_ck["B"+str(i)].value
        b.append(doit)

    if checklist in a:
        result = checklist
        wb_ck.close()
        return result
    else:
        if checklist not in b:
            ws_ck["B2"].value = checklist
            wb_ck.save(load_path)
            wb_ck.close()
            result ="doit"
            return result






if __name__ == "__main__":
    main()

