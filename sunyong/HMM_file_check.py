import os
import glob

down_excel_path ='C:\\Users\\vivans\\Downloads\\'
def main(checklist):
    flist = sorted(glob.glob(down_excel_path + '*.xlsx'), key=os.path.getmtime)
    result = flist[-1]
    return result

if __name__ == "__main__":
    main('aa')

