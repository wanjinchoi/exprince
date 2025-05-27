import csv
import matplotlib
matplotlib.use('Qt5Agg')
matplotlib.rcParams['font.family'] ='Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] =False
import matplotlib.pyplot as plt
import seaborn as sns

f = open('C:\\Users\\vivans\\Desktop\\test2\\rep2.csv', 'r', encoding='UTF-8')
data = csv.reader(f)
result = []
result2 = []
name = input('원하는 지역을 적어주세요(bar): ')
name2 = input('원하는 지역을 적어주세요(line): ')

for row in data:
    if name in row[0]:
        for i in row[1:]:
            result.append(int(i.replace(',', '')))
    if name2 in row[0]:
        for i in row[1:]:
            result2.append(int(i.replace(',', '')))


alabels=['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']
colors = sns.color_palette('summer',len(alabels))
potion=list(range(len(alabels)))
x = plt.bar(alabels, result, label=name,color = colors)
plt.title('5개년 누적 월별 음주운전 사고량: '+ name)
c = plt.plot(alabels,result2,linestyle='--',marker='o',color='b',label=name2)

plt.legend()
plt.show()