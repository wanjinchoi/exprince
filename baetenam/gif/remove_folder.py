import os
import datetime
import shutil


def main(checklist):
    directory = 'Z:\\viet\\store_screens\\'
    directory2 = 'Z:\\viet\\all_images\\'
    directory3 = 'Z:\\viet\\already_send\\'
    directory4 = 'Z:\\viet\\gif_folder\\'
    # 현재 날짜 구하기
    current_date = datetime.datetime.now()
    # 일주일 전의 날짜 계산
    one_week_ago = current_date - datetime.timedelta(days=7)

    # 디렉토리 안의 모든 항목을 확인하고, 폴더만 대상으로 함
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isdir(item_path):
            # 폴더의 생성 시간을 확인
            creation_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            # 폴더가 일주일 이전에 생성되었다면 삭제
            if creation_time < one_week_ago:
                try:
                    shutil.rmtree(item_path)  # 폴더와 내용물을 모두 삭제합니다.
                    print(f"폴더 {item_path} 및 그 내용물 삭제됨")
                except OSError as e:
                    print(f"폴더 삭제 중 오류 발생: {e}")

    for item in os.listdir(directory2):
        item_path = os.path.join(directory2, item)
        if os.path.isdir(item_path):
            # 폴더의 생성 시간을 확인
            creation_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            # 폴더가 일주일 이전에 생성되었다면 삭제
            if creation_time < one_week_ago:
                try:
                    shutil.rmtree(item_path)  # 폴더와 내용물을 모두 삭제합니다.
                    print(f"폴더 {item_path} 및 그 내용물 삭제됨")
                except OSError as e:
                    print(f"폴더 삭제 중 오류 발생: {e}")

    for item in os.listdir(directory3):
        item_path = os.path.join(directory3, item)
        if os.path.isdir(item_path):
            # 폴더의 생성 시간을 확인
            creation_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            # 폴더가 일주일 이전에 생성되었다면 삭제
            if creation_time < one_week_ago:
                try:
                    shutil.rmtree(item_path)  # 폴더와 내용물을 모두 삭제합니다.
                    print(f"폴더 {item_path} 및 그 내용물 삭제됨")
                except OSError as e:
                    print(f"폴더 삭제 중 오류 발생: {e}")

    for item in os.listdir(directory4):
        item_path = os.path.join(directory4, item)
        if os.path.isdir(item_path):
            # 폴더의 생성 시간을 확인
            creation_time = datetime.datetime.fromtimestamp(os.path.getctime(item_path))
            # 폴더가 일주일 이전에 생성되었다면 삭제
            if creation_time < one_week_ago:
                try:
                    shutil.rmtree(item_path)  # 폴더와 내용물을 모두 삭제합니다.
                    print(f"폴더 {item_path} 및 그 내용물 삭제됨")
                except OSError as e:
                    print(f"폴더 삭제 중 오류 발생: {e}")


    # 삭제하고자 하는 디렉토리 경로 설정


# 함수 호출하여 폴더 삭제



if __name__ == "__main__":
    main('aa')
