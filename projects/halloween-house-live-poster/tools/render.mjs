// Renders the live poster frame by frame in headless Chromium.
//
//   node tools/render.mjs --stills 0,3.5,6.05,7     -> work/stills/*.png
//   node tools/render.mjs --fps 30 --out work/video.mp4
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
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
page.on("console", (m) => m.type() === "error" && console.error("[page]", m.text()));
page.on("pageerror", (e) => console.error("[page]", e.message));
await page.goto(`http://127.0.0.1:${server.address().port}/index.html?render`);
const { LOOP } = await page.evaluate(async () => {
  await window.livePoster.ready;
  return { LOOP: window.livePoster.LOOP };
});

const shot = () => page.screenshot({ type: "png", clip: { x: 0, y: 0, width: 1080, height: 1920 } });

const stills = opt("stills");
if (stills) {
  const dir = path.join(root, "work/stills");
  fs.mkdirSync(dir, { recursive: true });
  for (const t of stills.split(",").map(Number)) {
    await page.evaluate((t) => window.livePoster.renderAt(t), t);
    fs.writeFileSync(path.join(dir, `t${t.toFixed(2)}.png`), await shot());
  }
  console.log(`stills written to ${dir}`);
} else {
  const fps = Number(opt("fps", 30));
  const out = path.resolve(root, opt("out", "work/video.mp4"));
  const frames = Math.round(LOOP * fps);
  const ff = spawn("ffmpeg", [
    "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(fps), "-i", "-",
    "-c:v", "libx264", "-preset", "slow", "-crf", "12", "-pix_fmt", "yuv420p", out,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const started = Date.now();
  for (let i = 0; i < frames; i++) {
    await page.evaluate(([t, i]) => window.livePoster.renderAt(t, i), [i / fps, i]);
    const png = await shot();
    if (!ff.stdin.write(png)) await new Promise((r) => ff.stdin.once("drain", r));
    if (i % fps === 0) {
      const rate = (i + 1) / ((Date.now() - started) / 1000);
      console.log(`frame ${i}/${frames}  ${rate.toFixed(1)} fps`);
    }
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  console.log(`video written to ${out}`);
}

await browser.close();
server.close();
