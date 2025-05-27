import shutil
import requests
import yaml
import sqlite3  # 데이터베이스와 상호 작용하기 위해 sqlite3를 임포트합니다.
import os
from datetime import datetime, timedelta
import glob
import paho.mqtt.client as mqtt
import time
import socket
from PIL import Image

##MQTT에 반영하기 위한 ㅡㄹ래스
class MqttClientHandler:
    def __init__(self, broker_ip, broker_port, company_name, device_role):

        self.client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.company_name = company_name
        self.device_role = device_role

        # MQTT 브로커에 연결 시 콜백 함수 설정
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish

        # 브로커 연결
        self.client.connect(self.broker_ip, self.broker_port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, reasonCode, properties):
        if reasonCode == 0:
            self.is_connected = True  # 연결 성공 시 플래그 설정
        else:
            print(f"연결 실패, 이유 코드: {reasonCode}")

    def on_publish(self, client, userdata, mid):
        print(f"메시지 전송 완료: {mid}")

    def unix_time_now(self):
        # 현재 시간을 유닉스 타임스탬프로 변환
        return int(time.time())

    def get_local_ip(self):
        # 로컬 IP 확인
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        except Exception:
            local_ip = "127.0.0.1"
        finally:
            s.close()
        return local_ip

    def get_last_octet(self, ip_address):
        # IP 주소의 마지막 옥텟 추출
        return ip_address.split('.')[-1]

    def make_message(self, company, role, value, extensionValue):
        timestamp = self.unix_time_now()
        message = '[["{}_{}{}_{}",{:d}{},{:d},"{}"]]'.format(
            company, role, self.get_last_octet(self.get_local_ip()), "MESSAGE", timestamp,
            "000000000", value, extensionValue
        )
        return message

    def publish_message(self, topic, company, role, value, extensionValue):
        message = self.make_message(company, role, value, extensionValue)
        self.client.publish(topic, payload=message, qos=0)



def post_message_success(company_name, message_text,access_token,group_id,type,file_path) :
    url = "http://61.109.249.21:41300/mds/v1/message/history"

    # UTC 시간 타임스탬프 생성
    utc_timestamp = datetime.utcnow().isoformat() + 'Z'

    # --파라미터 설명--
    # company - 회사명
    # sendTimeTs - 발신 시간 (utc timestamp)
    # messageType - 메세지 타입 => "R": report, "A": alart
    # message - 메세지 본문
    # accessToken - api access token (디버깅용)
    # chatRoomToken - 채팅방 id (디버깅용)
    # sendResult - 메세지 전송 결과 => "S": success, "F": failure
    data = {
        "company": company_name,
        "sendTimeTs": utc_timestamp,
        "messageType": type,
        "message": message_text,
        "accessToken": access_token,
        "chatRoomToken": group_id,
        "sendResult": "S"
    }

    files = None
    # 이미지파일 추가. 있을때만..
    files = {
        "image": open(file_path, "rb")
    }

    if files is not None:
        response = requests.post(url, data=data, files=files)
    else:
        response = requests.post(url, data=data)

    # 응답 출력
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())


def post_message_fail(company_name, message_text,access_token,group_id,type,file_path):
    url = "http://61.109.249.21:41300/mds/v1/message/history"

    # UTC 시간 타임스탬프 생성
    utc_timestamp = datetime.utcnow().isoformat() + 'Z'

    # --파라미터 설명--
    # company - 회사명
    # sendTimeTs - 발신 시간 (utc timestamp)
    # messageType - 메세지 타입 => "R": report, "A": alart
    # message - 메세지 본문
    # accessToken - api access token (디버깅용)
    # chatRoomToken - 채팅방 id (디버깅용)
    # sendResult - 메세지 전송 결과 => "S": success, "F": failure
    data = {
        "company": company_name,
        "sendTimeTs": utc_timestamp,
        "messageType": type,
        "message": message_text,
        "accessToken": access_token,
        "chatRoomToken": group_id,
        "sendResult": "F"
    }

    files = None
    # 이미지파일 추가. 있을때만..
    files = {

        "image": open("d:/a.png", "rb")
    }

    if files is not None:
        response = requests.post(url, data=data, files=files)
    else:
        response = requests.post(url, data=data)

    # 응답 출력
    print("Status Code:", response.status_code)
    print("Response JSON:", response.json())


def get_file_info(cursor, filename):
    # 주어진 파일명으로 데이터베이스에서 조회
    cursor.execute("SELECT cam, cam_name, register_ts, detection_type FROM files WHERE af_image_name = ?", (filename,))
    result = cursor.fetchone()
    if result:
        cam, cam_name, register_ts, detection_type = result
        return cam, cam_name, register_ts, detection_type
    else:
        print(f"No data found in database for {filename}")
        return None, None, None, None

def compress_image(input_path, target_size_mb):
    quality = 85  # 초기 품질 설정
    step = 5  # 품질을 줄이는 단위
    # 파일 이름 추출 및 output_path 설정
    file_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(os.path.dirname(input_path), f"{file_name}.jpg")

    #이미지 파일의 용량을 줄이고 형식을 jpeg로 바꿉니다.
    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, format='JPEG', quality=quality)

        while os.path.getsize(output_path) > target_size_mb * 1024 * 1024:
            quality -= step
            if quality <= 0:
                raise ValueError("이미지를 지정된 크기로 줄일 수 없습니다.")
            img.save(output_path, format='JPEG', quality=quality)
    # 기존 파일 삭제
    if os.path.exists(input_path):
        os.remove(input_path)
    return output_path

def send_file_to_telegram(telegram_bot_token, telegram_chat_id, detect_image_folder,full_screen_shot_path,cursor,company_name,device_role):
    #폴더 내 파일 없으면
    if  len(os.listdir(detect_image_folder)) == 0 and len(full_screen_shot_path)==0:
        return  None
    elif len(os.listdir(detect_image_folder)) != 0:
        #이미지 파일 가져오기
        for filename in os.listdir(detect_image_folder):
            if filename.endswith("_af.png") or filename.endswith("_bf.png"):
                #파일경로와 이름 가져오기
                file_path = os.path.join(detect_image_folder,filename)
                # db에서 정보 가져오기
                cam, cam_name, register_ts, detection_type = get_file_info(cursor, filename)

                if all([cam, cam_name, register_ts, detection_type]):
                    #보낼 메세지
                    message_text = f"ARGOS_{company_name}_General #1 / {register_ts} / {cam_name} {cam} / {detection_type}"
                    mqtt_client_handler = MqttClientHandler(
                        broker_ip="61.109.249.21",
                        broker_port=5653,
                        company_name=company_name,
                        device_role=device_role
                    )
                    # 텔레그램 API 호출
                    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
                    with open(file_path, 'rb') as file:
                        files = {'document': file}
                        data = {'chat_id': telegram_chat_id, 'caption': message_text}
                        response = requests.post(url, data=data, files=files)
                    # 응답 결과 확인
                    if response.status_code == 200:
                        mqtt_client_handler.publish_message(
                            topic="db/append/monitoring",
                            company=company_name,
                            role=device_role,
                            value=1,
                            extensionValue=""
                        )
                        post_message_success(company_name, message_text,telegram_bot_token,telegram_chat_id, 'A',file_path)
                    else:
                        mqtt_client_handler.publish_message(
                            topic="db/append/monitoring",
                            company=company_name,
                            role=device_role,
                            value=-1,
                            extensionValue=f"/send-message: {response.text}"
                        )
                        post_message_fail(company_name, {response.text},telegram_bot_token, telegram_chat_id,'A', file_path)
    #full_screen 폴더내에 파일 있는지 없는지 여부 검토
    elif len(os.listdir(full_screen_shot_path)) != 0:
        #full_screnn 내에 있는 파일들을 하나씩 가져오기
        for filename in os.listdir(full_screen_shot_path):
            if filename.endswith(".png"):
                file_path = os.path.join(full_screen_shot_path,filename)
                #1MB로 이하로 줄이기
                output_image_path = compress_image(file_path, target_size_mb=1)
                last_file_name = filename.replace('.png','')
                message_text = f"{company_name} / {last_file_name} 이상 없습니다."
                mqtt_client_handler = MqttClientHandler(
                    broker_ip="61.109.249.21",
                    broker_port=5653,
                    company_name=company_name,
                    device_role=device_role
                )
                url = f"https://api.telegram.org/bot{telegram_bot_token}/sendDocument"
                with open(output_image_path, 'rb') as file:
                    files = {'document': file}
                    data = {'chat_id': telegram_chat_id,
                            'caption': message_text}
                    response = requests.post(url, data=data, files=files)
                # 응답 결과 확인
                if response.status_code == 200:
                    mqtt_client_handler.publish_message(
                        topic="db/append/monitoring",
                        company=company_name,
                        role=device_role,
                        value=1,
                        extensionValue=""
                    )
                    post_message_success(company_name, message_text,telegram_bot_token, telegram_chat_id,'A', output_image_path)
                else:
                    mqtt_client_handler.publish_message(
                        topic="db/append/monitoring",
                        company=company_name,
                        role=device_role,
                        value=-1,
                        extensionValue=f"/send-message: {response.text}"
                    )
                    post_message_fail(company_name, {response.text},telegram_bot_token, telegram_chat_id, 'A',output_image_path)

def main(test):
    yaml_path = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    db_path = r"C:\ARGOSRPA\Master Service\GeneralService\database.db"
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        #텔레그램 보낼지 말지
        telegram_on_off = data['photo_telegram']
        #텔레그램 토큰값
        telegram_bot_token = data['telegram_bot_token']
        #텔레그램 채팅방 id
        telegram_chat_id = data['telegram_chat_id']
        # 회사이름
        company_name = data['company_name']
        #device_role
        device_role = data['device_role']
        # 사진폴더
        detect_image_folder = r"C:\ARGOSRPA\Master Service\Master_image\detection_screenshots"
        # full_screen 폴더
        full_screen_shot_path = r"C:\ARGOSRPA\Master Service\Master_image\Full screen"
        # 데이터베이스 연결 설정
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if telegram_on_off =='Y':
            send_file_to_telegram(telegram_bot_token,telegram_chat_id,detect_image_folder,full_screen_shot_path,cursor,company_name,device_role)
        else:
            print('yaml파일에 텔레그램 옵션이 쳌크되어있지 않습니다.')



if __name__ == "__main__":
    main('aa')
