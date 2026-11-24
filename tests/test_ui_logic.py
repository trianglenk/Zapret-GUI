"""Проверки логики интерфейса на заглушке Qt (визуальную часть смотри глазами): python -m unittest discover -s tests -v"""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))
import qt_stub  # noqa: E402

sys.modules["qt"] = qt_stub  # main.py импортирует Qt через модуль qt
import core  # noqa: E402
import look  # noqa: E402

spec = importlib.util.spec_from_file_location("main_under_test", ROOT / "main.py")
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)


class UiLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._saved = dict(core.CFG)
        cls._orig = (core.save, core.bg, core.is_running)
        core.save = lambda: None            # тесты не пишут config.json
        core.bg = lambda fn: None           # без потоков и сети
        core.is_running = lambda: False
        core.CFG["base_dir"] = tempfile.mkdtemp()
        cls.w = main.MainWindow()

    @classmethod
    def tearDownClass(cls):
        core.save, core.bg, core.is_running = cls._orig
        core.CFG.clear()
        core.CFG.update(cls._saved)

    def setUp(self):
        core.CFG.update(theme="violet", accent="", font_size="normal", corners="soft", density="normal",
                        animations=True)
        main.set_palette("violet")

    def test_density_changes_palette(self):
        seen = []
        for key in look.DENSITY_KEYS:
            self.w.set_look("density", key)
            self.assertEqual(core.CFG["density"], key)
            seen.append((main.P["PAD"], main.P["GAP"], main.P["MARG"]))
        self.assertEqual(seen, sorted(set(seen)))

    def test_every_accent_is_applied_and_saved(self):
        for acc in look.ACCENT_PRESETS:
            self.w.set_look("accent", acc)
            self.assertEqual(core.CFG["accent"], acc)
            self.assertEqual(main.P["ACC1"], acc)
        self.w.set_look("accent", "")
        self.assertEqual(main.P["ACC1"], look.THEMES["violet"]["ACC1"])

    def test_old_and_new_themes_switch(self):
        for key in look.THEME_KEYS:
            self.w.on_theme_pick(key)
            self.assertEqual(core.CFG["theme"], key)
        for font in look.FONT_KEYS:
            self.w.set_look("font_size", font)
            self.assertEqual(main.P["FS"], look.FONT_SIZES[font])
        self.w.set_look("font_size", 14.5)
        self.assertEqual(main.P["FS"], 14.5)

    def test_animations_switch_is_saved(self):
        self.w.on_anim_toggled(False)
        self.assertFalse(core.CFG["animations"])
        self.assertFalse(main.anim_on())
        self.w.on_anim_toggled(True)
        self.assertTrue(core.CFG["animations"])
        self.assertTrue(main.anim_on())

    def test_collapsible_section_state_is_saved(self):
        section = main.CollapsibleSection("Тестовый блок", "test_section")
        section.set_expanded(False)
        self.assertTrue(core.CFG["collapsed_sections"]["test_section"])
        section.set_expanded(True)
        self.assertFalse(core.CFG["collapsed_sections"]["test_section"])

    def test_section_default_setting_is_saved(self):
        self.w.set_section_default("about", True)
        self.assertTrue(core.CFG["collapsed_sections"]["about"])

    def test_animation_style_is_persisted(self):
        self.w.on_animation_style_changed(1)
        self.assertEqual(core.CFG["animation_style"], "quick")
        self.assertTrue(core.CFG["animations"])
        self.w.on_animation_style_changed(2)
        self.assertEqual(core.CFG["animation_style"], "none")
        self.assertFalse(core.CFG["animations"])
        self.w.on_animation_style_changed(0)
        self.assertEqual(core.CFG["animation_style"], "smooth")
        self.assertTrue(core.CFG["animations"])

    def test_animations_off_is_instant(self):
        core.CFG["animations"] = False
        nav = main.NavButton("power", "t")
        nav._retarget()
        self.assertEqual(nav._lv, 2.0)                      # сразу выбрано, без перехода
        power = main.PowerButton()
        power.set_state(True, True)
        self.assertEqual(power._level, 1.0)
        bar = main.RatioBar()
        bar.set_ratio(0.5)
        self.assertEqual(bar._v, 0.5)

    def test_animations_on_starts_transition(self):
        core.CFG["animations"] = True
        nav = main.NavButton("power", "t")
        nav._retarget()
        self.assertEqual(nav._lv, 0.0)                      # значение меняет анимация, а не мгновенный скачок
        power = main.PowerButton()
        power.set_state(True, True)
        self.assertEqual(power._level, 0.0)

    def test_reset_look(self):
        self.w.set_look("accent", "#ef4444")
        self.w.set_look("density", "spacious")
        self.w.on_anim_toggled(False)
        self.w.reset_look()
        self.assertEqual((core.CFG["theme"], core.CFG["accent"], core.CFG["density"], core.CFG["animations"]),
                         ("violet", "", "normal", True))

    def test_window_layouts(self):
        for compact in (True, False, True):
            self.w.apply_layout(compact)
            self.assertEqual(self.w.compact, compact)


if __name__ == "__main__":
    unittest.main()
