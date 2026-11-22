#!/usr/bin/env node
// Xưởng Phim – render lớp chữ/hiệu ứng (HTML + GSAP) thành video trong suốt, hoặc đo bố cục cho kiểm định.
//
//   node render/overlay.mjs render  <spec.json> <out.mov>
//   node render/overlay.mjs layout  <spec.json> <out.json> [--step 0.1]
//   node render/overlay.mjs frames  <spec.json> <outdir> --times 1.2,3.4,...
//
// Khung nào không có chữ thì dùng lại một ảnh trong suốt có sẵn (không chụp), nên nhanh hơn nhiều.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require("playwright")); }
catch { ({ chromium } = await import("playwright")); }

const here = path.dirname(fileURLToPath(import.meta.url));
const engine = pathToFileURL(path.join(here, "..", "effects", "engine.html")).href;
const [mode, specPath, out0, ...rest0] = process.argv.slice(2);
const out = mode === "has-behind" ? "-" : out0;
const rest = mode === "has-behind" ? [out0, ...rest0].filter(Boolean) : rest0;
if (!mode || !specPath || !out) {
  console.error("Dùng: overlay.mjs render|layout|frames <spec.json> <out> [--step s] [--times a,b]");
  process.exit(2);
}
const opt = (name, dflt) => { const i = rest.indexOf("--" + name); return i >= 0 ? rest[i + 1] : dflt; };
const spec = JSON.parse(fs.readFileSync(specPath, "utf8"));
const { w, h, fps } = spec.format;

const launchOpts = { args: ["--force-color-profile=srgb", "--disable-gpu", "--font-render-hinting=none"] };
if (process.env.XUONG_CHROMIUM) launchOpts.executablePath = process.env.XUONG_CHROMIUM;
const browser = await chromium.launch(launchOpts);
const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
page.on("pageerror", e => { console.error("Lỗi trong engine:", e.message); process.exitCode = 1; });
await page.goto(engine);
const info = await page.evaluate(s => window.XUONG.init(s), spec);
const layer = opt("layer", "");
if (layer) await page.evaluate(l => window.XUONG.setLayer(l), layer);
if (mode === "has-behind") {
  console.log(JSON.stringify({ behind: await page.evaluate(() => window.XUONG.hasBehind()) }));
  await browser.close(); process.exit(0);
}
const duration = spec.duration ?? info.duration;
const stage = page.locator("#stage");

if (mode === "layout") {
  const step = +opt("step", "0.1");
  const samples = [];
  for (let t = 0; t <= duration + 1e-6; t += step) {
    const boxes = await page.evaluate(tt => window.XUONG.layout(tt), +t.toFixed(3));
    samples.push({ t: +t.toFixed(3), boxes });
  }
  fs.writeFileSync(out, JSON.stringify({ format: spec.format, duration, samples }, null, 1));
  console.log(JSON.stringify({ ok: true, samples: samples.length }));
} else if (mode === "frames") {
  fs.mkdirSync(out, { recursive: true });
  const times = String(opt("times", "")).split(",").filter(Boolean).map(Number);
  for (const t of times) {
    await page.evaluate(tt => window.XUONG.seek(tt), t);
    await stage.screenshot({ path: path.join(out, `ov_${t.toFixed(2)}.png`), omitBackground: true });
  }
  console.log(JSON.stringify({ ok: true, frames: times.length }));
} else if (mode === "render") {
  const total = Math.round(duration * fps);
  const ff = spawn(process.env.FFMPEG || "ffmpeg", ["-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps),
    "-c:v", "png", "-i", "-", "-c:v", "qtrle", "-pix_fmt", "argb", out], { stdio: ["pipe", "inherit", "inherit"] });
  const write = buf => new Promise(res => ff.stdin.write(buf) ? res() : ff.stdin.once("drain", res));
  let blank = null, shot = 0;
  const t0 = Date.now();
  for (let i = 0; i < total; i++) {
    const t = i / fps;
    const visible = await page.evaluate(tt => window.XUONG.layout(tt).length, t);
    let buf;
    if (!visible) {
      blank ??= await stage.screenshot({ omitBackground: true, type: "png" });
      buf = blank;
    } else {
      buf = await stage.screenshot({ omitBackground: true, type: "png" }); shot++;
    }
    await write(buf);
    if (i % (fps * 5) === 0) process.stderr.write(`  lớp chữ ${Math.round(100 * i / total)}%\r`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error("ffmpeg lỗi " + c))));
  console.log(JSON.stringify({ ok: true, frames: total, captured: shot, seconds: (Date.now() - t0) / 1000 }));
} else {
  console.error("Chế độ không hợp lệ:", mode); process.exitCode = 2;
}
await browser.close();
