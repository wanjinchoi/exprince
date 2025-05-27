"""
 :ver`0.1` :date`2024.05.29`
====================================
 :mod:`dc_field_update`
====================================

"""
#####################################################
import pandas as pd


# ==========================================================================
def replace_dc(j_data):
    # 대상구분 엑셀 파일 불러오기
    filename = r'C:\work\voc\keywords\dc_update.xlsx'

    # 엑셀 파일 읽기: 제외 카페 시트 읽기
    df = pd.read_excel(filename, sheet_name='대상구분', engine='openpyxl')

    # 디시인사이드 게시판
    target_site = df['사이트명']
    # 변경할 대상구분 값
    target_category = df['대상구분']

    for row_index, site in target_site.items():
        if j_data['site_name'] == site:
            j_data['user_type'] = target_category.loc[row_index]
            break

    return j_data


def main(msg):
    j_data = replace_dc(msg)
    return j_data


###############################
if __name__ == '__main__':
    # msg는 수집 모듈에서 수집한 게시글 데이터
    main(msg)
