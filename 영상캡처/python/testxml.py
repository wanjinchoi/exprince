import os
import xml.etree.ElementTree as ET
from PIL import Image
import cv2

def create_annotation_xml(image_path, annotation_info, indent="    "):
    # 이미지 정보 가져오기
    with Image.open(image_path) as img:
        width, height = img.size
        depth = len(img.getbands())

    # 파싱할 이미지 경로에서 파일명과 확장자 추출
    filename = os.path.basename(image_path)
    filename_no_extension, _ = os.path.splitext(filename)

    # XML 루트 요소 생성
    annotation = ET.Element("annotation")

    # folder 요소 추가
    folder = ET.SubElement(annotation, "folder")
    folder.text = "images"

    # filename 요소 추가
    filename_elem = ET.SubElement(annotation, "filename")
    filename_elem.text = filename

    # path 요소 추가
    path = ET.SubElement(annotation, "path")
    path.text = image_path

    # source 요소 추가
    source = ET.SubElement(annotation, "source")
    database = ET.SubElement(source, "database")
    database.text = "Unknown"

    # size 요소 추가
    size = ET.SubElement(annotation, "size")
    width_elem = ET.SubElement(size, "width")
    height_elem = ET.SubElement(size, "height")
    depth_elem = ET.SubElement(size, "depth")

    width_elem.text = str(width)
    height_elem.text = str(height)
    depth_elem.text = str(depth)

    # segmented 요소 추가
    segmented = ET.SubElement(annotation, "segmented")
    segmented.text = "0"

    # object 요소 추가
    obj = ET.SubElement(annotation, "object")
    name = ET.SubElement(obj, "name")
    pose = ET.SubElement(obj, "pose")
    truncated = ET.SubElement(obj, "truncated")
    difficult = ET.SubElement(obj, "difficult")
    bndbox = ET.SubElement(obj, "bndbox")

    name.text = annotation_info['name']
    pose.text = "Unspecified"
    truncated.text = "0"
    difficult.text = "0"

    # bndbox의 좌표 추가
    xmin = ET.SubElement(bndbox, "xmin")
    ymin = ET.SubElement(bndbox, "ymin")
    xmax = ET.SubElement(bndbox, "xmax")
    ymax = ET.SubElement(bndbox, "ymax")

    xmin.text = str(annotation_info['xmin'])
    ymin.text = str(annotation_info['ymin'])
    xmax.text = str(annotation_info['xmax'])
    ymax.text = str(annotation_info['ymax'])

    # 생성한 XML 트리를 문자열로 반환
    xml_str = ET.tostring(annotation, encoding="unicode", method="xml")
    # 들여쓰기 적용
    xml_str = '\n'.join([line for line in xml_str.split('\n') if line.strip()])
    xml_str = xml_str.replace("  ", indent)
    return xml_str

# 마우스 이벤트 콜백 함수
def draw_contour(event, x, y, flags, param):
    global drawing, start_x, start_y, end_x, end_y, image

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start_x, start_y = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_x, end_y = x, y
            img_copy = image.copy()
            cv2.rectangle(img_copy, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
            cv2.imshow('Image', img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end_x, end_y = x, y
        cv2.rectangle(image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

        # 외곽선 좌표 출력
        print("외곽선 좌표:", (start_x, start_y, end_x, end_y))

        # XML 생성
        annotation_info = {
            'name': 'fire',
            'xmin': start_x,
            'ymin': start_y,
            'xmax': end_x,
            'ymax': end_y
        }
        xml_string = create_annotation_xml(image_path, annotation_info)
        print(xml_string)

        # XML 파일 저장
        xml_file_path = os.path.splitext(image_path)[0] + ".xml"
        with open(xml_file_path, 'w') as f:
            f.write(xml_string)
        print(f"XML 파일이 저장되었습니다: {xml_file_path}")

# 이미지 로드
image_path = r'C:\Users\Admin\Desktop\20240623\FireDataset-V6\fire\fire_image_1357.jpg'
image = cv2.imread(image_path)
drawing = False

if image is None:
    print(f"이미지를 읽을 수 없습니다: {image_path}")
else:
    # OpenCV 창 생성 및 마우스 이벤트 콜백 함수 등록
    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', draw_contour)

    # 이미지 표시 및 이벤트 대기
    while True:
        cv2.imshow('Image', image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # 'q' 키를 누르면 종료
            break

    # OpenCV 창 종료
    cv2.destroyAllWindows()
