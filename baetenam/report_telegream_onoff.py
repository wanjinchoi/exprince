import yaml


def main(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        telegram_on_off = data['report_telegrm']
        report_time =data['report_sendtime']
        if telegram_on_off =='Y':
            return report_time
        else:
            result = 'N'
            return result
if __name__ == "__main__":
    main('C:\\work\\baetenam\\road.yaml')
