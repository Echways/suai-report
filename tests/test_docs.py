import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import suai  # noqa: E402

REPO = suai.REPO
PAGES = [REPO / "README.md", *sorted((REPO / "docs").glob("*.md"))]

COMMAND_RE = re.compile(
    r"\\(?:newcommand|NewDocumentCommand)\s*\{?\\((?:suai[a-z]+|(?:fig|tab|lst|form)ref))(?![a-z@])")
KEY_RE = re.compile(r"^\s+([a-z-]+)\s+\.(?:tl_set|clist_set):", re.M)
LANGUAGE_RE = re.compile(r"\\lstdefinelanguage\{([^}]+)\}")
ALIAS_RE = re.compile(r"\\lstalias(?:\[\])?\{([^}]+)\}")
FENCE_RE = re.compile(r"^```.*?^```", re.M | re.S)
HEADING_RE = re.compile(r"^#+\s+(.+?)\s*$", re.M)
LINK_RE = re.compile(r"\]\(([^)\s]+)\)|(?:src|href)=\"([^\"]+)\"")

INTERNAL_COMMANDS = {"suairef", "suaiappletter"}
PREAMBLE_SETTINGS = {"suaiheadfont", "suaitablestretch", "suailistingcontinued"}


def read(path):
    return path.read_text(encoding="utf-8")


def github_anchors(text):
    out = set()
    for title in HEADING_RE.findall(FENCE_RE.sub("", text)):
        slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
        out.add(slug)
    return out


class DocsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sty = read(suai.STY)
        cls.docs = "\n".join(read(p) for p in PAGES)
        cls.commands = set(COMMAND_RE.findall(cls.sty)) - INTERNAL_COMMANDS

    def missing(self, names, text, pattern="`%s`"):
        return sorted(n for n in names if pattern % n not in text)

    def test_commands_are_found(self):
        self.assertIn("suaitable", self.commands)
        self.assertIn("figref", self.commands)
        self.assertNotIn("suai", self.commands)

    def test_every_command_is_documented(self):
        missing = sorted(c for c in self.commands if f"\\{c}" not in self.docs)
        self.assertEqual(missing, [])

    def test_every_command_is_in_writing_or_customization(self):
        pages = read(REPO / "docs" / "writing.md") + read(REPO / "docs" / "customization.md")
        missing = sorted(c for c in self.commands - {"suaisetup"} if f"\\{c}" not in pages)
        self.assertEqual(missing, [])

    def test_every_setup_key_is_documented(self):
        keys = set(KEY_RE.findall(self.sty))
        self.assertIn("teacher-post", keys)
        self.assertEqual(self.missing(keys, read(REPO / "docs" / "title.md")), [])

    def test_every_subcommand_is_documented(self):
        page = read(REPO / "docs" / "cli.md")
        self.assertEqual(self.missing(suai.HELP, page, "`suai %s"), [])

    def test_every_language_is_documented(self):
        page = read(REPO / "docs" / "writing.md")
        languages = LANGUAGE_RE.findall(self.sty)
        self.assertIn("Kotlin", languages)
        self.assertEqual(sorted(l for l in languages if l not in page), [])
        self.assertEqual(self.missing(ALIAS_RE.findall(self.sty), page), [])

    def test_styles_and_environments_are_documented(self):
        for name in ("gostcolor", "gostenum", "xltabular"):
            self.assertIn(name, self.docs)

    def test_demo_uses_every_command(self):
        demo = read(suai.DEMO)
        missing = sorted(c for c in self.commands - PREAMBLE_SETTINGS if f"\\{c}" not in demo)
        self.assertEqual(missing, [])

    def test_links(self):
        broken = []
        for page in PAGES:
            text = FENCE_RE.sub("", read(page))
            for found in LINK_RE.findall(text):
                link = found[0] or found[1]
                if re.match(r"[a-z]+:", link):
                    continue
                path, _, anchor = link.partition("#")
                target = (page.parent / path).resolve() if path else page
                if not target.exists():
                    broken.append(f"{page.name}: {link}")
                elif anchor and target.suffix == ".md" and anchor not in github_anchors(read(target)):
                    broken.append(f"{page.name}: {link}")
        self.assertEqual(broken, [])

    def test_every_page_is_linked_from_readme(self):
        readme = read(REPO / "README.md")
        missing = [p.name for p in PAGES[1:] if f"(docs/{p.name})" not in readme]
        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
