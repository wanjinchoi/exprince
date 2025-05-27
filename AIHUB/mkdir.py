import os
import shutil
from datetime import datetime

sesco_path = 'C:\\ARGOS RPA\\지로서 다운로드\\세스코\\'
hanjun_path = 'C:\\ARGOS RPA\\지로서 다운로드\\한전\\'
asone_path = 'C:\\ARGOS RPA\\지로서 다운로드\\에스원\\청구서\\'
asonetax_path = 'C:\\ARGOS RPA\\지로서 다운로드\\에스원\\세금계산서\\'


# sesco_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\세스코\\'
# hanjun_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\한전\\'
# asone_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\에스원\\청구서\\'
# asonetax_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\에스원\\세금계산서\\'

today = datetime.today()
today_month=today.strftime('%Y%m')

def main(checklist):
    sesco_exist = os.listdir(sesco_path)
    hanjun_exist = os.listdir(hanjun_path)
    asone_exist = os.listdir(asone_path)
    asonetax_exist = os.listdir(asonetax_path)

    if today_month in sesco_exist:
            pass
    else:
        os.mkdir(sesco_path+today_month)

    if today_month in hanjun_exist:
        pass
    else:
        os.mkdir(hanjun_path+today_month)

    #에스원 청구서
    if today_month in asone_exist:
            pass
    else:
        os.mkdir(asone_path + today_month)
    #에스원 전자세금계산서
    if today_month in asonetax_exist:
        pass
    else:
        os.mkdir(asonetax_path+today_month)

if __name__ == "__main__":
    main('aa')