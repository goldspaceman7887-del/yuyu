// Characters: Sora (face + back views), Aoi (face), Ren (profile, silhouette)
'use strict';

// One eye. fl=+1 for viewer-left eye (inner corner on right), -1 for viewer-right eye.
function eye(c, cx, cy, w, fl, o) {
  const open = (1 - (o.blink || 0)) * (1 - (o.down || 0) * .45);
  const h = w * .25 * open;
  const inner = [cx + fl * w * .5, cy + 3], outer = [cx - fl * w * .52, cy + 7];
  const top = [cx + fl * w * .02, cy - h - 2], bot = [cx - fl * w * .05, cy + w * .2];
  const upper = [inner, [cx + fl * w * .28, cy - h * .78], top, [cx - fl * w * .3, cy - h * .7 + 2], outer];
  const lower = [outer, [cx - fl * w * .2, cy + w * .13], bot, [cx + fl * w * .3, cy + w * .1], inner];
  // iris clipped to opening
  if (open > .12) {
    c.save(); path(c, [...upper, ...lower.slice(1, -1)], true, 8); c.clip();
    c.fillStyle = o.skin || 'rgba(0,0,0,0)'; c.fill();
    const lx = (o.look ? o.look[0] : 0) * w * .18, ly = (o.look ? o.look[1] : 0) * w * .12 + (o.down || 0) * w * .14;
    const ir = w * .2;
    c.fillStyle = C.ink; c.beginPath(); c.arc(cx + lx, cy + w * .07 + ly, ir, 0, 7); c.fill();
    c.fillStyle = C.tDark; c.beginPath(); c.arc(cx + lx, cy + w * .07 + ly, ir * .62, 0, 7); c.fill();
    c.fillStyle = C.ink; c.beginPath(); c.arc(cx + lx, cy + w * .07 + ly, ir * .36, 0, 7); c.fill();
    c.fillStyle = C.paper; c.beginPath(); c.arc(cx + lx + ir * .3 * fl, cy + ly - ir * .05, ir * .13, 0, 7); c.fill();
    // lid shadow
    c.fillStyle = 'rgba(17,17,17,.35)'; path(c, [...upper, [cx, cy - h * .2]], true, 6); c.fill();
    c.restore();
  }
  // upper lid line: heavier toward outer corner
  const ul = upper.slice().reverse().map((p, i) => [p[0], p[1], [1.6, 1.3, 1, .7, .45][i]]);
  brush(c, open > .12 ? ul : [outer, [cx, cy + w * .1], inner], w * .085, { min: .35 });
  if (open > .12) brush(c, [[outer[0] + fl * w * .1, outer[1] + 2], [cx - fl * w * .15, cy + w * .2], [cx + fl * w * .2, cy + w * .17]], w * .03, { alpha: .8 });
  // hidden double-eyelid crease (outer half) + lashes
  brush(c, [[cx + fl * w * .1, cy - h - w * .1], [cx - fl * w * .2, cy - h * .9 - w * .1], [cx - fl * w * .45, cy - w * .04]], w * .028, { alpha: .85 });
  brush(c, [[outer[0], outer[1]], [outer[0] - fl * w * .08, outer[1] - w * .02]], w * .05);
  // tiredness: under-eye hatch
  if (o.tired) brush(c, [[cx - fl * w * .3, cy + w * .32], [cx + fl * w * .05, cy + w * .36], [cx + fl * w * .3, cy + w * .3]], w * .022, { alpha: .6 });
}

/* drawFace: face units — eyes on y=0, face height ~ -270..280.
   o: {x,y,s, who:'sora'|'aoi', blink, look:[x,y], down, skin, alpha, shade:true, rot} */
function drawFace(c, o) {
  c.save(); c.translate(o.x, o.y); c.rotate(o.rot || 0); c.scale(o.s, o.s);
  if (o.alpha !== undefined) c.globalAlpha *= o.alpha;
  const sora = o.who !== 'aoi', d = o.down || 0, fy = d * 22; // features shift down when head bows
  const skin = o.skin || null;
  const faceCtrl = [[-168, -130], [-172, -20], [-160, 92], [-118, 196], [-55, 256], [2, 274], [62, 254], [124, 192], [166, 82], [178, -30], [174, -130], [100, -176], [0, -186], [-100, -176]];
  hairBack(c, sora);
  // neck
  if (skin) { c.fillStyle = skin; c.fillRect(-72, 200, 150, 200); }
  brush(c, [[-62, 236], [-66, 320], [-74, 400]], 6, { taper: 'end' });
  brush(c, [[70, 226], [74, 320], [84, 400]], 6, { taper: 'end' });
  c.save(); c.beginPath(); c.rect(-75, 230, 160, 170); c.clip(); c.fillStyle = tone(c, .35, 6); path(c, [[-75, 240], [0, 300], [85, 236], [85, 300], [-75, 310]]); c.fill(); c.restore();
  // skin + jaw line
  path(c, faceCtrl); if (skin) { c.fillStyle = skin; c.fill(); }
  if (o.shade !== false) { // shadow side (viewer-left), screentone
    c.save(); path(c, faceCtrl); c.clip(); c.fillStyle = tone(c, .28, 6);
    path(c, [[-200, -200], [-120, -200], [-128, -60], [-110, 60], [-80, 170], [-20, 290], [-200, 300]]); c.fill();
    c.fillStyle = tone(c, .18, 6); path(c, [[-30, -20], [-14, 20], [-12, 96], [-26, 108], [-34, 50]]); c.fill(); // nose side
    c.restore();
  }
  brush(c, [[-169, -40], [-162, 90], [-120, 196], [-56, 256], [2, 274], [62, 254], [124, 192], [166, 82], [178, -40]], 7, { min: .3 });
  if (!sora) { // ear (viewer-right, tucked hair) + stud earring
    fillShape(c, [[168, -30], [196, -44], [206, 0], [196, 50], [172, 70]], skin || C.paper);
    brush(c, [[170, -32], [198, -44], [208, 4], [194, 52], [170, 72]], 5, { min: .4 });
    brush(c, [[184, -18], [194, 10], [182, 40]], 3);
    c.fillStyle = C.tLight; c.beginPath(); c.arc(184, 80, 8, 0, 7); c.fill(); brush(c, [[176, 74], [190, 74], [190, 86], [176, 86], [176, 74]], 2.5, { taper: false });
  }
  c.save(); c.translate(0, fy);
  // brows
  if (sora) { brush(c, [[-140, -62], [-100, -66], [-48, -60]], 7, { min: .3 }); brush(c, [[38, -60], [90, -66], [138, -60]], 7, { min: .3 }); }
  else { brush(c, [[-138, -58], [-96, -74], [-50, -64]], 6.5, { min: .3 }); brush(c, [[40, -64], [88, -76], [134, -58]], 6.5, { min: .3 }); }
  eye(c, -88, 0, 92, 1, { ...o, tired: sora, skin });
  eye(c, 82, 0, 96, -1, { ...o, tired: sora, skin });
  if (!sora) { // full double-eyelid crease
    brush(c, [[-128, -18], [-88, -40 + d * 12], [-46, -22]], 3, { alpha: .9 }); brush(c, [[42, -22], [84, -42 + d * 12], [128, -16]], 3, { alpha: .9 });
  }
  // nose
  brush(c, [[-8, 30], [-14, 80], [-4, 112]], 4.5, { alpha: .9 });
  brush(c, [[-30, 118], [-10, 126], [14, 120]], 4, { min: .3 });
  // mouth
  if (sora) brush(c, [[-40, 176], [-6, 174], [34, 171]], 5.5, { min: .3 });
  else brush(c, [[-40, 172], [-8, 176], [30, 168]], 5.5, { min: .3 });
  brush(c, [[-16, 200], [6, 202], [22, 198]], 3.5, { alpha: .7 });
  if (sora) { c.fillStyle = C.ink; c.beginPath(); c.arc(52, 196, 5, 0, 7); c.fill(); } // mole: below character's left mouth corner
  c.restore();
  hairFront(c, sora);
  c.restore();
}

function strand(c, pts, w, col = C.ink) { brush(c, pts, w, { min: .05, taper: 'end', color: col }); }
function hairBack(c, sora) {
  c.fillStyle = C.ink;
  if (sora) {
    path(c, [[-205, -150], [-120, -255], [0, -288], [130, -258], [212, -150], [224, 0], [210, 110], [0, 140], [-210, 110], [-222, 0]]); c.fill();
    const r = rng(5);
    for (let i = 0; i < 12; i++) { const x = -214 + i * 9; strand(c, [[x + 10, 40], [x - 2 + r() * 6, 180], [x - 10 + r() * 16, 270 + r() * 50]], 28); }
    for (let i = 0; i < 12; i++) { const x = 214 - i * 9; strand(c, [[x - 10, 40], [x + 2 - r() * 6, 180], [x + 10 - r() * 16, 260 + r() * 50]], 28); }
  } else {
    path(c, [[-205, -160], [-120, -262], [5, -292], [140, -255], [205, -150], [214, 0], [200, 100], [150, 150], [-200, 260], [-236, 120], [-230, -40]]); c.fill();
    const r = rng(6);
    for (let i = 0; i < 11; i++) { const x = -236 + i * 14; strand(c, [[x + 16, 0], [x - 4, 220], [x + 30 + r() * 20, 360 + r() * 24], [x + 60, 372]], 40); }
    for (let i = 0; i < 6; i++) { const x = 205 - i * 10; strand(c, [[x - 10, 0], [x + 4, 120], [x - 20, 170 + r() * 20]], 34); }
  }
}
function hairFront(c, sora) {
  c.fillStyle = C.ink;
  if (sora) {
    path(c, [[-218, -80], [-206, -190], [-118, -262], [10, -282], [150, -244], [222, -130], [214, -80], [100, -160], [-30, -190], [-150, -150]]); c.fill();
    // fringe strands from a part just left of centre
    const tips = [[-206, -40], [-184, -70], [-160, -46], [-132, -84], [-96, -20], [-70, -78], [-40, -92], [-6, -70], [30, -100], [64, -78], [100, -104], [134, -72], [166, -96], [196, -54], [214, -20]];
    tips.forEach(([tx, ty], i) => { const rx = -30 + (tx + 30) * .35, ry = -250; strand(c, [[rx, ry], [lerp(rx, tx, .55) + (tx < -30 ? -14 : 14), lerp(ry, ty, .55)], [tx, ty]], i === 4 ? 30 : 52); });
    // side locks over the ears
    for (let k = 0; k < 4; k++) { strand(c, [[-196 + k * 6, -170], [-214 + k * 10, -20], [-200 + k * 14, 120 - k * 30], [-182 + k * 18, 200 - k * 50]], 30); strand(c, [[196 - k * 6, -170], [214 - k * 10, -20], [204 - k * 14, 120 - k * 30], [188 - k * 18, 196 - k * 50]], 30); }
    for (const s of [[[-150, -215], [-90, -245], [-20, -255]], [[40, -250], [110, -232], [160, -200]], [[-80, -200], [-100, -140], [-110, -80]], [[120, -200], [150, -150], [170, -110]]]) brush(c, s, 5, { color: C.paper, alpha: .7 });
  } else {
    path(c, [[-218, -60], [-206, -194], [-110, -266], [20, -284], [150, -240], [196, -150], [190, -80], [120, -170], [0, -200], [-150, -150]]); c.fill();
    // side-swept fringe from a part at right, sweeping to the viewer-left
    for (let i = 0; i < 9; i++) { const t = i / 8; strand(c, [[80, -250], [lerp(10, -120, t), lerp(-210, -150, t)], [lerp(-40, -210, t), lerp(-120, -10 + t * 30, t)]], 54); }
    strand(c, [[120, -240], [176, -170], [186, -70]], 40);
    for (const s of [[[-150, -205], [-80, -242], [10, -256]], [[60, -238], [120, -214], [160, -170]], [[30, -200], [-60, -170], [-150, -110]]]) brush(c, s, 5, { color: C.paper, alpha: .65 });
  }
}

// Shirt collar + coat shoulders under a face (face units, same transform as drawFace)
function drawBust(c, o) {
  c.save(); c.translate(o.x, o.y); c.scale(o.s, o.s); if (o.alpha !== undefined) c.globalAlpha *= o.alpha;
  const coat = o.coat || tone(c, .32, 7);
  path(c, [[-90, 380], [-300, 440], [-470, 560], [-520, 900], [520, 900], [480, 560], [300, 440], [100, 380], [0, 520]]);
  c.fillStyle = coat; c.fill();
  if (o.shirt !== false) { fillShape(c, [[-96, 370], [-40, 360], [0, 400], [44, 358], [100, 366], [60, 520], [0, 560], [-60, 520]], o.shirtFill || C.paper); brush(c, [[-96, 372], [-40, 420], [0, 404], [40, 420], [100, 368]], 5); }
  brush(c, [[-90, 380], [-300, 440], [-470, 560], [-520, 880]], 8, { min: .3 });
  brush(c, [[100, 380], [300, 440], [480, 560], [520, 880]], 8, { min: .3 });
  brush(c, [[-96, 372], [-150, 520], [-120, 900]], 6); brush(c, [[100, 368], [150, 520], [118, 900]], 6);
  c.restore();
}

// Sora seen from behind / three-quarter back, standing. (x,y)=feet center, hgt = figure height px
function soraBackStanding(c, x, y, hgt, f, o = {}) {
  const s = hgt / 300; c.save(); c.translate(x, y); c.scale(s, s);
  const wind = Math.sin(f * .21) * .5 + Math.sin(f * .53 + 1) * .5; // -1..1
  // legs + sneakers
  fillShape(c, [[-26, -130], [-6, -130], [-8, -10], [-24, -10]], C.deep); fillShape(c, [[4, -130], [24, -130], [24, -10], [8, -10]], C.deep);
  fillShape(c, [[-30, -12], [-4, -12], [-2, 2], [-32, 2]], C.paper); brush(c, [[-32, 2], [-30, -12], [-4, -12], [-2, 2], [-32, 2]], 2, { taper: false });
  fillShape(c, [[6, -12], [28, -12], [30, 2], [4, 2]], C.paper); brush(c, [[4, 2], [6, -12], [28, -12], [30, 2], [4, 2]], 2, { taper: false });
  // coat
  const hem = [[-50 - wind * 4, -110], [-20, -104 + wind * 3], [10, -106], [44 + wind * 10, -112 - wind * 3]];
  path(c, [[-34, -250], [-44, -232], [-48, -180], ...hem, [40, -180], [38, -232], [30, -252], [0, -258]]);
  c.fillStyle = C.tMid; c.fill(); c.fillStyle = tone(c, .3, 4); c.fill();
  c.save(); path(c, [[-34, -250], [-48, -180], ...hem, [40, -180], [30, -252]]); c.clip(); hatch(c, null, -60, -260, 120, 160, 1.35, 9, 1.4, { alpha: .6, seed: 3 }); c.restore();
  brush(c, [[-34, -250], [-44, -232], [-48, -180], hem[0]], 3); brush(c, [[30, -252], [38, -232], [40, -180], hem[3]], 3);
  brush(c, hem, 2.5, { taper: false });
  brush(c, [[-4, -240], [-8, -170], [-12, -108]], 1.6, { alpha: .8 });
  // arms
  brush(c, [[-40, -236], [-52, -190], [-54, -150]], 2.4); brush(c, [[34, -236], [46, -190], [48, -150]], 2.4);
  // bag strap on right shoulder (viewer right in back view) + olive bag
  brush(c, [[26, -250], [0, -200], [-30, -150]], 3.2, { taper: false, color: C.tDark });
  fillShape(c, [[-46, -158], [-16, -160], [-14, -126], [-48, -124]], C.tDark); brush(c, [[-46, -158], [-16, -160], [-14, -126], [-48, -124], [-46, -158]], 2, { taper: false });
  // head (back, slight turn to look up-left)
  c.save(); c.translate(-2, -282); c.rotate(-.12);
  fillShape(c, [[-20, -18], [-6, -28], [12, -26], [22, -10], [22, 12], [14, 26], [-12, 28], [-22, 12]], C.ink);
  fillShape(c, [[-22, -4], [-30, 2], [-28, 10], [-20, 12]], C.paper); brush(c, [[-22, -6], [-31, 2], [-28, 12], [-20, 14]], 1.6);
  for (let i = 0; i < 4; i++) brush(c, [[10 + i * 3, 18 + i * 2], [20 + i * 4 + wind * 6, 22 + i * 3], [28 + i * 3 + wind * 10, 18 + i * 4]], 2.2 - i * .3);
  c.restore();
  c.restore();
}

// Sora seated, seen from behind-left (night window). (x,y) = seat point
function soraSeatedBack(c, x, y, s) {
  c.save(); c.translate(x, y); c.scale(s, s);
  path(c, [[-120, 0], [-130, -160], [-100, -270], [-40, -300], [40, -300], [100, -268], [126, -150], [120, 0]]);
  c.fillStyle = C.tDark; c.fill(); c.fillStyle = tone(c, .45, 6); c.fill();
  brush(c, [[-120, 0], [-130, -160], [-100, -270], [-40, -300]], 5); brush(c, [[40, -300], [100, -268], [126, -150], [120, 0]], 5);
  brush(c, [[-10, -296], [-4, -170], [0, -20]], 2.5, { alpha: .6 });
  // head
  fillShape(c, [[-68, -300], [-80, -370], [-56, -440], [0, -464], [56, -446], [82, -380], [74, -300], [30, -280], [-30, -282]], C.ink);
  fillShape(c, [[-80, -372], [-96, -360], [-92, -330], [-76, -322]], C.tLight);
  brush(c, [[-30, -440], [10, -452], [50, -430]], 4, { color: C.tMid, alpha: .6 });
  c.restore();
}

// Ren in profile facing right, seated at desk (local origin = shoulder), unit ~ px
function renProfile(c, x, y, s, f) {
  c.save(); c.translate(x, y); c.scale(s, s);
  // torso (white shirt)
  fillShape(c, [[-40, 0], [40, -6], [70, 40], [80, 200], [-60, 210], [-70, 60]], C.paper);
  brush(c, [[-40, 0], [-70, 60], [-62, 210]], 4); brush(c, [[40, -6], [70, 40], [78, 200]], 4);
  brush(c, [[10, 30], [20, 110], [10, 190]], 1.8, { alpha: .5 }); brush(c, [[-30, 50], [-20, 140]], 1.6, { alpha: .4 });
  // tie
  fillShape(c, [[42, -2], [56, 6], [62, 110], [50, 122], [40, 108]], C.deep);
  // neck + head
  fillShape(c, [[-10, -40], [30, -44], [36, 0], [-14, 6]], C.paper); brush(c, [[30, -44], [36, 2]], 3); brush(c, [[-10, -40], [-14, 6]], 3);
  const head = [[-48, -110], [-40, -160], [0, -182], [44, -170], [62, -142], [66, -118], [80, -104], [70, -94], [72, -80], [66, -70], [70, -60], [56, -50], [30, -44], [-10, -46], [-40, -70]];
  fillShape(c, head, C.paper); brush(c, head.slice(4, 13), 3.2, { min: .4 });
  c.save(); path(c, head); c.clip(); c.fillStyle = tone(c, .22, 5); c.fillRect(-60, -190, 50, 160); c.restore();
  // hair 7:3, neat
  fillShape(c, [[-52, -100], [-50, -160], [-14, -192], [36, -188], [66, -156], [60, -140], [30, -150], [0, -146], [-20, -130], [-30, -100]], C.ink);
  brush(c, [[-30, -170], [10, -184], [50, -168]], 3, { color: C.paper, alpha: .6 });
  // ear, eye, brow
  brush(c, [[-16, -120], [-4, -128], [2, -110], [-6, -92]], 2.6);
  brush(c, [[44, -118], [58, -116]], 3.6); brush(c, [[40, -132], [60, -134]], 3.2);
  brush(c, [[46, -106], [56, -104]], 1.4, { alpha: .6 }); // fatigue line
  // arm to keyboard + watch
  brush(c, [[10, 20], [30, 110], [90, 150], [150, 150]], 34, { taper: false, color: C.paper });
  brush(c, [[10, 6], [24, 110], [86, 140], [150, 138]], 3); brush(c, [[-4, 40], [20, 130], [86, 164], [150, 164]], 3);
  fillShape(c, [[120, 134], [134, 132], [136, 168], [122, 170]], C.tMid); brush(c, [[120, 134], [134, 132], [136, 168], [122, 170], [120, 134]], 2.4, { taper: false });
  fillShape(c, [[150, 136], [178, 146], [174, 166], [150, 164]], C.paper); brush(c, [[150, 136], [178, 146], [174, 166], [150, 164]], 2.4);
  c.restore();
}

// Palm-down relaxed hand, fingers pointing to local -y. Outline via ink-then-skin double stroke.
function handTop(c, x, y, s, rot, o = {}) {
  const skin = o.skin || '#E9E4DA';
  c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s);
  const fingers = [[-48, -40, 140, -.12], [-16, -48, 158, -.03], [16, -44, 146, .05], [44, -30, 112, .14]];
  const fp = fingers.map(([fx, fy, len, a]) => [[fx, fy], [fx + Math.sin(a) * len * .5, fy - len * .5], [fx + Math.sin(a) * len, fy - len * (o.curl ? .8 : 1)]]);
  fp.forEach((p, i) => brush(c, p, i === 3 ? 34 : 38, { taper: false, color: C.ink }));
  fp.forEach((p, i) => brush(c, p, i === 3 ? 27 : 31, { taper: false, color: skin }));
  fp.forEach(p => { const t = p[2]; brush(c, [[t[0] - 9, t[1] + 14], [t[0], t[1] + 6], [t[0] + 9, t[1] + 14]], 2.4, { taper: false, alpha: .7 }); });
  const th = [[-60, 40], [-104, 0], [-132, -48]]; brush(c, th, 40, { taper: false }); brush(c, th, 33, { taper: false, color: skin });
  const palm = [[-66, -40], [-20, -58], [30, -54], [62, -30], [70, 50], [50, 150], [-40, 160], [-74, 60]];
  fillShape(c, palm, skin); brush(c, [[62, -30], [70, 50], [50, 150]], 4.5, { min: .4 }); brush(c, [[-74, 60], [-40, 160]], 4.5, { min: .4 });
  for (const [kx] of fingers) brush(c, [[kx - 10, -36], [kx, -42], [kx + 10, -36]], 2.2, { alpha: .6 });
  c.save(); path(c, palm); c.clip(); c.fillStyle = tone(c, .22, 6); c.fillRect(20, -60, 80, 240); c.restore();
  if (o.sleeve !== false) { const sl = [[-80, 130], [70, 120], [110, 400], [-110, 420]]; fillShape(c, sl, C.tMid); c.save(); path(c, sl); c.clip(); c.fillStyle = tone(c, .32, 5); c.fillRect(-120, 100, 260, 340); hatch(c, null, -120, 110, 240, 300, 1.2, 11, 1.3, { alpha: .5, seed: 8 }); c.restore(); brush(c, [[-80, 130], [70, 120]], 4); brush(c, [[-80, 130], [-110, 420]], 4); brush(c, [[70, 120], [110, 400]], 4); }
  c.restore();
}
