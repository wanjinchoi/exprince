


def check_id(a):
    if len(a) !=14:
        print("잘못된 번호입니다.\n올바른 번호를 넣어주세요")
    y = a[:2]
    m = a[2:4]
    sex = a[7:8]
    if sex == '2' or '4':
        human = "여자"
    else:
        human= '남자'


    if y =='00':
        ox = input('2000년 이후 출생자 입니까? 맞으면 o 아니면 x : ')

        if ox =='o':
            if sex !='4':
                print("잘못된 번호입니다.\n올바른 번호를 넣어주세요")
            else:
                print('20' + y + '년' + m + '월' + human)
        else:
            print('19' + y + '년' + m + '월' + human)
    else:
        print('19'+y+'년'+m+'월'+human)












a= input('주민번호를 입력하세요.(ex)230807-1234567): ')

check_id(a)

