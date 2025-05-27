import openpyxl
import re
import datetime
from datetime import datetime
from dateutil.relativedelta import relativedelta



today = datetime.today()
today_date=today.strftime('%d-%B-%Y')



def main(change_xlsx):
    #엑셀읽기
    wb = openpyxl.load_workbook(change_xlsx)
    ws = wb.active
    #===========================Qute Details 정보가져오기 ================================
    #검색을 위한 Ref번호가져오기 -0번
    ref = ws['A14'].value
    ref_no = ref.replace('CUSTOMER NO. ', '')

    ##Quote Reference - 1번
    quo = ws['D12'].value
    quo_no = quo.replace('QUOTATION NO. ','')

    #Prices good until: 30 Days면 다음달 동일 일자로 - 2번
    validity = ws['D15'].value
    v_date = validity.replace('VALIDITY ','')
    v_date = v_date.replace(' DAYS','')
    v_date = v_date.replace(' DAYS','')
    after = today + relativedelta(days=int(v_date))
    a_day = after.strftime('%B')

    year = after.year
    month = after.month
    day = after.day
    q = after.strftime('%Y,%m,%d')
    first_day = datetime.strptime(q, '%Y,%m,%d')
    #해당 요일 index값 구하기
    first_day_weekday = first_day.weekday()
    #해당주차 구하기
    week_number = (day + ((first_day_weekday + 1) % 7) - 1) // 7 + 1
    week = str(week_number)
    if first_day_weekday == 6:
        first_day_weekday = '1'
    else:
        first_day_weekday = str(first_day_weekday+2)

    # dayment = day.main(v_date)
    #Offered Quaility- 3번
    qf= ws['A20'].value
    qf_Q = qf.replace('**OFFERED SOURCE  :  ','')

    #Delivery Time // 4번
    dt = ws['A17'].value
    if "KOREA" in dt:
        dt_cmm ='nothing'
        dt_t = dt.replace('DELIVERY TERMS ','')
        dt_t = dt_t.replace(',', '')
        dt_t = dt_t.split(' ')
    else:
        #코멘트 입력을 위해
        dt_cmm = dt.replace('DELIVERY TERMS ', '')
        dt_t = dt.replace('DELIVERY TERMS ', '')
        dt_cmm = dt_t.replace(',', '')
        dt_t = dt_t.replace(', ', ' ')
        dt_t = dt_t.split(' ')
    if 'EXW' in dt_t[0]:
        dt_h = dt_t[0]
        dt_l = dt_t[1]
    elif 'FCA' in dt_t[0]:
        dt_h= dt_t[0]
        dt_l = dt_t[1]

    #Quoted Delivery // 5번
    lead_time = ws['A16'].value
    num = re.findall(r'\d+', lead_time)
    l_num = num[0]
    ## PAYMET TERMS
    pay_day = ws["A18"].value
    day = re.findall(r'\d+', pay_day)
    p_num = day[0]


    wb.close()
    a=[]
    a.append(ref_no)
    a.append(quo_no)
    a.append(a_day)
    a.append(week)
    a.append(first_day_weekday)
    a.append(qf_Q)
    a.append(dt_h)
    a.append(dt_l)
    a.append(dt_cmm)
    a.append(l_num)
    a.append(p_num)

    x = ','.join(a)


    print(x)


if __name__ == "__main__":
    main('C:\\Users\\vivans\\Desktop\\제출전\\ZN231227006.xlsx')

