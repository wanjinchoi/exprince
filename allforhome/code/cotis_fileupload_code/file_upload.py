import openpyxl
import os
import glob


def main(index,folder_num):
    #파일이름 등재하는 리스트
    file_name =[]
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    original_file_path = 'X:\\〔1〕   완 료 신 청 = 첨부 B\\'
    # 폴더이름 가져오기
    folders_check = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = max(folders_check, key=lambda f: os.path.getmtime(os.path.join(original_file_path, f)))
    folder_name = folders_check[0]
    # 폴더경로
    excel_folder_path = original_file_path + folder_name + '\\'
    # 엑셀 파일이름 가져오기
    flist = sorted(glob.glob(excel_folder_path + '*.xlsx'), key=os.path.getmtime)
    excel_path = flist[int(folder_num)]

    #접수번호 가져오기
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    number = ws['A'+str(index)].value

    original_file_path2 = 'X:\\〔1〕   완 료 신 청 = 첨부 B\\'
    for folder_name in os.listdir(original_file_path2):
        folder_path = os.path.join(original_file_path2, folder_name)

        # folder_path가 폴더인지 확인
        if os.path.isdir(folder_path):
            # folder_path의 하위 폴더 탐색
            for sub_folder_name in os.listdir(folder_path):
                sub_folder_path = os.path.join(folder_path, sub_folder_name)

                # sub_folder_path가 폴더인지 확인 (파일 제외)
                if os.path.isdir(sub_folder_path):
                    # sub_folder_path의 하위 폴더 탐색
                    for target_folder_name in os.listdir(sub_folder_path):
                        target_folder_path = os.path.join(sub_folder_path,target_folder_name)

                        # target_folder_path가 폴더이고, 폴더 이름에 number가 포함되어 있는지 확인
                        if os.path.isdir(target_folder_path) and number in target_folder_name:
                            exist_path = target_folder_path

    final_picture_path = exist_path+'\\'+'06 완료신청'+'\\'
    # 엑셀 파일이름 가져오기
    jpg_files = [file for file in os.listdir(final_picture_path) if file.lower().endswith('.jpg')]

    # #SKM파일이 들어간 파일 이름
    # # "SKM"이 포함된 파일 이름 변경 (여러 개일 경우 순차적으로 SKM_1.jpg, SKM_2.jpg, ...)
    # skm_files = [file for file in jpg_files if "SKM" in file]
    # for idx, file in enumerate(skm_files, start=1):
    #     old_path = os.path.join(final_picture_path, file)
    #     new_name = f"SKM_{idx}.jpg"
    #     new_path = os.path.join(final_picture_path, new_name)
    #     os.rename(old_path, new_path)
    #
    # # "SKM"이 포함되지 않은 파일 필터링
    non_skm_files = [file for file in jpg_files if "SKM" not in file]
    non_skm_count = len(non_skm_files)

    for idx, file in enumerate(non_skm_files, start=1):
        # 새 이름 생성
        new_name = f"{idx}.jpg"
        old_path = os.path.join(final_picture_path, file)
        new_path = os.path.join(final_picture_path, new_name)

        # 파일 이름 변경
        os.rename(old_path, new_path)
        file_name.append(new_name)
    print(" ".join(f'"{name}"' for name in file_name))


if __name__ == "__main__":
    main('3','0')

