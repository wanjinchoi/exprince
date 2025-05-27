import openpyxl
import os
import glob

def main(index,folder_num):
    # original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
    ##파일경로
    original_file_path = 'X:\\〔1〕   완 료 신 청 = 첨부 B\\'
    # 폴더이름 가져오기
    folders = [f for f in os.listdir(original_file_path) if
               os.path.isdir(os.path.join(original_file_path, f))]
    folder_name = folders[int(folder_num)]
    # 폴더경로
    folder_path = original_file_path + folder_name + '\\'
    # 엑셀 파일이름 가져오기
    flist = sorted(glob.glob(folder_path + '*.xlsx'), key=os.path.getmtime)
    filtered_list = [file for file in flist if '사무실' in os.path.basename(file)]
    excel_path = filtered_list[0]

    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    number = ws['A'+str(index)].value
    parts = number.split('-')
    front_part= parts[0]
    year = '20'+ front_part[:2]
    month = front_part[2:4]
    day = front_part[4:6]
    print( f'{year}-{month}-{day}')



if __name__ == "__main__":
    main('2','0')

