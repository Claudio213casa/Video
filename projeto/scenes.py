"""Shot definitions + per-frame world. Frame-exact, pure function of f."""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter
from render_lib import (W, H, PW, PH, GROUND, FPS, PLUM,
                        Cam, apply_cam, vgrad, cloud, hills, house, tree, road,
                        lamp, cushion, bean, paste_char, zzz, dust, sweat, font,
                        p0, p1, ss, lerp, out_back)

ROOT = os.path.dirname(os.path.abspath(__file__))
STREET = {}
INTER = {}

HOODS = [
    dict(shirt=(168, 178, 190), hair=(120, 110, 100), hairk='cap', skin=(216, 212, 198)),
    dict(shirt=(186, 164, 150), hair=(90, 76, 64), skin=(214, 208, 196)),
    dict(shirt=(150, 168, 160), hair=(70, 62, 58), hairk='bun', skin=(218, 214, 200)),
    dict(shirt=(178, 158, 178), hair=(140, 120, 96), skin=(212, 208, 196)),
    dict(shirt=(160, 160, 150), hair=(60, 56, 52), skin=(220, 216, 202)),
    dict(shirt=(150, 150, 168), hair=(110, 96, 84), skin=(216, 212, 198)),
]
MARTA = dict(shirt=(186, 160, 196), hair=(170, 170, 174), hairk='bun', skin=(218, 198, 186))
HERO_PJ = dict(shirt=(126, 190, 214), hair=(58, 44, 40), skin=(243, 203, 164))
HERO_WK = dict(shirt=(232, 230, 220), hair=(58, 44, 40), skin=(226, 198, 168))

def get_street(kind):
    if kind not in STREET:
        import render_lib as RL
        STREET[kind] = RL.build_street(kind)
    return STREET[kind]

def get_interior(key, **kw):
    if key not in INTER:
        import render_lib as RL
        INTER[key] = RL.build_interior(**kw)
    return INTER[key]

def draw_street_crowd(img, d, f, f0, n=6, golden=False):
    for i in range(n):
        st = (f - f0)
        x = 140 + ((i * 400 + st * 42 * (1.05 + 0.12 * (i % 3))) % (PW + 500)) - 200
        ph = st * 0.16 + i * 2.1
        pasted_depth = 2260 + (i % 3) * 120
        paste_char(img, x, pasted_depth, 490 + (i % 3) * 40, dict(HOODS[i % len(HOODS)], expr='moan', walkph=ph, lean=6), f)

# ------------------------------------------------------------------ shots
def shot1(f, plate):
    img = get_interior('bed', wall=(64, 84, 120), floor=(88, 96, 120)).copy()
    d = ImageDraw.Draw(img)
    x, y, w, h = 380, 420, 560, 760
    d.rectangle([x - 26, y - 26, x + w + 26, y + h + 26], fill=(46, 60, 92))
    vgrad(d, x, y, x + w, y + h, (40, 52, 86), (120, 120, 150), step=12)
    d.line([x + w / 2, y, x + w / 2, y + h], fill=(40, 34, 52), width=14)
    d.line([x, y + h / 2, x + w, y + h / 2], fill=(40, 34, 52), width=14)
    for i in range(3):
        px = x + 90 + i * 170 + math.sin(f * 0.02 + i) * 6
        bean(d, px, y + h - 60 - i * 8, 130, dict(HOODS[i], expr='moan'), f)
    d.rectangle([1520, 1060, 1860, 2100], fill=(96, 78, 90), outline=(60, 44, 60), width=6)
    d.ellipse([1800, 1560, 1840, 1600], fill=(200, 180, 120), outline=PLUM, width=3)
    bx, by = 760, 1850
    d.rectangle([bx - 340, by - 260, bx + 380, by + 240], fill=(84, 70, 100), outline=(52, 42, 68), width=8)
    cushion(d, [bx - 320, by - 240, bx - 40, by - 120], (196, 200, 214))
    d.rectangle([bx - 340, by - 90, bx + 380, by + 40], fill=(140, 110, 130), outline=(52, 42, 68), width=6)
    wake_t = ss((f - 2) / 22.0)
    hero = dict(HERO_PJ, expr='panic' if f > 40 else ('tired' if wake_t > .5 else 'sleep'),
                pose='up' if f <= 46 else 'push', seed=11)
    sit = 0.55 + 0.45 * wake_t
    paste_char(img, bx + 80, by - 90 - (1 - sit) * 40, 430, hero, f, lean=(1 - wake_t) * 38)
    if f < 26: zzz(img, bx + 140, by - 480, f, 240)
    if 40 <= f < 90: sweat(img, bx + 260, by - 620, f, 430)
    return img

def shot2(f, plate):
    img = get_street('dawn').copy()
    d = ImageDraw.Draw(img)
    d.rectangle([0, 1010, PW, 1060], fill=(52, 42, 68))
    d.rectangle([990, 0, 1058, 1100], fill=(52, 42, 68))
    draw_street_crowd(img, d, f, p0(3), n=5)
    return img

def shot3(f, plate):
    img = get_street('dawn').copy()
    d = ImageDraw.Draw(img)
    mx = 1120 + math.sin((f - 246) * 0.05) * 30
    paste_char(img, mx, 2380, 560, dict(MARTA, expr='moan', walkph=(f - 246) * 0.25,
                                        lean=9 + math.sin(f * 0.055) * 7), f)
    return img

def shot4(f, plate):
    img = get_interior('liv', wall=(226, 216, 200), floor=(178, 148, 118)).copy()
    d = ImageDraw.Draw(img)
    d.rectangle([160, 1080, 560, 2100], fill=(126, 100, 96), outline=(70, 50, 52), width=8)
    d.ellipse([500, 1560, 548, 1608], fill=(214, 188, 120), outline=PLUM, width=4)
    px = 900 - (380 - f) * 12 if f < 380 else 900
    hero_lean = 2.5 * math.sin(f * 0.09)
    paste_char(img, px, 2380, 560, dict(HERO_PJ, expr='panic' if f < 470 else 'tired',
                                        pose='push' if f < 470 else 'hip', seed=5, flip=-1), f,
               lean=hero_lean)
    if f > 378:
        sx = lerp(2100, 640, ss((f - 378) / 20.0))
        so = Image.new('RGBA', (760, 480), (0, 0, 0, 0))
        ds = ImageDraw.Draw(so)
        cushion(ds, [30, 60, 730, 300], (196, 120, 110))
        cushion(ds, [200, 10, 560, 140], (206, 136, 124))
        drop = max(0, 400 - f)
        so = so.rotate(drop * 12, expand=False)
        img.paste(so, (int(sx) - 380, 1650 - drop * 30), so)
        if f >= 400:
            dust(img, sx - 60, 2120, (f - 400) / 14.0, 500)
    if f > 405:
        sy = lerp(1180, 1520, out_back(f, 405, 10))
        sh = Image.new('RGBA', (700, 460), (0, 0, 0, 0))
        dsh = ImageDraw.Draw(sh)
        for si in range(3):
            dsh.rectangle([30, 60 + si * 120, 670, 100 + si * 120], fill=(150, 118, 88), outline=(96, 72, 52), width=5)
            if si < 2:
                for bi in range(5):
                    dsh.rectangle([80 + bi * 110, 10 + si * 120, 150 + bi * 110, 60 + si * 120],
                                  fill=(120, 140, 160) if bi % 2 else (180, 150, 120), outline=PLUM, width=3)
        img.paste(sh, (500, int(sy)), sh)
        if f >= 415:
            dust(img, 850, 2000, (f - 415) / 14.0, 460)
    if f > 424:
        by = lerp(1180, 1300, out_back(f, 424, 12))
        ang = min(28, (f - 424) * 7) + 2.5 * math.sin(f * 0.35) * max(0.0, 1.0 - (f - 436) / 22.0)
        bk = Image.new('RGBA', (620, 420), (0, 0, 0, 0))
        dbk = ImageDraw.Draw(bk)
        dbk.ellipse([40, 210, 300, 400], outline=PLUM, width=16)
        dbk.ellipse([330, 210, 590, 400], outline=PLUM, width=16)
        dbk.line([170, 305, 460, 305, 380, 180, 200, 180, 170, 305], fill=(150, 60, 90), width=22, joint='curve')
        dbk.line([460, 305, 560, 200], fill=(150, 60, 90), width=22)
        dbk.ellipse([540, 170, 600, 230], outline=PLUM, width=12)
        bk = bk.rotate(-ang, center=(300, 300), expand=False)
        img.paste(bk, (460, int(by)), bk)
        if f >= 436:
            dust(img, 770, 1930, (f - 436) / 14.0, 460)
    return img

def shot5(f, plate):
    img = get_interior('liv', wall=(226, 216, 200), floor=(178, 148, 118)).copy()
    d = ImageDraw.Draw(img)
    d.rectangle([160, 1080, 560, 2100], fill=(126, 100, 96), outline=(70, 50, 52), width=8)
    cushion(d, [240, 1560, 980, 1800], (196, 120, 110))
    for si in range(2):
        d.rectangle([300, 1350 + si * 105, 950, 1430 + si * 105], fill=(150, 118, 88), outline=(96, 72, 52), width=5)
    d.ellipse([340, 1180, 600, 1360], outline=PLUM, width=14)
    d.ellipse([520, 1180, 780, 1360], outline=PLUM, width=14)
    d.line([470, 1270, 650, 1270, 590, 1160, 330, 1160], fill=(150, 60, 90), width=18, joint='curve')
    hx = 1350
    paste_char(img, hx, 2380, 560, dict(HERO_PJ, pose='reach', expr='panic', seed=5), f)
    ring = (math.sin(f * 0.25) * 0.5 + 0.5)
    ph = Image.new('RGBA', (140, 240), (0, 0, 0, 0))
    dph = ImageDraw.Draw(ph)
    dph.rounded_rectangle([6, 6, 134, 234], radius=26, fill=(40, 44, 60, 255), outline=PLUM, width=6)
    dph.rounded_rectangle([20, 24, 120, 210], radius=10, fill=(200, 220, 255, 255))
    dph.text((70, 60), 'POLICIA', font=font(24), fill=(60, 60, 90), anchor='mm')
    dph.rounded_rectangle([30, 100, 110, 140], radius=6, fill=(120, 130, 150))
    img.paste(ph, (hx + 210, 1560), ph)
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.ellipse([hx + 130, 1450, hx + 450, 1900], fill=(255, 240, 200, int(30 + ring * 30)))
    img.paste(layer, (0, 0), layer)
    return img

def shot6(f, plate):
    img = get_street('day').copy()
    d = ImageDraw.Draw(img)
    draw_street_crowd(img, d, f, p0(7), n=6)
    fg = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    dfg = ImageDraw.Draw(fg)
    cushion(dfg, [-100, 2560, 1250, 2900], (196, 120, 110))
    cushion(dfg, [1200, 2560, 2300, 2900], (196, 120, 110))
    for si in range(2):
        dfg.rectangle([-100, 2400 + si * 80, 900, 2460 + si * 80], fill=(150, 118, 88, 255), outline=(96, 72, 52), width=6)
    img.paste(fg, (0, 0), fg)
    return img

def shot7(f, plate):
    img = get_street('day').copy()
    d = ImageDraw.Draw(img)
    draw_street_crowd(img, d, f, p0(8), n=6)
    for i in range(2):
        bx = 700 + (f + i * 90) * 2.2
        by = 430 + math.sin((f + i * 90) * 0.25) * 40
        wing = math.sin((f + i * 90) * 0.5) * 18
        d.line([(bx - 24, by + wing), (bx, by), (bx + 24, by + wing)], fill=(60, 56, 70), width=6)
    return img

def shot8(f, plate):
    img = get_street('day').copy()
    d = ImageDraw.Draw(img)
    d.rectangle([1180, 1300, 2048, 2330], fill=(206, 176, 160), outline=(120, 96, 84), width=8)
    paste_char(img, 1470, 1810, 280, dict(HERO_PJ, expr='tired', pose='hang', seed=5), f)
    glass = Image.new('RGBA', (PW, PH), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glass)
    dg.rectangle([1330, 1420, 1620, 1810], fill=(150, 170, 200, 70))
    img.paste(glass, (0, 0), glass)
    d.rectangle([1330, 1420, 1620, 1810], outline=(70, 50, 60), width=6)
    d.line([1475, 1420, 1475, 1810], fill=(70, 50, 60), width=5)
    sway = math.sin(f * 0.09) * 12
    cur = Image.new('RGBA', (560, 460), (0, 0, 0, 0))
    dcur = ImageDraw.Draw(cur)
    dcur.polygon([(0, 0), (100, 0), (100 + sway, 440), (0, 440)], fill=(146, 106, 118, 255), outline=PLUM, width=5)
    dcur.polygon([(240, 0), (340, 0), (340, 440), (240 + sway, 440)], fill=(146, 106, 118, 255), outline=PLUM, width=5)
    img.paste(cur, (1325, 1415), cur)
    paste_char(img, 700, 2320, 500, dict(HOODS[1], expr='blank', seed=3, lean=2), f)
    return img

def draw_tv(d, img, f, headline_on, tv_f0):
    on = f >= tv_f0 + 30
    flick = 1.0
    if on:
        flick = 0.8 + 0.2 * abs(math.sin(f * 1.9))
    d.rectangle([640, 1150, 1460, 1800], fill=(38, 36, 44), outline=(20, 18, 24), width=8)
    if on:
        glow = tuple(int(c * flick) for c in (190, 200, 220))
        d.rectangle([684, 1196, 1416, 1756], fill=glow)
        band = tuple(int(c * flick) for c in (60, 80, 130))
        d.rectangle([684, 1196, 1416, 1360], fill=band)
        if headline_on:
            tcol = tuple(int(c * flick) for c in (250, 242, 200))
            ha = int(255 * max(0.0, min(1.0, (f - 1084) / 6.0)))
            sh = Image.new('RGBA', (760, 300), (0, 0, 0, 0))
            dsh = ImageDraw.Draw(sh)
            dsh.rectangle([10, 40, 750, 260], fill=(30, 30, 50, 215 * ha // 255))
            dsh.text((380, 105), 'FALTOU CAFE', font=font(64), fill=(250, 240, 200, ha), anchor='mm')
            dsh.text((380, 190), 'NA CIDADE INTEIRA', font=font(44), fill=(255, 150, 150, ha), anchor='mm')
            img.paste(sh, (680, 1200), sh)
        else:
            for i in range(3):
                yy = 1250 + i * 150 + (f * 3 % 150) - 150
                d.line([684, yy, 1416, yy - 20], fill=(150, 160, 180), width=10)
    else:
        d.rectangle([684, 1196, 1416, 1756], fill=(22, 22, 30))
        d.ellipse([1020, 1450, 1080, 1520], outline=(90, 90, 110), width=4)

def shot9(f, plate):
    img = get_interior('night', wall=(74, 78, 108), floor=(120, 100, 96)).copy()
    d = ImageDraw.Draw(img)
    d.rectangle([680, 1780, 1440, 2120], fill=(138, 108, 84), outline=(86, 64, 50), width=8)
    draw_tv(d, img, f, headline_on=False, tv_f0=992)
    paste_char(img, 500, 2340, 560, dict(HERO_PJ, pose='point', expr='tired', seed=5), f)
    return img

def shot10(f, plate):
    img = get_interior('night', wall=(74, 78, 108), floor=(120, 100, 96)).copy()
    d = ImageDraw.Draw(img)
    d.rectangle([560, 1650, 1560, 2150], fill=(138, 108, 84), outline=(86, 64, 50), width=10)
    draw_tv(d, img, f + 60, headline_on=True, tv_f0=900)
    return img

def shot11(f, plate):
    img = Image.new('RGB', (PW, PH), (210, 208, 204))
    d = ImageDraw.Draw(img)
    vgrad(d, 0, 0, PW, 2020, (170, 176, 188), (226, 220, 212), step=10)
    d.rectangle([0, 2020, PW, PH], fill=(150, 152, 158))
    for i in range(0, PW, 220):
        d.line([i, 0, i, 2020], fill=(178, 172, 172), width=4)
        d.line([i, 2020, i, PH], fill=(126, 128, 134), width=4)
    for j in range(0, 2020, 220):
        d.line([0, j, PW, j], fill=(178, 172, 172), width=4)
    wig = math.sin(f * 0.05) * 4
    breath = 1.0 + 0.006 * math.sin(2 * math.pi * f / 75.0)
    d.rectangle([556, 240, 1336, 1560], fill=(226, 226, 230))
    mir = Image.new('RGB', (760, 1240), (226, 226, 230))
    dm = ImageDraw.Draw(mir)
    bean(dm, 380, 1140, 620 * breath, dict(HERO_PJ, expr='tired', pose='hang', seed=5, skin=(228, 200, 172)), f)
    t_in = min(1.0, (f - 1155) / 20.0)
    if t_in < 1.0:
        mir = mir.filter(ImageFilter.GaussianBlur(6 * (1 - t_in)))
    ref = mir.resize((600, 1060))
    img.paste(ref, (660 + int(wig), 360 + int(wig * .5)))
    d.rectangle([560, 240, 1336, 1560], outline=(90, 70, 84), width=14)
    flick = int(10 + 8 * math.sin(2 * math.pi * f / 47.0))
    fl = Image.new('RGB', (PW, PH), (236 * flick // 10, 232 * flick // 10, 226 * flick // 10))
    img = Image.blend(img, fl, 0.05)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([200, 1900, 620, 2000], radius=40, fill=(226, 226, 230), outline=(120, 118, 122), width=6)
    d.rectangle([380, 2000, 440, 2380], fill=(190, 188, 186), outline=(120, 118, 122), width=5)
    return img

def shot12(f, plate):
    img = get_street('golden').copy()
    d = ImageDraw.Draw(img)
    draw_street_crowd(img, d, f, p0(13), n=6)
    return img

def build_loterica():
    img = get_street('golden').copy()
    d = ImageDraw.Draw(img)
    x, ybase, w, h = 640, 2330, 760, 860
    wall = (222, 196, 150)
    seam = tuple(max(0, c - 46) for c in wall)
    d.rectangle([x, ybase - h, x + w, ybase], fill=wall, outline=seam, width=8)
    d.rectangle([x, ybase - h, x + w, ybase - h + 90], fill=(92, 70, 96), outline=(60, 44, 66), width=6)
    d.text((x + w / 2, ybase - h + 45), 'LOTERICA', font=font(52), fill=(250, 240, 200), anchor='mm',
           stroke_width=6, stroke_fill=(60, 40, 66))
    d.rectangle([x + 60, ybase - 480, x + w - 60, ybase - 160], fill=(120, 110, 130), outline=(70, 58, 74), width=6)
    d.line([x + w / 2, ybase - 480, x + w / 2, ybase - 160], fill=(70, 58, 74), width=6)
    d.rectangle([x + 320, ybase - 140, x + 440, ybase], fill=(90, 70, 80), outline=PLUM, width=5)
    return img

def shot13(f, plate):
    if 'lot' not in STREET:
        STREET['lot'] = build_loterica()
    img = STREET['lot'].copy()
    d = ImageDraw.Draw(img)
    sway = math.sin(f * 0.055) * 3
    paste_char(img, 1020, 2360, 620, dict(HERO_WK, expr='blank', pose='hang', seed=5,
                                          shoe=(60, 70, 90)), f, lean=sway)
    for i in range(6):
        wob = abs(math.sin(f * 0.07 + i)) * 6
        d.arc([660 + i * 126, 1478 - wob, 760 + i * 126, 1560 - wob], 0, 360,
              fill=(210, 150, 120), width=4)
    return img

def shot14(f, plate):
    img = Image.new('RGB', (PW, PH), (238, 186, 126))
    d = ImageDraw.Draw(img)
    vgrad(d, 0, 0, PW, GROUND, (226, 156, 106), (252, 230, 186))
    for i in range(3):
        cloud(d, 300 + i * 700, 350 + (i % 2) * 160, 320, (255, 238, 210))
    hills(d, GROUND - 60, (198, 168, 120), 9)
    cx, ybase = 240, 2360
    wall = (206, 176, 160)
    seam = tuple(max(0, c - 46) for c in wall)
    d.rectangle([cx, ybase - 900, cx + 760, ybase], fill=wall, outline=seam, width=8)
    d.polygon([(cx - 60, ybase - 900), (cx + 820, ybase - 900), (cx + 380, ybase - 1220)],
              fill=(168, 120, 96), outline=(120, 84, 66))
    d.rectangle([cx + 120, ybase - 700, cx + 640, ybase - 160], fill=(110, 96, 116), outline=(70, 58, 74), width=6)
    for i in range(8):
        col = (206, 110, 96) if i % 2 == 0 else (236, 226, 212)
        wob = abs(math.sin(f * 0.05 + i)) * 10
        d.polygon([(cx + 90 + i * 78, ybase - 780), (cx + 168 + i * 78, ybase - 780),
                   (cx + 168 + i * 78, ybase - 620 - wob), (cx + 90 + i * 78, ybase - 620 - wob)],
                  fill=col, outline=PLUM)
    d.text((cx + 380, ybase - 840), 'CAFE', font=font(58), fill=(250, 240, 200), anchor='mm',
           stroke_width=6, stroke_fill=(80, 50, 60))
    if f >= 1820:
        t = min(1.0, (f - 1820) / 9.0)
        prog = out_back(f, 1820, 9)
        sg = Image.new('RGBA', (420, 300), (0, 0, 0, 0))
        dsg = ImageDraw.Draw(sg)
        dsg.rounded_rectangle([20, 20, 400, 220], radius=18, fill=(238, 230, 214, 255), outline=PLUM, width=10)
        dsg.text((210, 120), 'FECHADO', font=font(54), fill=(90, 60, 90, 255), anchor='mm')
        ang = min(8.0, max(0, (f - 1829)) * 2.0)
        sg = sg.rotate(ang, expand=True, resample=Image.BICUBIC)
        img.paste(sg, (cx + 210, int(ybase - 800 + prog * 400)), sg)
    queue = [(880, 2410, 0), (1120, 2430, 1), (1340, 2400, 2), (1560, 2440, 3), (1780, 2410, 4), (1960, 2430, 5)]
    for qx, qy, i in queue:
        paste_char(img, qx, qy, 520, dict(HOODS[i], expr='moan', walkph=(f + i * 40) * 0.25, lean=4), f)
    hero_x = 700 - min(60, max(0, f - 1597) * 0.5)
    def mug(dd, ff, s, tw, th):
        mx, my = tw / 2 + s * 0.25, th - s * 0.55
        dd.ellipse([mx - 26, my - 20, mx + 26, my + 20], fill=(226, 226, 230), outline=PLUM, width=5)
        dd.ellipse([mx - 12, my - 12, mx + 12, my + 12], fill=(120, 100, 96))
    paste_char(img, hero_x, 2400, 560, dict(HERO_WK, expr='tired', pose='reach', seed=5), f, extra=mug)
    return img

SHOTS = [
    dict(name='s01_cama', f0=0, f1=116, cam=Cam([(0, 1024, 1260, 1.42), (116, 1024, 1380, 1.02)])),
    dict(name='s02_janela', f0=116, f1=246, cam=Cam([(116, 1024, 1560, 1.18), (246, 1000, 1600, 1.12)])),
    dict(name='s03_marta', f0=246, f1=355, cam=Cam([(246, 1100, 1700, 1.52), (355, 1120, 1700, 1.52)])),
    dict(name='s04_barricada', f0=355, f1=464, cam=Cam([(355, 1000, 1520, 1.02), (464, 960, 1500, 1.06)])),
    dict(name='s05_celular', f0=464, f1=576, cam=Cam([(464, 1300, 1620, 1.18), (576, 1520, 1750, 1.50)])),
    dict(name='s06_passando', f0=576, f1=714, cam=Cam([(576, 1024, 1700, 1.02), (714, 1000, 1680, 1.06)])),
    dict(name='s07_mesmo_lugar', f0=714, f1=893, cam=Cam([(714, 700, 1560, 1.10), (893, 1340, 1620, 1.10)])),
    dict(name='s08_cortina', f0=893, f1=984, cam=Cam([(893, 850, 1700, 1.18), (984, 1450, 1650, 1.32)])),
    dict(name='s09_tv', f0=984, f1=1087, cam=Cam([(984, 1024, 1500, 1.02), (1087, 1024, 1380, 1.22)])),
    dict(name='s10_manchete', f0=1087, f1=1155, cam=Cam([(1087, 1050, 1480, 1.45), (1155, 1050, 1470, 1.55)])),
    dict(name='s11_espelho', f0=1155, f1=1284, cam=Cam([(1155, 940, 1160, 1.02), (1210, 950, 1185, 1.05), (1284, 940, 1165, 1.02)])),
    dict(name='s12_multidao', f0=1284, f1=1422, cam=Cam([(1284, 1024, 1640, 1.12), (1422, 1024, 1700, 1.02)])),
    dict(name='s13_loterica', f0=1422, f1=1597, cam=Cam([(1422, 1024, 1750, 1.02), (1520, 1024, 1790, 1.22), (1597, 1024, 1800, 1.33)])),
    dict(name='s14_final', f0=1597, f1=1828, cam=Cam([(1597, 1024, 1600, 1.06), (1810, 1024, 1750, 1.02)])),
]

def shot_at(f):
    for s in SHOTS:
        if s['f0'] <= f < s['f1']:
            return s
    return SHOTS[-1]

DRAW = dict(s01_cama=shot1, s02_janela=shot2, s03_marta=shot3, s04_barricada=shot4,
            s05_celular=shot5, s06_passando=shot6, s07_mesmo_lugar=shot7, s08_cortina=shot8,
            s09_tv=shot9, s10_manchete=shot10, s11_espelho=shot11, s12_multidao=shot12,
            s13_loterica=shot13, s14_final=shot14)

MAXZ = {s['name']: max(k[3] for k in s['cam'].keys) + 0.03 for s in SHOTS}

def render_frame(f):
    sh = shot_at(f)
    plate = DRAW[sh['name']](f, None)
    return apply_cam(plate, sh['cam'] if sh['name'] != 's10_manchete' else sh['cam'], f)

if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stills'
    if mode == 'stills':
        frames = [int(x) for x in sys.argv[2].split(',')]
        outdir = sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for f in frames:
            render_frame(f).save(os.path.join(outdir, 'f%04d.jpg' % f), quality=90)
        print('stills done', frames)
    elif mode == 'frames':
        a, b = (int(x) for x in sys.argv[2].split('-'))
        outdir = sys.argv[3]
        os.makedirs(outdir, exist_ok=True)
        for f in range(a, b + 1):
            render_frame(f).save(os.path.join(outdir, 'f%04d.jpg' % f), quality=93)
