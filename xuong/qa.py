"""Kiểm định tự động thay cho người duyệt.

Đo trên chính thành phẩm và trên bố cục thật của từng khung chữ (không đoán):
  E1 chữ đè chữ            E2 chữ ra ngoài vùng an toàn TikTok/Reels   E3 chữ bị co quá nhỏ
  E4 điểm cắt rơi giữa từ  E5 phụ đề lệch lời nói                       E6 âm lượng sai chuẩn / bị rè
  E7 khung đen / hình đứng  E8 độ dài vượt mục tiêu                      E9 thiếu tiếng / thiếu hình
Kết quả: qa.<khổ>.json (điểm + lỗi + gợi ý sửa) và contact sheet PNG để Claude tự nhìn lại.
"""
import re
from pathlib import Path

from . import ROOT
from .timeline import overlay_spec
from .util import ffmpeg_bin, node_bin, probe, run, save

# Vùng an toàn (tỉ lệ khung) – 9:16: tránh thanh trên, cột nút bên phải, mô tả + nút ở đáy.
SAFE = {True: {"x0": .04, "y0": .08, "x1": .88, "y1": .80}, False: {"x0": .03, "y0": .04, "x1": .97, "y1": .96}}


def _inter(a, b):
    x = max(0, min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]))
    y = max(0, min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]))
    return x * y


def check_layout(tl, work):
    spec = Path(work) / "qa.spec.json"
    lay = Path(work) / "qa.layout.json"
    save(spec, overlay_spec(tl))
    run([node_bin(), ROOT / "render" / "overlay.mjs", "layout", spec, lay, "--step", "0.1"], capture=True)
    import json
    L = json.loads(lay.read_text())
    w, h = tl["format"]["w"], tl["format"]["h"]
    safe = SAFE[h > w]
    sx0, sy0, sx1, sy1 = safe["x0"] * w, safe["y0"] * h, safe["x1"] * w, safe["y1"] * h
    issues, seen = [], set()
    from .face import face_at, overlap_ratio
    from .util import load
    faces = load(Path(work) / "faces.json")
    pips = []
    for br in tl.get("broll", []):
        if br.get("mode") == "pip":
            f = br["file"] if Path(br["file"]).is_absolute() else str(ROOT / br["file"])
            try:
                i = probe(f); ar = i["height"] / i["width"]
            except Exception:
                ar = 9 / 16
            bw = int(w * 0.62) + 12
            pips.append((br, {"x": (w - bw) / 2, "y": int(h * 0.12), "w": bw, "h": int(w * 0.62 * ar) + 12}))
    for s in L["samples"]:
        for br, r in pips:
            if br["start"] + 0.2 <= s["t"] <= br["end"] - 0.1:
                for b in s["boxes"]:
                    if b.get("settled", True) and _inter(r, b) > 0.04 * min(r["w"] * r["h"], b["w"] * b["h"]) \
                            and ("E1", br["id"], b["id"]) not in seen:
                        seen.add(("E1", br["id"], b["id"]))
                        issues.append({"code": "E1", "severity": "error", "t": s["t"], "id": f"{br['id']}+{b['id']}",
                                       "msg": f"B-roll khung nhỏ «{br['id']}» đè chữ «{b['id']}» lúc {s['t']:.1f}s",
                                       "fix": "dời chữ sang vùng giữa hoặc đổi B-roll sang full"})
        face = face_at(faces, s["t"])
        if face:
            # chữ kinetic được phép ôm quanh đầu (tóc, trán) nhưng không được che mắt–mũi–miệng
            fw0, fh0 = face[2] / 1.3, face[3] / 1.6
            core = [face[0] + 0.15 * fw0, face[1] + 0.35 * fh0, fw0, fh0]
            for b in s["boxes"]:
                if b.get("layer") == "behind":
                    continue        # chữ nằm sau người: người che lên chữ, không che mặt
                fc = core if b.get("group") else face
                key = ("E10", b.get("group") or b["id"])
                if b.get("settled", True) and overlap_ratio(b, fc) > 0.12 and key not in seen:
                    seen.add(key)
                    issues.append({"code": "E10", "severity": "error", "t": s["t"], "id": b.get("group") or b["id"],
                                   "msg": f"«{b.get('group') or b['id']}» che {overlap_ratio(b, fc):.0%} khuôn mặt lúc {s['t']:.1f}s",
                                   "fix": "đổi zone, rút gọn chữ, hoặc dùng reframe fit-blur"})
        bs = [b for b in s["boxes"] if b.get("settled", True)]   # chỉ chấm khi chữ đã đứng yên
        for i in range(len(bs)):
            a = bs[i]
            if a["x"] < sx0 - 2 or a["y"] < sy0 - 2 or a["x"] + a["w"] > sx1 + 2 or a["y"] + a["h"] > sy1 + 2:
                key = ("E2", a.get("group") or a["id"])
                if key not in seen:
                    seen.add(key)
                    issues.append({"code": "E2", "severity": "error", "t": s["t"], "id": a.get("group") or a["id"],
                                   "msg": f"«{a.get('group') or a['id']}» ra ngoài vùng an toàn", "fix": "rút ngắn chữ hoặc đổi zone"})
            if a.get("fit", 1) < 0.62 and ("E3", a["id"]) not in seen:
                seen.add(("E3", a["id"]))
                issues.append({"code": "E3", "severity": "warn", "t": s["t"], "id": a["id"],
                               "msg": f"«{a['id']}» phải co chữ còn {a['fit']:.0%} vì quá dài", "fix": "viết ngắn lại ≤ 6 từ"})
            for b in bs[i + 1:]:
                if a.get("group") and a.get("group") == b.get("group"):
                    continue        # các từ trong cùng một cụm kinetic được phép chồng nhẹ (đúng phong cách)
                ov = _inter(a, b)
                small = min(a["w"] * a["h"], b["w"] * b["h"]) or 1
                if ov / small > 0.04:
                    key = ("E1", *sorted([a["id"], b["id"]]))
                    if key not in seen:
                        seen.add(key)
                        issues.append({"code": "E1", "severity": "error", "t": s["t"], "id": f"{a['id']}+{b['id']}",
                                       "msg": f"Chữ đè nhau: «{a['id']}» và «{b['id']}» lúc {s['t']:.1f}s",
                                       "fix": "dời một hiệu ứng sang thời điểm/vùng khác"})
    return issues


def check_cuts(tl, transcript):
    issues = []
    W = transcript["words"]
    for r in tl["ranges"]:
        for edge in ("s", "e"):
            t = r[edge]
            for w in W:
                if w["start"] + 0.03 < t < w["end"] - 0.03:
                    issues.append({"code": "E4", "severity": "error", "t": r.get("out_" + edge, 0),
                                   "msg": f"Điểm cắt {t:.2f}s rơi giữa từ «{w['text']}»", "fix": "chỉnh cuts theo ranh giới từ"})
    # phụ đề phải nằm trong thời lượng và đúng thứ tự
    last = -1
    for p in tl["captions"]["pages"]:
        if p["start"] < last - 1e-3 or p["end"] > tl["duration"] + 0.5:
            issues.append({"code": "E5", "severity": "error", "t": p["start"], "msg": f"Trang phụ đề {p['i']} sai thứ tự/thời lượng"})
        last = p["end"]
    return issues


def check_media(tl, final):
    issues, metrics = [], {}
    info = probe(final)
    metrics["duration"] = round(info["duration"], 2)
    if not info["has_audio"] or not info["has_video"]:
        issues.append({"code": "E9", "severity": "error", "msg": "Thiếu luồng hình hoặc tiếng"})
    if abs(info["duration"] - tl["duration"]) > 0.25:
        issues.append({"code": "E9", "severity": "warn", "msg": f"Độ dài {info['duration']:.2f}s ≠ timeline {tl['duration']:.2f}s"})
    md = (tl.get("target") or {}).get("max_duration")
    if md and info["duration"] > md + 0.5:
        issues.append({"code": "E8", "severity": "error", "msg": f"Dài {info['duration']:.1f}s > mục tiêu {md}s",
                       "fix": "cắt bớt câu ít giá trị trong edit-plan.cuts"})
    res = run([ffmpeg_bin(), "-hide_banner", "-nostats", "-i", final, "-filter_complex",
               "[0:a]ebur128=peak=true[ao];[0:v]blackdetect=d=0.4:pic_th=0.97,freezedetect=n=0.003:d=2.5[vo]",
               "-map", "[vo]", "-map", "[ao]", "-f", "null", "-"], capture=True, check=False)
    err = res.stderr
    mI = re.findall(r"I:\s+(-?[\d.]+) LUFS", err)
    mP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", err)
    if mI:
        metrics["lufs"] = float(mI[-1])
        target = (tl.get("target") or {}).get("lufs") or -14
        if abs(metrics["lufs"] - target) > 1.5:
            issues.append({"code": "E6", "severity": "error", "msg": f"Âm lượng {metrics['lufs']} LUFS, chuẩn {target}"})
    if mP:
        metrics["true_peak"] = float(mP[-1])
        if metrics["true_peak"] > -0.5:
            issues.append({"code": "E6", "severity": "error", "msg": f"Đỉnh âm {metrics['true_peak']} dBFS (có thể rè)"})
    for m in re.finditer(r"black_start:([\d.]+) black_end:([\d.]+)", err):
        issues.append({"code": "E7", "severity": "error", "t": float(m.group(1)), "msg": f"Khung đen {m.group(1)}–{m.group(2)}s"})
    for m in re.finditer(r"freeze_start: ([\d.]+)", err):
        issues.append({"code": "E7", "severity": "warn", "t": float(m.group(1)), "msg": f"Hình đứng yên từ {m.group(1)}s",
                       "fix": "chèn B-roll/hiệu ứng hoặc chuyển khổ fit-blur"})
    return issues, metrics


def contact_sheet(final, out_png, duration, n=12):
    """Ghép n khung đều nhau của thành phẩm thành 1 ảnh để Claude nhìn bằng mắt."""
    step = max(duration / n, 0.1)
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", final, "-vf",
         f"fps=1/{step:.3f},scale=-2:480,drawtext=fontfile={ROOT / 'effects/fonts/BeVietnamPro-Bold.ttf'}:"
         f"text='%{{pts\\:hms}}':x=8:y=8:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x2:padding=6:color=0x222222",
         "-frames:v", "1", out_png])
    return out_png


def run_qa(tl, transcript, final, project):
    work = Path(project) / "work" / tl["format_name"].replace(":", "x")
    work.mkdir(parents=True, exist_ok=True)
    issues = check_layout(tl, work) + check_cuts(tl, transcript)
    mi, metrics = check_media(tl, final)
    issues += mi
    sheet = contact_sheet(final, Path(project) / "out" / f"kiem-dinh.{tl['format_name'].replace(':', 'x')}.png", tl["duration"])
    errors = [i for i in issues if i["severity"] == "error"]
    warns = [i for i in issues if i["severity"] == "warn"]
    score = max(0, 100 - 15 * len(errors) - 3 * len(warns))
    report = {"format": tl["format_name"], "final": str(final), "passed": not errors, "score": score,
              "metrics": metrics, "issues": issues, "timeline_warnings": tl.get("warnings", []),
              "contact_sheet": str(sheet)}
    save(Path(project) / f"qa.{tl['format_name'].replace(':', 'x')}.json", report)
    return report
