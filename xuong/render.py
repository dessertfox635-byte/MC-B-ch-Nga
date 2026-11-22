"""Xuất phim: cắt + đổi khổ (ffmpeg) → lớp chữ (Chromium + GSAP) → trộn tiếng (giọng, lời dẫn, nhạc) → chuẩn âm lượng."""
import json
import re
from pathlib import Path

from . import ROOT
from .timeline import overlay_spec
from .util import ffmpeg_bin, node_bin, run, save, say


def _reframe_filter(src_w, src_h, w, h, reframe):
    mode = (reframe or {}).get("mode", "crop")
    xf = float((reframe or {}).get("x", 0.5))
    yf = float((reframe or {}).get("y", 0.5))
    ar, sar = w / h, src_w / src_h
    if abs(ar - sar) < 0.01:
        return f"scale={w}:{h}:flags=lanczos,setsar=1"
    if mode == "fit-blur":
        return (f"split=2[bgsrc][fgsrc];"
                f"[bgsrc]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=28:2,eq=brightness=-0.06[bg];"
                f"[fgsrc]scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    if sar > ar:   # nguồn rộng hơn → cắt hai bên
        cw = int(round(src_h * ar / 2) * 2)
        x = int((src_w - cw) * min(max(xf, 0), 1))
        return f"crop={cw}:{src_h}:{x}:0,scale={w}:{h}:flags=lanczos,setsar=1"
    ch = int(round(src_w / ar / 2) * 2)
    y = int((src_h - ch) * min(max(yf, 0), 1))
    return f"crop={src_w}:{ch}:0:{y},scale={w}:{h}:flags=lanczos,setsar=1"


def _camera_filter(tl, w, h):
    """Chuyển động máy quay giả lập trên khung đã đổi khổ:
    snap = phóng giật vào đúng từ nhấn (ramp 0.08s) · push = đẩy máy chậm dần đều · impact = chớp âm bản 2–3 khung."""
    zs = [z for z in tl.get("zooms", []) if z["type"] in ("snap", "push")]
    out = ""
    if zs:
        terms = []
        for z in zs:
            s, e, a = z["start"], z["end"], z["amount"]
            if z["type"] == "snap":
                terms.append(f"{a}*clip((t-{s})/0.08,0,1)*clip(({e}-t)/0.08,0,1)")
            else:
                terms.append(f"{a}*clip((t-{s})/{max(0.1, e - s):.3f},0,1)*lt(t,{e})")
        Z = "(1+" + "+".join(terms) + ")"
        fx = "+".join(f"{z['focus'][0]}*between(t,{z['start']},{z['end']})" for z in zs)
        fy = "+".join(f"{z['focus'][1]}*between(t,{z['start']},{z['end']})" for z in zs)
        out += (f",scale=w='2*trunc({w}*{Z}/2)':h='2*trunc({h}*{Z}/2)':eval=frame:flags=bilinear"
                f",crop={w}:{h}:x='(in_w-{w})*({fx})':y='(in_h-{h})*({fy})',setsar=1")
    for z in tl.get("zooms", []):
        if z["type"] == "impact":
            en = f"between(t,{z['start']},{z['end']})"
            out += f",negate=enable='{en}',eq=contrast=1.6:saturation=0:enable='{en}'"
    return out


def render_base(tl, src, out):
    """Một lượt ffmpeg: cắt theo các đoạn giữ lại (giữ hình–tiếng khớp nhau), làm mượt điểm cắt, đổi khổ."""
    w, h, fps = tl["format"]["w"], tl["format"]["h"], tl["format"]["fps"]
    si = tl["source"]
    parts, labels = [], []
    for k, r in enumerate(tl["ranges"]):
        d = r["e"] - r["s"]
        fade = min(0.012, d / 4)
        parts.append(f"[0:v]trim=start={r['s']:.3f}:end={r['e']:.3f},setpts=PTS-STARTPTS,fps={fps}[v{k}]")
        parts.append(f"[0:a]atrim=start={r['s']:.3f}:end={r['e']:.3f},asetpts=PTS-STARTPTS,"
                     f"afade=t=in:d={fade:.3f},afade=t=out:st={max(0, d - fade):.3f}:d={fade:.3f}[a{k}]")
        labels.append(f"[v{k}][a{k}]")
    parts.append(f"{''.join(labels)}concat=n={len(tl['ranges'])}:v=1:a=1[vc][ac]")
    parts.append(f"[vc]{_reframe_filter(si['width'], si['height'], w, h, tl.get('reframe'))}{_camera_filter(tl, w, h)}[vout]")
    script = Path(out).with_suffix(".filter.txt")
    script.write_text(";\n".join(parts), encoding="utf-8")
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", src, "-filter_complex_script", script,
         "-map", "[vout]", "-map", "[ac]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
         "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", out])
    return out


def render_overlay(tl, out, layer=None):
    spec_path = Path(out).with_suffix(".spec.json")
    save(spec_path, overlay_spec(tl))
    res = run([node_bin(), ROOT / "render" / "overlay.mjs", "render", spec_path, out] + (["--layer", layer] if layer else []), capture=True)
    say("  " + res.stdout.strip().splitlines()[-1])
    return out


def build_audio(tl, base, work, out):
    """Trộn: tiếng gốc + lời dẫn (giọng Bích Nga) + nhạc nền tự hạ khi có tiếng nói."""
    inputs = ["-i", base]
    filt, mix = [], ["[0:a]"]
    vo_files = []
    if tl["audio"]["voiceover"]:
        from .voice import synthesize
        for vo in tl["audio"]["voiceover"]:
            f = synthesize(vo["text"], vo["voice"], Path(work) / "vo")
            vo_files.append((vo, f))
    for k, (vo, f) in enumerate(vo_files, start=1):
        inputs += ["-i", f]
        ms = int(vo["start"] * 1000)
        filt.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vo['gain_db']}dB,adelay={ms}|{ms}[vo{k}]")
        mix.append(f"[vo{k}]")
    speech = "[speech]"
    if len(mix) > 1:
        filt.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first[speech]")
    else:
        filt.append("[0:a]anull[speech]")
    music = tl["audio"].get("music")
    final = "[speech]"
    if music and music.get("file"):
        mi = len(vo_files) + 1
        inputs += ["-stream_loop", "-1", "-i", str((ROOT / music["file"]) if not Path(music["file"]).is_absolute() else music["file"])]
        db = music.get("db", -20)
        dur = tl["duration"]
        filt.append("[speech]asplit=2[sp1][key]")
        filt.append(f"[{mi}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{dur:.3f},volume={db}dB,"
                    f"afade=t=in:d=0.8,afade=t=out:st={max(0, dur - 1.5):.3f}:d=1.5[mus]")
        if music.get("duck", True):
            filt.append("[mus][key]sidechaincompress=threshold=0.02:ratio=8:attack=20:release=400[musd]")
        else:
            filt.append("[key]anullsink;[mus]anull[musd]")
        filt.append("[sp1][musd]amix=inputs=2:normalize=0:duration=first[mixout]")
        final = "[mixout]"
    run([ffmpeg_bin(), "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filt), "-map", final,
         "-t", f"{tl['duration']:.3f}", "-c:a", "pcm_s16le", "-ar", "48000", out])
    return out


def measure_loudness(path):
    res = run([ffmpeg_bin(), "-hide_banner", "-nostats", "-i", path, "-af",
               "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", res.stderr, re.S)
    return json.loads(m.group(0)) if m else None


def render(tl, src, project, out_path):
    work = Path(project) / "work" / tl["format_name"].replace(":", "x")
    work.mkdir(parents=True, exist_ok=True)
    say(f"• [{tl['format_name']}] cắt + đổi khổ…")
    base = render_base(tl, src, work / "base.mkv")
    from .face import avoid_faces, detect
    roi = None
    if (tl.get("reframe") or {}).get("mode") == "fit-blur":
        si, W, H = tl["source"], tl["format"]["w"], tl["format"]["h"]
        k = min(W / si["width"], H / si["height"])
        fw, fh = si["width"] * k, si["height"] * k
        roi = ((W - fw) / 2, (H - fh) / 2, fw, fh)
    faces = detect(base, work / "faces.json", roi=roi)
    tl["faces"] = [s for s in faces["samples"] if s["box"]]
    moves = avoid_faces(tl, faces)
    tl.setdefault("warnings", []).extend(moves)
    say(f"  mặt người: thấy ở {faces['coverage']:.0%} khung" + (f"; dời {len(moves)} hiệu ứng khỏi mặt" if moves else ""))
    say(f"• [{tl['format_name']}] dựng chữ animation ({len(tl['overlays'])} hiệu ứng, {len(tl['captions']['pages'])} trang phụ đề)…")
    ov = render_overlay(tl, work / "overlay.mov", layer="front")
    behind = matte = None
    spec_path = Path(work / "overlay.mov").with_suffix(".spec.json")
    hb = run([node_bin(), ROOT / "render" / "overlay.mjs", "has-behind", spec_path], capture=True).stdout.strip().splitlines()[-1]
    if json.loads(hb).get("behind"):
        say("  có chữ nằm sau người nói → tách người khỏi nền…")
        from .matte import make_matte
        matte = make_matte(base, work / "matte.mkv")
        behind = render_overlay(tl, work / "overlay.behind.mov", layer="behind")
    say(f"• [{tl['format_name']}] trộn tiếng…")
    mix = build_audio(tl, base, work, work / "mix.wav")
    lufs = tl.get("target", {}).get("lufs") or -14
    m = measure_loudness(mix)
    ln = f"loudnorm=I={lufs}:TP=-1.5:LRA=11"
    if m:
        ln += (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
               f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    say(f"• [{tl['format_name']}] xuất bản cuối…")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    w, h = tl["format"]["w"], tl["format"]["h"]
    inputs, chain, last = [], [], "[0:v]"
    for k, br in enumerate(tl.get("broll", [])):
        f = br["file"] if Path(br["file"]).is_absolute() else str(ROOT / br["file"])
        d = br["end"] - br["start"]
        idx = 3 + k
        img = f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
        inputs += (["-loop", "1", "-t", f"{d:.3f}", "-i", f] if img else ["-ss", f"{br['in']:.3f}", "-t", f"{d:.3f}", "-i", f])
        if br["mode"] == "pip":   # khung nhỏ góc trên, vẫn thấy người nói
            fit = f"scale={int(w * 0.62)}:-2,pad=iw+12:ih+12:6:6:white"
            pos = f"x=(W-w)/2:y={int(h * 0.12)}"
        else:
            fit = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"
            pos = "x=0:y=0"
        chain.append(f"[{idx}:v]{fit},fps={tl['format']['fps']},format=yuva420p,fade=t=in:st=0:d=0.15:alpha=1,"
                     f"setpts=PTS-STARTPTS+{br['start']:.3f}/TB[b{k}]")
        chain.append(f"{last}[b{k}]overlay={pos}:eof_action=pass:enable='between(t,{br['start']:.3f},{br['end']:.3f})'[vb{k}]")
        last = f"[vb{k}]"
    if behind:
        bi, mi = 3 + len(tl.get("broll", [])), 4 + len(tl.get("broll", []))
        inputs += ["-i", behind, "-i", matte]
        off = "+".join(f"between(t,{b['start']:.3f},{b['end']:.3f})" for b in tl.get("broll", [])) or "0"
        chain.append(f"{last}split[vs1][vs2]")
        chain.append(f"[vs1][{bi}:v]overlay=0:0:format=auto[vt]")
        chain.append(f"[{mi}:v]format=gray,scale={w}:{h}[mk]")
        chain.append(f"[vs2][mk]alphamerge[person]")
        chain.append(f"[vt][person]overlay=0:0:format=auto:enable='not({off})'[vd]")
        last = "[vd]"
    chain.append(f"{last}[1:v]overlay=0:0:format=auto,format=yuv420p[v]")
    chain.append(f"[2:a]{ln},aresample=48000[a]")
    run([ffmpeg_bin(), "-y", "-loglevel", "error", "-i", base, "-i", ov, "-i", mix, *inputs,
         "-filter_complex", ";".join(chain),
         "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(tl["format"]["fps"]),
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{tl['duration']:.3f}", out_path])
    return out_path
