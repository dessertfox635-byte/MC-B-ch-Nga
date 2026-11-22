"""Kiểm tra máy còn thiếu gì cho Xưởng Phim. In bảng ✓/✗ kèm lệnh cài."""
import importlib
import platform
import shutil
import subprocess
import sys

from . import ROOT

MAC = platform.system() == "Darwin"


def _ver(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[0][:60]
    except Exception:
        return None


def checks():
    rows = []
    add = lambda name, ok, info, fix: rows.append((name, ok, info, fix))
    add("Python ≥ 3.10", sys.version_info >= (3, 10), sys.version.split()[0], "brew install python@3.12")
    for b, fix in (("ffmpeg", "brew install ffmpeg"), ("ffprobe", "brew install ffmpeg"), ("node", "brew install node"),
                   ("git", "xcode-select --install")):
        p = shutil.which(b)
        add(b, bool(p), _ver([b, "-version" if b.startswith("ff") else "--version"]) if p else "không có", fix)
    nv = _ver(["node", "-e", "console.log(process.versions.node)"])
    add("Node ≥ 22", bool(nv) and int(nv.split(".")[0]) >= 22, nv or "?", "brew install node")
    add("Claude Code", bool(shutil.which("claude")), _ver(["claude", "--version"]) or "không có",
        "curl -fsSL https://claude.ai/install.sh | bash")
    for mod, pipname in (("faster_whisper", "faster-whisper"), ("vieneu", "vieneu"), ("mediapipe", "mediapipe"), ("cv2", "mediapipe"), ("soundfile", "soundfile")):
        try:
            importlib.import_module(mod); ok = True
        except Exception:
            ok = False
        add(f"python: {pipname}", ok, "đã cài" if ok else "thiếu", f".venv/bin/pip install '{pipname}'")
    add("GSAP", (ROOT / "node_modules/gsap/dist/gsap.min.js").exists(), "", "npm install")
    pw = subprocess.run(["node", "-e", "require('playwright').chromium.launch().then(b=>{console.log('ok');return b.close()})"],
                        capture_output=True, text=True, cwd=ROOT, timeout=90) if shutil.which("node") else None
    add("Chromium (Playwright)", bool(pw and "ok" in pw.stdout), "chạy được" if pw and "ok" in pw.stdout else "không mở được",
        "npm install && npx playwright install chromium")
    add("Font tiếng Việt", (ROOT / "effects/fonts/BeVietnamPro-Bold.ttf").exists(), "", "git pull (font nằm trong repo)")
    add("Mô hình tách người", (ROOT / "models/selfie_segmenter.tflite").exists(), "", "tự tải ở lần dựng đầu (250 KB)")
    free = shutil.disk_usage(ROOT).free / 1e9
    add("Ổ trống ≥ 15 GB", free >= 15, f"{free:.0f} GB", "dọn ổ cứng")
    c = ROOT / "voice/consent/bich-nga.json"
    add("Giấy đồng ý giọng Bích Nga", c.exists(), "có" if c.exists() else "chưa có (Agent 3 sẽ từ chối)",
        "xem voice/consent/MAU-GIAY-DONG-Y.md")
    return rows


def main():
    rows = checks()
    w = max(len(r[0]) for r in rows) + 2
    print("Xưởng Phim – kiểm tra máy\n")
    for name, ok, info, fix in rows:
        print(f"  {'✓' if ok else '✗'} {name:<{w}} {info or ''}" + ("" if ok else f"\n      → {fix}"))
    bad = [r for r in rows if not r[1] and not r[0].startswith(("Giấy", "Mô hình"))]
    print(f"\n{'Sẵn sàng dựng phim.' if not bad else f'Còn thiếu {len(bad)} mục – chạy: bash setup/install_mac.sh'}")
    return 0 if not bad else 1
