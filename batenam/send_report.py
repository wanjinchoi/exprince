import yaml
import glob
import os
from datetime import datetime

def main(yaml_path):
    current_date_str = datetime.now().strftime("%Y-%m-%d")

    # yaml 파일읽어서 경로랑 시간 가져오기
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        folder_path = data['folder_path']
        result_folder_path = folder_path+'report/' +current_date_str + '/'
        flist = sorted(glob.glob(result_folder_path + '*.xlsx'),key=os.path.getmtime)
        result = flist[0]
        return result

if __name__ == "__main__":
    main(r'C:\ArgosRpa\ARGOS.yaml')

