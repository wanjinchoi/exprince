import openpyxl
from datetime import datetime
from dateutil.relativedelta import relativedelta



#name_path='C:\\ArgosRPA\\form\\Name.xlsx'
# name_path='C:\\work\\LDC\\Name.xlsx'



today = datetime.today()
aday_ago = today - relativedelta(day=1)


def main(checklist):
    wb_ck = openpyxl.load_workbook(name_path)
    ws_ck = wb_ck.active
    a =[]
    b= []

    for i in range(2,ws_ck.i+1):
        if ws_ck["B"+str(i)].value is not None:
            a.append(ws_ck["B"+str(i)].value)
            b.append(i)

        if ws_ck["B"+str(i)].value is None:
            pass



if __name__ == "__main__":
    main('000015100227')

