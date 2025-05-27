import os
import shutil
import time
from datetime import datetime

import openpyxl


today = datetime.today()
a = today.strftime('%y%m%d')
down_path='C:\\Users\\vivans\\Downloads\\'
new_path = 'C:\\work\\LDC\\'
name_path='C:\\work\\LDC\\Name.xlsx'
play_path =new_path+ a +'\\'

files = os.listdir(down_path)

for file in files:
    if 'xlsx' in file:
        shutil.move(down_path + file, play_path + file)




def main(a):
    files = os.listdir(down_path)

    for file in files:
        if 'xlsx' in file:
            shutil.move(down_path + file, play_path + file)

    files = os.listdir(play_path)
    for file in files:
          wb_ck = openpyxl.load_workbook(name_path)
          ws_ck = wb_ck.active
          for i in range(2, ws_ck.i+1):
            if file == ws_ck["B"+str(i)].value:
                result = 1
                return result
            if ws_ck["B"+str(i)].value is None:
                ws_ck["B"+str(i)].value = file
                wb_ck.save(name_path)
                result = file
                return file





if __name__ == "__main__":
    main(a)

