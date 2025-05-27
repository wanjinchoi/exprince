import os
from dateutil.relativedelta import relativedelta
import openpyxl
from datetime import datetime
import glob
name_path='C:\\work\\LDC\\Name.xlsx'
today = datetime.today()
today = datetime.today()
oneday_ago = today -relativedelta(days=1)
twoday_ago = today - relativedelta(days=2)


#ARGOS
origianl_form_path = 'C:\\work\\LDC\\form\\'
load_path = 'C:\\work\\LDC\\form\\'+today.strftime('%m%d')+'V_Name.xlsx'
nulack_filepath = 'C:\\work\\LDC\\nulack\\'+today.strftime('%m%d')+'nulack_Name.xlsx'
nulack_path = 'C:\\work\\LDC\\nulack\\'
form_path = 'C:\\work\\LDC\\form\\nulack.xlsx'

#LDC
# origianl_form_path = 'C:\\ArgosRPA\\form\\'
# load_path = 'C:\\ArgosRPA\\form\\'+today.strftime('%m%d')+'Name.xlsx'
# nulack_filepath = 'C:\\ArgosRPA\\nulack\\'+today.strftime('%m%d')+'nulack_Name.xlsx'
# nulack_path = 'C:\\ArgosRPA\\nulack\\'
# form_path = 'C:\\ArgosRPA\\form\\nulack.xlsx'


def main(paper_num):
    #form양식 엑셀파일 있는지 여부확인
    o_list = sorted(glob.glob(origianl_form_path + '*.xlsx'), key=os.path.getmtime)
    list = sorted(glob.glob(nulack_path + '*.xlsx'), key=os.path.getmtime)
    form_path_file =list[-1]
    origin_form_path_file = o_list[-1]
    if paper_num =='' or paper_num is None:
        b = 'no'
        return b

    else:
        wb_or = openpyxl.load_workbook(origin_form_path_file)
        ws_or = wb_or.active
        wb_ck = openpyxl.load_workbook(form_path_file)
        ws_ck = wb_ck.active
        or_complete_list = [cell.value for cell in ws_or['A']]
        complete_list = [cell.value for cell in ws_ck['A']]
        if (paper_num in complete_list) or (paper_num in or_complete_list):
            b = 'yes'
            return b
        else:
            nulack_exist = os.listdir(nulack_path)
            if today.strftime('%m%d')+'nulack_Name.xlsx' in nulack_exist:
                wb = openpyxl.load_workbook(nulack_filepath)
                ws = wb.active
                max_row = max((a.row for a in ws['A'] if a.value is not None))
                if ws['A'+str(max_row)].value == paper_num:
                    pass
                else:
                    ws['A' + str(max_row + 1)].value = paper_num
                    wb.save(nulack_filepath)
                wb.close()
            else:
                wb = openpyxl.load_workbook(form_path_file)
                ws = wb.active
                max_row = max((a.row for a in ws['A'] if a.value is not None))
                ws['A'+str(max_row+1)].value = paper_num
                wb.save(nulack_filepath)
                wb.close()
            b='no'
            return b
if __name__ == "__main__":
    main('HFRE-0066-2025-M')

