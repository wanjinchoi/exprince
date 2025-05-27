import openpyxl
import os
import shutil



def main(folder_num):
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    # 폴더이름 가져오기
    folders_check = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = folders_check[0]
    # 폴더경로
    excel_folder_path = original_file_path + folder_name
    #옮길경로
    destination_folder = r'X:\〔1〕   완 료 신 청 = 완료'
    destination_path = os.path.join(destination_folder, os.path.basename(excel_folder_path))

    shutil.move(excel_folder_path,destination_path)
    # 엑셀 파일이름 가져오기

if __name__ == "__main__":
    main('0')

