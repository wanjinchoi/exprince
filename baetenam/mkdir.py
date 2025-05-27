import os
import glob

folder_path= 'C:\\Users\\vivans\\Desktop\\detection_screenshots\\'

def main(checklist):
    #옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(folder_path + '*.png'), key=os.path.getmtime)
    if len(flist) == 0:
        b = 'no'
        return b
    else:
        f_len = len(flist)
        return f_len

if __name__ == "__main__":
    main('aa')

