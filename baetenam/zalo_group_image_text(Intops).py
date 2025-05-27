import shutil
import requests
import yaml
import sqlite3  # 데이터베이스와 상호 작용하기 위해 sqlite3를 임포트합니다.
from PIL import Image
import os
from datetime import datetime, timedelta
import glob
import paho.mqtt.client as mqtt
import time
import socket


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


def post_message_fail(company_name, message_text,access_token,group_id,type,file_path,error_message):
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
        "sendResult": "F",
        "errorMessage": error_message.get('message')
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


def image_move():
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    detect_folder = 'C:\\ARGOSRPA\\Master Service\\Master_image\\detection_screenshots\\'
    move_path = 'C:\\ARGOSRPA\\Master Service\\Master_image\\send_screens\\' + current_date_str + '\\'
    # 부모 폴더와 현재 날짜를 결합하여 새 폴더 경로 생성
    full_screen_shot_path = "C:\\ARGOSRPA\\Master Service\\Master_image\\Full screen\\"

    # 새 폴더 생성
    if not os.path.exists(move_path):
        os.makedirs(move_path)

    # 옮긴 파일 내에서 최신파일 가져오기
    flist = sorted(glob.glob(detect_folder + '*.png', recursive=True), key=os.path.getmtime)
    full_list = sorted(glob.glob(full_screen_shot_path + '*.jpg'), key=os.path.getmtime)
    r_len = len(flist) - 1
    f_len = len(full_list)-1
    # 파일 이름
    if r_len >= 0:
        for i in range(0, r_len + 1):
            r_file = flist[i]
            # 파일이름 가져오기 위해서 나누기
            a = r_file.split('\\')
            file_name = a[-1]
            # 파일 옮기기
            shutil.move(os.path.join(detect_folder, file_name), os.path.join(move_path + file_name))
    if f_len >= 0:
        for i in range(0, f_len + 1):
            f_file = full_list[i]
            # 파일이름 가져오기 위해서 나누기
            b = f_file.split('\\')
            file_name2 = b[-1]
            # 파일 옮기기
            shutil.move(os.path.join(full_screen_shot_path, file_name2), os.path.join(move_path + file_name2))

    # 전날 폴더와 그 안의 내용 삭제하기
    previous_date_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    previous_folder = 'C:\\ARGOSRPA\\Master Service\\Master_image\\send_screens\\' + previous_date_str + '\\'
    if os.path.exists(previous_folder):
        shutil.rmtree(previous_folder)



def compress_image(input_path, target_size_mb):
    quality = 85  # 초기 품질 설정
    step = 5  # 품질을 줄이는 단위
    # 파일 이름 추출 및 output_path 설정
    file_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(os.path.dirname(input_path), f"{file_name}.jpg")

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
def upload_image_to_zalo(image_path, access_token,company_name):
    # 이미지 업로드 URL
    upload_url = "https://openapi.zalo.me/v2.0/oa/upload/image"

    # 파일을 전송할 때 필요한 데이터
    try:
        files = {'file': open(image_path, 'rb')}
    except FileNotFoundError:
        print(f"File not found: {image_path}")
        return None

    headers = {
        'access_token': access_token
    }

    # 이미지 업로드 요청
    upload_response = requests.post(upload_url, files=files, headers=headers)

    # 업로드 응답 로그 출력
    print(f"Upload response: {upload_response.status_code}, {upload_response.text}")

    if upload_response.status_code == 200:
        # 이미지 업로드 성공 시, attachment_id를 가져옴
        attachment_id = upload_response.json().get('data', {}).get('attachment_id')
        if attachment_id:
            return attachment_id
        else:
            post_message_fail(company_name, '파일 업로드 API호출',access_token,'1691e68527dcce8297cd', 'A', image_path,error_message=upload_response.json())
            print(f"Response content: {upload_response.json()}")  # 응답 내용을 출력
            return None
    else:
        post_message_fail(company_name, '파일 업로드 API호출', access_token,'1691e68527dcce8297cd', 'A', image_path,error_message=upload_response.json())
        print(f"Failed to upload image: {upload_response.status_code}, {upload_response.text}")
        return None

def send_message_with_attachment(attachment_id, message_text, access_token,file_path,mqtt_client_handler):
    company_name = mqtt_client_handler.company_name
    device_role = mqtt_client_handler.device_role
    file_path=file_path
    message_url = 'https://openapi.zalo.me/v3.0/oa/group/message'
    headers = {
        'access_token': access_token,
        'Content-Type': 'application/json'
    }

    data = {
        "recipient": {
            #intops Alarm senter_group_id: 1691e68527dcce8297cd
            #Samkwang : 8cc798b90ce0e5bebcf1
            "group_id": "1691e68527dcce8297cd"
        },
        "message": {
            "text": message_text,
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "media",
                    "elements": [
                        {
                            "media_type": "image",
                            "attachment_id": attachment_id
                        }
                    ]
                }
            }
        }
    }
    # 메시지 전송 요청
    message_response = requests.post(message_url, json=data, headers=headers)
    # 상태 코드와 응답 내용을 출력
    if message_response.status_code == 200:
        # MQTT로 성공 메시지 전송
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=1,
            extensionValue=""
        )
        post_message_success(company_name, message_text, access_token,'1691e68527dcce8297cd', 'A',file_path)
        if message_response.json().get('error') != 0:
            post_message_fail(company_name, message_text, access_token,'1691e68527dcce8297cd', 'A', file_path,error_message=message_response.json())
        print(f"Response content: {message_response.json()}")  # 응답 내용을 출력


    else:
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue=f"/send-message: {message_response.status_code} - {message_response.text}"
        )
        post_message_fail(company_name, message_text, access_token,'1691e68527dcce8297cd', 'A', file_path,error_message=message_response.json())
        print(f"Failed to send message: {message_response.status_code}")
        print(f"Response content: {message_response.text}")

def get_file_info(cursor, filename):
    # 주어진 파일명으로 데이터베이스에서 조회
    if 'af' in filename:
        cursor.execute("SELECT cam, cam_name, register_ts, detection_type FROM files WHERE af_image_name = ?",(filename,))
    else:
        cursor.execute("SELECT cam, cam_name, register_ts, detection_type FROM files WHERE bf_image_name = ?", (filename,))
    result = cursor.fetchone()
    if result:
        cam, cam_name, register_ts, detection_type = result
        return cam, cam_name, register_ts, detection_type
    else:
        print(f"No data found in database for {filename}")
        return None, None, None, None

def send_all_images(folder_path,full_screen_shot_path,cursor, access_token,company_name,device_role):
    if len(os.listdir(folder_path)) == 0 and len(os.listdir(full_screen_shot_path)) == 0:
        return None
    elif len(os.listdir(folder_path)) != 0:
        for filename in os.listdir(folder_path):
            if filename.endswith(".png"):
                file_path = os.path.join(folder_path, filename)
                # 이미지 업로드 후 attachment_id 획득
                attachment_id = upload_image_to_zalo(file_path, access_token,company_name)
                if attachment_id:
                    # 데이터베이스에서 파일 정보 가져오기
                    cam, cam_name, register_ts, detection_type = get_file_info(cursor, filename)
                    if all([cam, cam_name, register_ts, detection_type]):
                        # 메시지 텍스트 구성
                        if detection_type =='fire':
                            message_text = f"ARGOS_{company_name}_Fire #1 / {register_ts} / {cam_name} {cam} / {detection_type}"
                        else:
                            message_text = f"ARGOS_{company_name}_General #1 / {register_ts} / {cam_name} {cam} / {detection_type}"
                        # attachment_id로 메시지 전송
                        mqtt_client_handler = MqttClientHandler(
                            broker_ip="61.109.249.21",
                            broker_port=5653,
                            company_name=company_name,
                            device_role=device_role
                        )
                        send_message_with_attachment(attachment_id, message_text, access_token,file_path,mqtt_client_handler=mqtt_client_handler)
    elif len(os.listdir(full_screen_shot_path)) != 0:
        for filename in os.listdir(full_screen_shot_path):
            if filename.endswith(".png"):
                file_path = os.path.join(full_screen_shot_path, filename)
                # 1MB 이하로 줄이기
                output_image_path = compress_image(file_path, target_size_mb=1)
                # 이미지 업로드 후 attachment_id 획득
                attachment_id = upload_image_to_zalo(output_image_path, access_token)
                if attachment_id:
                    last_file_name = filename.replace('.png','')
                    message_text = f"{company_name} / {last_file_name} 이상 없습니다."
                    # attachment_id로 메시지 전송
                    mqtt_client_handler = MqttClientHandler(
                        broker_ip="61.109.249.21",
                        broker_port=5653,
                        company_name=company_name,
                        device_role=device_role
                    )
                    send_message_with_attachment(attachment_id, message_text, access_token,file_path,mqtt_client_handler=mqtt_client_handler)

def main(access_token):
    yaml_file = r"C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml"
    db_path = r"C:\ARGOSRPA\Master Service\GeneralService\database.db"  # 경로 수정
    with open(yaml_file, 'r', encoding='utf-8') as file:
        yaml_data = yaml.safe_load(file)
    # access_token 추출
    access_token = yaml_data.get('access_token')
    company_name = yaml_data.get('company_name')
    device_role = yaml_data.get('device_role')
    # 이미지 파일들이 있는 폴더 경로
    folder_path = r"C:\ARGOSRPA\Master Service\Master_image\detection_screenshots"
    full_screen_shot_path = r"C:\ARGOSRPA\Master Service\Master_image\Full screen"
    # 데이터베이스 연결 설정
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 이미지 전송 실행
    send_all_images(folder_path,full_screen_shot_path ,cursor, access_token,company_name,device_role)
    image_move()

    # 데이터베이스 연결 종료
    conn.close()
if __name__ == "__main__":
    main('aa')