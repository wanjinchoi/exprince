import openpyxl
import os
import glob
import re





def main(index):

    # 그림파일들을 담을 리스트
    file_name =[]
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    original_file_path = 'C:\\〔1〕   완 료 신 청 = A\\'
    # 폴더이름 가져오기
    folders_check = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = folders_check[0]
    # 폴더경로
    excel_folder_path = original_file_path + folder_name + '\\'
    # 엑셀 파일이름 가져오기
    flist = sorted(glob.glob(excel_folder_path + '*.xlsx'), key=os.path.getmtime)
    excel_path = flist[0]

    #접수번호 가져오기
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    number = ws['A'+str(index)].value

    original_file_path2 = 'C:\\〔1〕   완 료 신 청 = 첨부 B\\'
    # 폴더이름 가져오기
    folders = [f for f in os.listdir(original_file_path2) if os.path.isdir(os.path.join(original_file_path2, f))]
    folder_name = folders[0]
    # 폴더경로
    folder_path = original_file_path2 + folder_name + '\\'
    folders2 = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    folder2_name = folders2[0]
    folder3_path = folder_path + folder2_name + '\\'
    folder4_list = [f for f in os.listdir(folder3_path) if os.path.isdir(os.path.join(folder3_path, f))]

    matching_folder = [folder for folder in folder4_list if number in folder]
    matching_folder_name = matching_folder[0]
    picture_path = folder3_path + matching_folder_name+'\\'

    final_picture_path = picture_path+'06 완료신청'+'\\'
    # 엑셀 파일이름 가져오기
    jpg_files = [file for file in os.listdir(final_picture_path) if file.lower().endswith('.jpg')]

    #SKM파일이 들어간 파일 이름
    skm_files = [file for file in jpg_files if "SKM" in file]
    # "SKM"이 포함된 파일 이름 변경
    for file in skm_files:
        old_path = os.path.join(final_picture_path, file)
        new_path = os.path.join(final_picture_path, "SKM.jpg")
        # 기존 SKM.jpg가 있다면 삭제
        os.rename(old_path, new_path)

    # "SKM"이 포함되지 않은 파일 필터링
    non_skm_files = [file for file in jpg_files if "SKM" not in file]
    non_skm_count = len(non_skm_files)

    for idx, file in enumerate(non_skm_files, start=1):
        # 새 이름 생성
        new_name = f"{idx}.jpg"
        old_path = os.path.join(final_picture_path, file)
        new_path = os.path.join(final_picture_path, new_name)

        # 파일 이름 변경
        new_file_name =  os.rename(old_path, new_path)
        file_name.append(new_file_name)

    print(new_file_name)


if __name__ == "__main__":
    main('2')

