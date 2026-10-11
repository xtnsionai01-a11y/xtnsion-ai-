// Frame-accurate renderer for index.html.
//   node render.cjs --snap 1.5,6,12          -> PNG stills in ./snaps
//   node render.cjs --out video.mp4 [--fps 60] [--workers 4] [--audio music.wav]
// Needs Playwright (Chromium) and ffmpeg on PATH.
const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const ROOT = __dirname;
const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => {
  if (v.startsWith('--')) a.push([v.slice(2), arr[i + 1] && !arr[i + 1].startsWith('--') ? arr[i + 1] : true]);
  return a;
}, []));
const FPS = +(args.fps || 60);
const WORKERS = +(args.workers || 4);
const TMP = args.tmp || path.join(ROOT, '.render');

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.png': 'image/png', '.css': 'text/css' };
function serve() {
  return new Promise(res => {
    const srv = http.createServer((req, rsp) => {
      const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
      fs.readFile(p.endsWith('/') ? p + 'index.html' : p, (err, buf) => {
        if (err) { rsp.writeHead(404); return rsp.end(); }
        rsp.writeHead(200, { 'Content-Type': MIME[path.extname(p)] || 'application/octet-stream' });
        rsp.end(buf);
      });
    }).listen(0, () => res(srv));
  });
}

async function openPage(browser, port) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => console.error('pageerror:', e.message));
  page.on('console', m => { if (m.type() === 'error') console.error('console:', m.text()); });
  await page.goto(`http://127.0.0.1:${port}/index.html?render`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 30000 });
  return page;
}

function ffmpegSegment(file) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-vf', 'scale=out_color_matrix=bt709:out_range=tv,noise=c0s=3:c0f=t,format=yuv420p',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-tune', 'film', '-x264-params', 'aq-mode=3:deblock=-1,-1',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-r', String(FPS), file], { stdio: ['pipe', 'inherit', 'inherit'] });
  return ff;
}

(async () => {
  const srv = await serve();
  const port = srv.address().port;
  const browser = await chromium.launch({ args: ['--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb'] });

  if (args.snap) {
    const dir = path.join(ROOT, 'snaps');
    fs.mkdirSync(dir, { recursive: true });
    const page = await openPage(browser, port);
    for (const t of String(args.snap).split(',').map(Number)) {
      await page.evaluate(t => window.seekTo(t), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(2)}.png`) });
      console.log('snap', t);
    }
    await browser.close(); srv.close(); return;
  }

  const page0 = await openPage(browser, port);
  const duration = await page0.evaluate(() => window.DURATION);
  await page0.close();
  const total = Math.round(duration * FPS);
  fs.mkdirSync(TMP, { recursive: true });
  const per = Math.ceil(total / WORKERS);
  const t0 = Date.now();
  let done = 0;

  const segs = await Promise.all([...Array(WORKERS)].map(async (_, w) => {
    const a = w * per, b = Math.min(total, a + per);
    const file = path.join(TMP, `seg${w}.mp4`);
    if (a >= b) return null;
    const page = await openPage(browser, port);
    // Prime the timeline in order up to the segment start so every tween records its start values.
    for (let t = 0; t < a / FPS; t += 0.25) await page.evaluate(t => window.seekTo(t), t);
    const ff = ffmpegSegment(file);
    const closed = new Promise(r => ff.on('close', r));
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.seekTo(t), f / FPS);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 120 === 0) console.log(`${done}/${total} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await closed;
    await page.close();
    return file;
  }));

  const list = path.join(TMP, 'list.txt');
  fs.writeFileSync(list, segs.filter(Boolean).map(f => `file '${f}'`).join('\n'));
  const out = path.resolve(args.out || path.join(ROOT, 'nxtlvl-promo.mp4'));
  const ffArgs = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  if (args.audio) ffArgs.push('-i', path.resolve(args.audio), '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-shortest');
  ffArgs.push('-c:v', 'copy', '-movflags', '+faststart', out);
  await new Promise((res, rej) => spawn('ffmpeg', ffArgs, { stdio: 'inherit' }).on('close', c => c ? rej(new Error('ffmpeg concat failed')) : res()));
  console.log(`wrote ${out} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  await browser.close(); srv.close();
})().catch(e => { console.error(e); process.exit(1); });
