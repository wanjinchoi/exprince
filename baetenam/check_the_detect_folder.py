import glob
import os
import shutil
from datetime import datetime, timedelta



def main(checklist):
    detect_folder_path = 'C:\\ARGOSRPA\\Master Service\\Master_image\\detection_screenshots\\'
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    move_path = 'C:\\ARGOSRPA\\Master Service\\Master_image\\send_screens\\'+current_date_str +'\\'
    full_screen_shot_path = "C:\\ARGOSRPA\\Master Service\\Master_image\\Full screen\\"

    # 폴더가 없으면 생성
    if not os.path.exists(move_path):
        os.makedirs(move_path)

    # detecfolder 체크
    # '_af.png'로 끝나는 파일들만 검색하여 수정 시간 기준으로 정렬
    flist = sorted(glob.glob(os.path.join(detect_folder_path, '*_af.png')),key=os.path.getmtime)
    full_list = sorted(glob.glob(full_screen_shot_path + '*.png'), key=os.path.getmtime)
    if len(flist) < 1 and len(full_list) < 1 :
        result = '1'
        return result
    else:
        result = ','.join(flist)
        return result


if __name__ == "__main__":
    main('aa')