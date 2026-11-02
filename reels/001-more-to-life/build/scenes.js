// Scenes 1–5 + transitions + text track. Timing follows production-package.md §2/§4 (24 fps, 360 frames).
'use strict';
const G = {}; // generated geometry, built once

function initScenes() {
  const r = rng(11);
  // scene 1 city strip
  G.city = []; for (let x = 0; x < 3200;) { const w = 60 + r() * 140, far = r() < .45; G.city.push({ x, w, h: far ? 200 + r() * 300 : 300 + r() * 520, far, win: r() }); x += w * (far ? .6 : 1) + r() * 20; }
  G.poles = []; for (let i = 0; i < 6; i++) G.poles.push(i * 560 + r() * 200);
  // crossing pedestrians
  G.peds = []; for (let i = 0; i < 60; i++) G.peds.push({ x: r() * 900, y: r() * 600, layer: i % 3, tone: r(), dir: r() < .5 ? 1 : -1, sz: .8 + r() * .4 });
  // lecture heads
  G.heads = []; for (let row = 0; row < 5; row++) { const sc = .55 + row * .17, y = 230 + row * 56 + row * row * 6, n = Math.floor(12 / sc); for (let i = 0; i < n; i++) { const x = 40 + i * (1008 - 60) / n + (r() - .5) * 20 * sc; G.heads.push({ x, y, sc, t: r(), sora: row === 2 && i === Math.floor(n * .55) }); } }
  // night bokeh + rain
  G.bokeh = []; for (let i = 0; i < 90; i++) G.bokeh.push({ x: r() * 960, y: 80 + r() * 1100, r: 6 + r() * r() * 30, a: .25 + r() * .6, ph: r() * 6 });
  G.rain = []; for (let i = 0; i < 26; i++) G.rain.push({ x: r() * 960, y0: r() * 1300, sp: 1.5 + r() * 4, len: 60 + r() * 220, seed: i });
  // splash: prerendered layers
  buildSplash();
  // café books
  G.books = []; for (let x = 0; x < 380;) { const w = 14 + r() * 22; G.books.push({ x, w, h: 90 + r() * 60, t: r() }); x += w + 2; }
}

/* ======================= SCENE 1 — ROUTINE ======================= */
function windowPanel(c, w, h, f) {
  c.fillStyle = C.tLight; c.fillRect(0, 0, w, h); c.fillStyle = tone(c, .16, 6); c.fillRect(0, 0, w, h);
  const wx = 40, wy = 150, ww = w - 80, wh = 1320;
  c.save(); c.beginPath(); c.roundRect(wx, wy, ww, wh, 40); c.clip();
  // outside: morning sky + scrolling city
  const sg = c.createLinearGradient(0, wy, 0, wy + wh); sg.addColorStop(0, '#E9E6DF'); sg.addColorStop(1, '#BDBAB3'); c.fillStyle = sg; c.fillRect(wx, wy, ww, wh);
  const off = (f * 16) % 2400;
  for (const pass of [true, false]) for (const b of G.city) if (b.far === pass) {
    const x = wx + ((b.x - off * (pass ? .5 : 1)) % 2400 + 2400) % 2400 - 300, top = wy + wh - b.h - (pass ? 260 : 120);
    if (x > wx + ww || x + b.w < wx) continue;
    c.fillStyle = pass ? tone(c, .12, 6) : tone(c, .28, 6); c.fillRect(x, top, b.w, wy + wh - top);
    if (!pass) { c.fillStyle = 'rgba(244,241,234,.35)'; for (let yy = top + 20; yy < wy + wh - 40; yy += 34) for (let xx = x + 10; xx < x + b.w - 14; xx += 24) c.fillRect(xx, yy, 10, 16); }
    brush(c, [[x, top + 4], [x + b.w, top]], 3, { taper: false, alpha: pass ? .4 : .9 });
  }
  // motion streak lines
  for (let i = 0; i < 7; i++) { const yy = wy + 300 + i * 150; brush(c, [[wx, yy], [wx + ww, yy + 4]], 1.5, { alpha: .25 }); }
  for (const p of G.poles) { const x = wx + ((p - f * 70) % 3360 + 3360) % 3360 - 200; if (x > wx - 40 && x < wx + ww + 40) { c.fillStyle = C.ink; c.globalAlpha = .85; c.fillRect(x, wy, 22, wh); c.globalAlpha = 1; } }
  // reflection (multiply ink over the outside view)
  const blink = f >= 46 && f <= 50 ? Math.sin(prog(f, 46, 50) * Math.PI) : 0;
  const sc = c.getTransform().a, R = (BUF.refl = BUF.refl || mk(1, 1));
  const rs = Math.min(3, sc * 1.05); if (R.width !== Math.ceil(w * rs)) { R.width = Math.ceil(w * rs); R.height = Math.ceil(h * rs); }
  const x = R.getContext('2d'); x.setTransform(1, 0, 0, 1, 0, 0); x.fillStyle = '#fff'; x.fillRect(0, 0, R.width, R.height); x.scale(rs, rs);
  drawBust(x, { x: w / 2 + 10, y: 700, s: .9, coat: C.tLight });
  drawFace(x, { x: w / 2 + 10, y: 700, s: .9, who: 'sora', blink, look: [-.35, -.1], skin: '#E2DED6' });
  c.save(); c.globalCompositeOperation = 'multiply'; c.globalAlpha = .82; c.drawImage(R, 0, 0, w, h); c.restore();
  // passing light bands
  for (const [a, b] of [[8, 26], [40, 52]]) {
    const p = prog(f, a, b); if (p <= 0 || p >= 1) continue;
    const x = lerp(wx + ww + 200, wx - 300, p);
    const g = c.createLinearGradient(x - 120, 0, x + 120, 0); g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(.5, 'rgba(255,253,246,.55)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    c.save(); c.globalCompositeOperation = 'screen'; c.translate(x, 0); c.transform(1, 0, -.35, 1, 0, 0); c.translate(-x, 0); c.fillStyle = g; c.fillRect(x - 160, wy, 320, wh); c.restore();
  }
  // glass sheen
  c.save(); c.globalAlpha = .18; c.fillStyle = C.paper; c.beginPath(); c.moveTo(wx, wy + 200); c.lineTo(wx + 120, wy); c.lineTo(wx + 190, wy); c.lineTo(wx, wy + 330); c.fill(); c.restore();
  c.restore();
  // door frame + rubber seal
  c.save(); c.lineWidth = 16; c.strokeStyle = C.deep; c.beginPath(); c.roundRect(wx, wy, ww, wh, 40); c.stroke(); c.restore();
  brush(c, [[wx + 14, wy + wh + 20], [wx + ww - 14, wy + wh + 20]], 3, { taper: false, alpha: .7 });
  c.fillStyle = tone(c, .35, 6); c.fillRect(0, wy + wh + 60, w, h); brush(c, [[0, wy + wh + 60], [w, wy + wh + 60]], 4, { taper: false });
  brush(c, [[w - 26, 0], [w - 26, h]], 6, { taper: false });
}
function strapPanel(c, w, h, f) {
  c.fillStyle = C.paper; c.fillRect(0, 0, w, h);
  gradTone(c, 0, 0, w, h, (u, v) => .08 + v * .25, 7);
  // ceiling ad frame (blank) + bar
  c.fillStyle = C.paper; c.fillRect(30, 20, w - 60, 70); inkRect(c, 30, 20, w - 60, 70, 3, 9);
  brush(c, [[-10, 130], [w + 10, 126]], 9, { taper: false });
  // background straps
  for (const bx of [60, 330]) { brush(c, [[bx, 130], [bx + 2, 230]], 12, { taper: false, color: C.tMid }); c.lineWidth = 7; c.strokeStyle = C.tMid; c.beginPath(); c.arc(bx + 2, 262, 30, 0, 7); c.stroke(); }
  // main strap swing
  const a = Math.sin(f * .26) * .045 + Math.sin(f * .61) * .015;
  c.save(); c.translate(200, 130); c.rotate(a);
  brush(c, [[0, 0], [0, 190]], 26, { taper: false, color: C.paper }); brush(c, [[-13, 0], [-13, 190]], 3, { taper: false }); brush(c, [[13, 0], [13, 190]], 3, { taper: false });
  c.lineWidth = 16; c.strokeStyle = C.paper; c.beginPath(); c.roundRect(-62, 190, 124, 120, 34); c.stroke();
  c.lineWidth = 3; c.strokeStyle = C.ink; c.beginPath(); c.roundRect(-70, 182, 140, 136, 40); c.stroke(); c.beginPath(); c.roundRect(-54, 198, 108, 104, 26); c.stroke();
  // hand gripping the top of the ring
  const hand = [[-58, 178], [-30, 166], [10, 164], [52, 172], [74, 196], [70, 232], [40, 246], [-10, 246], [-50, 236], [-72, 210]];
  fillShape(c, hand, C.paper); brush(c, [...hand, hand[0]], 3.5, { min: .5 });
  for (const x of [-34, -6, 22, 48]) brush(c, [[x, 182], [x + 2, 214], [x - 2, 242]], 2.6, { min: .4 });
  c.save(); path(c, hand); c.clip(); c.fillStyle = tone(c, .25, 5); c.fillRect(-80, 220, 160, 40); c.restore();
  // sleeve
  const sl = [[-50, 230], [40, 240], [120, 520], [-30, 540]]; fillShape(c, sl, C.tMid); c.save(); path(c, sl); c.clip(); c.fillStyle = tone(c, .3, 5); c.fillRect(-80, 200, 260, 400); hatch(c, null, -60, 230, 200, 320, 1.1, 10, 1.4, { alpha: .5 }); c.restore();
  brush(c, sl, 3.5); brush(c, [[-50, 230], [-30, 540]], 3.5); brush(c, [[-46, 262], [44, 270]], 2.5);
  c.restore();
}
function phonesPanel(c, w, h, f) {
  c.fillStyle = C.tDark; c.fillRect(0, 0, w, h); c.fillStyle = tone(c, .35, 6); c.fillRect(0, 0, w, h);
  hatch(c, null, 0, 0, w, h, 1.57, 14, 1.2, { alpha: .35, seed: 21, len: .6 });
  const people = [[80, 210, .8, 0], [300, 280, .9, 1], [170, 450, 1.1, 2]];
  for (const [x, y, s, k] of people) {
    c.save(); c.translate(x, y); c.scale(s, s);
    fillShape(c, [[-120, 70], [-60, 36], [60, 36], [120, 76], [140, 300], [-140, 300]], k === 1 ? C.tMid : C.deep);
    brush(c, [[-120, 70], [-60, 36], [60, 36], [120, 76], [140, 300]], 3.5, { color: C.ink });
    // head bowed, three-quarter down-right; face lit from below by the phone
    const head = [[-34, -66], [0, -86], [34, -74], [50, -40], [52, -6], [40, 24], [14, 40], [-16, 34], [-36, 0]];
    fillShape(c, head, '#CFCBC2'); c.save(); path(c, head); c.clip(); c.fillStyle = tone(c, .45, 5); c.fillRect(-40, -90, 50, 140); c.restore();
    brush(c, head.slice(3, 8), 3);
    fillShape(c, [[-44, -30], [-38, -84], [0, -100], [40, -84], [56, -44], [40, -52], [20, -60], [-6, -52], [-28, -26], [-36, 10]], C.ink);
    brush(c, [[20, -24], [36, -20]], 3.2); brush(c, [[30, -4], [36, 6], [30, 10]], 2.2); brush(c, [[20, 22], [32, 22]], 2.2);
    c.save(); c.translate(70, 64); c.rotate(-.5); c.fillStyle = C.ink; c.fillRect(-15, -24, 30, 50); c.fillStyle = '#F2F0EA'; c.fillRect(-12, -21, 24, 42); c.restore();
    brush(c, [[40, 80], [62, 70], [78, 76]], 16, { taper: false, color: '#CFCBC2' });
    glow(c, 64, 40, 80, 'rgba(255,255,250,1)', .3 + .08 * Math.sin(f * .9 + k * 2));
    c.restore();
  }
}
function shoesPanel(c, w, h, f) {
  c.fillStyle = C.tLight; c.fillRect(0, 0, w, h); gradTone(c, 0, 0, w, h, (u, v) => .35 - v * .2, 7);
  brush(c, [[0, 160], [w, 150]], 6, { taper: false }); brush(c, [[0, 175], [w, 166]], 2, { taper: false, alpha: .6 });
  for (let i = 0; i < 6; i++) brush(c, [[0, 230 + i * 70], [w, 220 + i * 74]], 1.4, { taper: false, alpha: .25 });
  const shoe = (x, y, s, white, flip) => {
    c.save(); c.translate(x, y); c.scale(flip ? -s : s, s);
    const p = [[-64, 6], [-62, -30], [-40, -34], [-14, -26], [16, -34], [46, -26], [66, -10], [70, 6], [60, 12], [-58, 12]];
    fillShape(c, p, white ? C.paper : C.ink);
    if (white) { brush(c, [...p, p[0]], 3, { taper: false }); brush(c, [[-62, 4], [66, 2]], 3, { taper: false }); for (let i = 0; i < 4; i++) brush(c, [[-10 + i * 8, -40 + i * 3], [4 + i * 8, -36 + i * 3]], 2); fillShape(c, [[-50, -6], [-30, -20], [-10, -10], [-26, 2]], tone(c, .25, 5)); }
    else { fillShape(c, [[-56, -28], [-40, -32], [-16, -24], [-30, -18]], '#2c2c2c'); brush(c, [[10, -30], [40, -24], [60, -10]], 3, { color: C.paper, alpha: .45 }); brush(c, [[-64, -4], [70, -2]], 1.5, { color: C.tMid, taper: false }); brush(c, [[-60, 8], [62, 6]], 4, { color: C.tMid, taper: false }); }
    c.restore();
  };
  const sw = Math.sin(f * .4) * 1.2;
  shoe(70, 300, 1, false, false); shoe(150, 320 + sw, 1.05, false, false);
  shoe(80, 450, 1.15, false, false); shoe(330, 300, 1, false, true); shoe(330, 430 + sw, 1.1, false, true);
  shoe(196, 540, 1.3, true, false); shoe(310, 560, 1.3, true, true);
}

function scene1(c, f) {
  c.fillStyle = C.paper; c.fillRect(0, 0, W, H);
  const vib = Math.sin(f * 1.7) * 1.2 + Math.sin(f * 4.3) * .5;
  // camera: slow push in 1A, big push into reflection in 1B
  const F = [454 + 305, 36 + 700];
  let s, fs;
  if (f < 30) { s = lerp(1, 1.05, f / 30); fs = [lerp(F[0], F[0] - 10, f / 30), F[1]]; }
  else { const p = ease(prog(f, 30, 59)); s = lerp(1.05, 2.6, p); fs = [lerp(F[0] - 10, 540, p), lerp(F[1], 880, p)]; }
  c.save(); c.translate(fs[0], fs[1] + vib); c.scale(s, s); c.translate(-F[0], -F[1]);
  const par = f >= 30 ? ease(prog(f, 30, 59)) * 260 : 0; // left column exits faster (parallax)
  c.save(); c.translate(-par, 0);
  panel(c, 36, 36, 400, 604, (c, w, h) => strapPanel(c, w, h, f));
  panel(c, 36, 658, 400, 604, (c, w, h) => phonesPanel(c, w, h, f));
  panel(c, 36, 1280, 400, 604, (c, w, h) => shoesPanel(c, w, h, f));
  c.restore();
  panel(c, 454, 36, 590, 1848, (c, w, h) => windowPanel(c, w, h, f));
  c.restore();
  tint(c, C.blueGray, .2, 'color');
}

/* ======================= SCENE 2 — EXPECTATIONS ======================= */
function lecturePanel(c, w, h) {
  c.fillStyle = C.paper; c.fillRect(0, 0, w, h);
  gradTone(c, 0, 0, w, h, (u, v) => .12 + v * .12, 7);
  for (let i = 0; i < 3; i++) { const x = 20 + i * 90; c.fillStyle = C.paper; c.fillRect(x, 20, 70, 200); inkRect(c, x, 20, 70, 200, 2.5, 30 + i); brush(c, [[x + 35, 20], [x + 35, 220]], 2, { taper: false }); }
  c.fillStyle = '#FBFAF6'; c.fillRect(380, 40, 330, 150); inkRect(c, 380, 40, 330, 150, 3, 41);
  // professor (small)
  fillShape(c, [[742, 150], [760, 150], [766, 210], [736, 210]], C.ink); c.fillStyle = C.ink; c.beginPath(); c.arc(751, 138, 11, 0, 7); c.fill();
  brush(c, [[0, 200], [w, 196]], 3, { taper: false });
  for (const hd of G.heads) {
    const { x, y, sc } = hd;
    c.save(); c.translate(x, y); c.scale(sc, sc);
    const fill = hd.sora ? tone(c, .32, 6) : hd.t < .4 ? C.deep : hd.t < .7 ? C.paper : tone(c, .5, 6);
    fillShape(c, [[-46, 30], [-22, 14], [22, 14], [46, 30], [54, 90], [-54, 90]], fill);
    brush(c, [[-54, 90], [-46, 30], [-22, 14], [22, 14], [46, 30], [54, 90]], 3);
    fillShape(c, [[-22, 14], [-26, -18], [-12, -36], [12, -36], [26, -18], [22, 14]], C.ink);
    if (hd.sora) { brush(c, [[-20, -30], [-6, -38], [14, -30]], 3, { color: C.paper, alpha: .6 }); fillShape(c, [[24, 30], [34, 24], [44, 90], [30, 90]], C.tDark); }
    c.restore();
  }
  for (let row = 0; row < 5; row++) { const sc = .55 + row * .17, y = 230 + row * 56 + row * row * 6 + 60 * sc; brush(c, [[0, y], [w, y - 4]], 4 * sc, { taper: false }); c.fillStyle = C.paper; c.fillRect(0, y + 2 * sc, w, 16 * sc); }
}
function renPanel(c, w, h, f) {
  c.fillStyle = '#E4E1DA'; c.fillRect(0, 0, w, h);
  for (let x = 0; x <= w; x += 46) brush(c, [[x, 0], [x, h]], x % 138 === 0 ? 4 : 1.5, { taper: false, alpha: .8 });
  for (let y = 40; y < 420; y += 120) brush(c, [[0, y], [w, y]], 3, { taper: false });
  for (let y = 0; y < 420; y += 12) brush(c, [[0, y], [w, y]], .8, { taper: false, alpha: .3 });
  c.fillStyle = tone(c, .4, 6); c.fillRect(0, 430, w, h); brush(c, [[0, 430], [w, 430]], 5, { taper: false });
  c.save(); c.translate(250, 420); c.rotate(-.25); c.fillStyle = C.deep; c.fillRect(-6, -110, 12, 110); c.restore();
  brush(c, [[170, 432], [300, 432]], 8, { taper: false, color: C.tMid });
  renProfile(c, 96, 300, .95, f);
}
function crossingPanel(c, w, h, f) {
  c.fillStyle = C.tDark; c.fillRect(0, 0, w, h); c.fillStyle = tone(c, .25, 5, C.ink); c.fillRect(0, 0, w, h);
  c.fillStyle = '#E8E5DE'; for (let x = -20; x < w; x += 54) c.fillRect(x, 190, 30, 150);
  for (let y = 0; y < h; y += 54) if (y < 170 || y > 350) c.fillRect(470, y, 120, 30);
  const sp = [1.6, 2.4, 3.4];
  for (const p of G.peds) {
    const L = p.layer; let x, y;
    if (L < 2) { x = ((p.x + p.dir * f * sp[L] * 2) % 900 + 900) % 900 - 100; y = 130 + p.y * .4; }
    else { x = 440 + p.x * .2; y = ((p.y + p.dir * f * sp[L] * 2) % 760 + 760) % 760 - 100; }
    const s = p.sz * (1 + L * .15);
    c.save(); c.translate(x, y); c.scale(s, s);
    c.fillStyle = 'rgba(17,17,17,.4)'; c.beginPath(); c.ellipse(8, 10, 20, 9, .3, 0, 7); c.fill();
    c.fillStyle = p.tone < .35 ? C.paper : p.tone < .7 ? C.tMid : C.deep; c.beginPath(); c.ellipse(0, 0, 18, 10, 0, 0, 7); c.fill();
    c.lineWidth = 2; c.strokeStyle = C.ink; c.stroke();
    c.fillStyle = C.ink; c.beginPath(); c.arc(0, -2, 8, 0, 7); c.fill();
    c.restore();
  }
  // the reel's only speed lines (pressure of routine), flickering on twos
  const rr = rng(Math.floor(f / 2) + 5);
  for (let i = 0; i < 9; i++) { const y = 60 + rr() * 440, x = rr() * w * .6; brush(c, [[x, y], [x + 120 + rr() * 220, y]], 2.2, { color: C.paper, alpha: .55 }); }
}
function clockPanel(c, w, h, f) {
  c.fillStyle = C.paper; c.fillRect(0, 0, w, h); gradTone(c, 0, 0, w, h, (u, v) => .1 + v * .3, 7);
  for (let x = 30; x < w; x += 60) brush(c, [[x, 420], [x, h]], 1.6, { taper: false, alpha: .6 });
  brush(c, [[150, 0], [150, 120]], 8, { taper: false });
  const cx = 150, cy = 250, R = 116;
  c.fillStyle = '#FBFAF6'; c.beginPath(); c.arc(cx, cy, R, 0, 7); c.fill(); c.lineWidth = 12; c.strokeStyle = C.ink; c.stroke();
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2, l = i % 5 ? 8 : 20, wd = i % 5 ? 2 : 6; line(c, cx + Math.sin(a) * (R - 12), cy - Math.cos(a) * (R - 12), cx + Math.sin(a) * (R - 12 - l), cy - Math.cos(a) * (R - 12 - l), wd, { wob: 0, n: 1 }); }
  const min = 47 + (f >= 104 ? 1 : 0), hr = 8 + min / 60;
  const hand = (a, len, wd) => line(c, cx, cy, cx + Math.sin(a) * len, cy - Math.cos(a) * len, wd, { wob: 0, n: 1 });
  hand(hr / 12 * Math.PI * 2, 58, 10); hand(min / 60 * Math.PI * 2, 88, 7);
  c.fillStyle = C.ink; c.beginPath(); c.arc(cx, cy, 9, 0, 7); c.fill();
}
function checklistPanel(c, w, h, f) {
  c.fillStyle = '#E2DCCF'; c.fillRect(0, 0, w, h); c.fillStyle = tone(c, .1, 5); c.fillRect(0, 0, w, h);
  for (let y = 100; y < h; y += 66) brush(c, [[20, y], [w - 20, y]], 1.2, { taper: false, alpha: .45 });
  brush(c, [[w - 34, 0], [w - 34, h]], 8, { taper: false }); // elastic band
  const rows = [150, 282, 414, 546, 678];
  rows.forEach((y, i) => {
    c.fillStyle = C.paper; c.fillRect(40, y - 40, 40, 40); inkRect(c, 40, y - 40, 40, 40, 2.6, 60 + i);
    const r = rng(90 + i), len = 120 + r() * 120, pts = [];
    for (let x = 0; x <= len; x += 10) pts.push([104 + x, y - 18 + Math.sin(x * .18 + i) * 6 + (r() - .5) * 4]);
    brush(c, pts, 3.2, { min: .5, raw: true });
    if (i < 4) brush(c, [[44, y - 22], [58, y - 4], [92, y - 56]], 6, { min: .3 });
  });
  const y5 = 678, tick = [[44, y5 - 22], [58, y5 - 4], [92, y5 - 56]];
  const tp = prog(f, 101, 106); if (tp > 0) brush(c, tick, 6, { min: .3, trim: tp });
  // pen + fingertips
  if (f >= 94 && f <= 116) {
    const pts = spline(tick, false, 8); const k = Math.min(pts.length - 1, Math.floor(pts.length * Math.max(tp, .02)));
    const enter = easeOut(prog(f, 94, 101)), leave = easeIn(prog(f, 107, 116));
    const tx = pts[k][0] + (1 - enter) * 260 + leave * 240, ty = pts[k][1] + (1 - enter) * 300 + leave * 280;
    c.save(); c.translate(tx, ty); c.rotate(-.75);
    fillShape(c, [[-5, 0], [5, 0], [12, 30], [12, 330], [-12, 330], [-12, 30]], C.ink); brush(c, [[-2, 40], [-2, 300]], 2, { color: C.paper, alpha: .5 });
    fillShape(c, [[-20, 80], [30, 90], [56, 150], [40, 240], [-30, 230], [-40, 140]], C.paper); brush(c, [[-20, 80], [30, 90], [56, 150], [40, 240]], 3); brush(c, [[-20, 80], [-40, 140], [-30, 230]], 3);
    c.restore();
  }
}
function vendingPanel(c, w, h, f) {
  c.fillStyle = C.deep; c.fillRect(0, 0, w, h);
  c.fillStyle = '#F7F6F1'; c.fillRect(24, 30, w - 48, 460); glow(c, w / 2, 250, 300, 'rgba(255,255,255,.7)', .6);
  for (let r = 0; r < 3; r++) for (let i = 0; i < 3; i++) { const x = 48 + i * 72, y = 70 + r * 140; c.fillStyle = [C.tMid, C.paper, C.tDark][(r + i) % 3]; c.beginPath(); c.roundRect(x, y, 48, 96, 10); c.fill(); brush(c, [[x, y + 10], [x, y + 90], [x + 48, y + 90], [x + 48, y + 10]], 2, { taper: false }); c.fillStyle = C.ink; c.fillRect(x + 6, y + 104, 36, 10); }
  inkRect(c, 24, 30, w - 48, 460, 3, 5);
  c.fillStyle = C.ink; c.fillRect(40, 560, w - 80, 110); inkRect(c, 40, 560, w - 80, 110, 3, 6, C.tMid);
  // can + hand + sleeve
  const lift = easeOut(prog(f, 72, 100)) * 40;
  c.save(); c.translate(150, 620 - lift);
  fillShape(c, [[-24, -30], [24, -30], [24, 40], [-24, 40]], C.tLight); brush(c, [[-24, -30], [24, -30], [24, 40], [-24, 40], [-24, -30]], 2.5, { taper: false });
  const hand = [[-40, -10], [10, -40], [60, -20], [64, 30], [20, 52], [-36, 40]]; fillShape(c, hand, C.paper); brush(c, [...hand, hand[0]], 3);
  for (const y of [-10, 8, 26]) brush(c, [[-20, y], [30, y - 6]], 2);
  const sl = [[40, -40], [200, -120], [240, 40], [60, 50]]; fillShape(c, sl, C.tMid); c.save(); path(c, sl); c.clip(); c.fillStyle = tone(c, .3, 5); c.fillRect(0, -150, 300, 250); c.restore(); brush(c, [...sl, sl[0]], 3);
  c.restore();
}
const S2 = [ // panel rects + slide dirs
  { r: [36, 36, 1008, 500], d: [0, -1], fn: (c, w, h, f) => lecturePanel(c, w, h, f) },
  { r: [36, 554, 300, 560], d: [-1, 0], fn: renPanel },
  { r: [354, 554, 690, 560], d: [1, 0], fn: crossingPanel },
  { r: [36, 1132, 300, 752], d: [-1, 0], fn: clockPanel },
  { r: [354, 1132, 380, 752], d: [0, 1], fn: checklistPanel },
  { r: [752, 1132, 292, 752], d: [1, 0], fn: vendingPanel },
];
function scene2(c, f) {
  c.fillStyle = C.paper; c.fillRect(0, 0, W, H);
  const push = ease(prog(f, 96, 108)), s = lerp(1, 1.08, push), fx = 544, fy = 1508;
  c.save(); c.translate(fx, fy); c.scale(s, s); c.translate(-fx, -fy);
  S2.forEach((p, i) => {
    const t = easeOut(prog(f, 61 + i * 4, 61 + i * 4 + 8)); if (t <= 0) return;
    const [x, y, w, h] = p.r;
    c.save(); c.globalAlpha = t; c.translate(p.d[0] * (1 - t) * 60, p.d[1] * (1 - t) * 60);
    panel(c, x, y, w, h, (c, w, h) => p.fn(c, w, h, f), { seed: i * 9 + 3 }); c.restore();
  });
  c.restore();
}

/* ======================= SCENE 3 — THE PAUSE ======================= */
function scene3a(c, f) {
  c.fillStyle = C.ink; c.fillRect(0, 0, W, H);
  panel(c, 60, 60, 960, 1800, (c, w, h) => {
    c.fillStyle = '#0B0B0B'; c.fillRect(0, 0, w, h);
    // window
    c.save(); c.beginPath(); c.rect(40, 40, w - 80, 1300); c.clip();
    c.fillStyle = '#050505'; c.fillRect(0, 0, w, h);
    for (const b of G.bokeh) { const a = b.a * (.85 + .15 * Math.sin(f * .15 + b.ph)); c.save(); c.globalAlpha = a; c.filter = `blur(${b.r * .35}px)`; c.fillStyle = b.r > 20 ? C.tLight : C.paper; c.beginPath(); c.arc(b.x, b.y + 300, b.r, 0, 7); c.fill(); c.restore(); }
    for (const rd of G.rain) { const y = (rd.y0 + f * rd.sp * 2) % 1400; const pts = []; for (let k = 0; k <= 6; k++) pts.push([rd.x + Math.sin(k + rd.seed) * 3, y - rd.len + k * rd.len / 6]); brush(c, pts, 2.2, { color: C.paper, alpha: .35, raw: false }); c.fillStyle = 'rgba(244,241,234,.7)'; c.beginPath(); c.arc(pts[6][0], y, 3.5, 0, 7); c.fill(); }
    c.restore();
    brush(c, [[w / 2, 40], [w / 2, 1340]], 10, { taper: false, color: C.deep }); brush(c, [[40, 1340], [w - 40, 1340]], 14, { taper: false, color: C.deep });
    inkRect(c, 40, 40, w - 80, 1300, 6, 31, C.deep);
    // counter
    c.fillStyle = C.deep; c.fillRect(0, 1360, w, h); brush(c, [[0, 1364], [w, 1360]], 3, { taper: false, color: C.tMid });
    hatch(c, () => { c.beginPath(); c.rect(0, 1380, w, 500); }, 0, 1380, w, 500, 0, 16, 1.2, { color: C.tDark, alpha: .6, seed: 4, len: .5 });
    soraSeatedBack(c, 250, 1600, .95);
    glow(c, 640, 1380, 90, 'rgba(244,241,234,.5)', .2); // mug glint
    fillShape(c, [[610, 1330], [670, 1330], [664, 1384], [616, 1384]], C.tMid);
  }, { borderColor: C.deep });
}
function scene3b(c, f) {
  c.fillStyle = C.ink; c.fillRect(0, 0, W, H);
  panel(c, 60, 60, 960, 1800, (c, w, h) => {
    c.fillStyle = '#16120F'; c.fillRect(0, 0, w, h);
    hatch(c, null, 0, 0, w, h, .06, 22, 1.4, { color: '#3a332c', seed: 8, len: .7 });
    // window reflection on counter
    c.save(); c.globalAlpha = .16; c.fillStyle = C.paper; c.beginPath(); c.moveTo(80, 0); c.lineTo(460, 0); c.lineTo(300, 900); c.lineTo(0, 900); c.fill(); c.restore();
    const ry = (f - 150) * 9; brush(c, [[250, 120 + ry], [246, 220 + ry], [252, 330 + ry]], 3, { color: C.paper, alpha: .45 });
    // notebook (open, blank)
    const nb = [[360, 1000], [820, 950], [880, 1450], [400, 1510]];
    fillShape(c, nb, '#EDEAE2'); brush(c, [...nb, nb[0]], 4, { taper: false });
    brush(c, [[590, 975], [640, 1480]], 3, { taper: false, alpha: .7 });
    c.save(); path(c, nb); c.clip(); c.fillStyle = tone(c, .12, 6); c.fillRect(570, 900, 60, 700); c.restore();
    brush(c, [[800, 952], [856, 1452]], 9, { taper: false });
    // mug
    c.save(); c.translate(250, 700);
    fillShape(c, [[-120, 0], [120, 0], [110, 260], [-110, 260]], '#D9D5CC'); c.save(); path(c, [[-120, 0], [120, 0], [110, 260], [-110, 260]]); c.clip(); c.fillStyle = tone(c, .35, 6); c.fillRect(-140, 0, 90, 280); c.restore();
    brush(c, [[-120, 0], [-110, 260]], 5, { taper: false }); brush(c, [[120, 0], [110, 260]], 5, { taper: false }); brush(c, [[-110, 260], [110, 260]], 5, { taper: false });
    c.fillStyle = C.coffee; c.beginPath(); c.ellipse(0, 40, 104, 24, 0, 0, 7); c.fill();
    c.lineWidth = 5; c.strokeStyle = C.ink; c.beginPath(); c.ellipse(0, 0, 120, 30, 0, 0, 7); c.stroke();
    c.lineWidth = 22; c.strokeStyle = '#D9D5CC'; c.beginPath(); c.arc(140, 120, 56, -1.3, 1.3); c.stroke(); c.lineWidth = 4; c.strokeStyle = C.ink; c.beginPath(); c.arc(140, 120, 68, -1.25, 1.25); c.stroke(); c.beginPath(); c.arc(140, 120, 44, -1.2, 1.2); c.stroke();
    for (let k = 0; k < 2; k++) { const pts = []; for (let i = 0; i < 9; i++) { const yy = -30 - i * 50, ph = f * .12 + i * .7 + k * 2; pts.push([Math.sin(ph) * (10 + i * 5) + k * 30 - 15, yy, 1 - i / 10]); } brush(c, pts, 7, { color: C.paper, alpha: .28 }); }
    c.restore();
    // pen lying on the notebook, hand resting beside it (not writing)
    c.save(); c.translate(700, 1230); c.rotate(-.9); fillShape(c, [[-6, -170], [6, -170], [9, 150], [-9, 150]], C.ink); brush(c, [[-2, -150], [-2, 130]], 2, { color: C.paper, alpha: .5 }); c.restore();
    handTop(c, 800, 1560, 1.25, -.55, { skin: '#E6E1D7' });
  }, { borderColor: C.deep });
  // breath + ink bleed to paper (f174–179)
  const p = prog(f, 173.5, 179.5);
  if (p > 0) {
    const r = rng(77); c.save(); c.fillStyle = C.ink;
    for (let i = 0; i < 70; i++) { const side = i % 4, t = r(); const x = side === 0 ? t * W : side === 1 ? W : side === 2 ? t * W : 0, y = side === 0 ? 0 : side === 1 ? t * H : side === 2 ? H : t * H; c.beginPath(); c.arc(x, y, easeIn(p) * (300 + r() * 700), 0, 7); c.fill(); }
    c.restore();
  }
}

/* ======================= SCENE 4 — THE QUESTION (splash) ======================= */
const SPL = { pad: 160 };
function buildSplash() {
  const r = rng(21), Hh = H + SPL.pad;
  // sky (monochrome tone)
  const sky = mk(W, Hh), s = sky.getContext('2d');
  s.fillStyle = C.paper; s.fillRect(0, 0, W, Hh);
  gradTone(s, 0, 0, W, 1400, (u, v) => .7 - v * .48, 9);
  SPL.sky = sky;
  // clouds (two drifting layers, wider than frame)
  SPL.clouds = [0, 1].map(k => {
    const cl = mk(1800, Hh), x = cl.getContext('2d'), rr = rng(30 + k);
    const n = k ? 6 : 8;
    for (let i = 0; i < n; i++) {
      const cx = (i + rr() * .6) * 1800 / n, cy = k ? 1080 + rr() * 60 : 200 + rr() * 330, bw = (k ? 220 : 300) + rr() * 300, bh = (k ? 40 : 60) + rr() * 60;
      const lobes = []; for (let j = 0; j < 7; j++) lobes.push([cx + (j - 3) * bw / 7 + (rr() - .5) * 30, cy - Math.sin(j / 6 * Math.PI) * bh * (.5 + rr() * .5), bw / 6 + rr() * 26]);
      const uni = () => { x.beginPath(); for (const [lx, ly, lr] of lobes) { x.moveTo(lx + lr * 1.3, ly); x.ellipse(lx, ly, lr * 1.3, lr * .75, 0, 0, 7); } };
      uni(); x.fillStyle = k ? '#D3D0C9' : '#ECE9E2'; x.fill();
      x.save(); uni(); x.clip(); x.fillStyle = tone(x, k ? .38 : .26, 6); x.fillRect(cx - bw, cy - bh * .1, bw * 2, bh * 2); x.fillStyle = tone(x, .12, 6); x.fillRect(cx - bw, cy - bh * .5, bw * 2, bh * .4); x.restore();
      brush(x, lobes.map(([lx, ly, lr]) => [lx, ly - lr * .72]), 2.8, { alpha: .7 });
    }
    return cl;
  });
  // city band + power lines (horizon at 1230)
  const city = mk(W, Hh), cx = city.getContext('2d'); const hz = 1230;
  for (let x = -20; x < W;) {
    const w = 40 + r() * 90, h = 40 + r() * 170 * (r() < .2 ? 2 : 1);
    cx.fillStyle = r() < .5 ? C.deep : C.tDark; cx.fillRect(x, hz - h, w, h + 40);
    cx.fillStyle = 'rgba(244,241,234,.5)'; for (let yy = hz - h + 10; yy < hz - 6; yy += 16) for (let xx = x + 6; xx < x + w - 6; xx += 14) if (r() < .35) cx.fillRect(xx, yy, 5, 7);
    if (r() < .25) brush(cx, [[x + w / 2, hz - h], [x + w / 2, hz - h - 40]], 2, { taper: false });
    x += w + r() * 6;
  }
  // viaduct
  cx.fillStyle = C.ink; cx.fillRect(0, hz - 70, W, 12); for (let x = 30; x < W; x += 110) cx.fillRect(x, hz - 60, 10, 60);
  // power lines
  for (const px of [120, 860]) { brush(cx, [[px, hz - 320], [px + 4, hz + 20]], 6, { taper: false }); brush(cx, [[px - 40, hz - 300], [px + 44, hz - 300]], 4, { taper: false }); }
  for (let k = 0; k < 3; k++) { const pts = []; for (let i = 0; i <= 20; i++) { const t = i / 20; pts.push([lerp(-40, 1120, t), hz - 300 + k * 10 + Math.sin(t * Math.PI * 3) * 26 + 20]); } brush(cx, pts, 1.6, { raw: true, taper: false, alpha: .8 }); }
  // embankment
  cx.fillStyle = C.ink; cx.fillRect(0, hz, W, 26);
  SPL.city = city; SPL.hz = hz;
}
function splash(c, f) {
  const hz = SPL.hz, still = f < 192;
  const drift = still ? 0 : ease(prog(f, 192, 275));
  const ty = -SPL.pad + drift * 70, sc = 1 + drift * .04;
  c.save(); c.translate(W / 2, H / 2); c.scale(sc, sc); c.translate(-W / 2, -H / 2 + ty);
  c.drawImage(SPL.sky, 0, 0);
  // sky color (fades in): muted blue only above horizon
  const blue = ease(prog(f, 190, 250));
  if (blue > 0) { c.save(); c.globalCompositeOperation = 'color'; c.globalAlpha = .75 * blue; const g = c.createLinearGradient(0, 0, 0, hz); g.addColorStop(0, C.sky1); g.addColorStop(1, C.sky2); c.fillStyle = g; c.fillRect(0, 0, W, hz); c.restore();
    c.save(); c.globalCompositeOperation = 'multiply'; c.globalAlpha = .35 * blue; const g2 = c.createLinearGradient(0, 0, 0, hz); g2.addColorStop(0, C.sky1); g2.addColorStop(1, C.sky2); c.fillStyle = g2; c.fillRect(0, 0, W, hz); c.restore(); }
  const cd = still ? 0 : (f - 192);
  c.drawImage(SPL.clouds[1], -300 - cd * .6, 0); c.drawImage(SPL.clouds[0], -200 - cd * 1.1, 0);
  // gold horizon
  const gold = ease(prog(f, 220, 260));
  if (gold > 0) { c.save(); c.globalAlpha = gold; const g = c.createLinearGradient(0, hz - 120, 0, hz); g.addColorStop(0, 'rgba(201,161,90,0)'); g.addColorStop(1, 'rgba(201,161,90,.75)'); c.fillStyle = g; c.fillRect(0, hz - 120, W, 120); c.fillStyle = C.gold; c.fillRect(0, hz - 8, W, 5); c.restore(); }
  // hand-drawn ink lines along horizon
  const ip = prog(f, 200, 240);
  for (let k = 0; k < 4; k++) { const y = hz - 150 - k * 22; brush(c, [[60 + k * 40, y], [400, y - 6], [760, y - 2], [1040 - k * 30, y - 8]], 2.2, { trim: ip, alpha: .55 }); }
  c.drawImage(SPL.city, 0, 0);
  // train on viaduct
  const tx = ((f - 180) * 3.2) % 1600 - 400; c.fillStyle = C.ink; c.fillRect(tx, hz - 96, 360, 26); c.fillStyle = 'rgba(244,236,214,.95)'; for (let i = 0; i < 16; i++) c.fillRect(tx + 8 + i * 22, hz - 90, 12, 10);
  // river with trembling reflections
  c.fillStyle = '#1b1b1b'; c.fillRect(0, hz + 26, W, 420);
  for (let i = 0; i < 40; i++) { const r = rng(i * 3 + 1), y = hz + 40 + r() * 380, x = r() * W, l = 30 + r() * 140, sh = still ? 0 : Math.sin(f * .3 + i) * 6; brush(c, [[x + sh, y], [x + l + sh, y + 1]], 2 + r() * 2, { color: i % 5 === 0 ? C.gold : C.paper, alpha: (i % 5 === 0 ? gold * .7 : .35) + .05 }); }
  // footbridge deck + rail (foreground)
  const ry = hz + 250;
  c.fillStyle = C.tDark; c.fillRect(0, ry + 60, W, H + SPL.pad - ry); c.fillStyle = tone(c, .45, 7); c.fillRect(0, ry + 60, W, H + SPL.pad - ry);
  brush(c, [[0, ry + 60], [W, ry + 52]], 5, { taper: false });
  brush(c, [[0, ry - 40], [W, ry - 60]], 12, { taper: false }); brush(c, [[0, ry + 10], [W, ry - 6]], 4, { taper: false });
  for (let x = 20; x < W; x += 90) brush(c, [[x, ry - 40 - x * .018], [x, ry + 58 - x * .008]], 5, { taper: false });
  soraBackStanding(c, 650, ry + 360, 380, still ? 0 : f);
  c.restore();
}

/* ======================= SCENE 5 — INVITATION ======================= */
function scene5a(c, f) {
  c.fillStyle = C.deep; c.fillRect(0, 0, W, H); c.fillStyle = tone(c, .5, 7); c.fillRect(0, 0, W, H);
  hatch(c, null, 0, 0, W, H, 1.57, 18, 1.2, { color: C.ink, alpha: .4, seed: 12, len: .6 });
  const dx = 250, dy = 300, dw = 580, dh = 1280;
  const open = easeOut(prog(f, 276, 293));
  // interior light behind door
  c.fillStyle = '#EAD9BC'; c.fillRect(dx, dy, dw, dh); glow(c, dx + dw / 2, dy + dh * .5, 700, 'rgba(232,184,120,1)', .9, 'multiply');
  // light wedge on the floor toward camera
  const ww = lerp(0, 1, open);
  c.save(); c.globalCompositeOperation = 'screen'; c.globalAlpha = .85 * ww; const g = c.createLinearGradient(0, dy + dh, 0, H); g.addColorStop(0, 'rgba(232,184,120,1)'); g.addColorStop(1, 'rgba(215,154,74,.15)'); c.fillStyle = g;
  c.beginPath(); c.moveTo(dx + dw, dy + dh); c.lineTo(dx + dw - dw * ww, dy + dh); c.lineTo(dx + dw - dw * ww * 1.7 - 100, H); c.lineTo(dx + dw + 200, H); c.fill(); c.restore();
  // floorboards
  for (let i = 0; i < 8; i++) brush(c, [[dx + dw / 2 + (i - 4) * 70, dy + dh], [W / 2 + (i - 4) * 260, H]], 2, { taper: false, alpha: .5 });
  // door leaf (hinge right), rotating inward: projected width shrinks
  const leafW = dw * (1 - open * .62), lx = dx + dw - leafW, skew = open * 60;
  const leaf = [[lx, dy + skew], [dx + dw, dy], [dx + dw, dy + dh], [lx, dy + dh - skew]];
  fillShape(c, leaf.map(p => [p[0], p[1]]), C.tMid);
  c.save(); c.beginPath(); c.moveTo(...leaf[0]); for (const p of leaf.slice(1)) c.lineTo(...p); c.closePath(); c.clip();
  c.fillStyle = tone(c, .3, 6); c.fillRect(dx, dy, dw, dh);
  for (let i = 1; i < 5; i++) { const x = lerp(lx, dx + dw, i / 5); brush(c, [[x, dy + skew * (1 - i / 5)], [x, dy + dh - skew * (1 - i / 5)]], 2.2, { taper: false, alpha: .7 }); }
  hatch(c, null, dx, dy, dw, dh, 1.57, 9, 1, { alpha: .35, seed: 2, len: .3 });
  c.restore();
  c.beginPath(); c.moveTo(...leaf[0]); for (const p of leaf.slice(1)) c.lineTo(...p); c.closePath(); c.lineWidth = 5; c.strokeStyle = C.ink; c.stroke();
  // brass handle + bell
  const hx = lerp(lx + 50, lx + 18, open); c.fillStyle = C.amber; c.beginPath(); c.roundRect(hx - 10, dy + dh * .5 - 50, 20, 100, 8); c.fill(); brush(c, [[hx - 10, dy + dh * .5 - 50], [hx - 10, dy + dh * .5 + 50]], 2.5, { taper: false });
  const sw = Math.sin(f * .9) * .3 * open; c.save(); c.translate(dx + dw - 70, dy + 20); c.rotate(sw); brush(c, [[0, 0], [0, 40]], 2, { taper: false }); c.fillStyle = C.amber; c.beginPath(); c.moveTo(-18, 70); c.quadraticCurveTo(0, 20, 18, 70); c.fill(); c.restore();
  inkRect(c, dx - 20, dy - 20, dw + 40, dh + 20, 10, 50);
}
function pourPanel(c, w, h, f) {
  c.fillStyle = '#E9E2D4'; c.fillRect(0, 0, w, h); gradTone(c, 0, 0, w, h, (u, v) => .25 - u * .2, 7);
  glow(c, 0, 0, 700, 'rgba(232,184,120,1)', .45, 'multiply');
  c.fillStyle = C.wood; c.globalAlpha = .55; c.fillRect(0, 470, w, h); c.globalAlpha = 1; hatch(c, () => { c.beginPath(); c.rect(0, 470, w, 200); }, 0, 470, w, 200, 0, 12, 1.2, { alpha: .5, seed: 5, len: .5 });
  brush(c, [[0, 472], [w, 470]], 4, { taper: false });
  // server + dripper
  const sx = 620;
  fillShape(c, [[sx - 90, 300], [sx + 90, 300], [sx + 110, 470], [sx - 110, 470]], 'rgba(220,214,204,.7)'); brush(c, [[sx - 90, 300], [sx - 110, 470], [sx + 110, 470], [sx + 90, 300]], 3.5);
  c.fillStyle = C.coffee; c.beginPath(); c.moveTo(sx - 104, 410); c.lineTo(sx + 104, 410); c.lineTo(sx + 110, 470); c.lineTo(sx - 110, 470); c.fill();
  fillShape(c, [[sx - 140, 160], [sx + 140, 160], [sx + 50, 300], [sx - 50, 300]], '#F1EEE7'); brush(c, [[sx - 140, 160], [sx - 50, 300], [sx + 50, 300], [sx + 140, 160], [sx - 140, 160]], 4, { taper: false });
  for (let i = 1; i < 5; i++) brush(c, [[sx - 140 + i * 56, 164], [sx - 50 + i * 20, 296]], 1.4, { taper: false, alpha: .5 });
  // gooseneck kettle: body, lid, handle, long spout curving to the dripper
  c.save(); c.translate(250, 150);
  path(c, [[-150, 60], [-140, -40], [-60, -80], [60, -80], [140, -40], [150, 60], [110, 100], [-110, 100]]); c.fillStyle = '#5a5855'; c.fill(); c.fillStyle = tone(c, .4, 5); c.fill();
  brush(c, [[-150, 60], [-140, -40], [-60, -80], [60, -80], [140, -40], [150, 60], [110, 100], [-110, 100], [-150, 60]], 4.5, { taper: false });
  brush(c, [[-100, -40], [-40, -66], [40, -66]], 6, { color: C.paper, alpha: .5 });
  fillShape(c, [[-50, -80], [50, -80], [30, -104], [-30, -104]], C.deep); c.fillStyle = C.ink; c.beginPath(); c.arc(0, -112, 12, 0, 7); c.fill();
  brush(c, [[-140, -30], [-230, -60], [-240, 40], [-150, 60]], 16, { taper: false });
  brush(c, [[130, 70], [230, 40], [290, -40], [330, -60], [356, -40]], 14, { taper: 'end', color: C.ink });
  c.restore();
  const wv = Math.sin(f * .8) * 2; brush(c, [[604, 112], [608 + wv, 200], [614, 280]], 6, { taper: 'start', color: '#B9B2A6' });
  for (let k = 0; k < 2; k++) { const pts = []; for (let i = 0; i < 7; i++) pts.push([sx - 40 + k * 70 + Math.sin(f * .15 + i + k) * (6 + i * 4), 150 - i * 22, 1 - i / 8]); brush(c, pts, 5, { color: C.paper, alpha: .5 }); }
  // barista hand on the kettle handle, rolled linen sleeve
  c.save(); c.translate(0, 120); fillShape(c, [[-20, -40], [80, -60], [110, 60], [-10, 90]], '#E8E3D8'); hatch(c, () => path(c, [[-20, -40], [80, -60], [110, 60], [-10, 90]]), -20, -60, 140, 160, .8, 10, 1.2, { alpha: .5 }); brush(c, [[-20, -40], [80, -60], [110, 60], [-10, 90], [-20, -40]], 3, { taper: false });
  fillShape(c, [[80, -50], [130, -70], [150, -10], [110, 40]], '#EEE8DE'); brush(c, [[80, -50], [130, -70], [150, -10], [110, 40], [80, -50]], 3, { taper: false }); c.restore();
}
function aoiPanel(c, w, h, f) {
  c.fillStyle = '#E7DFD0'; c.fillRect(0, 0, w, h); gradTone(c, 0, 0, w, h, (u, v) => .15 + u * .25, 8);
  // window light (left)
  c.fillStyle = '#F6EEDD'; c.fillRect(30, 40, 280, 560); inkRect(c, 30, 40, 280, 560, 4, 8); brush(c, [[170, 40], [170, 600]], 4, { taper: false });
  glow(c, 170, 300, 600, 'rgba(232,184,120,1)', .55, 'multiply'); glow(c, 170, 300, 500, 'rgba(255,240,215,1)', .35);
  // plant on the sill
  c.save(); c.translate(250, 600); fillShape(c, [[-40, 0], [40, 0], [30, 70], [-30, 70]], C.tMid); brush(c, [[-40, 0], [40, 0], [30, 70], [-30, 70], [-40, 0]], 3, { taper: false });
  for (let i = 0; i < 7; i++) { const a = -2.6 + i * .35; const ex = Math.cos(a) * 110, ey = Math.sin(a) * 110; fillShape(c, [[0, 0], [ex * .5 - 14, ey * .5], [ex, ey], [ex * .5 + 14, ey * .5]], i % 2 ? C.ink : C.tDark); }
  c.restore();
  // Ren in background (soft focus): seated, reading, tie loosened
  c.save(); c.filter = 'blur(1.6px)'; c.translate(820, 420);
  fillShape(c, [[-90, 60], [90, 60], [120, 330], [-120, 330]], '#E2DDD3'); fillShape(c, [[-140, 60], [-90, 50], [-120, 330], [-170, 330]], C.deep); fillShape(c, [[140, 60], [90, 50], [120, 330], [170, 330]], C.deep); brush(c, [[-90, 60], [-120, 330]], 4); brush(c, [[90, 60], [120, 330]], 4);
  fillShape(c, [[-14, 60], [14, 60], [20, 170], [-6, 180]], C.deep);
  fillShape(c, [[-46, -40], [-40, -90], [0, -110], [40, -90], [46, -40], [30, 30], [-30, 30]], '#D9D3C8'); c.save(); c.globalAlpha=.5; c.fillStyle = tone(c, .3, 5); c.fillRect(-50, -110, 40, 150); c.restore(); fillShape(c, [[-50, -46], [-44, -100], [0, -118], [44, -98], [50, -50], [20, -80], [-30, -76]], C.ink);
  brush(c, [[-20, -30], [-6, -30]], 3); brush(c, [[10, -30], [24, -30]], 3);
  const turn = prog(f, 306, 312); c.fillStyle = C.paper; c.fillRect(-90, 140, 180, 120); brush(c, [[0, 140], [0, 260]], 3, { taper: false }); inkRect(c, -90, 140, 180, 120, 3, 4);
  if (turn > 0 && turn < 1) { c.fillStyle = '#FBF8F1'; c.beginPath(); c.moveTo(0, 140); c.lineTo(90 * Math.cos(turn * Math.PI), 130); c.lineTo(90 * Math.cos(turn * Math.PI), 250); c.lineTo(0, 260); c.fill(); }
  c.restore();
  // table
  c.fillStyle = C.wood; c.globalAlpha = .7; c.beginPath(); c.ellipse(500, 1180, 560, 150, 0, 0, 7); c.fill(); c.globalAlpha = 1;
  c.save(); c.beginPath(); c.ellipse(500, 1180, 560, 150, 0, 0, 7); c.clip(); hatch(c, null, 0, 1000, w, 360, .05, 14, 1.2, { alpha: .45, seed: 3, len: .5 }); c.restore();
  brush(c, spline([[-60, 1180], [100, 1060], [500, 1030], [900, 1060], [1060, 1180]], false, 8), 4, { raw: true, taper: false });
  // Aoi
  const up = ease(prog(f, 299, 310));
  drawBust(c, { x: 480, y: 640, s: .62, coat: '#DCD3C2', shirtFill: C.paper });
  c.save(); c.translate(480, 640); c.scale(.62, .62); // cardigan knit texture
  c.save(); path(c, [[-90, 380], [-300, 440], [-470, 560], [-520, 900], [520, 900], [480, 560], [300, 440], [100, 380], [0, 520]]); c.clip(); c.fillStyle = tone(c, .18, 5); c.fillRect(-520, 360, 1040, 560); for (let y = 420; y < 900; y += 26) brush(c, [[-520, y], [520, y + 6]], 1.4, { taper: false, alpha: .3 }); c.restore();
  c.restore();
  drawFace(c, { x: 480, y: 640 + (1 - up) * 18, s: .62, who: 'aoi', skin: '#F1EBE0', down: (1 - up) * .9, look: [-.15 * up, -.25 * up], rot: (1 - up) * .06 });
  // journal + pen + cup
  const jr = [[300, 1120], [620, 1090], [660, 1210], [320, 1250]]; fillShape(c, jr, '#F6F2E9'); brush(c, [...jr, jr[0]], 3.5, { taper: false }); brush(c, [[460, 1105], [490, 1230]], 2.4, { taper: false });
  for (let i = 0; i < 4; i++) { const rr = rng(i + 40), pts = []; for (let x = 0; x < 110; x += 8) pts.push([330 + x + i * 4, 1140 + i * 22 + Math.sin(x * .3 + i) * 3 + (rr() - .5) * 2]); brush(c, pts, 2, { raw: true, alpha: .7, min: .5 }); }
  fillShape(c, [[720, 1080], [800, 1080], [794, 1160], [726, 1160]], '#EDE6DA'); brush(c, [[720, 1080], [726, 1160], [794, 1160], [800, 1080]], 3.5); c.fillStyle = C.coffee; c.beginPath(); c.ellipse(760, 1084, 38, 9, 0, 0, 7); c.fill(); brush(c, [[720, 1080], [800, 1080]], 3, { taper: false });
  // hands on journal
  fillShape(c, [[420, 1060], [500, 1050], [520, 1110], [430, 1130]], '#F1EBE0'); brush(c, [[420, 1060], [500, 1050], [520, 1110], [430, 1130], [420, 1060]], 3);
  tint(c, C.amber, .12, 'soft-light');
}
function scene5b(c, f) {
  c.fillStyle = C.paper; c.fillRect(0, 0, W, H);
  panel(c, 36, 36, 1008, 604, (c, w, h) => pourPanel(c, w, h, f));
  panel(c, 36, 658, 1008, 1226, (c, w, h) => aoiPanel(c, w, h, f));
}
function chair(c, x, y, s) {
  c.save(); c.translate(x, y); c.scale(s, s);
  const wood = C.wood;
  const seat = [[-150, 0], [150, -30], [200, 50], [-110, 90]];
  const legs = [[[-140, 40], [-150, 380]], [[-100, 90], [-96, 440]], [[190, 60], [200, 420]], [[150, -10], [160, 330]]];
  for (const [a, b] of legs) { brush(c, [a, b], 20, { taper: false, color: wood }); brush(c, [[a[0] - 10, a[1]], [b[0] - 10, b[1]]], 3, { taper: false }); brush(c, [[a[0] + 10, a[1]], [b[0] + 10, b[1]]], 3, { taper: false }); }
  brush(c, [[-145, 260], [195, 270]], 8, { taper: false, color: C.ink, alpha: .6 });
  // back (spindles) behind seat
  const bt = [[-150, -360], [150, -390]];
  for (let i = 0; i <= 4; i++) { const t = i / 4; const xa = lerp(-150, 150, t), ya = lerp(0, -30, t); brush(c, [[xa, ya], [xa, ya - 360]], i % 4 ? 10 : 20, { taper: false, color: wood }); brush(c, [[xa + (i % 4 ? 5 : 10), ya], [xa + (i % 4 ? 5 : 10), ya - 360]], 2.5, { taper: false }); }
  brush(c, [[-170, -350], [0, -385], [170, -385]], 34, { taper: false, color: wood }); brush(c, [[-170, -368], [0, -403], [170, -403]], 3, { taper: false }); brush(c, [[-170, -334], [0, -369], [170, -369]], 3, { taper: false });
  fillShape(c, seat, wood); c.save(); path(c, seat); c.clip(); hatch(c, null, -160, -40, 380, 140, .1, 10, 1.2, { alpha: .45, seed: 9, len: .5 }); c.restore();
  brush(c, [...seat, seat[0]], 4, { taper: false });
  fillShape(c, [[-110, 90], [200, 50], [200, 70], [-110, 112]], C.ink);
  c.restore();
}
function scene5c(c, f) {
  // back wall
  c.fillStyle = '#D8CFBF'; c.fillRect(0, 0, W, H); gradTone(c, 0, 0, W, H, (u, v) => .2 + v * .25, 8);
  // window (evening, cool, monochrome)
  c.fillStyle = '#9DA3A6'; c.fillRect(640, 120, 370, 580); gradTone(c, 640, 120, 370, 580, (u, v) => .45 - v * .25, 7);
  for (let i = 0; i < 12; i++) { const r = rng(i + 5); c.fillStyle = 'rgba(244,241,234,.6)'; c.beginPath(); c.arc(660 + r() * 330, 420 + r() * 260, 3 + r() * 8, 0, 7); c.fill(); }
  brush(c, [[825, 120], [825, 700]], 10, { taper: false, color: C.wood }); brush(c, [[640, 410], [1010, 410]], 10, { taper: false, color: C.wood }); inkRect(c, 640, 120, 370, 580, 10, 3);
  // shelf with books (left)
  c.save(); c.translate(40, 760);
  brush(c, [[0, 160], [300, 160]], 14, { taper: false, color: C.wood }); brush(c, [[0, 168], [300, 168]], 3, { taper: false });
  for (const b of G.books) { if (b.x + b.w > 290) continue; c.fillStyle = b.t < .3 ? C.deep : b.t < .65 ? C.tMid : C.cream; c.fillRect(b.x, 160 - b.h, b.w, b.h); brush(c, [[b.x, 160 - b.h], [b.x + b.w, 160 - b.h], [b.x + b.w, 160]], 1.8, { taper: false }); }
  c.restore();
  // plant on sill
  c.save(); c.translate(700, 700); fillShape(c, [[-36, 0], [36, 0], [28, 60], [-28, 60]], C.tMid); for (let i = 0; i < 6; i++) { const a = -2.5 + i * .35; fillShape(c, [[0, 0], [Math.cos(a) * 50 - 10, Math.sin(a) * 50], [Math.cos(a) * 100, Math.sin(a) * 100], [Math.cos(a) * 50 + 10, Math.sin(a) * 50]], i % 2 ? C.ink : C.tDark); } c.restore();
  // floor
  c.fillStyle = '#6E5847'; c.fillRect(0, 1140, W, H); c.fillStyle = tone(c, .4, 7); c.fillRect(0, 1140, W, H);
  for (let i = 0; i < 12; i++) brush(c, [[i * 110 - 200, H], [400 + i * 40, 1140]], 2, { taper: false, alpha: .5 });
  brush(c, [[0, 1140], [W, 1140]], 5, { taper: false });
  // lamp (warm amber)
  const breathe = 1 + .03 * Math.sin(f * .35);
  c.save(); c.translate(960, 900); brush(c, [[0, 0], [0, 130]], 6, { taper: false }); fillShape(c, [[-70, 0], [70, 0], [40, -90], [-40, -90]], C.amber); brush(c, [[-70, 0], [70, 0], [40, -90], [-40, -90], [-70, 0]], 3.5, { taper: false }); c.restore();
  glow(c, 960, 880, 560 * breathe, 'rgba(232,184,120,1)', .7, 'multiply'); glow(c, 960, 870, 380 * breathe, 'rgba(255,226,170,1)', .55);
  // table
  c.save(); c.translate(720, 1090);
  fillShape(c, [[-300, 0], [300, -40], [360, 60], [-240, 110]], C.wood); hatch(c, () => path(c, [[-300, 0], [300, -40], [360, 60], [-240, 110]]), -300, -40, 660, 160, .05, 12, 1.2, { alpha: .45, seed: 4, len: .5 }); brush(c, [[-300, 0], [300, -40], [360, 60], [-240, 110], [-300, 0]], 4, { taper: false });
  brush(c, [[-220, 110], [-210, 420]], 16, { taper: false, color: C.ink }); brush(c, [[330, 70], [340, 360]], 16, { taper: false, color: C.ink });
  // cups
  for (const [cx, cy, sc] of [[-120, -10, 1], [140, -40, .85]]) { c.save(); c.translate(cx, cy); c.scale(sc, sc); fillShape(c, [[-40, -70], [40, -70], [34, 0], [-34, 0]], '#EFE9DE'); brush(c, [[-40, -70], [-34, 0], [34, 0], [40, -70]], 3.5); c.fillStyle = C.coffee; c.beginPath(); c.ellipse(0, -68, 38, 9, 0, 0, 7); c.fill(); c.lineWidth = 3; c.strokeStyle = C.ink; c.beginPath(); c.ellipse(0, -70, 40, 10, 0, 0, 7); c.stroke(); c.restore(); }
  for (let k = 0; k < 2; k++) { const pts = []; for (let i = 0; i < 8; i++) pts.push([-120 + k * 24 + Math.sin(f * .14 + i * .8 + k * 2) * (5 + i * 4), -90 - i * 26, 1 - i / 9]); brush(c, pts, 5, { color: C.paper, alpha: .55 }); }
  c.restore();
  // the empty chair, pulled out toward the viewer
  chair(c, 640, 1420, 1.0);
  // warm wash on wood elements
  tint(c, C.amber, .1, 'soft-light');
  // Sora at the entrance — foreground left, cropped, out of focus, still monochrome
  c.save(); c.filter = 'blur(7px)';
  c.fillStyle = C.tMid; path(c, [[-120, 900], [60, 820], [240, 900], [330, 1200], [360, 1920], [-120, 1920]]); c.fill();
  c.fillStyle = tone(c, .4, 7); c.fill();
  fillShape(c, [[20, 820], [10, 700], [70, 620], [170, 620], [220, 700], [210, 820], [120, 860]], C.ink);
  c.restore();
}

/* ======================= TEXT TRACK ======================= */
function textTrack(c, f) {
  // T1 — 0.15 s / 0.60 s → 2.35 s
  if (f < 60) {
    const box = textAlpha(f, 4, 56);
    narration(c, ['毎日、', 'ちゃんと生きている。'], 500, 1140, 60, box, { stages: [{ a: 1, dy: 0, blur: 0 }, textAlpha(f, 14)] });
  }
  // T2 — 2.70 s / 3.20 s → 4.85 s
  if (f >= 60 && f < 120) {
    const box = textAlpha(f, 65, 116);
    narration(c, ['やるべきことも、', 'やっている。'], 520, 470, 60, box, { stages: [{ a: 1, dy: 0, blur: 0 }, textAlpha(f, 77)] });
  }
  // T3 — vertical, 5.30 s → 7.20 s
  if (f >= 120 && f < 180) {
    const a = textAlpha(f, 127, 173), b = textAlpha(f, 133, 173);
    vText(c, 'それなのに、', 800, 330, 64, { color: C.cream, st: a });
    vText(c, '時々思う。', 690, 330, 64, { color: C.cream, st: b });
  }
  // T4 — 8.00 s / 8.50 s → 11.30 s
  if (f >= 180 && f < 276) {
    const a = textAlpha(f, 192, 271), b = textAlpha(f, 204, 271);
    hText(c, '人生は、本当に', 540, 720, 76, { align: 'center', weight: 600, track: .14, color: C.cream, st: a, shadow: true });
    hText(c, 'これだけだろうか。', 540, 850, 76, { align: 'center', weight: 600, track: .14, color: C.cream, st: b, shadow: true });
  }
  // T5 — 12.40 s → end
  if (f >= 298) {
    const a = textAlpha(f, 298);
    narration(c, ['あなたは、', 'どう思いますか？'], 540, 420, 64, a, { minW: 640 });
  }
  // wordmark — 13.75 s → end
  if (f >= 330) {
    const a = easeOut(prog(f, 330, 342));
    c.save(); c.globalAlpha = a;
    const wx = 540 + 8, wy = 830, ww = measure(c, 'ゆとりば', 58, { track: .3 });
    hText(c, 'ゆとりば', wx, wy, 58, { align: 'center', weight: 500, track: .3, color: '#141414' });
    // single amber steam curve above と
    const sx = wx - ww / 2 + 58 * 1.3 * 1.5 - 4;
    brush(c, [[sx - 4, wy - 66], [sx + 6, wy - 80], [sx - 2, wy - 94], [sx + 8, wy - 108]], 4.5, { color: C.amber });
    c.restore();
  }
}

/* ======================= DISPATCH ======================= */
function drawScene(c, f) {
  if (f < 60) scene1(c, f);
  else if (f < 120) scene2(c, f);
  else if (f < 150) scene3a(c, f);
  else if (f < 180) scene3b(c, f);
  else if (f < 276) splash(c, f);
  else if (f < 294) scene5a(c, f);
  else if (f < 318) scene5b(c, f);
  else scene5c(c, f);
}
const BUF = {};
function renderFrame(f) {
  const c = ctx;
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none';
  drawScene(c, f);
  // page turn 1B → 2A (f56–61): blank page curls in from the right
  if (f >= 55 && f < 62) {
    const p = ease(prog(f, 55, 61.5)), x = W * (1 - p);
    if (f >= 60) { scene1Buf(f); c.drawImage(BUF.a, 0, 0); }
    c.save(); c.beginPath(); c.moveTo(x, 0); c.quadraticCurveTo(x - 60 * (1 - p), H / 2, x, H); c.lineTo(W, H); c.lineTo(W, 0); c.closePath(); c.clip(); scene2(c, Math.max(f, 60)); c.restore();
    const g = c.createLinearGradient(x - 70, 0, x, 0); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(0,0,0,.35)'); c.fillStyle = g; c.fillRect(x - 70, 0, 70, H);
  }
  // ink bleed → paper (f180–185)
  if (f >= 180 && f < 186) { c.save(); c.globalAlpha = 1 - prog(f, 179, 186); c.fillStyle = C.paper; c.fillRect(0, 0, W, H); c.restore(); }
  // light seam 4A → 5A (f270–281): splash outside, café door inside a widening warm seam
  if (f >= 270 && f < 282) {
    const p = ease(prog(f, 270, 282)), hw = W / 2 * p;
    BUF.b = BUF.b || mk(W, H); const b = BUF.b.getContext('2d'); b.setTransform(1, 0, 0, 1, 0, 0); b.globalAlpha = 1; splash(b, Math.min(f, 275));
    BUF.c = BUF.c || mk(W, H); const d = BUF.c.getContext('2d'); d.setTransform(1, 0, 0, 1, 0, 0); d.globalAlpha = 1; scene5a(d, Math.max(f, 276));
    c.drawImage(BUF.b, 0, 0);
    c.save(); c.beginPath(); c.rect(W / 2 - hw, 0, hw * 2, H); c.clip(); c.drawImage(BUF.c, 0, 0); c.restore();
    glow(c, W / 2 - hw, H / 2, 240, 'rgba(232,184,120,1)', .7); glow(c, W / 2 + hw, H / 2, 240, 'rgba(232,184,120,1)', .7);
    c.fillStyle = C.glow; c.fillRect(W / 2 - hw - 2, 0, 4, H); c.fillRect(W / 2 + hw - 2, 0, 4, H);
  }
  // soft dissolve 5B → 5C (f314–321)
  if (f >= 314 && f < 322) {
    BUF.b = BUF.b || mk(W, H); const b = BUF.b.getContext('2d'); b.setTransform(1, 0, 0, 1, 0, 0);
    if (f < 318) { scene5c(b, 318); c.save(); c.globalAlpha = prog(f, 313, 321); c.drawImage(BUF.b, 0, 0); c.restore(); }
    else { scene5b(b, 317); c.save(); c.globalAlpha = 1 - prog(f, 313, 321); c.drawImage(BUF.b, 0, 0); c.restore(); }
  }
  post(c, f, { paper: f >= 120 && f < 180 ? .25 : .55 });
  textTrack(c, f);
}
function scene1Buf(f) { BUF.a = BUF.a || mk(W, H); const b = BUF.a.getContext('2d'); b.setTransform(1, 0, 0, 1, 0, 0); scene1(b, Math.min(f, 59)); }
