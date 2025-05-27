from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ChromeDriver 경로 설정
chrome_driver_path = r"C:\Users\vivans\.wdm\drivers\chromedriver\win64\122.0.6261.69\chromedriver-win32\chromedriver.exe"

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--disable-notifications')  # 알림 비활성화
chrome_options.add_argument('--ignore-certificate-errors')  # 안전하지 않은 사이트 경고 무시

# Chrome 브라우저 시작
driver = webdriver.Chrome(executable_path=chrome_driver_path, options=chrome_options)

# 웹페이지 열기
url = 'http://partner.sunildyfas.com/'
driver.get(url)

# 여기에 추가적인 작업 수행 가능

# 브라우저 종료

