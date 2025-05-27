import glob
import os
import shutil
from datetime import datetime
from datetime import datetime, timedelta


def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

    yesterday_date = current_date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    folder_path = 'Z:\\viet\\all_images\\'+current_date_str+'\\'
    flist = sorted(glob.glob(folder_path + '*.png'), key=os.path.getmtime)
    if len(flist) > 1200:
        a='yes'
        return a
    else:
        b='no'
        return b

if __name__ == "__main__":
    main('aa')

