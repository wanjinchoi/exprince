import openpyxl

name_path='C:\\ArgosRPA\\porcure\\form\\p_name.xlsx'
#name_path='C:\\work\\LDC\\Name.xlsx'

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

    return len(a), b

if __name__ == "__main__":
    main()

