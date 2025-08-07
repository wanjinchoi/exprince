import google.generativeai as genai
def main(text):
    content = f"{text}에서 날짜,출발역, 도착역, 도착시간를 출력해줘"

    genai.configure(api_key="AIzaSyBkyJHsqoOE-_xgk81ncdelLyU81-pbjEk")

    # 사용할 모델 선택 (공식 지원 + 빠름)
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    # 메시지 생성
    response = model.generate_content(content)

    # 결과 출력

    x = response.text
    print(x)


if __name__ == "__main__":
    main('7월2일 수서에서 부산가는 기차중에 17시에 도착하는 기차 예매해줘')