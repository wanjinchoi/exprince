import requests
from ruamel.yaml import YAML
import datetime
import os


def main(nothing):
    yaml_file = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    # 오늘 날짜와 시간을 기록할 파일 경로를 지정합니다
    token_file = r'C:\ARGOSRPA\form\token_data.txt'

    # YAML 파일 읽기
    yaml = YAML()
    yaml.preserve_quotes = True  # 기존 스타일을 유지하도록 설정

    with open(yaml_file, 'r', encoding='utf-8') as file:
        yaml_data = yaml.load(file)

    # access_token과 refresh_token 업데이트
    if 'refresh_token' in yaml_data and 'access_token' in yaml_data:
        refresh_token = yaml_data['refresh_token']
        access_token = yaml_data['access_token']
    else:
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                lines = f.readlines()
                if len(lines) >= 3:
                    refresh_time = lines[0].strip()
                    access_token_line = lines[1].strip()
                    refresh_token_line = lines[2].strip()

                    # Split access_token and refresh_token lines to get the actual values
                    access_token = access_token_line.split(':', 1)[-1].strip()
                    refresh_token = refresh_token_line.split(':', 1)[-1].strip()

                    yaml_data['access_token'] = access_token
                    yaml_data['refresh_token'] = refresh_token

    # 현재 날짜와 시간을 가져옵니다
    now = datetime.datetime.now()

    # 실행 시간을 지정합니다 (예: 16:20)
    target_hour = 12
    target_minute = 58

    # 이전에 실행된 날짜를 확인합니다
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            lines = f.readlines()
            if len(lines) >= 1:
                last_run_time = lines[0].strip()
            else:
                last_run_time = ''
    else:
        last_run_time = ''

    # 현재 시간이 지정된 시간이고, 이전에 실행된 시간이 오늘이 아니라면 실행합니다
    today_date = now.strftime('%Y-%m-%d')
    if (now.hour == target_hour and now.minute == target_minute and last_run_time != today_date):
        # 토큰 갱신 코드 시작
        url = 'https://oauth.zaloapp.com/v4/oa/access_token'
        headers = {
            # Samgang_origin_secret_key: 9KvVeNwXXG4KW9PDnTVH
            # intops_secret_key: feNQoB28X2U4kHGDAM0l
            # Samgang_new_secret_ky: YYHRQkoIXAHgw48aTBME

            'Content-Type': 'application/x-www-form-urlencoded',
            'secret_key': 'YYHRQkoIXAHgw48aTBME'  # 실제 secret_key로 대체하세요
        }
        data = {
            # Samgang_origin_app_id: 1592126884022860935
            # intops app_id: 731051409565308601
            # Samgan_new_app_id : 240822927908901393
            'refresh_token': refresh_token,
            'app_id': '240822927908901393',  # 실제 app_id로 대체하세요
            'grant_type': 'refresh_token'
        }

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            response_data = response.json()
            access_token = response_data.get('access_token')
            refresh_token = response_data.get('refresh_token')

            # 갱신된 access_token과 refresh_token을 YAML 데이터에 업데이트합니다
            yaml_data['access_token'] = access_token
            yaml_data['refresh_token'] = refresh_token

            # 변경된 내용을 YAML 파일에 저장 (기존 포맷 유지)
            with open(yaml_file, 'w', encoding='utf-8') as file:
                yaml.dump(yaml_data, file)

            # 갱신된 토큰과 갱신 시간을 token_data.txt에 저장합니다
            with open(token_file, 'w') as f:
                f.write(f"{today_date}\naccess_token:{access_token}\nrefresh_token:{refresh_token}")

            print("토큰이 갱신되었습니다.")
        else:
            print("토큰 갱신 실패:", response.text)
    else:
        print("갱신 조건에 맞지 않아 실행되지 않았습니다.")


if __name__ == "__main__":
    main('aa')