import glob
import os
import shutil
from datetime import datetime


def main(checklist):
    download_path = 'C:\\Users\\vivans\\Downloads\\'
    move_path = 'C:\\ARGOS RPA\\senario1\\SK\\excel\\'

    # 옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(download_path + '*.xlsx'), key=os.path.getmtime)
    r_len = len(flist)-1
    # 파일 이름
    r_file = flist[r_len]
    # 파일이름 가져오기 위해서 나누기
    a = r_file.split('\\')
    file_name = a[4]
    # 파일 옮기기
    shutil.move(os.path.join(download_path, file_name), os.path.join(move_path + file_name))


if __name__ == "__main__":
    main('aa')
