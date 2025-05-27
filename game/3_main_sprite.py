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

#스프라이트(캐릭터) 불러오기
character = pygame.image.load(r'C:\work\game\character.png')
#캐릭터움직임 구현
character_size = character.get_rect().size  # 이미지의 크기를 구해옴
character_width = character_size[0] # 캐릭터의 가로크기
character_height = character_size[1]  #캐릭터의 세로크기
#캐릭터의 좌표
character_x_pos = (screen_width / 2) -(character_width / 2) #화면 가로의 절반 크기에 해당하는 곳에 위치
character_y_pos = screen_height - character_height  #화면 세로 크기 가장 아래에 해당하는 곳에 위치

#이벤트루프
running = True
while running:
    for event in pygame.event.get(): #어떤이벤트가 발생중인가
        if event.type == pygame.QUIT: #창이 닫히는 이벤트 발생
            running = False #게임이 진행중이아님

    screen.blit(background, (0, 0))  # 0,0은좌표 (x,y좌표임) / 배경그리기
    screen.blit(character,(character_x_pos, character_y_pos))
    pygame.display.update() #while문을 돌며 게임 화면을 계속 그려주는 거임 반드시 필요
pygame.quit()
