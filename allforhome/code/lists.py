import os
import re
import time
from threading import Timer
import natsort
import pandas as pd
import win32com.client

df = pd.read_csv(r"C:\Users\vivans\Desktop\올포홈\새 폴더 (2)\out_lists2.csv")
root = r"C:\Users\vivans\Desktop\올포홈\새 폴더 (2)"


# def check_process(name):
#     for proc in psutil.process_iter():
#         try:
#             if name.lower() in proc.name().lower():
#                 return True
#         except (
#                 psutil.NoSuchProcess, psutil.AccessDenied,
#                 psutil.ZombieProcess):
#             pass
#     return False;

def print_init(range):
    range = 1
    return range



def print_range(range):
    timeout = 5
    t = Timer(timeout, input,[int(1)])
    t.start()
    range = input("\n값을 입력하세요 : ")
    return range
    if range =='':
        t.cancel()
        range = 1
        return range
    else:
        t.cancel()
        return range


def excel_count(count):
    path = root + "\\" + df.iloc[i].subfolder + "\\" + xlsx[j]
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    try:
        wb = excel.Workbooks.Open(path)
    except Exception as e:
        fail_list.append(str(xlsx[j]) + " / File Path 가 올바르지 않습니다.")
        return 0
    try:
        ws = wb.Worksheets("사진대지")
        ws.Cells(4, 10).Value = count
    except Exception as e:
        fail_list.append(str(xlsx[j]) + " / Sheet Name 이 올바르지 않습니다.")
        return 0
    finally:
        wb.Save()
        excel.Quit()
    per = round(((j + 1) / len(xlsx)) * 100, 2)
    # 프린트 하는 함수, 테스트할 때 아래 코드를 주석처리하고 실행해보면 됨
    # os.startfile(path, "print")
    print(folder + '-' + xlsx[j] + "  진행률: " + str(per) + " %")
    print(time)


fail_list = []
start = time.time()
os.system('taskkill /f /im EXCEL.EXE')
for i in range(len(df)):
    if df.iloc[i].num_subfolders == 0:
        if df.iloc[i].num_files > 0 and df.iloc[i].depth > 1:
            folder = df.iloc[i].subfolder.split('\\')[-1]
            di2 = os.listdir(root + "\\" + df.iloc[i].subfolder)
            di2 = natsort.natsorted(di2)
            xlsx = [li for li in di2 if li.endswith(".xlsx")]
            a = print_range(range)
            # 중간에 실패할 경우 아래 count 변수의 값을 바꾸면 excel의 순번이 거기서부터 시작됨
            print(a)
            if a =='':
               pass
            else:
              del xlsx[:int(a)]
            count = 1
            for j in range(len(xlsx)):
                p = re.compile(r"\[(.+)\]")
                m = p.search(xlsx[j])
                m2 = p.search(xlsx[j - 1])
                try:
                    if m.group(1) == m2.group(1):
                        print()
                except Exception as e:
                    fail_list.append(
                        str(xlsx[j]) + " / 파일명을 비교할 수 없습니다.")
                    count += 1
                    continue
                while True:
                    # 프린터 속도의 조정이 필요할 때 아래 sleep 조정
                    time.sleep(5)
                    if len(xlsx) == 1:
                        excel_count(count)
                        count += 1
                    elif m.group(1) != m2.group(1):
                        excel_count(count)
                        count += 1
                    elif m.group(1) == m2.group(1):
                        excel_count(count - 1)
                    break

print("Time :", round(time.time() - start, 2), "s\n")
if len(fail_list) > 0:
    print("실패한 파일 리스트")
    for k in fail_list:
        print(k)
time.sleep(50000)
