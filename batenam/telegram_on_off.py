import yaml


def main(yaml_path):
    with open(yaml_path, 'r') as file:
        data = yaml.safe_load(file)
        telegram_on_off = data['telegram_on_off']
        report_time =data['report_time']
        if telegram_on_off =='Y':
            result = 'Y'
            return result
        else:
            result = 'N'
            return 'N'
if __name__ == "__main__":
    main('C:\\work\\baetenam\\road.yaml')
