#!/usr/bin/env python3
"""
Синтез звуков для сцены «Улица»: дождь (петля), гром (2 варианта),
проезжающая машина (петля: шины по мокрому асфальту + мотор).
Результат: assets/night_street/sfx/*.wav (16 бит, 44.1 кГц).

Запуск из корня проекта:  python3 tools/gen_street_sounds.py   (нужны numpy и scipy)
Любой файл можно заменить записанным звуком с тем же именем.
"""
import os

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "night_street", "sfx"))
rng = np.random.default_rng(1997)


def band(x, lo=None, hi=None, order=2):
    if lo and hi:
        sos = butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    elif lo:
        sos = butter(order, lo, "highpass", fs=SR, output="sos")
    else:
        sos = butter(order, hi, "lowpass", fs=SR, output="sos")
    return sosfilt(sos, x)


def brown(n):
    x = np.cumsum(rng.standard_normal(n))
    return band(x - np.mean(x), lo=20)


def seamless(x, fade):
    """Петля без щелчка: хвост плавно перетекает в начало."""
    body = x[:-fade].copy()
    t = np.linspace(0, 1, fade)
    if body.ndim == 2:
        t = t[:, None]
    body[:fade] = body[:fade] * t + x[-fade:] * (1 - t)
    return body


def save(name, x, peak=0.8):
    os.makedirs(OUT, exist_ok=True)
    x = x / np.max(np.abs(x)) * peak
    wavfile.write(os.path.join(OUT, name), SR, (x * 32767).astype(np.int16))
    print("  ", name, "%.1f с" % (len(x) / SR))


def rain_loop(seconds=12.0, fade=1.5):
    n = int((seconds + fade) * SR)
    ch = []
    for _ in range(2):  # два независимых канала — дождь «вокруг»
        hiss = band(rng.standard_normal(n), 700, 7500) * 0.35
        low = band(brown(n), hi=350) * 0.004
        # капли: редкие короткие щелчки разной силы
        imp = np.zeros(n)
        k = int(n / SR * 450)
        imp[rng.integers(0, n, k)] = rng.random(k) ** 3
        drops = band(np.convolve(imp, np.exp(-np.arange(200) / 25.0), "same"), 1800, 6000) * 1.2
        gust = 1 + 0.15 * np.sin(np.linspace(0, 2 * np.pi * seconds / 6.0, n) + rng.random() * 6)
        ch.append((hiss + low + drops) * gust)
    save("rain_loop.wav", seamless(np.stack(ch, 1), int(fade * SR)), 0.6)


def thunder(name, seconds=8.0):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    rumble = band(brown(n), 30, 260, order=3) * 0.02
    rumble += band(rng.standard_normal(n), 60, 500) * 0.15
    # Мягкое нарастание (без резкого «треска» в начале — он звучал как щелчок).
    env = np.exp(-t / 2.2) * np.clip(t / 0.45, 0, 1) ** 2
    for _ in range(4):  # несколько раскатов
        c, w = rng.uniform(0.6, 3.5), rng.uniform(0.3, 0.8)
        env += rng.uniform(0.3, 0.8) * np.exp(-((t - c) / w) ** 2) * np.exp(-t / 3)
    x = rumble * env
    x *= np.clip((seconds - t) / 1.5, 0, 1)  # мягкий конец
    save(name, x, 0.9)


def car_loop(seconds=4.0, fade=0.8):
    n = int((seconds + fade) * SR)
    t = np.arange(n) / SR
    tires = band(rng.standard_normal(n), 600, 4500) * 0.5
    spray = band(rng.standard_normal(n), 3000, 9000) * 0.25
    spray *= 1 + 0.3 * band(rng.standard_normal(n), hi=6) * 20
    f0 = 52 * (1 + 0.01 * np.sin(2 * np.pi * 0.7 * t))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    engine = sum(np.sin(ph * k) / k for k in range(1, 9))
    engine = band(engine, hi=380) * 0.35
    save("car_loop.wav", seamless(tires + spray + engine, int(fade * SR)), 0.7)


if __name__ == "__main__":
    print("Звуки в", OUT)
    rain_loop()
    thunder("thunder_1.wav")
    thunder("thunder_2.wav", 7.0)
    car_loop()
