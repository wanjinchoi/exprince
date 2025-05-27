import openpyxl


name_path='C:\\ArgosRPA\\meps\\form\\m_name.xlsx'
#name_path='C:\\work\\LDC\\Name.xlsx'

def main(checklist):
    wb_ck = openpyxl.load_workbook(name_path)
    ws_ck = wb_ck.active

    a = []

    for i in range(2, ws_ck.i+1):
        if ws_ck['B'+str(i)].value is None:
            break
        a.append(ws_ck['B'+str(i)].value)

    return len(a)




if __name__ == "__main__":
    main('000003132777')

