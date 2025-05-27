from openpyxl.styles import Font
import os
import openpyxl
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
from PIL import Image as PILImage
from openpyxl.drawing.image import Image as OpenpyxlImage
from openpyxl.comments import Comment
import yaml
from copy import copy
from openpyxl.styles import Alignment
import socket


def load_config(yaml_path):
    # yaml 파일읽어서 경로랑 시간 가져오기
    with open(yaml_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    def ensure_time_format(time_value):
        if isinstance(time_value, int):
            return f"{time_value // 60:02}:{time_value % 60:02}"
        return time_value

    report_time_start = ensure_time_format(data['report_time_start'])
    report_time_end = ensure_time_format(data['report_time_end'])
    report_sendtime = ensure_time_format(data['report_sendtime'])

    return {
        'form_path': 'C:\\ARGOSRPA\\form\\ARGOS_MDS_Report.xlsx',
        'monitor3_form_path': 'C:\\ARGOSRPA\\form\\ARGOS_MDS_Report_monitor3.xlsx',
        'report_path': 'C:\\ARGOSRPA\\report\\',
        'send_folder_path': 'C:\\ARGOSRPA\\detection_collector\\send_screens\\',
        'db_path': 'C:\\ARGOSRPA\\Master Service\\GeneralService\\database.db',
        'report_time_start': report_time_start,
        'report_time_end': report_time_end,
        'report_sendtime': report_sendtime,
        'txt_file_path': 'C:\\ARGOSRPA\\form\\send_report_list.txt',
    }

def query_db(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        ('files',))
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return [result[0] for result in results]


def prepare_excel_report(config, current_date_str, unique_screens):
    current_datetime = datetime.now()
    today_midnight = datetime.combine(current_datetime.date(),datetime.min.time())
    report_time_end = datetime.strptime(config['report_time_end'],"%H:%M").time()
    report_time_end_datetime = datetime.combine(today_midnight + timedelta(days=1), report_time_end)
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_date = datetime.strptime(current_date_str,"%Y-%m-%d") - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    yesterday_result_path = f"{config['report_path']}{yesterday_date_str}\\{yesterday_date_str}_ARGOS_MDS_Report.xlsx"
    result_folder_path = os.path.join(config['report_path'], current_date_str)
    if len(unique_screens) < 3:
        result_path = result_folder_path + '\\' + current_date_str + '_ARGOS_MDS_Report.xlsx'
    else:
        result_path = result_folder_path + '\\' + current_date_str + '_ARGOS_MDS_Report_monitor3.xlsx'
    output_pdf_path = result_folder_path + '\\' + current_date_str + '_ARGOS_MDS_Report.pdf'
    # 결과 폴더가 존재하지 않으면 생성
    if not os.path.exists(result_folder_path):
        os.makedirs(result_folder_path)

    # 엑셀 파일 로드
    if not os.path.exists(result_path):
        if len(unique_screens) < 3:
            wb = openpyxl.load_workbook(config['form_path'])
        else:
            wb = openpyxl.load_workbook(config['monitor3_form_path'])
    # elif current_datetime < today_midnight:
    #     wb = openpyxl.load_workbook(result_path)
    # elif today_midnight <= current_datetime < report_time_end_datetime:
    #     wb = openpyxl.load_workbook(yesterday_result_path)
    else:
        wb = openpyxl.load_workbook(result_path)
    # 아침에 딱 한번만 rpeort 만드는 경우
    # 결과 폴더가 존재하지 않으면 생성

    return wb, result_path


def update_excel(ws, data, current_date_str, result_path):
    #Fire인경우 빨간색으로
    red_font = Font(color="FF0000")
    #데이터가 없는 경우는 전부 0으로 입력되도록
    if len(data['dates'])==0:
        result ='nodata'
        ws['D3'].value = '0'
        ws['D5'].value = '0'
        ws['D6'].value = '0'
        ws['H5'].value = '0'
        ws['H6'].value = '0'
        ws['J5'].value = '0'
        ws['J6'].value = '0'
        screen_cam_dict = defaultdict(list)
        for screen, cam in zip(data['screens'], data['cams']):
            screen_cam_dict[screen].append(cam)

        x = []
        for screen in sorted(screen_cam_dict):
            cams = ', '.join(sorted(set(screen_cam_dict[screen])))  # 중복 제거 및 정렬
            x.append(f"{screen} ({cams})")

        # 리스트를 반복하면서 각 항목을 워크시트 셀에 할당
        for index, item in enumerate(x, start=3):  # 3행부터 시작
            part1 = item.split(' (')[0]  # 'SC01' 또는 'SC02' 추출
            part2 = item.split(' (')[1].rstrip(')')  # 괄호 안의 내용 추출
            ws[f'H{index}'].value = part1  # I열에 'SC01', 'SC02' 할당
            ws[f'I{index}'].value = part2  # J열에 괄호 안의 내용 할당

        print(result)
    else:
        # 필요한 스타일 요소들만 개별적으로 복사
        border_style = copy(ws['H9'].border)
        alignment_style = copy(ws['H9'].alignment)
        fill_style = copy(ws['H9'].fill)
        font_style = copy(ws['H9'].font)

        # H9과 동일하게 병합된 셀 적용 및 스타일 설정
        max_row = max((a.row for a in ws['B'] if a.value is not None))

        # H열부터 K열까지 병합하고 스타일을 적용
        for row in range(10, len(data['dates'])+9):
            ws.merge_cells(start_row=row, start_column=8, end_row=row,
                           end_column=11)

            # 병합된 셀에 스타일 개별적으로 적용
            for col in ['H', 'I', 'J', 'K']:  # H부터 K까지 병합되었으므로 각 셀에 스타일 적용
                cell = ws[f'{col}{row}']
                cell.border = border_style
                cell.alignment = alignment_style
                cell.fill = fill_style
                cell.font = font_style
        #모니터숫자가 2개일경우
        if 'monitor3' not in result_path:
            ## 날짜 기입
            ws['I2'].value = current_date_str
            ## Total Detection Count
            ws['D5'].value = str(len(data['dates']))
            ## Number of Monitoring Cams
            ws['D3'].value = data['number_of_cams'][0]

            ##Movent/Human
            # 공백 제거 및 소문자 통일
            movement_count = data['detection_types'].count('Movement')
            human_count = data['detection_types'].count('Human')
            different_cam_count = data['detection_types'].count('different_cam')
            fire_count = data['detection_types'].count('Fire')
            nosignl_count = data['detection_types'].count('no_signal')
            Discoloration_count = data['detection_types'].count('Discoloration')


            ## human Detection
            ws['H5'].value = human_count
            ## Movement Detection
            ws['J5'].value = movement_count
            ##Fire Detection
            ws['D6'].value = fire_count
            ## No signal/view angle Change Detection
            ws['H6'].value = nosignl_count
            ## Discoloration Detection
            ws['J6'].value = Discoloration_count

            #스크린 이름과 캠이름 매칭
            screen_cam_dict = defaultdict(list)
            for screen, cam in zip(data['screens'], data['cams']):
                screen_cam_dict[screen].append(cam)

            x = []
            for screen in sorted(screen_cam_dict):
                cams = ', '.join(sorted(set(screen_cam_dict[screen])))# 중복 제거 및 정렬
                x.append(f"{screen} ({cams})")

            # 리스트를 반복하면서 각 항목을 워크시트 셀에 할당
            for index, item in enumerate(x, start=3):  # 3행부터 시작
                part1 = item.split(' (')[0]  # 'SC01' 또는 'SC02' 추출
                part2 = item.split(' (')[1].rstrip(')')  # 괄호 안의 내용 추출
                ws[f'H{index}'].value = part1  # I열에 'SC01', 'SC02' 할당
                ws[f'I{index}'].value = part2  # J열에 괄호 안의 내용 할당

            ####### 내용 입력######################
            base_fonts = {col: copy(ws[col + '9'].font) for col in 'BCDEFGHIJ'}
            for font in base_fonts.values():
                font.name = 'Arial'
                font.size = 14
            #엑셀 셀서식 복사
            base_styles = {col: ws[col + '9']._style for col in 'BCDEFGH'}
            base_fonts = {col: copy(ws[col + '9'].font) for col in 'BCDEFGH'}
            base_borders = {col: copy(ws[col + '9'].border) for col in 'BCDEFGH'}
            base_fills = {col: copy(ws[col + '9'].fill) for col in 'BCDEFGH'}
            base_number_formats = {col: copy(ws[col + '9'].number_format) for col in 'BCDEFGH'}
            base_protections = {col: copy(ws[col + '9'].protection) for col in 'BCDEFGH'}
            base_alignments = {col: copy(ws[col + '9'].alignment) for col in 'BCDEFGH'}
            base_row_height = ws.row_dimensions[9].height
            #최대열 구하기
            max_row = max((a.row for a in ws['B'] if a.value is not None))
            #최대열이 9보다 작은경우 그러니깐 처음 입력할때
            if max_row < 9:
                j = 9
                for i in range(len(data['dates'])):
                    ws['B' + str(j)].value = '0' + str(i + 1)
                    ws['C' + str(j)].value = str(data['dates'][i]) + ' ' + str(data['times'][i])
                    ws['D' + str(j)].value = str(data['screens'][i])
                    ws['E' + str(j)].value = str(data['cams'][i])
                    ws['F' + str(j)].value = str(data['cam_names'][i])
                    ws['G' + str(j)].value = str(data['detection_types'][i])
                    hostname = socket.gethostname()
                    ip_address = socket.gethostbyname(hostname)
                    ws['H'+  str(j)].value = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].hyperlink = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].style = "Hyperlink"
                    ws['H' + str(j)].alignment = Alignment(horizontal='center')

                    # 이미지 파일 경로를 참조할 수 있도록 코멘트를 추가
                    # date_time_str = f"{data['dates'][i].replace('-', '')}_{data['times'][i].replace(':', '')}"
                    # screen_cam_str = f"{data['screens'][i]}_{data['cams'][i]}"
                    # ws[f'J{j}'].comment = Comment(f"{date_time_str}_{screen_cam_str}", "System")

                    #엑셀 셀서식 복사
                    for col in 'BCDEFGH':
                        cell = ws[col + str(j)]
                        if col in base_styles:
                            cell._style = base_styles[col]
                            cell.font = base_fonts[col]
                            cell.border = base_borders[col]
                            cell.fill = base_fills[col]
                            cell.number_format = base_number_formats[col]
                            cell.protection = base_protections[col]
                            cell.alignment = base_alignments[col]
                    #불일경우
                    if ws['G' + str(j)].value.lower() == 'fire':
                        ws['G' + str(j)].value = 'Fire'
                        ws['G' + str(j)].font = red_font

                    ws.row_dimensions[j].height = base_row_height
                    j += 1
            else:
                j = 9
                z = max_row - 8
                for i in range(j, len(data['dates'])):
                    max_row = max((a.row for a in ws['B'] if a.value is not None))
                    ws['B' + str(max_row + 1)].value = '0' + str(i + 1)
                    ws['C' + str(max_row + 1)].value = str(data['dates'][i]) + ' ' + str(data['times'][i])
                    ws['D' + str(max_row + 1)].value = str(data['screens'][i])
                    ws['E' + str(max_row + 1)].value = str(data['cams'][i])
                    ws['F' + str(max_row + 1)].value = str(data['cam_names'][i])
                    ws['G' + str(max_row + 1)].value = str(data['detection_types'][i])

                    # 이미지 슬라이드쇼 링크 넣는 코드
                    hostname = socket.gethostname()
                    ip_address = socket.gethostbyname(hostname)
                    ws['H'+  str(j)].value = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].hyperlink = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].style = "Hyperlink"
                    ws['H' + str(j)].alignment = Alignment(horizontal='center')


                    # 이미지 파일 경로를 참조할 수 있도록 코멘트를 추가
                    # date_time_str = f"{data['dates'][i].replace('-', '')}_{data['times'][i].replace(':', '')}"
                    # screen_cam_str = f"{data['screens'][i]}_{data['cams'][i]}"
                    # ws[f'J{max_row + 1}'].comment = Comment(f"{date_time_str}_{screen_cam_str}", "System")

                    for col in 'BCDEFGH':
                        cell = ws[col + str(max_row + 1)]
                        if col in base_styles:
                            cell._style = base_styles[col]
                            cell.font = base_fonts[col]
                            cell.border = base_borders[col]
                            cell.fill = base_fills[col]
                            cell.number_format = base_number_formats[col]
                            cell.protection = base_protections[col]
                            cell.alignment = base_alignments[col]

                    # H열의 글자가 fire이면 색깔을 빨간색으로 설정하고 글자를 Fire로 변경
                    if ws['G' + str(max_row + 1)].value.lower() == 'fire':
                        ws['G' + str(max_row + 1)].value = 'Fire'
                        ws['G' + str(max_row + 1)].font = red_font

                    ws.row_dimensions[max_row + 1].height = base_row_height
        else:

            ## 날짜 기입
            ws['I2'].value = current_date_str
            ## Total Detection Count
            ws['D6'].value = str(len(data['dates']))
            ## Number of Monitoring Cams
            ws['D3'].value = data['number_of_cams'][0]

            ##Movent/Human
            # 공백 제거 및 소문자 통일
            movement_count = data['detection_types'].count('Movement')
            human_count = data['detection_types'].count('Human')
            different_cam_count = data['detection_types'].count('different_cam')
            fire_count = data['detection_types'].count('Fire')
            nosignl_count = data['detection_types'].count('no_signal')
            Discoloration_count = data['detection_types'].count('Discoloration')


            ## human Detection
            ws['H6'].value = human_count
            ## Movement Detection
            ws['J6'].value = movement_count
            ##Fire Detection
            ws['D7'].value = fire_count
            ## No signal/view angle Change Detection
            ws['H7'].value = nosignl_count
            ## Discoloration Detection
            ws['J7'].value = Discoloration_count


            screen_cam_dict = defaultdict(list)
            for screen, cam in zip(data['screens'], data['cams']):
                screen_cam_dict[screen].append(cam)

            x = []
            for screen in sorted(screen_cam_dict):
                cams = ', '.join(sorted(set(screen_cam_dict[screen])))# 중복 제거 및 정렬
                x.append(f"{screen} ({cams})")

            # 리스트를 반복하면서 각 항목을 워크시트 셀에 할당
            for index, item in enumerate(x, start=3):  # 3행부터 시작
                part1 = item.split(' (')[0]  # 'SC01' 또는 'SC02' 추출
                part2 = item.split(' (')[1].rstrip(')')  # 괄호 안의 내용 추출
                ws[f'H{index}'].value = part1  # I열에 'SC01', 'SC02' 할당
                ws[f'H{index}'].value = part2  # J열에 괄호 안의 내용 할당



            #######모니터가 3개일때 내용 입력###################################

            ##셀서식 복사
            base_styles = {col: ws[col + '10']._style for col in 'BCDEFGH'}
            base_fonts = {col: copy(ws[col + '10'].font) for col in 'BCDEFGH'}
            base_borders = {col: copy(ws[col + '10'].border) for col in 'BCDEFGH'}
            base_fills = {col: copy(ws[col + '10'].fill) for col in 'BCDEFGH'}
            base_number_formats = {col: copy(ws[col + '10'].number_format) for col in 'BCDEFGH'}
            base_protections = {col: copy(ws[col + '10'].protection) for col in 'BCDEFGH'}
            base_alignments = {col: copy(ws[col + '10'].alignment) for col in 'BCDEFGH'}
            base_row_height = ws.row_dimensions[10].height


            max_row = max((a.row for a in ws['B'] if a.value is not None))
            if max_row < 10:
                j = 10
                for i in range(len(data['dates'])):
                    ws['B' + str(j)].value = '0' + str(i + 1)
                    ws['C' + str(j)].value = str(data['dates'][i]) + ' ' + str(data['times'][i])
                    ws['D' + str(j)].value = str(data['screens'][i])
                    ws['E' + str(j)].value = str(data['cams'][i])
                    ws['F' + str(j)].value = str(data['cam_names'][i])
                    ws['G' + str(j)].value = str(data['detection_types'][i])
                    hostname = socket.gethostname()
                    ip_address = socket.gethostbyname(hostname)
                    ws['H'+  str(j)].value = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].hyperlink = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].style = "Hyperlink"
                    ws['H' + str(j)].alignment = Alignment(horizontal='center')

                    # # 이미지 파일 경로를 참조할 수 있도록 코멘트를 추가
                    # date_time_str = f"{data['dates'][i].replace('-', '')}_{data['times'][i].replace(':', '')}"
                    # screen_cam_str = f"{data['screens'][i]}_{data['cams'][i]}"
                    # ws[f'J{j}'].comment = Comment(f"{date_time_str}_{screen_cam_str}", "System")

                    for col in 'BCDEFGH':
                        cell = ws[col + str(j)]
                        if col in base_styles:
                            cell._style = base_styles[col]
                            cell.font = base_fonts[col]
                            cell.border = base_borders[col]
                            cell.fill = base_fills[col]
                            cell.number_format = base_number_formats[col]
                            cell.protection = base_protections[col]
                            cell.alignment = base_alignments[col]

                    # H열의 글자가 fire이면 색깔을 빨간색으로 설정하고 글자를 Fire로 변경
                    if ws['G' + str(j)].value.lower() == 'fire':
                        ws['G' + str(j)].value = 'Fire'

                    ws.row_dimensions[j].height = base_row_height
                    j += 1
            else:
                j = 10
                z = max_row - 9
                for i in range(z, len(data['dates'])):
                    max_row = max((a.row for a in ws['B'] if a.value is not None))
                    ws['B' + str(max_row + 1)].value = '0' + str(i + 1)
                    ws['C' + str(max_row + 1)].value = str(data['dates'][i]) + ' ' + str(data['times'][i])
                    ws['D' + str(max_row + 1)].value = str(data['screens'][i])
                    ws['E' + str(max_row + 1)].value = str(data['cams'][i])
                    ws['F' + str(max_row + 1)].value = str(data['cam_names'][i])
                    hostname = socket.gethostname()
                    ip_address = socket.gethostbyname(hostname)
                    ws['H'+  str(j)].value = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].hyperlink = f'http://{ip_address}:8000/folders/{data["dates"][i]}/{data["screens"][i]}/{data["cams"][i]}/{data["af_image_names"][i]}'
                    ws['H' + str(j)].style = "Hyperlink"
                    ws['H' + str(j)].alignment = Alignment(horizontal='center')
                    # 이미지 파일 경로를 참조할 수 있도록 코멘트를 추가
                    # date_time_str = f"{data['dates'][i].replace('-', '')}_{data['times'][i].replace(':', '')}"
                    # screen_cam_str = f"{data['screens'][i]}_{data['cams'][i]}"
                    # ws[f'J{max_row + 1}'].comment = Comment(f"{date_time_str}_{screen_cam_str}", "System")

                    for col in 'BCDEFGH':
                        cell = ws[col + str(max_row + 1)]
                        if col in base_styles:
                            cell._style = base_styles[col]
                            cell.font = base_fonts[col]
                            cell.border = base_borders[col]
                            cell.fill = base_fills(col)
                            cell.number_format = base_number_formats(col)
                            cell.protection = base_protections(col)
                            cell.alignment = base_alignments(col)
                    # H열의 글자가 fire이면 색깔을 빨간색으로 설정하고 글자를 Fire로 변경
                    if ws['G' + str(max_row + 1)].value.lower() == 'fire':
                        ws['G' + str(max_row + 1)].value = 'Fire'

                    ws.row_dimensions[max_row + 1].height = base_row_height

##2024.09.09 폐기
def insert_images(ws, column, start_row, send_folder_path):
    height_px = int((4.79 / 2.54) * 96)
    width_px = int((6.35 / 2.54) * 96)
    row = start_row

    # K10과 L10의 스타일을 저장
    if column == 'J':
        base_style = ws['J10']._style
        base_font = copy(ws['J10'].font)
        base_border = copy(ws['J10'].border)
        base_fill = copy(ws['J10'].fill)
        base_number_format = copy(ws['J10'].number_format)
        base_protection = copy(ws['J10'].protection)
        base_alignment = copy(ws['J10'].alignment)
        base_row_height = ws.row_dimensions[10].height
    elif column == 'K':
        base_style = ws['K10']._style
        base_font = copy(ws['K10'].font)
        base_border = copy(ws['K10'].border)
        base_fill = copy(ws['K10'].fill)
        base_number_format = copy(ws['K10'].number_format)
        base_protection = copy(ws['K10'].protection)
        base_alignment = copy(ws['K10'].alignment)
        base_row_height = ws.row_dimensions[10].height

    max_row = ws.max_row

    while row <= max_row:
        comment_K = ws[f"J{row}"].comment
        comment_L = ws[f"K{row}"].comment
        bf_image_inserted = False
        af_image_inserted = False

        if comment_K:
            comment_text = comment_K.text
            parts = comment_text.split('_')
            date_str = parts[0]
            formatted_date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"  # YYYYMMDD -> YYYY-MM-DD
            time_str = parts[1]
            screen = parts[2]
            cam = parts[3]

            bf_image_path = os.path.join(send_folder_path, formatted_date_str, f"{time_str}_{screen}_{cam}_bf.png")
            af_image_path = os.path.join(send_folder_path, formatted_date_str, f"{time_str}_{screen}_{cam}_af.png")

            if os.path.exists(bf_image_path):
                try:
                    with PILImage.open(bf_image_path) as img:
                        new_img = img.resize((width_px, height_px), PILImage.LANCZOS)
                        resized_path = bf_image_path.replace('.png', '_resized.png')
                        new_img.save(resized_path, 'JPEG', quality=85)

                        if os.path.exists(resized_path):
                            img = OpenpyxlImage(resized_path)
                            cell_ref = f'J{row}'
                            ws.add_image(img, cell_ref)
                            ws[f"J{row}"].comment = Comment(f"Image Inserted: {os.path.basename(bf_image_path)}", "System")
                            bf_image_inserted = True
                except Exception as e:
                    print(f"Error processing image {bf_image_path}: {e}")

            if os.path.exists(af_image_path):
                try:
                    with PILImage.open(af_image_path) as img:
                        new_img = img.resize((width_px, height_px), PILImage.LANCZOS)
                        resized_path = af_image_path.replace('.png', '_resized.png')
                        new_img.save(resized_path, 'JPEG', quality=85)

                        if os.path.exists(resized_path):
                            img = OpenpyxlImage(resized_path)
                            cell_ref = f'K{row}'
                            ws.add_image(img, cell_ref)
                            ws[f"K{row}"].comment = Comment(f"Image Inserted: {os.path.basename(af_image_path)}", "System")
                            af_image_inserted = True
                except Exception as e:
                    print(f"Error processing image {af_image_path}: {e}")

        if bf_image_inserted or af_image_inserted:
            row += 1
        else:
            row += 1  # Ensure to move to the next row if no image was inserted


def main(yaml_path):

    current_date_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_date = datetime.strptime(current_date_str, "%Y-%m-%d") - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    # yesterday_date_str ='2024-09-10'
    # current_date_str='2024-09-11'
    # yaml 파일 정보 가져오기
    config = load_config(yaml_path)
    start_time = config['report_time_start']
    end_time = config['report_time_end']
    send_time = config['report_sendtime']
    start_time = datetime.strptime(start_time, "%H:%M").time()
    end_time = datetime.strptime(end_time, "%H:%M").time()
    send_time= datetime.strptime(send_time, "%H:%M").time()
    #리포트 받는 시간이 데이터 수집 시간보다 짧은경우 리포트 받는 시간에 맞춰서 데이터 조회
    if send_time < end_time:
        query = lambda field: f"""
                   SELECT {field}
                   FROM files
                   WHERE datetime(date || ' ' || time) >= '{yesterday_date_str} {config['report_time_start']}'
                   AND datetime(date || ' ' || time) <= '{current_date_str} {config['report_sendtime']}'
                   ORDER BY datetime(date || ' ' || time) ASC;
                   """
    #하루
    elif start_time >= end_time:
        # 쿼리 수정: date와 time을 결합하여 정렬
        query = lambda field: f"""
            SELECT {field}
            FROM files
            WHERE datetime(date || ' ' || time) >= '{yesterday_date_str} {config['report_time_start']}'
            AND datetime(date || ' ' || time) <= '{current_date_str} {config['report_time_end']}'
            ORDER BY datetime(date || ' ' || time) ASC;
            """

    ##당일
    elif start_time < end_time:
        query = lambda field: f"""
            SELECT {field}
            FROM files
            WHERE datetime(date || ' ' || time) >= '{current_date_str} {config['report_time_start']}'
            AND datetime(date || ' ' || time) <= '{current_date_str} {config['report_time_end']}'
            ORDER BY datetime(date || ' ' || time) ASC;
            """
    data2 = {
        'screens': query_db(config['db_path'], query('screen')),
    }

    # 스크린수 알기
    unique_screens = list(set(data2['screens']))
    # report 양식 가져오기
    wb, result_path = prepare_excel_report(config, current_date_str, unique_screens)
    ws = wb['Report1']

    type_change_report_sendtime = datetime.strptime(config['report_sendtime'], "%H:%M").time()

    # 현재 날짜를 기준으로 report_sendtime의 datetime 객체 생성
    report_sendtime_datetime = datetime.combine(datetime.today(), type_change_report_sendtime)

    # report_sendtime의 5분 후 시간을 계산
    five_minutes_after_report_sendtime = report_sendtime_datetime + timedelta(minutes=5)

    # 현재 시간을 가져옴
    now = datetime.now()
    #DB에서 정보가져오기
    data = {
        'dates': query_db(config['db_path'], query('date')),
        'times': query_db(config['db_path'], query('time')),
        'screens': query_db(config['db_path'], query('screen')),
        'screen_names': query_db(config['db_path'], query('screen_name')),
        'cams': query_db(config['db_path'], query('cam')),
        'cam_names': query_db(config['db_path'], query('cam_name')),
        'detection_types': query_db(config['db_path'], query('detection_type')),
        'bf_image_names': query_db(config['db_path'], query('bf_image_name')),
        'af_image_names': query_db(config['db_path'], query('af_image_name')),
        'number_of_cams': query_db(config['db_path'], query('cam_count'))
    }

    # 엑셀내용 입력
    update_excel(ws, data, current_date_str, result_path)

    if 'monitor3' not in result_path:
        start_row = 9
    else:
        start_row = 10

    # insert_images(ws, 'J', start_row, config['send_folder_path'])
    # insert_images(ws, 'K', start_row, config['send_folder_path'])

    wb.save(result_path)
    wb.close()
if __name__ == "__main__":
    main(r'C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml')
