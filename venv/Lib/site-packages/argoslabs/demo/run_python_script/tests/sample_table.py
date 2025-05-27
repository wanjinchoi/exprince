import pandas as pd

def main():
    url = 'https://finance.naver.com/sise/lastsearch2.nhn'
    dfs = pd.read_html(url, encoding='euc-kr')
    return dfs[1]

