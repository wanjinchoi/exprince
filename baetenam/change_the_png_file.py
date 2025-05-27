import base64

# PNG 파일을 base64로 인코딩하고 URL 형식으로 변환하는 함수
def png_to_data_url(file_path):
    with open(file_path, "rb") as image_file:
        # 파일을 base64로 인코딩
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # data URL 형식으로 변환
        data_url = f"data:image/png;base64,{encoded_string}"
    return data_url

# 사용 예시
file_path = r"C:\ARGOSRPA\ARGOS_DMS\Master Service\GeneralService\detect_colleters\003046_SC01_5x2_af.png"  # 변환하려는 PNG 파일 경로
data_url = png_to_data_url(file_path)
print(data_url)
