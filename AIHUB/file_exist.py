import os
import glob




file_path= 'C:\\Users\\vivans\\Downloads\\html\\'

def main(checklist):
    flist = sorted(glob.glob(file_path + '*.html'), key=os.path.getmtime)
    x = len(flist)

    if x ==0:
        b = 'no'
        return b
    else:
        b = 'yes'
        return b


if __name__ == "__main__":
    main('aa')

