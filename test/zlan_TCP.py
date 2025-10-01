# tcp_socket_example.py
import socket

IP = "192.168.14.200"
PORT = 4196  # 장비 서비스 포트로 변경
TIMEOUT = 5

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(TIMEOUT)
    try:
        s.connect((IP, PORT))
        # 장비가 단순히 접속만으로 데이터를 보내면 recv로 읽음
        # 또는 프로토콜에 맞는 요청을 전송해야 함
        # 예: s.sendall(b"GET /data\n")
        data = s.recv(4096)
        print("받은 데이터 (바이너리):", data)
        print("받은 데이터 (문자열):", data.decode(errors="replace"))
    except socket.timeout:
        print("연결/응답 타임아웃")
    except Exception as e:
        print("소켓 에러:", e)
