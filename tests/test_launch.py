"""Проверки запуска без Windows: разбор .bat, списки, объяснение ошибок winws."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core  # noqa: E402

BAT = r'''@echo off
chcp 65001 > nul
cd /d "%~dp0"
call service.bat status_zapret
set "BIN=%~dp0bin\"
set "LISTS=%~dp0lists\"
start "zapret: %~n0" /min "%BIN%winws.exe" --wf-tcp=80,443,2053,%GameFilterTCP% --wf-udp=443,%GameFilterUDP% ^
--filter-udp=443 --hostlist="%LISTS%list-general.txt" --hostlist="%LISTS%list-general-user.txt" ^
--hostlist-exclude="%LISTS%list-exclude-user.txt" --ipset-exclude="%LISTS%ipset-exclude-user.txt" ^
--dpi-desync=fake --dpi-desync-fake-quic="%BIN%quic_initial_www_google_com.bin" --new
'''


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self._base, self._save = dict(core.CFG), core.save
        core.CFG["base_dir"] = tempfile.mkdtemp()
        core.CFG["game_filter"] = False
        core.save = lambda: None
        self.rel = core.release_dir()
        self.rel.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        core.save = self._save  # подмена не должна влиять на другие тесты
        core.CFG.clear()
        core.CFG.update(self._base)

    def test_parse_bat_substitutes_variables(self):
        bat = self.rel / "general.bat"
        bat.write_text(BAT, encoding="utf-8")
        args = core.parse_bat(bat)
        self.assertIsNotNone(args)
        self.assertIn("--wf-tcp=80,443,2053,12", args)           # игровой фильтр выключен -> 12
        self.assertIn("list-general-user.txt", args)
        self.assertNotIn("%", args)                               # все переменные подставлены
        self.assertNotIn("^", args)                               # продолжения строк склеены

    def test_parse_bat_unescapes_cmd_exclamation(self):
        bat = self.rel / "general-caret.bat"
        bat.write_text('start "a" /min "%BIN%winws.exe" --hostlist="%LISTS%foo^!bar.txt"\n', encoding="utf-8")
        args = core.parse_bat(bat)
        self.assertIn("foo!bar.txt", args)
        self.assertNotIn("^!", args)

    def test_game_filter_changes_ports(self):
        bat = self.rel / "general.bat"
        bat.write_text(BAT, encoding="utf-8")
        core.CFG["game_filter"] = True
        self.assertIn("1024-65535", core.parse_bat(bat))

    def test_unknown_variable_falls_back_to_bat(self):
        bat = self.rel / "x.bat"
        bat.write_text('start "a" /min "%BIN%winws.exe" --foo=%Unknown%\n', encoding="utf-8")
        self.assertIsNone(core.parse_bat(bat))

    def test_ensure_lists_creates_missing_files(self):
        bat = self.rel / "general.bat"
        bat.write_text(BAT, encoding="utf-8")
        core.ensure_lists(core.parse_bat(bat))
        lists = self.rel / "lists"
        for name in ("list-general-user.txt", "list-exclude-user.txt", "ipset-exclude-user.txt"):
            self.assertTrue((lists / name).read_text().strip(), name)   # не пустые: пустой список = «без фильтра»

    def test_explain_windivert_codes(self):
        cases = {
            "windivert: error opening filter: Access denied (5)": "Нет доступа",
            "windivert: error opening filter: The system cannot find the file specified (2)": "WinDivert64.sys",
            "windivert: error opening filter: This driver has been blocked from loading (1275)": "заблокировала",
            "windivert: error opening filter: ... (577)": "подпись",
            "WinDivert: invalid filter (87)": "не подходит",
        }
        for text, word in cases.items():
            self.assertIn(word, core.explain_output(text), text)

    def test_explain_exit_codes_and_other_errors(self):
        self.assertIn("библиотек", core.explain_output("", -1073741515))       # 0xC0000135 как знаковое число
        self.assertIn("библиотек", core.explain_output("", 0xC0000135))
        self.assertIn("не подходит", core.explain_output("unknown option: --dpi-desync-foo"))
        self.assertIn("списка", core.explain_output("cannot open hostlist file lists\\x.txt"))
        self.assertEqual(core.explain_output(""), "")
        self.assertEqual(core.explain_output("something odd"), "")
        self.assertIn("экранирования", core.explain_output("could not read ^!"))

    def test_bin_problems(self):
        self.assertEqual(len(core.bin_problems()), 3)               # нет ни winws, ни WinDivert
        b = self.rel / "bin"
        b.mkdir()
        for name in ("winws.exe", "WinDivert.dll", "WinDivert64.sys"):
            (b / name).write_bytes(b"x")
        self.assertEqual(core.bin_problems(), [])                    # регистр имён не важен

    def test_test_launch_reports_missing_files(self):
        ok, text = core.test_launch("general.bat")
        self.assertFalse(ok)
        self.assertIn("winws.exe", text)


if __name__ == "__main__":
    unittest.main()
