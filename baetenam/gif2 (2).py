import os
import shutil
from datetime import datetime, timedelta
import imageio
import openpyxl as op
import glob
import xlwings as xw


def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

    yesterday_date = current_date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    image_folder_path = 'Z:\\viet\\all_images\\'+yesterday_date_str+'\\'

    store_xlsx_path = 'Z:\\viet\\report\\' + yesterday_date_str + '_report' + '.xlsx'
    git_folder_path = 'Z:\\viet\\gif_folder\\' + yesterday_date_str

    flist = sorted(glob.glob(image_folder_path + '*.png'), key=os.path.getmtime)
    ## all image 내 파일 삭제
    if len(flist) > 0:
        for i in range(len(flist)):
            os.remove(flist[i])

    #gif 파일 이동
    gif_folder_path = 'Z:\\viet\\gif_folder\\'
    move_gif_path ='Z:\\viet\\store_gif\\'
    gif_list = sorted(glob.glob(gif_folder_path + '*.gif'), key=os.path.getmtime)
    if len(gif_list)> 0 :
        for i in range(len(gif_list)):
            r_file = gif_list[i]
            # 파일이름 가져오기 위해서 나누기
            a = r_file.split('\\')
            file_name = a[3]
            shutil.move(os.path.join(gif_folder_path, file_name), os.path.join(move_gif_path + file_name))




if __name__ == "__main__":
    main('aa')
