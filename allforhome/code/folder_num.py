import openpyxl
import os
import glob

from datetime import datetime
from dateutil.relativedelta import relativedelta

# original_file_path = 'X:\\〔1〕   완 료 신 청 = A\\'
##파일경로


def main(index):
    original_file_path = 'C:\\〔1〕   완 료 신 청 = A\\'
    # 폴더이름 가져오기
    folders = [f for f in os.listdir(original_file_path) if os.path.isdir(os.path.join(original_file_path, f))]
    folders_num = len(folders)

    return folders_num





if __name__ == "__main__":
    main('2')

