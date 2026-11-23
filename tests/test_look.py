"""Проверки оформления и настроек без Qt:  python -m unittest discover -s tests -v"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core  # noqa: E402
import look  # noqa: E402

REQUIRED_KEYS = ["BG", "SURFACE", "BORDER", "TEXT", "MUTED", "ACC1", "ACC2", "ACC_FG", "ONACC", "OK", "BAD",
                 "HOVER", "BTN", "SEL", "MONO", "OFF", "DIS", "FS", "R1", "R2", "PAD", "PADI", "GAP", "MARG"]


def load_config(text):
    """Кладёт text в config.json во временную папку и читает его так же, как при запуске."""
    f = Path(tempfile.mkdtemp()) / "config.json"
    if text is not None:
        f.write_text(text, encoding="utf-8")
    old = core.CONFIG_FILE
    core.CONFIG_FILE = f
    try:
        return core._load(), f
    finally:
        core.CONFIG_FILE = old


class ConfigTests(unittest.TestCase):
    def test_old_config_keeps_values(self):
        cfg, _ = load_config(json.dumps({"theme": "dark", "font_size": "large", "corners": "sharp",
                                         "accent": "#3B82F6"}))
        self.assertEqual(cfg["theme"], "violet")          # старое имя темы "dark" -> фиолетовая
        self.assertEqual(cfg["font_size"], 9.0)       # старые значения не сбрасываются
        self.assertEqual(cfg["corners"], "sharp")
        self.assertEqual(cfg["accent"], "#3b82f6")
        self.assertEqual(cfg["density"], "normal")        # новых ключей в старом файле нет: берутся по умолчанию
        self.assertTrue(cfg["animations"])

    def test_old_theme_names_stay_valid(self):
        for name in ("light", "auto", "green", "light-green", "violet", "oled"):
            cfg, _ = load_config(json.dumps({"theme": name}))
            self.assertEqual(cfg["theme"], name)

    def test_missing_file_gives_defaults(self):
        cfg, _ = load_config(None)
        for key in ("theme", "accent", "font_size", "corners", "density", "animations"):
            self.assertEqual(cfg[key], core.DEFAULTS[key])

    def test_corrupt_json_does_not_crash(self):
        cfg, f = load_config("{это не json")
        self.assertEqual(cfg["theme"], "violet")
        self.assertTrue(f.with_name("config.json.bad").exists())  # испорченный файл сохранён рядом

    def test_config_that_is_not_an_object(self):
        cfg, _ = load_config("[1, 2, 3]")
        self.assertEqual(cfg["density"], "normal")

    def test_empty_file(self):
        cfg, _ = load_config("")
        self.assertEqual(cfg["theme"], "violet")

    def test_utf8_bom_is_accepted(self):
        f = Path(tempfile.mkdtemp()) / "config.json"
        f.write_bytes(b"\xef\xbb\xbf" + json.dumps({"density": "compact"}).encode())
        old, core.CONFIG_FILE = core.CONFIG_FILE, f
        try:
            self.assertEqual(core._load()["density"], "compact")
        finally:
            core.CONFIG_FILE = old

    def test_invalid_values_are_repaired(self):
        cfg, _ = load_config(json.dumps({"theme": 5, "density": "huge", "accent": "red", "animations": "false",
                                         "font_size": None, "sites": "x", "profiles_enabled": [1, "a"]}))
        self.assertEqual(cfg["theme"], "violet")
        self.assertEqual(cfg["density"], "normal")
        self.assertEqual(cfg["accent"], "")
        self.assertFalse(cfg["animations"])               # строка "false" понята как выключено
        self.assertEqual(cfg["font_size"], 9.0)
        self.assertEqual(len(cfg["sites"]), len(core.DEFAULTS["sites"]))
        self.assertEqual(cfg["profiles_enabled"], ["a"])

    def test_defaults_are_not_shared_between_loads(self):
        a, _ = load_config(None)
        a["sites"].append({"name": "x", "url": "https://x"})
        b, _ = load_config(None)
        self.assertEqual(len(b["sites"]), len(core.DEFAULTS["sites"]))

    def test_roundtrip_new_and_old_settings(self):
        d = Path(tempfile.mkdtemp())
        old_dir, old_file, backup = core.CONFIG_DIR, core.CONFIG_FILE, dict(core.CFG)
        core.CONFIG_DIR, core.CONFIG_FILE = d, d / "config.json"
        try:
            core.CFG.update(theme="green", font_size=9.0, accent="#f97316", density="spacious",
                            animations=False, corners="sharp")
            core.save()
            self.assertFalse((d / "config.json.tmp").exists())   # временный файл не остаётся
            loaded = core._load()
            for key in ("theme", "font_size", "accent", "density", "animations", "corners"):
                self.assertEqual(loaded[key], core.CFG[key], key)
        finally:
            core.CONFIG_DIR, core.CONFIG_FILE = old_dir, old_file
            core.CFG.clear()
            core.CFG.update(backup)


class LookTests(unittest.TestCase):
    def test_accent_presets(self):
        self.assertGreaterEqual(len(look.ACCENT_PRESETS), 12)
        self.assertEqual(len(set(look.ACCENT_PRESETS)), len(look.ACCENT_PRESETS))
        self.assertTrue(all(look.is_hex(c) for c in look.ACCENT_PRESETS))

    def test_every_theme_and_accent_is_readable(self):
        for theme in look.THEMES:
            for acc in [""] + look.ACCENT_PRESETS:
                pal = look.compute_palette({"theme": theme, "accent": acc})
                on_accent = min(look.contrast(pal["ONACC"], pal["ACC1"]), look.contrast(pal["ONACC"], pal["ACC2"]))
                self.assertGreaterEqual(on_accent, 4.4, f"текст на акценте: {theme} {acc}")
                self.assertGreaterEqual(look.contrast(pal["ACC_FG"], pal["SURFACE"]), 3.0, f"иконки: {theme} {acc}")

    def test_accent_is_applied(self):
        for acc in look.ACCENT_PRESETS:
            self.assertEqual(look.compute_palette({"accent": acc})["ACC1"], acc)

    def test_palette_has_everything_the_ui_needs(self):
        for theme in list(look.THEMES) + ["auto", "dark", "nonsense"]:
            pal = look.compute_palette({"theme": theme})
            for key in REQUIRED_KEYS:
                self.assertIn(key, pal, f"{theme}: нет {key}")

    def test_density_modes_change_spacing_in_steps(self):
        pals = [look.compute_palette({"density": k}) for k in look.DENSITY_KEYS]
        for key in ("PAD", "PADI", "GAP", "MARG"):
            values = [p[key] for p in pals]
            self.assertEqual(values, sorted(set(values)), f"{key} должен расти от компактной к просторной")

    def test_unknown_density_is_normal(self):
        self.assertEqual(look.compute_palette({"density": "?"})["PAD"], look.DENSITY["normal"]["PAD"])

    def test_continuous_font_size_is_clamped_and_used(self):
        cfg, _ = load_config(json.dumps({"font_size": 13.5}))
        self.assertEqual(cfg["font_size"], 9.0)
        self.assertEqual(look.compute_palette(cfg)["FS"], 9.0)
        cfg, _ = load_config(json.dumps({"font_size": 99}))
        self.assertEqual(cfg["font_size"], 9.0)

    def test_oled_theme_is_true_black(self):
        pal = look.compute_palette({"density": "normal", "font_size": "normal"}, "oled")
        self.assertEqual(pal["BG"], "#000000")
        self.assertEqual(pal["SURFACE"], "#080808")

    def test_system_theme(self):
        self.assertEqual(look.resolve_theme("auto", system_light=True), "light")
        self.assertEqual(look.resolve_theme("auto", system_light=False), "violet")

    def test_bool_parsing(self):
        for v in (False, 0, "0", "false", "False", "off", ""):
            self.assertFalse(look.to_bool(v))
        for v in (True, 1, "1", "true", "yes"):
            self.assertTrue(look.to_bool(v))


if __name__ == "__main__":
    unittest.main()
