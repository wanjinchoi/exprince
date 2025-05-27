import os
import glob
import shutil
from datetime import datetime


# download_path = 'C:\\Users\\AUTO-1\\Downloads\\'
download_path = 'C:\\Users\\vivans\\Downloads\\'
print_path = 'C:\\ArgosRPA\\vgroup\\print\\'



def main(checklist):

    flist = sorted(glob.glob(download_path + '*.pdf'), key=os.path.getmtime)

    f_len = len(flist) - 1
    # 파일 이름
    f_file = flist[f_len]
    #파일이름 가져오기 위해서 나누기
    time_stamp = os.path.getmtime(f_file)
    modified_date = datetime.fromtimestamp(time_stamp)
    a = f_file.split('\\')
    file_name = a[4]
    shutil.move(os.path.join(download_path+file_name),os.path.join(print_path+file_name))

if __name__ == "__main__":
    main('aa')

