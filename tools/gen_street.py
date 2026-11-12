#!/usr/bin/env python3
"""
Генератор пиксельной графики для сцены «Улица» (street.tscn).

1 пиксель картинки = 1 «большой» пиксель шейдера (pixel_res 320x240).
В игре спрайты масштабируются x3, поэтому графика ложится ровно на сетку
пост-эффекта и фактура совпадает с первой сценой.

Запуск из корня проекта:  python3 tools/gen_street.py   (нужны Pillow и numpy)
Положение фонарей, дверей и т.п. продублировано в scripts/street.gd —
если двигаете что-то здесь, поправьте и там.
"""
import math
import os

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(ROOT, "..", "assets", "street"))
H = 240          # высота кадра в пикселях шейдера
GROUND = 150     # линия, где фасады встречаются с тротуаром
WORLD = 1200     # ширина мира (x3 = 3600 px в игре)
LAMPS = [96, 300, 470, 730, 920, 1120]
NIGHT = 0.8      # затемнение стен: ночью их «проявляют» фонари в движке

rng = np.random.default_rng(1979)
HEDGE_SKIP = []  # участки без кустов (двери, витрины, переулки)


# ---------------------------------------------------------------- утилиты
def canvas(w, h=H):
    return np.zeros((h, w, 4), np.uint8)


def clip(c):
    return tuple(int(max(0, min(255, v))) for v in c[:3])


def shade(c, k):
    return clip([v * k for v in c[:3]])


def mix(a, b, t):
    return clip([a[i] + (b[i] - a[i]) * t for i in range(3)])


def put(img, x, y, c, a=255):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        img[y, x] = (*c[:3], a)


def rect(img, x, y, w, h, c, a=255):
    H_, W_ = img.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W_), min(y + h, H_)
    if x1 > x0 and y1 > y0:
        img[y0:y1, x0:x1] = (*c[:3], a)


def blend(img, x, y, c, k):
    h, w = img.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        p = img[y, x]
        if p[3] == 0:
            img[y, x] = (*c[:3], int(255 * k))
        else:
            img[y, x, :3] = clip([p[i] * (1 - k) + c[i] * k for i in range(3)])


def line(img, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        put(img, round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)


def blob(img, cx, cy, r, c, rough=0.25):
    for y in range(int(cy - r - 2), int(cy + r + 3)):
        for x in range(int(cx - r - 2), int(cx + r + 3)):
            d = math.hypot(x - cx, (y - cy) * 1.1)
            if d < r * (1 - rough * rng.random()):
                put(img, x, y, c)


def save(img, name):
    os.makedirs(OUT, exist_ok=True)
    Image.fromarray(img).save(os.path.join(OUT, name))
    print("  ", name, img.shape[1], "x", img.shape[0])


# ------------------------------------------------------- пиксельный шрифт
FONT = {
    "П": ["####", "#..#", "#..#", "#..#", "#..#"],
    "О": [".##.", "#..#", "#..#", "#..#", ".##."],
    "Л": ["..##", ".#.#", ".#.#", "#..#", "#..#"],
    "И": ["#..#", "#..#", "#.##", "##.#", "#..#"],
    "Ц": ["#..#", "#..#", "#..#", "####", "...#"],
    "Я": [".###", "#..#", ".###", ".#.#", "#..#"],
    "К": ["#..#", "#.#.", "##..", "#.#.", "#..#"],
    "А": [".##.", "#..#", "####", "#..#", "#..#"],
    "Ф": ["..#..", ".###.", "#.#.#", ".###.", "..#.."],
    "Е": ["####", "#...", "###.", "#...", "####"],
    "2": ["###.", "...#", ".##.", "#...", "####"],
    "4": ["#..#", "#..#", "####", "...#", "...#"],
}


def text_mask(s):
    w = sum(len(FONT[ch][0]) + 1 for ch in s) - 1
    m = np.zeros((5, w), bool)
    cx = 0
    for ch in s:
        for gy, row in enumerate(FONT[ch]):
            for gx, v in enumerate(row):
                if v == "#":
                    m[gy, cx + gx] = True
        cx += len(FONT[ch][0]) + 1
    return m


def neon_text(img, s, x, y, c, glow=True):
    m = text_mask(s)
    if glow:
        p = np.pad(m, 2)
        d1 = p.copy()
        for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            d1 |= np.roll(np.roll(p, dy, 0), dx, 1)
        d2 = d1.copy()
        for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)]:
            d2 |= np.roll(np.roll(d1, dy, 0), dx, 1)
        for yy, xx in zip(*np.nonzero(d2 & ~p)):
            blend(img, x - 2 + xx, y - 2 + yy, c, 0.4 if d1[yy, xx] else 0.15)
    for yy, xx in zip(*np.nonzero(m)):
        put(img, x + xx, y + yy, c)
    return m.shape[1]


# ------------------------------------------------------------------- небо
def gen_sky():
    w = 320
    img = canvas(w)
    stops = [(0, (5, 7, 18)), (80, (14, 20, 44)), (130, (36, 32, 62)),
             (165, (78, 52, 70)), (240, (78, 52, 70))]
    for y in range(H):
        for (y0, c0), (y1, c1) in zip(stops, stops[1:]):
            if y0 <= y <= y1:
                rect(img, 0, y, w, 1, mix(c0, c1, (y - y0) / (y1 - y0)))
                break
    for _ in range(70):
        b = int(rng.integers(70, 190))
        put(img, int(rng.integers(0, w)), int(rng.integers(24, 105)), (b, b, min(255, b + 30)))
    # луна
    cx, cy, r = 252, 50, 9
    for y in range(cy - r - 5, cy + r + 6):
        for x in range(cx - r - 5, cx + r + 6):
            d = math.hypot(x - cx, y - cy)
            if d <= r:
                c = (226, 220, 196)
                if math.hypot(x - cx + 3, y - cy - 2) < 2.5 or math.hypot(x - cx - 3, y - cy + 3) < 1.6:
                    c = (196, 190, 170)
                put(img, x, y, c)
            elif d <= r + 5:
                blend(img, x, y, (120, 120, 150), 0.22 * (1 - (d - r) / 5))
    # облака-полосы
    for cy2, x0, ln in [(58, 200, 110), (64, 150, 90), (88, 0, 140), (96, 60, 120), (74, 20, 70)]:
        for x in range(x0, min(w, x0 + ln)):
            th = 1 + int(2 * math.sin((x - x0) / ln * math.pi))
            for t in range(th):
                blend(img, x, cy2 + t, (26, 28, 52), 0.85)
            blend(img, x, cy2 - 1, (60, 56, 90), 0.4)
    save(img, "sky.png")


# --------------------------------------------------------- дальний город
WIN_WARM = [(210, 160, 90), (190, 140, 80), (230, 200, 140), (130, 170, 200), (200, 120, 90)]


def haze(img, y0, y1, fog, tmax):
    for y in range(y0, H):
        t = min(tmax, (y - y0) / (y1 - y0) * tmax)
        row = img[y]
        a = row[:, 3] > 0
        row[a, :3] = (row[a, :3] * (1 - t) + np.array(fog) * t).astype(np.uint8)


def gen_far():
    w = 480
    img = canvas(w)
    x = 0
    while x < w:
        bw = int(rng.integers(12, 34))
        top = int(rng.integers(62, 118))
        base = clip(np.array((22, 26, 46)) + rng.integers(-3, 4, 3))
        rect(img, x, top, bw, H - top, base)
        if rng.random() < 0.35:
            ah = int(rng.integers(5, 14))
            rect(img, x + bw // 2, top - ah, 1, ah, base)
            put(img, x + bw // 2, top - ah - 1, (200, 50, 50))
        for wy in range(top + 3, 170, 3):
            for wx in range(x + 2, x + bw - 2, 3):
                if rng.random() < 0.13:
                    put(img, wx, wy, shade(WIN_WARM[rng.integers(len(WIN_WARM))], rng.uniform(0.55, 1.0)))
        x += bw + int(rng.integers(0, 3))
    haze(img, 95, 175, (58, 46, 74), 0.75)
    save(img, "far.png")


def gen_mid():
    w = 720
    img = canvas(w)
    x = 0
    while x < w:
        bw = int(rng.integers(34, 80))
        top = int(rng.integers(50, 100))
        base = clip(np.array((30, 33, 54)) + rng.integers(-4, 5, 3))
        rect(img, x, top, bw, H - top, base)
        rect(img, x, top, bw, 1, shade(base, 1.4))
        rect(img, x + bw - 1, top, 1, H - top, shade(base, 0.7))
        if rng.random() < 0.4:  # бак на крыше
            tx = x + int(rng.integers(4, max(5, bw - 12)))
            rect(img, tx, top - 9, 8, 6, shade(base, 0.9))
            rect(img, tx + 1, top - 3, 1, 3, shade(base, 0.8))
            rect(img, tx + 6, top - 3, 1, 3, shade(base, 0.8))
        for _ in range(int(rng.integers(0, 3))):  # кондиционеры на крыше
            rect(img, x + int(rng.integers(2, bw - 6)), top - 3, 5, 3, shade(base, 1.2))
        for wy in range(top + 5, 175, 7):
            for wx in range(x + 3, x + bw - 4, 6):
                if rng.random() < 0.22:
                    c = shade(WIN_WARM[rng.integers(len(WIN_WARM))], rng.uniform(0.6, 1.0))
                    rect(img, wx, wy, 2, 3, c)
                else:
                    rect(img, wx, wy, 2, 3, shade(base, 0.6))
        if rng.random() < 0.35:  # вертикальная неоновая вывеска
            nc = [(255, 70, 150), (70, 220, 230), (255, 150, 60)][rng.integers(3)]
            sx, sy = x + bw - 6, top + int(rng.integers(8, 30))
            for yy in range(sy - 2, sy + 22):
                for xx in range(sx - 2, sx + 7):
                    blend(img, xx, yy, nc, 0.18)
            rect(img, sx, sy, 5, 20, shade(nc, 0.35))
            for k in range(4):
                rect(img, sx + 1, sy + 2 + k * 5, 3, 3, nc)
        x += bw + int(rng.integers(0, 4))
    haze(img, 110, 190, (50, 42, 70), 0.45)
    save(img, "mid.png")


# ----------------------------------------------------------- фасады улицы
def bjit(a, b):
    return ((a * 73856093) ^ (b * 19349663)) % 19 - 9


def wall(img, x0, x1, top, kind, base):
    h, w = GROUND - top, x1 - x0
    pn = rng.integers(-3, 4, (h, w))
    coarse = rng.integers(-4, 5, (h // 6 + 2, w // 6 + 2))
    for yy in range(h):
        y = top + yy
        for xx in range(w):
            x = x0 + xx
            n = int(pn[yy, xx])
            if kind == "brick":
                row = yy // 3
                off = 3 if row % 2 else 0
                if yy % 3 == 2 or (xx + off) % 7 == 6:
                    put(img, x, y, shade(base, 0.62))
                    continue
                n += bjit(row, (xx + off) // 7)
            elif kind == "stone":
                row = yy // 6
                off = 6 if row % 2 else 0
                if yy % 6 == 5 or (xx + off) % 12 == 11:
                    put(img, x, y, shade(base, 0.72))
                    continue
                n += bjit(row, (xx + off) // 12) // 2
            else:  # штукатурка
                n += int(coarse[yy // 6, xx // 6])
            put(img, x, y, clip([v + n for v in base]))


def window(img, x, y, wall_c, lit, arch=False, blinds=False, silhouette=False, w=8, h=14):
    frame = shade(wall_c, 1.3)
    rect(img, x - 1, y - 1, w + 2, h + 2, frame)
    if lit:
        top, bot = ((200, 222, 232), (140, 168, 190)) if blinds else ((255, 214, 150), (214, 140, 70))
        for yy in range(h):
            c = mix(top, bot, yy / (h - 1))
            if blinds and yy % 2:
                c = shade(c, 0.8)
            rect(img, x, y + yy, w, 1, c)
        if not blinds:
            rect(img, x, y, 2, h, (150, 84, 60))
            rect(img, x + w - 2, y, 2, h, (150, 84, 60))
        if silhouette:
            sc = (52, 30, 30)
            hx = x + w // 2 - 1
            rect(img, hx, y + h - 9, 3, 3, sc)
            rect(img, hx - 1, y + h - 6, 5, 6, sc)
        mull = (110, 128, 140) if blinds else (120, 76, 48)
    else:
        rect(img, x, y, w, h, (14, 18, 30))
        for i in range(3):
            put(img, x + w - 3 - i, y + 1 + i, (40, 52, 80))
        mull = shade(wall_c, 0.45)
    rect(img, x + w // 2, y, 1, h, mull)
    rect(img, x, y + h // 2 - 1, w, 1, mull)
    if arch:
        for dx, dy in [(0, 0), (1, 0), (0, 1), (w - 1, 0), (w - 2, 0), (w - 1, 1)]:
            put(img, x + dx, y + dy, frame)
        put(img, x - 1, y - 1, wall_c)
        put(img, x + w, y - 1, wall_c)
        rect(img, x + 1, y - 2, w - 2, 1, shade(wall_c, 1.15))
    else:
        rect(img, x - 1, y - 2, w + 2, 1, shade(wall_c, 1.15))
    rect(img, x - 2, y + h + 1, w + 4, 1, shade(wall_c, 1.45))
    rect(img, x - 1, y + h + 2, w + 2, 1, shade(wall_c, 0.6))


def door(img, x, w, wall_c, color=(70, 46, 34), lit=True):
    rect(img, x - 2, 117, w + 4, 33, shade(wall_c, 1.3))
    rect(img, x, 119, w, 31, color)
    rect(img, x, 119, w, 4, (230, 190, 120) if lit else (20, 24, 34))
    rect(img, x, 123, w, 1, shade(color, 0.6))
    for px in range(x + 1, x + w - 1, max(3, w // 2)):
        rect(img, px, 126, max(1, w // 2 - 2), 9, shade(color, 1.25))
        rect(img, px, 138, max(1, w // 2 - 2), 9, shade(color, 1.25))
    put(img, x + w - 3, 136, (210, 180, 100))
    rect(img, x - 3, 148, w + 6, 2, (110, 106, 112))
    HEDGE_SKIP.append((x - 5, x + w + 5))


def shopfront(img, x, w, wall_c, awning, sign=None, sign_c=None):
    rect(img, x - 2, 118, w + 4, 32, shade(wall_c, 0.5))
    for yy in range(24):
        rect(img, x, 121 + yy, w, 1, mix((246, 226, 176), (210, 170, 110), yy / 23))
    for sy in (127, 133, 139):  # полки с товаром
        rect(img, x + 2, sy, w - 4, 1, (120, 90, 60))
        px = x + 3
        while px < x + w - 4:
            c = [(170, 60, 50), (60, 110, 150), (200, 170, 80), (90, 140, 80)][rng.integers(4)]
            hh = int(rng.integers(1, 4))
            rect(img, px, sy - hh, 2, hh, c)
            px += int(rng.integers(3, 5))
    rect(img, x + w // 2 - 10, 140, 20, 5, (70, 50, 40))  # прилавок
    rect(img, x, 145, w, 2, shade(wall_c, 0.6))
    for i in range(w + 6):  # маркиза
        c = awning[(i // 4) % 2]
        rect(img, x - 3 + i, 113, 1, 5, c)
        if i % 4 < 2:
            put(img, x - 3 + i, 118, c)
    rect(img, x - 3, 112, w + 6, 1, shade(awning[0], 1.3))
    for i in range(w + 6):
        blend(img, x - 3 + i, 119, (0, 0, 0), 0.35)
    if sign:  # неоновая вывеска на тёмной плашке над витриной
        tw = text_mask(sign).shape[1]
        rect(img, x + (w - tw) // 2 - 4, 120, tw + 8, 9, (26, 16, 24))
        neon_text(img, sign, x + (w - tw) // 2, 122, sign_c)
    HEDGE_SKIP.append((x - 4, x + w + 4))


def balcony(img, x, y, wall_c, smoker=False):
    if smoker:
        sc = (30, 22, 26)
        rect(img, x + 8, y + 1, 3, 3, sc)
        rect(img, x + 7, y + 4, 5, 10, sc)
        rect(img, x + 11, y + 6, 2, 1, sc)
        put(img, x + 13, y + 6, (255, 150, 70))
        for dx, dy in [(1, 0), (0, -1), (1, -1)]:
            blend(img, x + 13 + dx, y + 6 + dy, (255, 120, 60), 0.3)
        for k in range(5):  # дымок
            blend(img, x + 13 + (k % 2), y + 4 - k, (150, 150, 170), 0.3 - k * 0.05)
    rect(img, x - 5, y + 15, 18, 2, shade(wall_c, 1.4))
    rect(img, x - 4, y + 17, 16, 1, shade(wall_c, 0.5))
    rect(img, x - 5, y + 8, 18, 1, (34, 32, 38))
    for bx in range(x - 5, x + 13, 2):
        rect(img, bx, y + 9, 1, 6, (30, 28, 34))
    for fx in (x - 5, x + 8):
        rect(img, fx, y + 6, 5, 2, (96, 58, 42))
        for k in range(5):
            if rng.random() < 0.8:
                c = [(180, 60, 70), (200, 120, 150), (220, 200, 110), (60, 110, 60)][rng.integers(4)]
                put(img, fx + k, y + 5 - int(rng.integers(0, 2)), shade(c, 0.85))


def fire_escape(img, x0, rows):
    metal, hi = (22, 22, 28), (60, 60, 72)
    for i, r in enumerate(rows):
        py = r + 17
        rect(img, x0, py, 44, 1, hi)
        rect(img, x0, py + 1, 44, 1, metal)
        rect(img, x0, r + 10, 44, 1, metal)
        for bx in range(x0, x0 + 45, 4):
            rect(img, bx, r + 10, 1, 7, metal)
        if i + 1 < len(rows):
            ny = rows[i + 1] + 17
            line(img, x0 + 40, py, x0 + 14, ny, hi)
            line(img, x0 + 40, py + 1, x0 + 14, ny + 1, metal)
    last = rows[-1] + 17
    rect(img, x0 + 4, last, 1, 112 - last, metal)
    rect(img, x0 + 8, last, 1, 112 - last, metal)
    for ly in range(last + 2, 112, 3):
        rect(img, x0 + 4, ly, 5, 1, metal)


def building(img, x0, x1, top, kind, base, lit_p=0.3, arch=False, blinds=False,
             skip=(), ground_windows=True, drain=True, ac=False):
    wall(img, x0, x1, top, kind, base)
    w = x1 - x0
    rect(img, x0, top, w, 2, shade(base, 1.35))
    rect(img, x0, top + 2, w, 1, shade(base, 1.12))
    rect(img, x0, top + 3, w, 1, shade(base, 0.6))
    rect(img, x0, 113, w, 1, shade(base, 1.2))
    rect(img, x0, 114, w, 1, shade(base, 0.65))
    rect(img, x0, GROUND - 4, w, 4, shade(base, 0.7))
    rows = [r for r in (95, 70, 45, 20) if r >= top + 7]
    for r in rows[:-1]:
        rect(img, x0, r - 6, w, 1, shade(base, 1.18))
        rect(img, x0, r - 5, w, 1, shade(base, 0.68))
    n = (w - 10) // 16
    start = x0 + (w - (n * 16 - 8)) // 2
    cols = [start + i * 16 for i in range(n)]
    for r in rows:
        for cx in cols:
            if (r, cx) in skip:
                continue
            window(img, cx, r, base, rng.random() < lit_p, arch, blinds, silhouette=rng.random() < 0.15)
            if ac and rng.random() < 0.15:
                rect(img, cx, r + 17, 7, 5, (96, 100, 106))
                for gx in range(cx + 1, cx + 6, 2):
                    rect(img, gx, r + 18, 1, 3, (60, 62, 68))
    if ground_windows:
        for cx in cols:
            window(img, cx, 124, base, rng.random() < lit_p * 0.7, arch, blinds)
    rect(img, x0, top, 1, GROUND - top, shade(base, 0.5))
    rect(img, x1 - 1, top, 1, GROUND - top, shade(base, 0.78))
    if drain:
        rect(img, x1 - 4, top + 4, 2, GROUND - top - 4, (30, 32, 40))
        for by in range(top + 12, GROUND, 22):
            rect(img, x1 - 5, by, 4, 1, (60, 62, 72))
    return rows, cols


def clear_ground_floor(img, x0, x1, base, kind, top):
    """Стирает окна первого этажа на участке (под дверь/витрину)."""
    sub = canvas(x1 - x0)
    wall(sub, 0, x1 - x0, top, kind, base)
    img[116:GROUND - 4, x0:x1] = sub[116:GROUND - 4]


def gen_facade():
    img = canvas(WORLD)

    # A: кирпич, 0..150
    a = shade((104, 58, 46), NIGHT)
    building(img, 0, 150, 34, "brick", a, lit_p=0.3, ac=True)
    clear_ground_floor(img, 52, 80, a, "brick", 34)
    door(img, 58, 14, a)

    # переулок 150..176: верёвки с бельём
    for ly, cl in [(68, [(122, 60, 60), (70, 90, 124), (150, 140, 110), (90, 110, 80)]),
                   (92, [(140, 120, 150), (110, 70, 60), (160, 150, 130)])]:
        for x in range(146, 181):
            t = (x - 146) / 34
            put(img, x, ly + round(3 * math.sin(math.pi * t)), (40, 40, 46))
        x = 150
        for c in cl:
            cw = int(rng.integers(3, 6))
            cy = ly + round(3 * math.sin(math.pi * (x - 146) / 34)) + 1
            rect(img, x, cy, cw, int(rng.integers(4, 8)), shade(c, 0.75))
            x += cw + 2
    HEDGE_SKIP.append((148, 178))

    # B: штукатурка, кафе, балкон, 176..336
    b = shade((78, 98, 88), NIGHT)
    rows, cols = building(img, 176, 336, 44, "stucco", b, lit_p=0.35)
    clear_ground_floor(img, 178, 334, b, "stucco", 44)
    shopfront(img, 188, 100, b, [(150, 40, 60), (210, 200, 190)], "КАФЕ", (255, 90, 170))
    door(img, 302, 14, b)
    balcony(img, cols[5], rows[1], b)

    # C: светлый, арочные окна, 336..500
    c = shade((128, 112, 82), NIGHT)
    rows, cols = building(img, 336, 500, 30, "stucco", c, lit_p=0.28, arch=True)
    clear_ground_floor(img, 404, 432, c, "stucco", 30)
    door(img, 410, 14, c, color=(56, 40, 32))

    # D: полицейский участок, камень, 500..700
    d = shade((86, 92, 106), NIGHT)
    rows, cols = building(img, 500, 700, 40, "stone", d, lit_p=0.6, blinds=True,
                          skip={(95, cx) for cx in range(590, 606)}, drain=False)
    clear_ground_floor(img, 576, 624, d, "stone", 40)
    door(img, 590, 20, d, color=(42, 32, 28))
    rect(img, 599, 126, 1, 21, (24, 18, 16))
    for cx in (584, 613):  # колонны
        rect(img, cx, 117, 4, 31, shade(d, 1.35))
        rect(img, cx + 3, 117, 1, 31, shade(d, 0.9))
    for i in range(6):  # фронтон
        rect(img, 582 + i * 3, 116 - i, 36 - i * 6, 1, shade(d, 1.4 - i * 0.04))
    rect(img, 581, 100, 38, 9, (18, 28, 70))
    rect(img, 581, 100, 38, 1, (60, 80, 140))
    neon_text(img, "ПОЛИЦИЯ", 583, 102, (190, 220, 255))
    for lx in (578, 621):  # настенные фонари
        rect(img, lx, 120, 2, 3, (255, 236, 190))
        rect(img, lx, 123, 2, 1, (30, 30, 34))
    HEDGE_SKIP.append((574, 626))

    # переулок 700..722
    HEDGE_SKIP.append((698, 724))

    # E: тёмный кирпич, пожарная лестница, 722..880
    e = shade((84, 44, 40), NIGHT)
    rows, cols = building(img, 722, 880, 38, "brick", e, lit_p=0.25, ac=True)
    fire_escape(img, cols[1] - 6, rows)
    clear_ground_floor(img, 804, 830, e, "brick", 38)
    door(img, 810, 14, e)

    # F: серо-голубая штукатурка, курильщик на балконе, 880..1040
    f = shade((82, 92, 112), NIGHT)
    rows, cols = building(img, 880, 1040, 48, "stucco", f, lit_p=0.3)
    window(img, cols[4], rows[1], f, True)
    balcony(img, cols[4], rows[1], f, smoker=True)
    clear_ground_floor(img, 944, 972, f, "stucco", 48)
    door(img, 950, 14, f, color=(40, 50, 60))

    # G: коричневый кирпич, круглосуточный магазин, 1040..1200
    g = shade((96, 64, 48), NIGHT)
    building(img, 1040, 1200, 36, "brick", g, lit_p=0.3, ac=True)
    clear_ground_floor(img, 1042, 1198, g, "brick", 36)
    shopfront(img, 1056, 96, g, [(40, 110, 80), (200, 210, 200)], "24", (90, 255, 140))
    door(img, 1166, 14, g)
    save(img, "facade.png")


# ---------------------------------------------------- кусты, тротуар, дорога
def gen_ground():
    img = canvas(WORLD)
    # тёмная земля в переулках
    for x0, x1 in [(150, 176), (700, 722)]:
        for y in range(132, GROUND):
            rect(img, x0, y, x1 - x0, 1, mix((16, 16, 22), (34, 32, 38), (y - 132) / 18))
        rect(img, x0 + 6, 138, 9, 12, (40, 46, 44))  # мусорный бак
        rect(img, x0 + 5, 137, 11, 2, (58, 64, 62))
    # кусты
    for x in range(WORLD):
        if any(a <= x < b for a, b in HEDGE_SKIP):
            continue
        top = 139 + round(1.5 * math.sin(x * 0.45) + 1.2 * math.sin(x * 0.13 + 1) + rng.random())
        for y in range(top, GROUND):
            k = rng.random()
            col = (22, 40, 30) if k < 0.4 else (30, 54, 38) if k < 0.85 else (44, 72, 50)
            put(img, x, y, col)
        put(img, x, top, (56, 86, 60))
        if rng.random() < 0.05:
            fc = [(170, 60, 80), (190, 110, 150), (200, 180, 100)][rng.integers(3)]
            put(img, x, top + int(rng.integers(1, 6)), fc)
    # тротуар
    for y in range(GROUND, 166):
        row = (y - GROUND) // 4
        for x in range(WORLD):
            off = 4 if row % 2 else 0
            if (y - GROUND) % 4 == 3 or (x + off) % 8 == 7:
                put(img, x, y, (52, 50, 58))
            else:
                j = bjit(row, (x + off) // 8) // 2 + int(rng.integers(-2, 3))
                put(img, x, y, clip([76 + j, 72 + j, 80 + j]))
    # бордюр и водосток
    rect(img, 0, 166, WORLD, 1, (132, 128, 134))
    rect(img, 0, 167, WORLD, 2, (104, 100, 108))
    rect(img, 0, 169, WORLD, 1, (26, 26, 32))
    # дорога
    noise = rng.integers(-4, 5, (H - 170, WORLD))
    for y in range(170, H):
        for x in range(WORLD):
            n = int(noise[y - 170, x])
            put(img, x, y, clip([34 + n, 36 + n, 44 + n]))
    for _ in range(14):  # заплатки
        px, py = int(rng.integers(0, WORLD - 40)), int(rng.integers(172, 220))
        rect(img, px, py, int(rng.integers(12, 40)), int(rng.integers(3, 8)), (28, 30, 36))
    for _ in range(10):  # лужи
        cx, cy = int(rng.integers(20, WORLD - 20)), int(rng.integers(176, 214))
        rx, ry = int(rng.integers(10, 26)), int(rng.integers(2, 4))
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1:
                    put(img, x, y, (48, 56, 80) if rng.random() > 0.1 else (90, 100, 132))
    for x in range(0, WORLD, 24):  # разметка
        rect(img, x, 201, 14, 1, (112, 106, 84))
    for mx in (380, 860):  # люки
        for y in range(186, 191):
            for x in range(mx - 6, mx + 7):
                if ((x - mx) / 6) ** 2 + ((y - 188) / 2.4) ** 2 <= 1:
                    put(img, x, y, (52, 52, 58) if (x + y) % 2 else (40, 40, 46))
    save(img, "ground.png")


# ------------------------------------ фонари и столбы (перед персонажем)
def lamp_post(img, x):
    post, hi = (22, 24, 32), (52, 56, 70)
    rect(img, x, 64, 2, 102, post)
    rect(img, x + 1, 64, 1, 102, hi)
    rect(img, x - 1, 154, 4, 12, post)
    rect(img, x - 2, 162, 6, 4, post)
    rect(img, x, 61, 2, 3, post)
    rect(img, x + 1, 59, 6, 2, post)
    rect(img, x + 5, 58, 8, 4, (30, 32, 40))
    rect(img, x + 5, 58, 8, 1, (60, 62, 74))
    rect(img, x + 6, 62, 6, 1, (255, 232, 176))
    put(img, x + 5, 62, (120, 100, 70))
    put(img, x + 12, 62, (120, 100, 70))


def gen_props():
    img = canvas(WORLD)
    for x in LAMPS:
        lamp_post(img, x)
    # пожарный гидрант
    rect(img, 160, 157, 5, 9, (128, 34, 34))
    rect(img, 159, 159, 7, 2, (150, 44, 44))
    rect(img, 161, 155, 3, 2, (150, 44, 44))
    rect(img, 164, 158, 1, 8, (80, 20, 22))
    # тумба экстренной связи
    rect(img, 538, 142, 6, 24, (28, 40, 92))
    rect(img, 543, 142, 1, 24, (18, 26, 60))
    rect(img, 538, 140, 6, 2, (60, 80, 150))
    rect(img, 539, 138, 4, 2, (120, 190, 255))
    rect(img, 539, 147, 4, 5, (16, 18, 26))
    rect(img, 539, 154, 4, 1, (200, 200, 210))
    # знак «стоянка запрещена»
    rect(img, 704, 124, 1, 42, (40, 42, 50))
    for y in range(116, 125):
        for x in range(700, 710):
            d = math.hypot(x - 704.5, y - 120)
            if d <= 4.5:
                put(img, x, y, (170, 30, 36) if d > 3 else (40, 70, 160))
    line(img, 702, 118, 707, 123, (170, 30, 36))
    # урна
    rect(img, 1000, 155, 7, 11, (40, 44, 46))
    rect(img, 999, 154, 9, 2, (70, 74, 76))
    for x in range(1001, 1006, 2):
        rect(img, x, 157, 1, 8, (30, 32, 34))
    save(img, "props.png")


# -------------------------------------------- передний план (силуэты)
def gen_foreground():
    w = 1520
    img = canvas(w)
    sil = (6, 7, 10)
    x = 140
    kinds = ["pole", "bush", "fence", "bush", "tree", "pole", "bush", "fence"]
    k = 0
    while x < w - 40:
        kind = kinds[k % len(kinds)]
        k += 1
        if kind == "pole":
            rect(img, x, 0, 5, H, sil)
            rect(img, x + 4, 0, 1, H, (24, 30, 46))
            for by in range(40, H, 46):
                rect(img, x - 1, by, 7, 2, sil)
        elif kind == "bush":
            for _ in range(6):
                blob(img, x + int(rng.integers(-30, 30)), int(rng.integers(205, 230)), int(rng.integers(14, 26)), sil)
        elif kind == "fence":
            fw = int(rng.integers(60, 100))
            rect(img, x, 186, fw, 2, sil)
            for px in range(x, x + fw, 30):
                rect(img, px, 184, 3, H - 184, sil)
            for yy in range(188, H):
                for xx in range(x, x + fw):
                    if (xx + yy) % 6 == 0 or (xx - yy) % 6 == 0:
                        put(img, xx, yy, sil)
        elif kind == "tree":
            rect(img, x, 110, 7, H - 110, sil)
            line(img, x + 3, 140, x + 30, 108, sil)
            line(img, x + 3, 130, x - 22, 100, sil)
            for _ in range(14):
                blob(img, x + int(rng.integers(-50, 50)), int(rng.integers(20, 110)), int(rng.integers(12, 24)), sil, 0.5)
        x += int(rng.integers(170, 300))
    # холодный контур сверху у силуэтов
    a = img[:, :, 3] > 0
    edge = a & ~np.roll(a, 1, 0)
    img[edge, :3] = (22, 28, 44)
    save(img, "foreground.png")


# --------------------------------------------------- световые текстуры
def gen_light_textures():
    def cone(w, h, top_hw, peak, name):
        img = canvas(w, h)
        for y in range(h):
            hw = top_hw + (w / 2 - top_hw) * y / (h - 1)
            for x in range(w):
                d = abs(x + 0.5 - w / 2) / hw
                if d < 1:
                    a = peak * (1 - y / h) ** 1.1 * (1 - d * d)
                    img[y, x] = (255, 255, 255, int(a))
        save(img, name)

    cone(48, 110, 3, 200, "cone.png")
    cone(40, 160, 1.5, 220, "beam.png")
    g = canvas(16, 16)
    for y in range(16):
        for x in range(16):
            r = math.hypot(x - 7.5, y - 7.5) / 8
            if r < 1:
                g[y, x] = (255, 255, 255, int(255 * (1 - r) ** 2))
    save(g, "glow.png")


# ------------------------------------------------------------- машины
def car(body, name, police=False, w=60, h=22):
    img = canvas(w, h)
    roof = body
    rect(img, 2, 10, w - 4, 7, body)
    rect(img, 1, 11, w - 2, 5, body)
    rect(img, 2, 10, w - 4, 1, shade(body, 1.3))
    rect(img, 1, 15, w - 2, 2, shade(body, 0.6))
    for y in range(3, 10):
        t = (y - 3) / 6
        l, r = int(20 - 6 * t), int(40 + 6 * t)
        rect(img, l, y, r - l, 1, roof)
    rect(img, 20, 3, 20, 1, shade(roof, 1.3))
    for y in range(5, 10):
        t = (y - 3) / 6
        l, r = int(20 - 6 * t) + 2, int(40 + 6 * t) - 2
        rect(img, l, y, r - l, 1, (40, 52, 74))
    rect(img, 30, 4, 2, 6, roof)
    put(img, 36, 5, (110, 130, 160))
    put(img, 35, 6, (110, 130, 160))
    if police:
        rect(img, 2, 12, w - 4, 2, (36, 64, 150))
        rect(img, 2, 14, w - 4, 1, (220, 224, 230))
        rect(img, 25, 1, 5, 2, (160, 30, 40))
        rect(img, 30, 1, 5, 2, (40, 70, 180))
        rect(img, 24, 2, 12, 1, (60, 60, 66))
    else:
        rect(img, 2, 13, w - 4, 1, shade(body, 1.5))
    for cx in (13, w - 13):
        rect(img, cx - 5, 12, 11, 4, (12, 12, 14))
        for y in range(13, 22):
            for x in range(cx - 4, cx + 5):
                if math.hypot(x - cx, y - 17) <= 4.2:
                    put(img, x, y, (18, 18, 20))
        rect(img, cx - 1, 16, 2, 2, (120, 120, 128))
    rect(img, w - 2, 11, 2, 2, (255, 236, 180))
    rect(img, 0, 11, 2, 2, (210, 40, 40))
    rect(img, w - 3, 15, 3, 1, (150, 150, 156))
    rect(img, 0, 15, 3, 1, (150, 150, 156))
    save(img, name)


def gen_drone():
    img = canvas(14, 6)
    rect(img, 1, 2, 12, 1, (28, 30, 36))
    rect(img, 5, 1, 4, 4, (40, 42, 52))
    rect(img, 0, 1, 3, 1, (100, 104, 116))
    rect(img, 11, 1, 3, 1, (100, 104, 116))
    put(img, 1, 3, (230, 40, 40))
    put(img, 12, 3, (40, 230, 90))
    put(img, 7, 5, (190, 230, 255))
    save(img, "drone.png")


# ---------------------------------------------------- полицейский (8 кадров)
def gen_officer():
    FW, FH, N = 20, 40, 8
    img = canvas(FW * N, FH)
    cap, cap_hi, visor, badge = (24, 30, 58), (48, 58, 98), (10, 10, 14), (226, 196, 100)
    skin, skin_d, hair = (214, 164, 130), (168, 118, 94), (40, 28, 22)
    coat, coat_d, coat_hi = (32, 40, 76), (20, 26, 50), (54, 66, 112)
    pants, pants_d, shoe, belt = (26, 30, 52), (16, 18, 32), (8, 8, 10), (12, 12, 16)

    A = [3, 1, -1, -3, -1, 1]
    B = [-3, -1, 1, 3, 1, -1]
    frames = [(1, -1, 0, 0, 0, 0, 0), (1, -1, 0, 0, 0, 1, 0)]  # покой: дыхание
    for i in range(6):
        lift_a = 1 if i in (4, 5) else 0
        lift_b = 1 if i in (1, 2) else 0
        bob = 1 if i in (0, 3) else 0
        frames.append((A[i], B[i], lift_a, lift_b, bob, 0, -round(A[i] * 0.7)))

    for f, (da, db, la, lb, bob, breath, arm) in enumerate(frames):
        ox = f * FW

        def P(x, y, c):
            if 0 <= x < FW:
                put(img, ox + x, y, c)

        def R(x, y, w, h, c):
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    P(xx, yy, c)

        def leg(dx, lift, c, cd):
            hip = 28 + bob
            end = 37 - lift
            for y in range(hip, end):
                t = (y - hip) / max(1, end - hip)
                x = round(8 + dx * t)
                R(x, y, 3, 1, c)
                P(x, y, cd)
            x = 8 + dx
            R(x, end, 5, 2, shoe)

        def arm_(dx, c, cd, sx):
            sy = 15 + bob + breath
            for y in range(sy, sy + 10):
                t = (y - sy) / 9
                x = round(sx + dx * t)
                R(x, y, 2, 1, c)
                P(x, y, cd)
            hx = round(sx + dx)
            R(hx, sy + 10, 2, 2, skin)

        up = bob + breath
        leg(db, lb, pants_d, pants_d)
        arm_(-arm, coat_d, coat_d, 8)
        # туловище / шинель
        R(7, 14 + up, 7, 1, coat)
        R(6, 15 + up, 9, 14 - up, coat)
        R(6, 15 + up, 2, 14 - up, coat_d)
        R(13, 15 + up, 2, 12 - up, coat_hi)
        R(11, 14 + up, 2, 2, (190, 196, 210))
        R(6, 25 + up, 9, 1, belt)
        P(12, 25 + up, badge)
        P(12, 18 + up, (200, 206, 220))
        for by in (19, 22):
            P(14, by + up, shade(badge, 0.8))
        # голова
        R(9, 7 + up, 6, 7, skin)
        R(8, 7 + up, 2, 5, hair)
        P(10, 10 + up, skin_d)
        P(13, 9 + up, (24, 18, 18))
        P(15, 10 + up, skin)
        R(10, 13 + up, 4, 1, skin_d)
        # фуражка
        R(7, 2 + up, 8, 4, cap)
        R(8, 2 + up, 6, 1, cap_hi)
        R(7, 5 + up, 8, 1, (12, 14, 26))
        R(12, 6 + up, 5, 1, visor)
        P(12, 3 + up, badge)
        leg(da, la, pants, pants_d)
        arm_(arm, coat_hi, coat, 11)
    save(img, "officer.png")


if __name__ == "__main__":
    print("Генерирую в", OUT)
    gen_sky()
    gen_far()
    gen_mid()
    gen_facade()
    gen_ground()
    gen_props()
    gen_foreground()
    gen_light_textures()
    car((180, 186, 196), "police_car.png", police=True)
    car((110, 40, 40), "car_a.png")
    car((50, 96, 100), "car_b.png")
    car((150, 130, 80), "car_c.png")
    gen_drone()
    gen_officer()
