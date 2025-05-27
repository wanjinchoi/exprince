import os
from datetime import datetime, timedelta
import glob

def main(checklist):
    #all image폴더 pa
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    yesterday_date = datetime.now() - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    all_image_folder_path = 'Z:\\viet\\all_images\\'+current_date_str+'\\'

    flist = sorted(glob.glob(all_image_folder_path + '*.png'), key=os.path.getmtime)

    if len(flist) > 1200:
        result = 'yes'
        return result
    else:
        result = 'no'
        return result



if __name__ == "__main__":
    main('aa')