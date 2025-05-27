import os
import glob
import shutil

file_path= 'C:\\Users\\vivans\\Desktop\\제출전\\'
move_path = 'C:\\ArgosRPA\\print\\'


def main(checklist):
    #최신파일 가져오기
    flist = sorted(glob.glob(file_path + '*.pdf'), key=os.path.getmtime)
    if len(flist) == 0:
        result ='nothing'
        return result
    else:
        if not flist:
            flist = sorted(glob.glob(file_path + '*.jpg'), key=os.path.getmtime)
            if not flist:
                flist = sorted(glob.glob(file_path + '*.png'), key=os.path.getmtime)
        #리스트에서 꺼내기
        r_len = len(flist) - 1
        #파일 이름
        r_file = flist[r_len]
        #파일이름 가져오기 위해서 나누기
        a = r_file.split('\\')
        f_name = len(a)-1
        file_name = a[f_name]
        if 'DWG' in file_name:
            choice = "DWG"
        elif 'CERT' in file_name:
            choice = "CERT"
        elif 'PHOTO' in file_name:
            choice = "PHOTO"
        else:
            choice ='nothing'

        result = r_file+','+choice

        return result

if __name__ == "__main__":
    main('aa')

