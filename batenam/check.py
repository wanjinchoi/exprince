import psutil
import os
import time
import sys
import yaml

def is_exe_running(exe_name):
    for process in psutil.process_iter(['pid', 'name']):
        try:
            if process.info['name'] == exe_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def run_exe_if_not_running(exe_path):
    exe_name = 'ArgosRPAUxRobotAgent.V3.exe'

    if not is_exe_running(exe_name):
        print(f"{exe_name}이 실행 중이지 않습니다. 실행 중...")

        try:
            os.startfile(exe_path)
            print(f"{exe_name}을 실행했습니다.")
        except Exception as e:
            print(f"실행 중 오류 발생: {e}")

    else:
        print(f"{exe_name}이 이미 실행 중입니다.")

# YAML 파일에서 exe_path를 읽어오기
config_path = 'Z:\\viet\\baetenam\\dist\\program_check.yaml'
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)
    exe_path = config['exe_path']

# 5초마다 검토 후 실행
try:
    while True:
        run_exe_if_not_running(exe_path)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n프로그램이 종료되었습니다.")
    sys.exit(0)
