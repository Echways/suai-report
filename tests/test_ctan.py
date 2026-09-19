import datetime
import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import ctan  # noqa: E402

STY = "\\NeedsTeXFormat{LaTeX2e}\n\\ProvidesPackage{suai-report}[2026/09/14 v2.0 SUAI report]\n"

CHANGELOG = """# Изменения

Пояснение про `## Unreleased`.

## Unreleased

- new thing

## 2.0 — 2026-09-14

<!-- announce -->
First release.

## 1.0 — 2026-01-01

Old.
"""


class VersionTest(unittest.TestCase):
    def test_sty_version(self):
        self.assertEqual(ctan.sty_version(STY), ("2.0", "2026-09-14"))

    def test_repo_sty_has_version(self):
        version, date = ctan.sty_version()
        self.assertRegex(version, ctan.VERSION_RE)
        datetime.date.fromisoformat(date)

    def test_section_accepts_any_dash(self):
        for dash in ("-", "–", "—"):
            text = f"# Изменения\n\n## 2.0 {dash} 2026-09-14\n\nBody.\n"
            self.assertEqual(ctan.sections(text), [("2.0", "2026-09-14", "Body.")])

    def test_repo_changelog_matches_sty(self):
        version, _ = ctan.sty_version()
        errors = ctan.check_tag(f"v{version}", ctan.STY.read_text(encoding="utf-8"),
                                ctan.CHANGELOG.read_text(encoding="utf-8"))
        self.assertEqual(errors, [])


class CheckTagTest(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(ctan.check_tag("v2.0", STY, CHANGELOG), [])

    def test_wrong_tag(self):
        errors = ctan.check_tag("v2.1", STY, CHANGELOG)
        self.assertEqual(len(errors), 1)
        self.assertIn("v2.1", errors[0])

    def test_missing_section(self):
        errors = ctan.check_tag("v2.0", STY, CHANGELOG.replace("## 2.0 — 2026-09-14", ""))
        self.assertTrue(any("нет раздела" in e for e in errors))

    def test_date_mismatch(self):
        errors = ctan.check_tag("v2.0", STY, CHANGELOG.replace("2026-09-14", "2026-09-13"))
        self.assertTrue(any("дата" in e for e in errors))


class NotesTest(unittest.TestCase):
    def test_notes_strip_marker(self):
        self.assertEqual(ctan.notes(CHANGELOG, "2.0"), "First release.")

    def test_announce_only_when_marked(self):
        self.assertEqual(ctan.notes(CHANGELOG, "2.0", announce_only=True), "First release.")
        self.assertEqual(ctan.notes(CHANGELOG, "1.0", announce_only=True), "")

    def test_inline_heading_is_not_a_section(self):
        self.assertEqual([v for v, _, _ in ctan.sections(CHANGELOG)],
                         ["Unreleased", "2.0", "1.0"])

    def test_archive_changelog_skips_unreleased(self):
        out = ctan.changelog_for_archive(CHANGELOG)
        self.assertNotIn("Unreleased", out)
        self.assertNotIn("announce", out)
        self.assertIn("## 2.0 — 2026-09-14\n\nFirst release.", out)


class BumpTest(unittest.TestCase):
    DATE = datetime.date(2026, 10, 1)

    def test_bump(self):
        sty, log = ctan.bump(STY, CHANGELOG, "2.1", self.DATE)
        self.assertEqual(ctan.sty_version(sty), ("2.1", "2026-10-01"))
        self.assertIn("SUAI report]", sty)
        self.assertIn("## Unreleased\n\n## 2.1 — 2026-10-01\n\n- new thing", log)
        self.assertEqual(ctan.check_tag("v2.1", sty, log), [])
        self.assertEqual(ctan.notes(log, "Unreleased"), "")

    def test_rejects_old_version(self):
        for version in ("2.0", "1.9", "2.0.0"):
            with self.assertRaises(SystemExit):
                ctan.bump(STY, CHANGELOG, version, self.DATE)

    def test_rejects_bad_format(self):
        with self.assertRaises(SystemExit):
            ctan.bump(STY, CHANGELOG, "v2.1", self.DATE)

    def test_rejects_empty_unreleased(self):
        with self.assertRaises(SystemExit):
            ctan.bump(STY, CHANGELOG.replace("- new thing", ""), "2.1", self.DATE)


class ArchiveTest(unittest.TestCase):
    def test_forbidden(self):
        self.assertIsNone(ctan.forbidden("suai-report.sty"))
        self.assertIsNone(ctan.forbidden("images/scheme.png"))
        self.assertIsNone(ctan.forbidden("suai-report-demo.pdf"))
        for name in (".gitignore", "images/.DS_Store", "main.log", "build/main.aux",
                     "main.pdf", "картинка.png", "my dir/a.tex"):
            self.assertIsNotNone(ctan.forbidden(name), name)

    def test_zip_layout(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "suai-report.zip"
            ctan.build_zip({"suai-report.sty": b"x", "images/a.png": b"y"}, dest)
            with zipfile.ZipFile(dest) as z:
                self.assertEqual(z.namelist(), ["suai-report/images/a.png", "suai-report/suai-report.sty"])
                self.assertEqual(z.getinfo("suai-report/suai-report.sty").external_attr >> 16, 0o644)
            first = dest.read_bytes()
            ctan.build_zip({"suai-report.sty": b"x", "images/a.png": b"y"}, dest)
            self.assertEqual(dest.read_bytes(), first)

    def test_zip_rejects_forbidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit):
                ctan.build_zip({".vscode/settings.json": b"{}"}, Path(tmp) / "suai-report.zip")

    def test_repo_entries_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            for src in ctan.FILES.values():
                (repo / src).parent.mkdir(parents=True, exist_ok=True)
                (repo / src).write_bytes(b"x")
            (repo / "demo" / "images").mkdir(parents=True, exist_ok=True)
            (repo / "demo" / "images" / "scheme.png").write_bytes(b"png")
            (repo / "CHANGELOG.md").write_text(CHANGELOG, encoding="utf-8")
            entries = ctan.archive_entries(repo)
            self.assertIn("README.md", entries)
            self.assertIn("suai-report-demo.pdf", entries)
            self.assertIn("images/scheme.png", entries)
            self.assertEqual([n for n in entries if ctan.forbidden(n)], [])

    def test_missing_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit), \
                    mock.patch("sys.stderr", io.StringIO()):
                ctan.archive_entries(Path(tmp))


class ApiTest(unittest.TestCase):
    def test_meta_fits_ctan_limits(self):
        meta = ctan.load_meta()
        form = ctan.fields(meta, "2.0", "a@example.org", "")
        keys = [k for k, _ in form]
        for key in ("pkg", "version", "author", "uploader", "email", "summary",
                    "description", "ctanPath", "license", "update"):
            self.assertIn(key, keys)
        self.assertEqual(keys.count("topic"), len(meta["topic"]))
        self.assertRegex(meta["pkg"], r"^[a-z][a-z0-9_-]*$")

    def test_field_too_long(self):
        with self.assertRaises(SystemExit):
            ctan.fields({"summary": "x" * 129}, "2.0", "a@example.org", "")

    def test_multipart(self):
        body, ctype = ctan.multipart([("pkg", "suai-report"), ("topic", "a"), ("topic", "b")],
                                     "suai-report.zip", b"ZIPDATA")
        boundary = ctype.split("boundary=")[1]
        self.assertTrue(ctype.startswith("multipart/form-data"))
        self.assertEqual(body.count(b'name="topic"'), 2)
        self.assertIn(b'filename="suai-report.zip"', body)
        self.assertIn(b"ZIPDATA", body)
        self.assertTrue(body.endswith(f"--{boundary}--\r\n".encode()))

    def test_parse_response(self):
        ok, lines = ctan.parse_response(200, b'[["INFO", "Upload successful"]]')
        self.assertTrue(ok)
        self.assertEqual(lines, ["INFO Upload successful"])
        ok, _ = ctan.parse_response(200, b'[["WARNING", "w"], ["ERROR", "Missing field", "pkg"]]')
        self.assertFalse(ok)
        ok, _ = ctan.parse_response(409, b'[["WARNING", "w"]]')
        self.assertFalse(ok)
        ok, lines = ctan.parse_response(500, b"<html>oops</html>")
        self.assertFalse(ok)
        self.assertIn("HTTP 500", lines[0])


if __name__ == "__main__":
    unittest.main()
