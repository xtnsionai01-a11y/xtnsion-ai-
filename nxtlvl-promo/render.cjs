// Frame-accurate renderer for index.html.
//   node render.cjs --snap 1.5,6,12          -> PNG stills in ./snaps
//   node render.cjs --out video.mp4 [--fps 60] [--mb 2] [--workers 4] [--audio music.wav]
// Each worker drives its own Chromium, writes a near-lossless segment, and a final
// pass concatenates the segments, adds light film grain (prevents gradient banding),
// and encodes the delivery file with the soundtrack.
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
const MB = +(args.mb || 1);                 // sub-frames per output frame, blended into motion blur
const BROWSER_ARGS = ['--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb', '--disable-gpu'];

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

const run = (cmd, a) => new Promise((res, rej) => spawn(cmd, a, { stdio: 'inherit' }).on('close', c => c ? rej(new Error(`${cmd} exited ${c}`)) : res()));

(async () => {
  const srv = await serve();
  const port = srv.address().port;

  if (args.snap) {
    const dir = path.join(ROOT, 'snaps');
    fs.mkdirSync(dir, { recursive: true });
    const browser = await chromium.launch({ args: BROWSER_ARGS });
    const page = await openPage(browser, port);
    for (const t of String(args.snap).split(',').map(Number)) {
      await page.evaluate(t => window.seekTo(t), t);
      await page.screenshot({ path: path.join(dir, `t${t.toFixed(2)}.png`) });
      console.log('snap', t);
    }
    await browser.close(); srv.close(); return;
  }

  const probe = await chromium.launch({ args: BROWSER_ARGS });
  const duration = await (await openPage(probe, port)).evaluate(() => window.DURATION);
  await probe.close();
  const RATE = FPS * MB;
  const total = Math.round(duration * RATE);
  fs.mkdirSync(TMP, { recursive: true });
  const per = Math.ceil(total / WORKERS);
  const t0 = Date.now();
  let done = 0;

  const segs = await Promise.all([...Array(WORKERS)].map(async (_, w) => {
    const a = w * per, b = Math.min(total, a + per);
    if (a >= b) return null;
    const file = path.join(TMP, `seg${w}.mkv`);
    const browser = await chromium.launch({ args: BROWSER_ARGS });
    const page = await openPage(browser, port);
    // Play the timeline forward to the segment start so every tween records its start values in order.
    for (let t = 0; t < a / RATE; t += 0.2) await page.evaluate(t => window.seekTo(t), t);
    const cdp = await page.context().newCDPSession(page);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(RATE), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'veryfast', '-qp', '4', '-pix_fmt', 'yuv444p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
    const closed = new Promise(r => ff.on('close', r));
    for (let f = a; f < b; f++) {
      await page.evaluate(t => window.seekTo(t), f / RATE);
      const buf = Buffer.from((await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true })).data, 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 120 === 0) console.log(`${done}/${total} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await closed;
    await browser.close();
    return file;
  }));
  console.log(`frames done in ${((Date.now() - t0) / 1000).toFixed(0)}s, encoding…`);

  const list = path.join(TMP, 'list.txt');
  fs.writeFileSync(list, segs.filter(Boolean).map(f => `file '${f}'`).join('\n'));
  const out = path.resolve(args.out || path.join(ROOT, 'nxtlvl-promo.mp4'));
  const ffArgs = ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list];
  if (args.audio) ffArgs.push('-i', path.resolve(args.audio), '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '256k', '-shortest');
  const blend = MB > 1 ? `tmix=frames=${MB},framestep=${MB},` : '';
  ffArgs.push('-vf', `${blend}scale=out_color_matrix=bt709:out_range=tv,noise=c0s=3:c0f=t,format=yuv420p`,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-tune', 'film', '-x264-params', 'aq-mode=3:deblock=-1,-1',
    '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
    '-r', String(FPS), '-movflags', '+faststart', out);
  await run('ffmpeg', ffArgs);
  console.log(`wrote ${out} in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  srv.close();
})().catch(e => { console.error(e); process.exit(1); });
