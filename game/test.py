member_names = ["갑돌이", "갑순이", "을돌이", "을순이", "병돌이", "병순이"]
member_records = [[4,5,3,5,6,5,3,4,1,3,4,5],[2,3,4,3,1,2,0,3,2,5,7,2],
           [1,3,0,3,3,4,5,6,7,2,2,1],[3,2,9,2,3,5,6,6,4,6,9,9],
           [8,7,7,5,6,7,5,8,8,6,10,9],[7,8,4,9,5,10,3,3,2,2,1,3]]






def sales_management(member_names, member_records):
        #평균점수를 담을 리스트
        avg=[]
        # 점수의 평균값 가져오기
        for record in member_records:
            avg.append(sum(record)//len(record))
        #이름과 점수 매칭
        member = {member_names[i]: avg[i] for i in range(len(avg))}
        #오름차순으로 정렬
        member_sort = sorted(member.items(), key=lambda x:x[1])
        #리스트내 마지막 순서와 마지막 순서 전사람을 변수로
        a = len(member_sort)-1
        b = len(member_sort)-2
        #이름만 가져오기
        bonus_one = list(member_sort[a])[0]
        bonus_two = list(member_sort[b])[0]
        interviewr = list(member_sort[0])[0]
        print(f"보너스 대상자 {bonus_one}")
        print(f"보너스 대상자 {bonus_two}")

        print(f'면담 대상자 {interviewr}')





sales_management(member_names,member_records)