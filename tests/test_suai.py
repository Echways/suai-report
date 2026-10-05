import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import suai  # noqa: E402

SETUP = """\\suaisetup{
  department   = 41,
  teacher      = А. А. Преподов,
  number       = 3,                  % пусто — без номера
  title        = Старое название,
  student      = Б. Б. Студентов,
  date         = 01.09.2026,
}"""


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


# Perl в Windows видит путь в ANSI-кодировке системы: кириллица в нём
# читается только при русской локали, которой на CI нет
COURSE = "Data bases" if suai.WINDOWS else "Базы данных"


class SetKeyTest(unittest.TestCase):
    def test_replaces_value(self):
        out = suai.set_key(SETUP, "title", "Новое")
        self.assertIn("  title        = Новое,", out)
        self.assertNotIn("Старое название", out)

    def test_keeps_comment_column(self):
        out = suai.set_key(SETUP, "number", "12")
        old = next(l for l in SETUP.splitlines() if "number" in l)
        new = next(l for l in out.splitlines() if "number" in l)
        self.assertEqual(new.index("%"), old.index("%"))
        self.assertTrue(new.startswith("  number       = 12,"))

    def test_empty_value(self):
        out = suai.set_key(SETUP, "number", "")
        self.assertIn("  number       = ,", out)

    def test_inserts_missing_key_before_brace(self):
        out = suai.set_key(SETUP, "year", "2030")
        lines = out.splitlines()
        self.assertEqual(lines[-1], "}")
        self.assertEqual(lines[-2], "  year         = 2030,")

    def test_commented_key_is_not_replaced(self):
        block = "\\suaisetup{\n% year = 2026,\n}"
        out = suai.set_key(block, "year", "2030")
        self.assertIn("% year = 2026,", out)
        self.assertIn("  year         = 2030,", out)

    def test_tex_value_escapes_comment_chars(self):
        self.assertEqual(suai.tex_value("Скидка 50% и #1"), r"Скидка 50\% и \#1")
        self.assertEqual(suai.tex_value(r"уже \% экранирован"), r"уже \% экранирован")

    def test_tex_value_escapes_chars_that_stop_the_build(self):
        self.assertEqual(suai.tex_value("Обмен A_B & C^2"), r"Обмен A\_B \& C\^{}2")
        self.assertEqual(suai.tex_value("Цена 5$"), r"Цена 5\$")
        self.assertEqual(suai.tex_value(r"\LaTeX{} и R\&D"), r"\LaTeX{} и R\&D")

    def test_tex_value_keeps_formula(self):
        self.assertEqual(suai.tex_value("Корни $x_1$ и $x^2$, 5%"), r"Корни $x_1$ и $x^2$, 5\%")

    def test_tex_value_braces_equals_sign(self):
        self.assertEqual(suai.tex_value("Расчёт y = kx"), "{Расчёт y = kx}")
        self.assertEqual(suai.tex_value("Прямая $y = kx_0$"), "{Прямая $y = kx_0$}")

    def test_split_comment_ignores_escaped_percent(self):
        self.assertEqual(suai.split_comment(r"a = 5\% x % c"), (r"a = 5\% x ", "% c"))
        self.assertEqual(suai.split_comment("a = 1"), ("a = 1", ""))


class SourcesTest(unittest.TestCase):
    """demo/, src/ и vscode/settings.json, от которых зависит генератор."""

    def test_demo_and_template_have_setup(self):
        self.assertIsNotNone(suai.read_setup(suai.DEMO))
        self.assertIsNotNone(suai.read_setup(suai.TEMPLATE))

    def test_latexmk_args(self):
        args = suai.latexmk_args()
        self.assertNotIn("%DOC_EXT%", args)
        self.assertEqual(args[0], "-e")
        self.assertIn("$out_dir = q(build)", args[1])

    @unittest.skipIf(shutil.which("perl") is None, "нет perl")
    def test_pdf_name_matches_latexmk(self):
        """PDF, который копирует сборка, и тот, что ищут open/clean, — один файл."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / COURSE / "lab-3"
            d.mkdir(parents=True)
            code = suai.latexmk_args()[1] + "; print $suai_pdf"
            out = subprocess.run(["perl", "-e", code], cwd=d, check=True,
                                 capture_output=True).stdout.decode()
            self.assertEqual(out, f"{COURSE}-lab-3.pdf")
            self.assertEqual(suai.pdf_path(d), d.resolve() / out)

    def test_latexmk_code_is_portable(self):
        """Строка -e уходит в Perl как есть в любой ОС: без кавычек (их
        по-разному разбирают cmd и sh) и без команд шелла вроде cp."""
        code = suai.latexmk_args()[1]
        for bad in ('"', "'", "&&", " cp "):
            self.assertNotIn(bad, code)
        self.assertIn("$success_cmd = q(internal suai_copy)", code)

    @unittest.skipIf(shutil.which("perl") is None, "нет perl")
    def test_latexmk_copies_pdf(self):
        """suai_copy кладёт build/main.pdf рядом с main.tex под именем из двух папок."""
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp) / COURSE / "lab-3"
            (d / "build").mkdir(parents=True)
            (d / "build" / "main.pdf").write_bytes(b"%PDF")
            code = "$root_filename = q(main); " + suai.latexmk_args()[1] + "; suai_copy()"
            subprocess.run(["perl", "-e", code], cwd=d, check=True)
            self.assertEqual(suai.pdf_path(d).read_bytes(), b"%PDF")

    def test_intellisense_matches_package(self):
        """suai-report.json описывает ровно пользовательские команды пакета."""
        sty = suai.STY.read_text(encoding="utf-8")
        defined = set(re.findall(
            r"\\(?:NewDocumentCommand|newcommand)\s*\{?\s*\\([a-z]+)(?![@a-z])", sty))
        public = {c for c in defined if c.startswith("suai") or c.endswith("ref")}
        public -= {"suairef", "suaiappletter"}       # служебные
        data = json.loads((suai.VSCODE / "suai-report.json").read_text(encoding="utf-8"))
        described = {m["name"] for m in data["macros"]}
        self.assertEqual(described, public)
        self.assertEqual(data["envs"], [])     # code — только для старых отчётов

    def test_template_dir_detection(self):
        self.assertTrue(suai.is_template_dir(suai.REPO))
        self.assertTrue(suai.is_template_dir(suai.DEMO.parent))
        self.assertTrue(suai.is_template_dir(suai.SRC))
        self.assertFalse(suai.is_template_dir(Path(tempfile.gettempdir())))


class FakeWinreg:
    """HKCU\\Environment с одним значением Path."""
    HKEY_CURRENT_USER, KEY_READ, KEY_WRITE = 1, 1, 2
    REG_SZ, REG_EXPAND_SZ = 1, 2

    def __init__(self, value=None, kind=2):
        self.value, self.kind = value, kind

    def OpenKey(self, *args):
        return contextlib.nullcontext(self)

    def QueryValueEx(self, key, name):
        if self.value is None:
            raise FileNotFoundError(name)
        return self.value, self.kind

    def SetValueEx(self, key, name, reserved, kind, value):
        self.value, self.kind = value, kind


class InstallTest(unittest.TestCase):
    """Установка: всё, что различается между Windows и остальными."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.sty = self.root / "texmf" / "suai-report.sty"
        self.patch("texmf_sty", mock.Mock(return_value=self.sty))

    def patch(self, name, value):
        patcher = mock.patch.object(suai, name, value)
        patcher.start()
        self.addCleanup(patcher.stop)

    def user_path(self, registry, d):
        with mock.patch.dict(sys.modules, {"winreg": registry, "ctypes": mock.Mock()}):
            return suai.add_to_user_path(Path(d))

    def test_symlink(self):
        linked = quiet(suai.link_sty, self.sty, suai.STY)     # в Windows может выйти копия
        self.assertEqual(self.sty.is_symlink(), linked)
        self.assertEqual(self.sty.read_bytes(), suai.STY.read_bytes())
        self.assertEqual(suai.refresh_sty(), "ok")

    def test_copy_when_symlinks_are_not_allowed(self):
        with mock.patch.object(Path, "symlink_to", side_effect=OSError(1314, "нет прав")):
            self.assertFalse(quiet(suai.link_sty, self.sty, suai.STY))
        self.assertFalse(self.sty.is_symlink())
        self.assertEqual(self.sty.read_bytes(), suai.STY.read_bytes())

    def test_install_replaces_old_file(self):
        self.sty.parent.mkdir(parents=True)
        self.sty.write_text("старое", encoding="utf-8")
        quiet(suai.link_sty, self.sty, suai.STY)
        self.assertEqual(self.sty.read_bytes(), suai.STY.read_bytes())

    def test_stale_copy_is_refreshed(self):
        self.assertEqual(suai.refresh_sty(), "missing")
        self.sty.parent.mkdir(parents=True)
        self.sty.write_text("старое", encoding="utf-8")
        self.assertEqual(suai.refresh_sty(), "updated")
        self.assertEqual(self.sty.read_bytes(), suai.STY.read_bytes())
        self.assertEqual(suai.refresh_sty(), "ok")

    def test_unix_launcher(self):
        self.patch("WINDOWS", False)
        text = suai.launcher().decode()
        self.assertTrue(text.startswith("#!/bin/sh\nexec python3 "))
        self.assertIn(str(Path(suai.__file__).resolve()), text)

    def test_windows_launcher(self):
        self.patch("WINDOWS", True)
        text = suai.launcher().decode("utf-8")
        line = text.splitlines()[-1]
        self.assertEqual(line, f'@"{sys.executable}" "{Path(suai.__file__).resolve()}" %*')
        self.assertTrue(text.endswith("\r\n"))
        self.assertNotIn("python3 ", line)

    def test_in_path(self):
        d = self.root / "bin"
        self.assertTrue(suai.in_path(d, f'/x;"{d}"', ";"))
        self.assertTrue(suai.in_path(d, f"{d}{os.sep}", ";"))
        self.assertFalse(suai.in_path(d, f"/x;{d}-other;", ";"))

    def test_user_path_is_appended_once(self):
        d = self.root / "bin"
        registry = FakeWinreg("C:\\Tools;%USERPROFILE%\\go\\bin;", FakeWinreg.REG_SZ)
        self.assertTrue(self.user_path(registry, d))
        self.assertEqual(registry.value, f"C:\\Tools;%USERPROFILE%\\go\\bin;{d}")
        self.assertEqual(registry.kind, FakeWinreg.REG_SZ)
        self.assertFalse(self.user_path(registry, d))
        self.assertEqual(registry.value, f"C:\\Tools;%USERPROFILE%\\go\\bin;{d}")

    def test_user_path_created_when_absent(self):
        registry = FakeWinreg()
        self.assertTrue(self.user_path(registry, self.root / "bin"))
        self.assertEqual(registry.value, str(self.root / "bin"))
        self.assertEqual(registry.kind, FakeWinreg.REG_EXPAND_SZ)

    def test_miktex_needs_perl(self):
        self.patch("shutil", mock.Mock(which=lambda name: None if name == "perl" else name))
        self.assertEqual(suai.missing_tools(), ["perl"])

    def test_files_are_written_with_lf(self):
        suai.write_text(self.root / "a.tex", "один\nдва\n")
        self.assertEqual((self.root / "a.tex").read_bytes(), "один\nдва\n".encode("utf-8"))


class ReportTestCase(unittest.TestCase):
    """Временная папка курса; ~/texmf и VS Code не трогаются."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for target, value in (("texmf_sty", mock.Mock(return_value=self.root / "none.sty")),
                              ("open_editor", mock.Mock())):
            patcher = mock.patch.object(suai, target, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def chdir(self, path: Path):
        old = os.getcwd()
        os.chdir(path)
        self.addCleanup(os.chdir, old)

    def new(self, name, title=None):
        quiet(suai.cmd_new, self.root / name, title, True)
        return suai.read_setup(self.root / name / "main.tex")

    def assertDies(self, fn, *args):
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            quiet(fn, *args)


class NewTest(ReportTestCase):
    def test_creates_report(self):
        setup = self.new("lab-4", "Настройка S3")
        d = self.root / "lab-4"
        self.assertTrue((d / "images").is_dir())
        self.assertEqual((d / ".gitignore").read_text(encoding="utf-8"), suai.REPORT_GITIGNORE)
        for f in suai.VSCODE.iterdir():
            self.assertEqual((d / ".vscode" / f.name).read_bytes(), f.read_bytes())
        self.assertIn("number       = 4,", setup)
        self.assertIn("title        = Настройка S3,", setup)
        self.assertIn("date         = today,", setup)
        suai.open_editor.assert_not_called()

    def test_body_comes_from_template(self):
        self.new("lab-1")
        main = (self.root / "lab-1" / "main.tex").read_text(encoding="utf-8")
        template = suai.TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(main.split("\\begin{document}")[1], template.split("\\begin{document}")[1])
        self.assertEqual(main.count("\\suaisetup{"), 1)

    def test_title_page_from_demo_without_siblings(self):
        setup = self.new("lab-1")
        demo = suai.read_setup(suai.DEMO)
        for key in ("teacher", "student", "course"):
            line = next(l for l in demo.splitlines() if l.lstrip().startswith(key))
            self.assertIn(suai.split_comment(line)[0].rstrip(), setup)
        self.assertIn("title        = Название работы,", setup)

    def test_title_page_from_newest_sibling(self):
        old = self.root / "lab-1"
        old.mkdir()
        (old / "main.tex").write_text(SETUP.replace("Б. Б. Студентов", "Старый"), encoding="utf-8")
        os.utime(old / "main.tex", (1, 1))
        fresh = self.root / "lab-2"
        fresh.mkdir()
        (fresh / "main.tex").write_text(SETUP, encoding="utf-8")

        setup = self.new("lab-3")
        self.assertIn("А. А. Преподов", setup)
        self.assertIn("Б. Б. Студентов", setup)
        self.assertIn("number       = 3,", setup)
        self.assertNotIn("01.09.2026", setup)

    def test_no_number_in_dir_name(self):
        setup = self.new("kursovaya")
        self.assertIn("number       = ,", setup)

    def test_refuses_existing_report(self):
        self.new("lab-1")
        self.assertDies(suai.cmd_new, self.root / "lab-1", None, True)

    def test_refuses_template_dir(self):
        self.assertDies(suai.cmd_new, suai.SRC, None, True)

    def test_keeps_existing_gitignore(self):
        d = self.root / "lab-1"
        d.mkdir()
        (d / ".gitignore").write_text("*.log\n", encoding="utf-8")
        self.new("lab-1")
        self.assertEqual((d / ".gitignore").read_text(encoding="utf-8"), "*.log\n")


class NextTest(ReportTestCase):
    def test_next_number(self):
        self.new("lab-3")
        self.chdir(self.root / "lab-3")
        quiet(suai.cmd_next, "Дальше", True)
        setup = suai.read_setup(self.root / "lab-4" / "main.tex")
        self.assertIn("number       = 4,", setup)
        self.assertIn("title        = Дальше,", setup)

    def test_keeps_zero_padding(self):
        self.new("lab-01")
        self.chdir(self.root / "lab-01")
        quiet(suai.cmd_next, None, True)
        self.assertTrue((self.root / "lab-02" / "main.tex").exists())

    def test_prefers_own_title_page_over_newer_sibling(self):
        cur = self.root / "lab-3"
        cur.mkdir()
        (cur / "main.tex").write_text(SETUP.replace("А. А. Преподов", "Свой"),
                                      encoding="utf-8")
        os.utime(cur / "main.tex", (1, 1))
        other = self.root / "lab-9"
        other.mkdir()
        (other / "main.tex").write_text(SETUP.replace("А. А. Преподов", "Чужой"),
                                        encoding="utf-8")

        self.chdir(cur)
        quiet(suai.cmd_next, None, True)
        setup = suai.read_setup(self.root / "lab-4" / "main.tex")
        self.assertIn("Свой", setup)
        self.assertNotIn("Чужой", setup)

    def test_dir_without_number(self):
        (self.root / "notes").mkdir()
        self.chdir(self.root / "notes")
        self.assertDies(suai.cmd_next, None, True)


class UpdateTest(ReportTestCase):
    def test_restores_changed_files(self):
        self.new("lab-1")
        d = self.root / "lab-1"
        (d / ".vscode" / "settings.json").write_text("{}", encoding="utf-8")
        (d / ".vscode" / "extensions.json").unlink()
        self.assertEqual(suai.install_kit(d), [".vscode/extensions.json", ".vscode/settings.json"])
        self.assertEqual(suai.install_kit(d), [])

    def test_update_needs_main_tex(self):
        self.chdir(self.root)
        self.assertDies(suai.cmd_update)

    def test_update_refuses_template(self):
        self.chdir(suai.REPO)
        self.assertDies(suai.cmd_update)


if __name__ == "__main__":
    unittest.main()
