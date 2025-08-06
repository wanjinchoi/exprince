from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime, timedelta
import requests
def open_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    return driver

def extract_arrival_time(cell_text):
    m = re.search(r"\d{2}:\d{2}", cell_text)
    return m.group(0) if m else None

def input_search_conditions(driver, dep, arr, date, time_slot):
    print("🔁 검색 조건 재입력")
    driver.get("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
    time.sleep(1)
    driver.find_element(By.ID, 'dptRsStnCdNm').clear()
    driver.find_element(By.ID, 'dptRsStnCdNm').send_keys(dep)

    driver.find_element(By.ID, 'arvRsStnCdNm').clear()
    driver.find_element(By.ID, 'arvRsStnCdNm').send_keys(arr)

    driver.execute_script("arguments[0].setAttribute('style','display: block;')",
                          driver.find_element(By.ID, 'dptDt'))
    Select(driver.find_element(By.ID, 'dptDt')).select_by_value(date)

    if time_slot:
        driver.execute_script("arguments[0].setAttribute('style','display: block;')",
                              driver.find_element(By.ID, 'dptTm'))
        Select(driver.find_element(By.ID, 'dptTm')).select_by_visible_text(time_slot)

    driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
    time.sleep(2)

def search_and_book(driver, dep, arr, date, time_slot, target_arrival_time):
    input_search_conditions(driver, dep, arr, date, time_slot)

    while True:
        driver.refresh()
        time.sleep(1)

        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "#result-form table tbody tr")
            if not rows:
                print("페이지 없음 → 새로고침 대기")
                time.sleep(5)
                continue

            found = False
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                # 1. 도착시간 셀 존재 확인
                arrival_found = False
                for cell in cells:
                    if extract_arrival_time(cell.text) == target_arrival_time:
                        arrival_found = True
                        break
                if not arrival_found:
                    continue  # 이 row는 해당 도착시간 아님

                # 2. 이 row의 모든 셀에서 "예약/예매" 버튼 탐색
                for cell in cells:
                    buttons = cell.find_elements(By.CSS_SELECTOR, "button, input[type=button], a")
                    for btn in buttons:
                        texts = [
                            btn.text,
                            btn.get_attribute("value") or "",
                            btn.get_attribute("aria-label") or "",
                            btn.get_attribute("title") or ""
                        ]
                        if any("예매" in t or "예약" in t for t in texts):
                            print(f"🎯 {target_arrival_time} 열차 예약 클릭")
                            btn.click()
                            print("🎉 예매 성공! 창을 직접 닫기 전까지 대기")
                            token = "7163901140:AAGuIrkFaeBKzGNf8_jEemmEv6JJnzDtt2U"
                            chatid = "-4695528209"
                            msg = "예약완료 로그인하세요"
                            try:
                                url = f"https://api.telegram.org/bot{token}/sendMessage"
                                data = {"chat_id": chatid, "text": msg}
                                resp = requests.post(url, data=data, timeout=5)
                                if resp.status_code == 200:
                                    print("텔레그램 전송 성공")
                                else:
                                    print(
                                        f"텔레그램 전송 실패: {resp.status_code}, {resp.text}")
                            except Exception as e:
                                print(f"텔레그램 예외: {e}")

                            while True:
                                time.sleep(10)
                # 3. 만약 매진
                for cell in cells:
                    cell_text = cell.text.strip()
                    if "매진" in cell_text:
                        print(f"⏳ {target_arrival_time} 열차 매진 → 새로고침 대기")
                        found = True
                        break
                found = True
                break

            if not found:
                print(f"⏳ {target_arrival_time} 도착시간 열차 없음 → 새로고침 대기")

        except Exception as e:
            print(f"⚠️ 예외 발생: {e} → 검색 조건 다시 입력")
            input_search_conditions(driver, dep, arr, date, time_slot)

        time.sleep(5)

def main():
    dep = input("출발역을 입력하세요: ").strip()
    arr = input("도착역을 입력하세요: ").strip()
    date = input("날짜를 입력하세요 (yyyymmdd): ").strip()
    target_arrival_time = input("목표 도착시각을 입력하세요 (HH:MM): ").strip()

    arr_time = datetime.strptime(target_arrival_time, "%H:%M")
    slot_time = arr_time - timedelta(hours=4)
    time_slot = str(slot_time.hour).zfill(2)

    print(f"time_slot: {time_slot}  # (target_arrival_time={target_arrival_time})")

    driver = open_driver()
    try:
        while True:
            search_and_book(driver, dep, arr, date, time_slot, target_arrival_time)
            time.sleep(30)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
