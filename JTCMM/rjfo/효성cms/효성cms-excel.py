import pandas as pd

def main():
    df = pd.read_excel(r"C:\work\JTCMM\rjfo\효성cms\exceldata.xlsx")

    df_success = df[df['결제상태'].str.contains('결제완료',na=False)]
    df_fail = df[df['결제상태'].str.contains("결제실패|취소",na=False)]

    df_success.to_excel(r"C:\work\JTCMM\rjfo\효성cms\exceldata-success.xlsx")
    df_fail.to_excel(r"C:\work\JTCMM\rjfo\효성cms\exceldata-fail.xlsx")

    #엑셀 파일 읽기
    df = pd.read_excel(r"C:/Users/RPA/Downloads/효성CMS/엑셀 파일 저장/exceldata.xls")

    df_success = df[df['결제상태'].str.contains('결제완료',na=False)]
    df_fail = df[df['결제상태'].str.contains("결제실패|취소",na=False)]

    df_success.to_excel(r"C:/Users/RPA/Downloads/효성CMS/엑셀 결과/exceldata-success.xlsx")
    df_fail.to_excel(r"C:/Users/RPA/Downloads/효성CMS/엑셀 결과/exceldata-fail.xlsx")

if __name__ == "__main__":
    main()