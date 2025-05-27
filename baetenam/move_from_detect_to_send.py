import glob
import os
import shutil
from datetime import datetime, timedelta


def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    detect_folder = 'C:\\ARGOSRPA\\Master Service\\Master_image\\detection_screenshots\\'
    move_path = 'C:\\ARGOSRPA\\Master Service\\Master_image\\send_screens\\' + current_date_str + '\\'
    # 부모 폴더와 현재 날짜를 결합하여 새 폴더 경로 생성
    full_screen_shot_path = "C:\\ARGOSRPA\\Master Service\\Master_image\\Full screen\\"

    # 새 폴더 생성
    if not os.path.exists(move_path):
        os.makedirs(move_path)

    # 옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(detect_folder + '*.png', recursive=True) + glob.glob(detect_folder + '*.PNG', recursive=True), key=os.path.getmtime)
    full_list = sorted(glob.glob(full_screen_shot_path + '*.jpg'), key=os.path.getmtime)
    r_len = len(flist) - 1
    f_len = len(full_list)-1
    # 파일 이름
    if r_len >= 0:
        for i in range(0, r_len + 1):
            r_file = flist[i]
            # 파일이름 가져오기 위해서 나누기
            a = r_file.split('\\')
            file_name = a[-1]
            # 파일 옮기기
            shutil.move(os.path.join(detect_folder, file_name), os.path.join(move_path + file_name))
    if f_len >= 0:
        for i in range(0, f_len + 1):
            f_file = full_list[i]
            # 파일이름 가져오기 위해서 나누기
            b = f_file.split('\\')
            file_name2 = b[-1]
            # 파일 옮기기
            shutil.move(os.path.join(full_screen_shot_path, file_name2), os.path.join(move_path + file_name2))

    # 전날 폴더와 그 안의 내용 삭제하기
    previous_date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    previous_folder = 'C:\\ARGOSRPA\\detection_collector\\send_screens\\' + previous_date_str + '\\'
    if os.path.exists(previous_folder):
        shutil.rmtree(previous_folder)


if __name__ == "__main__":
    main('aa')