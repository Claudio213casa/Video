"""Flat 2D bean-head renderer for the zombie-cafe short. 1080x1920@30."""
import json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont
from functools import lru_cache

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
PW, PH = 2048, 2816
GROUND = 2320
FPS = 30
PLUM = (96, 36, 80)
DARKSEAM = (60, 24, 52)

FONT_B = os.path.join(ROOT, 'assets', 'DejaVuSans-Bold.ttf')
FONT_R = os.path.join(ROOT, 'assets', 'DejaVuSans.ttf')
fnt_cache = {}
def font(sz, bold=True):
    key = (sz, bold)
    if key not in fnt_cache:
        fnt_cache[key] = ImageFont.truetype(FONT_B if bold else FONT_R, sz)
    return fnt_cache[key]

PHR = json.load(open(os.path.join(ROOT, 'work', 'phrases.json'), encoding='utf-8'))
PRAS = PHR['phrases']
NFRAMES = PHR['frames']

def p0(i): return PRAS[i]['f0']
def p1(i): return PRAS[i]['f1']

def ss(t):  # smootherstep 0..1
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)

def lerp(a, b, t): return a + (b - a) * t

def ease_prop(f, a, b, d0=18, over=6.0):
    """easeOut 0..1 over d0 frames, small overshoot."""
    if f < a: return 0.0
    t = (f - a) / max(1, d0)
    if t >= 1: return 1.0
    return 1.0 + over * math.exp(-6 * t) * math.sin(6.2 * t) * (t < 1) if t < 1 else 1.0

def out_back(f, a, d):
    if f < a: return 0.0
    t = min(1.0, (f - a) / max(1, d))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

class Cam:
    def __init__(self, keys, roll=0.0):
        self.keys = keys
        self.roll = roll
    def at(self, f):
        k = self.keys
        if f <= k[0][0]: px, py, z = k[0][1], k[0][2], k[0][3]
        elif f >= k[-1][0]: px, py, z = k[-1][1], k[-1][2], k[-1][3]
        else:
            for i in range(len(k) - 1):
                if k[i][0] <= f <= k[i + 1][0]:
                    t = ss((f - k[i][0]) / max(1, k[i + 1][0] - k[i][0]))
                    px = lerp(k[i][1], k[i + 1][1], t)
                    py = lerp(k[i][2], k[i + 1][2], t)
                    z = lerp(k[i][3], k[i + 1][3], t)
                    break
        px += 7 * math.sin(2 * math.pi * f / 700.0)
        py += 5 * math.sin(2 * math.pi * f / 520.0 + 1.0)
        z *= 1.0 + 0.004 * math.sin(2 * math.pi * f / 900.0)
        return px, py, z
    def crop_box(self, f):
        px, py, z = self.at(f)
        cw, ch = W / z, H / z
        x0 = min(max(px - cw / 2, 0), PW - cw)
        y0 = min(max(py - ch / 2, 0), PH - ch)
        return x0, y0, cw, ch

def apply_cam(plate, cam, f):
    x0, y0, cw, ch = cam.crop_box(f)
    img = plate.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
    if abs(cam.roll) > 0.05:
        img = img.rotate(cam.roll, resample=Image.BICUBIC, fillcolor=(24, 22, 30))
    return img

# ---------------------------------------------------------------- painters
def vgrad(d, x0, y0, x1, y1, c0, c1, step=6):
    for y in range(int(y0), int(y1), step):
        t = (y - y0) / max(1, (y1 - y0))
        c = tuple(int(lerp(c0[i], c1[i], t)) for i in range(3))
        d.rectangle([x0, y, x1, y + step], fill=c)

def cloud(d, x, y, w, base):
    lo = tuple(max(0, c - 18) for c in base)
    d.ellipse([x - w * .5, y - w * .16, x + w * .5, y + w * .16], fill=base, outline=lo, width=3)
    d.ellipse([x - w * .25, y - w * .30, x + w * .28, y + w * .02], fill=base)
    d.ellipse([x + w * .05, y - w * .24, x + w * .42, y - w * .02], fill=base)

def hills(d, yb, col, seed):
    r = random.Random(seed)
    xs = [-200]
    while xs[-1] < PW + 200:
        wdt = r.randint(300, 560); hgt = r.randint(140, 300)
        x = xs[-1] + wdt // 2
        d.ellipse([x - wdt, yb - hgt, x + wdt, yb + hgt], fill=col, outline=tuple(max(0, c - 30) for c in col), width=4)
        xs.append(xs[-1] + int(wdt * 1.05))

def house(d, x, ybase, w, h, wall, roof, seed, two_floor=False):
    r = random.Random(seed)
    seam = tuple(max(0, c - 46) for c in wall)
    d.rectangle([x, ybase - h, x + w, ybase], fill=wall, outline=seam, width=4)
    d.line([x, ybase - h, x + w, ybase - h], fill=seam, width=4)
    rh = h * 0.45
    d.polygon([(x - w * .08, ybase - h), (x + w * 1.08, ybase - h), (x + w * .5, ybase - h - rh)],
              fill=roof, outline=tuple(max(0, c - 40) for c in roof))
    d.polygon([(x - w * .08, ybase - h), (x + w * .5, ybase - h - rh), (x + w * .5, ybase - h)], fill=tuple(max(0, c - 22) for c in roof))
    wy = ybase - h + h * .18
    for wxp in (x + w * .2, x + w * .68):
        d.rectangle([wxp, wy, wxp + w * .16, wy + h * .22], fill=(70, 66, 88), outline=seam, width=3)
        d.line([wxp + w * .08, wy, wxp + w * .08, wy + h * .22], fill=seam, width=2)
    if two_floor:
        wy2 = wy - h * .42
        d.rectangle([x + w * .2, wy2, x + w * .36, wy2 + h * .2], fill=(70, 66, 88), outline=seam, width=3)
        d.rectangle([x + w * .62, wy2, x + w * .78, wy2 + h * .2], fill=(70, 66, 88), outline=seam, width=3)
    dx = x + w * .42
    d.rectangle([dx, ybase - h * .42, dx + w * .2, ybase], fill=tuple(max(0, c - 60) for c in wall), outline=seam, width=3)

def tree(d, x, ybase, s, seed=0):
    d.rectangle([x - s * .06, ybase - s * .9, x + s * .06, ybase], fill=(122, 88, 64), outline=(86, 60, 44), width=3)
    r = random.Random(seed)
    for i in range(3):
        cx = x + r.randint(-int(s * .18), int(s * .18))
        cy = ybase - s * (1.0 + .16 * i)
        rr = s * (.42 - .07 * i)
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=(122, 164, 110), outline=(88, 124, 80), width=4)

def road(d, y0, col=(150, 152, 160), horizon=2360):
    d.rectangle([0, y0, PW, PH], fill=col)
    d.rectangle([0, y0, PW, y0 + 26], fill=tuple(max(0, c - 26) for c in col))
    for x in range(-100, PW + 200, 260):
        d.rectangle([x, y0 + 150, x + 120, y0 + 190], fill=(210, 208, 196))

def outlined_rect(d, box, fill, w=4, seamoff=-46):
    seam = tuple(max(0, c + seamoff) for c in fill)
    d.rectangle(box, fill=fill, outline=seam, width=w)

def cushion(d, box, fill):
    seam = tuple(max(0, c - 40) for c in fill)
    hi = tuple(min(255, c + 22) for c in fill)
    d.rounded_rectangle(box, radius=26, fill=fill, outline=seam, width=4)
    d.rounded_rectangle([box[0] + 10, box[1] + 8, box[2] - 10, (box[1] + box[3]) / 2], radius=18, fill=hi)

def lamp(d, x, ybase, s, on=False):
    d.rectangle([x - s * .04, ybase - s, x + s * .04, ybase], fill=(90, 92, 104), outline=(60, 62, 72), width=3)
    d.ellipse([x - s * .14, ybase - s - s * .2, x + s * .14, ybase - s + s * .04],
              fill=(255, 236, 160) if on else (130, 134, 148), outline=(60, 62, 72), width=3)

# ------------------------------------------------------------- characters
def _capsule(d, p0_, p1_, wid, fill, outline=PLUM, ow=None):
    ow = ow or max(3, wid * 0.30)
    d.line([p0_, p1_], fill=outline, width=int(wid + ow * 2))
    d.line([p0_, p1_], fill=fill, width=int(wid))
    r = wid / 2
    for p in (p0_, p1_):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)
    r2 = (wid + ow * 2) / 2
    for p in (p0_, p1_):
        d.ellipse([p[0] - r2, p[1] - r2, p[0] + r2, p[1] + r2], outline=outline, width=max(2, int(ow)))
def _capsule2(d, p0_, p1_, wid, fill, outline=PLUM):
    d.line([p0_, p1_], fill=outline, width=int(wid * 1.5))
    d.line([p0_, p1_], fill=fill, width=int(wid))
    r2, r = wid * .75, wid / 2
    for p in (p0_, p1_):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)
        d.ellipse([p[0] - r2, p[1] - r2, p[0] + r2, p[1] + r2], fill=fill)

POSES = dict(hang=((0.25, 0.97), (-0.25, 0.97)), hip=((0.15, 0.75), (-0.45, 0.85)),
             up=((0.45, -0.90), (-0.45, -0.90)), point=((0.97, -0.05), (-0.25, 0.97)),
             push=((0.92, 0.10), (0.92, 0.10)), reach=((0.85, -0.30), (-0.25, 0.97)),
             cross=((-0.60, 0.75), (0.60, 0.75)), wave=((0.50, -0.88), (-0.25, 0.97)))

def bean(d, x, y, s, cfg, f):
    """x,y = soles center. s = full height."""
    flip = cfg.get('flip', 1)
    expr = cfg.get('expr', 'tired')
    pose = cfg.get('pose', 'hang')
    walkph = cfg.get('walkph')
    lean = cfg.get('lean', 0.0)
    skin = cfg.get('skin', (243, 203, 164))
    shirt = cfg.get('shirt', (126, 190, 214))
    hair = cfg.get('hair', (74, 54, 40))
    seed = cfg.get('seed', 0)
    ow = max(4, s * 0.035)
    bob = 0.0
    if walkph is not None:
        bob = abs(math.sin(walkph)) * s * 0.035
    else:
        bob = math.sin(f * 0.075 + seed) * s * 0.012
    hy = y - s * 0.25 - bob
    hr = s * 0.30
    hcx, hcy = x + lean * s * 0.1, hy - s * 0.30
    # legs
    if walkph is not None:
        sw = math.sin(walkph) * s * 0.055
        f1 = (x - s * 0.07 + sw, y - abs(math.sin(walkph)) * s * 0.05)
        f2 = (x + s * 0.07 - sw, y - abs(math.sin(walkph + math.pi)) * s * 0.05)
    else:
        f1 = (x - s * 0.075, y); f2 = (x + s * 0.075, y)
    for foot, hipx in ((f1, x - s * 0.055), (f2, x + s * 0.055)):
        _capsule2(d, (hipx, y - s * 0.30 - bob), foot, s * 0.075, tuple(max(0, c - 25) for c in skin))
        d.ellipse([foot[0] - s * 0.075, foot[1] - s * 0.045, foot[0] + s * 0.075, foot[1]], fill=cfg.get('shoe', (70, 50, 60)), outline=PLUM, width=max(2, int(ow * .6)))
    # body
    br = s * 0.25
    bcx, bcy = x, hy - br * 0.25
    d.ellipse([bcx - br, bcy - br * 1.15, bcx + br, bcy + br * 1.35], fill=shirt, outline=PLUM, width=int(ow))
    d.line([bcx, bcy - br * 1.05, bcx, bcy + br * 1.2], fill=tuple(max(0, c - 26) for c in shirt), width=max(2, int(ow * .5)))
    # arms
    if walkph is not None:
        for sx0, off in ((bcx - br * .8, math.pi), (bcx + br * .8, 0.0)):
            swing = math.sin(walkph + off) * s * 0.16
            _capsule(d, (sx0, bcy - br * 0.5), (sx0 + swing * flip, bcy - br * 0.5 + s * 0.16), s * 0.075, shirt)
    else:
        a0, a1 = POSES.get(pose, POSES['hang'])
        shorts = {'hip': 0.22, 'cross': 0.24}
        L = s * 0.30
        for (sx0, (dx, dy)) in ((bcx - br * .8, a0), (bcx + br * .8, a1)):
            if pose == 'wave':
                dx = dx + math.sin(f * 0.28 + seed) * 0.25
            ex = sx0 + dx * L * flip
            ey = bcy - br * 0.45 + dy * L * shorts.get(pose, 1.0)
            _capsule(d, (sx0, bcy - br * 0.45), (ex, ey), s * 0.075, shirt)
    # head
    d.ellipse([hcx - hr * 1.06, hcy - hr, hcx + hr * 1.06, hcy + hr * 1.06], fill=skin, outline=PLUM, width=int(ow))
    # hair
    if cfg.get('hairk') == 'bun':
        d.ellipse([hcx - hr * 1.06, hcy - hr, hcx + hr * 1.06, hcy - hr * 0.25], fill=hair, outline=PLUM, width=int(ow * .7))
        d.ellipse([hcx - hr * 0.30, hcy - hr * 1.35, hcx + hr * 0.30, hcy - hr * 0.75], fill=hair, outline=PLUM, width=int(ow * .7))
    elif cfg.get('hairk') == 'cap':
        d.ellipse([hcx - hr * 1.06, hcy - hr, hcx + hr * 1.06, hcy - hr * 0.30], fill=hair, outline=PLUM, width=int(ow * .7))
    elif cfg.get('hairk') == 'pat':
        pass
    else:
        d.ellipse([hcx - hr * 1.06, hcy - hr * 1.05, hcx + hr * 1.06, hcy - hr * 0.1], fill=hair, outline=PLUM, width=int(ow * .7))
    # face
    exl, exr = hcx - hr * 0.42, hcx + hr * 0.42
    ey = hcy + hr * 0.25
    blink = ((f + seed * 37) % 130) < 4
    if blink or expr == 'sleep':
        d.line([exl - hr * 0.16, ey, exl + hr * 0.16, ey], fill=PLUM, width=max(3, int(hr * 0.13)))
        d.line([exr - hr * 0.16, ey, exr + hr * 0.16, ey], fill=PLUM, width=max(3, int(hr * 0.13)))
    elif expr in ('tired', 'moan', 'blank'):
        lid_y = ey - hr * 0.25
        for ex in (exl, exr):
            d.ellipse([ex - hr * 0.13, lid_y, ex + hr * 0.13, ey + hr * 0.13], fill=(255, 255, 255), outline=PLUM, width=max(2, int(hr * 0.07)))
            d.ellipse([ex - hr * 0.055, ey - hr * 0.02, ex + hr * 0.055, ey + hr * 0.13], fill=(50, 30, 46))
            d.rectangle([ex - hr * 0.25, lid_y - hr * 0.25, ex + hr * 0.25, ey - hr * 0.25 + hr * 0.25], fill=skin)
            d.line([ex - hr * 0.25, ey - hr * 0.25, ex + hr * 0.25, ey - hr * 0.25], fill=PLUM, width=max(2, int(hr * 0.07)))
            if expr in ('tired', 'moan'):
                d.arc([ex - hr * 0.2, ey + hr * 0.18, ex + hr * 0.25, ey + hr * 0.5], 10, 170, fill=tuple(max(0, c - 60) for c in skin), width=max(2, int(hr * 0.09)))
    elif expr == 'panic':
        for ex in (exl, exr):
            d.ellipse([ex - hr * 0.25, ey - hr * 0.25, ex + hr * 0.25, ey + hr * 0.25], fill=(255, 255, 255), outline=PLUM, width=max(2, int(hr * 0.08)))
            d.ellipse([ex - hr * 0.07, ey - hr * 0.07, ex + hr * 0.07, ey + hr * 0.25], fill=(50, 30, 46))
    mouth_y = hcy + hr * 0.62
    if expr == 'moan':
        mo = abs(math.sin(f * 0.05 + seed)) * hr * 0.06
        d.ellipse([hcx - hr * 0.13, mouth_y - hr * 0.1 - mo, hcx + hr * 0.13, mouth_y + hr * 0.25 + mo], fill=(80, 40, 60), outline=PLUM, width=max(2, int(hr * 0.07)))
    elif expr == 'panic':
        d.ellipse([hcx - hr * 0.25, mouth_y - hr * 0.05, hcx + hr * 0.25, mouth_y + hr * 0.25], fill=(80, 40, 60), outline=PLUM, width=max(2, int(hr * 0.07)))
    elif expr == 'flat':
        d.line([hcx - hr * 0.22, mouth_y, hcx + hr * 0.25, mouth_y], fill=PLUM, width=max(3, int(hr * 0.09)))

def char_img(s, cfg, f, extra=None):
    """Render one character into RGBA tile; returns Image, paste offset multiplier."""
    pad = int(s * 0.25)
    tw, th = int(s * 1.5), int(s * 1.35)
    img = Image.new('RGBA', (tw, th), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bean(d, tw / 2, th - pad, s, cfg, f)
    if extra: extra(d, f, s, tw, th)
    return img

def paste_char(base, x, y, s, cfg, f, lean=0.0, extra=None):
    img = char_img(s, cfg, f, extra)
    if lean:
        img = img.rotate(lean, resample=Image.BICUBIC, expand=True)
    base.paste(img, (int(x - img.width / 2), int(y - img.height)), img)

# ---------------------------------------------------------------- effects
def zzz(base, x, y, f, s, seed=0):
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(3):
        t = ((f * 0.5 + i * 23 + seed) % 46) / 46.0
        a = int(200 * math.sin(math.pi * t))
        zx, zy = x + t * s * 0.5, y - t * s * 0.25 - i * s * 0.13
        z = s * (0.06 + 0.03 * t)
        d.line([(zx - z, zy), (zx + z, zy), (zx - z, zy + z * 1.6), (zx + z, zy + z * 1.6)], fill=(120, 90, 150, a), width=int(s * 0.03))
        d.line([(zx - z, zy), (zx - z, zy + z * 1.6), (zx + z, zy + z * 1.6)], fill=(120, 90, 150, a), width=int(s * 0.03))
    base.paste(layer, (0, 0), layer)

def dust(base, x, y, t, s):
    if t <= 0 or t > 1: return
    r = s * float(out_back_gamma(t))
    a = int(170 * (1 - t))
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for ang in range(0, 360, 60):
        px = x + math.cos(math.radians(ang)) * r * 1.4
        py = y + math.sin(math.radians(ang)) * r * 0.5
        rr = s * 0.05 * (1 - t * 0.5)
        d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(214, 206, 196, a))
    base.paste(layer, (0, 0), layer)

def out_back_gamma(t):
    t = min(1.0, t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2

def sweat(base, x, y, f, s):
    t = (f * 0.25) % 1.0
    layer = Image.new('RGBA', base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    px, py = x + t * s * 0.05, y + t * s * 0.30
    r = s * 0.035
    d.polygon([(px, py - r * 1.4), (px + r, py), (px + r * 0.6, py + r * 0.9), (px - r * 0.6, py + r * 0.9), (px - r, py)], fill=(150, 200, 235, 220), outline=PLUM)
    base.paste(layer, (0, 0), layer)

# ------------------------------------------------------------- plate bg builders
def empty_plate():
    img = Image.new('RGB', (PW, PH), (40, 34, 48))
    return img

def build_street(seed='dawn'):
    palettes = dict(dawn=((58, 76, 122), (206, 186, 186), (156, 158, 168)),
                    day=((120, 144, 170), (212, 214, 214), (150, 152, 160)),
                    golden=((238, 186, 126), (250, 226, 178), (172, 150, 132)))
    sky0, sky1, rd = palettes[seed]
    img = empty_plate()
    d = ImageDraw.Draw(img)
    vgrad(d, 0, 0, PW, GROUND, sky0, sky1)
    for i in range(4):
        cloud(d, 260 + i * 520, 320 + (i % 2) * 180, 300 + (i % 3) * 90, (235, 226, 226) if seed != 'golden' else (255, 240, 214))
    hills(d, GROUND - 40, (108, 130, 150) if seed != 'golden' else (196, 168, 128), 3)
    # far houses
    farcol = (172, 158, 168) if seed != 'golden' else (222, 196, 156)
    for i in range(9):
        house(d, 60 + i * 236, GROUND - 36, 200, 260 + (i % 3) * 60, farcol, (150, 104, 96) if seed != 'golden' else (196, 140, 100), i + 40)
    # main row
    cols = [(214, 196, 168), (196, 168, 140), (168, 186, 196), (206, 176, 160), (196, 180, 200)]
    roofs = [(150, 96, 84), (110, 124, 140), (170, 120, 90), (130, 90, 100), (96, 110, 130)]
    for i in range(7):
        house(d, 20 + i * 320, GROUND + 6, 280, 300 + (i % 3) * 70, cols[i % 5], roofs[i % 5], i + 7, two_floor=(i % 2 == 0))
    for i in range(5):
        tree(d, 180 + i * 460, GROUND + 10, 240, i + 2)
    road(d, GROUND + 6, rd)
    for i in range(3):
        lamp(d, 300 + i * 700, GROUND + 40, 420)
    return img

def build_interior(wall=(226, 216, 200), floor=(178, 148, 118), win=None, night_edge=True):
    img = empty_plate()
    d = ImageDraw.Draw(img)
    fy = 2100
    d.rectangle([0, 0, PW, fy], fill=wall)
    d.rectangle([0, fy, PW, PH], fill=floor)
    seam = tuple(max(0, c - 40) for c in floor)
    for i in range(0, PW, 160):
        d.line([i, fy, i, PH], fill=seam, width=4)
    for i in range(0, PW, 160):
        d.line([0, fy + 190, PW, fy + 190], fill=seam, width=3)
    d.rectangle([0, fy, PW, fy + 26], fill=tuple(max(0, c - 60) for c in wall))
    if win:
        x, y, w, h = win
        d.rectangle([x - 16, y - 16, x + w + 16, y + h + 16], fill=tuple(max(0, c - 60) for c in wall))
        d.rectangle([x, y, x + w, y + h], fill=(120, 140, 170), outline=(70, 58, 70), width=6)
        d.line([x + w / 2, y, x + w / 2, y + h], fill=(70, 58, 70), width=6)
        vgrad(d, x + 3, y + 3, x + w - 3, y + h - 3, (150, 176, 200), (225, 210, 190), step=10)
        d.line([x + w / 2, y + 3, x + w / 2, y + h - 3], fill=(70, 58, 70), width=6)
    return img
