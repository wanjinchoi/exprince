import openpyxl
import os
from datetime import datetime
import glob


###2025.02.04 office mode를 엑셀에 추가해달라는 요청에 따라 코드 추가
### 2025.03.04 office mode가 none이 아니라 ''이어서 = 가 계속입력되는 문제가 발생함에 따라 elif문으로 코드 수정


#template_path = 'C:\\work\\LDC\\form.xlsx'
#result_path ='C:\\work\\LDC\\p_result.xlsx'
today = datetime.today()
fileday = today.strftime('%Y%m%d')

# template_path = 'C:\\work\\LDC\\form.xlsx'
# result_path ='C:\\work\\LDC\\p_result.xlsx'
# file_path = 'C:\\work\\LDC\\예시excel파일\\'



template_path = 'C:\\ArgosRPA\\form\\form.xlsx'
result_path ='C:\\ArgosRPA\\porcure\\result\\p_result.xlsx'
file_path = 'C:\\ArgosRPA\\porcure\\'+fileday+'\\'


def main(procurse):
    #수정날짜 순으로 정리
    flist = sorted(glob.glob(file_path + '*.xlsx'), key=os.path.getmtime)
    r_len = len(flist) - 1
    r_file = flist[r_len]
    #가공할 엑셀파일 가져오기
    wb_p = openpyxl.load_workbook(r_file)
    ws_p = wb_p.active
    # 옮길 양식 에셀 파일 가져오기
    wb_fm = openpyxl.load_workbook(template_path)
    ws_fm = wb_fm.active

    # 최대열 구하기
    c_max_row = max((a.row for a in ws_p['C'] if a.value is not None))
    #원본파일 15행부터 있기 때문에 15행부터 시작
    for i in range(15, c_max_row+1):
        d_max_row = max((a.row for a in ws_fm['D'] if a.value is not None))
        if type(ws_p['B'+str(i)].value) == str:
            pass
        elif ws_p['B'+str(i)].value is None:
            pass
        else:
            #Line
            ws_fm['A' + str(d_max_row + 1)].value = ws_p['B' + str(i)].value
            #part no
            ws_fm['C' + str(d_max_row + 1)].value = ws_p['F' + str(i)].value
            ## 엑셀 16행 17행 정보 가져오기
        if ('Equipment' in str(ws_p['B' + str(i)].value)) and('Assembly' in str(ws_p['B' + str(i+1)].value)):
            below = ws_p['B' + str(i)].value+'@, '+ws_p['B' + str(i+1)].value+'@'
            q = below.replace('Equipment:-,', '').replace('Maker:-,', '').replace('Model:,', '').replace('Serial No:,','').replace('Book No:,', '').replace('Drawing No.: ,', '').replace('  ', ' ').replace('Equipment:,', '').replace('Maker:,', '')
            q = q.replace('Assembly: ,', '').replace('Maker: ,', '').replace('Model: ,', '').replace('Assembly Particulars: @', '').replace('Assembly Particulars: -,-', '').replace('Equipment Particulars:Particulars :  ','').replace(' Equipment Particulars:Particulars :','').replace('Maker: ,','').replace('Model: ,','').replace('Assembly Particulars: @','')
            if ('Equipment Particulars:@,' in q) or ('Equipment Particulars:-,-' in q):
                q = q.replace('Equipment Particulars:@,', '').replace('Equipment Particulars:-,-', '')
            below2 = q.replace('\n', ' ').replace('@', '')
            below3 = below2.replace('\0', '')
            below4 = below3.replace('\r', '')
            below5 = below4.replace('\t', ' ')
            y = len(below5)
            if y == '0':
                pass
            else:
                if ',' in below5[y - 5:y]:
                    below5 = below5.strip()
                    below5 = below5.rstrip(',')
            if below5 == '    ':
                pass
            else:
                if d_max_row+1 == 2:
                    ws_fm['B'+str(d_max_row+1)].value = '+'
                else:
                    ws_fm['B' + str(d_max_row + 1)].value = '-'
                if len(below5) > 250:
                    under = below5[0:250]
                    over = below5[250:]
                    ws_fm['D'+str(d_max_row+1)].value = under
                    ws_fm['B'+str(d_max_row+2)].value = '-'
                    ws_fm['D'+str(d_max_row+2)].value = over
                else:
                    ws_fm['D'+str(d_max_row+1)].value = below5
            wb_fm.save(result_path)

        else:
            #품명이있는지없는 지 검토
            a = ws_p['C' + str(i)].value
            if a is None:
                pass
            else:
                # 옮길행 최대열 구하기
                a_max_row = max((a.row for a in ws_fm['D'] if a.value is not None))
                # 품명에 띄어쓰기 없애기

                b = a.replace('\n', ' ')
                c = b.replace('\0', '')
                d = c.replace('\r', '')
                e = d.replace('\t', ' ')
                #Drawing NO가 None이면
                if (ws_p['H' + str(i)].value is None) or (ws_p['H' + str(i)].value =='') :
                    ws_fm['D' + str(a_max_row + 1)].value = e
                    ws_fm['E' + str(a_max_row + 1)].value = ws_p['I' + str(i)].value
                    ws_fm['F' + str(a_max_row + 1)].value = ws_p['J' + str(i)].value
                    #office Nonte가 None이면
                    if (ws_p['D'+str(i)].value) is None or ws_p['D'+str(i)].value =='' :
                        pass
                    # office nonte에 내용이 없어도 None가 아니라  ''로 표기됨
                    elif ws_p['D'+str(i)].value =='':
                        pass
                    else:
                        # 폼 양식 아랫칸에 =을 넣고 그다음 행에 office note값 넣기 D열이 office notes임
                        ws_fm['B'+str(a_max_row+2)].value = '='
                        ws_fm['D'+str(a_max_row+2)].value = ws_p['D'+str(i)].value
                        wb_fm.save(result_path)
                else:
                    #품명넣기
                    ws_fm['D' + str(a_max_row + 1)].value = e +',' +ws_p['H' + str(i)].value
                    ws_fm['E' + str(a_max_row + 1)].value = ws_p['I' + str(i)].value
                    ws_fm['F' + str(a_max_row + 1)].value = ws_p['J' + str(i)].value
                    if (ws_p['D'+str(i)].value) is None :
                        pass
                    elif ws_p['D'+str(i)].value =='':
                        pass
                    else:
                        # 폼 양식 아랫칸에 =을 넣고 그다음 행에 office note값 넣기 D열이 office notes임
                        ws_fm['B'+str(a_max_row+2)].value = '='
                        ws_fm['D'+str(a_max_row+2)].value = ws_p['D'+str(i)].value
                        wb_fm.save(result_path)
            wb_fm.save(result_path)

    purchasename = ws_p['B5'].value
    vesselname = ws_p['k6'].value
    refno = ws_p['H5'].value
    return (purchasename, vesselname, refno)








if __name__ == "__main__":
    main('aa')

