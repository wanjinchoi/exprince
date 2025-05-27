import openpyxl
import os
import glob
import shutil

def main(index,folder_num):
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    move_path ='X:\\〔1〕   완 료 신 청 = 완료\\'
    # 폴더이름 가져오기
    folders_check = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = folders_check[int(folder_num)]
    # 폴더경로
    excel_folder_path = original_file_path + folder_name + '\\'
    # 엑셀 파일이름 가져오기
    flist = sorted(glob.glob(excel_folder_path + '*.xlsx'), key=os.path.getmtime)
    excel_path = flist[0]

    #접수번호 가져오기
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    number = ws['A'+str(index)].value

    original_file_path2 = 'X:\\〔1〕   완 료 신 청 = 첨부 B\\'
    # original_file_path2의 하위 폴더를 탐색
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

    # final_picture_path = exist_path+'\\'+'06 완료신청'+'\\'
    # shutil.rmtree(final_picture_path)
    # dest_folder = os.path.join(move_path, os.path.basename(folder_path))
    # # 동일 이름의 폴더가 이미 존재하면 삭제 (덮어쓰기 효과)
    # if os.path.exists(dest_folder):
    #     shutil.rmtree(dest_folder)
    shutil.move(folder_path,move_path)
if __name__ == "__main__":
    main('2','0')

