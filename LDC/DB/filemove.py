import os
import glob
import shutil

file_path= 'C:\\Users\\vivans\\Desktop\\제출전\\'
move_path = 'C:\\Users\\vivans\\Desktop\\제출후\\'


def main(checklist):
    #최신파일 가져오기
    xlsx_file = sorted(glob.glob(file_path + '*.xlsx'), key=os.path.getmtime)
    attach_file = sorted(glob.glob(file_path + '*.pdf'), key=os.path.getmtime)
    if not attach_file:
        attach_file = sorted(glob.glob(file_path + '*.jpg'), key=os.path.getmtime)
        if not attach_file:
            flist = sorted(glob.glob(file_path + '*.png'), key=os.path.getmtime)
    #리스트에서 꺼내기
    x_len = len(xlsx_file) - 1
    x_file = xlsx_file[x_len]
    x = x_file.split('\\')
    x2 = len(x) - 1
    x_file_name = x[x2]
    shutil.move(os.path.join(file_path, x_file_name), os.path.join(move_path + x_file_name))
    ## attach file이 있는 경우
    if attach_file:
        a_len = len(attach_file) -1
        a_file = attach_file[a_len]
    #파일이름 가져오기 위해서 나누기
        a = a_file.split('\\')
        a2 = len(a)-1
        a_file_name = a[a2]
        shutil.move(os.path.join(file_path, a_file_name), os.path.join(move_path + a_file_name))

if __name__ == "__main__":
    main('aa')

