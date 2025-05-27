import os
import glob
import shutil
from datetime import datetime



file_path= 'C:\\Users\\vivans\\Downloads\\html\\'
asone_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\에스원\\'
today = datetime.today()


today_file_path = 'C:\\ArgosRPA\\print\\'+today.strftime('%m%d')+'\\'
yesterday_folder_path = 'C:\\ArgosRPA\\print\\'+today.strftime('%m%d')+'\\'
def main(checklist):
    # 이동파일경로 가져오기
    folder = os.listdir(asone_path)
    x = len(folder)-1
    move_path = asone_path + folder[x]+'\\'
    #최신파일 가져오기
    #리스트에서 꺼내기
    flist = sorted(glob.glob(file_path + '*.html'), key=os.path.getmtime)
    for i in range(0,len(flist)):
        flist = sorted(glob.glob(file_path + '*.html'), key=os.path.getmtime)
        r_len = len(flist) - 1
        #파일 이름
        r_file = flist[r_len]
        #파일이름 가져오기 위해서 나누기
        a = r_file.split('\\')
        file_name = a[5]
        #파일 옮기기
        shutil.move(os.path.join(file_path,file_name),os.path.join(move_path+file_name))
if __name__ == "__main__":
    main('aa')

