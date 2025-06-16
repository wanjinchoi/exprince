import pandas as pd
import os
import shutil
from copy import copy
import re
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
import xlwings as xw

folder_path= r'C:\〔3〕   내 역 작 업'
settle_form_path = r'C:\〔99〕   rpa_setting\정산\정산원본파일.xlsx'




#수식, 서식 복사한거 한칸 땡기는 함수
def shift_formula_refs_after_row(formula: str, start_row: int, delta: int):
    """
    수식 안의 셀 참조 중, start_row 이상인 행 번호만 delta만큼 이동
    예: start_row=7, delta=-1 => D7→D6, E8→E7 (D6은 그대로)
    """
    def repl(m):
        col = m.group(1)
        row = int(m.group(2))
        if row >= start_row:
            return col + str(row + delta)
        return m.group(0)

    return re.sub(r'(\$?[A-Z]{1,3})(\d+)', repl, formula)



#수식, 서식 복사 함수
def shift_formula_row(formula: str, from_row: int, to_row: int):
    # 셀 참조 중에서 A~Z + from_row 형태의 것을 A~Z + to_row로 바꾼다
    pattern = re.compile(r'(\$?[A-Z]{1,3})(\$?)' + str(from_row) + r'(?!\d)')
    result = pattern.sub(lambda m: m.group(1) + str(to_row), formula)
    #예를 들어 =D6인거를 =D7로 바꾸는것
    return result






################################## 내역틀 만들기 #################################
#경로내에 폴더리스트 가져오기
first_folders = [name for name in os.listdir(folder_path)if os.path.isdir(os.path.join(folder_path, name))]
for i in range(0, len(first_folders)):
    folder_name = first_folders[i]
    #옮길 폴더
    target_dir = os.path.join(folder_path, folder_name)

    # 새로 만들 (정산)파일 경로
    new_file_name = "(정산)" + folder_name + ".xlsx"
    new_file_path = os.path.join(target_dir, new_file_name)

    # 이미 정산파일이 있는지 확인
    if not os.path.exists(new_file_path):
        print(f"\n📁 현재 폴더 처리 중: {folder_name}")
        print(f"📄 원본 경로: {settle_form_path}")
        print(f"📂 복사 대상 폴더: {target_dir}")
        print(f"📁 타겟 폴더 존재 여부: {os.path.exists(target_dir)}")

        try:
            copied_file_path = shutil.copy(settle_form_path, target_dir)
            print(f"📄 복사된 파일 경로: {copied_file_path}")
            if not os.path.isfile(copied_file_path):
                print("❌ 복사된 결과가 파일이 아님 → 건너뜀")
                continue
            os.rename(copied_file_path, new_file_path)
        except Exception as e:
            print(f"❌ 복사 및 이름 변경 실패: {e}")
            continue

    # 0으로 시작하는 엑셀 찾기 (복사하기 위해서)
    excel_files = [f for f in os.listdir(target_dir)if f.lower().endswith('.xlsx') and f.startswith('0')]
    excel_file_path = os.path.join(target_dir, excel_files[0])
    #엑셀 불러오기
    df = pd.read_excel(excel_file_path, engine='openpyxl', header=0)

    # 엑셀 (정산)~~~.xlsx파일 열기
    wb = load_workbook(new_file_path)
    ws = wb['내역서']  # 첫 번째 시트 기준

    #엑셀값 넣기
    #(Z7행부터 넣야되니깐)
    start_row = 7
    for i , row in enumerate(df.values):
        for j, value in enumerate(row):
            ws.cell(row=start_row +i , column=26+j, value = value)

    wb.save(new_file_path)
    wb.close()

    # 데이터길이
    df_len = len(df)

    template_row = 6

    for i in range(df_len):
        target_row = template_row + 1 + i
        for col in range(1, 26):  # A~Y
            src_cell = ws.cell(row=template_row, column=col)
            tgt_cell = ws.cell(row=target_row, column=col)
            # 수식이 걸려있는 행에 숫자를 점진적으로 늘려주기 위해 정규표현식으로 치환
            if isinstance(src_cell.value, str) and src_cell.value.startswith("="):
                formula = src_cell.value
                new_formula = shift_formula_row(formula, template_row,target_row)
                tgt_cell.value = new_formula
            else:
                tgt_cell.value = src_cell.value

            # ✅ 스타일 및 기타 속성 복사 (무조건 수행)
            if src_cell.has_style:
                tgt_cell._style = copy(src_cell._style)
            if src_cell.hyperlink:
                tgt_cell.hyperlink = copy(src_cell.hyperlink)
            if src_cell.comment:
                tgt_cell.comment = copy(src_cell.comment)

    # ✅ 3. 프린트 영역 설정: B3 ~ Y(3 + df_len - 1)
    start_col = get_column_letter(2)  # B
    end_col = get_column_letter(25)  # Y
    start_row = 3
    end_row = start_row + df_len + 2
    ws.print_area = start_col + str(start_row) + ":" + end_col + str(end_row)

    # 6행 삭제 전: 수식에서 참조된 7행 이상을 전부 1 줄임 (D7→D6, D8→D7, ...)
    for row in ws.iter_rows(min_row=7, max_row=ws.max_row, max_col=25):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.startswith("="):
                cell.value = shift_formula_refs_after_row(cell.value, start_row=7, delta=-1)
    # 6행삭제
    ws.delete_rows(6)
    ws['C3'].value = folder_name
    wb.save(new_file_path)
    wb.close()
    print("처리 완료: " + new_file_path)

##########################서식복사###########################################
    print("서식복사 시작: " + new_file_path)
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter
    from copy import copy
    import os

    # 수식 복사
    # 수식 내부 참조 보정 함수

    # 기존 데이터행: 모든 참조를 해당 행 기준으로 바꿈
    def shift_cell_refs(formula, new_row):
        return re.sub(r'\b([A-Z]{1,3})([0-9]{1,7})\b',lambda m: m.group(1) + str(new_row), formula)


    def shift_insert_cell_refs_from_index(formula: str, current_row: int,index: int) -> str:
        target_row = index + (current_row - (index + 1))
        return re.sub(r'\b([A-Z]{1,3})([0-9]{1,7})\b',lambda m: m.group(1) + str(target_row),formula)

    def shift_Q_O_cell_content(formula,now_row):
        return re.sub(r'\b([A-Z]{1,3})([0-9]{1,7})\b',lambda m: m.group(1) + str(now_row), formula)

    wb = load_workbook(new_file_path, data_only=False)
    ws = wb["내역서"]
    ws_template = wb["서식복사"]

    first_max_row = ws.max_row

    # 23행 넣기
    for base_row in range(ws.max_row, 5, -1):
        insert_row = base_row + 1
        ws.insert_rows(insert_row, amount=8)
        for i in range(8):
            for col in range(1, 66):
                src = ws_template.cell(row=insert_row + i, column=col)
                tgt = ws.cell(row=insert_row + i, column=col)
                tgt.value = src.value
                tgt._style = copy(src._style)

    # 서식바꾸기
    n = ws.max_row
    sequence_values= []
    #등차 수열로 6부터 +9씩 값들 가져오기
    for i in range(1, n + 1):
        value = 6 + (i - 1) * 9
        if value <= ws.max_row:
            sequence_values.append(value)
        else:
            break
    # 6을 제외한 수열 값 구하기
    sequence_values_excluded_6 = sequence_values[1:]

    for j in range(len(sequence_values_excluded_6)):
        index = sequence_values_excluded_6[j]
        #삽입 후 기존 데이터행 바꾸기
        for i in range(1,66):
            tgt_cell = ws.cell(row =index, column=i)
            if isinstance(tgt_cell.value, str) and  tgt_cell.value.startswith("="):
                updated_formula = shift_cell_refs(tgt_cell.value, index)
                tgt_cell.value = updated_formula

        #삽입 후 삽입행 서식 바꾸기
        for z in range(index+1, index + 9):
            for y in range(1,66):
                tgt_cell2 = ws.cell(row=z, column=y)
                if isinstance(tgt_cell2.value,str) and tgt_cell2.value.startswith("="):
                    updated_formula2 = shift_insert_cell_refs_from_index(tgt_cell2.value, z, index)
                    tgt_cell2.value = updated_formula2
        #Q행부터 바꾸기
        for q in range(index+1, index + 9):
            for w in range(17,26):
                tgt_cell3 = ws.cell(row = q, column=w)
                if isinstance(tgt_cell2.value,str) and tgt_cell2.value.startswith("="):
                    updated_formula3 = shift_Q_O_cell_content(tgt_cell3.value,q)
                    tgt_cell3.value = updated_formula3


    wb.save(new_file_path)
    wb.close()
    # ✅ 인쇄영역 설정
    ws.print_area = "B3:Y" + str(ws.max_row)

    wb.save(new_file_path)
    wb.close()

    ######### 접수일련번호 -> 접수일련버호 일치 폴더찾기(해당폴더안의 폴더갯수로 수량파악) -> 단가표 찾기 -> 해당내용가져오기
    print("단가표에서 가져와서 입력시작")
    try:
        # 엑셀 앱 숨김으로 실행
        app = xw.App(visible=False)

        # 워크북 열기
        wb = app.books.open(new_file_path, update_links=False, read_only=False)

        # 시트 선택
        ws = wb.sheets['내역서']
        last_row = ws.range('C' + str(ws.cells.rows.count)).end('up').row
        # C열 값 가져오기
        range_add = 'C6' +':C'+ str(last_row)
        c_values = ws.range(range_add).value

        # 중복 제거 + None 제거
        #접수일련번호
        unique_values = list(dict.fromkeys(v for v in c_values if v is not None))
        print(unique_values)
        results = []

        for val in unique_values:
            # target_dir 안에서 폴더 리스트 가져오기
            subfolders = [name for name in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, name))]
            for folders in subfolders:
                #새 파일 경로
                new_targer_dit_path = os.path.join(target_dir,folders)
                #val과 매치 폴더 찾기
                matched_folders = [name for name in os.listdir(new_targer_dit_path) if os.path.isdir(os.path.join(new_targer_dit_path, name)) and val in name]
                if matched_folders:
                    print("해당폴더찾음")
                    # 매치된 폴더 경로
                    real_new_target_path = os.path.join(new_targer_dit_path,matched_folders[0])
                    subfolders2 = [name for name in os.listdir(real_new_target_path) if os.path.isdir(os.path.join(real_new_target_path, name))]
                    #대분류 없으면
                    if len(subfolders2) == 0:
                        folder_count =1

                    for c in subfolders2:
                        y = real_new_target_path + '\\' + c
                        #중분류
                        subfolders3 = [name for name in os.listdir(y) if os.path.isdir(os.path.join(y, name))]
                        #중분류없으면
                        if len(subfolders3) == 0:
                            folder_count =1
                        else:
                            for t in subfolders3:
                                last_path = os.path.join(y,t)
                                #소분류 폴더갯수
                                subfolders4 = [name for name in os.listdir(last_path) if os.path.isdir(os.path.join(last_path, name))]
                                if len(subfolders4) ==0:
                                    folder_count = 1
                                else:
                                    folder_count = len(subfolders4)
                                if '건설' in last_path:
                                    results.append([val, folder_count, t, '건설'])
                                else:
                                    results.append([val, folder_count,t, '매입'])

                    break

        conv_path = r'C:\〔99〕   rpa_setting\정산\중요원본파일.xlsx'
        # 엑셀 파일 열기
        wb_conv = app.books.open(conv_path)
        # 결과 출력
        for r in results:
            #접수일련번호
            input_num = r[0]
            #수량
            count = r[1]
            #명칭
            subfolder_names_list = r[2]
            cleaned = re.sub(r'^[\d\s]+', '', subfolder_names_list)
            #시트명
            tag = r[3]

            # 중복 여부 확인: C열에서 접수번호 찾고, 그 다음 줄의 I열 값이 None인지 확인
            last_row_check = ws.range('C' + str(ws.cells.rows.count)).end('up').row
            skip = False
            for i in range(6, last_row_check + 1):
                val = ws.range('C' + str(i)).value
                if str(val) == str(input_num):
                    if ws.range((i + 1, 9)).value == cleaned:
                        print("I열에 이미 값 존재:" +input_num + cleaned+"→ 건너뜀")
                        skip = True
                    break
            if skip:
                continue  # 다음 접수일련번호로 넘어감


            ws_conv = wb_conv.sheets[tag]
            try:
                final_data = []
                last_row_conv = ws_conv.range('E' + str(ws_conv.cells.rows.count)).end('up').row
                for row in range(8, last_row_conv + 1):
                    val = ws_conv.range((row, 5)).value  # E열 (index 4)
                    if isinstance(val, str) and cleaned in val:
                        row_data = ws_conv.range((row, 9), (row, 16)).value  # I~P열

                        # 스타일 복사용 셀
                        src_cell_j = ws_conv.range((row, 10))  # J열
                        src_cell_k = ws_conv.range((row, 11))  # K열

                        final_data.append({
                            'data': row_data,
                            'style_J': src_cell_j,
                            'style_K': src_cell_k,
                        })
                        break  # 매칭되는 첫 행만 추출


                if not final_data:  # 만약 final_data가 비어있다면 (매칭이 없으면)
                    print("매칭되지 않은 접수일련번호:" + input_num)
                    # 비어있으면 명칭넣기
                    last_row = ws.range('C' + str(ws.cells.rows.count)).end('up').row
                    found = False
                    for i in range(6, last_row + 1):
                        val = ws.range('C' + str(i)).value
                        if str(val) == str(input_num):
                            f_index = i + 1
                            x=2
                            while True:
                                if ws.range('I' + str(f_index)).value is None:
                                    break
                                x += 1
                                f_index +=1
                            found=True
                            break

                    # 수량
                    ws.range((f_index, 16)).value = count
                    print("수량넣기")
                    ws.range((f_index,9)).value = cleaned
                    print("명칭넣기")
                    wb.save()
                    continue  # 다음 접수일련번호로 넘어갑니다.
                print(final_data)
                last_row = ws.range('C' + str(ws.cells.rows.count)).end('up').row
                foune= False
                for i in range(6, last_row + 1):
                    val = ws.range('C' + str(i)).value
                    if str(val) == str(input_num):
                        f_index = i + 1
                        x = 2
                        while True:
                            if ws.range('I' + str(f_index)).value is None:
                                break
                            x += 1
                            f_index +=1
                        found = True
                        break
                # 단가코드 넣기
                ws.range((f_index, 8)).value = final_data[0]['data'][0]
                print("단가코드넣기")
                # 단위 넣기
                if final_data[0]['data'][3] is None:
                    ws.range((f_index, 11)).value = ''
                    print("단위 넣기")
                else:
                    ws.range((f_index, 11)).value = final_data[0]['data'][3]

                # 자재비
                if final_data[0]['data'][4] is None:
                    ws.range((f_index, 12)).value =''
                else:
                    ws.range((f_index, 12)).value = final_data[0]['data'][4]
                print("자재비넣기")
                # 인건비
                if final_data[0]['data'][5] is None:
                    ws.range((f_index, 13)).value=''
                else:
                    ws.range((f_index, 13)).value = final_data[0]['data'][5]
                print("인건비넣기")
                if final_data[0]['data'][6] is None:
                    ws.range((f_index, 13)).value = ''
                else:
                    # 경비
                    ws.range((f_index, 14)).value = final_data[0]['data'][6]
                print("경비넣기")
                if final_data[0]['data'][7] is None:
                    ws.range((f_index, 15)).value= ''
                else:
                    # 합계
                    ws.range((f_index, 15)).value = final_data[0]['data'][7]
                print("합계넣기")
                # 수량
                ws.range((f_index, 16)).value = count
                print("수량넣기")
                # 단가명 스타일 복사 (style_J -> 9열)
                src_cell_j = final_data[0]['style_J']
                dst_cell_j = ws.range((f_index, 9))
                dst_cell_j.value = final_data[0]['data'][1]
                dst_cell_j.api.Font.Name = src_cell_j.api.Font.Name
                dst_cell_j.api.Font.Size = src_cell_j.api.Font.Size
                dst_cell_j.api.Font.Bold = src_cell_j.api.Font.Bold
                dst_cell_j.api.Interior.Color = src_cell_j.api.Interior.Color
                dst_cell_j.api.NumberFormat = src_cell_j.api.NumberFormat
                dst_cell_j.api.HorizontalAlignment = src_cell_j.api.HorizontalAlignment
                dst_cell_j.api.VerticalAlignment = src_cell_j.api.VerticalAlignment
                for b in range(1, 5):
                    dst_cell_j.api.Borders(b).LineStyle = src_cell_j.api.Borders( b).LineStyle

                # 규격 스타일 복사 (style_K -> 10열)
                src_cell_k = final_data[0]['style_K']
                dst_cell_k = ws.range((f_index, 10))
                dst_cell_k.value = final_data[0]['data'][2]
                dst_cell_k.api.Font.Name = src_cell_k.api.Font.Name
                dst_cell_k.api.Font.Size = src_cell_k.api.Font.Size
                dst_cell_k.api.Font.Bold = src_cell_k.api.Font.Bold
                dst_cell_k.api.Interior.Color = src_cell_k.api.Interior.Color
                dst_cell_k.api.NumberFormat = src_cell_k.api.NumberFormat
                dst_cell_k.api.HorizontalAlignment = src_cell_k.api.HorizontalAlignment
                dst_cell_k.api.VerticalAlignment = src_cell_k.api.VerticalAlignment
                for b in range(1, 5):
                    dst_cell_k.api.Borders(b).LineStyle = src_cell_k.api.Borders(b).LineStyle
                wb.save()
            except Exception as e:
                print("행", r, "에서 에러 발생:", e)
        last_row = ws.range('C' + str(ws.cells.rows.count)).end('up').row
        for r in range(6, last_row + 1):
                ws.range(str(r) + ":" + str(r)).row_height = 20
    except Exception as e:
        print("전체 try 블록에서 예외 발생:", e)
    finally:
        wb.save()
        wb.close()
        app.quit()