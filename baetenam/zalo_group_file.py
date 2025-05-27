import requests
import json
from datetime import datetime, timedelta
import glob
import os
import yaml




def post_message_success(company_name, message_text,access_token,group_id,type,file_path) :
    url = "http://61.109.249.21:41300/mds/v1/message/history"

    # UTC 시간 타임스탬프 생성
    utc_timestamp = datetime.utcnow().isoformat() + 'Z'

    # --파라미터 설명--
    # company - 회사명
    # sendTimeTs - 발신 시간 (utc timestamp)
    # messageType - 메세지 타입 => "R": report, "A": alart
    # message - 메세지 본문
    # accessToken - api access token (디버깅용)
    # chatRoomToken - 채팅방 id (디버깅용)
    # sendResult - 메세지 전송 결과 => "S": success, "F": failure
    data = {
        "company": company_name,
        "sendTimeTs": utc_timestamp,
        "messageType": type,
        "message": message_text,
        "accessToken": access_token,
        "chatRoomToken": group_id,
        "sendResult": "S"
    }

    files = None
    # 이미지파일 추가. 있을때만..
    files = {
        "image": open(file_path, "rb")
    }

    if files is not None:
        response = requests.post(url, json=data, files=files)
    else:
        response = requests.post(url, json=data, files=files)

        # 응답 출력
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())


def post_message_fail(company_name, message_text,access_token,group_id,type,file_path):
    url = "http://61.109.249.21:41300/mds/v1/message/history"

    # UTC 시간 타임스탬프 생성
    utc_timestamp = datetime.utcnow().isoformat() + 'Z'

    # --파라미터 설명--
    # company - 회사명
    # sendTimeTs - 발신 시간 (utc timestamp)
    # messageType - 메세지 타입 => "R": report, "A": alart
    # message - 메세지 본문
    # accessToken - api access token (디버깅용)
    # chatRoomToken - 채팅방 id (디버깅용)
    # sendResult - 메세지 전송 결과 => "S": success, "F": failure
    data = {
        "company": company_name,
        "sendTimeTs": utc_timestamp,
        "messageType": type,
        "message": message_text,
        "accessToken": access_token,
        "chatRoomToken": group_id,
        "sendResult": "F"
    }

    files = None
    # 이미지파일 추가. 있을때만..
    files = {

        "image": open("d:/a.png", "rb")
    }

    if files is not None:
        response = requests.post(url, data=json.dumps(data,ensure_ascii=False).encode('utf-8'), files=files)
    else:
        response = requests.post(url, data=json.dumps(data,  ensure_ascii=False).encode('utf-8'))
    # 응답 출력
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())




def main(access_token):
    yaml_file = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"

    with open(yaml_file, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

    # 'accesstoken:' 값 확인
    accesstoken_value = data.get('access_token')
    company_name = data.get('company_name')
    url_upload = 'https://openapi.zalo.me/v2.0/oa/upload/file'
    headers_upload = {
        'access_token': accesstoken_value,
    }
    # 폴더 내 파일 처리
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    folder_path = 'C:\\ARGOSRPA\\'
    yesterday_date = datetime.strptime(current_date_str, "%Y-%m-%d") - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    result_folder_path = folder_path + 'report\\' + current_date_str + '\\'

    flist = sorted(glob.glob(result_folder_path + '*.pdf'), key=os.path.getmtime)

    # 모든 PDF 파일 업로드 및 메시지 전송
    for file_path in flist:
        # 파일 업로드 요청
        with open(file_path, 'rb') as f:
            files = {
                'file': f  # 파일을 바이너리 모드로 열기
            }
            response = requests.post(url_upload, headers=headers_upload, files=files)

        # 응답에서 파일 토큰 추출
        file_token = response.json()['data']['token']

        # 메시지 전송 URL
        url_message = 'https://openapi.zalo.me/v3.0/oa/group/message'
        headers_message = {
            'access_token': accesstoken_value,
            'Content-Type': 'application/json'
        }
        data = {
            "recipient": {
                # intops Daily_report: 9ad8f4c6359fdcc1858e
                # Samkwang : 786f029ca6c54f9b16d4
                # True_milk : e76b1b56910e7850211f
                "group_id": "e76b1b56910e7850211f"
            },
            "message": {
                "attachment": {
                    "type": "file",
                    "payload": {
                        "token": file_token
                    }
                }
            }
        }

        # POST 요청을 통해 API 호출
        response_message = requests.post(url_message, headers=headers_message, json=data)

        url = 'https://openapi.zalo.me/v3.0/oa/group/message'
        headers = {
            'access_token': access_token,
            'Content-Type': 'application/json'
        }

        data = {
            "recipient": {
                # intops Daily_report: 9ad8f4c6359fdcc1858e
                # Samkwang : 786f029ca6c54f9b16d4
                "group_id": "786f029ca6c54f9b16d4"
            },
            "message": {
                "text": ""
            }
        }
        # POST 요청을 보내고 응답을 확인
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            post_message_success(company_name, 'report_send', access_token, 'e76b1b56910e7850211f', 'R', file_path)
            print(f"{file_path} 전송 결과: ", response_message.json())
        else:
            post_message_fail(company_name,  response.text, access_token,'e76b1b56910e7850211f', 'R', file_path)

if __name__ == "__main__":
    main('aa')
