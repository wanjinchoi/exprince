import glob
import os
import shutil
from datetime import datetime


def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    detect_folder = 'Z:\\viet\\detection_screenshots\\'
    move_path ='Z:\\viet\\send_screens\\'+current_date_str +'\\'
    # 부모 폴더와 현재 날짜를 결합하여 새 폴더 경로 생성

    # 새 폴더 생성
    if os.path.exists(move_path):
        pass
    else:
        os.makedirs(move_path)

    # 옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(detect_folder + '*.png'), key=os.path.getmtime)
    r_len = len(flist) - 1
    # 파일 이름
    for i in range(0, r_len + 1):
        r_file = flist[i]
        # 파일이름 가져오기 위해서 나누기
        a = r_file.split('\\')
        file_name = a[-1]
        # 파일 옮기기
        shutil.move(os.path.join(detect_folder, file_name), os.path.join(move_path + file_name))


if __name__ == "__main__":
    main('aa')
