import os
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image
import pillow_heif

# 변환된 파일들을 저장할 리스트 초기화
converted_files = []


# HEIC 파일을 PNG로 변환하는 함수
def convert_heic_to_png(heic_path):
    heif_file = pillow_heif.read_heif(heic_path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    output_path = heic_path.replace('.heic', '.png')
    image.save(output_path, 'PNG')
    print(f'Converted {heic_path} to {output_path}')
    converted_files.append(output_path)  # 변환된 파일을 리스트에 추가
    os.remove(heic_path)  # 원본 파일 삭제
    print(f'Deleted original file: {heic_path}')


# PDF 파일을 PNG로 변환하는 함수
def convert_pdf_to_png(pdf_path):
    images = convert_from_path(pdf_path, poppler_path='C:/Release-22.07.0-0/poppler-24.07.0/Library/bin')
    for i, image in enumerate(images):
        output_path = f'{os.path.splitext(pdf_path)[0]}.png'
        image.save(output_path, 'PNG')
        print(f'Converted {pdf_path} to {output_path}')
        converted_files.append(output_path)  # 변환된 파일을 리스트에 추가
    os.remove(pdf_path)  # 원본 파일 삭제
    print(f'Deleted original file: {pdf_path}')


# JFIF 파일을 PNG로 변환하는 함수
def convert_jfif_to_png(jfif_path):
    image = Image.open(jfif_path)
    output_path = jfif_path.replace('.jfif', '.png')
    image.save(output_path, 'PNG')
    print(f'Converted {jfif_path} to {output_path}')
    converted_files.append(output_path)  # 변환된 파일을 리스트에 추가
    os.remove(jfif_path)  # 원본 파일 삭제
    print(f'Deleted original file: {jfif_path}')


# 파일을 PNG로 변환하는 메인 함수
def convert_to_png(file_path):
    _, file_ext = os.path.splitext(file_path)

    if file_ext.lower() == '.pdf':
        convert_pdf_to_png(file_path)
    elif file_ext.lower() == '.heic':
        convert_heic_to_png(file_path)
    elif file_ext.lower() == '.jfif':
        convert_jfif_to_png(file_path)
    else:
        print(f'Unsupported file type: {file_path}')



# newpath와 converted_files를 각각 extension과 afterextension 컬럼으로 저장하는 함수
def save_paths_to_excel(newpath, converted_files, excel_path):
    data = {'extension': newpath, 'afterextension': converted_files}
    df = pd.DataFrame(data)
    df.to_excel(excel_path, index=False)
    print(f'Saved file paths to {excel_path}')


# 메인 실행 부분
backup_dir = 'C:/backup'
db_path = 'C:/storage/RPA/hwamool.db'
old_str = 'C:/backup'
new_str = 'C:/UserDummy'


# 파일 리스트를 가져오는 함수들
def get_all_files_and_folders(root_dir):
    path_list = []
    for root, dirs, files in os.walk(root_dir):
        for name in files:
            modpath = os.path.join(root, name)
            modpath = modpath.replace('C:/backup\\', '')
            modpath = modpath.replace('\\', '/')
            path_list.append(modpath)

    return path_list


def get_all_files_and_folders1(root_dir):
    path_list = []
    for root, dirs, files in os.walk(root_dir):
        for name in files:
            modpath = os.path.join(root, name)
            modpath = modpath.replace('\\', '/')
            modpath = modpath.replace('C:/UserDummy/','')
            path_list.append(modpath)
    return path_list


# 파일 경로 가져오기
paths = get_all_files_and_folders(backup_dir)
paths1 = get_all_files_and_folders1(new_str)

newpath = set(paths1) - set(paths)
newpath = list(newpath)

# 파일 리스트를 순회하며 PNG로 변환 수행
for file_path in newpath:
    file_path = 'C:/UserDummy/'+file_path
    convert_to_png(file_path)

# 변환된 파일 리스트를 엑셀 파일로 저장
excel_file_path = 'C:/storage/extensionlist.xlsx'
save_paths_to_excel(newpath, converted_files, excel_file_path)

