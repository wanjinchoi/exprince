from datetime import datetime, timedelta
import glob
import os
def main(aa):

    yesterday_file_path = 'C:\\ArgosRPA\\vgroup\\print\\'
    # 현재 날짜와 시간 가져오기
    today = datetime.now()

    # 어제 날짜 계산
    yesterday = today - timedelta(days=1)

    # 날짜를 문자열로 변환 (예: "2024-02-05")
    today_str = today.strftime("%Y%m%d")
    yesterday_str = yesterday.strftime("%Y%m%d")
    final_yesterday_file_path =yesterday_file_path + today_str+'\\'
    flist = sorted(glob.glob(final_yesterday_file_path + '*.pdf'), key=os.path.getmtime)
    if len(flist)==1:
        return flist[0]
    else:
        reulst= "NO"
        return reulst

if __name__ == "__main__":
    main('aa')

