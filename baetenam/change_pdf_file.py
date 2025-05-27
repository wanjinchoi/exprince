import xlwings as xw
from datetime import datetime, timedelta

def main(access_token):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_date = datetime.strptime(current_date_str, "%Y-%m-%d") - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    xlsx_path = f'C:\\ARGOSRPA\\report\\{current_date_str}\\{current_date_str}_ARGOS_MDS_Report.xlsx'
    output_path = f'C:\\ARGOSRPA\\report\\{current_date_str}\\{current_date_str}_ARGOS_MDS_Report.pdf'

    # 여백 설정 (인치 단위)
    margin_in_inches = 0.5
    margin_in_points = margin_in_inches * 72  # 1인치 = 72포인트

    # 엑셀 애플리케이션을 숨김 모드로 실행
    with xw.App(visible=False) as app:
        try:
            # 엑셀 파일 열기
            wb = app.books.open(xlsx_path)

            # Sheet1 처리 (Report)
            sheet1 = wb.sheets['Report']

            # 데이터 영역 감지
            data_range1 = sheet1.used_range

            # 인쇄 영역 설정
            sheet1.api.PageSetup.PrintArea = data_range1.address

            # 페이지 설정 (가로 방향)
            sheet1.api.PageSetup.Orientation = xw.constants.PageOrientation.xlLandscape
            sheet1.api.PageSetup.Zoom = False
            sheet1.api.PageSetup.FitToPagesWide = 1
            sheet1.api.PageSetup.FitToPagesTall = False

            # 좌우 여백 설정 (동일하게)
            sheet1.api.PageSetup.LeftMargin = margin_in_points
            sheet1.api.PageSetup.RightMargin = margin_in_points

            # 내용 센터링 설정
            sheet1.api.PageSetup.CenterHorizontally = True

            # 여백 설정 (인치 단위)
            left_margin_in_inches = 0.8  # 왼쪽 여백을 1인치로 설정 (원하는 값으로 변경 가능)
            right_margin_in_inches = 0.3  # 오른쪽 여백을 0.3인치로 설정 (원하는 값으로 변경 가능)

            # 포인트로 변환 (1인치 = 72포인트)
            left_margin_in_points = left_margin_in_inches * 72
            right_margin_in_points = right_margin_in_inches * 72


            # Sheet2 처리 (Report1)
            sheet2 = wb.sheets['Report1']

            # 데이터 영역 감지
            data_range2 = sheet2.used_range

            # 인쇄 영역 설정
            sheet2.api.PageSetup.PrintArea = data_range2.address

            # 페이지 설정 (가로 방향)
            sheet2.api.PageSetup.Orientation = xw.constants.PageOrientation.xlLandscape

            # 비율 설정 (Sheet1과 동일하게)
            sheet2.api.PageSetup.Zoom = False
            sheet2.api.PageSetup.FitToPagesWide = 1
            sheet2.api.PageSetup.FitToPagesTall = False

            # 좌우 여백 설정 (동일하게)
            sheet2.api.PageSetup.LeftMargin = left_margin_in_points
            sheet2.api.PageSetup.RightMargin = right_margin_in_points

            # 내용 센터링 설정
            sheet2.api.PageSetup.CenterHorizontally = True

            # PDF로 저장
            wb.to_pdf(output_path)

            # 엑셀 파일 닫기
            wb.close()

        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main(r'C:\ARGOSRPA\ARGOS_DMS\Master Service\GeneralService\ARGOS.yaml')
