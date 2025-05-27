import paho.mqtt.client as mqtt
import time
import socket
import yaml

# MQTT 브로커에 연결했을 때 호출되는 콜백 함수
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("MQTT 브로커에 연결 성공")
    else:
        print(f"연결 실패, 에러 코드: {rc}")

# MQTT 메시지를 전송했을 때 호출되는 콜백 함수
def on_publish(client, userdata, mid):
    print(f"메시지 전송 완료: {mid}")


def unix_time_now():
    # 현재 시간을 유닉스 타임스탬프로 변환
    return int(time.time())

def get_local_ip():
    # UDP 소켓을 사용해 IP 주소 확인 (인터넷 연결 필수)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 임의의 외부 주소로 연결 시도 (실제 연결되지 않음)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception as e:
        local_ip = "127.0.0.1"  # 기본적으로 로컬호스트 IP 반환
    finally:
        s.close()

    return local_ip

def get_last_octet(ip_address):
    # IP 주소를 '.' 기준으로 나눈 후 마지막 값을 가져옴
    return ip_address.split('.')[-1]


def make_message(company, role, value, extensionValue):
    # 현재 타임스탬프 가져오기
    timestamp = unix_time_now()

    # 메시지 구성 (리스트를 JSON 형식 문자열로 만듦)
    message = '[["{}_{}{}_{}",{:d}{},{:d},"{}"]]'.format(company, role, get_last_octet(get_local_ip()), "MESSAGE", timestamp,
                                                        "000000000", value, extensionValue)

    return message

# MQTT 클라이언트 생성
client = mqtt.Client()

# 콜백 함수 설정
client.on_connect = on_connect
client.on_publish = on_publish

# MQTT 브로커에 연결 (예: broker.hivemq.com:1883)
client.connect("61.109.249.21", 5653, 60)

# 연결 유지 시작 (비동기 방식)
client.loop_start()
yaml_file = r'C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml'

with open(yaml_file, 'r', encoding='utf-8') as file:
    yaml_data = yaml.safe_load(file)
company_name = yaml_data.get('company_name')
device_role = yaml_data.get('device_role')

# 메시지 전송 (알림메세지 전송 결과 성공 : 1, 실패: -1)
client.publish("db/append/monitoring", payload=make_message(company_name, device_role, -1, "이유 없음."), qos=0)

# 연결을 유지한 채로 2초 대기 (메시지 전송 대기)
time.sleep(2)

# 연결 종료
client.loop_stop()
client.disconnect()
