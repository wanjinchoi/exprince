from openpyxl.styles.borders import Border, Side
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
import csv
import re


def csv2xlsx(input_path):
    wb = Workbook()
    ws = wb.active
    with open(input_path, 'r') as f:
        for row in csv.reader(f):
            ws.append(row)
    ws.title = "원본"
    wb.save(input_path.replace(".csv", ".xlsx"))
    return input_path.replace(".csv", ".xlsx")


def combine_cell(input_path):
    wb = load_workbook(input_path)
    ws = wb.active
    memo = wb.copy_worksheet(ws)
    memo.title = "메모"
    memo.insert_cols(5)
    memo['E1'].value = "배송메모"
    for i in range(len(ws['A'])):
        tmp = ""
        for j in range(5):
            try:
                keyword_check = memo[chr(70 + j) + str(i + 2)].value.replace(
                    "\n", "")
                Filtered = keyword_filter(keyword_check)
                tmp = tmp + Filtered
            except AttributeError:
                continue
        memo['E' + str(2 + i)].value = tmp
    memo.delete_cols(6, 5)
    valve = wb.copy_worksheet(memo)
    valve.title = "밸브"
    wb.save(input_path)
    return input_path


def sort_cell(xlsx):
    def change_cell(None_Cell_Num, Cell_Num):
        for k in range(6):
            noneList = memo[chr(65 + k) + str(None_Cell_Num)].value
            original = memo[chr(65 + k) + str(Cell_Num)].value
            memo[chr(65 + k) + str(Cell_Num)].value = noneList
            memo[chr(65 + k) + str(None_Cell_Num)].value = original
        wb.save(xlsx)

    wb = load_workbook(xlsx)
    memo = wb['메모']
    for i in range(len(memo['E'])):
        if memo['E' + str(i + 1)].value is None:
            for j in range(i + 1, len(memo['E'])):
                if memo['E' + str(j)].value is not None:
                    change_cell(i + 1, j)
                    break
    return xlsx


def nokoru_valve(input_path):
    wb = load_workbook(input_path)
    valve = wb['밸브']
    arr = ['고글리오', '스위스', 'pp', 'mm', '스티커', '아로마']
    delete_rows = []
    for i in range(len(valve['A']) + 1):
        result_arr = []
        for j in range(len(arr)):
            try:
                if arr[j] in valve['c' + str(i + 1)].value:
                    if len(valve['C' + str(i + 1)].value.split(
                            ",")) == 1 and "mm" in valve[
                        'C' + str(i + 1)].value:
                        result_arr.append(False)
                    else:
                        result_arr.append(True)
                else:
                    result_arr.append(False)
            except TypeError:
                continue
        if any(result_arr):
            continue
        else:
            if i != 0:
                delete_rows.append(i + 1)
    count = 0
    for k in delete_rows:
        valve.delete_rows(k - count)
        count += 1
    wb.save(input_path)
    return input_path
    #  length에 버그 없는지 확인..


def styling(input_path):
    wb = load_workbook(input_path)  # 엑셀 파일 로드
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                         top=Side(style='thin'),
                         bottom=Side(style='thin'))  # 윤각선 속성 설정
    yellowFill = PatternFill(start_color='FFFF00',
                             end_color='FFFF00',
                             fill_type='solid')
    pinkFill = PatternFill(start_color='F2DCDB',
                           end_color='F2DCDB',
                           fill_type='solid')
    beigeFill = PatternFill(start_color='FFF2CC',
                            end_color='FFF2CC',
                            fill_type='solid')
    whiteFill = PatternFill(start_color='FFFFFF',
                            end_color='FFFFFF',
                            fill_type='solid')
    wb['메모'].sheet_properties.tabColor = '00B0F0'  # 메모 탭 색상 변경
    wb['밸브'].sheet_properties.tabColor = 'FFFF00'  # 밸브 탭 색상 변경
    width_list = [15.25, 56.63, 48.5, 13.13, 53, 18]  # 컬럼 너비 초기화
    for i in range(len(width_list)):
        wb['메모'].column_dimensions[chr(65 + i)].width = width_list[
            i]  # 컬럼 너비 적용
    for j in range(len(wb['메모']['A'])):
        wb['메모'].row_dimensions[j + 2].height = 27.75  # 행 높이 적용
    for k in range(len(wb['메모']['E'])):
        if wb['메모']['E' + str(k + 1)].value is None:  # 첫 번째 행은 적용 안함
            break
        else:
            for l in range(2):
                wb['메모'].cell(row=k + 1,
                              column=5 + l).border = thin_border  # 윤곽선 적용
                wb['메모'].cell(row=k + 1, column=5 + l).alignment = Alignment(
                    horizontal='center', vertical='center')  # 정렬 적용
    memo_ = wb['메모']
    tmp = ""
    arr = []
    for i in range(len(memo_['E'])):
        if memo_['E' + str(i + 2)].value != tmp:
            arr.append(i + 1)
        else:
            continue
        tmp = memo_['E' + str(i + 2)].value
    for j in range(len(arr) - 1):
        memo_.merge_cells("E" + str(arr[j] + 1) + ":" + "E" + str(arr[j + 1]))
        memo_.merge_cells("F" + str(arr[j] + 1) + ":" + "F" + str(arr[j + 1]))
    # for i in range(arr[-1] - 1):
    #     memo_['E' + str(i + 1)].fill = yellowFill
    #     memo_['F' + str(i + 1)].fill = yellowFill
    wb['밸브'].insert_cols(1)
    fontStyle = Font(size="15")  # 폰트 사이즈 초기화
    for z in range(len(wb['밸브']['B']) - 1):
        wb['밸브']['A' + str(z + 2)].value = z + 1

    import time
    a = time.strftime("%H")
    if int(a) > 12:
        a = int(a) - 12
    wb['밸브']['A1'].value = str(a) + "시"
    wb['밸브']['F1'].value = "메모"
    wb['밸브']['G1'].value = "인수자"
    width_list = [8.38, 28.63, 54.88, 53, 13.5, 60, 15.88]
    valve_len = len(wb['밸브']['B'])
    for i in range(len(width_list)):
        wb['밸브'].column_dimensions[chr(65 + i)].width = width_list[i]
    for j in range(valve_len):
        wb['밸브'].row_dimensions[j + 1].height = 49.5
        for k in range(8):
            wb['밸브'].cell(row=j + 1, column=1 + k).alignment = Alignment(
                horizontal='center', vertical='center', wrap_text=True)
            wb['밸브'].cell(row=j + 1, column=1 + k).font = fontStyle
        for k in range(3):
            wb['밸브'].cell(row=j + 1, column=2 + k).alignment = Alignment(
                horizontal='left', vertical='center', wrap_text=True)
        for m in range(7):
            wb['밸브'].cell(row=j + 1, column=1 + m).border = thin_border
        if "mm" in wb['밸브']['D'+str(j+1)].value or "고글리" in wb['밸브']['D'+str(j+1)].value \
                or "스위스" in wb['밸브']['D'+str(j+1)].value or "pp" in wb['밸브']['D'+str(j+1)].value\
                or "pbs" in wb['밸브']['D'+str(j+1)].value:
            for n in range(7):
                wb['밸브'].cell(row=j + 1, column=1 + n).fill = beigeFill
        if wb['밸브']['F'+str(j+1)].value is not None:
            for n in range(7):
                wb['밸브'].cell(row=j + 1, column=1 + n).fill = pinkFill
                wb['밸브'].cell(row=1, column=1 + n).fill = whiteFill
        if "스티커" in wb['밸브']['D'+str(j+1)].value:
            for n in range(7):
                wb['밸브'].cell(row=j + 1, column=1 + n).fill = pinkFill
    wb['밸브'].sheet_view.zoomScale = 60  # 확대 비율 적용
    wb['밸브'].page_setup.scale = 48  # 페이지 레이아웃 배율 재설정
    wb['밸브'].print_area = "A1:F" + str(len(wb['밸브']['B']))
    wb.save(input_path)
    return input_path


def keyword_filter(word):
    p = re.compile("(\\d{10})").findall(word)
    if len(p) != 0:
        return ""
    keywd_arr = ['직접 받음', '직접 받고 부재 시 경비실', '직접 받고 부재 시 문 앞']
    # 위 키워드 외 숫자10자리가 들어올 경우 필터링
    for i in keywd_arr:
        if i in word:
            return ""
    return word


def main(csv_path):
    styling(nokoru_valve(sort_cell(combine_cell(csv2xlsx(csv_path)))))
    #  csv2xlsx : csv -> xlsx 파일 형식 변경
    #  combine_cell : 불필요한 메모 열들(네이버,배송메모) 하나의 열로 병합
    #  sort_cell : 위 과정에서 병합된 행들을 정렬함
    #  nokoru_value : 조건에 맞지 않는 행은 삭제
    #  styling : 윤곽선, 폰트, 정렬 및 프린트 영역 설정


if __name__ == '__main__':
    main()
