// ゆとりば Reel 001 — drawing engine: ink, tone, paper, type.
'use strict';
const W = 1080, H = 1920, FPS = 24, TOTAL = 360;
const C = {
  ink: '#111111', deep: '#2A2927', tDark: '#4A4946', tMid: '#8C8A85', tLight: '#C9C6BF',
  paper: '#F4F1EA', cream: '#F2EBDD', blueGray: '#6F7C86', sky1: '#4F6A84', sky2: '#8FA3B5',
  gold: '#C9A15A', amber: '#D79A4A', glow: '#E8B878', coffee: '#6B4A32', wood: '#8A6646',
};
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const ease = t => (t = clamp(t), t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const easeOut = t => 1 - Math.pow(1 - clamp(t), 3);
const easeIn = t => Math.pow(clamp(t), 3);
const prog = (f, a, b) => clamp((f - a) / (b - a));
function rng(seed) {
  let a = seed | 0;
  return () => { a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

// Catmull-Rom spline through control points -> dense point list
function spline(ctrl, closed = false, per = 10) {
  const out = [], n = ctrl.length;
  const get = i => closed ? ctrl[(i + n) % n] : ctrl[clamp(i, 0, n - 1)];
  const segs = closed ? n : n - 1;
  for (let i = 0; i < segs; i++) {
    const p0 = get(i - 1), p1 = get(i), p2 = get(i + 1), p3 = get(i + 2);
    for (let k = 0; k < per; k++) {
      const t = k / per, t2 = t * t, t3 = t2 * t;
      const f = (a, b, c, d) => .5 * ((2 * b) + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
      out.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1]), p1[2] !== undefined ? lerp(p1[2], p2[2] ?? p1[2], t) : 1]);
    }
  }
  if (!closed) out.push([...ctrl[n - 1].slice(0, 2), ctrl[n - 1][2] ?? 1]);
  return out;
}
function wob(pts, amt, seed) { const r = rng(seed); return pts.map(p => [p[0] + (r() - .5) * amt, p[1] + (r() - .5) * amt, p[2]]); }
function path(c, ctrl, closed = true, per = 10) {
  if (ctrl.length <= 4 && closed) { c.beginPath(); c.moveTo(ctrl[0][0], ctrl[0][1]); for (const q of ctrl.slice(1)) c.lineTo(q[0], q[1]); c.closePath(); return; }
  const p = spline(ctrl, closed, per); c.beginPath(); c.moveTo(p[0][0], p[0][1]);
  for (let i = 1; i < p.length; i++) c.lineTo(p[i][0], p[i][1]);
  if (closed) c.closePath();
}
function fillShape(c, ctrl, style, closed = true) { path(c, ctrl, closed); c.fillStyle = style; c.fill(); }

// Tapered brush stroke (filled polygon). pts can carry a 3rd value = width multiplier.
function brush(c, ctrl, w, o = {}) {
  const pts = o.raw ? ctrl : spline(ctrl, false, o.per || 8);
  const n = pts.length; if (n < 2) return;
  let upto = o.trim === undefined ? n : Math.max(2, Math.floor(n * clamp(o.trim)));
  if (o.trim !== undefined && o.trim <= 0) return;
  const L = [], R = [];
  for (let i = 0; i < upto; i++) {
    const p = pts[i], a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
    let dx = b[0] - a[0], dy = b[1] - a[1]; const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d;
    const u = i / (n - 1);
    const tp = o.taper === false ? 1 : o.taper === 'end' ? Math.max(.2, 1 - u * .85) : o.taper === 'start' ? Math.max(.2, .15 + u * .85) : Math.max(o.min ?? .18, Math.pow(Math.sin(Math.PI * u), .6));
    const ww = w * tp * (p[2] ?? 1) / 2;
    L.push([p[0] - dy * ww, p[1] + dx * ww]); R.push([p[0] + dy * ww, p[1] - dx * ww]);
  }
  c.save(); if (o.alpha !== undefined) c.globalAlpha *= o.alpha;
  c.fillStyle = o.color || C.ink; c.beginPath(); c.moveTo(L[0][0], L[0][1]);
  for (let i = 1; i < L.length; i++) c.lineTo(L[i][0], L[i][1]);
  for (let i = R.length - 1; i >= 0; i--) c.lineTo(R[i][0], R[i][1]);
  c.closePath(); c.fill(); c.restore();
}
function line(c, x1, y1, x2, y2, w, o = {}) {
  const r = rng(o.seed || (x1 * 7 + y1 * 13 + x2 * 17 + y2) | 0), wo = o.wob ?? 1.2;
  const mid = [];
  const n = o.n || 4;
  for (let i = 0; i <= n; i++) { const t = i / n; mid.push([lerp(x1, x2, t) + (i && i < n ? (r() - .5) * wo : 0), lerp(y1, y2, t) + (i && i < n ? (r() - .5) * wo : 0)]); }
  brush(c, mid, w, { taper: o.taper ?? false, color: o.color, alpha: o.alpha, min: .5, trim: o.trim });
}

// Screentone: dot patterns (cached), density = ink coverage 0..1
const patCache = {};
function tone(c, density, s = 7, fg = C.ink, bg = null) {
  const key = [density.toFixed(3), s, fg, bg].join('|');
  if (!patCache[key]) {
    const pc = mk(s * 2, s * 2), x = pc.getContext('2d');
    if (bg) { x.fillStyle = bg; x.fillRect(0, 0, s * 2, s * 2); }
    const r = s * Math.sqrt(2 * clamp(density, 0, .78) / Math.PI);
    x.fillStyle = fg;
    for (const [cx, cy] of [[s / 2, s / 2], [s * 1.5, s * 1.5]]) { x.beginPath(); x.arc(cx, cy, r, 0, 7); x.fill(); }
    patCache[key] = pc;
  }
  return c.createPattern(patCache[key], 'repeat');
}
// gradient dot tone into rect; fn(u,v)->density
function gradTone(c, x, y, w, h, fn, s = 8, fg = C.ink) {
  c.fillStyle = fg;
  for (let j = 0, row = 0; j < h + s; j += s * .5, row++) {
    for (let i = (row % 2) * s * .5; i < w + s; i += s) {
      const d = fn(i / w, j / h); if (d <= .005) continue;
      const r = s * Math.sqrt(clamp(d, 0, .8) / Math.PI) * .72;
      c.beginPath(); c.arc(x + i, y + j, r, 0, 7); c.fill();
    }
  }
}
function hatch(c, clipFn, x, y, w, h, ang, gap, lw, o = {}) {
  c.save(); if (clipFn) { clipFn(); c.clip(); }
  const r = rng(o.seed || 7); c.translate(x + w / 2, y + h / 2); c.rotate(ang);
  const R = Math.hypot(w, h) / 2 + 10;
  for (let t = -R; t < R; t += gap) {
    const j = (r() - .5) * gap * .4, len = o.len ? R * o.len : R;
    const s0 = o.len ? (r() * 2 - 1) * R * .6 : -R;
    brush(c, [[s0, t + j], [s0 + len * 2, t + j + (r() - .5) * 3]], lw * (.7 + r() * .6), { color: o.color, alpha: o.alpha, taper: o.taper ?? true, min: .3 });
  }
  c.restore();
}
// Hand-inked rectangle border
function inkRect(c, x, y, w, h, lw = 5, seed = 1, color = C.ink) {
  line(c, x, y, x + w, y, lw, { seed, wob: 2, color }); line(c, x + w, y, x + w, y + h, lw, { seed: seed + 1, wob: 2, color });
  line(c, x + w, y + h, x, y + h, lw, { seed: seed + 2, wob: 2, color }); line(c, x, y + h, x, y, lw, { seed: seed + 3, wob: 2, color });
}
function panel(c, x, y, w, h, draw, o = {}) {
  c.save(); c.beginPath(); c.rect(x, y, w, h); c.clip(); c.translate(x, y); draw(c, w, h); c.restore();
  if (o.border !== false) inkRect(c, x, y, w, h, o.lw || 5, o.seed || (x + y) | 0, o.borderColor);
}
function glow(c, x, y, r, color, a = 1, mode = 'screen') {
  c.save(); c.globalCompositeOperation = mode; c.globalAlpha = a;
  const g = c.createRadialGradient(x, y, 0, x, y, r); g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
  c.fillStyle = g; c.fillRect(x - r, y - r, r * 2, r * 2); c.restore();
}

// ---------- paper + grain (precomputed)
let PAPER, GRAIN = [];
function initTextures() {
  PAPER = mk(W, H); const p = PAPER.getContext('2d'); const r = rng(42);
  p.fillStyle = '#fff'; p.fillRect(0, 0, W, H);
  const id = p.getImageData(0, 0, W, H), d = id.data;
  for (let i = 0; i < d.length; i += 4) { const v = 255 - Math.floor(r() * r() * 34); d[i] = v; d[i + 1] = v - 2; d[i + 2] = v - 6; }
  p.putImageData(id, 0, 0);
  p.globalAlpha = .07; p.strokeStyle = '#6d6250';
  for (let i = 0; i < 900; i++) { const x = r() * W, y = r() * H, a = r() * 6.28, l = 6 + r() * 26; p.lineWidth = .6 + r(); p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + Math.cos(a) * l * .5 + (r() - .5) * 8, y + Math.sin(a) * l * .5, x + Math.cos(a) * l, y + Math.sin(a) * l); p.stroke(); }
  for (let k = 0; k < 4; k++) {
    const g = mk(W / 2, H / 2), x = g.getContext('2d'), gd = x.createImageData(W / 2, H / 2), rr = rng(100 + k);
    for (let i = 0; i < gd.data.length; i += 4) { const v = rr() * 255; gd.data[i] = gd.data[i + 1] = gd.data[i + 2] = v; gd.data[i + 3] = 255; }
    x.putImageData(gd, 0, 0); GRAIN.push(g);
  }
}
function post(c, f, o = {}) {
  c.save();
  c.globalCompositeOperation = 'multiply'; c.globalAlpha = o.paper ?? .55; c.drawImage(PAPER, 0, 0);
  c.globalCompositeOperation = 'overlay'; c.globalAlpha = .07; c.drawImage(GRAIN[Math.floor(f / 2) % 4], 0, 0, W, H);
  c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
  const g = c.createRadialGradient(W / 2, H / 2, H * .35, W / 2, H / 2, H * .75);
  g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, 'rgba(10,8,6,0.16)'); c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.restore();
}
// color layer helper: tint whole canvas region with blend
function tint(c, color, a, mode = 'color', clipFn) {
  c.save(); if (clipFn) { clipFn(); c.clip(); } c.globalCompositeOperation = mode; c.globalAlpha = a; c.fillStyle = color; c.fillRect(0, 0, W, H); c.restore();
}

// ---------- typography
const FONT = '"Shippori Mincho B1"';
function textAlpha(f, inF, outF) { // 8-frame in, 6-frame out
  const a = prog(f, inF, inF + 8), b = outF === undefined ? 1 : 1 - prog(f, outF - 6, outF);
  return { a: easeOut(a) * b, dy: (1 - easeOut(a)) * 8, blur: (1 - a) * 3 };
}
function hText(c, str, x, y, size, o = {}) { // centered unless o.align
  c.save(); c.font = `${o.weight || 500} ${size}px ${FONT}`; c.letterSpacing = `${(o.track ?? .14) * size}px`;
  c.textAlign = o.align || 'left'; c.textBaseline = 'alphabetic'; c.fillStyle = o.color || C.ink;
  const st = o.st || { a: 1, dy: 0, blur: 0 }; c.globalAlpha *= st.a; if (st.blur > .2) c.filter = `blur(${st.blur}px)`;
  if (o.shadow) { c.shadowColor = 'rgba(17,17,17,.45)'; c.shadowBlur = 10; }
  c.fillText(str, x, y + st.dy); c.restore();
}
function measure(c, str, size, o = {}) { c.save(); c.font = `${o.weight || 500} ${size}px ${FONT}`; c.letterSpacing = `${(o.track ?? .14) * size}px`; const w = c.measureText(str).width - (o.track ?? .14) * size; c.restore(); return w; }
// vertical text column, top at y, x = column center
function vText(c, str, x, y, size, o = {}) {
  c.save(); c.font = `${o.weight || 500} ${size}px ${FONT}`; c.fillStyle = o.color || C.ink; c.textAlign = 'center'; c.textBaseline = 'middle';
  const st = o.st || { a: 1, dy: 0, blur: 0 }; c.globalAlpha *= st.a; if (st.blur > .2) c.filter = `blur(${st.blur}px)`;
  let yy = y + size / 2 + st.dy; const step = size * 1.12;
  for (const ch of str) {
    if ('、。'.includes(ch)) c.fillText(ch, x + size * .62, yy - size * .55);
    else c.fillText(ch, x, yy);
    yy += step;
  }
  c.restore();
}
// cream narration box with centered lines
function narration(c, lines, cx, top, size, st, o = {}) {
  if (st.a <= 0.001) return;
  const padX = 56, padY = 46, lh = size * 1.7;
  const wMax = Math.max(...lines.map(l => measure(c, l, size)));
  const bw = Math.max(o.minW || 0, wMax + padX * 2), bh = lines.length * lh + padY * 2 - (lh - size);
  const x = cx - bw / 2, y = top;
  c.save(); c.globalAlpha = st.a;
  c.fillStyle = C.cream; c.fillRect(x, y + st.dy, bw, bh);
  inkRect(c, x, y + st.dy, bw, bh, 2.6, 77);
  c.restore();
  lines.forEach((l, i) => {
    const lst = o.stages ? o.stages[i] : st;
    hText(c, l, x + padX, y + padY + size * .86 + i * lh, size, { st: { a: lst.a * st.a, dy: lst.dy + st.dy, blur: lst.blur }, color: C.ink });
  });
}
