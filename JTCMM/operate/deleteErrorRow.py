from openpyxl import load_workbook


# CNPLUS 파일업로드 시 오류발생 리스트는 삭제 및 오류 사유 기재
def main(error_path, file_path):
    err_wb = load_workbook(error_path)
    wb = load_workbook(file_path)
    ws = wb.active
    for i in range(len(err_wb.active['A'])-1):
        err = err_wb.active['E'+str(i+2)].value
        for j in range(len(ws['E'])):
            if ws['E'+str(j+2)].value == err:
                ws.delete_rows(j+2)
    wb.save(file_path)


if __name__ == '__main__':
    main(r'C:\work\JTCMM\operate\230309 개인단말기 CN오류.xlsx',r'C:\work\JTCMM\operate\230309 개인단말기.xlsx')
