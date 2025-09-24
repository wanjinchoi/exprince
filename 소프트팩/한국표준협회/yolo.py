import argparse
from pathlib import Path
import sys
import cv2
import numpy as np
import fitz  # PyMuPDF
import pandas as pd
from ultralytics import YOLO


def get_names(model):
    # Ultralytics YOLO v8 기준
    names = getattr(getattr(model, "model", model), "names", None)
    if isinstance(names, list):
        return {i: n for i, n in enumerate(names)}
    if isinstance(names, dict):
        # 키가 str일 수도 있어 int로 정규화
        return {int(k): v for k, v in names.items()}
    return None


def resolve_target_class_ids(names_map):
    """
    'person' 또는 'human' 클래스를 우선 찾는다.
    없다면, 모델이 단일 클래스면 그 1개를 '사람'으로 간주(단일-인간 전용 가중치인 경우).
    """
    if not names_map:
        return None
    lowers = {cid: str(name).lower() for cid, name in names_map.items()}
    target = [cid for cid, nm in lowers.items() if nm in ("person", "human")]
    if target:
        return sorted(target)
    # 단일 클래스면 그걸로 처리
    if len(lowers) == 1:
        return [sorted(lowers.keys())[0]]
    # 못 찾으면 None
    return None


def yolo_detect_persons(model, image_bgr, target_ids, conf=0.3):
    """
    이미지에서 target_ids 클래스만 카운트/추출.
    target_ids가 None이면 모든 탐지를 사람으로 보지 않음(=0으로 처리).
    """
    if target_ids is None:
        return [], [], []

    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    r = model.predict(source=image_rgb, conf=conf, verbose=False)[0]

    boxes_xyxy = r.boxes.xyxy.cpu().numpy() if r.boxes.xyxy is not None else np.zeros(
        (0, 4))
    cls_ids = r.boxes.cls.cpu().numpy().astype(
        int) if r.boxes.cls is not None else np.zeros((0,), dtype=int)
    confs = r.boxes.conf.cpu().numpy() if r.boxes.conf is not None else np.zeros(
        (0,), dtype=float)

    sel = [i for i, c in enumerate(cls_ids) if c in target_ids]
    sel_boxes = [tuple(map(int, boxes_xyxy[i])) for i in sel]
    sel_scores = [float(confs[i]) for i in sel]
    sel_labels = ["person"] * len(sel)  # 목표가 '사람 여부'이므로 라벨 고정

    return sel_boxes, sel_labels, sel_scores


def draw_boxes(image_bgr, boxes, labels, scores, color=(0, 255, 0)):
    for (x1, y1, x2, y2), lab, sc in zip(boxes, labels, scores):
        cv2.rectangle(image_bgr, (x1, y1), (x2, y2), color, 2)
        txt = f"{lab} {sc:.2f}"
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        y0 = max(0, y1 - th - 4)
        cv2.rectangle(image_bgr, (x1, y0), (x1 + tw + 6, y0 + th + 4), color,
                      -1)
        cv2.putText(image_bgr, txt, (x1 + 3, y0 + th + 1),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1, cv2.LINE_AA)
    return image_bgr


def render_page_to_bgr(page, dpi=260):
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height,
                                                             pix.width, 3)
    return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


def extract_embedded_images_bgr(page):
    """
    페이지에 임베드된 원본 이미지를 모두 추출(BGR).
    """
    images = []
    for img in page.get_images(full=True):
        xref = img[0]  # XREF
        base = page.parent.extract_image(xref)
        img_bytes = base["image"]
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        im = cv2.imdecode(arr, cv2.IMREAD_COLOR)  # BGR
        if im is not None:
            images.append(im)
    return images


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def main():
    ap = argparse.ArgumentParser(description="PDF 내부 이미지/페이지에서 사람 여부 판별")
    ap.add_argument("--pdf", required=True, help="입력 PDF 경로")
    ap.add_argument("--weights", required=True, help="YOLO .pt 가중치 경로")
    ap.add_argument("--mode", choices=["page", "image"], default="page",
                    help="page=페이지 렌더에서 탐지, image=임베드 원본 이미지에서 탐지")
    ap.add_argument("--dpi", type=int, default=260,
                    help="page 모드용 렌더 DPI (200~320 권장)")
    ap.add_argument("--conf", type=float, default=0.30,
                    help="YOLO confidence 임계값")
    ap.add_argument("--out", default="out_pdf_person", help="출력 디렉터리")
    ap.add_argument("--save-annots", action="store_true", help="주석(박스) 이미지 저장")
    ap.add_argument("--save-csv", action="store_true", help="CSV 리포트 저장")
    ap.add_argument("--min-area", type=float, default=0.0,
                    help="박스 최소 면적 비율(0~1). 너무 작은 오검출 제외용. 예: 0.002")
    args = ap.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"PDF 없음: {pdf_path}")
        sys.exit(1)

    out_dir = Path(args.out)
    ann_dir = out_dir / "annotated"
    ensure_dir(out_dir)
    if args.save_annots:
        ensure_dir(ann_dir)

    # 모델 로드 및 타겟 클래스 확인
    model = YOLO(args.weights)
    names_map = get_names(model)
    target_ids = resolve_target_class_ids(names_map)
    if target_ids is None:
        print("⚠️ 'person/human' 클래스를 찾지 못했습니다.")
        print("   - 단일 클래스 가중치가 아니라면 data.yaml을 확인하세요.")
        print("   - 그래도 진행은 하지만, 탐지=0으로 나올 수 있습니다.")

    doc = fitz.open(pdf_path)
    rows = []  # CSV용

    for pi, page in enumerate(doc, start=1):
        if args.mode == "page":
            img_bgr = render_page_to_bgr(page, dpi=args.dpi)
            H, W = img_bgr.shape[:2]
            boxes, labels, scores = yolo_detect_persons(model, img_bgr,
                                                        target_ids,
                                                        conf=args.conf)

            # 너무 작은 박스 제거(비율 기준)
            if args.min_area > 0:
                keep = []
                for i, (x1, y1, x2, y2) in enumerate(boxes):
                    area = (x2 - x1) * (y2 - y1)
                    if area / float(H * W) >= args.min_area:
                        keep.append(i)
                boxes = [boxes[i] for i in keep]
                labels = [labels[i] for i in keep]
                scores = [scores[i] for i in keep]

            if args.save_annots:
                ann = draw_boxes(img_bgr.copy(), boxes, labels, scores)
                cv2.imwrite(str(ann_dir / f"page_{pi:03d}.jpg"), ann)

            rows.append({"unit": f"page_{pi:03d}", "type": "page",
                "count_person": len(boxes)})
            print(f"[page {pi}] persons={len(boxes)}")

        else:  # image 모드
            imgs = extract_embedded_images_bgr(page)
            if not imgs:
                rows.append({"unit": f"page_{pi:03d}", "type": "image-none",
                             "count_person": 0})
                print(f"[page {pi}] embedded images: 0")
                continue

            for ii, im in enumerate(imgs, start=1):
                H, W = im.shape[:2]
                boxes, labels, scores = yolo_detect_persons(model, im,
                                                            target_ids,
                                                            conf=args.conf)

                if args.min_area > 0 and boxes:
                    keep = []
                    for i, (x1, y1, x2, y2) in enumerate(boxes):
                        area = (x2 - x1) * (y2 - y1)
                        if area / float(H * W) >= args.min_area:
                            keep.append(i)
                    boxes = [boxes[i] for i in keep]
                    labels = [labels[i] for i in keep]
                    scores = [scores[i] for i in keep]

                if args.save_annots:
                    ann = draw_boxes(im.copy(), boxes, labels, scores)
                    cv2.imwrite(
                        str(ann_dir / f"page_{pi:03d}_img_{ii:02d}.jpg"), ann)

                rows.append(
                    {"unit": f"page_{pi:03d}_img_{ii:02d}", "type": "image",
                        "count_person": len(boxes)})
                print(f"[page {pi} image {ii}] persons={len(boxes)}")

    if args.save_csv:
        df = pd.DataFrame(rows)
        csv_path = out_dir / "detections.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"CSV saved: {csv_path}")

    print("done.")


if __name__ == "__main__":
    main()
