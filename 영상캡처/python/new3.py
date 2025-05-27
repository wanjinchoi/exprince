import os
import cv2
import xml.etree.ElementTree as ET

# 전역 변수
drawing = False
start_point = None
end_point = None
annotations = []
image = None
video_capture = None
frame_count = 0
initial_box = None

def create_annotation_xml(image_path, annotations, width, height, depth, indent="    "):
    annotation = ET.Element("annotation")

    folder = ET.SubElement(annotation, "folder")
    folder.text = "images"

    filename_elem = ET.SubElement(annotation, "filename")
    filename_elem.text = os.path.basename(image_path)

    path = ET.SubElement(annotation, "path")
    path.text = image_path

    source = ET.SubElement(annotation, "source")
    database = ET.SubElement(source, "database")
    database.text = "Unknown"

    size = ET.SubElement(annotation, "size")
    width_elem = ET.SubElement(size, "width")
    height_elem = ET.SubElement(size, "height")
    depth_elem = ET.SubElement(size, "depth")

    width_elem.text = str(width)
    height_elem.text = str(height)
    depth_elem.text = str(depth)

    segmented = ET.SubElement(annotation, "segmented")
    segmented.text = "0"

    for annotation_info in annotations:
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

        xmin = ET.SubElement(bndbox, "xmin")
        ymin = ET.SubElement(bndbox, "ymin")
        xmax = ET.SubElement(bndbox, "xmax")
        ymax = ET.SubElement(bndbox, "ymax")

        xmin.text = str(annotation_info['xmin'])
        ymin.text = str(annotation_info['ymin'])
        xmax.text = str(annotation_info['xmax'])
        ymax.text = str(annotation_info['ymax'])

    xml_str = ET.tostring(annotation, encoding="unicode", method="xml")

    xml_lines = xml_str.splitlines()
    for i, line in enumerate(xml_lines):
        if i == 0:
            continue
        xml_lines[i] = indent + line

    formatted_xml_str = "\n".join(xml_lines)

    return formatted_xml_str

def save_annotation():
    global frame_count, annotations, image
    xml_string = create_annotation_xml(f"frame_{frame_count}.jpg", annotations,
                                       image.shape[1], image.shape[0], image.shape[2])
    xml_file_path = f"frame_{frame_count}.xml"
    with open(xml_file_path, 'w') as f:
        f.write(xml_string)
    print(f"XML 파일이 저장되었습니다: {xml_file_path}")

    cv2.imwrite(f"frame_{frame_count}.jpg", image)
    print(f"이미지 파일이 저장되었습니다: frame_{frame_count}.jpg")

    frame_count += 1

def draw_contour(event, x, y, flags, param):
    global drawing, start_point, end_point, image, initial_box, annotations

    if event == cv2.EVENT_LBUTTONDOWN:
        if initial_box is None:
            drawing = True
            start_point = (x, y)
            end_point = (x, y)
        else:
            # 박스 크기를 유지하며 클릭한 위치에 새 박스를 추가하고 저장
            box_width = initial_box['xmax'] - initial_box['xmin']
            box_height = initial_box['ymax'] - initial_box['ymin']
            new_start_point = (x, y)
            new_end_point = (x + box_width, y + box_height)
            annotation_info = {
                'name': 'fire',
                'xmin': new_start_point[0],
                'ymin': new_start_point[1],
                'xmax': new_end_point[0],
                'ymax': new_end_point[1]
            }
            annotations.append(annotation_info)

            img_copy = image.copy()
            cv2.rectangle(img_copy, new_start_point, new_end_point, (0, 255, 0), 2)
            cv2.imshow('Image', img_copy)

            save_annotation()

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            end_point = (x, y)
            img_copy = image.copy()
            cv2.rectangle(img_copy, start_point, end_point, (0, 255, 0), 2)
            cv2.imshow('Image', img_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        if drawing:
            drawing = False
            end_point = (x, y)
            annotation_info = {
                'name': 'fire',
                'xmin': min(start_point[0], end_point[0]),
                'ymin': min(start_point[1], end_point[1]),
                'xmax': max(start_point[0], end_point[0]),
                'ymax': max(start_point[1], end_point[1])
            }
            annotations.append(annotation_info)
            initial_box = annotation_info  # 첫 번째 박스를 저장
            img_copy = image.copy()
            cv2.rectangle(img_copy, start_point, end_point, (0, 255, 0), 2)
            cv2.imshow('Image', img_copy)

video_path = r"C:\work\영상캡처\비디오\아파트 주차장에서 발생한 화재 #shorts.mp4"
video_capture = cv2.VideoCapture(video_path)

if not video_capture.isOpened():
    print(f"동영상을 열 수 없습니다: {video_path}")
else:
    while True:
        ret, frame = video_capture.read()
        if not ret:
            break
        image = frame.copy()

        cv2.namedWindow('Image')
        cv2.setMouseCallback('Image', draw_contour)

        while True:
            img_copy = image.copy()
            for annotation in annotations:
                cv2.rectangle(img_copy, (annotation['xmin'], annotation['ymin']),
                              (annotation['xmax'], annotation['ymax']), (0, 255, 0), 2)
            cv2.imshow('Image', img_copy)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                video_capture.release()
                cv2.destroyAllWindows()
                exit(0)
            elif key == ord('e'):
                start_point = None
                end_point = None
                annotations = []
                initial_box = None
                image = frame.copy()
            elif key == ord('a'):
                frame_count += 1
                ret, frame = video_capture.read()
                if ret:
                    image = frame.copy()
                    annotations = []
                break
            elif key == ord('z') and annotations:
                annotations.pop()
                initial_box = None if not annotations else annotations[0]
                image = frame.copy()
                for annotation in annotations:
                    cv2.rectangle(image, (annotation['xmin'], annotation['ymin']),
                                  (annotation['xmax'], annotation['ymax']), (0, 255, 0), 2)
                cv2.imshow('Image', image)

        if key == ord('q'):
            break

    cv2.destroyAllWindows()
    video_capture.release()
