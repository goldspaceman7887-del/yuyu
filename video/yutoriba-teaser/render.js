// Usage: node render.js out.mp4|--stills t1,t2,... outdir
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('console', m => console.log('[page]', m.text()));
  page.on('pageerror', e => { console.error('[pageerror]', e); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(async () => { await document.fonts.load('500 60px CG'); await document.fonts.ready; });
  await page.evaluate(() => window.init());
  const canvas = await page.$('#c');
  if (process.argv[2] === '--stills') {
    const ts = process.argv[3].split(',').map(Number); const out = process.argv[4];
    fs.mkdirSync(out, { recursive: true });
    for (const t of ts) {
      await page.evaluate(t => window.renderFrame(t), t);
      await canvas.screenshot({ path: path.join(out, `f_${t.toFixed(2)}.png`) });
    }
  } else {
    const fps = 30, n = 15 * fps;
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-tune', 'grain', process.argv[2]], { stdio: ['pipe', 'inherit', 'inherit'] });
    const t0 = Date.now();
    for (let i = 0; i < n; i++) {
      await page.evaluate(t => window.renderFrame(t), i / fps);
      const buf = await canvas.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 30 === 0) console.log(`frame ${i}/${n} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
