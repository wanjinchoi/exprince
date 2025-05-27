import pandas as pd
import os
import shutil
import openpyxl
from openpyxl.drawing.image import Image
import re
from PIL import Image
import time

wb = openpyxl.load_workbook(r'C:\Users\vivans\Desktop\올포홈\test\k3\test.xlsx')
ws = wb. active

path = r'C:\Users\vivans\Desktop\올포홈\test\k3\image'
img_files = os.listdir(r'C:\Users\vivans\Desktop\올포홈\test\k3\image')

for img_name in img_files:
    # img = Image(path+'/'+img_name)
    im = Image.open(path+'/'+img_name)
    deg = im.transpose(Image.ROTATE_90)
    deg.save(path+'/'+img_name)
    img = openpyxl.drawing.image.Image(path+'/'+img_name)
    img.width = 942.236220472
    img.height = 735.496062992
    ws.add_image(img,'A6')
    wb.save('tt.xlsx')

wb.save('tt.xlsx')

