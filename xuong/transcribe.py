"""Chuyển giọng nói thành chữ tiếng Việt, có mốc thời gian từng từ (chạy trên máy, miễn phí).

Đầu ra theo đúng định dạng mà Herk Edit Kit dùng:
  {"language_code","audio_duration_secs","text","words":[{"i","text","start","end","type":"word","p"}]}
"""
import os
import re
from pathlib import Path

from . import ROOT
from .util import ffmpeg_bin, run, save, say

DEFAULT_MODEL = os.environ.get("XUONG_WHISPER_MODEL", "large-v3-turbo")


def extract_audio(src, dst):
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", dst])
    return dst


def glossary() -> str:
    """Tên riêng/thuật ngữ để Whisper viết đúng (config/tu-dien.txt, mỗi dòng một cụm)."""
    p = ROOT / "config" / "tu-dien.txt"
    if not p.exists():
        return ""
    terms = [l.strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return ", ".join(terms)


def transcribe(audio_path, out_path, model_name=None, language="vi"):
    from faster_whisper import WhisperModel

    model_name = model_name or DEFAULT_MODEL
    device = os.environ.get("XUONG_WHISPER_DEVICE", "auto")
    compute = os.environ.get("XUONG_WHISPER_COMPUTE", "int8")
    say(f"• Whisper {model_name} ({device}/{compute}) đang nghe…")
    model = WhisperModel(model_name, device=device, compute_type=compute)
    prompt = glossary()
    # Đọc wav 16 kHz bằng soundfile rồi đưa mảng vào Whisper: tránh lệ thuộc phiên bản PyAV.
    import numpy as np
    import soundfile as sf
    pcm, sr = sf.read(str(audio_path), dtype="float32")
    if pcm.ndim > 1:
        pcm = pcm.mean(axis=1)
    if sr != 16000:
        raise RuntimeError("Cần wav 16 kHz (dùng extract_audio trước)")
    segments, info = model.transcribe(
        np.ascontiguousarray(pcm), language=language, word_timestamps=True, vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 300}, beam_size=5,
        initial_prompt=(f"Các tên riêng: {prompt}." if prompt else None),
        condition_on_previous_text=False,
    )
    words, texts = [], []
    for seg in segments:
        texts.append(seg.text.strip())
        for w in seg.words or []:
            t = w.word.strip()
            if not t:
                continue
            words.append({"i": len(words), "text": t, "start": round(w.start, 3), "end": round(w.end, 3),
                          "type": "word", "p": round(w.probability, 3)})
    fix_overlaps(words)
    data = {"language_code": language, "audio_duration_secs": round(info.duration, 3),
            "model": model_name, "text": " ".join(texts), "words": words}
    save(out_path, data)
    say(f"  ✓ {len(words)} từ, {info.duration:.1f}s")
    return data


def fix_overlaps(words):
    for a, b in zip(words, words[1:]):
        if b["start"] < a["end"]:
            mid = round((a["end"] + b["start"]) / 2, 3)
            a["end"], b["start"] = mid, mid
        if a["end"] <= a["start"]:
            a["end"] = round(a["start"] + 0.05, 3)


# ---------------------------------------------------------------- gợi ý biên tập
FILLERS = {"à", "ừ", "ừm", "ờ", "ơ", "ờm", "hừm", "ừa", "ạ ờ", "um", "uh", "ừ thì", "kiểu như", "thì là", "là là"}


def norm(t):
    return re.sub(r"[^\wÀ-ỹ]", "", t.lower())


def hints(transcript) -> dict:
    """Phát hiện máy móc các ứng viên cần cắt: từ đệm, cụm lặp liền nhau (nói vấp), từ nghe không rõ.

    Claude (Biên tập) đọc gợi ý này, quyết định cái nào thật sự cần cắt.
    """
    W = transcript["words"]
    n = [norm(w["text"]) for w in W]
    out = {"fillers": [], "repeats": [], "low_confidence": []}
    for i, t in enumerate(n):
        if t in {norm(f) for f in FILLERS}:
            out["fillers"].append(i)
        if W[i].get("p", 1) < 0.45:
            out["low_confidence"].append(i)
    # cụm k từ lặp ngay sau chính nó: "thứ nhất, thứ nhất là" -> cắt lần đầu
    i = 0
    while i < len(n):
        hit = False
        for k in (4, 3, 2, 1):
            if i + 2 * k <= len(n) and n[i:i + k] == n[i + k:i + 2 * k] and all(n[i:i + k]):
                out["repeats"].append({"cut_from": i, "cut_to": i + k - 1,
                                       "text": " ".join(w["text"] for w in W[i:i + k])})
                i += k
                hit = True
                break
        if not hit:
            i += 1
    return out


def hints_markdown(transcript, h) -> str:
    W = transcript["words"]
    lines = ["# Gợi ý biên tập (máy tự phát hiện, Claude quyết định)", ""]
    lines.append("## Bản ghi có đánh số từ")
    lines.append("Định dạng: `[chỉ số] từ` ; dấu ⏸ = ngắt > 0.6s")
    buf = []
    for i, w in enumerate(W):
        if i and w["start"] - W[i - 1]["end"] > 0.6:
            buf.append(f"⏸{w['start'] - W[i - 1]['end']:.1f}s")
        buf.append(f"[{i}]{w['text']}")
        if w["text"].endswith((".", "?", "!")):
            lines.append(" ".join(buf)); buf = []
    if buf:
        lines.append(" ".join(buf))
    lines += ["", "## Ứng viên cắt"]
    for r in h["repeats"]:
        lines.append(f"- Lặp: từ {r['cut_from']}–{r['cut_to']} «{r['text']}»")
    if h["fillers"]:
        lines.append("- Từ đệm: " + ", ".join(f"{i}«{W[i]['text']}»" for i in h["fillers"]))
    if h["low_confidence"]:
        lines.append("- Nghe không chắc (kiểm tra chính tả trong phụ đề): " +
                     ", ".join(f"{i}«{W[i]['text']}»" for i in h["low_confidence"]))
    return "\n".join(lines) + "\n"
