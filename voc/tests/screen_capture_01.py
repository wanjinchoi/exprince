import os
import time
from selenium import webdriver
from Screenshot import Screenshot_Clipping
from tempfile import gettempdir


wd_f = os.path.join(gettempdir(), 'PySelenium.cahce', 'win32_Chrome_96.exe')
driver = webdriver.Chrome(wd_f)
driver.maximize_window()
driver.implicitly_wait(10)
driver.get("https://waitbutwhy.com/2020/03/my-morning.html")
obj=Screenshot_Clipping.Screenshot()
img_loc=obj.full_Screenshot(driver, save_path=r'.', image_name='screen_capture_01.png')
print(img_loc)

time.sleep(5)
driver.close()
