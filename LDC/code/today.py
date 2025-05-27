from datetime import datetime, timedelta


def main(aa):
    # 현재 날짜와 시간 가져오기
    today = datetime.now()

    # 어제 날짜 계산
    yesterday = today - timedelta(days=1)

    # 날짜를 문자열로 변환 (예: "2024-02-05")
    today_str = today.strftime("%Y%m%d")
    yesterday_str = yesterday.strftime("%Y%m%d")
    return yesterday_str

if __name__ == "__main__":
    main('aa')

