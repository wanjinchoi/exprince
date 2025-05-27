import os
import requests

# 액세스 토큰 및 사용자 ID
access_token = "eKHm7TEvVM6kJdaRrRDtRQXCSX3MhG0Pi0jmCvAFVJQt8m8kZeDv0wSL4nIMlbyHYH8aFgINLZsfD5uSY8ikOVCpNthPirLwyp4YOuolH4xpBpanpgz8JyWs8J30ZIuFyH0XDyoAL1Qt4Zuxj-jpBxHD1LIQzcr-kNjYG8ZW23xxINqqqhCI2D4vRmZ9W3aAoHvDTRAs9tNEBLm8mgWX7xa1912zl2m9iJKZSfETU4ovQmasayPX5vfQ4nwUunine7OKC87AUX6ZGnSjeyPz08rTSok1gm88lo86TOMuJ7R_4Kb9thGbDSCiS0dWrmy5tLP22gF0IGE3QY47eUWb0fX9NYIzvrfQc1Wk8R6RUoAG9XODhO9f3xCB4ooHYnPKgtrcRxVb54ETILjbh_TVOgTiMXWqIyyyJjwbVMO"
user_id ='311624904954126430'
#user_id = "1682343958795760499"


# 이미지 파일들이 있는 폴더 경로
folder_path = r"C:\ARGOSRPA\ARGOS_DMS\Master Service\GeneralService\detect_colleters"


# Zalo에 이미지를 업로드하고 attachment_id를 반환하는 함수
def upload_image_to_zalo(image_path):
    # 이미지 업로드 URL
    upload_url = "https://openapi.zalo.me/v2.0/oa/upload/image"

    # 파일을 전송할 때 필요한 데이터
    try:
        files = {'file': open(image_path, 'rb')}
    except FileNotFoundError:
        print(f"File not found: {image_path}")
        return None

    headers = {
        'access_token': access_token
    }

    # 이미지 업로드 요청
    upload_response = requests.post(upload_url, files=files, headers=headers)

    # 업로드 응답 로그 출력
    print(
        f"Upload response: {upload_response.status_code}, {upload_response.text}")

    if upload_response.status_code == 200:
        # 이미지 업로드 성공 시, attachment_id를 가져옴
        attachment_id = upload_response.json().get('data', {}).get(
            'attachment_id')
        if attachment_id:
            return attachment_id
        else:
            print(
                f"Failed to get attachment_id for {image_path}: No attachment_id in response")
            return None
    else:
        print(
            f"Failed to upload image: {upload_response.status_code}, {upload_response.text}")
        return None


# attachment_id로 Zalo 사용자에게 메시지를 전송하는 함수
def send_message_with_attachment(attachment_id):
    # 메시지 전송 URL (v3.0 API 사용)
    message_url = "https://openapi.zalo.me/v3.0/oa/message/cs"

    # 메시지 전송을 위한 데이터 (attachment_id를 media_id로 사용)
    data = {
        "recipient": {
            "user_id": user_id
        },
        "message": {
            "attachment": {
                "payload": {
                    "elements": [
                        {
                            "media_type": "image",
                            "attachment_id": attachment_id
                        }
                    ],
                    "template_type": "media"
                },
                "type": "template"
            },
            "text": "test3"
        }
    }

    headers = {
        'Content-Type': 'application/json',
        'access_token': access_token  # 액세스 토큰을 헤더에 포함
    }

    # 메시지 전송 요청
    message_response = requests.post(message_url, json=data, headers=headers)

    # 상태 코드와 응답 내용을 출력
    if message_response.status_code == 200:
        print(f"Message sent successfully with attachment_id: {attachment_id}")
        print(f"Response content: {message_response.json()}")  # 응답 내용을 출력
    else:
        print(f"Failed to send message: {message_response.status_code}")
        print(f"Response content: {message_response.text}")


# 폴더 내 모든 PNG 파일을 업로드하고 전송하는 함수
def send_all_images():
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            file_path = os.path.join(folder_path, filename)
            print(f"Sending file: {file_path}")
            # 이미지 업로드 후 attachment_id 획득
            attachment_id = upload_image_to_zalo(file_path)
            if attachment_id:
                # attachment_id로 메시지 전송
                send_message_with_attachment(attachment_id)


# 이미지 전송 실행
send_all_images()
