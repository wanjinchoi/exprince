import glob
import os
import shutil
from datetime import datetime, timedelta



def main(checklist):
    detect_folder_path = 'Z:\\viet\\detection_screenshots\\'
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    move_path = os.path.join('Z:\\viet\\send_screens\\',current_date_str)

    # 폴더가 없으면 생성
    if not os.path.exists(move_path):
        os.makedirs(move_path)

    # detecfolder 체크
    flist = sorted(glob.glob(os.path.join(detect_folder_path, '*.png')),key=os.path.getmtime)
    if len(flist) < 1:
        result = '1'
        return result
    else:
        result = ','.join(flist)
        return result

    # else:
    # # 파일 이동
    #     for r_file in flist:
    #         file_name = os.path.basename(r_file)
    #         shutil.move(r_file, os.path.join(move_path, file_name))
    #         print(f"{file_name} 파일을 {move_path} 로 이동했습니다.")

if __name__ == "__main__":
    main('aa')