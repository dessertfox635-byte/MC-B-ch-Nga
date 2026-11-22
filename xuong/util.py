import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import ROOT


def ffmpeg_bin() -> str:
    return os.environ.get("FFMPEG", "ffmpeg")


def ffprobe_bin() -> str:
    return os.environ.get("FFPROBE", "ffprobe")


def run(cmd, check=True, capture=False, cwd=None):
    cmd = [str(c) for c in cmd]
    if os.environ.get("XUONG_DEBUG"):
        print("$", " ".join(cmd), file=sys.stderr)
    res = subprocess.run(cmd, cwd=cwd, text=True,
                         stdout=subprocess.PIPE if capture else None,
                         stderr=subprocess.PIPE if capture else None)
    if check and res.returncode != 0:
        msg = (res.stderr or "")[-3000:] if capture else ""
        raise RuntimeError(f"Lệnh lỗi ({res.returncode}): {' '.join(cmd[:6])} ...\n{msg}")
    return res


def probe(path) -> dict:
    out = run([ffprobe_bin(), "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
              capture=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    info = {"duration": float(d["format"].get("duration", 0)), "has_audio": a is not None, "has_video": v is not None}
    if v:
        w, h = int(v["width"]), int(v["height"])
        rot = 0
        for sd in v.get("side_data_list", []) or []:
            if "rotation" in sd:
                rot = int(sd["rotation"])
        rot = int(v.get("tags", {}).get("rotate", rot) or rot)
        if abs(rot) % 180 == 90:
            w, h = h, w
        num, den = (v.get("avg_frame_rate") or "30/1").split("/")
        fps = float(num) / float(den) if float(den) else 30.0
        info.update(width=w, height=h, fps=fps)
    return info


def load(path, default=None):
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save(path, data):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def node_bin() -> str:
    return os.environ.get("NODE", shutil.which("node") or "node")


def say(msg):
    print(msg, file=sys.stderr, flush=True)


FORMATS = {
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}


def project_paths(project: Path) -> dict:
    project = Path(project)
    return {
        "dir": project,
        "meta": project / "project.json",
        "audio16k": project / "work" / "audio16k.wav",
        "transcript": project / "transcript.json",
        "hints": project / "hints.md",
        "plan": project / "edit-plan.json",
        "timeline": lambda fmt: project / f"timeline.{fmt.replace(':', 'x')}.json",
        "work": project / "work",
        "out": project / "out",
        "qa": lambda fmt: project / f"qa.{fmt.replace(':', 'x')}.json",
    }


ROOT = ROOT
