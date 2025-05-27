import cv2
import os
from datetime import datetime


def main(checklist):
    current_date_str = datetime.now().strftime("%Y-%m-%d")

    # PNG 파일이 있는 폴더 경로 설정
    png_folder_path = r'C:\Users\vivans\Desktop\store_screens\2024-02-27'

    # 저장할 영상 파일 경로 및 이름 설정 (확장자에 따라 다른 형식을 선택할 수 있습니다. 예: .mp4, .avi)
    output_video_path = r'C:\Users\vivans\Desktop\store_screens\output.avi'

    # 폴더 내의 파일 목록 가져오기
    png_files = [f for f in os.listdir(png_folder_path) if f.endswith('.png')]

    # 파일명으로 정렬
    png_files.sort()

    # 첫 번째 PNG 파일을 읽어옴
    first_image = cv2.imread(os.path.join(png_folder_path, png_files[0]))

    # 영상의 크기 및 채널 설정
    height, width, channels = first_image.shape

    # 비디오 인코더 설정
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    video = cv2.VideoWriter(output_video_path, fourcc, 1.0, (width, height))

    # PNG 파일들을 영상으로 합치기
    for png_file in png_files:
        image_path = os.path.join(png_folder_path, png_file)
        img = cv2.imread(image_path)

        # 비디오에 프레임 추가
        video.write(img)

    # 비디오 릴리즈
    video.release()

if __name__ == "__main__":
    main('aa')
