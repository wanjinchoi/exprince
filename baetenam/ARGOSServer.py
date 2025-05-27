import time
import signal
import requests
import httpx
from influxdb import InfluxDBClient
from pydantic import BaseModel
import aiofiles
from fastapi import File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import shutil
import os
import asyncio
import yaml
import tkinter as tk
import threading
from datetime import datetime, timedelta
import logging
import uvicorn
from fastapi import FastAPI, status
from fastapi.responses import FileResponse
import sqlite3
from sqlite3 import Error
import ctypes
import schedule
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import base64
import pytz
import sys
from dateutil import parser
from cryptography.hazmat.primitives import serialization
import psutil
import hashlib
import socket
import paho.mqtt.client as mqtt

class DailyRotatingFileHandler(logging.FileHandler):
    def __init__(self, log_dir, log_filename_template):
        self.log_dir = log_dir
        self.log_filename_template = log_filename_template
        self.current_date = datetime.now().date()
        log_file = self.get_log_file_path()
        super().__init__(log_file, encoding='utf-8')
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def get_log_file_path(self):
        today_date = datetime.now().strftime('%Y-%m-%d')
        today_log_dir = os.path.join(self.log_dir, today_date)
        if not os.path.exists(today_log_dir):
            os.makedirs(today_log_dir)
        log_file = os.path.join(today_log_dir, self.log_filename_template.format(today_date))
        return log_file

    def emit(self, record):
        if datetime.now().date() != self.current_date:
            self.current_date = datetime.now().date()
            self.baseFilename = self.get_log_file_path()
            self.stream = self._open()
        super().emit(record)


def create_custom_logger(log_dir):
    log_filename_template = 'WebServer_{}.log'
    handler = DailyRotatingFileHandler(log_dir, log_filename_template)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger


# 폴더내 license.lic 정보를 읽고 public.key 값으로 검증한 이후 날짜 정보를 확인
# pip install 항목 2024.08.06 기준으로 설치된 버전을 표기함.
# pip install cryptography==43.0.0 pytz==2024.1
# cryptography 설치시 같이 설치되는 항목 : pycparser==2.22, cffi==1.16.0
# 사용방법
# ex) lic_checker = LicenseChecker()
#     result = lic_checker.verifyLicense() # 결과값이 True 일경우 라이센스가 유효한 상태, False 일경우 만료되거나 유효하지 않은 상태


# AES256 암호화를 위한 키 (32바이트, 256비트)
SECRET_KEY = b'your-secret-key-32bytes'  # 32바이트 길이로 설정


# AES256 암호화 함수
def encrypt(data, key):
    iv = os.urandom(16)  # 16바이트 초기화 벡터
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(data) + padder.finalize()

    encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

    return base64.b64encode(iv + encrypted_data).decode('utf-8')


# 기록 파일 경로 설정
appdata_folder = os.getenv('APPDATA')
hidden_folder = os.path.join(appdata_folder, '.hidden_license')
if not os.path.exists(hidden_folder):
    os.makedirs(hidden_folder)

record_file = os.path.join(hidden_folder, 'license_record.txt')


def save_license_check():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    encrypted_time = encrypt(current_time.encode('utf-8'), SECRET_KEY)
    with open(record_file, 'w') as f:
        f.write(encrypted_time)


def decrypt(enc_data, key):
    enc_data = base64.b64decode(enc_data)
    iv = enc_data[:16]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    decrypted_data = decryptor.update(enc_data[16:]) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    data = unpadder.update(decrypted_data) + unpadder.finalize()

    return data.decode('utf-8')


def verify_license_check():
    # 기록 파일 경로 설정
    appdata_folder = os.getenv('APPDATA')
    hidden_folder = os.path.join(appdata_folder, '.hidden_license')
    record_file = os.path.join(hidden_folder, 'license_record.txt')

    if not os.path.exists(record_file):
        logging.info("라이선스 체크 기록 파일이 없으므로, 체크를 생략합니다.")
        return

    if os.path.getsize(record_file) == 0:
        logging.info("라이선스 체크 기록 파일이 비어 있으므로, 체크를 생략합니다.")
        return

    with open(record_file, 'r') as f:
        encrypted_time = f.read()

    last_check_time = decrypt(encrypted_time, SECRET_KEY)
    last_check_time = datetime.strptime(last_check_time, '%Y-%m-%d %H:%M:%S')

    current_time = datetime.now()

    if last_check_time >= current_time:
        raise Exception("기록된 시간이 현재 시간보다 미래이거나 현재 시간과 동일합니다. 프로그램을 정지합니다!")

    if current_time.date() == last_check_time.date():
        raise Exception("오늘 자정에 라이선스 체크가 수행되지 않았습니다!")


class LicenseChecker:
    def load_public_key(self, pem_key):
        try:
            key = load_pem_public_key(pem_key.encode())
            logging.info("Public key loaded successfully")
            return key
        except ValueError as e:
            logging.error(f"Failed to load public key: {e}")
            return None

    def verify_license_key_new(self, hardware_id, license_key):
        try:
            parts = license_key.split('.')
            if len(parts) != 3:
                logging.error("License key split failed: Incorrect format")
                return False, None

            try:
                data = base64.b64decode(parts[0])
                signature = base64.b64decode(parts[1])
                public_key = self.load_public_key(self.convert_to_pem_format(base64.b64decode(parts[2])))
                logging.info("Base64 decoding successful")
            except Exception as e:
                logging.error(f"Base64 decoding failed: {e}")
                return False, None

            try:
                public_key.verify(
                    signature,
                    data,
                    padding.PKCS1v15(),
                    hashes.SHA256()
                )
                logging.info("Signature verification successful")
            except Exception as e:
                logging.error(f"Signature verification failed: {e}")
                return False, None

            license_data = data.decode('utf-8')
            license_parts = license_data.split('|')
            if len(license_parts) != 2:
                logging.error("License data split failed: Incorrect format")
                return False, None

            license_hardware_id = license_parts[0]
            if license_hardware_id.lower() != hardware_id.lower():
                logging.error("Hardware ID mismatch")
                return False, None

            iso_string = license_parts[1]
            try:
                expiry_date = parser.isoparse(iso_string)
                expiry_date = expiry_date.replace(microsecond=0, tzinfo=None)
            except ValueError as e:
                logging.error(f"Invalid isoformat string: {e}")
            timezone = pytz.timezone('Asia/Seoul')
            current_time_in_timezone = datetime.now(timezone)
            current_time_in_timezone = current_time_in_timezone.replace(microsecond=0, tzinfo=None)
            if current_time_in_timezone > expiry_date:
                logging.info("License key expired")
                return False, None

            return True, expiry_date
        except Exception as e:
            logging.error(f"Verification failed: {e}")
            return False, None

    def convert_to_pem_format(self, base64_public_key):
        try:
            der_public_key = base64.b64decode(base64_public_key)

            public_key = serialization.load_der_public_key(der_public_key)

            pem_public_key = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            return pem_public_key.decode('utf-8')
        except Exception as e:
            logging.error(f"Failed to convert public key to PEM format: {e}")
            return None

    @staticmethod
    def get_mac_address():
        # 네트워크 어댑터 목록을 가져옵니다.
        interfaces = psutil.net_if_addrs()
        # "Ethernet"과 "이더넷"이라는 이름을 가진 어댑터의 MAC 주소를 찾아 반환합니다.
        for interface in interfaces:
            if interface.startswith("Ethernet") or interface.startswith("이더넷"):
                for addr in interfaces[interface]:
                    if addr.family == psutil.AF_LINK:  # MAC 주소는 AF_LINK로 식별됩니다.
                        return addr.address.replace('-', '')

        return "Ethernet adapter not found"

    def verifyLicense(self):
        base64_public_key = ''
        license_key = ''
        try:
            # with open('public.key', 'r') as key_file:
            #     base64_public_key = key_file.read()
            with open('license.lic', 'r') as lic_file:
                license_key = lic_file.read()
        except FileNotFoundError:
            logging.error(f"License file not found.")
            return False

        is_valid, expiry_date = self.verify_license_key_new(self.get_mac_address(), license_key)
        logging.info(f"License Key is Valid: {is_valid}")
        if is_valid:
            logging.info(f"License Key Expiry Date: {expiry_date}")
        return is_valid


lic_checker = LicenseChecker()
result = lic_checker.verifyLicense()
if not result:
    logging.info("License 정보가 유요하지 않아 프로그램을 종료합니다.")
    sys.exit()


def check_license():
    verify_license_check()
    lic_checker = LicenseChecker()
    result = lic_checker.verifyLicense()
    logging.info(f"License verification result: {result}")
    save_license_check()
    if not result:
        logging.info("License 정보가 유요하지 않아 프로그램을 종료합니다.")
        shutdown_service()


def create_connection(db_file):
    """SQLite 데이터베이스에 연결하는 함수"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {db_file}")
    except Error as e:
        print(e)
    return conn


def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY,
                bf_image_name TEXT NOT NULL,
                af_image_name TEXT NOT NULL,
                screen TEXT NOT NULL,
                screen_name TEXT NOT NULL,
                cam TEXT NOT NULL,
                cam_name TEXT NOT NULL,
                time TEXT,
                date TEXT,
                register_ts TEXT,
                cam_count TEXT NOT NULL,
                detection_type TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_screen ON files(screen)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cam ON files(cam)")
        logging.info("Table creation complete ")
    except sqlite3.Error as e:
        logging.error(f"error message: {e}")


class Alarm:
    def __init__(self, tower_lamp, QUvc_dll, Usb_Qu_write, Usb_Qu_Open, Usb_Qu_Close, Usb_Qu_Getstate, C_lampoff,
                 C_lampon, C_lampblink, C_D_not):
        self.tower_lamp = tower_lamp
        self.QUvc_dll = QUvc_dll
        self.Usb_Qu_write = Usb_Qu_write
        self.Usb_Qu_Open = Usb_Qu_Open
        self.Usb_Qu_Close = Usb_Qu_Close
        self.Usb_Qu_Getstate = Usb_Qu_Getstate
        self.C_lampoff = C_lampoff
        self.C_lampon = C_lampon
        self.C_lampblink = C_lampblink
        self.C_D_not = C_D_not

    async def is_connected(self):
        try:
            state = self.Usb_Qu_Getstate()
            return state == 1
        except Exception as e:
            logging.exception("An error occurred while checking the device connection state")
            return False

    async def on(self, lamp_type, lamp_light, lamp_sound):
        if not await self.is_connected():
            logging.error("Device is not connected")
            return {"error": "Device is not connected"}

    async def on(self, lamp_type, lamp_light, lamp_sound):
        try:
            lamp_types = {
                '0': self.C_lampon,
                '1': self.C_lampblink
            }
            l_type = lamp_types.get(lamp_type, self.C_lampoff)

            bchk = False
            bbb = (ctypes.c_byte * 6)()
            bbb[lamp_light] = l_type
            bbb[5] = ctypes.c_byte(lamp_sound)
            bchk = self.Usb_Qu_write(ctypes.c_byte(0), ctypes.c_byte(0), bbb)
            if not bchk:
                raise ValueError("Write operation failed")
            return {"status": "success"}  # Ensure a valid response is returned
        except Exception as e:
            logging.exception("An error occurred in the 'on' method")
            return {"error": str(e)}  # Ensure error response is properly formatted

    async def clear(self):
        try:
            bchk = False
            bbb = (ctypes.c_byte * 6)()
            bbb[0] = self.C_lampoff
            bbb[1] = self.C_lampoff
            bbb[2] = self.C_lampoff
            bbb[3] = self.C_lampoff
            bbb[4] = self.C_lampoff
            bbb[5] = ctypes.c_byte(0)  # sound off
            bchk = self.Usb_Qu_write(ctypes.c_byte(0), ctypes.c_byte(0), bbb)

            if bchk:
                print("All off")
            else:
                print("write error")
        except Exception as e:
            logging.exception("An error occurred in the 'clear' method")


app = FastAPI()

with open('ARGOS.yaml', 'r', encoding='utf-8') as file:
    monitor_config = yaml.safe_load(file)
    image_path = monitor_config['image_path']

path = os.path.join(image_path, "all_images")
if not os.path.exists(path):
    os.makedirs(path)

current_directory = os.path.dirname(__file__)

file_name = './Ux64_dllc.dll'

QUvc_dll = ctypes.CDLL(file_name)
Usb_Qu_write = QUvc_dll.Usb_Qu_write
Usb_Qu_write.restype = ctypes.c_bool
Usb_Qu_write.argtypes = [ctypes.c_byte, ctypes.c_byte, ctypes.POINTER(ctypes.c_byte)]
Usb_Qu_Open = QUvc_dll.Usb_Qu_Open
Usb_Qu_Close = QUvc_dll.Usb_Qu_Close
Usb_Qu_Getstate = QUvc_dll.Usb_Qu_Getstate
Usb_Qu_Getstate.restype = ctypes.c_int
C_lampoff = ctypes.c_byte(0)
C_lampon = ctypes.c_byte(1)
C_lampblink = ctypes.c_byte(2)
C_D_not = ctypes.c_byte(100)
alarm_instance = Alarm(file_name, QUvc_dll, Usb_Qu_write, Usb_Qu_Open, Usb_Qu_Close,
                       Usb_Qu_Getstate, C_lampoff, C_lampon, C_lampblink, C_D_not)

app.mount("/images", StaticFiles(directory=path), name="images")


async def check_files_table():
    conn = sqlite3.connect("database1.db")
    cursor = conn.cursor()

    two_hours_ago = datetime.now() - timedelta(hours=2)

    cursor.execute("SELECT COUNT(*) FROM files WHERE register_ts >= ?", (two_hours_ago,))
    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count == 0


@app.post("/full_screen_save", status_code=status.HTTP_200_OK)
async def full_screen_save(name: str = Form(...), file: UploadFile = File(...)):

    safe_name = name.strip()

    full_screen = os.path.join(image_path, "Full screen")

    os.makedirs(full_screen, exist_ok=True)

    file_extension = os.path.splitext(file.filename)[1]
    if file_extension not in ['.png', '.jpg', '.jpeg']:
        raise HTTPException(status_code=400, detail="Invalid file type. Only PNG, JPG, and JPEG are allowed.")

    file_location = os.path.join(full_screen, f"{safe_name}{file_extension}")

    try:
        with open(file_location, "wb") as f:
            f.write(await file.read())
        logger.info(f"File '{safe_name}{file_extension}' saved at '{file_location}'")
        return {"info": f"File '{safe_name}{file_extension}' saved at '{file_location}'"}

    except Exception as e:
        logger.error(f"Error saving file '{safe_name}{file_extension}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save file '{safe_name}{file_extension}'")


@app.get("/db_check_no_problem")
async def db_check_no_problem():
    role = monitor_config["detection_mode"]
    device_role = monitor_config["device_role"]
    if device_role == "Master":
        ip = "127.0.0.1"
    else:
        ip = monitor_config["master_ip"]
    port = "8000"
    full_screen_url = f"http://{ip}:{port}/full_screen_save"

    try:
        if role == "General":
            monitors = monitor_config['monitors']
            for index, monitor in enumerate(monitors):
                current_path = os.path.join(image_path, monitor["monitor_name"], "captured_screens_cam")
                success = await send_images_to_full_screen(current_path, full_screen_url, "General #" + str(index))
                if success:
                    logger.info(f"Successfully processed images for monitor: {monitor['monitor_name']}")
                else:
                    logger.error(f"Failed to send images for monitor: {monitor['monitor_name']}")
                    raise HTTPException(status_code=500, detail=f"Failed to send images for monitor: {monitor['monitor_name']}")

        elif role == "Fire":
            monitors = monitor_config['monitors']
            for index, monitor in enumerate(monitors):
                current_path = os.path.join(image_path, monitor["monitor_name"], "fire_screen")
                success = await send_images_to_full_screen(current_path, full_screen_url, "Fire #" + str(index))
                if success:
                    logger.info(f"Successfully processed images for monitor: {monitor['monitor_name']}")
                else:
                    logger.error(f"Failed to send images for monitor: {monitor['monitor_name']}")
                    raise HTTPException(status_code=500, detail=f"Failed to send images for monitor: {monitor['monitor_name']}")
    except Exception as e:
        logger.error(f"Error in db_check_no_problem: {e}")
        raise HTTPException(status_code=500, detail="Error in db_check_no_problem")


async def send_images_to_full_screen(current_path, full_screen_url, name):
    try:
        image_files = [f for f in os.listdir(current_path) if f.endswith('.png')]
        if image_files:
            image_file = image_files[0]
            saved_image = os.path.join(current_path, image_file)

            async with httpx.AsyncClient() as client:
                with open(saved_image, 'rb') as f:
                    files = {'file': (image_file, f, 'image/png')}
                    data = {'name': name}

                    response = await client.post(full_screen_url, files=files, data=data)

                    if response.status_code == 200:
                        logger.info(f"Successfully sent {image_file} to full_screen_save API.")
                        return True
                    elif response.status_code == 422:
                        logger.error(f"Unprocessable Entity error for {image_file}: {response.content}")
                        return False
                    else:
                        logger.warning(
                            f"Failed to send {image_file} to full_screen_save API, status code: {response.status_code}")
                        return False
        else:
            logger.warning("No PNG images found in the directory.")
            return False

    except Exception as e:
        logger.error(f"Error in send_images_to_full_screen: {e}")
        return False



@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), monitor_name: str = Form(...)):
    try:
        base_path = os.path.join(image_path, monitor_name, "captured_screens_cam")

        file_name_only, file_extension = os.path.splitext(file.filename)

        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
        return {"filename": file.filename, "file_path": save_path}
    except Exception as e:
        logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
        return JSONResponse(content={"error": "Failed to upload file"}, status_code=500)


@app.post("/upload/coordinate/")
async def upload_file(file: UploadFile = File(...), monitor_name: str = Form(...)):
    try:
        base_path = os.path.join(image_path, monitor_name, "coordinate_screen")

        file_name_only, file_extension = os.path.splitext(file.filename)

        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
        return {"filename": file.filename, "file_path": save_path}
    except Exception as e:
        logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
        return JSONResponse(content={"error": "Failed to upload file"}, status_code=500)


@app.post("/upload/no_signal/")
async def upload_file(file: UploadFile = File(...), monitor_name: str = Form(...)):
    try:
        base_path = os.path.join(image_path, monitor_name, "no_signal_capture")

        file_name_only, file_extension = os.path.splitext(file.filename)

        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
        return {"filename": file.filename, "file_path": save_path}
    except Exception as e:
        logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
        return JSONResponse(content={"error": "Failed to upload file"}, status_code=500)


# 데이터 모델 정의
class FileData(BaseModel):
    bf_image_name: str
    af_image_name: str
    screen: str
    screen_name: str
    cam: str
    cam_name: str
    time: str
    date: str
    register_ts: str
    cam_count: str
    detection_type: str


class AlarmOnRequest(BaseModel):
    lamp_type: str
    lamp_light: str
    lamp_sound: str
    message: str


class GUIManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GUIManager, cls).__new__(cls)
            cls._instance._init_gui()
        return cls._instance

    def _init_gui(self):
        self.root = tk.Tk()
        self.root.title("Alarm Status")
        self.root.geometry(f"+500+300")
        self.root.focus_force()

        # Create a frame for the text widget and scrollbar
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create a Text widget to display messages
        self.text_widget = tk.Text(frame, wrap=tk.WORD, width=90, height=10, padx=20, pady=20)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create a Scrollbar widget
        self.scrollbar = tk.Scrollbar(frame, command=self.text_widget.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Attach the scrollbar to the Text widget
        self.text_widget.config(yscrollcommand=self.scrollbar.set)

        # Create a Clear button
        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_gui, padx=10, pady=5)
        self.clear_button.pack()

    def append_message(self, message):
        self.text_widget.insert(tk.END, message + '\n')
        self.text_widget.yview(tk.END)  # Scroll to the end

    def clear_gui(self):
        async def clear_alarm():
            # Implement your clear alarm logic here
            await alarm_instance.clear()
            self.root.destroy()

        # Run the async function in the event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(clear_alarm())
        loop.close()

        # Clean up the singleton instance to allow for a new instance to be created
        GUIManager._instance = None

    def show(self):
        self.root.mainloop()


def create_gui(message: str):
    def run_gui():
        # Get the singleton instance of GUIManager
        gui_manager = GUIManager()
        gui_manager.append_message(message)
        gui_manager.show()

    # Start the GUI in a new thread
    gui_thread = threading.Thread(target=run_gui)
    gui_thread.start()


def restart_gui(message: str):
    # Clear the existing GUI instance if it exists
    if GUIManager._instance:
        GUIManager._instance.clear_gui()

    # Create a new GUI instance
    create_gui(message)


@app.post("/alarm/on")
async def alarm_on(request: AlarmOnRequest):
    logging.info(f"Received request to turn on alarm: {request.json()}")
    try:
        if await alarm_instance.is_connected():
            result = await alarm_instance.on(int(request.lamp_type), int(request.lamp_light), int(request.lamp_sound))
            if result.get("status") == "failure":
                logging.error(f"Alarm on failed with message: {result}")
                return {"status": "failure", "detail": result["error"]}
            logging.info(f"Alarm on successful with message: {result}")
        # create_gui(request.message)
        return {"status": "success"}
    except Exception as e:
        logging.exception("An unexpected error occurred while processing the alarm on request")
        raise HTTPException(status_code=500, detail="Internal server error. Please try again later.")


@app.post("/insert/file")
async def insert_file(file: FileData):
    conn = create_connection(database)
    if conn is None:
        logging.error("Failed to connect to the database")
        raise HTTPException(status_code=500, detail="Database connection error")

    # bf_image_name이 이미 존재하는지 확인하는 쿼리
    check_sql = '''SELECT 1 FROM files WHERE bf_image_name = ?'''
    insert_sql = '''INSERT INTO files(bf_image_name, af_image_name, screen, screen_name, cam, cam_name, time, date, register_ts, cam_count, detection_type)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?)'''

    cur = conn.cursor()
    try:
        # 존재 여부 확인
        cur.execute(check_sql, (file.bf_image_name,))
        existing = cur.fetchone()

        if existing:
            logging.warning(f"File with bf_image_name '{file.bf_image_name}' already exists. Insertion skipped.")
            return {"message": f"File with bf_image_name '{file.bf_image_name}' already exists. Insertion skipped."}

        # 데이터 삽입
        cur.execute(insert_sql, (
            file.bf_image_name, file.af_image_name, file.screen, file.screen_name, file.cam, file.cam_name, file.time,
            file.date, file.register_ts, file.cam_count, file.detection_type))
        conn.commit()
        last_row_id = cur.lastrowid
        logging.info(f"Data inserted successfully with ID: {last_row_id}")

    except sqlite3.Error as e:
        logging.error(f"Failed to insert data: {e}")
        raise HTTPException(status_code=500, detail="Failed to insert data")

    finally:
        conn.close()
        logging.info("Database connection closed")

    return {"id": last_row_id}


@app.post("/upload/fire/")
async def upload_fire(file: UploadFile = Form(...), monitor_name: str = Form(...)):
    # 파일이 저장될 기본 경로
    try:
        base_path = os.path.join(image_path, monitor_name, "fire_screen")

        file_name_only, file_extension = os.path.splitext(file.filename)

        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
        return {"filename": file.filename, "file_path": save_path}
    except Exception as e:
        logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")


@app.post("/select/detection/file")
async def select_sqlite_detection_file(cam: str = Form(...), screen: str = Form(...)):
    try:
        conn = create_connection(database)
        if conn is None:
            logging.error("Failed to connect to the database")
            raise HTTPException(status_code=500, detail="Database connection error")

        cur = conn.cursor()
        query = "SELECT * FROM files WHERE cam = ? AND screen = ? ORDER BY register_ts DESC LIMIT 1"
        cur.execute(query, (cam, screen))
        row = cur.fetchone()

        if row:
            columns = [column[0] for column in cur.description]
            result = dict(zip(columns, row))
            logging.info(f"File selected: {result}")
        else:
            logging.warning("No files found")
            result = {"error": "No files found"}

        return JSONResponse(content=result)
    except Exception as e:
        logging.error(f"Failed to select file: {e}")
        raise HTTPException(status_code=500, detail="Failed to select file")
    finally:
        if conn:
            conn.close()
            logging.info("Database connection closed")


@app.post("/send/main/fire_detection")
async def send_main_fire_detection(file: UploadFile = Form(...)):
    base_path = os.path.join(image_path, "detection_screenshots")

    file_name_only, file_extension = os.path.splitext(file.filename)
    save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")

    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
        return {"filename": file.filename, "file_path": save_path}
    except Exception as e:
        logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
        return JSONResponse(content={"error": "Failed to upload file"}, status_code=500)


@app.post("/send/main/hidden_eyes_detection")
async def send_main_hidden_eyes_detection(files: list[UploadFile] = File(...)):
    base_path = os.path.join(image_path, "detection_screenshots")
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    saved_files = []
    for file in files:
        file_name_only, file_extension = os.path.splitext(file.filename)
        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
            saved_files.append({"filename": file.filename, "file_path": save_path})
        except Exception as e:
            logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
            return JSONResponse(content={"error": f"Failed to upload file '{file.filename}'"}, status_code=500)
    return {"saved_files": saved_files}


@app.post("/send/main/lost_signal")
async def send_main_lost_signal(files: list[UploadFile] = File(...)):
    base_path = os.path.join(image_path, "detection_screenshots")
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    saved_files = []
    for file in files:
        file_name_only, file_extension = os.path.splitext(file.filename)
        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
            saved_files.append({"filename": file.filename, "file_path": save_path})
        except Exception as e:
            logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
            return JSONResponse(content={"error": f"Failed to upload file '{file.filename}'"}, status_code=500)
    return {"saved_files": saved_files}


@app.post("/send/main/all_images")
async def send_main_all_images(files: list[UploadFile] = File(...), date: str = Form(...),
                               cam: str = Form(...), folder_name: str = Form(...), monitor_name: str = Form(...)):
    base_path = os.path.join(image_path, "all_images", date, monitor_name, cam, folder_name)
    saved_files = []
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    for file in files:
        file_name_only, file_extension = os.path.splitext(file.filename)
        save_path = os.path.join(base_path, f"{file_name_only}{file_extension}")
        try:
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            logging.info(f"File '{file.filename}' uploaded successfully. Saved to '{save_path}'")
            saved_files.append({"filename": file.filename, "file_path": save_path})
        except Exception as e:
            logging.error(f"Failed to upload file '{file.filename}'. Error: {e}")
            saved_files.append({"filename": file.filename, "error": str(e)})
    if any("error" in file for file in saved_files):
        return JSONResponse(content={"files": saved_files}, status_code=500)

    return {"files": saved_files}


@app.post("/send/yaml_file")
async def send_yaml_file():
    file_path = "ARGOS.yaml"
    if os.path.exists(file_path):
        logging.info(f"File '{file_path}' found, preparing to send")
        return FileResponse(file_path, media_type='application/octet-stream', filename='ARGOS.yaml')
    else:
        logging.error(f"File '{file_path}' not found")
        return {"error": "File not found"}


@app.post("/upload/multiple/")
async def upload_multiple_files(
        image: UploadFile = File(...),
        text: UploadFile = File(...),
):
    try:
        upload_folder = './monitors'
        os.makedirs(upload_folder, exist_ok=True)
        logging.info(f"Upload folder '{upload_folder}' is ready")

        if image:
            image_path = os.path.join(upload_folder, image.filename)
            async with aiofiles.open(image_path, "wb") as f:
                content = await image.read()
                await f.write(content)
            logging.info(f"Image file '{image.filename}' uploaded successfully to '{image_path}'")

        if text:
            text_path = os.path.join(upload_folder, text.filename)
            async with aiofiles.open(text_path, "wb") as f:
                content = await text.read()
                await f.write(content)
            logging.info(f"Text file '{text.filename}' uploaded successfully to '{text_path}'")

        return JSONResponse(content={"message": "Files uploaded successfully", "files": {
            "image": image.filename,
            "text": text.filename
        }})
    except Exception as e:
        logging.error(f"Failed to upload files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload files: {e}")


def list_image_files(directory):
    return [f for f in os.listdir(directory) if f.endswith(('.png', '.jpg', '.jpeg', '.gif'))]


@app.get("/folders/{date}/{monitor_name}/{cam_name}/{detection_time}", response_class=HTMLResponse)
async def get_images(date: str, monitor_name: str, cam_name: str, detection_time: str):
    combined_folder_path = os.path.join(path, date, monitor_name, cam_name, detection_time)
    if not os.path.isdir(combined_folder_path):
        raise HTTPException(status_code=404, detail="Folder not found")
    image_files = list_image_files(combined_folder_path)
    # HTML 컨텐츠를 생성합니다.
    html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Image Slideshow</title>
                <style>
                body, html {
                    height: 100%;
                    margin: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    color: #fff;
                }
                .slideshow-container {
                    width: 800px;
                    height: 600px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    overflow: hidden;
                }
                .slideshow-image {
                    display: none;
                    width: 800px;
                    height: 600px;
                    object-fit: contain;
                }
            </style>
                <script>
                    let imageIndex = 0;
                    function showNextImage() {{
                        let images = document.getElementsByClassName('slideshow-image');
                        for (let i = 0; i < images.length; i++) {{
                            images[i].style.display = 'none';
                        }}
                        images[imageIndex].style.display = 'block';
                        imageIndex = (imageIndex + 1) % images.length;
                        setTimeout(showNextImage, 500);
                    }}
                    window.onload = function() {{
                        showNextImage();
                    }}
                </script>
            </head>
            <body>
                <div class="slideshow-container">
            """

    for idx, image_file in enumerate(image_files):
        html_content += f"""
                    <img src="/images/{date}/{monitor_name}/{cam_name}/{detection_time}/{image_file}" class="slideshow-image">
                """

    html_content += """
                </div>
            </body>
            </html>
            """

    return HTMLResponse(content=html_content)


class MessageRequest(BaseModel):
    type: str


def get_latest_record(sensor_name: str, room_name: str) -> dict:
    ensure_table_exists()
    conn = sqlite3.connect('modbus.db')
    cursor = conn.cursor()

    today = datetime.today().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())

    cursor.execute('''
        SELECT * FROM sensor
        WHERE sensor_name = ? AND room_name = ?
          AND times BETWEEN ? AND ?
        ORDER BY times DESC
        LIMIT 1
    ''', (sensor_name, room_name, today_start, today_end))

    record = cursor.fetchone()
    conn.close()

    if record:
        return {
            'sensor_name': record[2],
            'room_name': record[1],
            'times': datetime.strptime(record[4], '%Y-%m-%d %H:%M:%S')  # Ensure times is a datetime object
        }
    else:
        return {}


async def send_zalo_detection_message(detection_type: str, sensor_id: str, value: str, room: str,
                                      isDbSaveEnabled: bool, mqtt_client_handler):
    url = 'https://openapi.zalo.me/v3.0/oa/group/message'
    accessToken = monitor_config["access_token"]
    group_id = monitor_config["alarm_group_id"]
    company_name = mqtt_client_handler.company_name
    device_role = mqtt_client_handler.device_role

    try:
        room_config = await load_room_config('RoomName.yaml')
    except Exception as e:
        logging.error(f"Failed to load room config: {e}")
        # MQTT로 에러 전송
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue=f"/send-message: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to load room configuration")

    room_name = None
    sensor_description = None

    # 룸 이름과 센서 설명 가져오기
    if 'rooms' in room_config:
        for room_info in room_config['rooms']:
            if room_info['id'] == str(room):
                room_name = room_info['name']
                if sensor_id:
                    sensor = next((s for s in room_info['sensors'] if s['id'] == int(int(sensor_id) + 1)), None)
                    if sensor:
                        sensor_description = sensor['description']

    if not room_name or not sensor_description:
        logging.error("Room name or sensor description not found.")
        # MQTT로 에러 전송
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue="Room or sensor not found"
        )
        raise HTTPException(status_code=404, detail="Room or sensor not found")

    message = f"{room_name} / {sensor_description} / {detection_type} / {value}"
    headers = {
        'access_token': accessToken,
        'Content-Type': 'application/json'
    }
    data = {
        "recipient": {
            "group_id": group_id
        },
        "message": {
            "text": message
        }
    }

    try:
        # Zalo 메시지 전송
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)

        if response.status_code == 200:
            logging.info("Message sent successfully")

            # MQTT로 성공 메시지 전송
            mqtt_client_handler.publish_message(
                topic="db/append/monitoring",
                company=company_name,
                role=device_role,
                value=1,
                extensionValue=""
            )

            # 데이터베이스에 저장
            if isDbSaveEnabled:
                save_to_database(
                    room_name=room_name,
                    sensor_name=sensor_description,
                    content=message,
                    detection_type=detection_type,
                    value=float(value)
                )
        else:
            logging.error(f"Failed to send message: {response.status_code} - {response.text}")
            # MQTT로 에러 전송
            mqtt_client_handler.publish_message(
                topic="db/append/monitoring",
                company=company_name,
                role=device_role,
                value=-1,
                extensionValue=f"/send-message: {response.status_code} - {response.text}"
            )
            raise HTTPException(status_code=500, detail="Failed to send message")

    except httpx.RequestError as e:
        logging.error(f"HTTP request error: {e}")
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue=f"/send-message: {e}"
        )
        raise HTTPException(status_code=500, detail="Request error")

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue=f"/send-message: {e}"
        )
        raise HTTPException(status_code=500, detail="Unexpected error")


async def load_room_config(file_path: str) -> dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            return config
    except Exception as e:
        logging.error(f"Failed to load room config from {file_path}: {e}")


async def send_modbus_error_message(message: str, room: str, sensor_id: str, mqtt_client_handler):
    company_name = mqtt_client_handler.company_name
    device_role = mqtt_client_handler.device_role
    try:
        room_config = await load_room_config('RoomName.yaml')
        room_name = None
        sensor_description = None
        alarm = room_config.get("alarm_minute", 60)

        for room_info in room_config.get('rooms', []):
            if room_info['id'] == room:
                room_name = room_info['name']
                if sensor_id:
                    sensor = next((s for s in room_info['sensors'] if s['id'] == int(sensor_id) + 1), None)
                    if sensor:
                        sensor_description = sensor['description']

        latest_record = get_latest_record(sensor_description or '', room_name or '')
        now = datetime.now()

        if latest_record:
            last_sent_time = latest_record['times']
            time_diff = now - last_sent_time
        else:
            time_diff = timedelta.max

        if time_diff > timedelta(minutes=alarm):
            if room_name and sensor_description:
                full_message = (f"{message} = {room_name} / {sensor_description} / 확인이 필요합니다. \n"
                                f"{message} = {room_name} / {sensor_description} / Cần phải xác nhận.")
            elif room_name:
                full_message = (f"{message} = {room_name} / 확인이 필요합니다.\n"
                                f"{message} = {room_name} / Cần phải xác nhận.")
            else:
                full_message = (f"{message} = 확인이 필요합니다.\n"
                                f"{message} = Cần phải xác nhận.")

            url = 'https://openapi.zalo.me/v3.0/oa/group/message'
            access_token = monitor_config["access_token"]
            group_id = monitor_config["alarm_group_id"]

            headers = {
                'access_token': access_token,
                'Content-Type': 'application/json'
            }
            data = {
                "recipient": {
                    "group_id": group_id
                },
                "message": {
                    "text": full_message
                }
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=data)

            if response.status_code == 200:
                logging.info("Error message sent successfully")

                # 데이터베이스에 저장
                save_to_database(room_name or "", sensor_description or "", full_message, detection_type="Error",
                                 value=0.0)

                # MQTT 성공 메시지 전송
                mqtt_client_handler.publish_message(
                    topic="db/append/monitoring",
                    company=company_name,
                    role=device_role,
                    value=1,
                    extensionValue=""
                )
            else:
                # MQTT 실패 메시지 전송
                mqtt_client_handler.publish_message(
                    topic="db/append/monitoring",
                    company=company_name,
                    role=device_role,
                    value=-1,
                    extensionValue=f"/send_modbus_error_message: {response.status_code} - {response.text}"
                )
                raise HTTPException(status_code=500, detail="Failed to send message")

    except Exception as e:
        logging.error(f"Error in send_modbus_error_message: {e}")

        # MQTT 에러 메시지 전송
        mqtt_client_handler.publish_message(
            topic="db/append/monitoring",
            company=company_name,
            role=device_role,
            value=-1,
            extensionValue=f"/send_modbus_error_message: {e}"
        )
        raise HTTPException(status_code=500, detail="Failed to process the error message")


def ensure_table_exists():
    try:
        with sqlite3.connect('modbus.db') as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensor'")
            table_exists = cursor.fetchone()

            if not table_exists:
                cursor.execute('''
                    CREATE TABLE sensor (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        room_name TEXT,
                        sensor_name TEXT,
                        content TEXT,
                        times TEXT,
                        type TEXT,
                        value REAL
                    )
                ''')
                conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise


# async def get_files_last_hour():
#     one_hour_ago = datetime.now() - timedelta(hours=1)
#     conn = None
#     try:
#         conn = sqlite3.connect('database.db')
#         cursor = conn.cursor()
#         query = """
#            SELECT * FROM files 
#            WHERE register_ts >= ?
#        """
#         cursor.execute(query, (one_hour_ago,))
#         records = cursor.fetchall()
#         return records if records else None
#
#     except Exception as e:
#         logging.error(f"Error querying files from the last hour: {e}")
#         return None


@app.post("/send-hour-message")
async def send_alert():
    try:
        company_name = monitor_config["company_name"]
        device_role = monitor_config["device_role"]

        mqtt_client_handler = MqttClientHandler(
            broker_ip="61.109.249.21",
            broker_port=5653,
            company_name=company_name,
            device_role=device_role
        )
        sensor_records = await get_sensor_min_max_avg_value()
        # file_records = await get_files_last_hour()

        await send_zalo_message(sensor_records, mqtt_client_handler)

        logger.info("Successfully retrieved sensor and file records, and sent Zalo message.")
        return {"sensor_records": sensor_records}

    except Exception as e:
        logger.error(f"Error in send_alert: {e}")
        return {"error": str(e)}


async def get_monitor_description(screen, monitor_config):
    for monitor in monitor_config.get('monitors', []):
        if monitor.get('monitor_name') == screen:
            return monitor.get('monitor_description')
    return ""


class MqttClientHandler:
    def __init__(self, broker_ip, broker_port, company_name, device_role):

        self.client = mqtt.Client()
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

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT 브로커에 연결 성공")
        else:
            print(f"연결 실패, 에러 코드: {rc}")

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


# 메시지 전송 함수
async def send_zalo_message(records, mqtt_client_handler):
    url = 'https://openapi.zalo.me/v3.0/oa/group/message'
    access_token = "your_access_token"
    company_name = mqtt_client_handler.company_name
    device_role = mqtt_client_handler.device_role
    group_id = "your_group_id"
    headers = {
        'access_token': access_token,
        'Content-Type': 'application/json'
    }

    try:
        room_config = await load_room_config('RoomName.yaml')
    except Exception as e:
        logging.error(f"Failed to load room config: {e}")
        mqtt_client_handler.publish_message("db/append/monitoring", company_name, device_role, -1,
                                            f"Error loading room config: {e}")
        return

    messages = []

    # human_detected = False
    # fire_detected = False

    # if file_records:
    #     for file_record in file_records:
    #         (files_id, _, _, screen, _, cam, _, _, _,
    #          register_ts, _, detection_type) = file_record
    #         monitor_description = await get_monitor_description(screen, monitor_config)
    #         if detection_type == "Human":
    #             human_detected = True
    #             file_message = f"{company_name} / {monitor_description} = {register_ts} / {cam} / {detection_type}"
    #             messages.append(file_message)
    #         elif detection_type == "Fire":
    #             fire_detected = True
    #             file_message = f"{company_name} / {monitor_description} = {register_ts} / {cam} / {detection_type}"
    #             messages.append(file_message)
    #
    # if not human_detected and not fire_detected:
    #     messages.append(f"{company_name} / General 이상 없습니다.")
    #     messages.append(f"{company_name} / Fire 이상 없습니다.")
    #
    # elif not human_detected:
    #     messages.append(f"{company_name} / General 이상 없습니다.")
    #
    # elif not fire_detected:
    #     messages.append(f"{company_name} / Fire 이상 없습니다.")
    if records:
        messages.append(f"--------{company_name}--------")
        for record in records:
            id_, register_time, min_value, max_value, avg_value, sensor_type, room, slave_id, current_value = record

            room_name = next((r['name'] for r in room_config['rooms'] if r['id'] == room), room)
            sensor_description = next((s['description'] for r in room_config['rooms'] for s in r['sensors']
                                       if r['id'] == room and s['id'] == int(slave_id)), slave_id)

            message = f"{room_name} / {sensor_description} / {sensor_type} ({min_value:.1f}, {max_value:.1f}, {avg_value:.1f}) / {current_value}"
            messages.append(message)

    if not messages:
        logger.warning("No messages to send, skipping Zalo message.")
        return

    final_message = "\n".join(messages)

    data = {
        "recipient": {
            "group_id": group_id
        },
        "message": {
            "text": final_message
        }
    }

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(url, headers=headers, json=data)
            response.raise_for_status()
            mqtt_client_handler.publish_message("db/append/monitoring", company_name, device_role, 1, "")
    except httpx.HTTPStatusError as e:
        logging.error(f"Error sending message to Zalo: {e.response.text}")
        mqtt_client_handler.publish_message("db/append/monitoring", company_name, device_role, -1, f"Error Zalo: {e.response.text}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        mqtt_client_handler.publish_message("db/append/monitoring", company_name, device_role, -1, f"Error Zalo: {e}")


async def get_sensor_min_max_avg_value():
    try:
        conn = sqlite3.connect("modbus.db")
        cursor = conn.cursor()

        time_end = datetime.now()
        time_start = time_end - timedelta(hours=1)

        query_range = """
            SELECT id, register_time, min_value, max_value, avg_value, type, room, slave_id, current_value
            FROM min_max
            WHERE (room, slave_id, type, register_time) IN (
                SELECT room, slave_id, type, MAX(register_time)
                FROM min_max
                WHERE register_time BETWEEN ? AND ?
                GROUP BY room, slave_id, type
            )
            ORDER BY register_time DESC
        """

        cursor.execute(query_range, (time_start.strftime('%Y-%m-%d %H:%M:%S'),
                                     time_end.strftime('%Y-%m-%d %H:%M:%S')))
        records = cursor.fetchall()

        if not records:
            records = None
    except Exception as e:
        records = None
    finally:
        if conn:
            conn.close()

    return records


def save_to_database(room_name: str, sensor_name: str, content: str, detection_type: str, value: float):
    try:
        ensure_table_exists()

        with sqlite3.connect('modbus.db') as conn:
            cursor = conn.cursor()

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO sensor (room_name, sensor_name, content, times, type, value)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (room_name, sensor_name, content, current_time, detection_type, value))

            conn.commit()

    except sqlite3.OperationalError as e:
        logging.error(f"SQLite operational error: {e}")
        raise HTTPException(status_code=500, detail="Database operational error")
    except sqlite3.DatabaseError as e:
        logging.error(f"SQLite database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error")


class Message(BaseModel):
    detection_type: str
    sensor_id: str
    value: str
    room: str
    isDbSaveEnabled: bool


@app.post("/send-message")
async def send_message(request: Message):
    try:
        # MQTT 클라이언트 핸들러 생성
        company_name = monitor_config["company_name"]
        device_role = monitor_config["device_role"]

        mqtt_client_handler = MqttClientHandler(
            broker_ip="61.109.249.21",
            broker_port=5653,
            company_name=company_name,
            device_role=device_role
        )

        await send_zalo_detection_message(
            detection_type=request.detection_type,
            sensor_id=request.sensor_id,
            value=request.value,
            room=request.room,
            isDbSaveEnabled=request.isDbSaveEnabled,
            mqtt_client_handler=mqtt_client_handler  # MQTT 핸들러 전달
        )
        return {"status": "Message sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send modbus message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


class ErrorMessage(BaseModel):
    message: str
    room: str
    sensor_id: str


# 오류 메시지를 전송하는 API
@app.post("/send-error-message")
async def send_error_message(error_message: ErrorMessage):
    try:
        # MQTT 클라이언트 핸들러 생성
        company_name = monitor_config["company_name"]
        device_role = monitor_config["device_role"]

        mqtt_client_handler = MqttClientHandler(
            broker_ip="61.109.249.21",
            broker_port=5653,
            company_name=company_name,
            device_role=device_role
        )

        await send_modbus_error_message(
            message=error_message.message,
            room=error_message.room,
            sensor_id=error_message.sensor_id,
            mqtt_client_handler=mqtt_client_handler  # MQTT 핸들러 전달
        )
        return {"status": "Error Message sent successfully"}
    except Exception as e:
        logging.error(f"Failed to send modbus error message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send error message")


def cleanup_old_images(images_folder: str, days_old: int = 15):
    now = datetime.now()
    cutoff_date = now - timedelta(days=days_old)

    for folder_name in os.listdir(images_folder):
        folder_path = os.path.join(images_folder, folder_name)
        if os.path.isdir(folder_path):
            folder_creation_time = datetime.fromtimestamp(os.path.getctime(folder_path))
            if folder_creation_time < cutoff_date:
                logging.info(f"Deleting folder: {folder_path}")
                shutil.rmtree(folder_path)
                logging.info(f"Deleted folder: {folder_path}")


def cleanup_old_logs(logs_folder: str, days_old: int = 7):
    now = datetime.now()
    cutoff_date = now - timedelta(days=days_old)

    for folder_name in os.listdir(logs_folder):
        folder_path = os.path.join(logs_folder, folder_name)
        if os.path.isdir(folder_path):
            folder_creation_time = datetime.fromtimestamp(os.path.getctime(folder_path))
            if folder_creation_time < cutoff_date:
                logging.info(f"Deleting folder: {folder_path}")
                shutil.rmtree(folder_path)
                logging.info(f"Deleted folder: {folder_path}")


def cleanup_database():
    db_path = 'database1.db'
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='files';")
        if cursor.fetchone() is None:
            logging.error("Table 'files' does not exist.")
            return

        seven_days_ago = datetime.now() - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')
        table_name = 'files'
        delete_query = f"DELETE FROM {table_name} WHERE register_ts < ?"
        cursor.execute(delete_query, (seven_days_ago_str,))
        conn.commit()
        logging.info(f"Deleted data older than {seven_days_ago_str}.")
        logs_folder = "logs"
        logging.info(f"Running cleanup for logs folder: {logs_folder}")
        cleanup_old_logs(logs_folder)
        all_images_path = os.path.join(image_path, "all_images")
        logging.info(f"Running cleanup for all_images folder: {all_images_path}")
        cleanup_old_images(all_images_path)

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
    except Exception as e:
        logging.error(f"Error in cleanup_database: {e}")
    finally:
        if conn:
            conn.close()


stop_event = threading.Event()


def shutdown_service():
    logging.info("Shutting down the service...")
    stop_event.set()
    os.kill(os.getpid(), signal.SIGINT)


def create_min_max_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS min_max (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        register_time TEXT NOT NULL,
        min_value REAL NOT NULL,
        max_value REAL NOT NULL,
        avg_value REAL NOT NULL,
        type TEXT NOT NULL,
        room TEXT NOT NULL,
        slave_id TEXT NOT NULL,
        current_value TEXT NOT NULL
    );
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating table: {e}")


async def insert_min_max(conn, min_value, max_value, avg_value,
                         current_value, sensor_type, room_id, slave_id, rooms):
    register_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    min_value = round(min_value, 1) if min_value is not None else None
    max_value = round(max_value, 1) if max_value is not None else None
    avg_value = round(avg_value, 1) if avg_value is not None else None
    current_value = round(current_value, 1) if current_value is not None else None

    room_name = next((room['name'] for room in rooms if room['id'] == room_id), room_id)

    insert_sql = """
    INSERT INTO min_max (register_time, min_value, max_value, avg_value, current_value, type, room, slave_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    try:
        c = conn.cursor()
        c.execute(insert_sql, (register_time, min_value, max_value, avg_value,
                               current_value, sensor_type, room_name, int(slave_id) - 1))
        conn.commit()
        logger.info(
            f"Inserted data into min_max table: register_time={register_time}, min_value={min_value}, "
            f"max_value={max_value}, avg_value={avg_value}, current_value={current_value}, "
            f"type={sensor_type}, room={room_id}, slave_id={slave_id}")
    except sqlite3.Error as e:
        logger.error(f"Error inserting data into table: {e}")


async def get_min_max_avg_from_influxdb(client, room_id, sensor_id, sensor_type, start_time, end_time):
    client.switch_database('sensor_data')

    measurement = "sensor_data_table"

    query = f"""
                SELECT MIN("data") AS min_value, 
                       MAX("data") AS max_value, 
                       MEAN("data") AS avg_value, 
                       LAST("data") AS current_value
                FROM "{measurement}"
                WHERE time >= '{start_time}' AND time <= '{end_time}' 
                  AND "room" = '{room_id}' 
                  AND "slave_id" = '{sensor_id}' 
                  AND "type" = '{sensor_type}'
                GROUP BY "room", "slave_id", "type"
            """

    try:
        result = client.query(query)
        points = list(result.get_points())

        if not points:
            logger.warning(
                f"No data points found for room={room_id}, sensor={sensor_id}, type={sensor_type} between {start_time} and {end_time}")
            return {'min_value': None, 'max_value': None, 'avg_value': None, 'current_value': None}

        point = points[0]

        min_max_avg_data = {
            'min_value': point.get('min_value'),
            'max_value': point.get('max_value'),
            'avg_value': point.get('avg_value'),
            'current_value': point.get('current_value')
        }

        logger.info(
            f"Fetched for room={room_id}, sensor_id={sensor_id}, type={sensor_type}: "
            f"min_value={min_max_avg_data['min_value']}, "
            f"max_value={min_max_avg_data['max_value']}, "
            f"avg_value={min_max_avg_data['avg_value']}, "
            f"current_value={min_max_avg_data['current_value']}"
        )
        return min_max_avg_data

    except Exception as e:
        logger.error(f"Error querying InfluxDB: {e}")
        return {'min_value': None, 'max_value': None, 'avg_value': None, 'current_value': None}


async def update_min_max_data(rooms):
    try:
        client = InfluxDBClient(
            host='localhost',
            port=8086,
            username='argos',
            password='argos0520'
        )
    except Exception as e:
        logger.error(f"Error connecting to InfluxDB: {e}")
        return

    try:
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        start_time = one_hour_ago.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_time = now.strftime('%Y-%m-%dT%H:%M:%SZ')

        database = "modbus.db"
        conn = create_connection(database)
        if conn:
            create_min_max_table(conn)
        else:
            logger.error("Error creating connection to SQLite database.")
            return
    except Exception as e:
        logger.error(f"Error preparing time and database connection: {e}")
        return

    try:
        for room in rooms:
            room_id = room['id']
            for sensor in room['sensors']:
                sensor_id = sensor['id']
                for sensor_type in sensor['types']:
                    try:
                        min_max_avg_data = await get_min_max_avg_from_influxdb(client, room_id, sensor_id, sensor_type, start_time, end_time)

                        min_value = min_max_avg_data.get('min_value')
                        max_value = min_max_avg_data.get('max_value')
                        avg_value = min_max_avg_data.get('avg_value')
                        current_value = min_max_avg_data.get('current_value')

                        logger.info(
                            f"Inserting min_value={min_value}, max_value={max_value}, avg_value={avg_value}, "
                            f"current_value={current_value} for room_id={room_id}, sensor_id={sensor_id}, "
                            f"sensor_type={sensor_type} into table"
                        )

                        if min_value is not None and max_value is not None and avg_value is not None and current_value is not None:
                            await insert_min_max(conn, min_value, max_value, avg_value, current_value, sensor_type, room_id, sensor_id, rooms)
                        else:
                            logger.warning(
                                f"Skipping insertion due to None value: min_value={min_value}, max_value={max_value}, "
                                f"avg_value={avg_value}, current_value={current_value}"
                            )
                    except Exception as e:
                        logger.error(f"Error processing sensor {sensor_id} for room {room_id}: {e}")
    except Exception as e:
        logger.error(f"Error processing rooms: {e}")
    finally:
        if conn:
            conn.close()


def check_influxdb():
    try:
        response = requests.get('http://localhost:8086/ping')
        return response.status_code == 204
    except requests.ConnectionError:
        return False


def load_rooms_from_yaml(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
        return data['rooms']


def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def load_monitor_config(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        return config


def reload_monitor_config():
    global monitor_config
    monitor_config = load_monitor_config('ARGOS.yaml')


def monitor_file(file_path, check_interval=10):
    last_hash = get_file_hash(file_path)
    while True:
        time.sleep(check_interval)
        current_hash = get_file_hash(file_path)
        if current_hash != last_hash:
            logging.info(f"{file_path} has been modified.")
            last_hash = current_hash
            reload_monitor_config()


def job_send_alert():
    asyncio.run(send_alert())


async def call_db_check_no_problem_api():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/db_check_no_problem")
            if response.status_code == 200:
                logger.info("Successfully called /db_check_no_problem API.")
                return True
            else:
                logger.warning(f"Failed to call API, status code: {response.status_code}")
                return False
    except Exception as e:
        logger.error(f"Error calling API: {e}")
        return False


async def job_update_min_max_data_async(rooms):
    await update_min_max_data(rooms)


last_sent_time = None


async def job_check_database():
    global last_sent_time
    if last_sent_time is None or (datetime.now() - last_sent_time) >= timedelta(hours=2):
        if await check_files_table():
            logger.info("No records found in the last 2 hours. Calling /db_check_no_problem API.")
            success = await call_db_check_no_problem_api()
            if success:
                last_sent_time = datetime.now()


task_in_progress = False


def run_job_check_database():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(job_check_database())
    except Exception as e:
        logger.error(f"Error in job_check_database: {e}")
    finally:
        loop.close()


def async_job_send_alert():
    # asyncio.run()을 사용하여 이벤트 루프를 명시적으로 실행
    asyncio.run(send_alert())


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    log_dir = os.path.join(os.getcwd(), 'logs')
    logger = create_custom_logger(log_dir)

    logger.info("WebServer start")

    rooms = load_rooms_from_yaml('RoomName.yaml')
    monitor_config = load_monitor_config('ARGOS.yaml')

    monitor_thread = threading.Thread(target=monitor_file, args=('ARGOS.yaml', 1), daemon=True)
    monitor_thread.start()

    job_send_alert()
    schedule.every().day.at("00:00").do(cleanup_database)
    schedule.every().day.at("00:00").do(check_license)
    schedule.every(10).minutes.do(run_job_check_database)

    schedule.every(2).hours.do(job_send_alert)
    if check_influxdb():
        schedule.every(30).minutes.do(lambda: asyncio.run(job_update_min_max_data_async(rooms)))
        asyncio.run(update_min_max_data(rooms))
    else:
        logger.warning("InfluxDB server is not running.")

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()


    try:
        database = "database.db"
        conn = create_connection(database)
        if conn is not None:
            create_table(conn)
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
