/*
 * Thư viện hiệu ứng chữ của Xưởng Phim (GSAP 3, render tất định).
 * Mỗi hiệu ứng: { zone, fields, build(el, ov, ctx) -> gsap.timeline } ; thời gian 0 = ov.start.
 * Phần tử nhìn thấy được gắn data-ink để bộ kiểm định đo đúng vùng chữ thật.
 * Không dùng Math.random: mọi ngẫu nhiên đi qua seeded() để mỗi lần xuất ra cùng một khung hình.
 */
(function () {
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  function seeded(str) {
    let h = 1779033703 ^ String(str).length;
    for (let i = 0; i < String(str).length; i++) { h = Math.imul(h ^ String(str).charCodeAt(i), 3432918353); h = h << 13 | h >>> 19; }
    return function () { h = Math.imul(h ^ h >>> 16, 2246822507); h = Math.imul(h ^ h >>> 13, 3266489909); return ((h ^= h >>> 16) >>> 0) / 4294967296; };
  }
  const dur = ov => Math.max(0.3, ov.end - ov.start);
  const words = (text, hl = []) => String(text).trim().split(/\s+/).map(w => {
    const bare = w.toLowerCase().replace(/[.,!?:;]/g, "");
    return `<span class="word${hl.map(x => x.toLowerCase()).includes(bare) ? " hl" : ""}" data-ink>${esc(w)}</span>`;
  }).join(" ");
  function outro(tl, targets, d, how = "fade") {
    const at = Math.max(0, d - 0.22);
    if (how === "drop") tl.to(targets, { y: "+=40", autoAlpha: 0, duration: 0.2, ease: "power2.in" }, at);
    else tl.to(targets, { autoAlpha: 0, scale: 0.92, duration: 0.2, ease: "power2.in" }, at);
    return tl;
  }

  const EFFECTS = {
    // Tiêu đề mở đầu (hook): từng chữ "dập" xuống, rung nhẹ khung.
    "hook-title": {
      zone: "top", fields: ["text", "highlight[]"],
      build(el, ov) {
        el.innerHTML = `<div class="shadow">${words(ov.text, ov.highlight || [])}</div>`;
        const ws = el.querySelectorAll(".word"), d = dur(ov), tl = gsap.timeline();
        tl.from(ws, { scale: 2.4, autoAlpha: 0, y: -30, duration: 0.28, ease: "back.out(2.2)", stagger: 0.09 });
        tl.to(el, { x: 6, duration: 0.04, yoyo: true, repeat: 3, ease: "none" }, ws.length * 0.09 + 0.1);
        tl.addLabel("settled", ws.length * 0.09 + 0.3);
        tl.to(ws, { y: -6, duration: 0.6, yoyo: true, repeat: Math.max(0, Math.floor((d - 1.2) / 0.6)), ease: "sine.inOut", stagger: 0.05 }, 0.6);
        return outro(tl, ws, d);
      }
    },
    // Từ khóa nổi bật (snap zoom): chip màu bật lên giữa khung.
    "keyword-pop": {
      zone: "center", fields: ["text"],
      build(el, ov) {
        el.innerHTML = `<div class="chip" data-ink>${esc(ov.text)}</div>`;
        const c = el.firstChild, d = dur(ov), tl = gsap.timeline();
        tl.from(c, { scale: 0, rotation: -8, duration: 0.32, ease: "back.out(3)" });
        tl.addLabel("settled", 0.35);
        tl.to(c, { scale: 1.04, duration: 0.5, yoyo: true, repeat: Math.max(0, Math.floor((d - 0.8) / 0.5)), ease: "sine.inOut" }, 0.35);
        return outro(tl, c, d);
      }
    },
    // Thanh tên (lower third): giới thiệu người nói.
    "lower-third": {
      zone: "center", fields: ["text", "subtext"],
      build(el, ov) {
        el.style.alignItems = "flex-start";
        el.innerHTML = `<div class="bar" data-ink><div class="name">${esc(ov.text)}</div>${ov.subtext ? `<div class="role">${esc(ov.subtext)}</div>` : ""}</div>`;
        const b = el.firstChild, d = dur(ov), tl = gsap.timeline();
        tl.from(b, { xPercent: -120, duration: 0.45, ease: "power4.out" });
        tl.from(b.children, { autoAlpha: 0, x: -20, duration: 0.3, stagger: 0.1 }, 0.2);
        tl.addLabel("settled", 0.6);
        tl.to(b, { xPercent: -120, duration: 0.3, ease: "power3.in" }, Math.max(0.5, d - 0.32));
        return tl;
      }
    },
    // Danh sách tích từng mục (checklist pop). items: [{text, at}] với at tính từ ov.start.
    "checklist": {
      zone: "top", fields: ["title", "items[{text,at}]"],
      build(el, ov) {
        const items = (ov.items || []).map(it => typeof it === "string" ? { text: it } : it);
        el.innerHTML = `<div class="list" data-ink>${ov.title ? `<div class="title">${esc(ov.title)}</div>` : ""}` +
          items.map(it => `<div class="row"><span class="box"><span class="tick">✓</span></span><span>${esc(it.text)}</span></div>`).join("") + `</div>`;
        const list = el.firstChild, rows = list.querySelectorAll(".row"), d = dur(ov), tl = gsap.timeline();
        tl.from(list, { y: -40, autoAlpha: 0, duration: 0.35, ease: "power3.out" });
        rows.forEach((r, i) => {
          const at = items[i].at ?? (0.4 + i * Math.min(1.2, (d - 1) / Math.max(1, items.length)));
          gsap.set(r, { autoAlpha: 0.35 });
          gsap.set(r.querySelector(".tick"), { scale: 0 });
          tl.to(r, { autoAlpha: 1, duration: 0.15 }, at);
          tl.to(r.querySelector(".tick"), { scale: 1, duration: 0.3, ease: "back.out(3)" }, at);
          tl.from(r.lastChild, { x: 18, duration: 0.25 }, at);
        });
        return outro(tl, list, d);
      }
    },
    // Bình luận rơi xuống (comment drop).
    "comment-drop": {
      zone: "top", fields: ["author", "text"],
      build(el, ov) {
        const a = String(ov.author || "Khán giả").trim();
        el.innerHTML = `<div class="card" data-ink><div class="avatar">${esc(a[0].toUpperCase())}</div><div><div class="who">${esc(a)}</div><div class="msg">${esc(ov.text)}</div></div></div>`;
        const c = el.firstChild, d = dur(ov), tl = gsap.timeline();
        tl.from(c, { y: -260, rotation: -6, autoAlpha: 0, duration: 0.55, ease: "bounce.out" });
        tl.addLabel("settled", 0.6);
        tl.to(c, { rotation: 1.5, duration: 0.8, yoyo: true, repeat: Math.max(0, Math.floor((d - 1.3) / 0.8)), ease: "sine.inOut" }, 0.6);
        return outro(tl, c, d, "drop");
      }
    },
    // Số đếm tăng dần (growth counter).
    "counter": {
      zone: "center", fields: ["from", "to", "prefix", "suffix", "label"],
      build(el, ov) {
        el.innerHTML = `<div data-ink><div class="num"></div>${ov.label ? `<div class="label shadow">${esc(ov.label)}</div>` : ""}</div>`;
        const n = el.querySelector(".num"), d = dur(ov), o = { v: +ov.from || 0 }, tl = gsap.timeline();
        const fmt = v => (ov.prefix || "") + Math.round(v).toLocaleString("vi-VN") + (ov.suffix || "");
        n.textContent = fmt(+ov.to || 100);           // widest value first so fitText measures it
        tl.call(() => { n.textContent = fmt(o.v); }, null, 0);
        tl.from(el.firstChild, { scale: 0.4, autoAlpha: 0, duration: 0.3, ease: "back.out(2)" }, 0);
        tl.to(o, { v: +ov.to || 100, duration: Math.min(1.6, d * 0.6), ease: "power2.out", onUpdate: () => { n.textContent = fmt(o.v); } }, 0.05);
        return outro(tl, el.firstChild, d);
      }
    },
    // Gõ chữ (typewriter).
    "typewriter": {
      zone: "center", fields: ["text"],
      build(el, ov) {
        const chars = Array.from(String(ov.text));
        el.innerHTML = `<div class="tw" data-ink>${chars.map(ch => `<span class="ch">${esc(ch)}</span>`).join("")}<span class="caret"></span></div>`;
        const cs = el.querySelectorAll(".ch"), d = dur(ov), tl = gsap.timeline();
        const per = Math.min(0.06, (d * 0.6) / Math.max(1, cs.length));
        gsap.set(cs, { display: "none" });
        cs.forEach((c, i) => tl.set(c, { display: "inline" }, 0.1 + i * per));
        tl.to(el.querySelector(".caret"), { autoAlpha: 0, duration: 0.01, yoyo: true, repeat: Math.floor(d / 0.45), repeatDelay: 0.44 }, 0);
        return outro(tl, el.firstChild, d);
      }
    },
    // Bão tiêu đề (headline storm): các từ bay vào từ nhiều hướng.
    "headline-storm": {
      zone: "center", fields: ["text"],
      build(el, ov) {
        el.innerHTML = `<div>${words(ov.text)}</div>`;
        const ws = el.querySelectorAll(".word"), d = dur(ov), rnd = seeded(ov.id + ov.text), tl = gsap.timeline();
        ws.forEach((w, i) => tl.from(w, { x: (rnd() - 0.5) * 900, y: (rnd() - 0.5) * 700, rotation: (rnd() - 0.5) * 70,
          scale: 0.3, autoAlpha: 0, duration: 0.45, ease: "power4.out" }, i * 0.07));
        tl.addLabel("settled", ws.length * 0.07 + 0.45);
        return outro(tl, ws, d);
      }
    },
    // Chữ nổ kèm tia (sticker burst).
    "sticker-burst": {
      zone: "center", fields: ["text"],
      build(el, ov) {
        el.innerHTML = `<div class="core" data-ink>${esc(ov.text)}${"<span class='spark'></span>".repeat(10)}</div>`;
        const core = el.firstChild, sp = core.querySelectorAll(".spark"), d = dur(ov), rnd = seeded(ov.id), tl = gsap.timeline();
        tl.from(core, { scale: 0, duration: 0.3, ease: "back.out(3)" });
        sp.forEach((s, i) => {
          const a = (i / sp.length) * Math.PI * 2 + rnd() * 0.4, r = 260 + rnd() * 120;
          tl.fromTo(s, { x: 0, y: 0, scale: 1, autoAlpha: 1 }, { x: Math.cos(a) * r, y: Math.sin(a) * r * 0.6, scale: 0, autoAlpha: 0, duration: 0.7, ease: "power3.out" }, 0.08);
        });
        return outro(tl, core, d);
      }
    },
    // Kêu gọi theo dõi (CTA) ở cuối video.
    "cta": {
      zone: "center", fields: ["text"],
      build(el, ov) {
        el.innerHTML = `<div class="btn" data-ink><span class="plus">+</span><span>${esc(ov.text || "Theo dõi")}</span></div>`;
        const b = el.firstChild, d = dur(ov), tl = gsap.timeline();
        tl.from(b, { y: 120, autoAlpha: 0, duration: 0.4, ease: "back.out(2)" });
        tl.addLabel("settled", 0.45);
        tl.to(b, { scale: 1.04, duration: 0.35, yoyo: true, repeat: Math.max(0, Math.floor((d - 0.8) / 0.35)), ease: "sine.inOut" }, 0.45);
        return outro(tl, b, d);
      }
    }
  };

  // Phụ đề theo từng từ. page = {i, start, end, lines:[[{text,start,end}]]}
  function capBuild(style) {
    return {
      build(el, page) {
        el.innerHTML = page.lines.map(line => `<span class="line">` + line.map((w, j) =>
          `<span class="word" data-ink data-s="${w.start}" data-e="${w.end}">${esc(w.text)}</span>`).join(" ") + `</span>`).join("");
        const tl = gsap.timeline(), ws = el.querySelectorAll(".word");
        if (style !== "clean") tl.from(el, { scale: 0.86, y: 14, duration: 0.12, ease: "back.out(2)" }, 0);
        ws.forEach(w => {
          const s = +w.dataset.s - page.start;
          if (style === "pop") tl.fromTo(w, { scale: 1 }, { scale: 1.12, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.out", immediateRender: false }, Math.max(0, s));
        });
        tl.set({}, {}, Math.max(0.01, page.end - page.start));   // keep the page alive to its end
        // Active-word highlight is derived from time on every render, so any seek order is exact.
        tl.eventCallback("onUpdate", () => {
          const t = tl.time() + page.start;
          ws.forEach(w => w.classList.toggle("on", t >= +w.dataset.s && t < +w.dataset.e));
        });
        return tl;
      }
    };
  }
  const CAPTIONS = { pop: capBuild("pop"), box: capBuild("box"), clean: capBuild("clean") };

  window.EFFECTS = EFFECTS;
  window.CAPTIONS = CAPTIONS;
})();
