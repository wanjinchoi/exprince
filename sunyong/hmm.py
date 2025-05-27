import pandas as pd
import openpyxl
import json


def spare(excel_path):
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    ws_t = wb.create_sheet('Sheet2')

    # Sheet2에 파일 column지정
    headers = ['NO', '코드', '품명', '수량', '단위']
    for col_num, header in enumerate(headers, start=1):
        ws_t.cell(row=1, column=col_num, value=header)

    # sheet 1의 내용 sheet2로 옮기기
    for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        # Transfer A, D, I, J columns to A, B, D, E in Sheet2
        ws_t.cell(row=row_idx, column=1, value=row[0].value)  # A -> A
        ws_t.cell(row=row_idx, column=2, value=row[2].value)  # C -> B
        ws_t.cell(row=row_idx, column=4, value=row[8].value)  # I -> D
        ws_t.cell(row=row_idx, column=5, value=row[9].value)  # J -> E

        # 품명에 들어갈 내용들 합치기
        f_value = row[5].value or ""
        g_value = row[6].value or ""
        s_value = row[18].value or ""
        # E로 시작하면 [ENG]
        if s_value.startswith('E'):
            if g_value is None or g_value == '':
                combined_value = f"[ENG] {f_value}"
            else:
                combined_value = f"[ENG] {f_value} ***** {g_value}"
        elif s_value.startswith('D'):
            if g_value is None or g_value == '':
                combined_value = f"[DECk] {f_value}"
            else:
                combined_value = f"[DECk] {f_value} ***** {g_value}"
        else:
            combined_value = f"{f_value} *** {g_value}"
        ws_t.cell(row=row_idx, column=3, value=combined_value)
    del wb['Sheet 1']
    wb.save(excel_path)


def excel(rfq_json, excel_path, kind):
    if kind == "STORE":
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active
        # 원본에서 옮기기
        ws_t = wb.create_sheet('Sheet2')
        ws['U1'] = 'etc'

        # Sheet2에 파일 column지정
        headers = ['NO', '코드', '품명', '수량', '단위']
        for col_num, header in enumerate(headers, start=1):
            ws_t.cell(row=1, column=col_num, value=header)

        # sheet 1의 내용 sheet2로 옮기기
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            # Transfer A, D, I, J columns to A, B, D, E in Sheet2
            ws_t.cell(row=row_idx, column=1, value=row[0].value)  # A -> A
            ws_t.cell(row=row_idx, column=2, value=row[3].value)  # D -> B
            ws_t.cell(row=row_idx, column=4, value=row[8].value)  # I -> D
            ws_t.cell(row=row_idx, column=5, value=row[9].value)  # J -> E

            # 품명에 들어갈 내용들 합치기
            f_value = row[5].value or ""
            g_value = row[6].value or ""
            s_value = row[18].value or ""
            #E로 시작하면 [ENG]
            if s_value.startswith('E'):
                if g_value is None or g_value == '':
                    combined_value = f"[ENG] {f_value}"
                else:
                    combined_value = f"[ENG] {f_value} ***** {g_value}"
            elif s_value.startswith('D'):
                if g_value is None or g_value == '':
                    combined_value = f"[DECk] {f_value}"
                else:
                    combined_value = f"[DECk] {f_value} ***** {g_value}"
            else:
                combined_value = f"{f_value} *** {g_value}"
            ws_t.cell(row=row_idx, column=3, value=combined_value)
        del wb['Sheet 1']
        wb.save(excel_path)
        #
        #
        #
        #
        #
        #
        #
        #
        # for r in ws.rows:
        #     row_index = r[0].row
        #     description = r[4].value
        #     specification = r[5].value
        #     dept = r[14].value
        #     remarks = str(r[15].value)
        #
        #     if row_index == 1:
        #         pass
        #     else:
        #         # description이 specification안에 없으면 합치고
        #         if description not in specification:
        #             r[5].value = description + specification
        #         # description이 빈칸이면 pass
        #         elif description == '':
        #             pass
        #         # specification이 빈칸이면
        #         elif specification == '':
        #             r[5].value = description
        #
        #         if dept == "D":
        #             r[14].value = "[Deck]"
        #         elif dept == "E":
        #             r[14].value = "[ENG]"
        #
        #         # 마지막에 Dept + Specification + ***** + VSL Remarks
        #         if remarks == '':
        #             r[20].value = str(r[14].value) + str(r[5].value)
        #         else:
        #             r[20].value = str(r[14].value) + str(r[5].value) + "*****" + remarks
        #
        # # NO, IMPA CODE, Qty, Unit
        # cols_to_delete = ['1', '2', '4', '5', '6', '8', '9', '12', '13', '14', '15', '16', '17', '18', '19', '20']
        # for e, col in enumerate(cols_to_delete):
        #     ws.delete_cols(int(col) - e)
        #
        # for i in range(ws.max_column+1):
        #     if i == 0:
        #         pass
        #     else:
        #         for j in range(ws.max_row+1):
        #             if j == 0:
        #                 pass
        #             else:
        #                 try:
        #                     ws_t.cell(row=j, column=i).value = ws.cell(row=j+1, column=i).value
        #                 except ValueError as err:
        #                     print(err)
        # del wb['Sheet 1']
        #
        # wb.save(excel_path)

    elif kind == "SPARE":
        spare(excel_path)


def delete_rfq(rfq_json, rfq_no):
    try:
        rfq_json["rfq"].remove(rfq_no)
    except ValueError:
        pass

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(rfq_json, f, ensure_ascii=False, indent=4)


def is_rfq(rfq_json, rfq_no):
    if rfq_no in rfq_json["rfq"]:
        return True
    else:
        return False


def rfq_append(rfq_json, rfq_no):
    if rfq_no in rfq_json["rfq"]:
        return True
    else:
        rfq_json["rfq"].append(rfq_no)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(rfq_json, f, ensure_ascii=False, indent=4)
        return False


def main(func, *args, **kwargs):
    global json_path
    # json_path = r'C:\Users\vivans\PycharmProjects\ts-python\komasco\file\H'
    json_path = r'C:\ARGOS RPA\senario1\HMM\result\HMM_RFQ관리_계정딴거.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        rfq_json = json.load(f)

    return globals()[func](rfq_json, *args, **kwargs)


if __name__ == "__main__":
    print(main('excel',r'C:\ARGOS RPA\senario1\HMM\excel\HMM_6000545062_SPARE.xlsx','SPARE'))
