import glob
import os
import re
def main(checklist):
    txt_file_path = r'C:\ARGOS RPA\senario1\SK\mail\\'
    flist = sorted(glob.glob(os.path.join(txt_file_path, '*.txt')), key=os.path.getmtime)
    txt_file = flist[0]

    with open(txt_file, 'r', encoding='utf-8') as file:
        content = file.read()

    # Inquiry No 추출
    inquiry_no_match = re.search(r'Inquiry No\s*:\s*(\S+)', content)
    if inquiry_no_match and inquiry_no_match.group(1).strip() not in ['-', '']:
        inquiry_no = inquiry_no_match.group(1).strip()
        a = inquiry_no.split('-')
        #IP or IT or IR 검증하기 위해서
        x = a[2]
        #문서번호
    else:
        inquiry_no = 'no'
        x ='no'
    ship_name_match = re.search(r'Ship Name\s*:\s*(.+)', content)
    if ship_name_match:
        ship_name = ship_name_match.group(1).strip()
    else:
        print('Ship Name을 찾을 수 없습니다.')
    print(inquiry_no)
    print(x)
    print(ship_name)
if __name__ == "__main__":
    main('aa')

