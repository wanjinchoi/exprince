import csv
import matplotlib
import numpy as np

matplotlib.use('Qt5Agg')
matplotlib.rcParams['font.family'] ='Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] =False
import matplotlib.pyplot as plt
from wordcloud import WordCloud

from PIL import Image

f = open('C:\\Users\\vivans\\Desktop\\test2\\rep2.csv', 'r', encoding='UTF-8')
data = csv.reader(f)
area=[]
amount =[]

for row in data:
    if '대분류' in row[0]:
        pass
    else:
        x = row[0].replace('지방경찰청','')
        if x == '':
            pass
        else:
            area.append(x)
        if row[12] == '':
            pass
        else:
            c = row[12].replace(',', '')
            amount.append(int(c))
result = dict(zip(area, amount))

icon = Image.open('C:\\Users\\vivans\\Desktop\\test2\\car.png')
mask = Image.new("RGB", icon.size, (255,255,255))
mask.paste(icon,icon)
mask = np.array(mask)



wc = WordCloud(random_state = 1234,font_path = 'malgun', width = 400,
               height = 400, background_color = 'white', max_font_size=300, mask=mask, colormap='inferno')

wc2 = wc.generate_from_frequencies(result)

plt.figure(figsize = (10, 10))
plt.axis('off') # 축 없애기
plt.imshow(wc2, interpolation="bilinear")
plt.show()


