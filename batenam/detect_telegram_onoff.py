import yaml


def main(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        telegram_on_off = data['photo_telegram']
        if telegram_on_off =='Y':
            result ='Y'
            return result
        else:
            result = 'N'
            return result
if __name__ == "__main__":
    main('C:\\work\\baetenam\\road.yaml')
