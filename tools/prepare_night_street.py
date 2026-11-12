#!/usr/bin/env python3
"""
Подготовка ассетов для сцены «Улица» (night_street.tscn) из пакета
references/US_1997_Night_Street_Godot.

- копирует слои и пропсы в assets/night_street/;
- перерисовывает голову фонаря (в пакете вместо плафона вырезано световое пятно);
- собирает спрайт-лист полицейского из references/junior_officer_godot_pack:
  кадр покоя + 8 кадров ходьбы, ячейки 80×160, ноги на общей линии, жёсткая альфа;
- рисует текстуры для света: мягкое пятно (glow.png) и конус фонаря (cone.png);
- перекрашивает седан в несколько цветов для проезжающих машин (props/cars/);
- собирает из модулей фасадов два слоя города справа, за забором
  (layers/10_city_mid.png, layers/11_city_near.png);
- рисует капли и брызги для дождя (fx/raindrop.png, fx/splash.png);
- делает маску «погасшего» окна (fx/window_off.png) — затемняет только светлое стекло.

Запуск из корня проекта:  python3 tools/prepare_night_street.py
"""
import os
import shutil

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PACK = os.path.join(ROOT, "references", "US_1997_Night_Street_Godot")
OUT = os.path.join(ROOT, "assets", "night_street")

LAYERS = [
    "00_sky.png", "01_distant_skyline.png",
    "03_brick_facades.png", "04_lot_fence.png", "05_sidewalk_and_curb.png",
    "06_wet_asphalt.png", "08_optional_light_haze.png",
]
PROPS = [
    "police_cruiser_1997.png", "sedan_1990s.png", "streetlamp_amber.png",
    "payphone_booth.png", "trash_can.png", "tree_01.png", "one_way_sign.png",
]
OFFICER_PACK = os.path.join(ROOT, "references", "junior_officer_godot_pack", "frames")
CELL_W, CELL_H = 80, 160
BASELINE = 154  # нижняя строка ступней в ячейке


def officer_sheet():
    """Кадр покоя + 8 кадров ходьбы в одну строку. Кадр покоя в пакете ниже кадров
    ходьбы (115 px против 123), поэтому он масштабируется до их роста."""
    paths = [os.path.join(OFFICER_PACK, "idle_right", "idle_right_01.png")]
    paths += [os.path.join(OFFICER_PACK, "walk_right", "walk_right_%02d.png" % i) for i in range(1, 9)]
    frames = [Image.open(p).convert("RGBA") for p in paths]

    def bbox(im):
        a = np.array(im)[:, :, 3]
        ys, xs = np.nonzero(a > 100)
        return xs.min(), ys.min(), xs.max(), ys.max()

    walk_h = np.mean([bbox(f)[3] - bbox(f)[1] for f in frames[1:]])
    sheet = Image.new("RGBA", (CELL_W * len(frames), CELL_H))
    for i, f in enumerate(frames):
        x0, y0, x1, y1 = bbox(f)
        part = f.crop((0, y0, CELL_W, y1 + 1))
        if i == 0:
            k = walk_h / (y1 - y0)
            part = part.resize((round(CELL_W * k), round(part.height * k)), Image.NEAREST)
            part = part.crop(((part.width - CELL_W) // 2, 0, (part.width - CELL_W) // 2 + CELL_W, part.height))
        cell = Image.new("RGBA", (CELL_W, CELL_H))
        cell.alpha_composite(part, (0, BASELINE + 1 - part.height))
        arr = np.array(cell)
        arr[:, :, 3] = np.where(arr[:, :, 3] >= 128, 255, 0)
        sheet.alpha_composite(Image.fromarray(arr), (i * CELL_W, 0))
    sheet.save(os.path.join(OUT, "officer_sheet.png"))
    print("   officer_sheet.png", sheet.width, "x", sheet.height, "(покой + 8 кадров ходьбы)")


def light_textures():
    os.makedirs(os.path.join(OUT, "fx"), exist_ok=True)
    n = 64
    yy, xx = np.mgrid[:n, :n]
    r = np.hypot(xx - (n - 1) / 2, yy - (n - 1) / 2) / (n / 2)
    a = np.clip(1 - r, 0, 1) ** 2
    img = np.zeros((n, n, 4), np.uint8)
    img[:, :, :3] = 255
    img[:, :, 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(OUT, "fx", "glow.png"))
    w, h = 96, 160
    yy, xx = np.mgrid[:h, :w]
    half = 6 + (w / 2 - 6) * yy / (h - 1)
    d = np.abs(xx + 0.5 - w / 2) / half
    a = np.clip(1 - d * d, 0, 1) * (1 - yy / h) ** 0.8
    img = np.zeros((h, w, 4), np.uint8)
    img[:, :, :3] = 255
    img[:, :, 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(OUT, "fx", "cone.png"))
    print("   fx/glow.png, fx/cone.png")


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def fix_lamp(path):
    """Стирает неверно вырезанную голову фонаря и рисует новую: кронштейн, колпак, рассеиватель."""
    im = np.array(Image.open(path).convert("RGBA"))
    im[0:37, 54:] = 0          # всё справа от столба выше его верха
    im[0:30, 40:60] = 0
    im[37:44, 54:64] = 0       # обрывок старого кронштейна

    def px(x, y, c, a=255):
        if 0 <= y < im.shape[0] and 0 <= x < im.shape[1]:
            im[y, x] = (*c, a)

    dark, mid, hi = (26, 25, 32), (46, 44, 52), (92, 86, 84)
    # верх столба с колпачком
    for y in range(30, 37):
        for x in range(46, 54):
            px(x, y, dark if x < 50 else mid)
    for x in range(45, 55):
        px(x, 29, hi if 47 <= x <= 51 else mid)
    # изогнутый кронштейн: дуга от столба вверх-вправо к плафону
    for i in range(0, 41):
        t = i / 40
        x = 50 + t * 30
        y = 31 - 16 * (1 - (1 - t) ** 2)
        for d in range(3):
            px(round(x), round(y) + d, hi if d == 0 else dark)
    # колпак: приплюснутый купол
    cx, top = 90, 9
    for y in range(top, top + 10):
        half = 7 + min(y - top, 5) * 2 if y < top + 6 else 17
        for x in range(cx - half, cx + half + 1):
            c = mid
            if y == top or (y < top + 3 and abs(x - cx) > half - 2):
                c = hi
            elif y == top + 9:
                c = dark
            px(x, y, c)
    for x in range(cx - 2, cx + 3):  # шишечка сверху
        px(x, top - 1, hi)
        px(x, top - 2, mid)
    # рассеиватель: светится, ступенчато сужается книзу
    warm_c, warm_e = (255, 236, 182), (232, 160, 84)
    for k, half in enumerate((15, 13, 10, 6)):
        y = top + 10 + k
        for x in range(cx - half, cx + half + 1):
            px(x, y, mix(warm_c, warm_e, abs(x - cx) / 16 + k * 0.08))
    Image.fromarray(im).save(path)


CAR_VARIANTS = {  # имя: (оттенок 0..1, насыщенность, множитель яркости)
    "car_maroon": (0.98, 0.45, 1.0),
    "car_green": (0.38, 0.3, 0.9),
    "car_navy": (0.61, 0.55, 0.9),
    "car_black": (0.62, 0.15, 0.55),
}


def car_variants():
    """Седан из пакета в других цветах: меняется оттенок кузова, а тёмные стёкла
    и шины и яркие фары/хром остаются как были."""
    import colorsys
    src = np.array(Image.open(os.path.join(OUT, "props", "sedan_1990s.png")).convert("RGBA")).astype(float) / 255
    os.makedirs(os.path.join(OUT, "props", "cars"), exist_ok=True)
    shutil.copy2(os.path.join(OUT, "props", "sedan_1990s.png"), os.path.join(OUT, "props", "cars", "car_beige.png"))
    h, w = src.shape[:2]
    for name, (hue, sat, val_k) in CAR_VARIANTS.items():
        out = src.copy()
        for y in range(h):
            for x in range(w):
                r, g, b, a = src[y, x]
                if a == 0:
                    continue
                hh, ss, vv = colorsys.rgb_to_hsv(r, g, b)
                if vv < 0.12 or vv > 0.7:
                    continue  # стёкла, шины, фары, хром
                k = np.clip((vv - 0.12) / 0.1, 0, 1)  # мягкий переход у тёмных деталей
                nr, ng, nb = colorsys.hsv_to_rgb(hue, sat, min(1.0, vv * val_k))
                out[y, x, :3] = (1 - k) * np.array([r, g, b]) + k * np.array([nr, ng, nb])
        Image.fromarray((out * 255).astype(np.uint8)).save(os.path.join(OUT, "props", "cars", name + ".png"))
    print("   props/cars/: car_beige +", ", ".join(CAR_VARIANTS))


MODULES = os.path.join(PACK, "assets", "modules")


def _module(name, scale):
    im = Image.open(os.path.join(MODULES, name + ".png")).convert("RGBA")
    return im.resize((round(im.width * scale), round(im.height * scale)), Image.NEAREST)


def _tower(upper, ground, width, height):
    """Фасад нужной ширины и высоты: внизу «первый этаж», выше — повторённые этажи."""
    col = Image.new("RGBA", (width, height))
    y = height - ground.height
    for x in range(0, width, ground.width):
        col.alpha_composite(ground.crop((0, 0, min(ground.width, width - x), ground.height)), (x, y))
    while y > 0:
        y -= upper.height
        for x in range(0, width, upper.width):
            part = upper.crop((0, max(0, -y), min(upper.width, width - x), upper.height))
            col.alpha_composite(part, (x, max(0, y)))
    return col


def _atmosphere(arr, fog, amount, dark):
    """Ночная дымка: стены темнеют и уходят в цвет тумана, горящие окна — меньше."""
    rgb = arr[:, :, :3].astype(float)
    lum = rgb @ [0.299, 0.587, 0.114]
    warm = np.clip((rgb[:, :, 0] - rgb[:, :, 2] - 20) / 60, 0, 1) * np.clip((lum - 70) / 70, 0, 1)
    k = amount * (1 - 0.75 * warm)[:, :, None]
    out = rgb * dark * (1 - k) + np.array(fog) * k
    arr[:, :, :3] = np.clip(out, 0, 255).astype(np.uint8)
    return arr


def city_layer(name, scale, x_from, x_to, heights, fog_amount, dark, seed):
    W, H, BASE = 2700, 724, 480
    rng = np.random.default_rng(seed)
    upper_mods = [_module(n, scale) for n in ("brick_apartments", "fire_escape")]
    ground_mods = [_module(n, scale) for n in ("brick_apartments", "brick_stoop", "fire_escape")]
    layer = Image.new("RGBA", (W, H))
    x = x_from
    i = 0
    while x < x_to:
        width = int(rng.integers(2, 4) * upper_mods[0].width * rng.uniform(0.55, 0.85))
        height = int(heights[i % len(heights)] * scale)
        up = upper_mods[rng.integers(len(upper_mods))]
        gr = ground_mods[rng.integers(len(ground_mods))]
        b = _tower(up, gr, width, height)
        a = np.array(b)
        # карниз и тень сбоку
        a[0:max(3, round(6 * scale)), :, :3] = (a[0:max(3, round(6 * scale)), :, :3] * 0.55).astype(np.uint8)
        a[:, :max(2, round(4 * scale)), :3] = (a[:, :max(2, round(4 * scale)), :3] * 0.6).astype(np.uint8)
        a[:, :, 3] = 255
        b = Image.fromarray(a)
        top = BASE - height
        layer.alpha_composite(b, (x, top))
        # иногда — бак для воды на крыше (тёмный силуэт)
        if rng.random() < 0.45:
            tx = x + int(rng.uniform(0.2, 0.7) * width)
            tw, th = round(34 * scale), round(30 * scale)
            d = ImageDraw.Draw(layer)
            d.rectangle((tx, top - th, tx + tw, top - round(10 * scale)), fill=(22, 20, 26, 255))
            d.polygon([(tx - 2, top - th), (tx + tw // 2, top - th - round(12 * scale)), (tx + tw + 2, top - th)], fill=(18, 16, 22, 255))
            for lx in (tx + 3, tx + tw - 5):
                d.rectangle((lx, top - round(10 * scale), lx + 2, top), fill=(18, 16, 22, 255))
        x += width + int(rng.integers(0, round(26 * scale)))
        i += 1
    arr = _atmosphere(np.array(layer), (30, 34, 56), fog_amount, dark)
    Image.fromarray(arr).save(os.path.join(OUT, "layers", name))
    print("   layers/%s" % name)


def city_layers():
    city_layer("10_city_mid.png", 0.95, 900, 2700, [300, 230, 340, 260, 210, 320], 0.55, 0.7, 11)
    city_layer("11_city_near.png", 1.45, 950, 2700, [170, 135, 195, 125, 180], 0.3, 0.8, 23)


def rain_textures():
    """Капля — тонкая вертикальная черта, светлее к низу; брызги — короткий штрих."""
    drop = np.zeros((10, 1, 4), np.uint8)
    drop[:, :, :3] = 255
    drop[:, 0, 3] = (np.linspace(0.15, 1.0, 10) * 255).astype(np.uint8)
    Image.fromarray(drop).save(os.path.join(OUT, "fx", "raindrop.png"))
    splash = np.zeros((2, 5, 4), np.uint8)
    splash[:, :, :3] = 255
    splash[0, :, 3] = (80, 200, 255, 200, 80)
    splash[1, :, 3] = (0, 120, 160, 120, 0)
    Image.fromarray(splash).save(os.path.join(OUT, "fx", "splash.png"))
    print("   fx/raindrop.png, fx/splash.png")


WINDOW_OFF_RECT = (215, 235, 276, 320)  # окно 2-го этажа слева на 03_brick_facades.png


def window_off_mask():
    """Тёмная маска поверх светлого стекла окна: включаешь — окно «гаснет»,
    рама и переплёт остаются видны."""
    x0, y0, x1, y1 = WINDOW_OFF_RECT
    fac = np.array(Image.open(os.path.join(OUT, "layers", "03_brick_facades.png")).convert("RGBA"), float)
    part = fac[y0:y1, x0:x1]
    lum = part[:, :, :3] @ [0.299, 0.587, 0.114]
    warm = np.clip((part[:, :, 0] - part[:, :, 2] - 10) / 40, 0, 1)  # светящееся стекло — тёплое
    a = np.clip((lum - 30) / 45, 0, 1) * warm * 0.96
    img = np.zeros(part.shape, np.uint8)
    img[:, :, :3] = (16, 17, 24)
    img[:, :, 3] = (a * 255).astype(np.uint8)
    Image.fromarray(img).save(os.path.join(OUT, "fx", "window_off.png"))
    print("   fx/window_off.png", WINDOW_OFF_RECT)


def main():
    for sub, names in (("layers", LAYERS), ("props", PROPS)):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
        for n in names:
            shutil.copy2(os.path.join(PACK, "assets", sub, n), os.path.join(OUT, sub, n))
            print("  ", sub + "/" + n)
    fix_lamp(os.path.join(OUT, "props", "streetlamp_amber.png"))
    print("   props/streetlamp_amber.png: голова фонаря перерисована")

    officer_sheet()
    light_textures()
    rain_textures()
    city_layers()
    car_variants()
    window_off_mask()


if __name__ == "__main__":
    main()
