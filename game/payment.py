
import random

def get_computer_choice():
    choices = ["가위", "바위", "보"]
    computer_choice = random.choice(choices)
    return computer_choice


def get_user_choice():
    user_choice = input("가위, 바위, 보 중 하나를 선택하세요: ").strip().lower()
    while user_choice not in ["가위", "바위", "보"]:
        print("잘못된 입력입니다. 가위, 바위, 보 중에서 선택하세요.")
        user_choice = input("가위, 바위, 보 중 하나를 선택하세요: ").strip().lower()
    return user_choice


def compare_choices(computer_choice, user_choice):
    if computer_choice == user_choice:
        return "무승부"
    elif (computer_choice == "가위" and user_choice == "보") or \
            (computer_choice == "바위" and user_choice == "가위") or \
            (computer_choice == "보" and user_choice == "바위"):
        return "컴퓨터 승리"
    else:
        return "나의 승리"





def rsp_advanced(games):
        games = games+1

        co = 0
        us = 0
        dr = 0
        for i in range(0,games):
            # 컴퓨터의 선택 생성
            computer_choice = get_computer_choice()
            # 사용자의 선택 받기
            user_choice = get_user_choice()
            # 선택 비교하고 결과 출력1
            result = compare_choices(computer_choice, user_choice)
            if result =='컴퓨터 승리':
                co +=1
            elif result =='나의 승리':
                us +=1
            else:
                dr +=1
            print('가위 바위 보:'+ str(games-1))
            print(f'나: {user_choice}')
            print(f"컴퓨터: {computer_choice}")
            if result =='나의 승리':
                print(f"{games} 번째 판 나의승리!")

        print(f"나의 전적: {us}승 {dr}무 {co}패")
        print(f"컴퓨터의 전적: {co}승 {dr}무 {us}패")



games = int(input("몇판을 진행하시겠습니까?:"))
rsp_advanced(games)


