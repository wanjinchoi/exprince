import os
import glob
import win32com.client as win32
import time

file_path= 'C:\\Users\\vivans\\Desktop\\제출전\\'



def xls2xlsx(f_file):
    if os.path.isfile(f_file + "x"):
        os.remove(f_file+"x")

    wb = win32.gencache.EnsureDispatch('Excel.Application').Workbooks.Open(f_file)

    wb.SaveAs(f_file + "x", FileFormat=51)
    wb.Close()

    win32.gencache.EnsureDispatch('Excel.Application').Application.Quit()
    time.sleep(1)

    xlsx_path = f_file + "x"

    os.remove(f_file)

    return xlsx_path








def main(checklist):
    #옮긴 파일 내에서 최신파일 가져오기

    flist = sorted(glob.glob(file_path + '*.xls'), key=os.path.getmtime)
    f_len = len(flist) - 1
    # 파일 이름
    f_file = flist[f_len]
    r_file = xls2xlsx(f_file)

    return r_file








if __name__ == "__main__":
    main('aa')

