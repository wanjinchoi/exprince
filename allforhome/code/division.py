import os
import shutil
import pandas as pd
import time
import natsort

df = pd.read_csv(r"C:\Users\vivans\Desktop\올포홈\list.csv")
root = r"C:\Users\vivans\Desktop\올포홈\test\〔2〕   사 진 대 장"

for i in range(len(df)):
    if df.iloc[i].depth > 3 and df.iloc[i].num_subfolders == 0:
        path = root + "\\" + df.iloc[i].subfolder
        count = os.listdir(path)
        div_count = round(len(count) / 4)
        if len(count) > 4:
            for j in reversed(range(div_count - 1)):
                list_pic = os.listdir(path)
                sorted_list = natsort.natsorted(list_pic)
                os.mkdir(path + "-" + str(j))
                shutil.move(path + "\\" + sorted_list[-1],
                            path + "-" + str(j))
                shutil.move(path + "\\" + sorted_list[-2],
                            path + "-" + str(j))
                shutil.move(path + "\\" + sorted_list[-3],
                            path + "-" + str(j))
                shutil.move(path + "\\" + sorted_list[-4],
                            path + "-" + str(j))
print("Division Complete!!")
time.sleep(2)
