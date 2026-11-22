"""Оформление без Qt: темы, акценты, плотность, контраст и проверка настроек.
Модуль не зависит от Qt, поэтому его можно проверять обычными тестами (tests/test_look.py)."""
from __future__ import annotations

import colorsys
import re

THEMES = {
    "violet": dict(NAME="Фиолетовая", SWATCH=("#0c0d12", "#7c5cff", "#e6e8ef"),
                   BG="#0c0d12", SURFACE="#15161d", BORDER="#242530", TEXT="#f2f3f7", MUTED="#7c7f93",
                   ACC1="#7c5cff", ACC2="#b794ff", OK="#34d399", BAD="#ff5c7a", HOVER="#272836",
                   BTN="#1e1f29", SEL="#2a2550", MONO="#b4b7c9", OFF="#2d2e3c", DIS="#565869", ONACC="#ffffff"),
    "green": dict(NAME="Зелёная", SWATCH=("#070b09", "#22c55e", "#14301f"),
                  BG="#070b09", SURFACE="#0e1612", BORDER="#1b2b22", TEXT="#eaf5ee", MUTED="#6f8a7a",
                  ACC1="#16a34a", ACC2="#4ade80", OK="#4ade80", BAD="#ff6b6b", HOVER="#16251d",
                  BTN="#12201a", SEL="#14301f", MONO="#a9c4b4", OFF="#24382c", DIS="#4d6358", ONACC="#04130a"),
    "light": dict(NAME="Светлая", SWATCH=("#ffffff", "#6a4cff", "#c9cbd8"),
                  BG="#f4f5fa", SURFACE="#ffffff", BORDER="#e1e3ee", TEXT="#14151c", MUTED="#6b6f85",
                  ACC1="#6a4cff", ACC2="#a78bfa", OK="#0f9f8a", BAD="#e03e5c", HOVER="#ecedf6",
                  BTN="#f0f1f8", SEL="#e4defe", MONO="#4a4d63", OFF="#d5d7e4", DIS="#a3a6b8", ONACC="#ffffff"),
    "light-green": dict(NAME="Светло-зелёная", SWATCH=("#ffffff", "#16a34a", "#cfe0d5"),
                        BG="#f2f7f4", SURFACE="#ffffff", BORDER="#dbe8df", TEXT="#12201a", MUTED="#5f7a6b",
                        ACC1="#15803d", ACC2="#22c55e", OK="#15803d", BAD="#dc2f4f", HOVER="#e8f1ec",
                        BTN="#ecf3ef", SEL="#d5efdf", MONO="#3f5a4b", OFF="#cfe0d5", DIS="#9db3a6", ONACC="#ffffff"),
    "ocean": dict(NAME="Океаническая", SWATCH=("#08121d", "#0ea5e9", "#17334a"),
                  BG="#08121d", SURFACE="#101f2d", BORDER="#1c3548", TEXT="#eaf6ff", MUTED="#7894aa",
                  ACC1="#0ea5e9", ACC2="#38bdf8", OK="#34d399", BAD="#fb7185", HOVER="#1a3042",
                  BTN="#14283a", SEL="#123d58", MONO="#a9c9df", OFF="#29465b", DIS="#5b7182", ONACC="#06131d"),
    "rose": dict(NAME="Розовая", SWATCH=("#180d15", "#ec4899", "#452039"),
                 BG="#180d15", SURFACE="#24131f", BORDER="#402337", TEXT="#fff0f7", MUTED="#ad8299",
                 ACC1="#ec4899", ACC2="#f9a8d4", OK="#4ade80", BAD="#fb7185", HOVER="#3a2032",
                 BTN="#301a2a", SEL="#542344", MONO="#e2b5ce", OFF="#523044", DIS="#8d657c", ONACC="#ffffff"),
    "amber": dict(NAME="Янтарная", SWATCH=("#171109", "#f59e0b", "#493516"),
                  BG="#171109", SURFACE="#241b0d", BORDER="#403019", TEXT="#fff8e8", MUTED="#a99775",
                  ACC1="#f59e0b", ACC2="#fcd34d", OK="#4ade80", BAD="#fb7185", HOVER="#392b16",
                  BTN="#30230f", SEL="#554019", MONO="#e8d4a7", OFF="#514126", DIS="#8b7955", ONACC="#1b1204"),
    "oled": dict(NAME="OLED", SWATCH=("#000000", "#7c5cff", "#171717"),
                 BG="#000000", SURFACE="#080808", BORDER="#1c1c1c", TEXT="#f5f5f7", MUTED="#85858f",
                 ACC1="#7c5cff", ACC2="#b794ff", OK="#34d399", BAD="#ff5c7a", HOVER="#171717",
                 BTN="#101010", SEL="#241d40", MONO="#c4c4ce", OFF="#252525", DIS="#606068", ONACC="#ffffff"),
}
THEME_KEYS = ["violet", "green", "ocean", "rose", "amber", "oled", "light", "light-green", "auto"]
LEGACY_THEMES = {"dark": "violet"}          # имена тем из старых версий
FONT_KEYS = ["small", "normal", "large"]
FONT_SIZES = {"small": 9, "normal": 10, "large": 11.5}
CORNER_KEYS = ["soft", "sharp"]
CORNERS = {"soft": (14, 10), "sharp": (6, 4)}
DENSITY_KEYS = ["compact", "normal", "spacious"]
# PAD: поля кнопок, PADI: поля полей ввода и пунктов списков, GAP: промежутки, MARG: поля карточек
DENSITY = {
    "compact":  dict(PAD=5,  PADI=4,  GAP=8,  MARG=12),
    "normal":   dict(PAD=8,  PADI=7,  GAP=12, MARG=16),
    "spacious": dict(PAD=11, PADI=10, GAP=16, MARG=20),
}
ACCENT_PRESETS = [
    "#7c5cff", "#6366f1", "#3b82f6", "#0ea5e9", "#06b6d4", "#14b8a6", "#22c55e",
    "#84cc16", "#eab308", "#f97316", "#ef4444", "#f43f5e", "#ec4899", "#a855f7",
]
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def is_hex(s) -> bool:
    return isinstance(s, str) and bool(_HEX.match(s))


def to_rgb(h: str) -> tuple:
    return int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)


def to_hex(r: float, g: float, b: float) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(x)))) for x in (r, g, b))


def mix_hex(a: str, b: str, t: float) -> str:
    ra, rb = to_rgb(a), to_rgb(b)
    return to_hex(*(ra[i] * (1 - t) + rb[i] * t for i in range(3)))


def lighten(h: str, factor: float = 1.35) -> str:
    """Светлее на factor (как QColor.lighter): растёт яркость, при переполнении падает насыщенность."""
    r, g, b = (x / 255 for x in to_rgb(h))
    hh, s, v = colorsys.rgb_to_hsv(r, g, b)
    v *= factor
    if v > 1:
        s = max(0.0, s - (v - 1))
        v = 1.0
    return to_hex(*(x * 255 for x in colorsys.hsv_to_rgb(hh, s, v)))


def luminance(h: str) -> float:
    def lin(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(x) for x in to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def readable_on(colors: list, light: str = "#ffffff", dark: str = "#0c0d12") -> str:
    """Какой цвет текста (белый или тёмный) лучше читается на этих фонах."""
    return max((light, dark), key=lambda t: min(contrast(t, c) for c in colors))


def readable_accent(acc: str, bg: str, min_ratio: float = 3.0) -> str:
    """Акцент для иконок и текста на фоне bg: если контраст мал, сдвигаем цвет к чёрному/белому."""
    if contrast(acc, bg) >= min_ratio:
        return acc
    target = "#000000" if luminance(bg) > 0.5 else "#ffffff"
    for i in range(1, 11):
        c = mix_hex(acc, target, i / 10)
        if contrast(c, bg) >= min_ratio:
            return c
    return target


def resolve_theme(name: str, system_light: bool = False) -> str:
    name = LEGACY_THEMES.get(name, name)
    if name == "auto":
        return "light" if system_light else "violet"
    return name if name in THEMES else "violet"


def compute_palette(cfg: dict, theme: str | None = None, system_light: bool = False) -> dict:
    """Полная палитра для интерфейса: тема + акцент + шрифт + углы + плотность."""
    pal = dict(THEMES[resolve_theme(theme if theme is not None else cfg.get("theme", "violet"), system_light)])
    acc = cfg.get("accent")
    if is_hex(acc):  # свой цвет акцента перекрывает цвета темы
        pal["ACC1"], pal["ACC2"] = acc.lower(), lighten(acc)
        pal["SEL"] = mix_hex(pal["BG"], acc, 0.25)
    onacc = readable_on([pal["ACC1"]])  # подпись подбираем под основной цвет, светлый край подтянем ниже
    for i in range(11):  # светлый край градиента подтягиваем к основному цвету, пока подпись на нём читается
        c2 = mix_hex(pal["ACC2"], pal["ACC1"], i / 10)
        if contrast(onacc, c2) >= 4.5:
            pal["ACC2"] = c2
            break
    else:
        pal["ACC2"] = pal["ACC1"]
    pal["ONACC"] = readable_on([pal["ACC1"], pal["ACC2"]])
    pal["ACC_FG"] = readable_accent(pal["ACC1"], pal["SURFACE"])
    pal.update(DENSITY[cfg["density"] if cfg.get("density") in DENSITY else "normal"])
    fs = cfg.get("font_size", "normal")
    pal["FS"] = float(fs) if isinstance(fs, (int, float)) and not isinstance(fs, bool) else FONT_SIZES.get(fs, 10)
    pal["R1"], pal["R2"] = CORNERS.get(cfg.get("corners"), (14, 10))
    return pal


def to_bool(v, default: bool = True) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        return v.strip().lower() not in ("", "0", "false", "no", "off", "нет")
    return default


def sanitize_look(cfg: dict) -> dict:
    """Приводит настройки оформления к допустимым значениям (старые, битые и чужие значения не роняют приложение)."""
    t = cfg.get("theme")
    t = LEGACY_THEMES.get(t, t)
    cfg["theme"] = t if t in THEME_KEYS else "violet"
    acc = cfg.get("accent")
    cfg["accent"] = acc.lower() if is_hex(acc) else ""
    fs = cfg.get("font_size", "normal")
    if isinstance(fs, (int, float)) and not isinstance(fs, bool):
        cfg["font_size"] = max(9.0, min(16.0, float(fs)))
    else:
        cfg["font_size"] = fs if fs in FONT_KEYS else "normal"
    cfg["corners"] = cfg.get("corners") if cfg.get("corners") in CORNER_KEYS else "soft"
    cfg["density"] = cfg.get("density") if cfg.get("density") in DENSITY_KEYS else "normal"
    cfg["animations"] = to_bool(cfg.get("animations", True))
    cfg["animation_style"] = cfg.get("animation_style") if cfg.get("animation_style") in ("smooth", "quick", "subtle") else "smooth"
    return cfg
