import psutil
import os
import time
import sys
import subprocess

def is_exe_running(exe_path):
    """주어진 경로의 실행 파일이 실행 중인지 확인합니다."""
    exe_name = os.path.basename(exe_path).lower()  # 실행 파일 이름 추출
    for process in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = process.info['cmdline']
            if cmdline and isinstance(cmdline, list):
                # cmdline이 리스트 형태의 이터러블인지 확인
                cmdline_str = " ".join(cmdline).lower()
                if exe_name in process.info['name'].lower() or exe_path.lower() in cmdline_str:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def run_exe_if_not_running(exe_path):
    """실행 파일이 실행 중이지 않으면 실행합니다."""
    error_log_path = os.path.join(os.path.dirname(exe_path), 'error_log.txt')

    if not is_exe_running(exe_path):
        print(f"{exe_path}이 실행 중이지 않습니다. 실행 중...")

        try:
            if os.path.exists(exe_path):
                subprocess.Popen(['cmd.exe', '/c', exe_path])  # 실행 파일 실행
                print(f"{exe_path}을 실행했습니다.")
                time.sleep(10)  # 실행 후 10초 기다립니다.
            else:
                error_message = f"실행 파일을 찾을 수 없습니다: {exe_path}"
                print(error_message)
                with open(error_log_path, 'a', encoding='utf-8') as error_file:
                    error_file.write(f"{error_message}\n")
        except Exception as e:
            error_message = f"실행 중 오류 발생: {e}"
            print(error_message)
            with open(error_log_path, 'a', encoding='utf-8') as error_file:
                error_file.write(f"{error_message}\n")

    else:
        print(f"{exe_path}이 이미 실행 중입니다.")

# 초기 실행 파일 경로 설정
exe_path = "C:\\ARGOSRPA\\ArgosEbot.ofb"
if not os.path.exists(exe_path):
    error_message = f"실행 파일을 찾을 수 없습니다: {exe_path}"
    print(error_message)
    sys.exit(1)

# 5초마다 실행 여부 확인 후 실행
try:
    while True:
        run_exe_if_not_running(exe_path)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n프로그램이 종료되었습니다.")
    sys.exit(0)
