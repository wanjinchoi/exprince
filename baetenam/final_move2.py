import glob
import os
import shutil
from datetime import datetime, timedelta


def main(checklist):
    current_date = datetime.now()
    current_date_str = current_date.strftime("%Y-%m-%d")
    yesterday_date = current_date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")

    folder_path = 'Z:\\viet\\send_screens\\'
    move_path_today = 'Z:\\viet\\store_screens\\' + current_date_str + '\\'
    move_path_yesterday = 'Z:\\viet\\store_screens\\' + yesterday_date_str + '\\'

    # 새 폴더 생성
    if not os.path.exists(move_path_today):
        os.makedirs(move_path_today)

    # 어제 날짜의 폴더 생성
    if not os.path.exists(move_path_yesterday):
        os.makedirs(move_path_yesterday)

    # 옮긴 파일 내에서 최신 파일 가져오기
    flist = sorted(glob.glob(folder_path + '*.png'), key=os.path.getmtime)
    r_len = len(flist) - 1

    # 파일 이름
    for i in range(0, r_len + 1):
        r_file = flist[i]
        # 파일이름 가져오기 위해서 나누기
        a = r_file.split('\\')
        file_name = a[3]
        # 파일이 오늘의 파일인지 어제의 파일인지 확인
        file_date = datetime.fromtimestamp(os.path.getmtime(r_file)).date()
        if file_date == current_date.date():
            # 오늘 날짜 파일이면 오늘 날짜 폴더로 이동
            destination_path = os.path.join(move_path_today, file_name)
        elif file_date == yesterday_date.date():
            # 어제 날짜 파일이면 어제 날짜 폴더로 이동
            destination_path = os.path.join(move_path_yesterday, file_name)
        else:
            # 다른 날짜의 파일이면 넘어감
            continue

        # 파일 옮기기
        shutil.move(r_file, destination_path)


if __name__ == "__main__":
    main('aa')
