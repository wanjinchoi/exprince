from openpyxl import load_workbook


def main(file_path):
    wb = load_workbook(file_path)
    ws = wb.active
    return ws.i - 1


if __name__ == '__main__':
    main(r'C:\work\JTCMM\operate\230306 개인단말기.xlsx')

