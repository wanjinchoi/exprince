import openpyxl


def main(change_xlsx):

    wb = openpyxl.load_workbook(change_xlsx)
    ws = wb.active
    ref = ws['A14'].value
    ref_no = ref.replace('CUSTOMER NO. ', '')

    return ref_no



if __name__ == "__main__":
    main()

