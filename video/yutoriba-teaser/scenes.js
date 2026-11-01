// Yutoriba — 15s vertical teaser. Procedural canvas renderer.
// renderFrame(t) draws one frame (t in seconds, 0..15) onto #c.
'use strict';

const W = 1080, H = 1920, DUR = 15;
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

// ---------- palette ----------
const C = {
  cream: '#F4EADB', beige: '#E6D3B3', coffee: '#5A3E2B', coffeeDk: '#3A2A21',
  amber: '#E8A04C', gold: '#F2C46D', blue: '#7F9BB0', forest: '#4E6B4A',
  sakura: '#F2C6CF', ink: '#4A3426',
};

// ---------- helpers ----------
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
const ease = (t) => 0.5 - 0.5 * Math.cos(Math.PI * clamp(t));
function mk(w, h) { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; }

function makeLayer(lw, lh, k, fn, blur = 0) {
  const c = mk(Math.round(lw * k), Math.round(lh * k));
  const g = c.getContext('2d');
  g.scale(k, k);
  fn(g);
  if (blur > 0) {
    const b = mk(c.width, c.height);
    const bg = b.getContext('2d');
    bg.filter = `blur(${blur * k}px)`;
    bg.drawImage(c, 0, 0);
    return { c: b, lw, lh };
  }
  return { c, lw, lh };
}
// draw layer so that layer-point (cx,cy) lands on screen center, scaled by zoom
function drawLayer(g, L, cx, cy, zoom, alpha = 1) {
  g.save();
  g.globalAlpha *= alpha;
  g.translate(W / 2, H / 2); g.scale(zoom, zoom); g.translate(-cx, -cy);
  g.drawImage(L.c, 0, 0, L.lw, L.lh);
  g.restore();
}
function camApply(g, cx, cy, zoom) { g.translate(W / 2, H / 2); g.scale(zoom, zoom); g.translate(-cx, -cy); }
function camPoint(x, y, cx, cy, zoom) { return [W / 2 + (x - cx) * zoom, H / 2 + (y - cy) * zoom]; }

function makeProj(vx, vy, f, camH) {
  return (X, Y, z) => [vx + X * f / z, vy + (camH - Y) * f / z];
}
function poly(g, pts, fill) {
  g.beginPath(); g.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) g.lineTo(pts[i][0], pts[i][1]);
  g.closePath(); if (fill) { g.fillStyle = fill; g.fill(); }
}
function glow(g, x, y, r, color, a = 1, op = 'source-over') {
  g.save(); g.globalCompositeOperation = op; g.globalAlpha *= a;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, color); gr.addColorStop(1, 'rgba(0,0,0,0)');
  // use transparent version of same hue at edge
  g.fillStyle = gr; g.beginPath(); g.arc(x, y, r, 0, Math.PI * 2); g.fill(); g.restore();
}
function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}
function softGlow(g, x, y, r, hex, a, op = 'source-over') {
  g.save(); g.globalCompositeOperation = op;
  const gr = g.createRadialGradient(x, y, 0, x, y, r);
  gr.addColorStop(0, rgba(hex, a)); gr.addColorStop(0.35, rgba(hex, a * 0.45));
  gr.addColorStop(1, rgba(hex, 0));
  g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2); g.restore();
}
function vGrad(g, y0, y1, stops) {
  const gr = g.createLinearGradient(0, y0, 0, y1);
  stops.forEach(([o, c]) => gr.addColorStop(o, c)); return gr;
}
function cloud(g, x, y, w, h, color, a, R) {
  g.save(); g.globalAlpha = a; g.fillStyle = color;
  for (let i = 0; i < 9; i++) {
    const px = x + (R() - 0.5) * w, py = y + (R() - 0.5) * h * 0.5;
    const rx = w * (0.18 + R() * 0.2), ry = h * (0.3 + R() * 0.3);
    g.beginPath(); g.ellipse(px, py, rx, ry, 0, 0, Math.PI * 2); g.fill();
  }
  g.restore();
}

// =====================================================================
// SCENE 1 — empty station platform, golden hour
// =====================================================================
const S1 = { VP: [540, 1060], sun: [455, 985] };
function buildStation(g) {
  const R = rng(11);
  const P = makeProj(540, 1060, 620, 2.6);
  // sky
  g.fillStyle = vGrad(g, 0, 1070, [[0, '#8EA5B6'], [0.35, '#BFC3BF'], [0.62, '#E8D2AE'], [0.86, '#F7D99E'], [1, '#FCE6B8']]);
  g.fillRect(0, 0, W, 1075);
  // high thin clouds
  cloud(g, 250, 330, 520, 70, '#F3E1CB', 0.35, R);
  cloud(g, 820, 520, 420, 50, '#F6D7C2', 0.3, R);
  cloud(g, 180, 700, 360, 40, '#F8DDB4', 0.35, R);
  cloud(g, 760, 820, 300, 30, '#FBE2BC', 0.3, R);
  // sun
  softGlow(g, S1.sun[0], S1.sun[1], 640, '#FFE3A6', 0.55);
  softGlow(g, S1.sun[0], S1.sun[1], 180, '#FFF3D6', 0.9);
  g.fillStyle = '#FFF8EA'; g.beginPath(); g.arc(S1.sun[0], S1.sun[1], 34, 0, 7); g.fill();
  // distant mountains
  g.fillStyle = 'rgba(150,150,165,0.35)'; g.beginPath(); g.moveTo(0, 1062);
  for (let x = 0; x <= W; x += 20) g.lineTo(x, 1040 - 18 * Math.sin(x / 140) - 10 * Math.sin(x / 47 + 1));
  g.lineTo(W, 1062); g.fill();
  // distant town silhouettes
  for (let i = 0; i < 70; i++) {
    const x = R() * W, w = 8 + R() * 30, h = 6 + R() * 30;
    const d = Math.abs(x - S1.sun[0]) / 500;
    g.fillStyle = `rgba(${150 + 40 * (1 - clamp(d))},${120 + 30 * (1 - clamp(d))},${105},${0.45 + 0.25 * clamp(d)})`;
    g.fillRect(x, 1062 - h, w, h);
  }
  for (let i = 0; i < 40; i++) { // tree blobs
    const x = R() * W, r = 6 + R() * 14;
    g.fillStyle = `rgba(110,115,90,${0.35 + R() * 0.2})`;
    g.beginPath(); g.arc(x, 1060 - r * 0.6, r, 0, 7); g.fill();
  }
  // track bed
  poly(g, [P(-12, 0, 1.2), P(-1.4, 0, 1.2), P(-1.4, 0, 900), P(-12, 0, 900)],
    vGrad(g, 1060, 1920, [[0, '#C9A784'], [0.15, '#8E705A'], [1, '#5B4436']]));
  // gravel speckle
  for (let i = 0; i < 2600; i++) {
    const z = 1.3 + Math.pow(R(), 2.2) * 60, X = -12 + R() * 10.6;
    const [x, y] = P(X, 0, z); if (x < -10 || x > W + 10 || y > H) continue;
    const s = Math.max(0.6, 7 / z);
    g.fillStyle = R() < 0.5 ? 'rgba(60,42,32,0.35)' : 'rgba(230,200,160,0.25)';
    g.fillRect(x, y, s, s * 0.6);
  }
  // sleepers
  for (let z = 1.6; z < 90; z += 0.7) {
    const a = 0.75 * (1 - smooth(10, 90, z));
    poly(g, [P(-4.8, 0.06, z), P(-2.6, 0.06, z), P(-2.6, 0.06, z + 0.24), P(-4.8, 0.06, z + 0.24)], `rgba(58,40,30,${a})`);
  }
  // rails
  for (const rx of [-4.3, -3.2]) {
    poly(g, [P(rx, 0.17, 1.2), P(rx + 0.08, 0.17, 1.2), P(rx + 0.08, 0.17, 900), P(rx, 0.17, 900)],
      vGrad(g, 1060, 1920, [[0, '#FFF1CF'], [0.08, '#F3C977'], [0.5, '#A07A55'], [1, '#6B5040']]));
    poly(g, [P(rx + 0.08, 0.17, 1.2), P(rx + 0.08, 0.0, 1.2), P(rx + 0.08, 0, 900), P(rx + 0.08, 0.17, 900)], 'rgba(50,36,28,0.6)');
  }
  // catenary poles + wires (left)
  g.strokeStyle = 'rgba(60,45,40,0.85)';
  for (let z = 3; z < 160; z += 16) {
    const a = P(-7, 0, z), b = P(-7, 7.2, z), c = P(-3.2, 6.6, z);
    g.lineWidth = Math.max(0.8, 34 / z);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    g.lineWidth = Math.max(0.6, 18 / z);
    g.beginPath(); g.moveTo(b[0], b[1] + 6 / z * 40); g.lineTo(c[0], c[1]); g.stroke();
  }
  g.lineWidth = 1.6; g.strokeStyle = 'rgba(70,52,44,0.6)';
  for (const [X, Y] of [[-3.75, 6.2], [-3.75, 6.6]]) {
    const a = P(X, Y, 1.0), b = P(X, Y, 900);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
  }
  // platform side face
  poly(g, [P(-1.4, 0, 1.2), P(-1.4, 1, 1.2), P(-1.4, 1, 900), P(-1.4, 0, 900)], '#3E2C22');
  // platform top
  poly(g, [P(-1.4, 1, 1.0), P(9, 1, 1.0), P(9, 1, 900), P(-1.4, 1, 900)],
    vGrad(g, 1060, 1920, [[0, '#FBE3B4'], [0.08, '#EBD2A8'], [0.4, '#D6BE9C'], [1, '#B79F84']]));
  // platform tile seams
  g.strokeStyle = 'rgba(120,95,75,0.18)'; g.lineWidth = 1;
  for (let z = 1.5; z < 80; z *= 1.12) {
    const a = P(-1.4, 1, z), b = P(9, 1, z);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
  }
  // edge line + tactile strip
  poly(g, [P(-1.4, 1, 1.0), P(-1.22, 1, 1.0), P(-1.22, 1, 900), P(-1.4, 1, 900)], '#F6EEDC');
  poly(g, [P(-0.95, 1, 1.0), P(-0.62, 1, 1.0), P(-0.62, 1, 900), P(-0.95, 1, 900)], 'rgba(214,170,80,0.85)');
  // canopy (upper right)
  const cz0 = 0.5, cz1 = 52, cX = 1.25, cY = 4.5;
  // shadows of pillars on platform (sun from left/ahead => shadows lean right toward camera)
  for (let z0 = 6; z0 < 50; z0 += 7) {
    poly(g, [P(3.0, 1, z0), P(3.32, 1, z0), P(5.9, 1, z0 - 6.2), P(5.2, 1, z0 - 6.2)], 'rgba(80,52,36,0.26)');
  }
  // canopy shadow edge on platform (soft)
  g.save(); g.filter = 'blur(10px)';
  poly(g, [P(2.2, 1, 1.0), P(9, 1, 1.0), P(9, 1, 50), P(2.6, 1, 50)], 'rgba(90,60,45,0.18)');
  g.restore();
  // canopy underside
  poly(g, [P(cX, cY, cz0), P(14, cY, cz0), P(14, cY, cz1), P(cX, cY, cz1)],
    vGrad(g, 0, 1040, [[0, '#3C2B22'], [0.6, '#5E4535'], [1, '#9C7656']]));
  // transverse beams
  for (let z = 1.2; z < cz1; z += 3.5) {
    const a = P(cX, cY, z), b = P(14, cY, z);
    g.strokeStyle = 'rgba(40,28,22,0.55)'; g.lineWidth = Math.max(1, 40 / z);
    g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
  }
  // fascia
  poly(g, [P(cX, cY, cz0), P(cX, cY + 0.55, cz0), P(cX, cY + 0.55, cz1), P(cX, cY, cz1)], '#34261E');
  // gold lit lower edge of fascia
  g.strokeStyle = 'rgba(255,214,140,0.85)'; g.lineWidth = 2.5;
  { const a = P(cX, cY, 0.9), b = P(cX, cY, cz1); g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke(); }
  // pillars
  for (let z0 = 49; z0 >= 6; z0 -= 7) {
    const [x1, y1] = P(3.0, cY, z0), [x2, y2] = P(3.32, 1, z0);
    g.fillStyle = '#3A2A21'; g.fillRect(x1, y1, x2 - x1, y2 - y1);
    g.fillStyle = 'rgba(255,205,130,0.75)'; g.fillRect(x1, y1, Math.max(1, (x2 - x1) * 0.14), y2 - y1);
  }
  // hanging station sign
  {
    const z = 13, a = P(1.7, 3.85, z), b = P(3.9, 3.35, z);
    g.strokeStyle = 'rgba(40,30,25,0.8)'; g.lineWidth = 2;
    const w1 = P(2.0, cY, z), w2 = P(3.6, cY, z);
    g.beginPath(); g.moveTo(w1[0], w1[1]); g.lineTo(w1[0], a[1]); g.moveTo(w2[0], w2[1]); g.lineTo(w2[0], a[1]); g.stroke();
    g.fillStyle = '#EFE6D6'; g.fillRect(a[0], a[1], b[0] - a[0], b[1] - a[1]);
    g.fillStyle = 'rgba(127,155,176,0.9)'; g.fillRect(a[0], a[1] + (b[1] - a[1]) * 0.72, b[0] - a[0], (b[1] - a[1]) * 0.12);
    g.fillStyle = 'rgba(70,52,40,0.7)'; g.fillRect(a[0] + (b[0] - a[0]) * 0.3, a[1] + (b[1] - a[1]) * 0.25, (b[0] - a[0]) * 0.4, (b[1] - a[1]) * 0.25);
    g.fillStyle = 'rgba(30,22,18,0.35)'; g.fillRect(a[0], b[1], b[0] - a[0], 3);
  }
  // bench
  {
    const s = [P(4.2, 1.45, 8.5), P(4.75, 1.45, 8.5), P(4.75, 1.45, 11), P(4.2, 1.45, 11)];
    poly(g, [P(4.75, 1.5, 8.5), P(4.75, 2.1, 8.5), P(4.75, 2.1, 11), P(4.75, 1.5, 11)], '#4A3528');
    poly(g, s, '#6A4C38');
    poly(g, [P(4.2, 1.45, 8.5), P(4.2, 1.35, 8.5), P(4.2, 1.35, 11), P(4.2, 1.45, 11)], '#3A2A21');
    for (const z of [8.8, 10.7]) { const a = P(4.3, 1.35, z), b = P(4.3, 1, z); g.fillStyle = '#2E221B'; g.fillRect(a[0], a[1], 4, b[1] - a[1]); }
    g.strokeStyle = 'rgba(255,210,140,0.7)'; g.lineWidth = 2;
    g.beginPath(); g.moveTo(s[0][0], s[0][1]); g.lineTo(s[3][0], s[3][1]); g.stroke();
  }
  // horizon haze
  g.save(); g.globalCompositeOperation = 'screen';
  g.fillStyle = vGrad(g, 900, 1250, [[0, 'rgba(255,220,160,0)'], [0.45, 'rgba(255,220,160,0.35)'], [1, 'rgba(255,220,160,0)']]);
  g.fillRect(0, 900, W, 350); g.restore();
  // foreground shade for depth
  g.fillStyle = vGrad(g, 1350, 1920, [[0, 'rgba(70,46,32,0)'], [1, 'rgba(70,46,32,0.38)']]);
  g.fillRect(0, 1350, W, 570);
  // god rays
  g.save(); g.globalCompositeOperation = 'lighter';
  const R2 = rng(5);
  for (let i = 0; i < 6; i++) {
    const ang = Math.PI * (0.22 + 0.56 * R2()), len = 1500, wd = 0.012 + R2() * 0.025;
    const [sx, sy] = S1.sun;
    const gr = g.createRadialGradient(sx, sy, 0, sx, sy, len);
    gr.addColorStop(0, 'rgba(255,225,160,0.07)'); gr.addColorStop(0.5, 'rgba(255,225,160,0.015)'); gr.addColorStop(1, 'rgba(255,225,160,0)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(sx, sy);
    g.lineTo(sx + Math.cos(ang - wd) * len, sy + Math.sin(ang - wd) * len);
    g.lineTo(sx + Math.cos(ang + wd) * len, sy + Math.sin(ang + wd) * len); g.fill();
  }
  g.restore();
}
function scene1(g, t) {
  const p = ease(t / 3.4);
  const zoom = lerp(1.0, 1.11, p);
  const cx = lerp(540, 520, p), cy = lerp(990, 1010, p);
  drawLayer(g, L.station, cx, cy, zoom);
  const [sx, sy] = camPoint(S1.sun[0], S1.sun[1], cx, cy, zoom);
  flare(g, sx, sy, 0.55 + 0.45 * Math.sin(Math.PI * clamp(t / 3.2)));
}

// =====================================================================
// SCENE 2 — cozy coffee shop interior
// =====================================================================
const S2W = 1400;
function buildCafeBG(g) {
  const R = rng(22);
  // back wall
  g.fillStyle = vGrad(g, 0, 1500, [[0, '#6B4D3A'], [0.5, '#8C6A4F'], [1, '#B08A68']]);
  g.fillRect(0, 0, S2W, 1920);
  // wainscot
  g.fillStyle = '#5A3E2B'; g.fillRect(0, 1180, S2W, 740);
  g.fillStyle = 'rgba(255,220,170,0.12)'; g.fillRect(0, 1180, S2W, 6);
  for (let x = 20; x < S2W; x += 90) { g.fillStyle = 'rgba(30,20,15,0.25)'; g.fillRect(x, 1190, 3, 730); }
  // window (right)
  const wx = 660, wy = 260, ww = 640, wh = 900;
  g.fillStyle = vGrad(g, wy, wy + wh, [[0, '#F8E7C2'], [0.5, '#FBE0A8'], [1, '#F2C98A']]);
  g.fillRect(wx, wy, ww, wh);
  // outside: soft trees + street bokeh
  for (let i = 0; i < 26; i++) {
    const x = wx + R() * ww, y = wy + R() * wh * 0.7, r = 40 + R() * 110;
    g.fillStyle = R() < 0.6 ? 'rgba(110,140,95,0.35)' : 'rgba(240,190,200,0.35)';
    g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
  }
  softGlow(g, wx + ww * 0.65, wy + wh * 0.35, 420, '#FFF4D8', 0.9);
  g.fillStyle = 'rgba(200,170,140,0.5)'; g.fillRect(wx, wy + wh * 0.78, ww, wh * 0.22);
  // mullions
  g.fillStyle = '#4A3528';
  g.fillRect(wx - 26, wy - 26, ww + 52, 26); g.fillRect(wx - 26, wy + wh, ww + 52, 34);
  g.fillRect(wx - 26, wy, 26, wh); g.fillRect(wx + ww, wy, 26, wh);
  g.fillRect(wx + ww / 2 - 9, wy, 18, wh); g.fillRect(wx, wy + wh * 0.42, ww, 14);
  // sill
  g.fillStyle = '#6E4F3A'; g.fillRect(wx - 40, wy + wh + 20, ww + 80, 22);
  // shelves left
  for (const sy of [420, 640]) {
    g.fillStyle = '#4A3528'; g.fillRect(40, sy, 480, 18);
    g.fillStyle = 'rgba(255,220,170,0.15)'; g.fillRect(40, sy, 480, 3);
    let x = 60;
    while (x < 500) {
      const t = R(), w = 40 + R() * 40, h = 60 + R() * 70;
      if (t < 0.45) { // jar
        g.fillStyle = 'rgba(230,210,180,0.55)'; g.fillRect(x, sy - h, w, h);
        g.fillStyle = 'rgba(90,62,43,0.8)'; g.fillRect(x + 4, sy - h * 0.7, w - 8, h * 0.7 - 2);
        g.fillStyle = '#3A2A21'; g.fillRect(x - 2, sy - h - 10, w + 4, 12);
      } else if (t < 0.75) { // books
        for (let k = 0; k < 4; k++) {
          const bc = ['#7F9BB0', '#C9A27A', '#4E6B4A', '#B8735A', '#E6D3B3'][Math.floor(R() * 5)];
          g.fillStyle = bc; g.fillRect(x + k * 13, sy - h + R() * 15, 12, h);
        }
        w > 52 || (x += 10);
      } else { // plant
        g.fillStyle = '#7A5A44'; g.fillRect(x + 6, sy - 46, w - 12, 46);
        for (let k = 0; k < 9; k++) {
          g.fillStyle = k % 2 ? '#4E6B4A' : '#6E8A5E';
          g.beginPath(); g.ellipse(x + w / 2 + (R() - 0.5) * w, sy - 60 - R() * 50, 16, 34, (R() - 0.5) * 1.6, 0, 7); g.fill();
        }
      }
      x += w + 18;
    }
  }
  // pendant lamp
  g.strokeStyle = '#2E221B'; g.lineWidth = 3; g.beginPath(); g.moveTo(300, 0); g.lineTo(300, 160); g.stroke();
  g.fillStyle = '#3A2A21'; g.beginPath(); g.moveTo(240, 230); g.quadraticCurveTo(300, 140, 360, 230); g.closePath(); g.fill();
  softGlow(g, 300, 245, 360, '#FFC979', 0.55);
  softGlow(g, 300, 236, 60, '#FFF2D0', 1);
  // seat for the reader
  g.fillStyle = '#3E2C22'; g.fillRect(820, 880, 300, 300);
  g.fillStyle = '#4A3528'; g.fillRect(1180, 980, 160, 26); g.fillRect(1250, 1006, 14, 175);
  // light shafts from window
  g.save(); g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 5; i++) {
    const x0 = wx + 60 + i * 120;
    const gr = g.createLinearGradient(x0, wy, x0 - 600, 1900);
    gr.addColorStop(0, 'rgba(255,220,150,0.09)'); gr.addColorStop(1, 'rgba(255,220,150,0)');
    g.fillStyle = gr; g.beginPath();
    g.moveTo(x0, wy + 40); g.lineTo(x0 + 70, wy + 40); g.lineTo(x0 - 520, 1920); g.lineTo(x0 - 650, 1920); g.fill();
  }
  g.restore();
}
function buildReader(g) {
  // silhouette seated by window, facing left, reading — backlit
  g.save(); g.translate(960, 900);
  const sil = new Path2D();
  // torso
  sil.moveTo(-40, -150); sil.bezierCurveTo(-95, -120, -110, -10, -100, 120);
  sil.lineTo(110, 120); sil.bezierCurveTo(120, 20, 95, -120, 40, -150); sil.closePath();
  // neck + head
  sil.rect(-18, -190, 36, 50);
  sil.ellipse(-6, -238, 52, 60, 0, 0, Math.PI * 2);
  // hair bun-ish back
  sil.ellipse(34, -250, 30, 34, 0, 0, Math.PI * 2);
  // arms holding book
  sil.moveTo(-70, -60); sil.quadraticCurveTo(-130, 10, -170, -30); sil.lineTo(-160, -60); sil.quadraticCurveTo(-120, -30, -60, -100); sil.closePath();
  g.fillStyle = 'rgba(255,212,145,0.95)'; g.fill(sil);
  g.save(); g.translate(-7, 3); g.fillStyle = '#3B2A22'; g.fill(sil); g.restore();
  // book
  g.save(); g.translate(-185, -60); g.rotate(-0.45);
  g.fillStyle = '#E9DCC4'; g.fillRect(-46, -36, 92, 58);
  g.fillStyle = 'rgba(80,60,45,0.4)'; g.fillRect(-1, -36, 2, 58);
  g.restore();
  g.restore();
}
function buildTable(g) {
  // wooden table top in perspective, at bottom
  const top = 1360;
  g.fillStyle = vGrad(g, top, 1920, [[0, '#8A5E3F'], [0.4, '#6E4A33'], [1, '#4A3226']]);
  g.beginPath(); g.moveTo(-200, top); g.lineTo(S2W + 200, top); g.lineTo(S2W + 200, 1920); g.lineTo(-200, 1920); g.fill();
  const R = rng(7);
  for (let i = 0; i < 40; i++) { // grain
    const y = top + Math.pow(R(), 1.5) * 560;
    g.strokeStyle = `rgba(${R() < 0.5 ? '40,26,18' : '220,170,120'},${0.08 + R() * 0.08})`;
    g.lineWidth = 1 + R() * 3;
    g.beginPath(); g.moveTo(-200, y);
    for (let x = -200; x < S2W + 200; x += 80) g.lineTo(x, y + Math.sin(x / 200 + i) * 4);
    g.stroke();
  }
  g.fillStyle = 'rgba(255,215,160,0.5)'; g.fillRect(-200, top, S2W + 400, 3);
  // window light patch on table
  g.save(); g.globalCompositeOperation = 'screen'; g.filter = 'blur(18px)';
  g.fillStyle = 'rgba(255,200,130,0.35)';
  g.beginPath(); g.moveTo(560, top + 30); g.lineTo(1300, top + 30); g.lineTo(1100, 1920); g.lineTo(150, 1920); g.fill();
  g.restore();
  // saucer
  const cx = 640, cy = 1500;
  g.fillStyle = 'rgba(40,25,18,0.35)'; g.beginPath(); g.ellipse(cx + 40, cy + 40, 240, 52, 0, 0, 7); g.fill();
  g.fillStyle = '#EDE3D2'; g.beginPath(); g.ellipse(cx, cy + 20, 230, 56, 0, 0, 7); g.fill();
  g.fillStyle = '#D9CCB6'; g.beginPath(); g.ellipse(cx, cy + 16, 150, 34, 0, 0, 7); g.fill();
  // cup body
  const cupTop = cy - 210, rw = 130;
  const body = new Path2D();
  body.moveTo(cx - rw, cupTop);
  body.bezierCurveTo(cx - rw, cupTop + 150, cx - 100, cy + 10, cx - 50, cy + 14);
  body.lineTo(cx + 50, cy + 14);
  body.bezierCurveTo(cx + 100, cy + 10, cx + rw, cupTop + 150, cx + rw, cupTop);
  body.closePath();
  const bg = g.createLinearGradient(cx - rw, 0, cx + rw, 0);
  bg.addColorStop(0, '#FFF6E4'); bg.addColorStop(0.35, '#F3E8D5'); bg.addColorStop(0.8, '#C9B79C'); bg.addColorStop(1, '#A8957C');
  g.fillStyle = bg; g.fill(body);
  // handle
  g.strokeStyle = '#D8C8AE'; g.lineWidth = 22;
  g.beginPath(); g.ellipse(cx + rw + 18, cupTop + 90, 46, 56, 0, -1.6, 1.6); g.stroke();
  // rim
  g.fillStyle = '#FBF2E2'; g.beginPath(); g.ellipse(cx, cupTop, rw, 30, 0, 0, 7); g.fill();
  g.fillStyle = '#4A2C1C'; g.beginPath(); g.ellipse(cx, cupTop + 4, rw - 12, 22, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(200,140,80,0.5)'; g.beginPath(); g.ellipse(cx - 10, cupTop + 6, rw - 40, 12, 0, 0, 7); g.fill();
  // rim highlight
  g.strokeStyle = 'rgba(255,240,210,0.9)'; g.lineWidth = 3;
  g.beginPath(); g.ellipse(cx, cupTop, rw, 30, 0, Math.PI * 1.05, Math.PI * 1.6); g.stroke();
  // spoon
  g.save(); g.translate(cx + 210, cy + 22); g.rotate(-0.12);
  g.fillStyle = '#C9B48C'; g.fillRect(-120, -5, 120, 9);
  g.beginPath(); g.ellipse(-130, -1, 26, 12, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(255,240,200,0.8)'; g.fillRect(-110, -5, 100, 2);
  g.restore();
  // small notebook edge left
  g.save(); g.translate(150, 1700); g.rotate(-0.08);
  g.fillStyle = '#7F9BB0'; g.fillRect(-260, -90, 360, 200);
  g.fillStyle = '#EFE6D6'; g.fillRect(-260, -100, 352, 14);
  g.restore();
  // little plant
  g.fillStyle = '#B98B66'; g.fillRect(1040, 1300, 90, 90);
  for (let k = 0; k < 10; k++) {
    g.fillStyle = k % 2 ? '#4E6B4A' : '#6E8A5E';
    g.beginPath(); g.ellipse(1085 + Math.cos(k) * 40, 1270 - (k % 4) * 18, 16, 34, Math.cos(k * 2), 0, 7); g.fill();
  }
}
function steam(g, x, y, t, scale = 1, alpha = 1) {
  g.save(); g.globalCompositeOperation = 'screen'; g.filter = `blur(${10 * scale}px)`;
  for (let k = 0; k < 3; k++) {
    const ph = k * 2.1;
    g.beginPath();
    for (let i = 0; i <= 40; i++) {
      const h = i / 40, yy = y - h * 420 * scale;
      const xx = x + (k - 1) * 30 * scale + Math.sin(h * 5 + t * 1.3 + ph) * (12 + 60 * h) * scale + Math.sin(h * 11 - t * 0.9 + ph) * 8 * h * scale;
      i ? g.lineTo(xx, yy) : g.moveTo(xx, yy);
    }
    const gr = g.createLinearGradient(0, y, 0, y - 420 * scale);
    gr.addColorStop(0, `rgba(255,245,230,${0.0})`); gr.addColorStop(0.15, `rgba(255,245,230,${0.32 * alpha})`);
    gr.addColorStop(1, 'rgba(255,245,230,0)');
    g.strokeStyle = gr; g.lineWidth = (26 - k * 5) * scale; g.lineCap = 'round'; g.stroke();
  }
  g.restore();
}
function scene2(g, t) {
  const p = ease(t / 3.6);
  // camera drifts left: background shifts less than foreground
  const bgX = lerp(760, 700, p), fgX = lerp(760, 640, p);
  drawLayer(g, L.cafeBG, bgX, 960, 1.0);
  g.save(); g.translate(Math.sin(t * 1.2) * 0.8, Math.sin(t * 0.9) * 1.2);
  drawLayer(g, L.reader, bgX, 960, 1.0);
  g.restore();
  drawLayer(g, L.table, fgX, 960, 1.0);
  const [sx, sy] = camPoint(640, 1290, fgX, 960, 1.0);
  steam(g, sx, sy, t + 2);
  // soft warm wash
  g.save(); g.globalCompositeOperation = 'soft-light'; g.fillStyle = 'rgba(255,190,110,0.25)'; g.fillRect(0, 0, W, H); g.restore();
}

// =====================================================================
// SCENE 3 — tree-lined street, bookstore, tilt up
// =====================================================================
const S3H = 3000;
function buildStreetSky(g) {
  const R = rng(33);
  g.fillStyle = vGrad(g, 0, 2400, [[0, '#7C98AE'], [0.3, '#A9BACA'], [0.55, '#E5D7C0'], [0.75, '#F5DEB0'], [1, '#F8E3BC']]);
  g.fillRect(0, 0, W, S3H);
  cloud(g, 300, 380, 640, 120, '#F7EBDD', 0.55, R);
  cloud(g, 820, 720, 520, 90, '#F8E2CF', 0.5, R);
  cloud(g, 200, 1050, 420, 70, '#F9DFC0', 0.45, R);
  softGlow(g, 980, 1250, 700, '#FFE3A8', 0.55);
}
function buildBookstore(g) {
  const R = rng(34);
  // neighbours (muted, hazy)
  g.fillStyle = '#B9A994'; g.fillRect(-20, 1640, 200, 980);
  g.fillStyle = '#C8B49A'; g.fillRect(900, 1580, 220, 1040);
  for (let y = 1700; y < 2400; y += 170) { g.fillStyle = 'rgba(127,155,176,0.45)'; g.fillRect(30, y, 100, 100); g.fillRect(950, y + 30, 110, 100); }
  // main building
  const bx = 170, bw = 740;
  g.fillStyle = '#EBDDC6'; g.fillRect(bx, 1480, bw, 620);
  // roof eave
  g.fillStyle = '#5A3E2B'; g.beginPath(); g.moveTo(bx - 40, 1500); g.lineTo(bx + bw + 40, 1500); g.lineTo(bx + bw + 10, 1440); g.lineTo(bx - 10, 1440); g.fill();
  // upper windows with plants
  for (const wx of [bx + 90, bx + bw - 290]) {
    g.fillStyle = '#5A3E2B'; g.fillRect(wx - 10, 1600, 220, 230);
    g.fillStyle = vGrad(g, 1610, 1820, [[0, '#9FB4C4'], [1, '#E7D3B0']]); g.fillRect(wx, 1610, 200, 210);
    g.fillStyle = '#5A3E2B'; g.fillRect(wx + 95, 1610, 10, 210);
    g.fillStyle = '#7A5A44'; g.fillRect(wx - 10, 1830, 220, 26);
    for (let k = 0; k < 12; k++) { g.fillStyle = k % 2 ? '#4E6B4A' : '#6E8A5E'; g.beginPath(); g.arc(wx + R() * 200, 1825 - R() * 30, 14 + R() * 10, 0, 7); g.fill(); }
  }
  // ground floor shopfront
  g.fillStyle = '#5A3E2B'; g.fillRect(bx, 2100, bw, 520);
  // awning
  g.fillStyle = '#4E6B4A';
  g.beginPath(); g.moveTo(bx - 30, 2080); g.lineTo(bx + bw + 30, 2080); g.lineTo(bx + bw + 60, 2200); g.lineTo(bx - 60, 2200); g.fill();
  for (let i = 0; i < 14; i++) { // scallops + stripes
    const x0 = bx - 60 + i * ((bw + 120) / 14);
    g.fillStyle = i % 2 ? '#5F7D58' : '#4E6B4A';
    g.beginPath(); g.moveTo(x0 + 3 + 0.5 * i, 2080); g.lineTo(x0 + (bw + 120) / 14, 2080); g.lineTo(x0 + (bw + 120) / 14, 2200); g.lineTo(x0, 2200); g.fill();
    g.fillStyle = i % 2 ? '#5F7D58' : '#4E6B4A';
    g.beginPath(); g.arc(x0 + (bw + 120) / 28, 2200, (bw + 120) / 28, 0, Math.PI); g.fill();
  }
  g.fillStyle = 'rgba(255,230,180,0.35)'; g.fillRect(bx - 30, 2080, bw + 60, 4);
  // sign board
  g.fillStyle = '#EFE3CC'; g.fillRect(bx + bw / 2 - 150, 1960, 300, 90);
  g.strokeStyle = '#5A3E2B'; g.lineWidth = 6; g.strokeRect(bx + bw / 2 - 150, 1960, 300, 90);
  g.fillStyle = '#5A3E2B'; g.font = '500 52px CG'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('BOOKS', bx + bw / 2, 2006);
  // display windows
  for (const [wx, ww] of [[bx + 30, 260], [bx + bw - 290, 260]]) {
    g.fillStyle = vGrad(g, 2240, 2560, [[0, '#F6CD86'], [1, '#D9934E']]); g.fillRect(wx, 2240, ww, 320);
    for (let sy = 2290; sy < 2560; sy += 85) {
      let x = wx + 8;
      while (x < wx + ww - 16) {
        const bw2 = 10 + R() * 14, bh = 45 + R() * 30;
        g.fillStyle = ['#7F9BB0', '#C9A27A', '#4E6B4A', '#B8735A', '#E6D3B3', '#8C5E46', '#F2C6CF'][Math.floor(R() * 7)];
        g.globalAlpha = 0.85; g.fillRect(x, sy + 70 - bh, bw2, bh); g.globalAlpha = 1; x += bw2 + 2;
      }
      g.fillStyle = '#6B4A35'; g.fillRect(wx, sy + 70, ww, 8);
    }
    softGlow(g, wx + ww / 2, 2330, 220, '#FFE0A0', 0.45);
    g.fillStyle = 'rgba(255,255,255,0.12)'; g.beginPath(); g.moveTo(wx + 30, 2240); g.lineTo(wx + 110, 2240); g.lineTo(wx + 20, 2560); g.lineTo(wx - 60 < wx ? wx : wx, 2560); g.fill();
  }
  // door
  const dx = bx + bw / 2 - 90;
  g.fillStyle = '#3E2C22'; g.fillRect(dx - 12, 2228, 204, 392);
  g.fillStyle = vGrad(g, 2240, 2610, [[0, '#F3C47A'], [1, '#C98448']]); g.fillRect(dx, 2240, 180, 380);
  g.fillStyle = '#3E2C22'; g.fillRect(dx + 86, 2240, 8, 380);
  g.fillStyle = '#C9A050'; g.fillRect(dx + 70, 2420, 6, 40); g.fillRect(dx + 104, 2420, 6, 40);
  // pots
  for (const px of [bx + 10, bx + bw - 90]) {
    g.fillStyle = '#9C6B4E'; g.fillRect(px, 2540, 80, 80);
    for (let k = 0; k < 10; k++) { g.fillStyle = k % 2 ? '#4E6B4A' : '#6E8A5E'; g.beginPath(); g.ellipse(px + 40 + (R() - 0.5) * 70, 2520 - R() * 60, 15, 30, (R() - 0.5) * 1.4, 0, 7); g.fill(); }
  }
  // sidewalk
  g.fillStyle = vGrad(g, 2620, 3000, [[0, '#D8C3A3'], [1, '#B79F84']]); g.fillRect(-20, 2620, W + 40, 400);
  g.strokeStyle = 'rgba(110,85,65,0.25)'; g.lineWidth = 2;
  for (let y = 2660; y < 3000; y += 60 + (y - 2620) * 0.25) { g.beginPath(); g.moveTo(0, y); g.lineTo(W, y); g.stroke(); }
  for (let i = -8; i <= 8; i++) { g.beginPath(); g.moveTo(540 + i * 70, 2620); g.lineTo(540 + i * 160, 3000); g.stroke(); }
  g.fillStyle = 'rgba(70,50,38,0.25)'; g.fillRect(-20, 2620, W + 40, 14);
  // warm sun wash across facade (from right)
  g.save(); g.globalCompositeOperation = 'soft-light';
  const gr = g.createLinearGradient(W, 1500, 0, 2600); gr.addColorStop(0, 'rgba(255,200,120,0.7)'); gr.addColorStop(1, 'rgba(255,200,120,0)');
  g.fillStyle = gr; g.fillRect(0, 1400, W, 1600); g.restore();
}
function sakuraCanopy(g, cx, cy, rx, ry, seed) {
  const R = rng(seed);
  const pts = [];
  for (let i = 0; i < 16; i++) {
    const a = R() * Math.PI * 2, d = Math.sqrt(R()) * 0.8;
    pts.push([cx + Math.cos(a) * rx * d, cy + Math.sin(a) * ry * d, (0.35 + R() * 0.3) * Math.min(rx, ry * 1.6)]);
  }
  // shadow mass
  g.fillStyle = '#D79AAA';
  for (const [x, y, r] of pts) { g.beginPath(); g.arc(x - r * 0.08, y + r * 0.12, r, 0, 7); g.fill(); }
  // main mass
  g.fillStyle = '#EBB8C3';
  for (const [x, y, r] of pts) { g.beginPath(); g.arc(x, y, r * 0.9, 0, 7); g.fill(); }
  // light from upper right
  for (const [x, y, r] of pts) {
    const gr = g.createRadialGradient(x + r * 0.35, y - r * 0.35, 0, x + r * 0.35, y - r * 0.35, r * 0.9);
    gr.addColorStop(0, 'rgba(255,236,226,0.85)'); gr.addColorStop(1, 'rgba(255,236,226,0)');
    g.fillStyle = gr; g.beginPath(); g.arc(x, y, r * 0.9, 0, 7); g.fill();
  }
  // blossom texture: small clusters
  for (let i = 0; i < 1400; i++) {
    const [x0, y0, r0] = pts[Math.floor(R() * pts.length)];
    const a = R() * Math.PI * 2, d = Math.sqrt(R()) * r0 * 1.02;
    const x = x0 + Math.cos(a) * d, y = y0 + Math.sin(a) * d;
    const lit = (Math.cos(a) - Math.sin(a)) * (d / r0);
    g.fillStyle = lit > 0.3 ? (R() < 0.5 ? '#FFF1EE' : '#F9DCE0') : lit < -0.4 ? (R() < 0.5 ? '#C98A9C' : '#DDA2B1') : (R() < 0.5 ? '#F2C6CF' : '#E7AFBB');
    g.globalAlpha = 0.55 + R() * 0.45;
    g.beginPath(); g.arc(x, y, 3 + R() * 7, 0, 7); g.fill();
  }
  g.globalAlpha = 1;
  // a few dark branch hints
  g.strokeStyle = 'rgba(74,52,40,0.55)'; g.lineCap = 'round';
  for (let i = 0; i < 0; i++) {
    const [x, y, r] = pts[i]; g.lineWidth = 3 + R() * 3;
    g.beginPath(); g.moveTo(x, y + r * 0.6); g.quadraticCurveTo(x + (R() - 0.5) * r, y, x + (R() - 0.5) * r * 1.2, y - r * 0.4); g.stroke();
  }
}
function trunk(g, x0, y0, x1, y1, w) {
  g.fillStyle = '#4A3428';
  g.beginPath(); g.moveTo(x0 - w, y0); g.quadraticCurveTo((x0 + x1) / 2 - w * 0.6, (y0 + y1) / 2, x1 - w * 0.35, y1);
  g.lineTo(x1 + w * 0.35, y1); g.quadraticCurveTo((x0 + x1) / 2 + w * 0.6, (y0 + y1) / 2, x0 + w, y0); g.fill();
}
function buildMidTrees(g) {
  // green trees behind/around building + sakura above
  const R = rng(35);
  for (let i = 0; i < 6; i++) {
    const x = R() * W, y = 1350 + R() * 200;
    g.fillStyle = 'rgba(78,107,74,0.55)';
    for (let k = 0; k < 30; k++) { g.beginPath(); g.arc(x + (R() - 0.5) * 300, y + (R() - 0.5) * 160, 30 + R() * 40, 0, 7); g.fill(); }
  }
  sakuraCanopy(g, 540, 1300, 380, 160, 81);
}
function buildFgTrees(g) {
  trunk(g, 40, 3000, 120, 1300, 46);
  trunk(g, 110, 1700, 380, 1150, 16);
  trunk(g, 1050, 3000, 960, 1250, 42);
  trunk(g, 980, 1650, 720, 1050, 14);
  sakuraCanopy(g, 180, 1150, 420, 300, 91);
  sakuraCanopy(g, 920, 1060, 440, 320, 92);
  sakuraCanopy(g, 560, 880, 300, 140, 93);
  sakuraCanopy(g, 60, 820, 260, 180, 94);
  sakuraCanopy(g, 1030, 760, 240, 170, 95);
}
function scene3(g, t) {
  const p = ease(t / 3.5);
  const cy = lerp(2040, 1000, p);
  drawLayer(g, L.streetSky, 540, lerp(2040, 1250, p), 1.0);
  drawLayer(g, L.midTrees, 540, lerp(2040, 1080, p), 1.0);
  drawLayer(g, L.bookstore, 540, cy, 1.0);
  // light rays through trees
  g.save(); g.globalCompositeOperation = 'lighter';
  for (let i = 0; i < 6; i++) {
    const x0 = 650 + i * 90 + Math.sin(t * 0.4 + i) * 10;
    const gr = g.createLinearGradient(x0, 0, x0 - 500, H);
    gr.addColorStop(0, 'rgba(255,225,165,0.08)'); gr.addColorStop(1, 'rgba(255,225,165,0)');
    g.fillStyle = gr; g.beginPath(); g.moveTo(x0, 0); g.lineTo(x0 + 40, 0); g.lineTo(x0 - 420, H); g.lineTo(x0 - 520, H); g.fill();
  }
  g.restore();
  g.save(); g.translate(Math.sin(t * 0.7) * 3, 0);
  drawLayer(g, L.fgTrees, 540, lerp(2040, 900, p), 1.0);
  g.restore();
}

// =====================================================================
// SCENE 4 — two friends through café glass
// =====================================================================
function person(g, o, t) {
  // profile facing +x. origin at table edge below torso centre.
  g.save(); g.translate(o.x, o.y); if (o.flip) g.scale(-1, 1);
  const breathe = Math.sin(t * 1.6 + o.ph) * 2;
  // torso
  g.fillStyle = o.shirt;
  g.beginPath(); g.moveTo(-90, 40); g.bezierCurveTo(-110, -120, -90, -230 + breathe, -20, -255 + breathe);
  g.bezierCurveTo(40, -262 + breathe, 80, -200 + breathe, 85, -120); g.lineTo(80, 40); g.closePath(); g.fill();
  // shirt shade (back side)
  g.fillStyle = 'rgba(40,25,18,0.25)';
  g.beginPath(); g.moveTo(-90, 40); g.bezierCurveTo(-110, -120, -90, -230 + breathe, -20, -255 + breathe); g.lineTo(-40, -200); g.lineTo(-50, 40); g.fill();
  // neck
  g.fillStyle = o.skinShade; g.fillRect(-14, -300 + breathe, 34, 60);
  // head (with nod)
  g.save(); g.translate(4, -300 + breathe); g.rotate(o.nod(t));
  g.fillStyle = o.skin;
  g.beginPath(); g.moveTo(-50, -40);
  g.bezierCurveTo(-50, -120, 50, -130, 62, -60); // crown to brow
  g.quadraticCurveTo(64, -42, 74, -30); // nose
  g.quadraticCurveTo(66, -22, 62, -14);
  g.quadraticCurveTo(64, 2, 54, 10); // chin
  g.quadraticCurveTo(20, 22, -10, 8);
  g.closePath(); g.fill();
  // hair
  g.fillStyle = o.hair;
  g.beginPath(); g.moveTo(-58, 20);
  g.bezierCurveTo(-80, -60, -40, -140, 20, -128);
  g.bezierCurveTo(60, -120, 70, -80, 64, -62);
  g.quadraticCurveTo(30, -80, 10, -60); g.quadraticCurveTo(-5, -30, -10, 8);
  if (o.long) { g.quadraticCurveTo(-20, 60, -40, 80); g.quadraticCurveTo(-70, 60, -58, 20); }
  g.closePath(); g.fill();
  // ear hint + warm rim
  g.fillStyle = o.skinShade; g.beginPath(); g.ellipse(0, -30, 9, 14, 0, 0, 7); g.fill();
  g.strokeStyle = 'rgba(255,214,150,0.7)'; g.lineWidth = 3;
  g.beginPath(); g.moveTo(62, -60); g.quadraticCurveTo(64, -42, 74, -30); g.quadraticCurveTo(66, -22, 62, -14); g.quadraticCurveTo(64, 2, 54, 10); g.stroke();
  g.restore();
  // forearm on table toward cup
  const lift = o.gesture ? o.gesture(t) : 0;
  g.fillStyle = o.shirt;
  g.beginPath(); g.moveTo(10, -170 + breathe);
  g.quadraticCurveTo(70, -120, 70, -40 - lift * 0.4);
  g.lineTo(160, -30 - lift); g.lineTo(160, 0 - lift); g.lineTo(40, -6); g.quadraticCurveTo(10, -60, -20, -150); g.closePath(); g.fill();
  g.fillStyle = o.skin; g.beginPath(); g.ellipse(170, -14 - lift, 20, 16, 0, 0, 7); g.fill();
  g.restore();
}
function buildCafeInterior(g) {
  const R = rng(44);
  g.fillStyle = vGrad(g, 0, 1920, [[0, '#4A3226'], [0.45, '#8A5E3F'], [0.7, '#B9814E'], [1, '#6E4A33']]);
  g.fillRect(0, 0, W, H);
  // bokeh string lights / shelves
  for (let i = 0; i < 40; i++) {
    const x = R() * W, y = 300 + R() * 700, r = 14 + R() * 40;
    softGlow(g, x, y, r * 2, R() < 0.7 ? '#FFC979' : '#F2C6CF', 0.35 + R() * 0.35);
  }
  // back shelves (soft)
  for (const sy of [700, 900]) { g.fillStyle = 'rgba(60,40,30,0.6)'; g.fillRect(120, sy, 840, 14); }
  // plant left
  for (let k = 0; k < 20; k++) { g.fillStyle = k % 2 ? 'rgba(78,107,74,0.8)' : 'rgba(110,138,94,0.8)'; g.beginPath(); g.ellipse(170 + (R() - 0.5) * 140, 980 - R() * 220, 20, 46, (R() - 0.5) * 1.8, 0, 7); g.fill(); }
  g.fillStyle = '#7A5A44'; g.fillRect(120, 980, 110, 130);
  // pendant lamp over table
  g.strokeStyle = '#2E221B'; g.lineWidth = 3; g.beginPath(); g.moveTo(540, 0); g.lineTo(540, 620); g.stroke();
  g.fillStyle = '#3A2A21'; g.beginPath(); g.moveTo(450, 720); g.quadraticCurveTo(540, 580, 630, 720); g.closePath(); g.fill();
  softGlow(g, 540, 760, 700, '#FFB866', 0.55);
  softGlow(g, 540, 726, 80, '#FFF2D0', 1);
}
function buildCafeTable(g) {
  g.fillStyle = '#5A3E2B'; g.beginPath(); g.ellipse(540, 1250, 300, 46, 0, 0, 7); g.fill();
  g.fillStyle = 'rgba(255,200,130,0.35)'; g.beginPath(); g.ellipse(540, 1244, 290, 38, 0, Math.PI, 0); g.fill();
  g.fillStyle = '#3E2C22'; g.fillRect(525, 1290, 30, 400); g.fillRect(420, 1680, 240, 18);
  for (const [x, c] of [[430, '#EDE3D2'], [650, '#E6D3B3']]) {
    g.fillStyle = c; g.beginPath(); g.moveTo(x - 36, 1180); g.lineTo(x + 36, 1180); g.lineTo(x + 28, 1240); g.lineTo(x - 28, 1240); g.fill();
    g.fillStyle = '#4A2C1C'; g.beginPath(); g.ellipse(x, 1182, 34, 8, 0, 0, 7); g.fill();
  }
}
function buildWindowFrame(g) {
  // exterior: wooden frame + wall, with glass opening
  const gx = 110, gy = 360, gw = 860, gh = 1240;
  g.fillStyle = '#3A2A21';
  g.beginPath(); g.rect(0, 0, W, H); g.rect(gx, gy, gw, gh); g.fill('evenodd');
  // exterior wall above/below: cream plaster
  g.fillStyle = '#D9C6A6'; g.fillRect(0, 0, W, 240);
  g.fillStyle = '#C8B08E'; g.fillRect(0, 1700, W, 220);
  g.fillStyle = '#4A3528'; g.fillRect(gx - 30, gy - 40, gw + 60, 40); g.fillRect(gx - 50, gy + gh, gw + 100, 50);
  g.fillStyle = 'rgba(255,220,160,0.4)'; g.fillRect(gx - 50, gy + gh, gw + 100, 5);
  g.fillStyle = '#4A3528'; g.fillRect(gx + gw / 2 - 8, gy, 16, gh);
  // sill plant
  const R = rng(46);
  g.fillStyle = '#9C6B4E'; g.fillRect(820, 1560, 120, 100);
  for (let k = 0; k < 16; k++) { g.fillStyle = k % 2 ? '#4E6B4A' : '#6E8A5E'; g.beginPath(); g.ellipse(880 + (R() - 0.5) * 120, 1540 - R() * 80, 18, 38, (R() - 0.5) * 1.6, 0, 7); g.fill(); }
}
function scene4(g, t) {
  const p = ease(t / 3.6);
  const zoom = lerp(1.0, 1.06, p);
  // interior (slightly soft)
  drawLayer(g, L.cafeIn, 540, 980, zoom);
  g.save(); camApply(g, 540, 980, zoom);
  g.filter = 'blur(1.2px)';
  const A = { x: 300, y: 1230, flip: false, ph: 0, shirt: '#E6D3B3', hair: '#4A3226', skin: '#F1D2B6', skinShade: '#D8B396', long: true,
    nod: (tt) => -0.03 + 0.04 * Math.sin(tt * 1.4) * smooth(0.4, 1.2, tt) };
  const B = { x: 780, y: 1230, flip: true, ph: 1.3, shirt: '#7F9BB0', hair: '#2E221B', skin: '#EDCBAE', skinShade: '#D2AB8C', long: false,
    nod: (tt) => 0.02 * Math.sin(tt * 0.9 + 1),
    gesture: (tt) => 26 * smooth(0.8, 2.0, tt) * (1 - smooth(2.4, 3.4, tt)) };
  person(g, A, t); person(g, B, t);
  g.filter = 'none';
  g.restore();
  drawLayer(g, L.cafeTable, 540, 980, zoom);
  {
    const [x1, y1] = camPoint(430, 1175, 540, 980, zoom), [x2, y2] = camPoint(650, 1175, 540, 980, zoom);
    steam(g, x1, y1, t, 0.35, 0.8); steam(g, x2, y2, t + 1.5, 0.35, 0.8);
  }
  // glass: reflection + streaks
  g.save(); g.globalCompositeOperation = 'screen';
  g.fillStyle = vGrad(g, 0, H, [[0, 'rgba(127,155,176,0.22)'], [0.5, 'rgba(127,155,176,0.05)'], [1, 'rgba(242,198,207,0.08)']]);
  g.fillRect(0, 0, W, H);
  for (let i = 0; i < 3; i++) {
    const x = 200 + i * 300 + t * 12;
    const gr = g.createLinearGradient(x, 0, x + 160, 0);
    gr.addColorStop(0, 'rgba(255,240,220,0)'); gr.addColorStop(0.5, `rgba(255,240,220,${0.10 - i * 0.02})`); gr.addColorStop(1, 'rgba(255,240,220,0)');
    g.fillStyle = gr; g.save(); g.translate(x, 960); g.rotate(-0.35); g.fillRect(-120, -1400, 300, 2800); g.restore();
  }
  g.restore();
  drawLayer(g, L.winFrame, 540, 980, lerp(1.0, 1.09, p));
}

// =====================================================================
// SCENE 5 — dusk street, windows lighting, wordmark
// =====================================================================
const S5 = { windows: [], lamps: [] };
const P5 = makeProj(540, 1180, 560, 1.7);
function buildDusk(g) {
  const R = rng(55); const P = P5;
  g.fillStyle = vGrad(g, 0, 1200, [[0, '#4E6782'], [0.35, '#7E8BA6'], [0.62, '#C3A3AE'], [0.85, '#EBB98A'], [1, '#F4CF9A']]);
  g.fillRect(0, 0, W, 1200);
  cloud(g, 300, 420, 600, 90, '#D8A9A8', 0.35, R);
  cloud(g, 820, 650, 480, 60, '#EDBB98', 0.35, R);
  softGlow(g, 560, 1170, 520, '#FFD39A', 0.6);
  // road
  poly(g, [P(-30, 0, 1), P(30, 0, 1), P(30, 0, 900), P(-30, 0, 900)], vGrad(g, 1180, 1920, [[0, '#A08A86'], [0.15, '#6A6472'], [1, '#3C3C4A']]));
  // amber reflection on road
  g.save(); g.globalCompositeOperation = 'screen'; g.filter = 'blur(20px)';
  g.fillStyle = 'rgba(255,190,120,0.35)'; g.beginPath(); g.moveTo(520, 1180); g.lineTo(560, 1180); g.lineTo(760, 1920); g.lineTo(340, 1920); g.fill();
  g.restore();
  // centre dashes
  for (let z = 2; z < 120; z += 4) poly(g, [P(-0.08, 0, z), P(0.08, 0, z), P(0.08, 0, z + 1.6), P(-0.08, 0, z + 1.6)], 'rgba(240,226,200,0.5)');
  // sidewalks
  for (const s of [-1, 1]) {
    const a = 4.2 * s, b = 7.5 * s;
    poly(g, [P(a, 0.15, 1), P(b, 0.15, 1), P(b, 0.15, 900), P(a, 0.15, 900)], vGrad(g, 1180, 1920, [[0, '#B59C8E'], [1, '#6E6268']]));
    poly(g, [P(a, 0, 1), P(a, 0.15, 1), P(a, 0.15, 900), P(a, 0, 900)], 'rgba(230,200,170,0.5)');
  }
  // building facades
  const bldgs = [];
  for (const s of [-1, 1]) {
    let z = 2.2;
    while (z < 130) {
      const len = 5 + R() * 7, h = 6 + R() * 9, X = (7.5 + R() * 0.8) * s;
      bldgs.push({ s, z0: z, z1: z + len, h, X, tone: R() });
      z += len + 0.3;
    }
  }
  bldgs.sort((a, b) => b.z0 - a.z0);
  for (const b of bldgs) {
    const c = ['#6A5A5E', '#7A6862', '#5E5560', '#806A5E', '#6E6266'][Math.floor(b.tone * 5)];
    poly(g, [P(b.X, 0, b.z0), P(b.X, b.h, b.z0), P(b.X, b.h, b.z1), P(b.X, 0, b.z1)], c);
    // front edge face (facing camera)
    poly(g, [P(b.X, 0, b.z0), P(b.X, b.h, b.z0), P(b.X + 3 * b.s, b.h, b.z0), P(b.X + 3 * b.s, 0, b.z0)], 'rgba(60,50,58,1)');
    // roof edge highlight from dusk sky
    g.strokeStyle = 'rgba(240,190,150,0.5)'; g.lineWidth = Math.max(1, 20 / b.z0);
    const r0 = P(b.X, b.h, b.z0), r1 = P(b.X, b.h, b.z1); g.beginPath(); g.moveTo(r0[0], r0[1]); g.lineTo(r1[0], r1[1]); g.stroke();
    // windows
    for (let fy = 3.2; fy + 1.4 < b.h; fy += 3) {
      for (let wz = b.z0 + 0.8; wz + 1.2 < b.z1; wz += 2.4) {
        const q = [P(b.X, fy, wz), P(b.X, fy + 1.4, wz), P(b.X, fy + 1.4, wz + 1.2), P(b.X, fy, wz + 1.2)];
        poly(g, q, 'rgba(50,45,60,0.75)');
        S5.windows.push({ q, z: wz, on: 0 });
      }
    }
    // ground shop
    const sq = [P(b.X, 0.3, b.z0 + 0.5), P(b.X, 2.4, b.z0 + 0.5), P(b.X, 2.4, b.z1 - 0.5), P(b.X, 0.3, b.z1 - 0.5)];
    poly(g, sq, 'rgba(45,40,52,0.8)');
    S5.windows.push({ q: sq, z: b.z0, on: 0, shop: true });
  }
  // far building at end
  { const a = P(-7.5, 14, 135), b2 = P(7.5, 0, 135); g.fillStyle = '#6E6470'; g.fillRect(a[0], a[1], b2[0] - a[0], b2[1] - a[1]); }
  // utility poles + wires
  g.strokeStyle = '#2F2A33';
  const tops = [];
  for (let z = 3; z < 120; z += 11) {
    const a = P(-4.6, 0, z), b = P(-4.6, 9.5, z);
    g.lineWidth = Math.max(1, 26 / z); g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.stroke();
    const c1 = P(-5.6, 8.8, z), c2 = P(-3.6, 8.8, z);
    g.lineWidth = Math.max(1, 14 / z); g.beginPath(); g.moveTo(c1[0], c1[1]); g.lineTo(c2[0], c2[1]); g.stroke();
    tops.push(z);
    S5.lamps.push({ z, p: P(-4.0, 5.2, z) });
  }
  g.lineWidth = 1.5; g.strokeStyle = 'rgba(40,36,44,0.8)';
  for (const [X, Y] of [[-5.5, 8.8], [-4.6, 9.4], [-3.7, 8.8], [-3.0, 8.0]]) {
    for (let i = 0; i < tops.length - 1; i++) {
      const a = P(X, Y, tops[i]), b = P(X, Y, tops[i + 1]); const m = P(X, Y - 0.5, (tops[i] + tops[i + 1]) / 2);
      g.beginPath(); g.moveTo(a[0], a[1]); g.quadraticCurveTo(m[0], m[1] + (m[1] - (a[1] + b[1]) / 2), b[0], b[1]); g.stroke();
    }
    // wire toward camera
    const a = P(X, Y, tops[0]), b = P(X, Y + 1.5, 0.8);
    g.beginPath(); g.moveTo(a[0], a[1]); g.quadraticCurveTo((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 60, b[0], b[1]); g.stroke();
  }
  // assign lighting times
  const R2 = rng(77);
  S5.windows.forEach((w) => { w.on = w.shop ? 12.15 + R2() * 0.4 : (R2() < 0.75 ? 12.2 + R2() * 1.5 : 99); w.warm = R2(); });
  S5.lamps.forEach((l, i) => { l.on = 12.4 + i * 0.12; });
}
function scene5(g, t) { // t = absolute time
  const lt = t - 12;
  const p = ease(lt / 2.2);
  const zoom = lerp(1.2, 1.0, p);
  const cx = 540, cy = lerp(1180, 960, p);
  drawLayer(g, L.dusk, cx, cy, zoom);
  g.save(); camApply(g, cx, cy, zoom);
  for (const w of S5.windows) {
    const a = smooth(w.on, w.on + 0.35, t); if (a <= 0) continue;
    const col = w.warm < 0.7 ? `rgba(255,${190 + Math.floor(w.warm * 40)},120,${0.9 * a})` : `rgba(255,226,180,${0.85 * a})`;
    poly(g, w.q, col);
    const m = w.q.reduce((s, p) => [s[0] + p[0] / 4, s[1] + p[1] / 4], [0, 0]);
    const r = Math.abs(w.q[2][0] - w.q[0][0]) * 1.4 + 6;
    softGlow(g, m[0], m[1], r, '#FFC277', 0.35 * a, 'lighter');
  }
  for (const l of S5.lamps) {
    const a = smooth(l.on, l.on + 0.4, t); if (a <= 0) continue;
    const r = 260 / l.z + 4;
    softGlow(g, l.p[0], l.p[1], r * 6, '#FFD9A0', 0.6 * a, 'lighter');
    g.fillStyle = `rgba(255,245,220,${a})`; g.beginPath(); g.arc(l.p[0], l.p[1], Math.max(1.2, r * 0.4), 0, 7); g.fill();
  }
  g.restore();
}
function wordmark(g, t) {
  // cream card
  g.fillStyle = '#F4EADB'; g.fillRect(0, 0, W, H);
  softGlow(g, 540, 900, 900, '#FFE7BF', 0.55);
  softGlow(g, 540, 1000, 500, '#F2C6CF', 0.12);
  const a = smooth(13.75, 14.9, t);
  const blur = (1 - a) * 8;
  g.save();
  g.globalAlpha = a; g.filter = `blur(${blur.toFixed(2)}px)`;
  g.fillStyle = '#4A3426'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '500 168px CG';
  if ('letterSpacing' in g) g.letterSpacing = '6px';
  g.fillText('Yutoriba', 540, 950 - (1 - a) * 10);
  if ('letterSpacing' in g) g.letterSpacing = '0px';
  g.restore();
  const la = smooth(14.1, 15.0, t);
  g.fillStyle = `rgba(90,62,43,${0.55 * la})`;
  const lw = 140 * ease(la);
  g.fillRect(540 - lw / 2, 1075, lw, 2);
}

// =====================================================================
// effects: flare, particles, bloom, text, vignette, grain
// =====================================================================
function flare(g, x, y, k) {
  g.save(); g.globalCompositeOperation = 'lighter';
  softGlow(g, x, y, 380, '#FFD58A', 0.35 * k);
  // anamorphic streak
  const gr = g.createLinearGradient(x - 700, 0, x + 700, 0);
  gr.addColorStop(0, 'rgba(255,210,150,0)'); gr.addColorStop(0.5, `rgba(255,225,180,${0.35 * k})`); gr.addColorStop(1, 'rgba(255,210,150,0)');
  g.fillStyle = gr; g.fillRect(x - 700, y - 3, 1400, 6);
  g.globalAlpha = 0.5; g.fillRect(x - 700, y - 10, 1400, 20);
  g.globalAlpha = 1;
  // ghosts along axis through centre
  const dx = W / 2 - x, dy = H / 2 - y;
  const ghosts = [[0.5, 40, '#F2C6CF', 0.10], [0.8, 90, '#FFD58A', 0.07], [1.25, 26, '#A9C4D6', 0.12], [1.55, 140, '#F6D7B0', 0.05], [1.9, 60, '#F2C6CF', 0.08]];
  for (const [f, r, c, a] of ghosts) {
    const gx = x + dx * f, gy = y + dy * f;
    const rg = g.createRadialGradient(gx, gy, r * 0.6, gx, gy, r);
    rg.addColorStop(0, rgba(c, a * k * 0.5)); rg.addColorStop(0.85, rgba(c, a * k)); rg.addColorStop(1, rgba(c, 0));
    g.fillStyle = rg; g.beginPath(); g.arc(gx, gy, r, 0, 7); g.fill();
  }
  g.restore();
}

const DUST = [], PETALS = [];
(function initParticles() {
  const R = rng(99);
  for (let i = 0; i < 90; i++) DUST.push({ x: R() * W, y: R() * H, vx: (R() - 0.5) * 14, vy: -4 - R() * 10, s: 1 + R() * 3.2, ph: R() * 7, z: R() });
  for (let i = 0; i < 34; i++) PETALS.push({ x: R() * W * 1.4, y: R() * H, vx: -45 - R() * 40, vy: 70 + R() * 70, s: 9 + R() * 14, ph: R() * 7, spin: 0.6 + R() * 1.4, z: R() });
})();
function intensity(t, table) { // table: [[t, v], ...]
  for (let i = 0; i < table.length - 1; i++) {
    const [t0, v0] = table[i], [t1, v1] = table[i + 1];
    if (t >= t0 && t <= t1) return lerp(v0, v1, smooth(t0, t1, t));
  }
  return table[table.length - 1][1];
}
function particles(g, t) {
  const dI = intensity(t, [[0, 1], [2.7, 1], [3.3, 0.85], [8.7, 0.45], [9.3, 0.6], [11.7, 0.6], [12.3, 0.25], [13.6, 0.25], [14, 0.5], [15, 0.5]]);
  g.save(); g.globalCompositeOperation = 'lighter';
  for (const d of DUST) {
    const x = ((d.x + d.vx * t + Math.sin(t * 0.6 + d.ph) * 18) % W + W) % W;
    const y = ((d.y + d.vy * t) % H + H) % H;
    const tw = 0.55 + 0.45 * Math.sin(t * 2.2 + d.ph * 3);
    const a = dI * tw * (0.25 + 0.5 * d.z);
    const r = d.s * (1 + d.z) * 2.2;
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, `rgba(255,236,190,${a})`); gr.addColorStop(1, 'rgba(255,236,190,0)');
    g.fillStyle = gr; g.fillRect(x - r, y - r, r * 2, r * 2);
  }
  g.restore();
  const pI = intensity(t, [[0, 0.12], [2.7, 0.12], [3.3, 0], [5.6, 0], [6.4, 1], [8.7, 1], [9.3, 0.25], [11.7, 0.25], [12.3, 0.45], [13.6, 0.45], [14, 0.3], [15, 0.3]]);
  if (pI <= 0.001) return;
  const n = Math.round(PETALS.length * Math.min(1, pI + 0.2));
  for (let i = 0; i < n; i++) {
    const p = PETALS[i];
    const x = (((p.x + p.vx * t + Math.sin(t * 1.1 + p.ph) * 40) % (W + 200)) + W + 200) % (W + 200) - 100;
    const y = (((p.y + p.vy * t) % (H + 200)) + H + 200) % (H + 200) - 100;
    const s = p.s * (0.6 + p.z * 0.8);
    g.save(); g.translate(x, y); g.rotate(t * p.spin + p.ph); g.scale(1, Math.cos(t * p.spin * 1.7 + p.ph) * 0.8 + 0.2);
    g.globalAlpha = pI * (0.55 + 0.45 * p.z);
    if (p.z < 0.3) g.filter = 'blur(2px)';
    const gr = g.createLinearGradient(0, -s, 0, s); gr.addColorStop(0, '#FBE3E6'); gr.addColorStop(1, '#E9A9B7');
    g.fillStyle = gr; g.beginPath();
    g.moveTo(0, -s * 0.65);
    g.quadraticCurveTo(s * 0.15, -s, s * 0.45, -s * 0.9);
    g.quadraticCurveTo(s * 0.7, -s * 0.1, 0, s);
    g.quadraticCurveTo(-s * 0.7, -s * 0.1, -s * 0.45, -s * 0.9);
    g.quadraticCurveTo(-s * 0.15, -s, 0, -s * 0.65);
    g.fill(); g.restore();
  }
}
const bloomC = mk(270, 480), bloomG = bloomC.getContext('2d');
const bloomC2 = mk(270, 480), bloomG2 = bloomC2.getContext('2d');
function bloom(g, amt) {
  bloomG.clearRect(0, 0, 270, 480);
  bloomG.filter = 'brightness(0.85) contrast(2.2)';
  bloomG.drawImage(canvas, 0, 0, 270, 480);
  bloomG2.clearRect(0, 0, 270, 480);
  bloomG2.filter = 'blur(7px)';
  bloomG2.drawImage(bloomC, 0, 0);
  g.save(); g.globalCompositeOperation = 'screen'; g.globalAlpha = amt;
  g.drawImage(bloomC2, 0, 0, W, H); g.restore();
}
function caption(g, text, t, tin, tout, y = 860) {
  const a = smooth(tin, tin + 0.9, t) * (1 - smooth(tout - 0.5, tout, t));
  if (a <= 0) return;
  g.save();
  g.textAlign = 'center'; g.textBaseline = 'middle';
  g.font = '500 66px CG';
  if ('letterSpacing' in g) g.letterSpacing = '2px';
  const dy = (1 - smooth(tin, tin + 1.2, t)) * 14;
  g.globalAlpha = a;
  g.filter = `blur(${((1 - smooth(tin, tin + 0.8, t)) * 6).toFixed(2)}px)`;
  g.shadowColor = 'rgba(60,40,28,0.7)'; g.shadowBlur = 30;
  g.fillStyle = '#FFF7EA';
  g.fillText(text, 540, y + dy);
  g.shadowBlur = 0;
  g.fillText(text, 540, y + dy);
  g.restore();
}
function vignette(g, k) {
  const gr = g.createRadialGradient(540, 900, 500, 540, 960, 1250);
  gr.addColorStop(0, 'rgba(40,26,18,0)'); gr.addColorStop(1, `rgba(40,26,18,${k})`);
  g.fillStyle = gr; g.fillRect(0, 0, W, H);
}
const grainC = mk(512, 512);
(function () {
  const g = grainC.getContext('2d'), id = g.createImageData(512, 512), R = rng(3);
  for (let i = 0; i < id.data.length; i += 4) { const v = 128 + (R() - 0.5) * 120; id.data[i] = id.data[i + 1] = id.data[i + 2] = v; id.data[i + 3] = 255; }
  g.putImageData(id, 0, 0);
})();
function grain(g, t, a) {
  const f = Math.floor(t * 30);
  const R = rng(1000 + f);
  g.save(); g.globalCompositeOperation = 'overlay'; g.globalAlpha = a;
  const ox = -Math.floor(R() * 512), oy = -Math.floor(R() * 512);
  for (let x = ox; x < W; x += 512) for (let y = oy; y < H; y += 512) g.drawImage(grainC, x, y);
  g.restore();
}

// =====================================================================
// timeline
// =====================================================================
let L = null;
window.init = function () {
  L = {
    station: makeLayer(W, H, 1.15, buildStation),
    cafeBG: makeLayer(S2W, H, 1, buildCafeBG, 5),
    reader: makeLayer(S2W, H, 1, buildReader, 3),
    table: makeLayer(S2W, H, 1, buildTable),
    streetSky: makeLayer(W, S3H, 1, buildStreetSky, 2),
    midTrees: makeLayer(W, S3H, 1, buildMidTrees, 3),
    bookstore: makeLayer(W, S3H, 1, buildBookstore, 0.6),
    fgTrees: makeLayer(W, S3H, 1, buildFgTrees, 1.2),
    cafeIn: makeLayer(W, H, 1.1, buildCafeInterior, 6),
    cafeTable: makeLayer(W, H, 1.1, buildCafeTable, 1.5),
    winFrame: makeLayer(W, H, 1.1, buildWindowFrame, 7),
    dusk: makeLayer(W, H, 1.25, buildDusk),
  };
  return true;
};

const SCENES = [
  { a: 0, b: 3, fn: (g, t) => scene1(g, t) },
  { a: 3, b: 6, fn: (g, t) => scene2(g, t - 3 + 0.35) },
  { a: 6, b: 9, fn: (g, t) => scene3(g, t - 6 + 0.35) },
  { a: 9, b: 12, fn: (g, t) => scene4(g, t - 9 + 0.35) },
  { a: 12, b: 13.9, fn: (g, t) => scene5(g, t) },
  { a: 13.9, b: 15.1, fn: (g, t) => wordmark(g, t) },
];
const XF = 0.7; // crossfade length
const buf = mk(W, H), bufG = buf.getContext('2d');
window.renderFrame = function (t) {
  ctx.save();
  ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < SCENES.length; i++) {
    const s = SCENES[i];
    const start = i === 0 ? -1 : s.a - XF / 2, end = i === SCENES.length - 1 ? 99 : s.b + XF / 2;
    if (t < start || t > end) continue;
    const xf = i === SCENES.length - 1 ? 0.9 : XF;
    const a = i === 0 ? 1 : smooth(s.a - xf / 2, s.a + xf / 2, t);
    if (a >= 0.999) { ctx.save(); s.fn(ctx, t); ctx.restore(); }
    else {
      bufG.save(); bufG.clearRect(0, 0, W, H); s.fn(bufG, t); bufG.restore();
      ctx.save(); ctx.globalAlpha = a; ctx.drawImage(buf, 0, 0); ctx.restore();
    }
  }
  particles(ctx, t);
  const finalA = smooth(13.45, 14.35, t);
  bloom(ctx, 0.32 * (1 - finalA * 0.6));
  caption(ctx, 'Is this everything?', t, 0.9, 3.05, 600);
  caption(ctx, 'There may be more.', t, 6.7, 9.05, 400);
  caption(ctx, "Let's find out together.", t, 9.6, 12.05, 250);
  vignette(ctx, lerp(0.42, 0.12, finalA));
  // global fades
  const fin = 1 - smooth(0, 0.6, t);
  if (fin > 0) { ctx.fillStyle = `rgba(20,14,10,${fin})`; ctx.fillRect(0, 0, W, H); }
  grain(ctx, t, 0.07);
  ctx.restore();
  return true;
};
