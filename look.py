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
    # GTA VI — неоновый Vice City: маджента, фиолетовый, закатный оранжевый
    "gta6": dict(NAME="GTA VI", SWATCH=("#0a0514", "#F1499E", "#FF934A"),
                 BG="#0a0514", SURFACE="#160b22", BORDER="#2e1644", TEXT="#fce8f5", MUTED="#a87a9e",
                 ACC1="#F1499E", ACC2="#FE8780", OK="#FFB145", BAD="#ff5c7a", HOVER="#241430",
                 BTN="#1c0f28", SEL="#3B146B", MONO="#e2b5ce", OFF="#3a2048", DIS="#6d4a6a", ONACC="#ffffff"),
    # GTA IV — Liberty City: ночной асфальт, мокрый бетон, янтарь
    "gta4": dict(NAME="GTA IV", SWATCH=("#141619", "#C89B4B", "#1E2226"),
                 BG="#141619", SURFACE="#1E2226", BORDER="#2c3138", TEXT="#ece8e0", MUTED="#9a9588",
                 ACC1="#C89B4B", ACC2="#E0B86A", OK="#C89B4B", BAD="#c94a4a", HOVER="#262b32",
                 BTN="#1a1e24", SEL="#3a3220", MONO="#c8c4b8", OFF="#2c3138", DIS="#6a665c", ONACC="#1a1408"),
    # Red Dead Redemption 2 — кровь, уголь, пыль
    "rdr2": dict(NAME="Red Dead II", SWATCH=("#0a0b0c", "#C90511", "#E89A3C"),
                 BG="#0a0b0c", SURFACE="#141618", BORDER="#2a2e32", TEXT="#f5f5f5", MUTED="#8a8e94",
                 ACC1="#C90511", ACC2="#EE0000", OK="#E89A3C", BAD="#EE0000", HOVER="#1e2124",
                 BTN="#191C1F", SEL="#3a1012", MONO="#c4c4ce", OFF="#2a2e32", DIS="#5a5e64", ONACC="#ffffff"),
    # Cyberpunk 2077 — Night City: жёлтый логотипа, циан, розовый неон
    "cyberpunk": dict(NAME="Cyberpunk 2077", SWATCH=("#050508", "#FCEE0A", "#00F0FF"),
                      BG="#050508", SURFACE="#0e0e14", BORDER="#1c1c28", TEXT="#f5f5e8", MUTED="#8a8a6e",
                      ACC1="#FCEE0A", ACC2="#FFE566", OK="#00F0FF", BAD="#FF003C", HOVER="#16161f",
                      BTN="#12121a", SEL="#2a2410", MONO="#c8c8a0", OFF="#252530", DIS="#5a5a48", ONACC="#0a0a00"),
    # GTA Vice City — Майами 80-х: hot pink, бирюза, закат
    "vicecity": dict(NAME="Vice City", SWATCH=("#0b0520", "#FF2D95", "#00E5E8"),
                     BG="#0b0520", SURFACE="#160a2e", BORDER="#2f1860", TEXT="#ffe6f5", MUTED="#b07aaa",
                     ACC1="#FF2D95", ACC2="#FF7AC8", OK="#00E5E8", BAD="#FF5A5A", HOVER="#24124a",
                     BTN="#1c0e38", SEL="#4a1878", MONO="#e8b8d8", OFF="#3a2060", DIS="#7a5a90", ONACC="#ffffff"),
}
THEME_KEYS = ["violet", "green", "ocean", "rose", "amber", "oled", "gta6", "gta4", "vicecity", "rdr2", "cyberpunk", "light", "light-green", "auto"]
LEGACY_THEMES = {"dark": "violet"}          # имена тем из старых версий

# Характер анимаций «как в игре» для специальных тем (длительности в мс).
# half: (fade_out, fade_in) при смене темы; dim: до какого opacity затемнять;
# pulse: период «дыхания» кнопки питания; busy: скорость busy-bar.
THEME_ANIM = {
    "gta6": dict(
        flavor="neon",
        half=(70, 110), dim=0.20,
        ease_out="InQuad", ease_in="OutBack",
        pulse=900, busy=900, toggle=200,
        page_ms=140, page_style="slide",
        sfx_theme="theme_gta6.mp3",
        sfx_power="power_gta6.mp3",
        sfx_switch="switch_gta6.mp3",
        icon="gta6",
    ),
    "gta4": dict(
        flavor="urban",
        half=(100, 140), dim=0.25,
        ease_out="InQuad", ease_in="OutCubic",
        pulse=1600, busy=1200, toggle=260,
        page_ms=200, page_style="fade",
        sfx_theme="theme_gta4.mp3",
        sfx_power="power_gta4.mp3",
        sfx_switch="switch_gta4.mp3",
        icon="urban",
    ),
    "vicecity": dict(
        flavor="neon",
        half=(80, 130), dim=0.18,
        ease_out="InQuad", ease_in="OutBack",
        pulse=1100, busy=1000, toggle=220,
        page_ms=160, page_style="slide",
        sfx_theme="theme_vicecity.mp3",
        sfx_power="power_vicecity.mp3",
        sfx_switch="switch_vice.mp3",
        icon="vice",
    ),
    "rdr2": dict(
        flavor="cinematic",
        half=(200, 260), dim=0.10,
        ease_out="InCubic", ease_in="OutCubic",
        pulse=2800, busy=1600, toggle=420,
        page_ms=380, page_style="fade",
        sfx_theme="theme_rdr2.mp3",
        sfx_power="power_rdr2.mp3",
        sfx_switch="switch_rdr2.mp3",
        icon="western",
    ),
    "cyberpunk": dict(
        flavor="glitch",
        half=(35, 70), dim=0.28,
        ease_out="InQuad", ease_in="OutQuad",
        pulse=550, busy=700, toggle=160,
        glitch=True,
        page_ms=180, page_style="glitch",
        sfx_theme="theme_cyberpunk.mp3",
        sfx_power="power_cyberpunk.mp3",
        sfx_switch="switch_cyberpunk.mp3",
        icon="cyber",
    ),
}

def theme_anim(theme: str | None = None) -> dict:
    """Параметры анимации для темы (или пустой dict для обычных тем)."""
    if not theme:
        return {}
    theme = LEGACY_THEMES.get(theme, theme)
    return dict(THEME_ANIM.get(theme, {}))

FONT_KEYS = ["small", "normal", "large", "compact"]
FONT_SIZES = {"small": 9, "compact": 9, "normal": 10.5, "large": 10.5}
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
    # фиксированный компактный шрифт — не раздувает интерфейс
    pal["FS"] = 9.0
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
    cfg["font_size"] = 9.0  # только компактный размер
    cfg["corners"] = cfg.get("corners") if cfg.get("corners") in CORNER_KEYS else "soft"
    cfg["density"] = cfg.get("density") if cfg.get("density") in DENSITY_KEYS else "normal"
    style = cfg.get("animation_style")
    if style in ("smooth", "quick", "none"):
        cfg["animation_style"] = style
    elif style == "subtle":  # старое «ненавязчивая» -> полностью без анимаций
        cfg["animation_style"] = "none"
    else:
        cfg["animation_style"] = "smooth"
    # «Нет» полностью отключает анимации; иначе включаем и применяем выбранный стиль
    if cfg["animation_style"] == "none":
        cfg["animations"] = False
    else:
        cfg["animations"] = to_bool(cfg.get("animations", True))
        if not cfg["animations"]:
            cfg["animation_style"] = "none"
    return cfg
