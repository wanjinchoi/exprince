info = "abc,21세,010-1234-5678,남자,서울,5,cdb,25세,x,남자,서울,4,bbc,30세,010-2222-3333,여자,서울,3,ccb,29세,x,여자,경기,9,dab,26세,x,남자,인천,8,aab,23세,010-3333-1111,여자,경기,10"



def good_customer(info):
    a = info.split(',')
    r = []
    id = []
    age = []
    phone = []
    gender = []
    location = []
    purchase = []
    #정보의 index가 6개씩 끊어지므로 6개씩 끊어 담는다.
    for i in range(0,len(a),6):
        r.append(a[i:i+6])
    #담은 정보들을 종류별로 세분화 해준다.
    for i in range(len(r)):
        id.append(r[i][0])
        age.append(r[i][1])
        phone.append(r[i][2])
        gender.append(r[i][3])
        location.append(r[i][4])
        purchase.append(r[i][5])

    #각각의 특징에 맞게 딕셔너리로 전환 해준다.
    di = dict()
    di['아이디'] =id
    di['나이'] =age
    di['전화번호']=phone
    di['성별']=gender
    di['지역']=location
    di['구매횟수'] =purchase

    # 값 비교를 위해 string 타입의 purchase를 int타입으로 변환
    int_purchase = list(map(int, purchase))
    #아이디에 맞춰서 값을 가져오기 위해 각각 아이디와 묶어준다
    id_pur = {k: v for k, v in zip(id, int_purchase)}
    id_age = {k: v for k, v in zip(id, age)}
    id_phone = {k: v for k, v in zip(id, phone)}
    id_gender = {k: v for k, v in zip(id, gender)}
    id_location = {k: v for k, v in zip(id, location)}
    print(di)
    # 8회 이상 찾기 위해 내림차순으로 정렬
    f_good_customer= sorted(id_pur.items(), key=lambda x:x[1], reverse=True)
    #듀플 형식으로 값이 8이상인 것들을 찾는다
    for gcid in f_good_customer:
        if gcid[1] >=8:
            id = gcid[0]
            print(f'할인 쿠폰을 받을 회원정보 아이디:{id}, 나이 : {id_age[id]}, 전화번호: {id_phone[id]}, 성별: {id_gender[id]}, 지역: {id_location[id]}, 구매횟수: {id_pur[id]}')




good_customer(info)