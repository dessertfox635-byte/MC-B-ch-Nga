"""Nhận diện khuôn mặt (OpenCV, chạy trên máy) để chữ animation không che mặt người nói.

detect(video) -> {"w","h","samples":[{"t","box":[x,y,w,h]|None}], "median":[x,y,w,h]|None}
Hộp mặt được nới thêm phần trán–cằm vì chữ đè lên tóc/cằm cũng khó coi.
"""
import statistics

from .util import save


def detect(video, out_json=None, step=0.5, roi=None):
    """roi=(x,y,w,h): chỉ tìm mặt trong vùng này (vd. khung chính của chế độ fit-blur)."""
    import cv2

    if not hasattr(cv2, "CascadeClassifier"):      # bản OpenCV thiếu bộ nhận diện → coi như không thấy mặt
        data = {"w": 0, "h": 0, "samples": [], "median": None, "coverage": 0.0}
        if out_json:
            save(out_json, data)
        return data
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
    samples, every = [], max(1, int(round(fps * step)))
    for f in range(0, max(n, 1), every):
        cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, img = cap.read()
        if not ok:
            break
        scale = 480 / max(W, H)
        small = cv2.resize(img, (int(W * scale), int(H * scale)))
        g = cv2.equalizeHist(cv2.cvtColor(small, cv2.COLOR_BGR2GRAY))
        min_side = int(min(small.shape[:2]) * 0.08)
        faces = list(casc.detectMultiScale(g, 1.1, 5, minSize=(min_side, min_side)))
        if not faces:
            faces = list(prof.detectMultiScale(g, 1.1, 5, minSize=(min_side, min_side)))
        box = None
        if faces:
            # bỏ mặt bị làm mờ (ảnh nền fit-blur, phản chiếu…): chỉ giữ mặt đủ sắc nét
            def sharp(b):
                x, y, w, h = b
                roi = cv2.cvtColor(small[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
                return cv2.Laplacian(roi, cv2.CV_64F).var() if roi.size else 0
            sh = [sharp(b) for b in faces]
            faces = [b for b, v in zip(faces, sh) if v >= max(25.0, 0.6 * max(sh))]
        if faces and roi:
            rx, ry, rw, rh = (v * scale for v in roi)
            faces = [b for b in faces if rx <= b[0] + b[2] / 2 <= rx + rw and ry <= b[1] + b[3] / 2 <= ry + rh]
        if faces:
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            # nới: trán/tóc 35%, cằm 25%, hai bên 15%
            x, y, w, h = x - 0.15 * w, y - 0.35 * h, w * 1.3, h * 1.6
            box = [round(v / scale, 1) for v in (max(0, x), max(0, y), w, h)]
        samples.append({"t": round(f / fps, 3), "box": box})
    cap.release()
    boxes = [s["box"] for s in samples if s["box"]]
    med = [round(statistics.median(b[i] for b in boxes), 1) for i in range(4)] if boxes else None
    data = {"w": W, "h": H, "samples": samples, "median": med, "coverage": round(len(boxes) / max(1, len(samples)), 2)}
    if out_json:
        save(out_json, data)
    return data


def face_at(faces, t):
    if not faces or not faces.get("samples"):
        return None
    best = min(faces["samples"], key=lambda s: abs(s["t"] - t))
    return best["box"] if abs(best["t"] - t) <= 0.6 else None


def overlap_ratio(box, face):
    """Tỉ lệ diện tích mặt bị chữ che."""
    x = max(0, min(box["x"] + box["w"], face[0] + face[2]) - max(box["x"], face[0]))
    y = max(0, min(box["y"] + box["h"], face[1] + face[3]) - max(box["y"], face[1]))
    return (x * y) / max(1.0, face[2] * face[3])


# Vùng chữ (khớp effects/engine.html) để chọn chỗ tránh mặt trước khi dựng chữ.
ZONES_V = {"top": (.08, .11, .76, .24), "center": (.08, .38, .76, .22)}
ZONES_H = {"top": (.08, .07, .84, .26), "center": (.20, .36, .60, .28)}


def avoid_faces(tl, faces):
    """Dời hiệu ứng sang vùng ít che mặt nhất (nếu vùng đó đang trống ở khoảng thời gian ấy)."""
    if not faces or not faces.get("median"):
        return []
    W, H = tl["format"]["w"], tl["format"]["h"]
    zones = ZONES_V if H > W else ZONES_H
    moves = []
    for ov in tl["overlays"]:
        if ov["zone"] not in zones:
            continue
        mids = [face_at(faces, ov["start"] + k * (ov["end"] - ov["start"]) / 4) for k in range(5)]
        mids = [m for m in mids if m]
        if not mids:
            continue

        def cover(z):
            zx, zy, zw, zh = zones[z]
            r = {"x": zx * W, "y": zy * H, "w": zw * W, "h": zh * H}
            return max(overlap_ratio(r, m) for m in mids)

        cur = cover(ov["zone"])
        if cur < 0.15:
            continue
        for z in sorted(zones, key=cover):
            if z == ov["zone"] or cover(z) >= cur:
                continue
            busy = any(o is not ov and o["zone"] == z and o["start"] < ov["end"] and ov["start"] < o["end"] for o in tl["overlays"])
            if not busy:
                moves.append(f"{ov['id']}: {ov['zone']}→{z} để không che mặt ({cur:.0%}→{cover(z):.0%})")
                ov["zone"] = z
                break
    return moves
