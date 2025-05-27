import glob
import os
import shutil
from datetime import datetime


def main(file_index):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = 'Z:\\viet\\send_screens\\'+current_date_str+'\\'
    flist = sorted(glob.glob(folder_path + '*.png'), key=os.path.getmtime)
    # result = len(flist)
    try:
        result = flist[int(file_index)]
        return result
    except IndexError:
        return 'no'


if __name__ == "__main__":
    main('1')

