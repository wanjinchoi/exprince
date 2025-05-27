import openpyxl
import pandas as pd
#name_path='C:\\ArgosRPA\\form\\Name.xlsx'
excel_path= 'C:\\ArgosRPA\\meps\\excel\\'

def main(checklist):
    try:
        df = pd.read_csv(excel_path+'meps.csv', encoding='cp949',sep='\t')
        df.to_excel(excel_path+'meps.xlsx', index=False)
    except:
        wb = openpyxl.load_workbook(excel_path+'meps.xlsx')
        ws = wb.active
        wb.remove(ws)
        wb.create_sheet('Sheet1')
        wb.save(excel_path+'meps.xlsx')

if __name__ == "__main__":
    main('aa')

