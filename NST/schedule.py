import datetime

def main(checklist):
   ####2024/06/27
   ## 09시 10분 / 3:30분에 선일 시나리오 돌게해달라고 연락옴 그래서 선일은 제외


    # 현재 시간을 구합니다.
    current_time = datetime.datetime.now().time()

    # 각 시간대에 따라 조건을 확인합니다.
    #태양
    if datetime.time(8, 30) <= current_time < datetime.time(8, 50):
        return 1
    #선일
    # elif datetime.time(8, 55) <= current_time < datetime.time(9, 30):
    #     return 2
    #영신
    elif datetime.time(9, 30) <= current_time < datetime.time(10, 30):
        return 3
    #청우
    elif datetime.time(12, 0) <= current_time < datetime.time(14, 0):
        return 4
    #경민
    elif datetime.time(14, 5) <= current_time < datetime.time(15, 30):
        return 5
    #선일
    # elif datetime.time(15, 30) <= current_time < datetime.time(17, 30):
    #     return 6
    else:
        # 주어진 시간대 외의 시간에는 None을 반환합니다.
        return None
if __name__ == "__main__":
        main('aa')