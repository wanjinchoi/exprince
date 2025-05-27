import os
import glob
import shutil
from datetime import datetime


today = datetime.today()
today_folder_name = today.strftime('%Y%m%d')

# file_path= 'C:\\Users\\vivans\\Downloads\\'
# move_path = 'C:\\work\\\LDC\\form\\'+today.strftime('%Y%m%d')+'\\'
# folder_path = 'C:\\work\\LDC\\form\\'

file_path= 'C:\\Users\\AUTO-1\\Downloads\\'
move_path = 'C:\\ArgosRPA\\vgroup\\print\\'+today.strftime('%Y%m%d')+'\\'
folder_path = 'C:\\ArgosRPA\\vgroup\\print\\'




def main(checklist):
    #최신파일 가져오기
    flist = sorted(glob.glob(file_path + '*.pdf'), key=os.path.getmtime)
    #리스트에서 꺼내기
    r_len = len(flist) - 1
    #파일 이름
    r_file = flist[r_len]
    #파일이름 가져오기 위해서 나누기
    a = r_file.split('\\')
    file_name = a[4]
    folder_list = os.listdir(folder_path)
    if today_folder_name in folder_list:
        pass
    else:
        os.mkdir(move_path)
    #파일 옮기기
    shutil.move(os.path.join(file_path,file_name),os.path.join(move_path+file_name))

if __name__ == "__main__":
    main('aa')

