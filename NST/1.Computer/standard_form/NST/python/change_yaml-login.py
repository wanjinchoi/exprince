""" 

"""

#####################################################
import os
import yaml


#####################################################

def main(org_yaml_path, uid, pw, datatime):

    with open(org_yaml_path, encoding='utf-8') as f:
        file = yaml.safe_load(f)
                        # 라이더
    file['params']['user_id'] = uid                             # bmrm00@naver.com
    file['params']['user_pwd'] = pw                            # woowahan1234
    file['params']['check time']['datetime'] = datatime

    yaml_dir_path = r'C:\work\NST\pythonlogin.yaml'
    if not os.path.exists(yaml_dir_path):
        os.makedirs(yaml_dir_path)

    yaml_path = r'C:\work\NST\python\login.yaml'
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(file, f, allow_unicode=True)

    return yaml_path


if __name__ == '__main__':
    main('C:/work/newone/python/login.yaml', '999', 'n000000000', '2023-12-28 13:30:00')
