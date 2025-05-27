import win32com.client
import pandas as pd

# Excel 실행
excel = win32com.client.Dispatch("Excel.Application")
excel.Visible = False

# 엑셀 파일 열기
wb = excel.Workbooks.Open("C:/RPA/conv/conv.xlsx")
ws = wb.Sheets("conv")

# 최대 셀 범위 자동 탐지
used_range = ws.UsedRange
row_count = used_range.Rows.Count
col_count = used_range.Columns.Count

# 셀 값 읽기 (수식이 아닌 계산된 값)
data = []
for i in range(1, row_count + 1):
    row = []
    for j in range(1, col_count + 1):
        row.append(ws.Cells(i, j).Value)
    data.append(row)

# 엑셀 닫기
wb.Close(SaveChanges=False)
excel.Quit()

# DataFrame 생성
df = pd.DataFrame(data)

# DataFrame 가공 및 저장
for i in range(len(df.columns)):
    # NaN 제거 → 문자열화 → 양쪽 공백 제거 → 빈 문자열 아닌 것만 필터
    result = df[i].dropna().astype(str).map(str.strip)
    result = result[result != '']  # 빈 문자열 제거
    if not result.empty:
        result.to_excel(f"C:/RPA/conv/conv_result{i + 1}.xlsx", header=False,
                        index=False)