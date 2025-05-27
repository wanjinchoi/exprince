import os
import yaml


def main(yaml_path):
    # yaml 파일읽어서 경로랑 시간 가져오기
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        photo_telegram = data['photo_telegram']
        if photo_telegram == 'Y':
            result = 'Y'
            return result
        else:
            result = 'N'
            return result


if __name__ == "__main__":
    main(r'C:\ARGOSRPA\ARGOS.yaml')

