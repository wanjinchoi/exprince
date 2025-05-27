import openpyxl
import os
import glob
import re


def main(index,folder_num):
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    # 폴더이름 가져오기
    folders_check = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = folders_check[int(folder_num)]
    # 폴더경로
    excel_folder_path = original_file_path + folder_name + '\\'
    # 엑셀 파일이름 가져오기
    flist = sorted(glob.glob(excel_folder_path + '*.xlsx'),key=os.path.getmtime)
    excel_path = flist[0]

    # 접수번호 가져오기
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    number = ws['A' + str(index)].value

    original_file_path2 = 'X:\\〔1〕   완 료 신 청 = 첨부 B\\'
    ## 접수번호가 들어있는 폴더 경로 찾기
    for folder_name in os.listdir(original_file_path2):
        folder_path = os.path.join(original_file_path2, folder_name)

        # 각 폴더 안에 '4부도'라는 폴더가 존재하는지 확인
        if os.path.isdir(folder_path):
            sub_folder_path = os.path.join(folder_path, '4부도')
            if os.path.exists(sub_folder_path) and os.path.isdir(sub_folder_path):
                # '4부도' 하위 폴더에서 number가 들어간 폴더 탐색
                for sub_folder_name in os.listdir(sub_folder_path):
                    sub_folder_full_path = os.path.join(sub_folder_path,sub_folder_name)
                    if os.path.isdir(sub_folder_full_path) and number in sub_folder_name:
                            exist_path = sub_folder_full_path

    final_picture_path = exist_path+'\\'+'06 완료신청'+'\\'
    # 엑셀 파일이름 가져오기
    jpg_files = [file for file in os.listdir(final_picture_path) if file.lower().endswith('.jpg')]

    # "SKM"이 포함되지 않은 파일 필터링
    non_skm_files = [file for file in jpg_files if "SKM" not in file]

    return len(non_skm_files)


if __name__ == "__main__":
    main('2','0')

