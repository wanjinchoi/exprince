import yaml

def main(yaml_path):
    # yaml 파일읽어서 경로랑 시간 가져오기
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    # telegram_token과 telegram_chat_ID를 가져오기
    telegram_token = data.get('telegram_bot_token')
    telegram_chat_ID = data.get('telegram_chat_id')

    # 결과 출력
    print(f"{telegram_token}")
    print(f"{telegram_chat_ID}")



if __name__ == "__main__":
    main(r'C:\ArgosRpa\ARGOS.yaml')

