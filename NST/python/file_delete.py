
import os
import shutil

def main(checklist):
    path = r"C:\work\NST\1.Computer\output\sunil"

    #폴더 정보 가져오기
    folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
    #전체 폴더길이
    length = len(folders)-1
    if length > 1:
        # 1씩 감소
        for i in range(length,0,-1):
            #폴더
            folder_path = os.path.join(path, folders[i])
            shutil.rmtree(folder_path)
            folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            length = len(folders)
            if length == 1:
                break

    print("폴더삭제완료")



if __name__ == "__main__":
    main('aa')