import os
import glob

file_path= 'C:\\Users\\user\\Downloads\\'
move_path = 'C:\\ArgosRPA\\print\\'



def main(checklist):
    #옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(move_path + '*.pdf'), key=os.path.getmtime)
    f_len = len(flist) - 1
    # 파일 이름
    f_file = flist[f_len]
    return f_file

if __name__ == "__main__":
    main('aa')

