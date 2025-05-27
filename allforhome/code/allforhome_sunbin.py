"""
====================================
 :mod:`작업내역서 권역별 분류`
====================================
.. moduleauthor:: Jeong Sunbin <jsnb6n0@argos-labs.com>
.. note:: ARGOS-LABS License

Description
===========
Module for AllForHome(올포홈)
작업내역서 권역별 분류 및 a업무 자동화 시나리오
"""
################################################################################
# Authors
# ===========
#
# * Jeong Sunbin
#
# Change Log
# --------
#  * [2022/12/08]
#     - in_rpa_work에서 엑셀 취합하는 부분 수정
#     - 작업 완료된 폴더 이동하도록 추가
#
#  * [2022/12/05]
#     - starting
################################################################################
import os
import re
import time
import shutil
import datetime
import openpyxl
# from alabs.common.util.vvlogger import get_logger


################################################################################
# 단가코드(H열) 기준 마지막 행 구하기
def get_i(ws_w):
    cnt = 0
    max_r = 9
    for i in range(5, ws_w.i + 1):
        if (ws_w["H" + str(i + 1)].value is None) and (ws_w["H" + str(i + 2)].value is None) and (ws_w["H" + str(i + 3)].value is None) and (ws_w["H" + str(i + 4)].value is None) and (ws_w["H" + str(i + 5)].value is None) and (ws_w["H" + str(i + 6)].value is None) and (ws_w["H" + str(i + 7)].value is None):
            max_r = i + 1
            break
    return max_r


################################################################################
def in_rpa_work():
    dirs_path_list = []

    root_dir_path_r = r'C:\Users\vivans\Desktop\올포홈\allforhome\test\내역작업=완료'
    check_dir_path_r = root_dir_path_r + r'\(★완 료★)'

    root_dir_path_w = r'C:\Users\vivans\Desktop\올포홈\allforhome\test\기성작업'


    check_dir_list_r = os.listdir(check_dir_path_r) #(★완 료★)폴더내 파일리스트
    print(check_dir_list_r)
    for check_dir in check_dir_list_r:
        p = re.compile('K\d') #권역에서 숫자를 찾는다. ex) k3 / re.compile 를 하면 리스트로 담김
        print(p)
        area = p.findall(check_dir)[0].replace('K', '') #찾은 k+숫자들 중 list형식으로 가져오기 떄문에 숫자만 가져오기 위해 replace
        print(area)
        pp = re.compile('\(K\d\)\d{4}\.\d{2}.\d{2} ') #(K3)2020.12.20에서 숫자를 묶어서 가져옴 list에 담김
        print(pp)
        user_name = pp.split(check_dir)[-1]
        print(user_name)

        check_dir_path_b = check_dir_path_r + '\\' + check_dir
        print(check_dir_path_b)
        dirs_path_list.append(check_dir_path_b)
        print(dirs_path_list)
        for xlsx in os.listdir(check_dir_path_b):
            xlsx_path_r = check_dir_path_b + '\\' + xlsx
            if ("정산" in xlsx) and ("~$" not in xlsx):
                print(xlsx_path_r)

                wb_r = openpyxl.load_workbook(xlsx_path_r, data_only=True)
                ws_r = wb_r.active

                xlsx_path_wm = root_dir_path_w + f'/2020 LH 경북{area}/내역사진정리/내역/--'
                xlsx_path_w = xlsx_path_wm + '/합 1.0.xlsx'
                if os.path.exists(xlsx_path_w):
                    wb_w = openpyxl.load_workbook(xlsx_path_w)
                else:
                    wb_w = openpyxl.load_workbook('//agoodday/5.RPA 작업/〔99〕   rpa_setting/작업내역서 권역별 분류 및 a업무 자동화 시나리오/python/서식.xlsx')
                ws_w = wb_w.active

                max_r = get_i(ws_w)
                row_to_w = max_r + 1
                for r in ws_r.iter_rows(min_row=6, i=ws_r.i, min_col=8, max_col=16,
                                        values_only=True):
                    for i, cell in enumerate(r):
                        if cell is None:
                            cell = ''

                        ws_w.cell(row=row_to_w, column=8+i).value = cell
                    row_to_w += 1

                row_to_w = max_r
                for r in ws_r.iter_rows(min_row=6, i=ws_r.i, min_col=26, max_col=ws_r.max_column,
                                        values_only=True):
                    row = []
                    for i, cell in enumerate(r):
                        if cell is None:
                            cell = ''

                        ws_w.cell(row=row_to_w, column=26+i).value = cell
                    row_to_w += 1

                wb_w.save(xlsx_path_w)
                time.sleep(3)

                # 작업한 정산 엑셀 이동
                print(f"move {xlsx_path_r} to...{xlsx_path_wm}")
                shutil.move(xlsx_path_r, xlsx_path_wm)

            # p2.xlsx, p3.xlsx, conv.xlsx 는 삭재
            elif ("p2" in xlsx) or ("p3" in xlsx) or ("conv" in xlsx):
                print(f"remove {xlsx}")
                os.remove(xlsx_path_r)

            # //(권역)YYYY.mm.dd user_name/dir/*dirs/*.xlsx 이동 -> //기성작업/2020 LH 권역(n)/내역,사진정리/사진/*dirs/안으로 이동
            elif os.path.isdir(xlsx_path_r):
                print("dir")
                area_dir_path = xlsx_path_r  # source directory
                area_dir_list = os.listdir(area_dir_path)

                for dir in area_dir_list:
                    area_dir_path_b = area_dir_path + '/' + dir
                    area_dir_list_b = os.listdir(area_dir_path_b)
                    for xlsx_area in area_dir_list_b:
                        xlsx_path_area = area_dir_path_b + '/' + xlsx_area

                        if '.xlsx' in xlsx_path_area:
                            dir_path_target = root_dir_path_w + f'/2020 LH 경북{area}/내역사진정리/사진/{xlsx}'
                            # "//기성작업/2020 LH 경북4/내역사진정리/사진/4건설"폴더가 없으면 생성
                            if not os.path.exists(dir_path_target):
                                os.makedirs(dir_path_target)
                            #
                            if os.path.exists(dir_path_target + '/' + xlsx_area):
                                os.remove(dir_path_target + '/' + xlsx_area)

                            print(f"move {xlsx_path_area} to {dir_path_target}")
                            shutil.move(xlsx_path_area, dir_path_target)

    print("rpa work: End>>>>>")
    return dirs_path_list


def move_dir(dirs_list):
    root_dir_path_m = '//agoodday/5.RPA 작업/〔99〕   rpa_setting/작업내역서 권역별 분류 및 a업무 자동화 시나리오/test/사진대장백업'
    pp = re.compile('\(K\d\)\d{4}\.\d{2}.\d{2} ')

    for directory in dirs_list:
        user_name = pp.split(directory)[-1]
        dir_path_m = root_dir_path_m+'/'+user_name

        if not os.path.exists(dir_path_m):
            os.makedirs(dir_path_m)

        print(f"move {directory} to {dir_path_m}")
        shutil.move(directory, dir_path_m)


def main():
    dirs_list = in_rpa_work()
    move_dir(dirs_list)


if __name__ == "__main__":
    start_time = datetime.datetime.now()
    print(start_time)
    main()
    print(datetime.datetime.now() - start_time)
