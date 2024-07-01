import glob
import os
from copy import copy
import openpyxl
from datetime import datetime, timedelta
import sqlite3
from collections import defaultdict
from PIL import Image as PILImage
from openpyxl.drawing.image import Image as OpenpyxlImage
import warnings
from openpyxl.comments import Comment
from openpyxl.reader.excel import load_workbook
import yaml

warnings.filterwarnings("ignore", category=DeprecationWarning)
import io
def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")
    yesterday_date = current_date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")

    with open('road.yaml','r') as file:
        data = yaml.safe_load(file)
        form_path = os.path.normpath(data['form_path'])
        report_path = os.path.normpath(data['report_path'])
        db_path = os.path.normpath(data['db_path'])
        seend_screen_path = os.path.normpath(data['send_folder_path'])
    result_folder_path = report_path + current_date_str
    if not os.path.exists(result_folder_path):
        os.mkdir(result_folder_path)


    #db연결
    conn = sqlite3.connect(db_path)
    #커서 객체 생성. SQL 명령어 실행
    cursor = conn.cursor()

    # 오전 8시 기준 시간 설정
    cutoff_time = datetime.strptime("08:00:00", "%H:%M:%S").time()

    # 쿼리 조건 설정
    now = datetime.now()
    current_time = now.time()
    if current_time >= cutoff_time:
        time_condition = "AND strftime('%H:%M:%S', time) >= '08:00:00'"
    else:
        time_condition = ""


    # 날짜 쿼리문
    query = f"SELECT date FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition};"
    cursor.execute(query)
    dates = cursor.fetchall()
    simple_dates = [date[0] for date in dates]

    # 시간조회
    query = f"SELECT time FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    times = cursor.fetchall()
    simple_time = [time[0] for time in times]

    # Screen
    query = f"SELECT screen FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    screens = cursor.fetchall()
    simple_screen = [screen[0] for screen in screens]

    # Screen_name
    query = f"SELECT screen_name FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    screen_names = cursor.fetchall()
    simple_screen_name = [screen_name[0] for screen_name in screen_names]

    # cam
    query = f"SELECT cam FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    cams = cursor.fetchall()
    simple_cam = [cam[0] for cam in cams]

    # cam_name
    query = f"SELECT cam_name FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    cam_names = cursor.fetchall()
    simple_cam_name = [cam_name[0] for cam_name in cam_names]

    # detection_type
    query = f"SELECT detection_type FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    detection_types = cursor.fetchall()
    simple_detection_type = [detection_type[0] for detection_type in detection_types]

    # bf_image_name
    query = f"SELECT bf_image_name FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    bf_image_names = cursor.fetchall()
    simple_bf_image_name = [bf_image_name[0] for bf_image_name in bf_image_names]

    # af_image_name
    query = f"SELECT af_image_name FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    af_image_names = cursor.fetchall()
    simple_af_image_name = [af_image_name[0] for af_image_name in af_image_names]

    # number_of_cams
    query = f"SELECT cam_count FROM files WHERE strftime('%Y-%m-%d', date) = date('now') {time_condition} ORDER BY time ASC;"
    cursor.execute(query)
    number_of_cams = cursor.fetchall()
    simple_number_of_cams = [number_of_cam[0] for number_of_cam in number_of_cams]


####################################엑셀 편집#############################################
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    current_date = datetime.strptime(current_date_str, "%Y-%m-%d")

    yesterday_date = current_date - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")
    yesterday_result_folder_path = report_path + yesterday_date_str
    yesterday_result_path= yesterday_result_folder_path + '\\'+yesterday_date_str+'_ARGOS C-CUBE Report_v1.0.xlsx'

    result_path = result_folder_path + '\\' + current_date_str + '_ARGOS C-CUBE Report_v1.0.xlsx'

    # 현재 날짜와 시간 가져오기
    current_datetime = datetime.now()

    # 08:00 시간 생성
    today_midnight = datetime.combine(now.date(), datetime.min.time())
    tomorrow_8am = today_midnight + timedelta(days=1, hours=8)



    if not os.path.exists(result_path):
        wb = openpyxl.load_workbook(form_path)
        ws = wb['Report']
        store_path = result_path
    elif now < today_midnight:
        wb = openpyxl.load_workbook(result_path)
        ws = wb['Report']
        store_path = result_path
    elif today_midnight <= now < tomorrow_8am:
        wb = openpyxl.load_workbook(yesterday_result_path)
        ws = wb['Report']
        store_path = yesterday_result_path
    else:
        wb = openpyxl.load_workbook(yesterday_result_path)
        ws = wb['Report']
        store_path = result_path


    ## 날짜 기입
    ws['L2'].value = current_date_str
    ## Total Detection Count
    ws['E4'].value = str(len(simple_dates))
    ## Number of Monitoring Cams
    ws['E3'].value = simple_number_of_cams[0]

    ##Movent/Human
    # 공백 제거 및 소문자 통일
    simple_detection_type = [item.strip().lower() for item in simple_detection_type]
    human_count = sum('human' in item for item in simple_detection_type)
    movent_count = simple_detection_type.count('movement')
    all_count = simple_detection_type.count('all')
    count_result = int(human_count) + int(movent_count)+ int(all_count)
    #human_count와 movent_count가 각각 있는경우
    if (human_count > 0) or (movent_count >0):
        ws['I4'].value = str(movent_count)+'/'+str(human_count)
     #all만 있는 경우
    else:
        ws['I4'].value = str(all_count)

    # Monitoring CAMS
    screen_cam_dict = defaultdict(list)

    # 각 스크린 ID에 해당하는 카메라 목록을 채우기
    for screen, cam in zip(simple_screen, simple_cam):
        screen_cam_dict[screen].append(cam)

    # 결과 출력
    x =[]
    for screen in sorted(screen_cam_dict):
        cams = ', '.join(sorted(set(screen_cam_dict[screen])))  # 중복 제거 및 정렬
        x.append(f"{screen} ({cams})")

    # 리스트의 모든 항목을 하나의 문자열로 결합하고 I3 셀에 저장
    ws['I3'] = ", ".join(x)


    #############################내용 입력#####################################
    base_styles = {col: ws[col + '8']._style for col in 'BCDEFGH'}
    j = 8
    base_style = ws['F8']._style
    # 이전 셀의 너비와 높이를 가져오기 위한 코드
    base_styles = {col: ws[col + '8']._style for col in 'BCDEFGH'}
    base_fonts = {col: copy(ws[col + '8'].font) for col in 'BCDEFGH'}
    base_borders = {col: copy(ws[col + '8'].border) for col in 'BCDEFGH'}
    base_fills = {col: copy(ws[col + '8'].fill) for col in 'BCDEFGH'}
    base_number_formats = {col: copy(ws[col + '8'].number_format) for col in'BCDEFGH'}
    base_protections = {col: copy(ws[col + '8'].protection) for col in'BCDEFGH'}
    base_alignments = {col: copy(ws[col + '8'].alignment) for col in 'BCDEFGH'}
    base_row_height = ws.row_dimensions[8].height
    max_row = max((a.row for a in ws['B'] if a.value is not None))
    if max_row < 8:
        for i in range(len(simple_time)):
            #index
            ws['B'+str(j)].value = '0'+str(i+1)
            #Date
            ws['C'+str(j)].value = str(simple_dates[i])+'\n'+ str(simple_time[i])
            #Screen
            ws['D'+str(j)].value = str(simple_screen[i])
            #Screen Name
            ws["E"+str(j)].value = str(simple_screen_name[i])
            #CAM#
            ws['F'+str(j)].value = str(simple_cam[i])
            #CAM Name
            ws['G'+str(j)].value = str(simple_cam_name[i])
            #Detection Type
            ws['H'+str(j)].value = str(simple_detection_type[i])

            # 스타일 적용
            for col in 'BCDEFGH':
                cell = ws[col + str(j)]
                if col in base_styles:  # 기본 스타일이 있으면 적용
                    cell._style = base_styles[col]
                    cell.font = base_fonts[col]
                    cell.border = base_borders[col]
                    cell.fill = base_fills[col]
                    cell.number_format = base_number_formats[col]
                    cell.protection = base_protections[col]
                    cell.alignment = base_alignments[col]

            ws.row_dimensions[j].height = base_row_height

            j += 1
    else:
        j=8
        ## 엑셀은 8번째 행부터 시작하기 때문에 데이터는 -7을 해줘야함
        z = max_row -7
        for i in range(z,len(simple_time)):
            max_row = max((a.row for a in ws['B'] if a.value is not None))
            # index
            ws['B' + str(max_row+1)].value = '0' + str( i+ 1)
            # Date
            ws['C' + str(max_row+1)].value = str(simple_dates[i]) + '\n' + str(simple_time[i])
            # Screen
            ws['D' + str(max_row+1)].value = str(simple_screen[i])
            # Screen Name
            ws["E" + str(max_row+1)].value = str(simple_screen_name[i])
            # CAM#
            ws['F' + str(max_row+1)].value = str(simple_cam[i])
            # CAM Name
            ws['G' + str(max_row+1)].value = str(simple_cam_name[i])
            # Detection Type
            ws['H' + str(max_row+1)].value = str(simple_detection_type[i])

            # 스타일 적용
            for col in 'BCDEFGH':
                cell = ws[col + str(j)]
                if col in base_styles:  # 기본 스타일이 있으면 적용
                    cell._style = base_styles[col]
                    cell.font = base_fonts[col]
                    cell.border = base_borders[col]
                    cell.fill = base_fills[col]
                    cell.number_format = base_number_formats[col]
                    cell.protection = base_protections[col]
                    cell.alignment = base_alignments[col]

            ws.row_dimensions[max_row + 1].height = base_row_height

    wb.save(store_path)
    wb.close()


    #####################이미지 삽입############################################
    send_folder_path = seend_screen_path+current_date_str+'\\'
    flist = sorted(glob.glob(send_folder_path + '*.png'), key=os.path.getmtime)
    ## 이미지 리스트에서 bf파일 매치해서 찾기
    bf_filenames = {os.path.basename(path): path for path in flist}
    ## 이미지 리스트에서 af파일 매치해서 찾기
    af_filenames = {os.path.basename(path2): path2 for path2 in flist}
    # 일치하는 파일의 전체 경로를 저장할 리스트
    bf_matched_paths = []
    af_matched_paths= []
    # 이미지 리스트중 bf맞는 것 끼리만 리스트에 넣기
    for filename in simple_bf_image_name:
        if filename in bf_filenames:
            bf_matched_paths.append(bf_filenames[filename])

    # 이미지 리스트중 af맞는 것 끼리만 리스트에 넣기
    for filename in simple_af_image_name:
        if filename in af_filenames:
            af_matched_paths.append(af_filenames[filename])

    # 센티미터에서 인치로 변환(이미지 크리 변동을 위해)
    height_px = int((4.79 / 2.54) * 96)
    width_px = int((6.35 / 2.54) * 96)  # cm to inches
    if len(simple_time)> 0:
        def resize_and_insert_image(image_paths, column, start_row, ws):
            row = start_row
            for path in image_paths:
                filename = os.path.basename(path)

                try:
                    # 이미지가 이미 삽입된 셀인지 확인
                    while ws[f"{column}{row}"].comment and "Image Inserted" in ws[
                        f"{column}{row}"].comment.text:
                        if filename in ws[f"{column}{row}"].comment.text:
                            print(
                                f"Image already inserted at {column}{row}: {filename}")
                            break
                        row += 1
                    else:
                        # 루프가 정상적으로 종료된 경우에만 이미지 삽입
                        with PILImage.open(path) as img:
                            new_img = img.resize((width_px, height_px),
                                                 PILImage.LANCZOS)
                            resized_path = path.replace('.png', '_resized.png')
                            new_img.save(resized_path, 'JPEG',quality=85)

                            if os.path.exists(resized_path):
                                img = OpenpyxlImage(resized_path)
                                cell_ref = f'{column}{row}'
                                ws.add_image(img, cell_ref)
                                # 중복을 피하기 위해 코멘트 삽입
                                ws[f"{column}{row}"].comment = Comment(
                                    f"Image Inserted: {filename}", "System")
                                print(f"Added image to Excel at: {cell_ref}")
                            else:
                                print(
                                    f"Resized image does not exist: {resized_path}")
                            row += 1
                except Exception as e:
                    print(f"Error processing image {path}: {e}")

        try:
            # 엑셀 파일 열기
            wb = load_workbook(store_path)
            ws = wb.active
            # 이미지 크기 설정
            height_px = int((4.79 / 2.54) * 96)
            width_px = int((6.35 / 2.54) * 96)

            # bf 이미지 삽입
            resize_and_insert_image(bf_matched_paths, 'K', 8, ws)

            # af 이미지 삽입
            resize_and_insert_image(af_matched_paths, 'L', 8, ws)

            # 엑셀 파일 저장
            print("Saving Excel file...")
            wb.save(store_path)
            print(f"Excel file saved: {store_path}")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            # 엑셀 파일 닫기


            print("Closing Excel file...")
            try:
                wb.close()
                print("Excel file closed")
            except Exception as e:
                print(f"Error closing Excel file: {e}")

        # 파일 저장 후 다른 접근 시도 여부 확인
        try:
            print("Checking if any file operation is attempted after closing...")
            # 예시로 파일을 다시 열려고 시도합니다.
            # wb = load_workbook(result_path)
            # ws = wb.active
            # print("Excel file re-opened")
        except Exception as e:
            print(f"Error during post-close file operation: {e}")

        print("Script completed.")
if __name__ == "__main__":
    main('aa')