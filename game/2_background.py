import pygame

pygame.init() #초기화 (반드시 필요)

#화면 크기설정
screen_width = 480
screen_height = 640
screen = pygame.display.set_mode((screen_width,screen_height))


#화면 타이틀 설정
pygame.display.set_caption("Wanjin Game")#게임이름

#배경이미지 불러오기
background = pygame.image.load(r'C:\work\game\background.png')

#이벤트루프
running = True
while running:
    for event in pygame.event.get(): #어떤이벤트가 발생중인가
        if event.type == pygame.QUIT: #창이 닫히는 이벤트 발생
            running = False #게임이 진행중이아님
    #screen.fill((0, 0, 255))
    screen.blit(background, (0, 0))  # 0,0은좌표 (x,y좌표임) / 배경그리기
    pygame.display.update() #while문을 돌며 게임 화면을 계속 그려주는 거임 반드시 필요
pygame.quit()
