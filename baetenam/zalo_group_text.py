import requests
import json
import yaml

def main(access_token):
    # yaml 파일읽어서 경로랑 시간 가져오기
    with open('C:\\ARGOSRPA\\Master Service\\GeneralService\\ARGOS.yaml', 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)

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
            "text":"감지결과 " +report_time_start +"~"+report_sendtime+" 까지 아무런 이상이 없었습니다."
        }
    }

    # POST 요청을 보내고 응답을 확인
    response = requests.post(url, headers=headers, data=json.dumps(data))

# 응답을 JSON 형식으로 출력
    print(response.json())
if __name__ == "__main__":
    main('aa')