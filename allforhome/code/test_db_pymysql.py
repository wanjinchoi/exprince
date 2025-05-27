import pymysql
import openpyxl


connect = pymysql.connect(host='127.0.0.1', user='truewan', password='test1234', db='test',charset='utf8mb4')
cur = connect.cursor()

query ='select*from test_name'
cur.execute(query)
# connect.commit()

datas = cur.fetchall()
data2 =[]
wb = openpyxl.load_workbook('tt.xlsx')
ws = wb.active
for data in datas:
    print(data)
    for i in range(len(data)):
        ws['A'+str(i+1)] = data[i]
wb.save('tt.xlsx')