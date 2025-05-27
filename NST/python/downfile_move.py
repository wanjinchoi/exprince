import os
import shutil
from glob import glob

def main(folder_name):
    # 다운로드 폴더와 대상 폴
    # 더 경로 설정
    downloads_folder = r'C:\Users\vivans\Downloads'
    # downloads_folder = r'C:\Users\PC\Downloads'
    target_folder = r'C:\work\NST\선일'

    # 다운로드 폴더에서 가장 최근에 다운로드한 .xlsx 파일 찾기
    list_of_files = glob(os.path.join(downloads_folder, '*.xlsx'))
    latest_file = max(list_of_files, key=os.path.getctime)

    # 대상 경로 설정
    destination_path = os.path.join(target_folder,os.path.basename(latest_file))

    # 파일 이동 (덮어쓰기)
    shutil.move(latest_file, destination_path)

if __name__ == "__main__":
    main('영신')
