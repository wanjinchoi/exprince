"""
 :ver`1.1` :date`2022.09.27`
====================================
 :mod:`korea.py`
====================================
.. moduleauthor:: MinJung Kim <kkiminjj@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
ARGOS LABS Rossum API unittest module
"""
# Authors
# ===========
#
#
#
# * MinJung Kim
#
# Change Log
# --------
#####################################################
import openpyxl as op
import pandas as pd
import xlwings as xw
from openpyxl.utils import get_column_letter
import warnings
#####################################################


# ==================
# 열 이름을 통해서 필요없는 열 삭제 (pandas)
def excel_pandas(args, check, sina):
    # 설정
    # name = ['pos', 'shipserv', 'sk', 'anglo', 'fleet', 'request', 'hmm']
    name = {
        'pos': ['No', '파트번호', '단위', '수량', '품명'],
        'shipserv': ['Line', 'Part No', 'Item Description', 'Qty', 'Unit'],
        'sk': [],
        'anglo': [],
        'fleet': [],
        'request': [],
        'hmm': []
    }
    cols = []
    # 필요한 리스트 이름 찾기
    for x, n in enumerate(name):
        if n == sina:
            break
    # 엑셀 읽기
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        df = pd.read_excel(args, engine="openpyxl", sheet_name=0)
    # 열 이름 구하기
    for col in df.columns:
        cols.append(col)
    # 필요한 열 제외
    del_col = set(cols) - set(name[n])
    # 필요 없는 열 삭제
    df.drop(del_col, axis=1, inplace=True)
    # 저장
    df.to_excel(args, index=False)


# ==================
# 아이템명과 비고 합친 품명 작성하기 (openpyxl)
def input_excel(args, check, sina):
    if check == 'input':
        # 아이템명과 비고 구하기
        excel = {
            'pos': ['아이템명', '비고'],
            'shipserv': ['Item Description', 'no'],
            'sk': [],
            'anglo': [],
            'fleet': [],
            'request': [],
            'hmm': []
        }
        # 필요한 리스트 이름 찾기
        for x, n in enumerate(excel):
            if n == sina:
                break
        test = excel[n][0]
        tess = excel[n][1]
        # 엑셀 읽기
        wb = op.load_workbook(args)
        ws = wb.active
        # 시트 이름 구하기
        # sheetname = wb.get_sheet_names()
        # sheet = wb[sheetname[0]]
        # 전체 행과 열
        col_max = ws.max_column
        row_max = ws.i
        # 입력해야 될 열
        num = col_max+1
        col = get_column_letter(col_max+1)
        cols = get_column_letter(col_max+1)
        # 아이템명과 비고 구하기
        for x, name in enumerate(ws[1]):
            if name.value == excel[n][0]:
                # item = column_index_from_string(val)
                item = get_column_letter(x+1)
            if name.value == excel[n][1]:
                ref = get_column_letter(x+1)
            if name.value == '품명2':
                num = col_max
                col = get_column_letter(col_max)
        # 품명 입력
        ws[str(col) + str(1)] = '품명2'
        ws[str(cols) + str(1)] = '품명'
        # 함수 입력 반복
        for row in range(2, row_max+1):
            func = f"={item}{str(row)}&IF(ISBLANK({ref}{str(row)}), \"\",\"*****\")&{ref}{str(row)}"
            ran = str(col)+str(row)
            ws[ran] = func
        # 저장
        wb.save(args)
        # 종료
        wb.close()
        # 재저장
        try:
            # 엑셀 인스턴스 생성
            app = xw.App(visible=False)
            # 파일 불러오기
            wbxl = app.books.open(args)
            sheet = wbxl.sheets[0]
            # 함수 입력 반복
            for row in range(2, row_max + 1):
                ran = str(col) + str(row)
                ran2 = str(cols) + str(row)
                val = sheet.range(ran).options().value
                # 품명2 에서 품명으로 데이터만 옮기기
                sheet.range(ran2).options(transpose=False).value = val
            # 닫기
            wbxl.save(args)
            wbxl.close()
            app.kill()
        except:
            # 닫기
            wbxl.save(args)
            wbxl.close()
            app.kill()
    else:
        print('아이템명과 품명 합칠 필요가 없습니다.')


# ==================
def main(*args):
    try:
        input_excel(*args)
        excel_pandas(*args)
        print('0 ')
    except:
        print('Except')
        pass


###############################
if __name__ == '__main__':
    # epath = "C:\ARGOS RPA\senario1\POS\excel\excel file name"
    # 1.1 POS "경로", "input", "pos"
    # 1.2 SHIPSERV "경로", "no", "shipserv"
    # 1.3 SK "경로", "", "sk"
    # 1.4 ANGLO "경로", "", "anglo"
    # 1.5 FLEET "경로", "", "fleet"
    # 1.6 REQUEST "경로", "", "request"
    # 1.7 HMM "경로", "", "hmm"
    # test: r"C:\work\format_check\korea\pos_S-SPRH-RFQ2022090026.xlsx", 'input', "pos"
    main()