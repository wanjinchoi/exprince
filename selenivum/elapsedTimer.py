import time

class ElapsedTimer:
    def __init__(self):
        # 객체 생성 시 현재 시간을 시작 시간으로 설정
        self.start_time = time.time()

    def elapsed(self):
        # 현재 시간과 시작 시간의 차이를 밀리초로 반환
        end_time = time.time()
        # elapsed_time = (end_time - self.start_time) * 1000  # 초를 밀리초로 변환
        elapsed_time = (end_time - self.start_time) # 초
        return elapsed_time

"""
# 사용 예시
timer = ElapsedTimer()  # 타이머 시작
# ... 여기에 시간을 측정하고자 하는 코드를 실행 ...
elapsed_time = timer.elapsed()  # 실행 시간 측정
print(f"Elapsed time: {elapsed_time} ms")
"""