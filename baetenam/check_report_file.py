"""

"""

#####################################################
import os
import yaml


#####################################################

def main(content):
    file_path= r'/baetenam/send_report_list.txt'
    try:
        # 파일을 읽기 모드로 열기
        with open(file_path, 'r') as file:
            lines = file.readlines()
            # 줄바꿈 문자를 제거하여 내용 비교
            lines = [line.strip() for line in lines]
            if content in lines:
                return "exist"
    except FileNotFoundError:
        # 파일이 없으면 새로 생성
        lines = []

    # 파일에 내용을 추가하기 위해 쓰기 모드로 열기
    with open(file_path, 'a') as file:
        file.write(content + '\n')
        return content


if __name__ == '__main__':
    main('2024-07-03_ARGOS C-CUBE Report_v1.0.xlsx')
