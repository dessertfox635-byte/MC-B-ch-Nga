"""Tách người khỏi nền (MediaPipe Selfie Segmenter, chạy trên máy ~12ms/khung).

Dùng cho hiệu ứng chiều sâu: từ khoá khổng lồ nằm SAU người nói (người che lên chữ), như video mẫu.
Đầu ra: video mặt nạ xám (trắng = người) cùng kích thước, cùng số khung với base.
"""
import subprocess
from pathlib import Path

from . import ROOT
from .util import ffmpeg_bin, say

MODEL = ROOT / "models" / "selfie_segmenter.tflite"
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"


def ensure_model():
    if not MODEL.exists():
        import urllib.request
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        say("• Tải mô hình tách người (250 KB)…")
        urllib.request.urlretrieve(MODEL_URL, MODEL)
    return MODEL


def make_matte(video, out):
    import cv2
    import mediapipe as mp
    import numpy as np
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision

    opt = vision.ImageSegmenterOptions(base_options=mpt.BaseOptions(model_asset_path=str(ensure_model())),
                                       running_mode=vision.RunningMode.VIDEO, output_confidence_masks=True)
    seg = vision.ImageSegmenter.create_from_options(opt)
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ff = subprocess.Popen([ffmpeg_bin(), "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}",
                           "-r", str(fps), "-i", "-", "-c:v", "ffv1", "-pix_fmt", "gray", str(out)], stdin=subprocess.PIPE)
    prev, i = None, 0
    while True:
        ok, img = cap.read()
        if not ok:
            break
        r = seg.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)),
                                  int(i * 1000 / fps))
        m = r.confidence_masks[0].numpy_view()[..., 0] if r.confidence_masks[0].numpy_view().ndim == 3 else r.confidence_masks[0].numpy_view()
        m = np.clip((m - 0.35) / 0.3, 0, 1)                      # mép gọn hơn
        m = cv2.GaussianBlur(m, (0, 0), max(1.0, W / 960))       # mép mềm
        prev = m if prev is None else 0.6 * m + 0.4 * prev       # chống rung giữa các khung
        ff.stdin.write((prev * 255).astype(np.uint8).tobytes())
        i += 1
    cap.release(); seg.close()
    ff.stdin.close(); ff.wait()
    return out
