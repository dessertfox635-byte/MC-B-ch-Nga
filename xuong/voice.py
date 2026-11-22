"""Agent 3 – Giọng Bích Nga (VieNeu-TTS, chạy trên máy, Apache 2.0).

Nguyên tắc cứng:
  1. Không có giấy đồng ý hợp lệ của chính người có giọng → không clone, không đọc. Không có ngoại lệ.
  2. Mọi file giọng tạo ra đều mang watermark âm thanh của VieNeu và một file .json ghi nguồn gốc.
  3. Giọng mẫu và hồ sơ giọng là dữ liệu sinh trắc học: không commit lên git (đã chặn trong .gitignore).
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

from . import ROOT
from .util import ffmpeg_bin, run, save, say

VOICE_DIR = ROOT / "voice"
REGISTRY = VOICE_DIR / "voices.json"
_tts = None
_enrolled = set()


class ConsentError(RuntimeError):
    pass


def registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8")) if REGISTRY.exists() else {}


def check_consent(voice_id):
    if voice_id.startswith("preset:"):
        return {"preset": True}
    reg = registry()
    if voice_id not in reg:
        raise ConsentError(f"Chưa đăng ký giọng «{voice_id}» trong voice/voices.json")
    cpath = ROOT / reg[voice_id]["consent"]
    if not cpath.exists():
        raise ConsentError(f"Thiếu giấy đồng ý: {cpath.relative_to(ROOT)}. Xem voice/consent/MAU-GIAY-DONG-Y.md")
    c = json.loads(cpath.read_text(encoding="utf-8"))
    problems = []
    if not c.get("signed"):
        problems.append("chưa ký (signed=false)")
    if c.get("revoked"):
        problems.append("đã bị thu hồi")
    doc = c.get("document")
    if not doc or not (ROOT / doc).exists():
        problems.append(f"không thấy bản scan đã ký ({doc})")
    exp = c.get("expires")
    if exp and dt.date.fromisoformat(exp) < dt.date.today():
        problems.append(f"đã hết hạn {exp}")
    if problems:
        raise ConsentError(f"Giấy đồng ý giọng «{voice_id}» không hợp lệ: " + "; ".join(problems))
    return c


def engine():
    global _tts
    if _tts is None:
        from vieneu import Vieneu
        say("• Nạp VieNeu-TTS…")
        _tts = Vieneu()
    return _tts


def _ensure_voice(voice_id):
    tts = engine()
    if voice_id.startswith("preset:"):
        return voice_id.split(":", 1)[1] or None
    if voice_id not in _enrolled:
        ref = ROOT / registry()[voice_id]["reference"]
        if not ref.exists():
            raise RuntimeError(f"Chưa có giọng mẫu {ref.relative_to(ROOT)}. Chạy: python -m xuong voice prepare {voice_id} <file ghi âm>")
        tts.add_voice(voice_id, str(ref), denoise=False)
        _enrolled.add(voice_id)
    return voice_id


def synthesize(text, voice_id, outdir):
    """Đọc `text` bằng giọng `voice_id` → đường dẫn wav (có cache theo nội dung)."""
    consent = check_consent(voice_id)
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{voice_id}|{text}".encode()).hexdigest()[:12]
    wav = outdir / f"{voice_id.replace(':', '_')}-{key}.wav"
    if wav.exists():
        return wav
    v = _ensure_voice(voice_id)
    tts = engine()
    audio = tts.infer(text, voice=v, apply_watermark=True) if v else tts.infer(text, apply_watermark=True)
    tts.save(audio, str(wav))
    save(wav.with_suffix(".json"), {
        "voice": voice_id, "text": text, "engine": "VieNeu-TTS", "watermark": True, "ai_generated": True,
        "consent_ref": None if consent.get("preset") else registry()[voice_id]["consent"],
        "scope": consent.get("scope"), "created": dt.datetime.now().isoformat(timespec="seconds"),
    })
    return wav


def prepare_reference(voice_id, sources, seconds=(3.0, 8.0)):
    """Tự chọn đoạn giọng mẫu tốt nhất (3–8s, nói liền mạch, rõ, đều tiếng) từ các file ghi âm/video gốc."""
    check_consent(voice_id)
    from .transcribe import extract_audio, transcribe
    import numpy as np
    import soundfile as sf

    work = VOICE_DIR / "work" / voice_id
    work.mkdir(parents=True, exist_ok=True)
    cands = []
    for k, src in enumerate(sources):
        a16 = extract_audio(src, work / f"src{k}.16k.wav")
        hi = work / f"src{k}.48k.wav"
        run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", src, "-vn", "-ac", "1", "-ar", "48000", hi])
        tr = transcribe(a16, work / f"src{k}.json")
        wav, sr = sf.read(hi)
        W = tr["words"]
        for i in range(len(W)):
            for j in range(i + 1, len(W)):
                d = W[j]["end"] - W[i]["start"]
                if d > seconds[1]:
                    break
                if d < seconds[0]:
                    continue
                gaps = [W[x + 1]["start"] - W[x]["end"] for x in range(i, j)]
                if max(gaps, default=0) > 0.6:
                    continue
                seg = wav[int(W[i]["start"] * sr):int(W[j]["end"] * sr)]
                frames = seg[: len(seg) // 2400 * 2400].reshape(-1, 2400)
                rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
                steadiness = float(np.median(rms) / (np.std(rms) + 1e-6))
                conf = float(np.mean([w.get("p", 1) for w in W[i:j + 1]]))
                clip = float((np.abs(seg) > 0.98).mean())
                score = conf * 2 + min(steadiness, 3) * 0.5 - clip * 50 + (1 if W[j]["text"].endswith((".", "!", "?")) else 0)
                cands.append((score, k, W[i]["start"], W[j]["end"], " ".join(w["text"] for w in W[i:j + 1])))
    if not cands:
        raise RuntimeError("Không tìm được đoạn 3–8s nói liền mạch. Cần bản ghi âm rõ, ít nhạc nền.")
    cands.sort(reverse=True)
    score, k, s, e, text = cands[0]
    raw = work / "best.raw.wav"
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-ss", f"{max(0, s - 0.08):.3f}", "-to", f"{e + 0.15:.3f}",
         "-i", work / f"src{k}.48k.wav", raw])
    ref = ROOT / registry()[voice_id]["reference"]
    ref.parent.mkdir(parents=True, exist_ok=True)
    engine().denoise(str(raw), out_path=str(ref))
    info = {"voice": voice_id, "source": str(sources[k]), "start": s, "end": e, "text": text, "score": round(score, 2),
            "alternatives": [{"source": str(sources[c[1]]), "start": c[2], "end": c[3], "text": c[4]} for c in cands[1:4]]}
    save(ref.with_suffix(".json"), info)
    say(f"  ✓ Giọng mẫu {e - s:.1f}s: «{text}»")
    return info
