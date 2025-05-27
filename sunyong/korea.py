"""
 :ver`1.3` :date`2022.09.27`
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
#  * [2022/11/01]
#     - shipserv input_excel 해주는 것으로 변경
#     - SK 진행 시, IT와 IP를 분리
#  * [2023/01/30]
#     - def get_logger 추가
#     - main 함수 내 함수에 변수 추가 (logger=logger)
#     - 관련 함수에 매개 변수 추가 (logger=None)

#####################################################
import openpyxl as op
import pandas as pd
import xlwings as xw
from openpyxl.utils import get_column_letter
import warnings
import os
import datetime
import pathlib
import logging
import logging.handlers
#####################################################
# 로그 설정
# txt_path = r"C:\ARGOS RPA\code\log.txt"
log_path = r"C:\ARGOS RPA\code\log.txt"
one_data = '\n\n================================='

def get_logger(logfile,
               logsize=500*1024, logbackup_count=4,
               logger=None, loglevel=logging.DEBUG):
    loglevel = loglevel
    pathlib.Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    if logger is None:
        logger = logging.getLogger(os.path.basename(logfile))
    logger.setLevel(loglevel)
    if logger.handlers is not None and len(logger.handlers) >= 0:
        for handler in logger.handlers:
            logger.removeHandler(handler)
        logger.handlers = []
    loghandler = logging.handlers.RotatingFileHandler(
        logfile,
        maxBytes=logsize, backupCount=logbackup_count,
        encoding='utf8')
    # else:
    #     loghandler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s-%(name)s-%(levelname)s-'
        '%(filename)s:%(lineno)s-[%(process)d] %(message)s')
    loghandler.setFormatter(formatter)
    logger.addHandler(loghandler)
    return logger


# ==================
# 열 이름을 통해서 필요없는 열 삭제 (pandas)
def excel_pandas(args, check, sina, logger=None):
    # 로그
    txt_data = f"excel_pandas START"
    # make_log(txt_path, txt_data)
    logger.info(txt_data)
    # 설정
    # name = ['pos', 'shipserv', 'sk1', 'sk2', 'jibe', 'fleet', 'request', 'hmm']
    name = {
        'pos': ['No', '파트번호', '단위', '수량', '품명'],
        'shipserv': ['Line', 'Part No', 'Qty', 'Unit', '품명'],
        'sk1': ['No', 'IMPA', 'Description & Spec', 'Unit', 'Qty'],
        'sk2': ['No', 'Part No', 'Unit', 'Qty', '품명'],
        'jibe': ['S. No.', 'Part No.', 'Items', 'Unit', 'Rsqt Qty'],
        'fleet': ['No.', 'Items', 'Qty.', 'Unit', '아이템 번호'], # Price 포함이면 Unit과 아이템 번호 사이에 넣기
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
        df = pd.read_excel(args, engine="openpyxl", sheet_name=0,converters={'Part No': str})
    # 열 이름 구하기
    for col in df.columns:
        cols.append(col)
    # 필요한 열 제외
    del_col = set(cols) - set(name[n])
    # 필요 없는 열 삭제
    df.drop(del_col, axis=1, inplace=True)
    # 저장
    df.to_excel(args, index=False)
    # 로그
    txt_data = f"excel_pandas DONE\nEND"
    # make_log(txt_path, txt_data)
    logger.info(txt_data)


# ==================
# 아이템명과 비고 합친 품명 작성하기 (openpyxl)
def input_excel(args, check, sina, logger=None):
    # 3) input 사용 시, excel_pandas의 name도 합치는 상단 이름 모두 빼고 품명으로 만들어줘야됨 !!
    if 'input' in check:
        # 로그
        txt_data = f"input_excel START"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)
        # 아이템명과 비고 구하기
        excel = {
            'pos': ['아이템명', '비고'],
            'shipserv': ['Item Description', 'Buyer Comments'],
            'sk1': ['no', 'no'],
            'sk2': ['Description', 'Vessel Remark'],
            'jibe': ['S. No.', 'Part No.', 'Items', 'Unit', 'Rsqt Qty'],
            'fleet': ['Items', 'no'],
            'request': [],
            'hmm': []
        }
        # 필요한 리스트 이름 찾기
        for x, n in enumerate(excel):
            if n == sina:
                break
        # 엑셀 읽기
        wb = op.load_workbook(args)
        ws = wb.active
        # 시트 이름 구하기
        # sheetname = wb.get_sheet_names()
        # sheet = wb[sheetname[0]]
        # 전체 행과 열
        col_max = ws.max_column
        row_max = ws.max_row
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
            if ws[str(ref)+str(row)].value == 'No comment' or ws[str(ref)+str(row)].value == '[]':
                func = f"={item}{str(row)}"
            else:
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
            # 로그
            txt_data = f"input_excel DONE"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)
        except Exception as e:
            # 닫기
            wbxl.save(args)
            wbxl.close()
            app.kill()
            # 로그
            txt_data = f"input_excel ERROR: {e}"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)
    else:
        # 로그
        txt_data = f"input_excel NONE"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)


# ==================
# 합치기 전에 엑셀 설정하기 (openpyxl)
def check_excel(args, check, sina, logger=None):
    try:
        # 로그
        txt_data = f"{args}, {check}, {sina}\ncheck_excel START"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)
        # 1) SK 첫 번째에 No 적기
        if 'A1' in check:
            # 로그
            txt_data = f"check_excel A1 START"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)
            # 엑셀 읽기
            wb = op.load_workbook(args)
            ws = wb.active
            # 입력
            ws['A1'] = 'No'
            # 전체 행
            row_max = ws.max_row
            ws.delete_rows(row_max)
            # 저장
            wb.save(args)
            # 종료
            wb.close()
            txt_data = f"check_excel A1 DONE"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)
        else:
            # 로그
            txt_data = f"check_excel: 아이템명과 품명 합칠 필요가 없습니다."
            # make_log(txt_path, txt_data)
            logger.info(txt_data)

        # 2) sk2 (ip)는 first_add 3개를 합쳐서 첫 번째 품명에 넣어야 됨
        if 'sk2' in sina:
            txt_data = f"check_excel sk2 START"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)
            # 파일 이름 구하기
            name = os.path.basename(args)
            sk2name = "sk2_" + name

            # 경로
            path = rf'C:\ARGOS RPA\senario1\SK\excel\{sk2name}.xlsx'
            # path = rf'C:\work\format_check\korea\sk\{sk2name}.xlsx'

            # 새로운 sk2 엑셀 설정
            new_wb = op.Workbook()
            new_ws = new_wb.active
            new_ws.title = 'sk2'
            # 읽어야 되는 상단 이름 열?
            first_add = ['Euipment', 'Maker', 'Type']
            # 원본 엑셀 읽기
            wb = op.load_workbook(args)
            ws = wb.active

            # 전체 행과 열
            col_max = ws.max_column
            row_max = ws.max_row

            # 해당 위치 구하기
            for x, name in enumerate(ws[1]):
                if name.value == first_add[0]:
                    # item = column_index_from_string(val)
                    euipment = get_column_letter(x + 1)
                if name.value == first_add[1]:
                    maker = get_column_letter(x + 1)
                if name.value == first_add[2]:
                    type = get_column_letter(x + 1)

            # 함수 입력 반복 - 데이터 모두 하나로 합치기
            data = []
            for row in range(2, row_max + 1):
                d1 = ws[str(euipment) + str(row)].value
                d2 = ws[str(maker) + str(row)].value
                d3 = ws[str(type) + str(row)].value
                dall = str(d1) + ' / ' + str(d2) + ' / ' + str(d3)
                data.append(dall)

            # 중복 데이터 제거
            setdata = list(set(data))

            # 사이에 엔터 넣고 하나로 합치기
            notlst = "\n".join(setdata)

            # 새로운 엑셀 파일에 데이터 적기
            new_ws['A1'] = 'opt'
            new_ws['A2'] = '-'
            new_ws['B1'] = '품명'
            new_ws['B2'] = str(notlst)

            # 저장
            new_wb.save(path)

            # 로그
            txt_data = f"check_excel sk2 DONE"
            # make_log(txt_path, txt_data)
            logger.info(txt_data)

            # 종료
            wb.close()
            new_wb.close()

        # 로그
        txt_data = f"check_excel DONE"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)
    except Exception as e:
        # 로그
        txt_data = f"check_excel ERROR: {e}"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)


# =======================================================
# python 진행 로그 만들기
# def make_log(txt_path, txt_data):
#     try:
#         if os.path.exists(txt_path):
#             mode = 'a'
#         else:
#             mode = 'w'
#         f = open(f"{txt_path}", f"{mode}")
#         f.write(txt_data)
#         f.write("\n")
#         f.close()
#     except Exception as e:
#         print(f"make_log: {e}")



# ==================
def main(*args):
    try:
        # make_log(txt_path, one_data)
        logger = get_logger(log_path, logsize=1024 * 1024 * 10)
        check_excel(*args, logger=logger)
        input_excel(*args, logger=logger)
        excel_pandas(*args, logger=logger)
        print('0')
    except Exception as e:
        print('Except')
        txt_data = f"main ERROR {e}"
        # make_log(txt_path, txt_data)
        logger.info(txt_data)


###############################
if __name__ == '__main__':
    # epath = "C:\ARGOS RPA\senario1\POS\excel\excel file name"
    # 1.1 POS "경로", "input", "pos"
    # 1.2 SHIPSERV "경로", "input", "shipserv"
    # 1.3 SK "경로", "A1no", "sk1"
    # 1.3 SK "경로", "A1input", "sk2"
    # 1.4 ANGLO "경로", "", "anglo"
    # 1.5 FLEET "경로", "", "fleet"
    # 1.6 REQUEST "경로", "", "request"
    # 1.7 HMM "경로", "", "hmm"
    # test: r"C:\work\format_check\korea\pos_S-SPRH-RFQ2022090026.xlsx", 'input', "pos"
    # test: r"C:\Users\vivans\Downloads\김민정S\한국선용품\오류\엑셀 전\KMS-1-221101AE1108_testㅇ.xlsx", "input", "shipserv"
    main(r'C:\work\sunyong\New QOT 9910-24-358.xlsx','input','shipserv')