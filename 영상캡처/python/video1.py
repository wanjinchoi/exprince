import os
import cv2
import xml.etree.ElementTree as ET

# 전역 변수
drawing = False
start_x, start_y, end_x, end_y = 0, 0, 0, 0
image = None
video_capture = None
frame_count = 0

def create_annotation_xml(image_path, annotation_info, indent="    "):
    # XML 루트 요소 생성
    annotation = ET.Element("annotation")

    # folder 요소 추가
    folder = ET.SubElement(annotation, "folder")
    folder.text = "images"

    # filename 요소 추가
    filename_elem = ET.SubElement(annotation, "filename")
    filename_elem.text = os.path.basename(image_path)

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

    width_elem.text = str(annotation_info['width'])
    height_elem.text = str(annotation_info['height'])
    depth_elem.text = str(annotation_info['depth'])

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
    xml_str = '\n'.join([line for line in xml_str.split('\n') if line.strip()])
    xml_str = xml_str.replace("  ", indent)
    return xml_str

# 마우스 이벤트 콜백 함수
def draw_contour(event, x, y, flags, param):
    global drawing, start_x, start_y, end_x, end_y, image, frame_count

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
        img_copy = image.copy()
        cv2.rectangle(img_copy, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)
        cv2.imshow('Image', img_copy)

        # XML 생성
        annotation_info = {
            'name': 'fire',
            'xmin': start_x,
            'ymin': start_y,
            'xmax': end_x,
            'ymax': end_x,
            'width': image.shape[1],   # 이미지 너비
            'height': image.shape[0],  # 이미지 높이
            'depth': image.shape[2]    # 이미지 채널 수
        }
        xml_string = create_annotation_xml(f"frame_{frame_count}.jpg", annotation_info)
        print(xml_string)

        # XML 파일 저장
        xml_file_path = f"frame_{frame_count}.xml"
        with open(xml_file_path, 'w') as f:
            f.write(xml_string)
        print(f"XML 파일이 저장되었습니다: {xml_file_path}")

        # 이미지 파일 저장
        cv2.imwrite(f"frame_{frame_count}.jpg", image)
        print(f"이미지 파일이 저장되었습니다: frame_{frame_count}.jpg")

        # 다음 프레임으로 이동
        if video_capture.isOpened():
            frame_count += 1
            ret, frame = video_capture.read()
            if ret:
                image = frame.copy()
                cv2.imshow('Image', image)

# 동영상 파일 경로
video_path = r"C:\work\영상캡처\비디오\Y2meta.app-[대전MBC뉴스]시청자 제보 영상-카이스트 화재‥소방관도 부상-(1080p).mp4"
video_capture = cv2.VideoCapture(video_path)

if not video_capture.isOpened():
    print(f"동영상을 열 수 없습니다: {video_path}")
else:
    ret, frame = video_capture.read()
    image = frame.copy()

    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', draw_contour)

    while True:
        cv2.imshow('Image', image)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # 'q' 키를 누르면 종료
            break

    # OpenCV 창 종료
    cv2.destroyAllWindows()
    video_capture.release()
