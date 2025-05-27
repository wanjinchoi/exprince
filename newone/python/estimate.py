"""
====================================

====================================

Description
===========
견적서 처리
"""
## Authors
# ===========
#
# yong seok Lee
#
#
#  * [2023/12/08]
#     - starting
####################################################

import os
import sys
import requests
import json
import csv
import pandas as pd
from alabs.common.util.vvlogger import get_logger
from alabslib.selenium import PySelenium, Keys


####################################################
class Estimate(PySelenium):

    # ==============================================
    def __init__(self, file_path):

        PySelenium.__init__(self, headless=True, url='https://www.google.com/',
                            browser='Chrome',
                            width='1200', height='800')

        self.file_path = file_path
        log_path = r'C:\work\newone\3.estimate\log\estimate'
        if not os.path.exists(os.path.dirname(log_path)):
            os.makedirs(os.path.dirname(log_path))
        self.logger = get_logger(self.get_safe_path(log_path, 'estimate.log'),
                                 logsize=1024 * 1024 * 10)

    # ==============================================
    def csv_read(self):
        # Excel 파일 읽기
        data_df = pd.read_excel(self.file_path, dtype=str)

        # DataFrame을 리스트 형태로 변환하여 반환
        data_list = data_df.values.tolist()

        return data_list

    # ==============================================
    def get_WMS(self, csv_data):

        # api 키
        # api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNjk5NTc3MDM4LCJleHAiOjE3MzExMTMwMzh9.uIF3yaiXGpmjvopj2AR6J7P61yqCee2_iYypV-Jx8ho'
        api_key = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0b2tlbkNyZWF0ZSIsIlJPTEUiOiJST0xFX0FETUlOIiwiaWF0IjoxNzMxMjk5Nzk3LCJleHAiOjE4MjU5MDc3OTd9.N9byMbOV9LdM1az6MB9e65rftdx8GT2f3uF0V9UJTtI'

        # API 요청 URL
        # base_url = 'http://211.34.80.120:23301/platform/v1/product/item_search?warehouseCode=WC1&'
        base_url = 'http://211.34.80.120:23301/platform/v1/product/item_search_detail?'

        result_list = []

        if csv_data:
            csv_data_number = [row[0] for row in csv_data]

            for item_code in csv_data_number:

                # URL + 품목 코드
                request_url = f'{base_url}itemCode={item_code}'

                # 헤더 설정
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {api_key}'
                }

                try:
                    # GET 요청 보내기
                    response = requests.get(request_url, headers=headers)

                    # 응답 확인
                    if response.status_code == 200:
                        result = response.json()

                        data = result.get('data', None)
                        result_subset = {
                            'itemCode': data.get('itemCode', None),
                            'unit': data.get('itemUnit', None),
                            'priceIn': data.get('itemPrcIn', None),
                            'priceOut': data.get('itemPrcOut', None)
                        }

                        result_list.append(result_subset)
                    else:
                        print(f"Error: {response.status_code}")

                except Exception as e:
                    print(f"An error occurred: {e}")

        return result_list

    # ==============================================

    def csv_process(self, result_list, csv_data):

        # CSV 데이터를 DataFrame으로 변환
        csv_df = pd.DataFrame(csv_data, columns=['itemCode', 'itemName', 'quantity'])

        # Result List를 DataFrame으로 변환
        result_df = pd.DataFrame(result_list)

        # 'itemCode' 열을 문자열로 강제 변환
        csv_df['itemCode'] = csv_df['itemCode'].astype(str)
        result_df['itemCode'] = result_df['itemCode'].astype(str)

        # 'itemCode' 열을 기준으로 합치기 위해 index를 설정
        csv_df.set_index('itemCode', inplace=True)
        result_df.set_index('itemCode', inplace=True)

        # 두 DataFrame을 'itemCode' 열을 기준으로 합침
        merged_df = pd.concat([csv_df, result_df], axis=1, join='outer')

        # 계산할 변수 숫자로 형변환
        numeric_cols = ['quantity', 'priceIn', 'priceOut']
        merged_df[numeric_cols] = merged_df[numeric_cols].apply(pd.to_numeric, errors='coerce')

        # 결측값(NaN)을 0으로 채움
        merged_df.fillna(0, inplace=True)

        # 수량과 단가를 기반으로 계산하여 새로운 열 추가
        # merged_df['단가입고'] = merged_df['priceIn'] * merged_df['quantity']
        # merged_df['단가출고'] = merged_df['priceOut'] * merged_df['quantity']

        merged_df['priceIn'] = merged_df['priceIn'] * merged_df['quantity']
        merged_df['priceOut'] = merged_df['priceOut'] * merged_df['quantity']

        # 업데이트된 데이터를 Excel 파일로 저장
        merged_df.reset_index(inplace=True)

        # 업데이트한 excel 파일 경로
        file_path_plus = 'C:\work\\newone\\3.estimate\outlook\견적서(요청)_업데이트.xlsx'
        # Excel 파일 저장
        with pd.ExcelWriter(file_path_plus, engine='xlsxwriter') as writer:
            merged_df.to_excel(writer, sheet_name='Sheet1', index=False,
                               header=['품목코드', '품목명', '수량', '단위', '입고단가', '출고단가'])

    # ==============================================
    def save_json(self, data, output_file):
        with open(output_file, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f"Data saved to {output_file}")

    # ==============================================
    def start(self):
        try:
            # csv 파일 읽기
            csv_data = self.csv_read()

            # WMS 품목 정보 가져오기
            result_list = self.get_WMS(csv_data)

            # 품목 정보로 csv 업데이트
            self.csv_process(result_list, csv_data)
        except Exception as e:
            self.logger.error(e)
            return 1


# ==============================================
def do_start(file_path):
    with Estimate(file_path=file_path) as ws:
        ws.start()
# def do_start(**kwargs):
#     with Estimate(kwargs['file_path']) as ws:
#         ws.start()


# ==============================================
def main(file_path):
    do_start(file_path)


# ==============================================
if __name__ == '__main__':
    file_path = r'C:\work\newone\3.estimate\outlook\견적서(2차요청) .xlsx'
    # do_start(file_path=file_path)
    main(file_path)
