import os
import shutil
from datetime import datetime, timedelta
import glob

def main(folder_name):
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y%m%d")

    # 다운로드 폴더와 목적지 폴더의 경로를 설정합니다.
    base_path = 'C:\\Users\\user\\Downloads\\'
    #base_path = 'C:\\Users\\vivans\\Desktop\\test\\'
    # base_path = 'C:\\Users\\vivans\\Downloads\\'
    folder_path = 'C:\\ArgosRPA\\'
    endfile_path = os.path.join(folder_path, current_date_str)

    # 목적지 폴더가 존재하지 않으면 생성합니다.
    if not os.path.exists(endfile_path):
        os.makedirs(endfile_path)

    # 다운로드 폴더 내 파일 목록을 조회합니다.
    flist = sorted(glob.glob(base_path + '*.xlsx'), key=os.path.getmtime)
    if flist:
        file_name = flist[-1]
        r_file_name = os.path.basename(file_name)

        # 파일을 목적지 폴더로 이동합니다.
        shutil.move(os.path.join(base_path, r_file_name),os.path.join(endfile_path, r_file_name))
    else:
        return 'no'


if __name__ == "__main__":
    main('선일')
