import pandas as pd


def main(input_path):
    file_name = input_path.replace(".xlsx", "")
    df = pd.read_excel(input_path)
    df = df[df['세금계산서 발급상태'] == '요청']
    df = df.drop_duplicates(['주문번호'], keep='first', inplace=False,ignore_index=False)
    df.to_excel(file_name+"replace.xlsx", index=False)
    return file_name+"replace.xlsx"


if __name__ == '__main__':
    main()