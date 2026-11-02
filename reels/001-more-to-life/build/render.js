// Usage: node render.js stills 0,30,59  |  node render.js video out.mp4 [audio.wav]
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const path = require('path'), fs = require('fs');
(async () => {
  const [mode, arg, audio] = process.argv.slice(2);
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('console', m => console.log('[page]', m.text())); page.on('pageerror', e => { console.error('PAGEERROR', e); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'reel.html'));
  console.log('font ok:', await page.evaluate(() => window.ready));
  const grab = f => page.evaluate(f => { renderFrame(f); return document.getElementById('c').toDataURL('image/png').slice(22); }, f);
  if (mode === 'stills') {
    fs.mkdirSync(path.join(__dirname, 'stills'), { recursive: true });
    for (const f of arg.split(',').map(Number)) fs.writeFileSync(path.join(__dirname, 'stills', `f${String(f).padStart(3, '0')}.png`), Buffer.from(await grab(f), 'base64'));
  } else {
    const out = arg;
    const a = ['-y', '-f', 'image2pipe', '-framerate', '24', '-i', '-'];
    if (audio) a.push('-i', audio);
    a.push('-c:v', 'libx264', '-profile:v', 'high', '-pix_fmt', 'yuv420p', '-crf', '15', '-preset', 'slow', '-r', '24', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-movflags', '+faststart');
    if (audio) a.push('-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-shortest');
    a.push('-t', '15', out);
    const ff = spawn('ffmpeg', a, { stdio: ['pipe', 'ignore', 'inherit'] });
    const t0 = Date.now();
    for (let f = 0; f < 360; f++) {
      const buf = Buffer.from(await grab(f), 'base64');
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (f % 30 === 0) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(1) + 's');
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await browser.close();
})();
