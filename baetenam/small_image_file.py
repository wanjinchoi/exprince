from PIL import Image
import os


def compress_image(input_path, output_path, target_size_mb):
    quality = 85  # 초기 품질 설정
    step = 5  # 품질을 줄이는 단위

    with Image.open(input_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.save(output_path, format='JPEG', quality=quality)

        while os.path.getsize(output_path) > target_size_mb * 1024 * 1024:
            quality -= step
            if quality <= 0:
                raise ValueError("이미지를 지정된 크기로 줄일 수 없습니다.")
            img.save(output_path, format='JPEG', quality=quality)


input_image_path = r"C:\ARGOSRPA\Master Service\Master_image\Full screen\General #1.png"
output_image_path = r"C:\ARGOSRPA\Master Service\Master_image\Full screen\General #1_compressed.jpg"
compress_image(input_image_path, output_image_path,target_size_mb=1)  # 1MB 이하로 줄이기