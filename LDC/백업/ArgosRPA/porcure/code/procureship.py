import openpyxl
import os
from datetime import datetime
import glob

#template_path = 'C:\\work\\LDC\\form.xlsx'
#result_path ='C:\\work\\LDC\\p_result.xlsx'
today = datetime.today()
fileday = today.strftime('%Y%m%d')

template_path = 'C:\\ArgosRPA\\form\\form.xlsx'
result_path ='C:\\ArgosRPA\\porcure\\result\\p_result.xlsx'
file_path = 'C:\\ArgosRPA\\porcure\\'+fileday+'\\'


def main(procurse):
    #수정날짜 순으로 정리
    flist = sorted(glob.glob(file_path + '*.xlsx'), key=os.path.getmtime)
    r_len = len(flist) - 1
    r_file = flist[r_len]
    wb_p = openpyxl.load_workbook(r_file)
    ws_p = wb_p.active
    wb_fm = openpyxl.load_workbook(template_path)
    ws_fm = wb_fm.active

    below = ws_p['B16'].value + ws_p['B17'].value
    below2 = below.replace('\n',' ')
    below3 = below2.replace('\0', '')
    below4 = below3.replace('\r', '')
    below5 = below4.replace('\t', ' ')


    ws_fm['B2'].value='+'
    if len(below5)> 250:
        under = below5[0:250]
        over = below5[250:]
        ws_fm['D2'].value = under
        ws_fm['B3'].value = '+'
        ws_fm['D3'].value = over
    else:
        ws_fm['D2'].value =below5

    wb_fm.save(result_path)
    c_i = max((a.row for a in ws_p['C'] if a.value is not None))
    for i in range(18, c_i+1):
        a_i = max((a.row for a in ws_fm['D'] if a.value is not None))
        if type(ws_p['B'+str(i)].value) == str:
            pass
        else:
            ws_fm['A' + str(a_i + 1)].value = ws_p['B' + str(i)].value
            ws_fm['C' + str(a_i + 1)].value = ws_p['F' + str(i)].value
        if 'Equipment' in str(ws_p['B' + str(i)].value):
            d_i = max((a.row for a in ws_fm['D'] if a.value is not None))
            elow = ws_p['B'+str(i)].value + ws_p['B'+str(i+1)].value
            elow2 = elow.replace('\n', ' ')
            elow3 = elow2.replace('\0', '')
            elow4 = elow3.replace('\r', '')
            elow5 = elow4.replace('\t', ' ')
            ws_fm['B'+str(d_i+1)].value = '-'
            if len(below5) > 250:
                under2 = elow5[0:250]
                over2 = elow5[250:]
                ws_fm['D'+str(d_i+1)].value = under2
                ws_fm['B'+str(d_i+2)].value = '-'
                ws_fm['D'+str(d_i+2)].value = over2
            else:
                ws_fm['D'+str(d_i+1)].value = elow5
            wb_fm.save(result_path)

        else:
            a = ws_p['C' + str(i)].value
            if a is None:
                pass
            else:
                a_i = max((a.row for a in ws_fm['D'] if a.value is not None))
                b = a.replace('\n', ' ')
                c = b.replace('\0', '')
                d = c.replace('\r', '')
                e = d.replace('\t', ' ')
                if ws_p['H' + str(i)].value is None:
                    ws_fm['D' + str(a_i + 1)].value = e
                else:
                    ws_fm['D' + str(a_i + 1)].value = e +',' +ws_p['H' + str(i)].value
                    ws_fm['E' + str(a_i + 1)].value = ws_p['I' + str(i)].value
                    ws_fm['F' + str(a_i + 1)].value = ws_p['J' + str(i)].value
            wb_fm.save(result_path)

    purchasename = ws_p['B5'].value
    vesselname = ws_p['k6'].value
    refno = ws_p['H5'].value
    return purchasename, vesselname, refno







if __name__ == "__main__":
    main('aa')

