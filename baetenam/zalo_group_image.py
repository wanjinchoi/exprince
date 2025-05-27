import os
import requests
import yaml
# 액세스 토큰 및 사용자 ID
def main(access_token):
    yaml_file = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    db_path: 'C:\\ARGOSRPA\\Master Service\\GeneralService\\database.db'
    
    access_token = access_token
    # 이미지 파일들이 있는 폴더 경로
    folder_path = r"C:\ARGOSRPA\Master Service\Master_image\detection_screenshots"


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
        print(f"Upload response: {upload_response.status_code}, {upload_response.text}")

        if upload_response.status_code == 200:
            # 이미지 업로드 성공 시, attachment_id를 가져옴
            attachment_id = upload_response.json().get('data', {}).get(
                'attachment_id')
            if attachment_id:
                return attachment_id
            else:
                print(f"Failed to get attachment_id for {image_path}: No attachment_id in response")
                return None
        else:
            print(f"Failed to upload image: {upload_response.status_code}, {upload_response.text}")
            return None


    # attachment_id로 Zalo 사용자에게 메시지를 전송하는 함수
    def send_message_with_attachment(attachment_id):
        message_url = 'https://openapi.zalo.me/v3.0/oa/group/message'
        headers = {
            'access_token': access_token,
            'Content-Type': 'application/json'
        }

        data = {
            "recipient": {
                "group_id": "8cc798b90ce0e5bebcf1"
            },
            "message": {
                "text": "test4",
                "attachment": {
                    "type": "template",
                    "payload": {
                        "template_type": "media",
                        "elements": [
                            {
                                "media_type": "image",
                                "attachment_id": attachment_id
                            }
                        ]
                    }
                }
            }
        }

        # 메시지 전송 요청
        message_response = requests.post(message_url, json=data, headers=headers)

        # 상태 코드와 응답 내용을 출력
        if message_response.status_code == 200:
            print(f"Response content: {message_response.json()}")  # 응답 내용을 출력
        else:
            print(f"Failed to send message: {message_response.status_code}")
            print(f"Response content: {message_response.text}")


    # 폴더 내 모든 PNG 파일을 업로드하고 전송하는 함수
    def send_all_images():
        if len(os.listdir(folder_path))==0:
            return None
        else:
            for filename in os.listdir(folder_path):
                if filename.endswith("_af.png"):
                    file_path = os.path.join(folder_path, filename)
                    # 이미지 업로드 후 attachment_id 획득
                    attachment_id = upload_image_to_zalo(file_path)
                    if attachment_id:
                        # attachment_id로 메시지 전송
                        send_message_with_attachment(attachment_id)



    # 이미지 전송 실행
    send_all_images()

    url = 'https://openapi.zalo.me/v3.0/oa/group/message'
    headers = {
        'access_token': access_token,
        'Content-Type': 'application/json'
    }

    data = {
        "recipient": {
            "group_id": "786f029ca6c54f9b16d4"
        },
        "message": {
            "text":""
        }
    }

    # POST 요청을 보내고 응답을 확인
    response = requests.post(url, headers=headers, data=json.dumps(data))
if __name__ == "__main__":
    main('LEoO2thNRsXRvf4DVDrbP5tacWP_mobW2g3QMIJvI45veiPW0yHPNbE4gcbynLy8Fg2gAKpH6KaGivGrFyjhKN7qxbSgbLiqLz-lDmYcEJvDuAeUCwyQF1tHxHTIi6KE7zZr4tcRP0zNsf8q8fTZKmV_a4X4ZpXH9j2kHb3fANHrWwno2FCIKok9ca5pyWf8ExYUBqBuApKWcDeXJjnNHXYNto13ocb54A3eIpBXV5ONsOftPP4xLnFqgLbcXoX25lsdNcIjEsqxxyXl7QL3UdxgosPRf7f_9fpPLc6iMM10zj865hna74dSoYO7b6OqO-d54pw2TJHUljGD1C9-37-prZWwqNijRABSBpBSDnL1kPmG0z8n02EEWmHYjImMGj670psKBYeTw9agVTK7F0wxYbX7PXS9nb5toszl')
