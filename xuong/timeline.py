"""Từ bản ghi + kế hoạch biên tập (edit-plan.json) → timeline xác định cho từng khổ hình.

Mọi hiệu ứng được neo vào CHỈ SỐ TỪ trong bản ghi gốc (at_word/until_word), không neo vào giây.
Nhờ vậy sau khi cắt, chữ vẫn khớp đúng câu nói — đây là chỗ lần trước làm hỏng khi sửa tay file CapCut.
"""
from .util import FORMATS

# vùng mặc định của từng hiệu ứng (khớp effects/effects.js)
EFFECT_ZONES = {
    "hook-title": "top", "keyword-pop": "center", "lower-third": "center", "checklist": "top",
    "comment-drop": "top", "counter": "center", "typewriter": "center", "headline-storm": "center",
    "sticker-burst": "center", "cta": "center",
}
DEFAULT_DUR = {"hook-title": 2.8, "keyword-pop": 1.6, "lower-third": 3.0, "checklist": 5.0, "comment-drop": 3.0,
               "counter": 2.5, "typewriter": 2.5, "headline-storm": 2.2, "sticker-burst": 1.4, "cta": 3.0}
MIN_DUR = 0.8

SIL = {"gap": 0.55, "head": 0.22, "tail": 0.34, "pre": 0.10, "breath_long": 0.24, "breath_sentence": 0.20,
       "breath": 0.14}


def keep_ranges(words, removed=frozenset(), hook=None, total=None, sil=None):
    """Trả về danh sách đoạn giữ lại theo thứ tự phát: [{"s","e","words":[i...]}] (giây trên file gốc)."""
    sil = {**SIL, **(sil or {})}
    n = len(words)
    kept = [i for i in range(n) if i not in removed]
    if hook:
        hs = [i for i in range(hook[0], hook[1] + 1) if i not in removed]
        order = hs + [i for i in kept if i not in set(hs)]
    else:
        order = kept
    groups = []
    for i in order:
        if groups:
            prev = groups[-1][-1]
            if i == prev + 1 and words[i]["start"] - words[prev]["end"] <= sil["gap"]:
                groups[-1].append(i)
                continue
        groups.append([i])
    total = total if total is not None else (words[-1]["end"] + 1.0 if words else 0)
    ranges = []
    for gi, g in enumerate(groups):
        a, b = words[g[0]], words[g[-1]]
        before = words[g[0] - 1]["end"] if g[0] > 0 else 0.0
        after = words[g[-1] + 1]["start"] if g[-1] + 1 < n else total
        pre = sil["head"] if gi == 0 else sil["pre"]
        gap_after = after - b["end"]
        if g[-1] + 1 >= n:
            post = sil["tail"]
        elif gap_after >= 2.0:
            post = sil["breath_long"]
        elif b["text"].endswith((".", "!", "?")):
            post = sil["breath_sentence"]
        else:
            post = sil["breath"]
        s = max(before, a["start"] - pre, 0.0)
        e = min(after, b["end"] + post, total)
        ranges.append({"s": round(s, 3), "e": round(e, 3), "words": g})
    # gộp các đoạn liền nhau trên file gốc
    merged = []
    for r in ranges:
        if merged and merged[-1]["words"][-1] + 1 == r["words"][0] and r["s"] - merged[-1]["e"] < 0.02:
            merged[-1]["e"] = r["e"]; merged[-1]["words"] += r["words"]
        else:
            merged.append(dict(r))
    return merged


def retime(words, ranges, fixes=None):
    """Đặt từng từ được giữ lên trục thời gian mới. fixes: {chỉ_số: "chữ sửa chính tả"}."""
    fixes = {int(k): v for k, v in (fixes or {}).items()}
    out, src2out, t = [], {}, 0.0
    for r in ranges:
        for i in r["words"]:
            w = words[i]
            s = t + max(0.0, w["start"] - r["s"])
            e = t + min(r["e"] - r["s"], w["end"] - r["s"])
            src2out[i] = len(out)
            out.append({"src": i, "text": fixes.get(i, w["text"]), "start": round(s, 3), "end": round(max(e, s + 0.04), 3)})
        r["out_s"] = round(t, 3)
        t += r["e"] - r["s"]
        r["out_e"] = round(t, 3)
    return out, src2out, round(t, 3)


def caption_pages(tw, max_chars=18, max_lines=2, gap_break=0.45):
    pages, cur, lines, line_len = [], [], [[]], 0

    def flush():
        nonlocal cur, lines, line_len
        if cur:
            pages.append({"i": len(pages), "start": cur[0]["start"], "end": cur[-1]["end"],
                          "lines": [[{"text": w["text"], "start": w["start"], "end": w["end"]} for w in l] for l in lines if l]})
        cur, lines, line_len = [], [[]], 0

    for k, w in enumerate(tw):
        if cur and (w["start"] - cur[-1]["end"] > gap_break):
            flush()
        add = len(w["text"]) + (1 if lines[-1] else 0)
        ends_sentence = w["text"].endswith((".", "!", "?"))
        # không để một từ cuối câu đứng lẻ sang trang mới: cho phép vượt dòng tối đa 6 ký tự
        slack = 6 if ends_sentence else 0
        if line_len + add > max_chars + slack and lines[-1]:
            if len(lines) >= max_lines:
                flush(); add = len(w["text"])
            else:
                lines.append([]); line_len = 0; add = len(w["text"])
        lines[-1].append(w); cur.append(w); line_len += add
        if w["text"].endswith((".", "!", "?")):
            flush()
    flush()
    for a, b in zip(pages, pages[1:]):
        a["end"] = round(min(a["end"] + 0.3, b["start"]), 3)
    if pages:
        pages[-1]["end"] = round(pages[-1]["end"] + 0.3, 3)
    return pages


VI_STOP = set("""và là của có những các một để thì mà này đó kia với cho khi rất cũng được đã sẽ đang như từ trong ra vào
lên xuống mình bạn tôi chúng ta họ nó hãy nhé nha ạ ơi thế nào gì ai đâu sao không chưa rồi nếu nhưng hay hoặc vì nên
thật luôn bằng về theo hôm nay ở tại lại còn chỉ đều nhiều ít nữa vậy thôi đi ấy anh chị em các bạn quý vị mọi người
the a an and or to of in on at is are was it this that for with you i we my your just so but""".split())


def auto_heroes(tw):
    """Khi Claude chưa chọn: mỗi cụm 1 từ khoá = cặp từ (hoặc từ đơn) giàu nghĩa nhất, tránh hư từ."""
    import re as _re
    norm = lambda t: _re.sub(r"[^\w]", "", t.lower())
    picks, used = [], set()
    i = 0
    for ph in _phrase_bounds(tw):
        best, score = None, 0
        for j in range(ph[0], ph[1] + 1):
            a = norm(tw[j]["text"])
            if not a or a in VI_STOP or a.isdigit() and len(a) < 2:
                continue
            sc = len(a) + (2 if tw[j]["text"][0].isupper() else 0) + (3 if a.isdigit() else 0)
            span = (j, j)
            if j + 1 <= ph[1]:
                b2 = norm(tw[j + 1]["text"])
                if b2 and b2 not in VI_STOP and not tw[j]["text"].endswith((",", ".")):
                    sc2 = len(a) + len(b2) + 2
                    if sc2 > sc:
                        sc, span = sc2, (j, j + 1)
            if sc > score:
                best, score = span, sc
        if best:
            picks.append((tw[best[0]]["src"], tw[best[1]]["src"]))
    return picks


def _re_norm(t):
    import re as _re
    return _re.sub(r"[^\w]", "", t.lower())


def _phrase_bounds(tw, max_words=8, max_dur=3.2, gap=0.35, unit_of=None):
    unit_of = unit_of or {}
    out, s = [], 0
    for k in range(len(tw)):
        # không cắt đôi một từ khoá ghép (vd. «bí | quyết»)
        if k + 1 < len(tw) and tw[k]["src"] in unit_of and unit_of.get(tw[k + 1]["src"]) == unit_of[tw[k]["src"]]:
            continue
        end_here = (k == len(tw) - 1
                    or tw[k]["text"].endswith((".", "!", "?")) and k - s >= 1
                    or tw[k]["text"].endswith((",", ";", ":")) and k - s >= 2
                    or tw[k + 1]["start"] - tw[k]["end"] > gap
                    or k - s + 1 >= max_words
                    or tw[k]["end"] - tw[s]["start"] > max_dur)
        if end_here:
            out.append((s, k)); s = k + 1
    # gộp cụm chỉ có 1 từ vào cụm trước nếu liền mạch (tránh «kỹ.» đứng lẻ)
    merged = []
    for a, b in out:
        if merged and b == a and tw[a]["start"] - tw[merged[-1][1]]["end"] < 0.5:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


def kinetic_phrases(tw, hero_spans):
    """Cụm chữ kiểu kinetic: từ hiện đúng lúc nói, giữ tới hết cụm. hero_spans: [(from_src, to_src)]."""
    unit_of = {}
    for u, (a, b) in enumerate(hero_spans):
        for x in range(int(a), int(b) + 1):
            unit_of[x] = u
    phrases = []
    bounds = _phrase_bounds(tw, unit_of=unit_of)
    for n, (a, b) in enumerate(bounds):
        def tier(w):
            if w["src"] in unit_of:
                return "hero"
            t = _re_norm(w["text"])
            return "mid" if (t and t not in VI_STOP and (len(t) >= 5 or t.isdigit())) else "small"
        ws = [{"text": w["text"], "start": w["start"], "end": w["end"], "hero": w["src"] in unit_of,
               "unit": unit_of.get(w["src"]), "tier": tier(w)} for w in tw[a:b + 1]]
        start = tw[a]["start"]
        nxt = tw[bounds[n + 1][0]]["start"] if n + 1 < len(bounds) else tw[b]["end"] + 0.6
        phrases.append({"i": n, "start": round(start - 0.02, 3), "end": round(min(tw[b]["end"] + 0.35, nxt - 0.01), 3), "words": ws})
    return phrases


def resolve_overlays(items, duration, src2out, tw, captions_on=True, fmt=None):
    """Neo hiệu ứng vào từ, gán vùng, chống đè: cùng vùng không được trùng thời gian."""
    warnings, placed = [], []

    def word_time(idx, edge):
        idx = int(idx)
        # nếu từ đã bị cắt thì bám từ giữ lại gần nhất
        cand = sorted(src2out.keys(), key=lambda j: (abs(j - idx), j))
        if not cand:
            return 0.0
        w = tw[src2out[cand[0]]]
        return w[edge]

    for k, ov in enumerate(items):
        ov = dict(ov)
        if ov.pop("_dropped", False) or fmt in ov.pop("dropped_formats", []):
            continue
        zbf = ov.pop("zone_by_format", {})
        if fmt in zbf:
            ov["zone"] = zbf[fmt]
        ov.pop("_tried", None)
        ov["plan_index"] = k
        typ = ov.get("type")
        if typ not in EFFECT_ZONES:
            warnings.append(f"Bỏ hiệu ứng không tồn tại: {typ}")
            continue
        ov.setdefault("id", f"{typ}-{k}")
        if "at_word" in ov:
            start = word_time(ov["at_word"], "start")
        else:
            start = float(ov.get("start", 0))
            if start < 0:
                start = duration + start
        if "until_word" in ov:
            end = word_time(ov["until_word"], "end") + 0.25
        elif "end" in ov and "at_word" not in ov:
            end = float(ov["end"]); end = duration + end if end < 0 else end
        else:
            end = start + float(ov.get("duration", DEFAULT_DUR[typ]))
        # mục checklist có thể neo vào từ
        if typ == "checklist":
            its = []
            for it in ov.get("items", []):
                it = {"text": it} if isinstance(it, str) else dict(it)
                if "at_word" in it:
                    it["at"] = round(max(0.2, word_time(it.pop("at_word"), "start") - start), 3)
                its.append(it)
            ov["items"] = its
        zone = ov.get("zone") or EFFECT_ZONES[typ]
        if zone == "lower" and captions_on:
            zone = "center"
            warnings.append(f"{ov['id']}: vùng dưới dành cho phụ đề → dời lên giữa")
        start, end = max(0.0, start), min(duration, end)
        ov.update(start=round(start, 3), end=round(end, 3), zone=zone)
        for k2 in ("at_word", "until_word", "duration"):
            ov.pop(k2, None)
        placed.append(ov)

    placed.sort(key=lambda o: (o["start"], o.get("priority", 5)))
    final, busy = [], {}
    for ov in placed:
        z = ov["zone"]
        zones = ["top", "center"] if z == "full" else [z]
        last = max([busy.get(zz, 0.0) for zz in zones] + [busy.get("full", 0.0)])
        if ov["start"] < last:
            shifted = last + 0.05
            if ov["end"] - shifted >= MIN_DUR:
                warnings.append(f"{ov['id']}: trùng vùng {z} → lùi tới {shifted:.2f}s")
                ov["start"] = round(shifted, 3)
            else:
                warnings.append(f"{ov['id']}: trùng vùng {z}, không đủ chỗ → bỏ")
                continue
        if ov["end"] - ov["start"] < MIN_DUR:
            warnings.append(f"{ov['id']}: quá ngắn ({ov['end'] - ov['start']:.2f}s) → bỏ")
            continue
        for zz in zones:
            busy[zz] = ov["end"]
        final.append(ov)
    return final, warnings


def build(transcript, plan, fmt, source_info):
    words = transcript["words"]
    removed = set()
    for c in plan.get("cuts", []):
        removed.update(range(int(c["from_word"]), int(c["to_word"]) + 1))
    hook = plan.get("hook")
    hook = (int(hook["from_word"]), int(hook["to_word"])) if hook else None
    ranges = keep_ranges(words, frozenset(removed), hook, total=source_info["duration"], sil=plan.get("silence"))
    tw, src2out, duration = retime(words, ranges, plan.get("caption_fixes"))
    w, h = FORMATS[fmt]
    vertical = h > w
    cap = plan.get("captions", {"style": "pop", "enabled": True})
    phrases = []
    if cap.get("style") == "kinetic" and cap.get("enabled", True):
        spans = cap.get("hero") or auto_heroes(tw)
        phrases = kinetic_phrases(tw, [tuple(x) for x in spans])
        pages = []
    else:
        pages = caption_pages(tw, max_chars=cap.get("max_chars", 18 if vertical else 32)) if cap.get("enabled", True) else []
    overlays, warns = resolve_overlays(plan.get("overlays", []), duration, src2out, tw, captions_on=bool(pages or phrases), fmt=fmt)
    audio = {"music": plan.get("music"), "voiceover": []}
    for k, vo in enumerate(plan.get("voiceover", [])):
        at = vo.get("start", 0)
        if "at_word" in vo and src2out:
            j = min(src2out, key=lambda x: abs(x - int(vo["at_word"])))
            at = tw[src2out[j]]["start"]
        audio["voiceover"].append({"id": f"vo-{k}", "text": vo["text"], "voice": vo.get("voice", "bich-nga"),
                                   "start": round(float(at), 3), "gain_db": vo.get("gain_db", 0)})
    broll = []
    for k, br in enumerate(plan.get("broll", [])):
        st = tw[src2out[min(src2out, key=lambda x: abs(x - int(br["at_word"])))]]["start"] if "at_word" in br and src2out else float(br.get("start", 0))
        if "until_word" in br and src2out:
            en = tw[src2out[min(src2out, key=lambda x: abs(x - int(br["until_word"])))]]["end"]
        else:
            en = st + float(br.get("duration", 3.0))
        broll.append({"id": f"broll-{k}", "file": br["file"], "start": round(st, 3), "end": round(min(en, duration), 3),
                      "mode": br.get("mode", "full"), "in": float(br.get("in", 0))})
    zooms = []
    for k, z in enumerate(plan.get("zooms", [])):
        wt = lambda idx, edge: tw[src2out[min(src2out, key=lambda x: abs(x - int(idx)))]][edge]
        st = wt(z["at_word"], "start") if "at_word" in z and src2out else float(z.get("start", 0))
        typ = z.get("type", "snap")
        dflt = {"snap": 1.2, "push": 3.0, "impact": 0.1}.get(typ, 1.2)
        en = wt(z["until_word"], "end") if "until_word" in z and src2out else st + float(z.get("duration", dflt))
        if typ in ("snap", "push", "impact") and en - st >= 0.06:
            zooms.append({"type": typ, "start": round(st, 3), "end": round(min(en, duration), 3),
                          "amount": float(z.get("amount", {"snap": 0.18, "push": 0.10}.get(typ, 0))),
                          "focus": z.get("focus", [0.5, 0.38])})
    fps = plan.get("fps", 30)
    return {
        "version": 1, "format_name": fmt,
        "format": {"w": w, "h": h, "fps": fps},
        "source": source_info, "duration": duration,
        "reframe": (plan.get("reframe_by_format") or {}).get(fmt) or plan.get("reframe", {"mode": "crop", "x": 0.5}),
        "ranges": [{"s": r["s"], "e": r["e"], "out_s": r["out_s"], "out_e": r["out_e"]} for r in ranges],
        "removed_words": sorted(removed), "words": tw,
        "theme": plan.get("theme", {}),
        "overlays": overlays,
        "captions": {"style": cap.get("style", "pop"), "zone": "lower", "pages": pages, **({"phrases": phrases} if phrases else {})},
        "audio": audio, "broll": broll, "zooms": zooms, "warnings": warns,
        "target": {"max_duration": plan.get("max_duration"), "lufs": plan.get("lufs", -14)},
    }


def overlay_spec(tl):
    spec = {k: tl[k] for k in ("format", "duration", "theme", "overlays", "captions")}
    spec["faces"] = tl.get("faces", [])
    return spec
