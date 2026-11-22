"""Bảng điều khiển dòng lệnh của Xưởng Phim.

  python -m xuong doctor                         kiểm tra máy còn thiếu gì
  python -m xuong new <video> [--name ten]       tạo dự án từ một file quay
  python -m xuong transcribe <dự án>             nghe → chữ (Whisper, tiếng Việt)
  python -m xuong hints <dự án>                  gợi ý cắt (nói vấp, từ đệm) → hints.md
  python -m xuong plan-auto <dự án>              kế hoạch biên tập tự động (khi chạy không có Claude)
  python -m xuong make <dự án> [--format 9:16]   dựng timeline → xuất phim → kiểm định (thoát mã 1 nếu trượt)
  python -m xuong auto <video>                   chạy hết từ đầu đến cuối không cần Claude
  python -m xuong effects                        liệt kê hiệu ứng chữ
  python -m xuong voice check|prepare|say ...    Agent 3: giọng Bích Nga
"""
import argparse
import datetime as dt
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from . import ROOT
from .util import FORMATS, load, probe, project_paths, save, say


def slugify(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().replace("đ", "d")
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()[:40] or "video"


def brand():
    return load(ROOT / "config" / "brand.json", {})


def cmd_new(a):
    src = Path(a.video).resolve()
    if not src.exists():
        sys.exit(f"Không thấy file: {src}")
    name = a.name or slugify(src.stem)
    proj = ROOT / "projects" / f"{dt.date.today():%Y%m%d}-{name}"
    proj.mkdir(parents=True, exist_ok=True)
    info = probe(src)
    if not info["has_audio"]:
        sys.exit("File không có tiếng – Xưởng Phim cần lời nói để dựng.")
    meta = {"name": name, "source": str(src), "source_info": info, "brief": a.brief or "", "created": dt.datetime.now().isoformat(timespec="seconds")}
    save(proj / "project.json", meta)
    print(proj)
    return proj


def cmd_transcribe(a):
    from .transcribe import extract_audio, transcribe
    P = project_paths(a.project)
    meta = load(P["meta"])
    extract_audio(meta["source"], P["audio16k"])
    transcribe(P["audio16k"], P["transcript"], model_name=a.model)


def cmd_hints(a):
    from .transcribe import hints, hints_markdown
    P = project_paths(a.project)
    tr = load(P["transcript"])
    h = hints(tr)
    save(P["dir"] / "hints.json", h)
    P["hints"].write_text(hints_markdown(tr, h), encoding="utf-8")
    print(P["hints"])


def auto_plan(tr, h, meta):
    """Kế hoạch tối thiểu không cần AI: cắt lặp + từ đệm, thanh tên đầu video, nút theo dõi cuối video."""
    b = brand()
    cuts = [{"from_word": r["cut_from"], "to_word": r["cut_to"], "reason": "lặp"} for r in h["repeats"]]
    cuts += [{"from_word": i, "to_word": i, "reason": "từ đệm"} for i in h["fillers"]]
    W = tr["words"]
    overlays = []
    if b.get("name") and W:
        overlays.append({"type": "lower-third", "at_word": 0, "duration": 3.0, "text": b["name"], "subtext": b.get("role", "")})
    if b.get("cta"):
        overlays.append({"type": "cta", "start": -3.0, "end": -0.2, "text": b["cta"]})
    return {"title": meta.get("name"), "formats": b.get("default_formats", ["9:16"]), "cuts": cuts,
            "captions": {"style": b.get("caption_style", "kinetic"), "enabled": True}, "overlays": overlays, "theme": b.get("theme", {}),
            "music": None, "voiceover": [], "reframe": {"mode": "crop", "x": 0.5}, "_auto": True}


def cmd_plan_auto(a):
    P = project_paths(a.project)
    tr, meta = load(P["transcript"]), load(P["meta"])
    h = load(P["dir"] / "hints.json")
    if h is None:
        from .transcribe import hints
        h = hints(tr)
    if P["plan"].exists() and not a.force:
        sys.exit("edit-plan.json đã có (do Claude viết?). Dùng --force để ghi đè.")
    save(P["plan"], auto_plan(tr, h, meta))
    print(P["plan"])


def cmd_make(a):
    from .qa import run_qa
    from .render import render
    from .timeline import build
    P = project_paths(a.project)
    meta, tr, plan = load(P["meta"]), load(P["transcript"]), load(P["plan"])
    if plan is None:
        sys.exit("Thiếu edit-plan.json")
    fmts = [a.format] if a.format else plan.get("formats", ["9:16"])
    outbox = ROOT / "outbox" / P["dir"].name
    outbox.mkdir(parents=True, exist_ok=True)
    results = []
    for fmt in fmts:
        if fmt not in FORMATS:
            sys.exit(f"Khổ không hỗ trợ: {fmt}")
        tag = fmt.replace(":", "x")
        final = P["out"] / f"{meta['name']}.{tag}.mp4"
        for rnd in range(a.fix + 1):
            tl = build(tr, plan, fmt, meta["source_info"])
            for w in tl["warnings"]:
                say("  ! " + w)
            if not a.qa_only:
                render(tl, meta["source"], P["dir"], final)
            else:   # dùng lại vị trí mặt đã đo ở lần xuất trước
                tl["faces"] = (load(P["timeline"](fmt)) or {}).get("faces", [])
            save(P["timeline"](fmt), tl)            # lưu sau khi bộ máy dời chữ khỏi mặt
            say(f"• [{fmt}] kiểm định (vòng {rnd + 1})…")
            rep = run_qa(tl, tr, final, P["dir"])
            mark = "ĐẠT" if rep["passed"] else "CHƯA ĐẠT"
            say(f"  {mark} – điểm {rep['score']}/100 – {rep['metrics']}")
            for i in rep["issues"]:
                say(f"    [{i['severity']}] {i['code']} {i['msg']}" + (f" → {i['fix']}" if i.get("fix") else ""))
            if rep["passed"] or a.qa_only or rnd == a.fix:
                break
            applied = autofix(plan, tl, rep, fmt)
            if not applied:
                say("  Máy không còn cách sửa tự động – chuyển cho Claude Kiểm định.")
                break
            for x in applied:
                say("  ↻ tự sửa: " + x)
            plan.setdefault("autofix_log", []).extend(f"[{fmt}] {x}" for x in applied)
            save(P["plan"], plan)
        results.append(rep)
        shutil.copy2(final, outbox / final.name)
        shutil.copy2(rep["contact_sheet"], outbox / Path(rep["contact_sheet"]).name)
    write_report(P, meta, plan, results, outbox)
    print(json.dumps({"passed": all(r["passed"] for r in results), "outbox": str(outbox),
                      "results": [{"format": r["format"], "score": r["score"], "errors": sum(i["severity"] == "error" for i in r["issues"])} for r in results]},
                     ensure_ascii=False))
    return 0 if all(r["passed"] for r in results) else 1


def autofix(plan, tl, rep, fmt):
    """Cách sửa máy móc cho lỗi kỹ thuật. Lỗi biên tập (quá dài, nội dung) để Claude quyết."""
    applied = []
    ovs = {o["id"]: o for o in tl["overlays"]}
    errs = [i for i in rep["issues"] if i["severity"] == "error"]
    # chữ/phụ đề che mặt ở khổ đang cắt sát → đổi sang khung nền mờ để mặt nhỏ lại
    cap_face = [i for i in errs if i["code"] == "E10" and str(i.get("id", "")).startswith("cap-")]
    if cap_face and (tl.get("reframe") or {}).get("mode", "crop") == "crop":
        plan.setdefault("reframe_by_format", {})[fmt] = {"mode": "fit-blur"}
        applied.append("phụ đề che mặt → khung nền mờ (fit-blur) cho khổ " + fmt)
    for i in errs:
        if i["code"] in ("E10", "E2", "E1") and not str(i.get("id", "")).startswith("cap-"):
            for oid in str(i.get("id", "")).split("+"):
                ov = ovs.get(oid)
                if not ov or "plan_index" not in ov:
                    continue
                po = plan["overlays"][ov["plan_index"]]
                tried = po.setdefault("_tried", [])
                if ov["zone"] not in tried:
                    tried.append(ov["zone"])
                alt = [z for z in ("top", "center") if z not in tried]
                if alt:
                    po.setdefault("zone_by_format", {})[fmt] = alt[0]
                    applied.append(f"{oid}: {i['code']} → dời sang vùng {alt[0]}")
                else:
                    po.setdefault("dropped_formats", []).append(fmt)
                    applied.append(f"{oid}: {i['code']} không còn vùng trống → bỏ hiệu ứng ở khổ {fmt}")
                break
    return applied


def write_report(P, meta, plan, results, outbox):
    tr = load(P["transcript"])
    lines = [f"# Báo cáo dựng: {meta['name']}", "", f"- Nguồn: `{meta['source']}`", f"- Yêu cầu: {meta.get('brief') or '(không có)'}",
             f"- Kế hoạch do: {'máy (tự động)' if plan.get('_auto') else 'Claude biên tập'}", ""]
    cut_words = sum(int(c['to_word']) - int(c['from_word']) + 1 for c in plan.get("cuts", []))
    lines.append(f"## Biên tập\n- Cắt {cut_words} từ ({len(plan.get('cuts', []))} chỗ): " +
                 "; ".join(f"«{' '.join(w['text'] for w in tr['words'][int(c['from_word']):int(c['to_word']) + 1])}» ({c.get('reason', '')})" for c in plan.get('cuts', [])[:12]))
    if plan.get("hook"):
        h = plan["hook"]
        lines.append(f"- Đưa câu mở đầu (hook) lên đầu: từ {h['from_word']}–{h['to_word']}")
    lines.append(f"- Hiệu ứng: " + ", ".join(o["type"] for o in plan.get("overlays", [])))
    if plan.get("voiceover"):
        lines.append(f"- Lời dẫn giọng AI (có watermark): {len(plan['voiceover'])} câu")
    lines.append("\n## Thành phẩm")
    for r in results:
        lines.append(f"- **{r['format']}**: `{Path(r['final']).name}` — {'ĐẠT' if r['passed'] else 'CHƯA ĐẠT'} {r['score']}/100, "
                     f"{r['metrics'].get('duration')}s, {r['metrics'].get('lufs')} LUFS")
        for i in r["issues"]:
            lines.append(f"  - [{i['severity']}] {i['msg']}")
    (outbox / "BAO-CAO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_auto(a):
    a.name, a.brief = a.name, a.brief
    proj = cmd_new(a)
    ns = argparse.Namespace(project=proj, model=a.model, force=True, format=None, qa_only=False, fix=2)
    cmd_transcribe(ns); cmd_hints(ns); cmd_plan_auto(ns)
    return cmd_make(ns)


def cmd_effects(a):
    from .timeline import DEFAULT_DUR, EFFECT_ZONES
    for k in EFFECT_ZONES:
        print(f"{k:16s} vùng={EFFECT_ZONES[k]:7s} mặc định {DEFAULT_DUR[k]}s")


def cmd_voice(a):
    from . import voice
    if a.vcmd == "check":
        try:
            c = voice.check_consent(a.voice)
            print(f"✓ Giấy đồng ý hợp lệ cho «{a.voice}»: phạm vi {c.get('scope')}, hết hạn {c.get('expires') or 'không'}")
        except voice.ConsentError as e:
            sys.exit(f"✗ {e}")
    elif a.vcmd == "prepare":
        voice.prepare_reference(a.voice, a.sources)
    elif a.vcmd == "say":
        out = voice.synthesize(a.text, a.voice, Path(a.out).parent if a.out else ROOT / "outbox" / "giong")
        if a.out:
            shutil.move(out, a.out); shutil.move(Path(out).with_suffix(".json"), Path(a.out).with_suffix(".json"))
            out = a.out
        print(out)


def cmd_doctor(a):
    from .doctor import main
    return main()


def main(argv=None):
    p = argparse.ArgumentParser(prog="xuong", description="Xưởng Phim – dựng phim tự động")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("new"); s.add_argument("video"); s.add_argument("--name"); s.add_argument("--brief"); s.set_defaults(f=cmd_new)
    s = sub.add_parser("transcribe"); s.add_argument("project", type=Path); s.add_argument("--model"); s.set_defaults(f=cmd_transcribe)
    s = sub.add_parser("hints"); s.add_argument("project", type=Path); s.set_defaults(f=cmd_hints)
    s = sub.add_parser("plan-auto"); s.add_argument("project", type=Path); s.add_argument("--force", action="store_true"); s.set_defaults(f=cmd_plan_auto)
    s = sub.add_parser("make"); s.add_argument("project", type=Path); s.add_argument("--format"); s.add_argument("--qa-only", action="store_true"); s.add_argument("--fix", type=int, default=2); s.set_defaults(f=cmd_make)
    s = sub.add_parser("auto"); s.add_argument("video"); s.add_argument("--name"); s.add_argument("--brief"); s.add_argument("--model"); s.set_defaults(f=cmd_auto)
    s = sub.add_parser("effects"); s.set_defaults(f=cmd_effects)
    s = sub.add_parser("doctor"); s.set_defaults(f=cmd_doctor)
    s = sub.add_parser("voice"); vs = s.add_subparsers(dest="vcmd", required=True)
    v = vs.add_parser("check"); v.add_argument("voice")
    v = vs.add_parser("prepare"); v.add_argument("voice"); v.add_argument("sources", nargs="+")
    v = vs.add_parser("say"); v.add_argument("voice"); v.add_argument("text"); v.add_argument("--out")
    s.set_defaults(f=cmd_voice)
    a = p.parse_args(argv)
    from .voice import ConsentError
    try:
        rc = a.f(a)
    except ConsentError as e:
        print(f"✗ TỪ CHỐI: {e}", file=sys.stderr)
        return 3
    return rc if isinstance(rc, int) else 0


if __name__ == "__main__":
    sys.exit(main())
