from openpyxl import load_workbook, Workbook
from openpyxl.styles import Alignment, Font
import requests
import math
import time
import yaml
import csv
import re
import datetime


CUST_SAMPLE = {
    "자사홈페이지-네이버페이(센터)": "00830",
    "자사홈페이지-네이버페이(PG)": "00669",
    "자사홈페이지-네이버페이(PG-무통장)": "01008",
    "현금영수증": "00014",
    "미발행": "00013",
}

LOGIN_INFO = {
    "COM_CODE": "21008",
    "USER_ID": "softpack25",
    "API_CERT_KEY": "1743927c9627f4c1995791adf158b1fae1",
    "LAN_TYPE": "ko-KR",
    "ZONE": "CC"
}

URL_INFO = {
    "upload": "https://oapiCC.ecount.com/OAPI/V2/Sale/SaveSale?SESSION_ID={SESSION_ID}"
}


# 프로젝트 코드에 입력될 코드를 계산하기 위한 Datetime 형 변수
AM000000 = datetime.datetime.strptime('00:00:00', "%H:%M:%S").time()
AM082959 = datetime.datetime.strptime('08:29:59', "%H:%M:%S").time()
AM083000 = datetime.datetime.strptime('08:30:00', "%H:%M:%S").time()
PM122959 = datetime.datetime.strptime('12:29:59', "%H:%M:%S").time()
PM123000 = datetime.datetime.strptime('12:30:00', "%H:%M:%S").time()
PM022959 = datetime.datetime.strptime('14:29:59', "%H:%M:%S").time()
PM023000 = datetime.datetime.strptime('14:30:00', "%H:%M:%S").time()
PM235959 = datetime.datetime.strptime('23:59:59', "%H:%M:%S").time()


# 메이크샵에서 내려받은 .csv 파일을 xlsx 파일로 재가공
def csv2xlsx(input_path):
    wb = Workbook()
    ws = wb.active
    with open(input_path, 'r') as f:
        for row in csv.reader(f):
            ws.append(row)
    wb.save(input_path.replace(".csv", ".xlsx"))
    return input_path.replace(".csv", ".xlsx")


def add_invoice_num(input_path):
    new_wb = Workbook()
    new_ws = new_wb.active
    wb = load_workbook(input_path)
    ws = wb['Sheet']
    add_count = 2
    add_invoice_list = []
    for i in range(len(ws['C']) - 1):
        price = ws['K' + str(i + 2)].value
        if math.floor(int(price) / 120000) > 0:
            if ws['B' + str(i + 2)].value not in add_invoice_list:
                new_ws['A' + str(add_count)].value = ws['N' + str(i + 2)].value
                new_ws['B' + str(add_count)].value = ws['R' + str(i + 2)].value
                new_ws['C' + str(add_count)].value = ws['P' + str(i + 2)].value
                new_ws['D' + str(add_count)].value = ws['O' + str(i + 2)].value
                new_ws['H' + str(add_count)].value = math.floor(
                    int(price) / 120000)
                add_invoice_list.append(ws['B' + str(i + 2)].value)
                add_count += 1
    new_wb.save(
        r"C:\Users\다현짱\Downloads\결과물\추가박스_" + time.strftime(
            "%H") + "시.xlsx")
    return r"C:\Users\다현짱\Downloads\결과물\추가박스_" + time.strftime(
        "%H") + "시.xlsx"


def read_yml():
    with open(
            r'C:\ARGOSRPA\code\session.yml') as f:
        load = yaml.load(f, Loader=yaml.FullLoader)
        return load['key']


def write_yml(session):
    with open(
            r'C:\ARGOSRPA\code\session.yml',
            'w') as f:
        yaml.dump(session, f)


# 할인 종류에 따라 다른 코드를 반환
def sale_policy(sale_type):
    sale_code = []
    if "네이버" in sale_type or "앱 구매혜택" in sale_type:
        sale_code.append("D-2")
        sale_code.append("앱할인")
    elif "SILVER" in sale_type or "우수" in sale_type or "GOLD" in sale_type:
        sale_code.append("D-3")
        sale_code.append("우수회원 할인")
    elif "VIP" in sale_type:
        sale_code.append("D-4")
        sale_code.append("VIP 할인")
    return sale_code


# 추가박스 .xlsx 파일의 너비, 정렬등 파일 스타일링
def styling_xlsx(input_path):
    wb = load_workbook(input_path)
    ws = wb['Sheet']
    header = ['받는분 성명', '받는분 주소', '받는분 전화번호', '받는분 기타연락처', '품목명', '운임구분',
              '기본운임', '박스수량', '배송 메시지']
    width_list = [13, 66, 15, 18, 10, 10, 10, 10, 12]
    for i in range(9):
        ws[chr(65 + i) + str(1)].value = header[i]
        ws[chr(65 + i) + str(1)].alignment = Alignment(horizontal='center',
                                                       vertical='center')
        ws[chr(65 + i) + str(1)].font = Font(bold=True)
        wb['Sheet'].column_dimensions[chr(65 + i)].width = width_list[i]
    wb.save(input_path)


def extract_company_code(code):
    wb = load_workbook(r"C:\ARGOSRPA\mapping\company_code.xlsx")
    ws = wb['Sheet1']
    for i in range(len(ws['A'])):
        if ws['A'+str(i+2)].value == code:
            return True
    return False


# 입금완료 시간에 따른 프로젝트 코드 반환
def return_PJT_CD(input_value):
    value = datetime.datetime.strptime(input_value.split(" ")[1], "%X").time()
    if AM000000 <= value <= AM082959:
        return "00012"
    elif AM083000 <= value <= PM122959:
        return "00013"
    elif PM123000 <= value <= PM022959:
        return "00014"
    elif PM023000 <= value <= PM235959:
        return "00019"


# API 호출하여 session_id 발급, 현재 Zone 값 'CC'
# Zone값 오류 발생 시 주석처리된 부분 주석 해제 후 실행
def api_login():
    get_zone = requests.post("https://oapi.ecount.com/OAPI/V2/Zone",
                             json={"COM_CODE": "21008"})
    zone = get_zone.json()['Data']['ZONE']
    login_url = "https://oapiCC.ecount.com/OAPI/V2/OAPILogin"
    get_session = requests.post(login_url, json=LOGIN_INFO)
    print("API 세션 요청 상태코드 : " + str(get_session))
    session = get_session.json()['Data']['Datas']['SESSION_ID']
    return session


def replace_price(price):
    p = re.compile(":\\s(.*)")
    return p.findall(price)[0].replace(",", "").replace("원", "").replace("-", "")


# API호출에 사용될 json 생성
# 변수명에 대한 설명은 https://sboapi.ecount.com/ECERP/OAPI/OAPIView?lan_type=ko-KR# 참조
def make_json(input_path, mapping_file, mapping_file2):
    newWorkbook = Workbook()
    ws = newWorkbook.create_sheet("발주서 목록")
    balju_wb = load_workbook(mapping_file2)
    balju_ws = balju_wb['Sheet1']
    mapping_wb = load_workbook(mapping_file)
    mapping_ws = mapping_wb['Sheet1']
    wb = load_workbook(input_path)
    ws = wb['Sheet']
    rows = len(ws['B'])
    prev_num = ""
    item_name = ""
    item_code = ""
    PJT_CD = ""
    item_QTY = 0
    code_count = 0
    api_arr = []
    find_codes = []
    count = 0
    CUST = 0
    U_TXT1 = ""
    U_MEMO3 = ""
    IO_DATE = '20220120'
    status_delivery_sale = 0
    sale_flag = 0
    for i in range(rows - 1):
        if prev_num != ws['B' + str(i + 2)].value:
            status_delivery_sale = 0
            sale_flag = 0
            code_count += 1
        item_name = ws['E' + str(i + 2)].value
        address = ws['R' + str(i + 2)].value
        name_and_phone = ws['L' + str(i+2)].value + "/" + ws['P'+ str(i+2)].value
        try:
            split = ws['G' + str(i + 2)].value.split(",")
        except AttributeError:
            split = [ws['G' + str(i + 2)].value]
        U_TXT1 = ws['N' + str(i + 2)].value
        try:
            U_MEMO3 = ""
            U_MEMO3_tmp = list(ws['AF' + str(i + 2)].value)
            U_MEMO3_tmp.insert(4, "*")
            U_MEMO3_tmp.insert(9, "*")
            U_MEMO3 = "CJ " + ''.join(U_MEMO3_tmp)
        except TypeError:
            pass
        if "드립백박스" in ws['D' + str(i + 2)].value:
            item_QTY = int(ws['H' + str(i + 2)].value) * 10
        else:
            item_QTY = int(ws['H' + str(i + 2)].value) * 100
        if ws['AD' + str(i + 2)].value == "요청":
            try:
                CUST_tmp = ws['AB' + str(i + 2)].value.replace("-", "")
                if extract_company_code(CUST_tmp):
                    CUST = CUST_tmp
                else:
                    CUST = ""
            except AttributeError:
                # 수정 필요
                CUST = ""
        elif "무통장입금-네이버페이결제" in ws['AA' + str(i + 2)].value:
            CUST = "01008"
        elif "카드결제(PG결제)-네이버페이결제" in ws['AA' + str(i + 2)].value or "충전포인트 결제-네이버페이결제" in ws['AA' + str(i + 2)].value:
            CUST = "00669"
        elif "카드결제(네이버결제)-네이버페이결제" in ws['AA' + str(i + 2)].value:
            CUST = "00830"
        elif "폰" in ws['I' + str(i + 2)].value:
            CUST = "00094"
        elif "카카오" in ws['I' + str(i + 2)].value:
            CUST = "00500"
        elif ws['I' + str(i + 2)].value == "카드" or \
                ws['I' + str(i + 2)].value == "카드+적립금":
            CUST = "00001"
        elif ws['AD' + str(i + 2)].value == "미요청" and (ws['AC' + str(i + 2)].value is None or ws['AC' + str(i + 2)].value == "미발행"):
            CUST = "00013"
        elif ws['AD' + str(i + 2)].value == "미요청" and ws['AC' + str(i + 2)].value == "발급완료":
            CUST = "00014"
        else:
            CUST = ""
        PJT_CD = return_PJT_CD(ws['AG' + str(i + 2)].value)
        for j in range(len(split)):
            for k in range(len(mapping_ws['A'])):
                if item_name == mapping_ws['A' + str(k + 1)].value and split[j] == mapping_ws['B' + str(k+1)].value:
                    temp_code = mapping_ws['C' + str(k + 1)].value
                    for l in range(len(balju_ws['A'])):
                        if temp_code == balju_ws['A'+str(l+2)].value:
                            if balju_ws['C'+str(l+2)].value == 1018645056:
                                try:
                                    write_wb = load_workbook(
                                        r"C:\Users\다현짱\Downloads\결과물\발주서목록-이메일.xlsx")
                                except FileNotFoundError:
                                    write_wb = Workbook()
                                    write_ws = write_wb.active
                                    write_ws['A1'].value = "코드"
                                    write_ws['B1'].value = "납품처"
                                    write_ws['C1'].value = "납품처주소"
                                    write_ws['D1'].value = "상품명"
                                    write_ws['E1'].value = "업체코드"
                                    write_ws['F1'].value = "주문번호"
                                    write_ws['G1'].value = "수량"
                                    write_ws['H1'].value = "유선번호"
                            else:
                                try:
                                    write_wb = load_workbook(
                                        r"C:\Users\다현짱\Downloads\결과물\발주서목록-이카운트.xlsx")
                                except FileNotFoundError:
                                    write_wb = Workbook()
                                    write_ws = write_wb.active
                                    write_ws['A1'].value = "코드"
                                    write_ws['B1'].value = "납품처"
                                    write_ws['C1'].value = "납품처주소"
                                    write_ws['D1'].value = "상품명"
                                    write_ws['E1'].value = "업체코드"
                                    write_ws['F1'].value = "주문번호"
                                    write_ws['G1'].value = "수량"
                            write_ws = write_wb.active
                            last_row = write_ws.i
                            write_ws['A'+str(last_row+1)].value = temp_code
                            write_ws['B'+str(last_row+1)].value = name_and_phone
                            write_ws['C' + str(last_row + 1)].value = address
                            write_ws['D' + str(last_row + 1)].value = balju_ws['B'+str(l+2)].value
                            write_ws['E' + str(last_row + 1)].value = balju_ws['C'+str(l+2)].value
                            write_ws['F' + str(last_row + 1)].value = ws['B' + str(i + 2)].value
                            write_ws['G' + str(last_row + 1)].value = ws['H' + str(i + 2)].value
                            write_ws['H' + str(last_row + 1)].value = ws['O' + str(i + 2)].value
                            if balju_ws['C'+str(l+2)].value == 1018645056:
                                write_wb.save(r"C:\Users\다현짱\Downloads\결과물\발주서목록-이메일.xlsx")
                            else:
                                write_wb.save(
                                    r"C:\Users\다현짱\Downloads\결과물\발주서목록-이카운트.xlsx")
                if item_name == mapping_ws['A' + str(k + 1)].value and \
                        split[j] == mapping_ws['B' + str(k + 1)].value:
                    PROD_CD = mapping_ws['C' + str(k + 1)].value
                    PROD_DES = mapping_ws['E' + str(k + 1)].value
                    UPLOAD_SER_NO = code_count
                    EMP_CD = "test01"
                    WH_CD = "10"
                    find_codes.append(PROD_CD)
                    obj = {
                        "Line": "0",
                        "BulkDatas": {
                            "IO_DATE": IO_DATE,
                            "UPLOAD_SER_NO": UPLOAD_SER_NO,
                            "CUST": CUST,
                            "CUST_DES": "",
                            "EMP_CD": EMP_CD,
                            "WH_CD": WH_CD,
                            "IO_TYPE": "",
                            "EXCHANGE_TYPE": "",
                            "EXCHANGE_RATE": "",
                            "PJT_CD": PJT_CD,
                            "DOC_NO": "",
                            "PROD_CD": PROD_CD,
                            "PROD_DES": PROD_DES,
                            "SIZE_DES": "",
                            "UQTY": "",
                            "QTY": item_QTY,
                            "PRICE": "",
                            "USER_PRICE_VAT": "",
                            "SUPPLY_AMT": "",
                            "SUPPLY_AMT_F": "",
                            "VAT_AMT": "",
                            "U_TXT1": U_TXT1,
                            "U_MEMO3": U_MEMO3,
                            "REMARKS": "",
                            "ITEM_CD": "",
                            "REL_DATE": "",
                            "REL_NO": "",
                            "MAKE_FLAG": "",
                            "CUST_AMT": ""
                        }
                    }
                    api_arr.append(obj)
        if int(ws['Z' + str(i + 2)].value) > 0:  # 배송비 입력
            if status_delivery_sale == 1 or status_delivery_sale == 0:
                obj = {
                    "Line": "0",
                    "BulkDatas": {
                        "IO_DATE": IO_DATE,
                        "UPLOAD_SER_NO": code_count,
                        "CUST": CUST,
                        "CUST_DES": "",
                        "EMP_CD": 'test01',
                        "WH_CD": '10',
                        "PROD_CD": '4',
                        "PROD_DES": '배송비',
                        "QTY": '1',
                        "PRICE": round(int(ws['Z' + str(i + 2)].value) / 1.1),
                        "SUPPLY_AMT": round(int(ws['Z' + str(i + 2)].value) / 1.1),
                        "VAT_AMT": round(int(ws['Z' + str(i + 2)].value) - round(
                            int(ws['Z' + str(i + 2)].value) / 1.1)),
                        "U_MEMO3": U_MEMO3,
                    }
                }
                status_delivery_sale += 2
                api_arr.append(obj)
        if int(ws['AH' + str(i + 2)].value) > 0:  # 적립금이 있을 경우
            if status_delivery_sale == 2 or status_delivery_sale == 0:
                obj = {
                    "Line": "0",
                    "BulkDatas": {
                        "IO_DATE": IO_DATE,
                        "UPLOAD_SER_NO": code_count,
                        "CUST": CUST,
                        "CUST_DES": "",
                        "EMP_CD": 'test01',
                        "WH_CD": '10',
                        "PROD_CD": 'D-1',
                        "PROD_DES": '적립금',
                        "QTY": '-1',
                        "PRICE": int(ws['AH' + str(i + 2)].value),
                        "SUPPLY_AMT": -int(ws['AH' + str(i + 2)].value),
                        "VAT_AMT": round(-int(ws['AH' + str(i + 2)].value)*0.1),
                        "U_MEMO3": U_MEMO3,
                    }
                }
                status_delivery_sale += 1
                api_arr.append(obj)

        if ws['Y' + str(i + 2)].value is not None:
            print(ws['Y' + str(i + 2)].value)
            if sale_flag == 0:
                sale_split = ws['Y' + str(i + 2)].value.split("원,")
                for k in sale_split:
                    price = replace_price(k)
                    tmp = sale_policy(k)
                    print(tmp)
                    obj = {
                        "Line": "0",
                        "BulkDatas": {
                            "IO_DATE": IO_DATE,
                            "UPLOAD_SER_NO": code_count,
                            "CUST": CUST,
                            "CUST_DES": "",
                            "EMP_CD": 'test01',
                            "WH_CD": '10',
                            "PROD_CD": tmp[0],
                            "PROD_DES": tmp[1],
                            "QTY": '-1',
                            "PRICE": int(price),
                            "SUPPLY_AMT": -int(price),
                            "VAT_AMT": round(-int(price)*0.1),
                            "U_MEMO3": U_MEMO3,
                        }
                    }
                    api_arr.append(obj)
                sale_flag = 1
        prev_num = ws['B' + str(i + 2)].value
    uload_json = {
        "SaleList": api_arr
    }
    wb.save(input_path)
    mapping_wb.close()
    return find_codes, uload_json


# 판매입력을 하는 API 호출
def upload(session_id, json):
    URL = URL_INFO['upload'].format(SESSION_ID=session_id)
    result = requests.post(URL, json=json)
    return result.json()


# 판매입력할 상품들의 단가를 조회하기 위하여 API 호출
# 08/23 박명국 -> 기존 API 호출하여 상품 조회하던 것을 이카운트에 등록된 엑셀파일을 읽는 것으로 변경
def find(input_list):
    code_wb = load_workbook(r"C:\ARGOSRPA\mapping\item_code.xlsx")
    code_ws = code_wb['품목등록']
    my_set = set(input_list)
    input_list = list(my_set)
    result = []
    for i in input_list:
        for j in range(len(code_ws['A'])):
            if i == code_ws['A' + str(j + 2)].value:
                item = {
                    "code": i,
                    "price": code_ws['E' + str(j + 2)].value
                }
                result.append(item)
                break
    return result


def json2excel(json):
    wb = Workbook()
    ws = wb.active
    ws['A1'].value = "거래처코드"
    ws['B1'].value = "담당자명"
    ws['C1'].value = "상품코드"
    ws['D1'].value = "상품명"
    ws['E1'].value = "수량"
    ws['F1'].value = "인수자"
    ws['G1'].value = "프로젝트코드"
    ws['H1'].value = "단가"
    ws['I1'].value = "공급가액"
    ws['J1'].value = "부가세"
    ws['K1'].value = "송장번호"
    sample = json
    all_length = len(sample['SaleList'])
    for i in range(all_length):
        ws['A' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['CUST']
        ws['B' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['EMP_CD']
        ws['C' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['PROD_CD']
        ws['D' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['PROD_DES']
        ws['E' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['QTY']
        try:
            ws['F' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['U_TXT1']
        except KeyError:
            pass
        try:
            ws['G' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['PJT_CD']
        except KeyError:
            pass
        ws['H' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas'][
            'PRICE']
        ws['I' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas'][
            'SUPPLY_AMT']
        ws['J' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas'][
            'VAT_AMT']
        ws['K' + str(i + 2)].value = sample['SaleList'][i]['BulkDatas']['U_MEMO3']

    wb.save(r"C:\Users\다현짱\Downloads\결과물\json2excel.xlsx")


# 조회한 단가, 공급가, 부가세를 판매 입력할 json에 입력
def change_OUTPRICE(original_json, price_list):
    for i in range(len(original_json['SaleList'])):
        json_tmp = original_json['SaleList'][i]['BulkDatas']
        for j in range(len(price_list)):
            if json_tmp['PROD_DES'] == '배송비':
                continue
            if json_tmp['PROD_CD'] == price_list[j]['code']:
                json_tmp['PRICE'] = price_list[j]['price']
                json_tmp['SUPPLY_AMT'] = int(float(json_tmp['QTY'])) * int(float(json_tmp['PRICE']))
                json_tmp['VAT_AMT'] = int(float(json_tmp['SUPPLY_AMT'])) / 10
                break
    return original_json


def compare_(order_count, order_price, json):
    price = 0
    for i in range(len(json['SaleList'])):
        price += float(json['SaleList'][i]['BulkDatas']['SUPPLY_AMT'])
        price += float(json['SaleList'][i]['BulkDatas']['VAT_AMT'])
    total_price = round(price)
    total_count = len(json['SaleList'])
    print("총합 금액 : " + str(total_price), "총합 개수 : " + str(total_count))
    if order_count == total_count and order_price == total_price:
        return True
    else:
        return False


# csv2xlsx : 메이크샵에서 받은 .csv 파일을 .xlsx 확장자 변경
# make_json : .xlsx 파일과 mapping.xlsx 파일을 참조하여 판매 입력할 Json 생성
# api_login : api 호출에 사용할 session_id 획득
# find : upload 할 때 사용될 제품 단가 획득 (V2: 판매목록 엑셀 다운로드 후 값 대입)
# change_OUTPRICE : find 에서 획득한 값을 Json에 적용
# upload : 판매 입력 API를 통해 Json Data 전송
# compare_ : 메이크샵의 총 주문액, 주문건수와 비교, 틀릴 시 Exception
# add_invoice_num : 주문금액 120,000원을 초과할 시 추가 송장 요청 엑셀을 생성
def main(input_csv, order_count, order_price):
    start = time.time()
    mapping_file = r"C:\ARGOSRPA\mapping\mapping.xlsx"
    mapping_file2 = r"C:\ARGOSRPA\mapping\mapping2.xlsx"
    xlsx = csv2xlsx(input_csv)
    # jsons = make_json(xlsx, mapping_file, mapping_file2)
    # print("time :", time.time() - start)
    # styling_xlsx(add_invoice_num(xlsx))
    # session = read_yml()
    # product_list = find(jsons[0])
    # upload_json = change_OUTPRICE(jsons[1], product_list)
    # print(upload_json)
    # json2excel(upload_json)
    # # if not compare_(order_count, order_price, upload_json):
    # #     raise Exception
    # upload_status = upload(session, upload_json)
    # print(upload_status)
    # if upload_status['Status'] == '500':  # API 상태코드가 500일 경우 세션 재발급
    #     print("Session Key reissuance")
    #     session = api_login()  # 다시 Session Id 요청 후 session.yml에 저장 (호출 횟수 최소화)
    #     write_yml({"key": session})
    #     upload_status = upload(session, upload_json)
    #     print(upload_status)

if __name__ == '__main__':
    main()
