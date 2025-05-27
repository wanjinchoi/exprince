import os
import requests

# Line Notify API Token
token = 'ABBg3x6uivAvo119vkuHNJNeaDInsolKzVV0g7wuMrQ'
headers = {
    'Authorization': f'Bearer {token}'
}

# 폴더 경로 설정
folder_path = 'C:\\ARGOSRPA\\ARGOS_DMS\\Master Service\\GeneralService\\detect_colleters\\'

# 폴더 내의 모든 파일을 탐색
for file_name in os.listdir(folder_path):
    # 파일이 이미지 파일인지 확인
    if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        file_path = os.path.join(folder_path, file_name)

        # 이미지 파일을 Line으로 전송
        with open(file_path, 'rb') as file:
            files = {'imageFile': file}
            data = {'message': '이미지 전송'}  # 기본 메시지 추가
            response = requests.post('https://notify-api.line.me/api/notify',
                                     headers=headers, data=data, files=files)

            # 응답 상태 확인 및 출력
            if response.status_code == 200:
                print(f'{file_name} 전송 성공!')
            else:
                print(f'{file_name} 전송 실패: {response.status_code}')
                print(f'응답 내용: {response.text}')  # 응답 본문 출력

print("모든 이미지 파일 전송 완료.")
