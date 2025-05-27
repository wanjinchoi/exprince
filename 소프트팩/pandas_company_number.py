import pandas as pd


def main(input_path):
    df = pd.read_excel(input_path)
    df = df[(df['세금계산서 발급상태'] == "요청") & (df['기업 사업자번호'].isnull())]
    df = df.drop_duplicates(['주문번호'],keep='first')
    df.to_excel(r"C:\ARGOSRPA\mapping\sample.xlsx", index=None)


if __name__ == '__main__':
    main()

