// Renders the live poster frame by frame in headless Chromium.
//
//   node tools/render.mjs --stills 0,3.5,6.05,7     -> work/stills/*.jpg
//   node tools/render.mjs --fps 60 --workers 3 --out work/video.mp4
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argv = process.argv.slice(2);
const opt = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i === -1 ? fallback : argv[i + 1];
};

const MIME = {
  ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript",
  ".png": "image/png", ".webp": "image/webp", ".m4a": "audio/mp4", ".json": "application/json",
};
const server = http.createServer((req, res) => {
  const file = path.join(root, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!file.startsWith(root) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404).end();
    return;
  }
  res.writeHead(200, { "content-type": MIME[path.extname(file)] ?? "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));

const browser = await chromium.launch({
  args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const url = `http://127.0.0.1:${server.address().port}/index.html?render`;

async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on("console", (m) => m.type() === "error" && !m.text().includes("404") && console.error("[page]", m.text()));
  page.on("pageerror", (e) => console.error("[page]", e.message));
  await page.goto(url);
  const loop = await page.evaluate(async () => {
    await window.livePoster.ready;
    return window.livePoster.LOOP;
  });
  const frame = async (t, i) => {
    await page.evaluate(([t, i]) => window.livePoster.renderAt(t, i), [t, i]);
    // quality-100 JPEG is visually lossless here and encodes ~6x faster than PNG
    return page.screenshot({ type: "jpeg", quality: 100, clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  };
  return { loop, frame };
}

const stills = opt("stills");
if (stills) {
  const { frame } = await openPage();
  const dir = path.join(root, "work/stills");
  fs.mkdirSync(dir, { recursive: true });
  for (const t of stills.split(",").map(Number)) {
    fs.writeFileSync(path.join(dir, `t${t.toFixed(2)}.jpg`), await frame(t));
  }
  console.log(`stills written to ${dir}`);
} else {
  // Frames are independent, so several pages render in parallel while a single
  // writer hands them to FFmpeg in order.
  const fps = Number(opt("fps", 60));
  const workers = Number(opt("workers", 2));
  const out = path.resolve(root, opt("out", "work/video.mp4"));
  const pages = await Promise.all(Array.from({ length: workers }, openPage));
  const frames = Math.round(pages[0].loop * fps);
  const ff = spawn("ffmpeg", [
    "-y", "-loglevel", "error", "-f", "image2pipe", "-c:v", "mjpeg", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", out,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const done = new Map();
  let next = 0;
  let written = 0;
  let wake = () => {};
  const started = Date.now();
  await Promise.all(pages.map(async ({ frame }) => {
    while (next < frames) {
      const i = next++;
      while (i - written > workers * 4) await new Promise((r) => setTimeout(r, 20));
      done.set(i, await frame(i / fps, i));
      wake();
    }
  }).concat((async () => {
    while (written < frames) {
      if (!done.has(written)) {
        await new Promise((r) => { wake = r; setTimeout(r, 50); });
        continue;
      }
      const png = done.get(written);
      done.delete(written);
      if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
      if (written % fps === 0) {
        const rate = (written + 1) / ((Date.now() - started) / 1000);
        console.log(`frame ${written}/${frames}  ${rate.toFixed(1)} fps`);
      }
      written++;
    }
  })()));
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  console.log(`video written to ${out}`);
}

await browser.close();
server.close();
