from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from datetime import datetime, timedelta
import requests
from selenium.common.exceptions import NoAlertPresentException



#경고창 닫기
def handle_alert(driver):
    try:
        alert = driver.switch_to.alert
        print(f"[ALERT] {alert.text.strip()}")
        alert.accept()
        time.sleep(1)
        return True
    except NoAlertPresentException:
        return False

def open_driver():
    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options=options)
    return driver

def extract_time_from_td(td_element):
    ems = td_element.find_elements(By.TAG_NAME, "em")
    for em in ems:
        if "time" in em.get_attribute("class"):
            return em.text.strip()
    m = re.search(r"\d{2}:\d{2}", td_element.text)
    return m.group(0) if m else None

def parse_arr_station_and_time(td):
    text = td.text.strip().replace("\n", "")
    # '대전13:07' 패턴 자동 분리
    m = re.match(r'^([^\d]+)(\d{2}:\d{2})$', text)
    if m:
        return m.group(1), m.group(2)
    # fallback: 뒤에서부터 5글자가 시간일 때 분리
    if len(text) >= 6 and ':' in text[-5:]:
        return text[:-5], text[-5:]
    return text, None

def input_search_conditions(driver, dep, arr, date, time_slot):
    print("🔁 검색 조건 재입력")
    driver.get("https://etk.srail.kr/hpg/hra/01/selectScheduleList.do?pageId=TK0101010000")
    time.sleep(1)

    el = driver.find_element(By.ID, 'dptRsStnCdNm')
    el.clear()
    el.send_keys(dep)
    time.sleep(0.5)
    el.send_keys(Keys.TAB)
    time.sleep(0.2)

    el = driver.find_element(By.ID, 'arvRsStnCdNm')
    el.clear()
    el.send_keys(arr)
    time.sleep(0.5)
    el.send_keys(Keys.TAB)
    time.sleep(0.2)

    driver.execute_script("arguments[0].setAttribute('style','display: block;')",
                          driver.find_element(By.ID, 'dptDt'))
    Select(driver.find_element(By.ID, 'dptDt')).select_by_value(date)

    if time_slot:
        driver.execute_script("arguments[0].setAttribute('style','display: block;')",
                              driver.find_element(By.ID, 'dptTm'))
        dpt_tm_select = Select(driver.find_element(By.ID, 'dptTm'))
        available_options = [opt.text.strip() for opt in dpt_tm_select.options]
        print(f"[디버깅] 출발시간 옵션 목록: {available_options}")

        if time_slot in available_options:
            dpt_tm_select.select_by_visible_text(time_slot)
        else:
            print(f"❌ '{time_slot}' 시간대 없음. 가장 첫 번째 시간('{available_options[0]}')으로 대체.")
            dpt_tm_select.select_by_index(0)

    driver.find_element(By.XPATH, "//input[@value='조회하기']").click()
    time.sleep(2)

def search_and_book(driver, dep, arr, date, time_slot, target_arrival_time, login_id, login_pw):
    input_search_conditions(driver, dep, arr, date, time_slot)

    while True:
        driver.refresh()
        time.sleep(1)
        try:
            rows = driver.find_elements(By.CSS_SELECTOR, "#result-form table tbody tr")
            if not rows:
                print("페이지 없음 → 검색조건 재입력")
                input_search_conditions(driver, dep, arr, date, time_slot)
                time.sleep(5)
                continue

            target_time_obj = datetime.strptime(target_arrival_time, "%H:%M")
            candidate_rows = []
            print(f"[DEBUG] 도착역 후보 & 도착시간 리스트:")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 5:
                    continue

                arr_station, arr_time = None, None
                if len(cells) > 4:
                    arr_station, arr_time = parse_arr_station_and_time(cells[4])

                print(f"  arr_station: '{arr_station}', arr_time: '{arr_time}'")

                if arr_station == arr and arr_time:
                    try:
                        arr_time_obj = datetime.strptime(arr_time, "%H:%M")
                        candidate_rows.append((row, arr_time_obj, arr_time))
                    except:
                        print(f"    -> 시간 파싱 실패: {arr_time}")

            # 후보 전체 출력
            print(f"[DEBUG] 시간 비교 결과 (±30분 이내):")
            min_time = target_time_obj - timedelta(minutes=30)
            max_time = target_time_obj + timedelta(minutes=30)
            for row, arr_time_obj, arr_time in candidate_rows:
                diff = (arr_time_obj - target_time_obj).total_seconds() / 60
                in_range = min_time <= arr_time_obj <= max_time
                print(f"  {arr_time} (차이 {diff:+.0f}분) → {'IN' if in_range else 'OUT'}")

            # 1. 완전 일치 먼저
            found_row = None
            for row, arr_time_obj, arr_time in candidate_rows:
                if arr_time_obj == target_time_obj:
                    found_row = (row, arr_time_obj, arr_time)
                    break

            # 2. ±30분 이내에서 가장 가까운 것(차이 동일하면 더 이른 시간 우선)
            if not found_row:
                in_range = []
                for row, arr_time_obj, arr_time in candidate_rows:
                    if min_time <= arr_time_obj <= max_time:
                        diff = abs((arr_time_obj - target_time_obj).total_seconds())
                        direction = (arr_time_obj - target_time_obj).total_seconds()
                        in_range.append((diff, direction, arr_time_obj, row, arr_time))
                if in_range:
                    in_range.sort(key=lambda x: (x[0], x[1] if x[1] < 0 else 1, x[2]))
                    _, _, _, best_row, best_arr_time = in_range[0]
                    found_row = (best_row, None, best_arr_time)

            if not found_row:
                print(f"⏳ {target_arrival_time}±30분 내 도착(역/시간) 행 없음 → 새로고침 대기")
                time.sleep(5)
                continue

            best_row, _, best_arr_time = found_row
            booked = False
            for cell in best_row.find_elements(By.TAG_NAME, "td"):
                buttons = cell.find_elements(By.CSS_SELECTOR, "a,button,input[type=button]")
                for btn in buttons:
                    txt = (btn.text or "") + (btn.get_attribute("value") or "")
                    if "예약" in txt:
                        print(f"🎯 {arr} {best_arr_time} 도착행 예약 클릭")
                        btn.click()
                        print("🎉 예매 성공! 창을 직접 닫기 전까지 대기")
                        time.sleep(2)
                        while handle_alert(driver):
                            pass
                        if "selectLoginForm.do" in driver.current_url or driver.find_elements(
                                By.ID, "srchDvNm01"):
                            print("🔑 로그인 필요: 자동 로그인 진행")
                            driver.find_element(By.ID, "srchDvNm01").clear()
                            driver.find_element(By.ID, "srchDvNm01").send_keys(login_id)
                            driver.find_element(By.ID, "hmpgPwdCphd01").clear()
                            driver.find_element(By.ID,
                                                "hmpgPwdCphd01").send_keys(
                                login_pw)
                            driver.find_element(By.XPATH, "//input[@type='submit' and contains(@class, 'loginSubmit')]").click()
                            time.sleep(2)
                            print("✅ 로그인 완료")

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
                                print(f"텔레그램 전송 실패: {resp.status_code}, {resp.text}")
                        except Exception as e:
                            print(f"텔레그램 예외: {e}")

                        booked = True
                        while True:
                            time.sleep(10)
            if not booked:
                print(f"⏳ {arr} {best_arr_time} 도착행 예약버튼 없음 → 새로고침 대기")

        except Exception as e:
            print(f"⚠️ 예외 발생: {e} → 검색 조건 다시 입력")
            input_search_conditions(driver, dep, arr, date, time_slot)
        time.sleep(5)

def main():
    dep = input("출발역을 입력하세요: ").strip()
    arr = input("도착역을 입력하세요: ").strip()
    date = input("날짜를 입력하세요 (yyyymmdd): ").strip()
    target_arrival_time = input("목표 도착시각을 입력하세요 (HH:MM): ").strip()
    login_id = input("아이디를 입력하세요: ").strip()
    login_pw = input("비밀번호를 입력하세요: ").strip()

    arr_time = datetime.strptime(target_arrival_time, "%H:%M")
    slot_time = arr_time - timedelta(hours=2)
    slot_hour = (slot_time.hour // 2) * 2
    time_slot = f"{slot_hour:02d}"

    print(f"time_slot: {time_slot}  # (target_arrival_time={target_arrival_time})")

    driver = open_driver()
    try:
        while True:
            search_and_book(driver, dep, arr, date, time_slot, target_arrival_time,login_id, login_pw)
            time.sleep(30)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
