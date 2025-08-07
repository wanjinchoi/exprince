import openai
import re
from datetime import datetime
client = openai.OpenAI(api_key="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")# API 키 생략
today = datetime.now()
today_str = today.strftime("%Y.%m.%d")
# 역이름 → 코드 매핑
station_code_map = {
    "수서": "0551", "동탄": "0552", "평택지제": "0553", "경주": "0508", "곡성": "0049",
    "공주": "0514", "광주송정": "0036", "구례구": "0050", "김천구미": "0507", "나주": "0037",
    "남원": "0048", "대전": "0010", "동대구": "0015", "마산": "0059", "목포": "0041",
    "밀양": "0017", "부산": "0020", "서대구": "0506", "순천": "0051", "여수EXPO": "0053",
    "여천": "0139", "오송": "0297", "울산(통도사)": "0509", "익산": "0030", "전주": "0045",
    "정읍": "0033", "진영": "0056", "진주": "0063", "창원": "0057", "창원중앙": "0512",
    "천안아산": "0502", "포항": "0515"
}

# 도착역이 -3시간 적용 대상인 경우
three_hour_arrivals = {
    "서대구", "동대구", "밀양", "울산(통도사)", "부산", "포항", "마산", "진영", "진주",
    "창원", "창원중앙", "공주", "익산", "정읍", "전주", "광주송정", "나주",
    "목포", "여천", "순천", "구례구", "곡성", "남원", "여수EXPO"
}

# 도착시간 기준 출발시각 코드 추출
def get_departure_time_code(arrival_hour: int, arr_name: str) -> str:
    #서대구부터는 -3시간
    subtract_hour = 3 if arr_name in three_hour_arrivals else 2
    #-3시간 뺀값
    departure_hour = max(0, arrival_hour - subtract_hour)
    time_options = [22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2, 0]

    for t in time_options:
        if departure_hour >= t:
            return f"{t:02d}0000"
    return "000000"

def main(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": (f"오늘은 {today_str}이다. "
                                                 "사용자의 문장에서 날짜(월, 일), 출발역, 도착역, 도착 희망 시간을 추출하고, "
                                                 "다음 형식으로 정확히 출력하세요:\n"
                                                 "2025.MM.DD, 출발역, 도착역, HH:mm\n"
                                                 "예시: 2025.07.01, 수서, 부산, 17")},
            {"role": "user", "content": text}], temperature=0)

    gpt_output = response.choices[0].message.content.strip()

    # 정규식으로 결과 파싱
    pattern = r"2025\.(\d{1,2})\.(\d{1,2}),\s*(\S+),\s*(\S+),\s*(\d{1,2})(?::(\d{2}))?"
    match = re.search(pattern, gpt_output)
    if match:
        month, day, dep_name, arr_name, hour,minute  = match.groups()
        minute = minute or "00"
        dep_code = station_code_map.get(dep_name)
        arr_code = station_code_map.get(arr_name)

        if not dep_code or not arr_code:
            print(f"❌ 역 이름 매핑 실패: {dep_name=} {arr_name=}")
            return None

        dptTm_code = get_departure_time_code(int(hour), arr_name)

        # 최종 출력: 날짜, 출발코드, 도착코드, 도착시각, 출발시간코드
        result = f"2025.{int(month):02d}.{int(day):02d},{dep_code},{arr_code},{int(hour):02d}:{minute},{dptTm_code}"
        return result
    else:
        print("⚠ 예상 형식이 아님. GPT 출력 확인 필요.")
        return None

if __name__ == "__main__":
    main('7/10 수서에서 부산가는 기차중 18시에 도착하는 기차 예매해줘')