import contextlib
import io
import os
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

    def test_template_dir_detection(self):
        self.assertTrue(suai.is_template_dir(suai.REPO))
        self.assertTrue(suai.is_template_dir(suai.DEMO.parent))
        self.assertTrue(suai.is_template_dir(suai.SRC))
        self.assertFalse(suai.is_template_dir(Path(tempfile.gettempdir())))


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
