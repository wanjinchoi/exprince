import time
import sys

import elapsedTimer
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions
from webdriver_manager.chrome import ChromeDriverManager



def toHTML(obj, fname, dom_tree=None):
    try:
        # HTML 문서를 파일로 저장
        html_file_path = fname+'.html'  # HTML 파일을 저장할 경로
        with open(html_file_path, 'w', encoding='utf-8') as file:
            file.write(dom_tree)

        print(f"DOM Tree 저장 성공: {html_file_path}")
    except:
        print(f"DOM Tree 저장 실패")

# ChromeDriver 경로 설정
chrome_driver_path = r"C:\Users\vivans\.wdm\drivers\chromedriver\win64\122.0.6261.69\chromedriver-win32\chromedriver.exe"




# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("detach", True)
chrome_options.add_argument("--headless=old")  # Headless 모드 활성화
chrome_options.add_argument("--disable-gpu")  # GPU 가속 비활성화
chrome_options.add_argument("--incognito")  # secrete mode
chrome_options.add_argument("--window-size=1920,1080")  # 창 크기 설정, 필요에 따라 조정
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.add_argument('--no-sandbox')
#chrome_options.add_argument("--enable-automation");
#chrome_options.add_argument("--disable-extensions");
#chrome_options.add_argument("disable-blink-features")
chrome_options.add_argument("disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-3d-apis")

chrome_options.page_load_strategy = 'none'

# screenshot 생성 할 때, "tile memory limits exceeded" 방지
chrome_options.add_argument('--force-gpu-mem-available-mb=768') # 768 mb 이상, 메시지 없음


# mobile mode
chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1')

chrome_options.add_argument("--timeout=5000")
# WebDriver 객체 생성
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

url = "http://test_btn_delay.com/"

driver.get(url)



# Now click on button
try:
    timer =elapsedTimer.ElapsedTimer()
    # driver.find_element(By.TAG_NAME, 'button').click()
    iframe = WebDriverWait(driver, 5, poll_frequency=0.7).until(
        EC.presence_of_element_located((By.TAG_NAME, "button"))
    )
    elapsed_time = timer.elapsed()
    print(f"Total Elapsed time: {elapsed_time:.2f} s ")
    print(f" - found a button !!")

except exceptions.TimeoutException as e:
        print(f">> {type(e).__name__} for finding button: {e.args}\n")
        
        elapsed_time = timer.elapsed()
        print(f" - Elapsed time for finding button error: {elapsed_time:.2f} s")

        driver.quit()
        sys.exit()

#element = WebDriverWait(driver, 10).until(
#    EC.presence_of_element_located((By.XPATH, '//*[@id="cdasdat"]/div[5]'))
#)

# switch back to default content
# driver.quit() # for TC3 = 연결 거부 오류 발생하고 바로 종료함
# driver.switch_to.default_content()

driver.quit()

# 실행 시간 측정
#elapsed_time = timer.elapsed()
#print(f"Total Elapsed time: {elapsed_time:.2f} s ")