import requests
from ruamel.yaml import YAML
import datetime
import os

def main(refresh_token):
    yaml_file = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    refresh_token2 = refresh_token
    # 현재 날짜와 시간을 가져옵니다
    now = datetime.datetime.now()

    # 오늘 날짜를 기록할 파일 경로를 지정합니다
    date_file = r'C:\ARGOSRPA\form\last_run_date.txt'

    # 이전에 실행된 날짜를 확인합니다
    if os.path.exists(date_file):
        with open(date_file, 'r') as f:
            last_run_date = f.read().strip()  # 파일에서 읽은 이전 실행 날짜
    else:
        last_run_date = ''  # 파일이 없을 경우 빈 문자열로 초기화

    # 오늘 날짜를 문자열로 저장합니다
    today_date = now.strftime('%Y-%m-%d')

    # 오늘 날짜와 last_run_date를 비교하여 같다면 실행을 생략합니다
    if last_run_date == today_date:
        print("이미 오늘 실행되었습니다. 실행을 생략합니다.")
        return  # 함수 종료 (토큰 갱신 코드 실행 안 함)
    yaml = YAML()
    yaml.preserve_quotes = True  # 기존 스타일을 유지하도록 설정
    with open(yaml_file, 'r', encoding='utf-8') as file:
        yaml_data = yaml.load(file)
        refresh_token = yaml_data['refresh_token']

    if refresh_token is None:
        refresh_token=refresh_token2
        url = 'https://oauth.zaloapp.com/v4/oa/access_token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            # Samgang_origin_secret_key: 9KvVeNwXXG4KW9PDnTVH
            # intops_secret_key: Kd35PWG5v5yv3cwVFHxL
            # Samgang_new_secret_ky: YYHRQkoIXAHgw48aTBME
            # True Milk_secret_key : W19CClF0LsGli9U66IWH
            'secret_key': 'YYHRQkoIXAHgw48aTBME'  # 실제 secret_key로 대체하세요
        }
        data = {
            'refresh_token': refresh_token,
            # Samgang_origin_app_id: 1592126884022860935
            #intops app_id: 2177092586003776792
            #Samgan_new_app_id : 240822927908901393
            # True_milk_app_id: 2598870905601127952
            'app_id': '240822927908901393',  # 실제 app_id로 대체하세요
            'grant_type': 'refresh_token'
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')
            refresh_token = response_data.get('refresh_token')

            print(access_token)
            print(refresh_token)

            # YAML 파일 읽기
            yaml = YAML()
            with open(yaml_file, 'r', encoding='utf-8') as file:
                yaml_data = yaml.load(file)

            # access_token과 refresh_token 업데이트
            yaml_data['access_token'] = access_token
            yaml_data['refresh_token'] = refresh_token

            # 변경된 내용을 YAML 파일에 저장 (원본 포맷 유지)
            with open(yaml_file, 'w', encoding='utf-8') as file:
                yaml.dump(yaml_data, file)

            # 오늘 날짜를 기록하여 중복 실행을 방지합니다
            with open(date_file, 'w') as f:
                f.write(today_date)
if __name__ == "__main__":
    main('Z1EKCq06Mc-56P4uIGnKPeGIaJjMHLu1n12MMdbC8Nxz8BnQSqCQHzWudrz79qvKtZh4M1P_MmQX99O1P6KU9lqSjJXj2NXWmMNZPquSUM3NUkb9UYqc7kHQbq5rMYnRmaIZNdybQsR9FjDjKLjhSUP4y4js7JfS-qcCSKO20tZUPRTwPWKS9k1Xj2PE20uvu6It158yE0ZxVgjJKWaTUEDsZ65LRYT2cGMB5H0V3mAk2gOMCLODDvKXnHKdL7L9x2h2SNjA3sl9Ax5h0KiIFP0rh3ugGcC7xmx82qD0VIZL9F0X7qTkB88brIyuQszvimN4NoTmJ5tlDEP09L4hIEWEhcHHGZLDtbtvSaCPKtU9KvnM14WYKw4Tvb84V2jIaton2YK6THA0OhmT7nuuEgjzjIOu8Yib_2tyRaGGMca')
