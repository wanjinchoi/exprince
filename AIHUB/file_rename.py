import os
import glob




asone_path = 'C:\\Users\\vivans\\Desktop\\AI허브\\지로서 다운로드\\에스원\\'


def main(date):
    #폴더 최신꺼 가져오기
    folder = os.listdir(asone_path)
    x = len(folder)-1
    rename_path = asone_path + folder[x]+'\\'


    flist = sorted(glob.glob(rename_path + '*.html'), key=os.path.getmtime)
    x = len(flist)
    for i in range(0, x):
        flist = sorted(glob.glob(rename_path + '*.html'), key=os.path.getmtime)
        r_file = flist[i]
        #파일이름 가져오기 위해서 나누기
        a = r_file.split('\\')
        x = len(a)-1
        file_name = a[x]
        os.rename(rename_path+file_name,rename_path+'에스원_청구서_'+date+'_'+str(i+1)+'.html')



if __name__ == "__main__":
    main('202312261352')

