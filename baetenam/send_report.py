import glob
import os
from datetime import datetime

def main(yaml_path):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = 'C:\\ARGOSRPA\\'
    result_folder_path = folder_path+'report\\' +current_date_str + '\\'
    flist = sorted(glob.glob(result_folder_path + '*.xlsx'),key=os.path.getmtime)
    result = flist[0]
    return result

if __name__ == "__main__":
    main(r'C:\ArgosRpa\ARGOS.yaml')

