import os
import openpyxl
from datetime import datetime, timedelta
import sqlite3
import yaml
from copy import copy
from collections import defaultdict
from openpyxl.styles import Font, Border, Fill, Protection, Alignment

def load_config(yaml_path):
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
        'send_folder_path': 'C:\\ARGOSRPA\\report\\send_screens\\',
        'db_path': 'C:\\ARGOSRPA\\Master Service\\GeneralService\\modbus.db',
        'report_time_start': report_time_start,
        'report_time_end': report_time_end,
        'report_sendtime': report_sendtime,
        'txt_file_path': 'C:\\ARGOSRPA\\form\\'
    }


def query_db(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results


def copy_cell_style(src_cell, dest_cell):
    dest_cell.font = copy(src_cell.font)
    dest_cell.border = copy(src_cell.border)
    dest_cell.fill = copy(src_cell.fill)
    dest_cell.number_format = copy(src_cell.number_format)
    dest_cell.protection = copy(src_cell.protection)
    dest_cell.alignment = copy(src_cell.alignment)


def main(yaml_path):
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_date = datetime.strptime(current_date_str,"%Y-%m-%d") - timedelta(days=1)
    yesterday_date_str = yesterday_date.strftime("%Y-%m-%d")

    # yaml 파일 정보 가져오기
    config = load_config(yaml_path)
    start_time = config['report_time_start']  # 그대로 'HH:MM' 형식으로 사용
    end_time = config['report_time_end']  # 그대로 'HH:MM' 형식으로 사용
    send_time = config['report_sendtime']

    # 폴더가 없으면 생성
    report_path = config['report_path'] + current_date_str + '\\'
    if not os.path.exists(report_path):
        os.makedirs(report_path)

    xlsx_path = 'C:\\ARGOSRPA\\report\\'+current_date_str+'\\'+current_date_str+'_ARGOS_MDS_Report.xlsx'
    if not os.path.exists(xlsx_path):
        xlsx_path = config['form_path']

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb['Report']
    ws['K2'].value = current_date_str
#     ############################# 임계치 초과 값 입력 시작
    # 리포트 받는 시간이 데이터 수집 시간보다 짧은 경우 리포트 받는 시간에 맞춰서 데이터 조회
    if send_time < end_time:
        query = lambda fields: f"""
                SELECT {fields}
                FROM sensor
                WHERE ((times >= '{yesterday_date_str} {start_time}') AND (times <= '{current_date_str} {send_time}'))
                ORDER BY times ASC;
            """
    elif start_time >= end_time:
        query = lambda fields: f"""
                       SELECT {fields}
                       FROM sensor
                       WHERE ((times >= '{yesterday_date_str} {start_time}') AND (times <= '{current_date_str} {end_time}'))
                       ORDER BY times ASC;
                   """
    else:
        query = lambda fields: f"""
                      SELECT {fields}
                      FROM sensor
                      WHERE ((times >= '{current_date_str} {start_time}') OR (times <= '{current_date_str} {end_time}'))
                      ORDER BY times ASC;
                          """



    # 모든 데이터를 문자열로 변환하고 strip()을 적용
    data = {
        'room_name': query_db(config['db_path'], query('room_name')),
        'sensor_name': query_db(config['db_path'], query('sensor_name')),
        'times': query_db(config['db_path'], query('times')),
        'type': query_db(config['db_path'], query('type')),
        'value': query_db(config['db_path'], query('value'))
    }

# 데이터 처리
    entries = []
    num_entries = len(data['room_name'])
    if num_entries > 0:
        for i in range(num_entries):
            entry = {}
            for key in data.keys():
                value = data[key][i][0]  # 튜플에서 값 추출
                entry[key] = value
            entries.append(entry)

        # 'value' 값이 0보다 큰 항목 필터링
        filtered_entries = [entry for entry in entries if float(entry['value']) > 0]

        i=7
        j=1
        # 각 항목의 데이터를 변수에 저장하고 활용
        if len(filtered_entries)>0:
            for entry in filtered_entries:
                room_name = entry['room_name']
                time = entry['times']
                type_ = entry['type']
                value = entry['value']
                sensor_name = entry['sensor_name']
                if isinstance(sensor_name, int):
                    entry['slave_ids'] = sensor_name - 1
                elif sensor_name == '':
                    pass
                elif isinstance(sensor_name, str):
                    # 쉼표로 나누고 각 요소를 정수로 변환하기 전에 공백을 제거한 후 -1을 적용
                    sensor_name = ','.join([str(int(sid.strip()) - 1) for sid in sensor_name.split(',')])
                # i가 12에 도달하면 행 삽입
                if i == 12:
                    ws.insert_rows(i)

                ###### 엑셀입력
                ##NO
                ws['B'+str(i)].value = j
                ##Time
                ws['C'+str(i)].value = time
                ##Location
                ws['E'+str(i)].value = room_name
                ##ID
                ws['G'+str(i)].value = sensor_name
                ##Type
                ws['I'+str(i)].value = type_
                ##value
                ws['K'+str(i)].value = value
                # 7행의 셀 서식과 행 높이를 현재 행에 복사
                for col in ['B', 'C', 'E', 'F', 'I', 'K']:
                    source_cell = ws[col + '7']
                    target_cell = ws[col + str(i)]
                    target_cell._style = copy(source_cell._style)  # 셀 서식 복사

                # 행 높이 복사
                ws.row_dimensions[i].height = ws.row_dimensions[7].height

                # 7행에서 병합된 셀이 있다면 현재 행에도 병합 적용
                for merged_cell in ws.merged_cells.ranges:
                    if merged_cell.min_row == 7:
                        # 병합 범위를 현재 행으로 이동
                        new_merged_cell = f"{merged_cell.coord.replace('7', str(i))}"
                        ws.merge_cells(new_merged_cell)

                i += 1
                j += 1
        else:
            ##NO
            ws['B' + str(i)].value = '-'
            ##Time
            ws['C' + str(i)].value = '-'
            ##Location
            ws['E' + str(i)].value = '-'
            ##ID
            ws['G' + str(i)].value = '-'
            ##Type
            ws['I' + str(i)].value = '-'
            ##value
            ws['K' + str(i)].value = '-'

    #######################엑셀 통계치 입력시작
    # 리포트 받는 시간이 데이터 수집 시간보다 짧은 경우 리포트 받는 시간에 맞춰서 데이터 조회
    if send_time < end_time:
        query = lambda fields: f"""
            SELECT {fields}
            FROM min_max
            WHERE ((register_time >= '{yesterday_date_str} {start_time}') AND (register_time <= '{current_date_str} {send_time}'))
            ORDER BY register_time ASC;
        """
    elif start_time >= end_time:
        query = lambda fields: f"""
                   SELECT {fields}
                   FROM min_max
                   WHERE ((register_time >= '{yesterday_date_str} {start_time}') AND (register_time <= '{current_date_str} {end_time}'))
                   ORDER BY register_time ASC;
               """
    else:
        query = lambda fields: f"""
                          SELECT {fields}
                          FROM min_max
                          WHERE ((register_time >= '{current_date_str} {start_time}') OR (register_time <= '{current_date_str} {end_time}'))
                          ORDER BY register_time ASC;
                      """

    # 모든 데이터를 문자열로 변환하고 strip()을 적용
    data = {
        'room': query_db(config['db_path'], query('room')),
        'slave_id': query_db(config['db_path'], query('slave_id')),
        'register_time': query_db(config['db_path'], query('register_time')),
        'type': query_db(config['db_path'], query('type')),
        'min_value': query_db(config['db_path'], query('min_value')),
        'max_value': query_db(config['db_path'], query('max_value')),
        'avg_value': query_db(config['db_path'], query('avg_value'))
    }
    # 1단계: 데이터를 딕셔너리의 리스트로 변환
    entries = []
    num_entries = len(data['room'])
    for i in range(num_entries):
        entry = {}
        for key in data.keys():
            value = data[key][i][0]  # 튜플에서 값을 추출
            entry[key] = value
        entries.append(entry)

    # 2단계: 'room', 'type', 'slave_id'별로 데이터를 그룹화
    grouped_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for entry in entries:
        room = entry['room']
        type_ = entry['type']
        slave_id = entry['slave_id']
        grouped_data[room][type_][slave_id].append(entry)

    # 3단계: 각 room, type, slave_id에 대한 통계 계산, 결과를 'results' 리스트에 저장
    results = []
    for room, types in grouped_data.items():
        for type_, slave_ids in types.items():
            for slave_id, entries_list in slave_ids.items():
                min_values = [float(entry['min_value']) for entry in
                              entries_list]
                max_values = [float(entry['max_value']) for entry in
                              entries_list]
                avg_values = [float(entry['avg_value']) for entry in
                              entries_list]

                min_of_min_values = round(min(min_values), 1)  # 소수점 첫째 자리까지 반올림
                max_of_max_values = round(max(max_values), 1)
                avg_of_avg_values = round(sum(avg_values) / len(avg_values), 1)

                result = {
                    'room': room,
                    'type': type_,
                    'slave_ids': slave_id,  # 각 slave_id별로 처리
                    'min_of_min_values': min_of_min_values,
                    'max_of_max_values': max_of_max_values,
                    'avg_of_avg_values': avg_of_avg_values
                }
                results.append(result)    # Step 4: 엑셀입력
    # 변수에 결과를 저장하고 출력하는 예시
    i = 16
    j = 1
    for result in results:
        room = result['room']
        type_ = result['type']
        slave_ids = result['slave_ids']
        # if isinstance(slave_ids, int):
        #     result['slave_ids'] = slave_ids - 1
        # elif isinstance(slave_ids, str):
        #     # 쉼표로 나누고 각 요소를 정수로 변환하기 전에 공백을 제거한 후 -1을 적용
        #     slave_ids = ','.join([str(int(sid.strip()) - 1) for sid in slave_ids.split(',')])


        min_value = result['min_of_min_values']
        max_value = result['max_of_max_values']
        avg_value = result['avg_of_avg_values']
        # NO값
        ws['B'+str(i)].value = j
        #Location
        ws['C'+str(i)].value = str(room)
        #ID
        ws['D'+str(i)].value = str(slave_ids)
        #Type
        ws['E'+str(i)].value = str(type_)
        #Min
        ws['G'+str(i)].value = str(min_value)
        # Max
        ws['I' + str(i)].value = str(max_value)
        # AVG
        ws['K'+ str(i)].value = str(avg_value)

        # 16행의 셀 서식을 복사하여 현재 행의 셀에 적용
        for col in ['B', 'C', 'D', 'E', 'G', 'I', 'K']:
            source_cell = ws[col + '16']
            target_cell = ws[col + str(i)]

            # 셀 스타일 복사
            target_cell._style = copy(source_cell._style)

        # 행 높이 복사
        ws.row_dimensions[i].height = ws.row_dimensions[16].height

        # 16행에서 병합된 셀이 있다면 현재 행에도 병합 적용
        for merged_cell in ws.merged_cells.ranges:
            if merged_cell.min_row == 16:
                # 병합 범위를 현재 행으로 이동
                new_merged_cell = f"{merged_cell.coord.replace('16', str(i))}"
                ws.merge_cells(new_merged_cell)

        i+=1
        j+=1

        # 행 높이도 복사 (필요한 경우)
        ws.row_dimensions[i].height = ws.row_dimensions[16].height
    xlsx_path = 'C:\\ARGOSRPA\\report\\' + current_date_str + '\\' + current_date_str + '_ARGOS_MDS_Report.xlsx'
    wb.save(xlsx_path)
############일주일치에 대한 값 가져오기
    ##어제날짜를 기준으로 일요일부터~토요일까지의 값
    yesterday = datetime.now() - timedelta(days=1)
    start_of_week = (yesterday - timedelta(days=yesterday.weekday() + 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb['Report']

    #location, id, type 가져오기
    row = 16
    while ws[f'C{row}'].value is not None:
        room = ws[f'C{row}'].value
        slave_id = ws[f'D{row}'].value
        type_ = ws[f'E{row}'].value
    # DB에서 지난주 데이터 가져오는 쿼리

        query = f"""
            SELECT 
            Min(min_value) AS min_value, 
            Max(max_value) AS max_value,
            Avg(avg_value) AS avg_value
            FROM min_max
            WHERE room = '{room}' AND slave_id = '{slave_id}' AND type = '{type_}'
            AND register_time BETWEEN '{start_of_week}' AND '{end_of_week}';
        """
        data = query_db(config['db_path'], query)

        if data:
            min_values = [float(row[0]) for row in data]
            max_values = [float(row[1]) for row in data]
            avg_values = [float(row[2]) for row in data]

            min_value = min(min_values)
            max_value = max(max_values)
            avg_value = sum(avg_values) / len(avg_values)
            avg_value = round(float(data[0][2]), 1)

            # 'Last week' 컬럼에 값 입력 (예: 열 L이 Last week 컬럼인 경우)
            #Min값
            ws[f'F{row}'].value = min_value
            #Max값
            ws[f'H{row}'].value = max_value
            #Avg
            ws[f'J{row}'].value = avg_value
            #Limit
            if ws[f'E{row}'].value =='temp':
                ws[f'L{row}'].value = str('60')
            elif ws[f'E{row}'].value =='humidity':
                ws[f'L{row}'].value = '-'
            elif ws[f'E{row}'].value =='smoke':
                ws[f'L{row}'].value = str('60')
            else:
                ws[f'L{row}'].value = '0'  # 필요 시 기본값 설정

            # NoneType 오류 방지: L 열과 J 열이 None일 경우 기본값 설정
            limit_value_str = ws[f'L{row}'].value
            if limit_value_str is None or limit_value_str == '-':
                limit_value = 0.0
            else:
                limit_value = float(limit_value_str)

            avg_value_str = ws[f'J{row}'].value
            if avg_value_str is None or avg_value_str == '-':
                avg_value_from_excel = 0.0
            else:
                avg_value_from_excel = float(avg_value_str)

            #Gap
            if ws[f'E{row}'].value == 'humidity':
                ws[f'M{row}'].value = '-'
            else:
                ws[f'M{row}'].value = round(limit_value - avg_value_from_excel, 1)


            # 16행의 셀 서식을 복사하여 현재 행의 셀에 적용
            for col in ['F', 'H', 'J','L','M']:
                source_cell = ws[col + '16']
                target_cell = ws[col + str(row)]
                copy_cell_style(source_cell, target_cell)  # 스타일 복사

            # 행 높이 복사
            ws.row_dimensions[row].height = ws.row_dimensions[16].height

            # 16행에서 병합된 셀이 있다면 현재 행에도 병합 적용
            for merged_cell in ws.merged_cells.ranges:
                if merged_cell.min_row == 16:
                    # 병합 범위를 현재 행으로 이동
                    new_merged_cell = f"{merged_cell.coord.replace('16', str(row))}"
                    ws.merge_cells(new_merged_cell)
            row += 1

    wb.save(xlsx_path)

if __name__ == "__main__":
    main(r'C:\ARGOSRPA\Master Service\GeneralService\ARGOS.yaml')
