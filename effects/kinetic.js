/*
 * Kiểu chữ "kinetic" – chữ bám lời nói, xếp thành cụm quanh người nói.
 * Phân tích từ video mẫu (invideo-style), làm lại từ đầu:
 *   - mỗi từ hiện đúng lúc được nói, ở lại tới hết cụm câu rồi xoá sạch;
 *   - 2 cấp chữ: từ thường trắng mảnh nhỏ; TỪ KHOÁ đỏ đậm khổng lồ (3–6 lần);
 *   - bố cục tự do: so le, lệch dòng, chồng nhẹ, từ khoá xoay hoặc uốn vòng cung quanh đầu;
 *   - kiểu xuất hiện của từ khoá: pixel, tumble (lộn từng chữ cái), blurzoom, slam, pop;
 *   - đặt cụm chữ vào phía trống của khung, tránh mặt người nói.
 * phrase = {i,start,end,layout?,words:[{text,start,end,hero,unit}]}
 * ctx.faceAt(t) -> [x,y,w,h] | null  (toạ độ khung ra)
 */
(function () {
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function seeded(str) {
    let h = 2166136261;
    for (const ch of String(str)) { h ^= ch.codePointAt(0); h = Math.imul(h, 16777619); }
    return () => { h ^= h << 13; h ^= h >>> 17; h ^= h << 5; return ((h >>> 0) % 100000) / 100000; };
  }
  const HERO_FX = ["pixel", "tumble", "blurzoom", "slam", "pop"];

  function units(words) {
    // gộp các từ khoá liền nhau thành một khối (vd. «sự kiện»), từ thường gộp thành dòng ngắn
    const out = [];
    for (const w of words) {
      const last = out[out.length - 1];
      if (w.hero && last && last.hero && last.unit === w.unit) { last.words.push(w); continue; }
      const mid = w.tier === "mid";
      if (!w.hero && !mid && last && !last.hero && !last.mid && last.words.length < 2 &&
          last.words.reduce((n, x) => n + x.text.length + 1, 0) + w.text.length <= 12) { last.words.push(w); continue; }
      out.push({ hero: !!w.hero, mid, unit: w.unit, words: [w] });
    }
    return out;
  }

  function region(ctx, face, busy) {
    const { w, h, vertical } = ctx;
    const S = vertical ? { x0: .05 * w, y0: .09 * h, x1: .86 * w, y1: .79 * h } : { x0: .05 * w, y0: .07 * h, x1: .95 * w, y1: .93 * h };
    const pad = 0.04 * Math.min(w, h);
    // khoét bỏ phần đang có hiệu ứng khác (giữ phía còn rộng hơn)
    const carve = r => {
      for (const b of busy || []) {
        if (b.x < r.x1 && b.x + b.w > r.x0 && b.y < r.y1 && b.y + b.h > r.y0) {
          if (b.y - r.y0 >= r.y1 - (b.y + b.h)) r.y1 = b.y - pad * 0.5; else r.y0 = b.y + b.h + pad * 0.5;
        }
      }
      return r;
    };
    const area = r => Math.max(0, r.x1 - r.x0) * Math.max(0, r.y1 - r.y0);
    if (!face) return carve({ ...S, side: "full" });
    const [fx, fy, fw, fh] = face;
    const cands = (vertical
      ? [{ ...S, y1: Math.min(S.y1, fy - pad), side: "above" }, { ...S, y0: Math.max(S.y0, fy + fh + pad), side: "below" }]
      : [{ ...S, x1: Math.min(S.x1, fx - pad), side: "left" }, { ...S, x0: Math.max(S.x0, fx + fw + pad), side: "right" }]).map(carve);
    cands.sort((a, b) => area(b) - area(a));
    const best = cands[0];
    const minW = vertical ? .6 * w : .26 * w, minH = vertical ? .12 * h : .4 * h;
    if (best.x1 - best.x0 >= minW && best.y1 - best.y0 >= minH) return best;
    const full = carve({ ...S, side: "full" });
    return area(full) > area(best) ? full : best;
  }

  function build(el, ph, ctx) {
    const { w, h, vertical } = ctx;
    const rnd = seeded("k" + ph.i + ph.words.map(x => x.text).join(""));
    const theme = ctx.theme || {};
    const hero = theme.hero || "#E3120B", ink = theme.ink_light || "#F4F4F2";
    el.style.left = "0px"; el.style.top = "0px"; el.style.width = w + "px"; el.style.height = h + "px";
    el.dataset.split = "1";
    const mid = (ph.start + ph.end) / 2;
    const face = ctx.faceAt ? (ctx.faceAt(mid) || ctx.faceAt(ph.start)) : null;
    const busy = ctx.busy ? ctx.busy(ph.start, ph.end) : [];
    const R = region(ctx, face, busy);
    const hitsBusy = r => busy.some(b => b.x < r.right && b.x + b.w > r.left && b.y < r.bottom && b.y + b.h > r.top);
    const RW = R.x1 - R.x0, RH = R.y1 - R.y0;
    const small = Math.round(vertical ? 0.040 * h : 0.068 * h);
    const midSize = Math.round(small * 1.55);
    const us = units(ph.words);
    const block = document.createElement("div");
    block.className = "kin-block";
    block.style.cssText = `position:absolute;left:${R.x0}px;top:${R.y0}px;width:${RW}px;`;
    el.appendChild(block);

    // dựng từng dòng
    const rows = [];
    us.forEach((u, k) => {
      const row = document.createElement("div");
      row.className = "kin-row " + (u.hero ? "kin-hero" : "kin-small");
      const text = u.words.map(x => x.text).join(" ");
      const caps = u.hero && text.replace(/[^\p{L}\p{N}]/gu, "").length <= 4;
      if (u.hero) {
        row.style.cssText = `font-family:${caps ? "Anton" : "Paytone"};color:${hero};line-height:.86;white-space:nowrap;` +
          `letter-spacing:${caps ? "0" : "-0.02em"};${caps ? "text-transform:uppercase;" : ""}`;
        const stack = u.words.length === 2 && (ph.stack ?? rnd() < 0.55);
        const chs = t => Array.from(t).map(c => `<span class="kin-ch">${esc(c)}</span>`).join("");
        row.innerHTML = stack
          ? `<span class="kin-word" data-ink style="display:inline-block;line-height:.82">${chs(u.words[0].text)}<br>${chs(u.words[1].text)}</span>`
          : `<span class="kin-word" data-ink>${chs(text)}</span>`;
        if (stack) { row.style.lineHeight = ".82"; u.stacked = true; }
      } else {
        row.style.cssText = `font-family:BVPM;font-weight:500;color:${ink};line-height:1.0;white-space:nowrap;` +
          `text-shadow:0 0.05em 0.25em rgba(0,0,0,.55);font-size:${u.mid ? midSize : small}px;letter-spacing:-0.01em;`;
        row.innerHTML = u.words.map(x => `<span class="kin-word" data-ink>${esc(x.text)}</span>`).join(" ");
      }
      row.style.position = "absolute";
      block.appendChild(row);
      rows.push({ row, u, k });
    });

    // cỡ chữ từ khoá: lấp đầy bề ngang vùng trống, có trần theo chiều cao
    rows.forEach(r => {
      if (!r.u.hero) return;
      r.row.style.fontSize = "100px";
      const wid = r.row.scrollWidth || 1;
      const target = (vertical ? Math.min(RW, w * (0.7 + 0.16 * rnd())) : Math.min(0.68 * w, Math.max(RW * 1.25, 0.5 * w)) * (0.85 + 0.15 * rnd()))
        * (r.u.stacked ? 0.8 : 1);
      const cap = (vertical ? 0.17 : 0.36) * h * (r.u.stacked ? 0.62 : 1);
      r.row.style.fontSize = Math.max(small * 2.2, Math.min(cap, 100 * target / wid)) + "px";
    });

    // xếp dọc, so le
    let y = 0;
    const placed = [];
    rows.forEach(r => {
      const rw = r.row.scrollWidth, rh = r.row.offsetHeight;
      const slack = Math.max(0, RW - rw);
      let x;
      if (r.u.hero) x = slack * (0.15 + 0.7 * rnd());
      else x = slack * (R.side === "left" ? 0.55 + 0.45 * rnd() : R.side === "right" ? 0.45 * rnd() : rnd());
      const rot = r.u.hero ? (rnd() < 0.35 ? 0 : (rnd() - 0.5) * 18) : (rnd() < 0.7 ? 0 : (rnd() - 0.5) * 6);
      const overlap = r.u.hero ? -0.12 * rh : -0.05 * rh;
      if (placed.length) y += overlap;
      placed.push({ ...r, x, y, rot, rw, rh });
      y += rh;
    });
    // co cả khối nếu cao hơn vùng
    const total = y, scale = Math.min(1, RH / Math.max(1, total));
    const top = (RH - total * scale) * (0.25 + 0.5 * rnd());
    block.style.top = (R.y0 + top) + "px";
    block.style.transformOrigin = "0 0"; block._scale = scale;
    if (scale < 1) block.style.transform = `scale(${scale})`;
    placed.forEach(p => {
      p.row.style.left = p.x + "px"; p.row.style.top = p.y + "px";
      p.row.style.transform = p.rot ? `rotate(${p.rot}deg)` : "";
      p.row.style.transformOrigin = "50% 60%";
    });

    // Chiều sâu: từ khoá lớn đè lên thân người thì đặt SAU người (mặt nạ tách người che lên chữ).
    // Từ nằm trước người thì không được che lõi khuôn mặt: co lại tới khi tránh được.
    if (face) {
      const [fx, fy, fw, fh] = face;
      const core = { x: fx + 0.15 * fw / 1.3, y: fy + 0.35 * fh / 1.6, w: fw / 1.3, h: fh / 1.6 };
      const body = { x: fx - 0.9 * fw, y: fy - 0.2 * fh, w: fw * 2.8, h: h - fy };
      const hit = (r, b) => Math.max(0, Math.min(r.right, b.x + b.w) - Math.max(r.left, b.x)) * Math.max(0, Math.min(r.bottom, b.y + b.h) - Math.max(r.top, b.y));
      placed.forEach(p => {
        let r = p.row.getBoundingClientRect();
        if (p.u.hero && ctx.depth !== false && hit(r, body) > 0.05 * r.width * r.height && rnd() < 0.85) {
          p.row.dataset.layer = "behind"; p.behind = true; return;
        }
        // thử đẩy ra xa mặt trước, rồi mới co chữ
        const away = (r.left + r.right) / 2 < core.x + core.w / 2 ? -1 : 1;
        let shift = 0;
        while (shift < 0.25 * w && hit(r, core) > 0.02 * core.w * core.h) {
          shift += 0.02 * w; p.row.style.left = (p.x + away * shift / (block._scale || 1)) + "px"; r = p.row.getBoundingClientRect();
          if (r.left < 0.04 * w || r.right > 0.96 * w) { p.row.style.left = p.x + "px"; r = p.row.getBoundingClientRect(); break; }
        }
        let guard = 12;
        while (guard-- > 0 && hit(r, core) > 0.02 * core.w * core.h) {
          p.row.style.fontSize = parseFloat(getComputedStyle(p.row).fontSize) * 0.9 + "px";
          r = p.row.getBoundingClientRect();
        }
      });
    }

    // ép mọi dòng nằm trong vùng an toàn của khung
    const SX0 = 0.045 * w, SX1 = (vertical ? 0.87 : 0.955) * w, SY0 = (vertical ? 0.085 : 0.065) * h, SY1 = (vertical ? 0.795 : 0.935) * h;
    // đo đúng phần mực nhìn thấy (chữ xếp 2 tầng tràn khỏi hộp dòng)
    const inkBox = row => {
      let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
      row.querySelectorAll("[data-ink]").forEach(n => { const q = n.getBoundingClientRect(); x0 = Math.min(x0, q.left); y0 = Math.min(y0, q.top); x1 = Math.max(x1, q.right); y1 = Math.max(y1, q.bottom); });
      return { left: x0, top: y0, right: x1, bottom: y1, width: x1 - x0, height: y1 - y0 };
    };
    placed.forEach(p => {
      let r = inkBox(p.row), k = block._scale || 1;
      if (r.width > (SX1 - SX0) * 0.93) { p.row.style.fontSize = parseFloat(getComputedStyle(p.row).fontSize) * (SX1 - SX0) / r.width * 0.9 + "px"; r = inkBox(p.row); }
      const gx = r.width * 0.035, gy = r.height * 0.035;     // chừa chỗ cho nhịp phóng 5%
      let dx = r.left - gx < SX0 ? SX0 - r.left + gx : r.right + gx > SX1 ? SX1 - r.right - gx : 0;
      let dy = r.top - gy < SY0 ? SY0 - r.top + gy : r.bottom + gy > SY1 ? SY1 - r.bottom - gy : 0;
      if (dx) p.row.style.left = parseFloat(p.row.style.left) + dx / k + "px";
      if (dy) p.row.style.top = parseFloat(p.row.style.top) + dy / k + "px";
      // còn chạm vùng hiệu ứng khác → bỏ xoay, co chữ
      let g2 = 8; r = inkBox(p.row);
      while (g2-- > 0 && hitsBusy(r)) {
        p.row.style.transform = ""; p.row.style.fontSize = parseFloat(getComputedStyle(p.row).fontSize) * 0.88 + "px";
        r = inkBox(p.row);
      }
    });

    // vòng cung trên đầu: khi có mặt và còn trống phía trên
    const heroRow = placed.find(p => p.u.hero);
    const arcOK = face && heroRow && (ph.layout === "arc" || (ph.layout !== "stack" && rnd() < 0.28)) &&
      face[1] > 0.16 * h && Array.from(heroRow.u.words.map(x => x.text).join(" ")).length <= 11;
    if (arcOK && !heroRow.behind && arcFree(heroRow, face, placed, { SX0, SX1, SY0, SY1 }, hitsBusy)) arcify(heroRow, face, ctx, block, scale);

    // ---- chuyển động
    const tl = gsap.timeline();
    placed.forEach(p => {
      const t0 = Math.max(0, p.u.words[0].start - ph.start);
      p.row.dataset.t0 = (ph.start + t0).toFixed(3);       // để bộ kiểm định chỉ đo khi chữ đã vào xong
      if (!p.u.hero) {
        p.row.querySelectorAll(".kin-word").forEach((sp, j) => {
          const tt = Math.max(0, p.u.words[j].start - ph.start);
          tl.fromTo(sp, { autoAlpha: 0, y: small * 0.35, filter: "blur(6px)" },
            { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.14, ease: "power2.out", immediateRender: true }, tt);
        });
        return;
      }
      const fx = ph.fx || HERO_FX[Math.floor(rnd() * HERO_FX.length)];
      const word = p.row.querySelector(".kin-word"), chars = p.row.querySelectorAll(".kin-ch");
      if (fx === "tumble" || p.arc) {
        chars.forEach((c, j) => tl.fromTo(c, { autoAlpha: 0, rotation: (rnd() - 0.5) * 120, yPercent: -60 - 60 * rnd(), scale: 0.3 },
          { autoAlpha: 1, rotation: c._rot || 0, yPercent: 0, scale: 1, duration: 0.32, ease: "back.out(2)", immediateRender: true }, t0 + j * 0.025));
      } else if (fx === "pixel") {
        pixelate(p.row, word, tl, t0, hero);
      } else if (fx === "blurzoom") {
        tl.fromTo(word, { autoAlpha: 0, scale: 1.9, filter: "blur(18px)" },
          { autoAlpha: 1, scale: 1, filter: "blur(0px)", duration: 0.24, ease: "power3.out", immediateRender: true }, t0);
      } else if (fx === "slam") {
        tl.fromTo(word, { autoAlpha: 0, scale: 3.2 }, { autoAlpha: 1, scale: 1, duration: 0.16, ease: "power4.in", immediateRender: true }, t0);
        tl.to(p.row, { x: "+=8", duration: 0.04, yoyo: true, repeat: 3, ease: "none" }, t0 + 0.16);
      } else {
        tl.fromTo(word, { autoAlpha: 0, scale: 0 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2.6)", immediateRender: true }, t0);
      }
      // đẩy nhẹ suốt cụm cho có "sức sống"
      tl.fromTo(p.row, { scale: 1 }, { scale: 1.05, duration: Math.max(0.3, ph.end - ph.start - t0), ease: "none", immediateRender: false }, t0);
    });
    tl.set({}, {}, Math.max(0.05, ph.end - ph.start));
    return tl;
  }

  // Vòng cung chỉ dùng khi dải phía trên đầu không đụng các dòng chữ khác.
  function arcFree(hero, face, placed, safe, hitsBusy) {
    const [fx, fy, fw] = face;
    const fs = Math.min(parseFloat(hero.row.style.fontSize), fw * 0.55);
    const R = Math.max(fw * 0.75, hero.row.scrollWidth * fs / parseFloat(hero.row.style.fontSize) / Math.PI * 1.05);
    const box = { left: fx + fw / 2 - R - fs, right: fx + fw / 2 + R + fs, top: fy - R * 0.45 - fs * 1.6, bottom: fy + fw * 0.3 };
    if (box.top < safe.SY0 || box.left < safe.SX0 || box.right > safe.SX1 || hitsBusy(box)) return false;
    return placed.every(p => {
      if (p === hero) return true;
      const r = p.row.getBoundingClientRect();
      return r.right < box.left || r.left > box.right || r.bottom < box.top || r.top > box.bottom;
    });
  }

  // Từ khoá chạy theo vòng cung phía trên đầu (như «CONTROL» trong video mẫu).
  function arcify(p, face, ctx, block, scale) {
    const [fx, fy, fw, fh] = face;
    const word = p.row.querySelector(".kin-word");
    const chars = Array.from(p.row.querySelectorAll(".kin-ch"));
    const fs = Math.min(parseFloat(p.row.style.fontSize), fw * 0.55);
    p.row.style.fontSize = fs + "px";
    const widths = chars.map(c => { c.style.display = "inline-block"; return c.offsetWidth; });
    const total = widths.reduce((a, b) => a + b, 0);
    const R = Math.max(fw * 0.75, total / Math.PI * 1.05);
    const cx = fx + fw / 2, cy = fy + fh * 0.55;
    // đưa dòng về toạ độ khung (bỏ khỏi block để không bị scale)
    block.parentNode.appendChild(p.row);
    p.row.style.left = "0px"; p.row.style.top = "0px"; p.row.style.transform = "";
    word.style.position = "relative"; word.style.display = "block";
    let acc = -total / 2;
    chars.forEach((c, j) => {
      const mid = acc + widths[j] / 2; acc += widths[j];
      const a = mid / R;                       // radian, 0 = đỉnh đầu
      const x = cx + R * Math.sin(a) - widths[j] / 2, y = cy - R * Math.cos(a) - fs * 0.8;
      c.style.position = "absolute"; c.style.left = x + "px"; c.style.top = y + "px";
      c._rot = a * 180 / Math.PI;
      gsap.set(c, { rotation: c._rot, transformOrigin: "50% 100%" });
    });
    p.arc = true;
  }

  // Hiệu ứng vỡ điểm ảnh: vẽ chữ lên canvas ở độ phân giải thấp rồi nét dần.
  function pixelate(row, word, tl, t0, color) {
    const r = word.getBoundingClientRect();
    const cs = getComputedStyle(row);
    const W = Math.ceil(r.width / (row.closest(".kin-block")?._scale || 1)) + 40, H = Math.ceil(parseFloat(cs.fontSize) * 1.25);
    const cv = document.createElement("canvas");
    cv.width = W; cv.height = H; cv.dataset.ink = "";
    cv.style.cssText = `position:absolute;left:-20px;top:${-0.12 * H}px;width:${W}px;height:${H}px;image-rendering:pixelated;`;
    row.appendChild(cv);
    const off = document.createElement("canvas"), o = { px: 34 };
    const draw = () => {
      const px = Math.max(1, Math.round(o.px));
      const sw = Math.max(1, Math.ceil(W / px)), sh = Math.max(1, Math.ceil(H / px));
      off.width = sw; off.height = sh;
      const g = off.getContext("2d");
      g.clearRect(0, 0, sw, sh);
      g.save(); g.scale(sw / W, sh / H);
      g.font = `${cs.fontSize} ${cs.fontFamily}`; g.fillStyle = color; g.textBaseline = "alphabetic";
      if (cs.textTransform === "uppercase") g.fillText(word.textContent.toUpperCase(), 20, H * 0.86);
      else g.fillText(word.textContent, 20, H * 0.86);
      g.restore();
      const c = cv.getContext("2d");
      c.clearRect(0, 0, W, H); c.imageSmoothingEnabled = false; c.drawImage(off, 0, 0, W, H);
    };
    tl.set(word, { autoAlpha: 0 }, 0);
    tl.fromTo(cv, { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.01, immediateRender: true }, t0);
    tl.fromTo(o, { px: 34 }, { px: 1, duration: 0.34, ease: "steps(6)", onUpdate: draw, immediateRender: true }, t0);
    tl.set(cv, { autoAlpha: 0 }, t0 + 0.35);
    tl.set(word, { autoAlpha: 1 }, t0 + 0.35);
    draw();
  }

  window.CAPTIONS = window.CAPTIONS || {};
  window.CAPTIONS.kinetic = { build, custom: true };
})();
