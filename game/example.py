stocks = "삼성전자/10/85000,카카오/15/130000,LG화학/3/820000,NAVER/5/420000"
sells = [82000, 160000, 835000, 410000]



def stocks_profit(stocks,sells):
    #주식 수익률 계산법 = (현재 주식가격/매수한 주식사격)*100-100
    a = stocks.split(',')
    company = []
    price = []
    p_rate = []
    #회사이름과 구매가 리스트에 담기
    for i in range(len(a)):
        b= a[i].split('/')
        company.append(b[0])
        price.append(b[2])
    # 수익률 계산
    for i in range(len(sells)):
        profit = (int(sells[i]) / int(price[i])) * 100 - 100
        p_rate.append(profit)
    #두개의 리스트 튜플로 묶기
    dic = {k:v for k,v in zip(company,p_rate)}
    #묶은거 순서대로 정렬
    stock_p_sort = sorted(dic.items(), key=lambda item: item[1], reverse=True)
    #출력
    for k, v in stock_p_sort:
        print(f'{k}의 수익률 {v:.3}')

stocks_profit(stocks,sells)