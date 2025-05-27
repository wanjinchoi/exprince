import os
import glob
import shutil
from datetime import datetime, timedelta

# 현재 날짜와 시간 가져오기
today = datetime.now()

# 어제 날짜 계산
yesterday = today - timedelta(days=1)
#ShipServ
# today_file_path = 'C:\\ArgosRPA\\print\\'+today.strftime('%Y%m%d')+'\\'
# yesterday_folder_path='C:\\ArgosRPA\\print\\'
# yesterday_folder = 'C:\\ArgosRPA\\print\\'+yesterday.strftime('%Y%m%d')+'\\'
# move_folder_path = 'C:\\ArgosRPA\\print\\기존파일들\\'
#Vgroup
today_file_path = 'C:\\ArgosRPA\\vgroup\\print\\'+today.strftime('%Y%m%d')+'\\'
yesterday_folder_path='C:\\ArgosRPA\\vgroup\\print\\'
yesterday_folder = 'C:\\ArgosRPA\\vgroup\\print\\'+yesterday.strftime('%Y%m%d')+'\\'
move_folder_path = 'C:\\ArgosRPA\\vgroup\\print\\기존파일들\\'


def main(checklist):
        shutil.move(os.path.join(yesterday_folder_path+yesterday.strftime('%Y%m%d')+'\\'), os.path.join(move_folder_path+yesterday.strftime('%Y%m%d')+'\\'))

        flist = sorted(glob.glob(today_file_path + '*.pdf'), key=os.path.getmtime)
        for i in range(0, len(flist)):
            flist = sorted(glob.glob(today_file_path + '*.pdf'), key=os.path.getmtime)
            r_len = len(flist) - 1
            # 파일 이름
            r_file = flist[r_len]
            # 파일이름 가져오기 위해서 나누기
            a = r_file.split('\\')
            file_name = a[4]
            # 파일 옮기기
            shutil.move(os.path.join(today_file_path, file_name), os.path.join(move_folder_path + file_name))
if __name__ == "__main__":
    main('aa')

