import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import suai  # noqa: E402

DOC = """\\documentclass[a4paper,14pt]{extarticle}
\\usepackage{suai-report}
\\begin{document}
%s\\end{document}
"""

LINES = "\\ExplSyntaxOn\\typeout{LINES=\\seq_count:N \\g__suai_lines_seq}\\ExplSyntaxOff\n"

MARKS = "\\lstset{keywordstyle=\\typeout{KEYWORD}, commentstyle=\\typeout{COMMENT}}\n"
UNKNOWN = "Язык листинга %s"

LANGUAGES = {
    "JavaScript": "const x = 1; // c",
    "TypeScript": "interface A {} // c",
    "Kotlin": "fun main() {} // c",
    "Rust": "fn main() {} // c",
    "JSON": '{"a": true}',
    "YAML": "a: true # c",
    "Dockerfile": "FROM alpine # c",
}
ALIASES = {
    "cpp": "int x; // c",
    "cs": "class A {} // c",
    "csharp": "class A {} // c",
    "C#": "class A {} // c",
    "js": "const x = 1; // c",
    "ts": "interface A {} // c",
    "py": "def f(): pass # c",
    "sh": "if true; then echo; fi # c",
    "kt": "fun main() {} // c",
    "rs": "fn main() {} // c",
    "yml": "a: true # c",
    "docker": "FROM alpine # c",
}


def code(language, line):
    return f"\\suaicode[{language}]{{Код}}\n  {line}\n\n"


@unittest.skipIf(shutil.which("xelatex") is None, "нет xelatex")
class StyTest(unittest.TestCase):
    def build(self, body, **files):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = self.root = Path(tmp.name)
        suai.write_text(root / "main.tex", DOC % body)
        for name, text in files.items():
            suai.write_text(root / f"{name}.tex", text)
        env = dict(os.environ, TEXINPUTS=os.pathsep.join([".", str(suai.SRC), ""]))
        run = subprocess.run(
            ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
            cwd=root, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log = (root / "main.log").read_text(encoding="utf-8", errors="replace")
        errors = [l for l in log.splitlines() if l.startswith("!")]
        self.assertEqual((run.returncode, errors), (0, []))
        return log

    def test_command_line_ends_block(self):
        log = self.build(
            "\\suailist\nодин\nдва\n\\section{Дальше}\n" + LINES
            + "\\begin{center}\n\\suailist\nодин\nдва\n\\end{center}\n" + LINES
            + "\\suailist\nодин\nдва\n\\begin{center}текст\\end{center}\n" + LINES
            + "\\suailist\nодин\nдва\n\\suaitable{Т}\nA | B\n\n" + LINES)
        self.assertEqual(log.count("LINES=2"), 3)
        self.assertEqual(log.count("LINES=1"), 1)

    def test_listing_environment_keeps_first_line(self):
        listing = "\\begin{lstlisting}[language=Python]\nimport os\nx = 1\n\\end{lstlisting}\n"
        log = self.build(
            MARKS + "\\suailist\nодин\nдва\n" + listing
            + "\\suailist\nодин\nдва\n\\begin{code}[Python]{Код}\nimport os\n\\end{code}\n"
            + "\\suaicode[Python]{Код}\n  x = 1\n" + listing
            + "\\suailist\nодин\nдва\n\\begin{align}\na &= b\n\\end{align}\n")
        self.assertEqual(log.count("KEYWORD"), 3)

    def test_block_before_end_document(self):
        self.build("\\suailist\nодин\nдва\n")

    def test_block_at_end_of_input_file(self):
        log = self.build("\\input{part}\n" + LINES + "\\input{table}\n" + LINES,
                         part="\\suailist\nодин\nдва\n",
                         table="\\suaitable{Т}\nA | B\n1 | 2\n3 | 4")
        self.assertEqual(log.count("LINES=2"), 1)
        self.assertEqual(log.count("LINES=3"), 1)

    def test_code_at_end_of_input_file(self):
        self.build("\\input{code}\nтекст\n\n\\input{blank}\nтекст\n",
                   code="\\suaicode[bash]{Код}\n  echo 1\n",
                   blank="\\suaicode[bash]{Код}\n  echo 1\n\n")

    def test_table_cell_with_spaces_in_math(self):
        self.build("\\suaitable{Т}\nФормула | Ещё\n"
                   "$a + b$ | \\( c + d \\)\n"
                   "$\\lvert x \\rvert$ и текст | \\texttt {x y}\n\n")

    def test_bar_inside_formula_does_not_split_cell(self):
        log = self.build(
            "\\ExplSyntaxOn\\cs_set_eq:NN \\suaicells \\__suai_cells:n\n"
            "\\cs_new:Npn \\suaicount { \\seq_count:N \\l__suai_cells_seq }\\ExplSyntaxOff\n"
            + "".join(f"\\suaicells{{{row}}}\\typeout{{CELLS {n}=\\suaicount}}\n"
                      for n, row in enumerate([
                          "$|x|$ | модуль | $a$",
                          "\\( a | b \\) | условная вероятность",
                          "5 \\$ | цена | \\textbf{$a|b$}",
                          "A | | C"]))
            + "\\suaitable{Т}\nФормула | Смысл\n$|x|$ | модуль\n\n"
            + "\\suaieq{y = |x|}\n$|x|$ | модуль числа\n\n")
        self.assertEqual(re.findall(r"CELLS \d=(\d+)", log), ["3", "2", "3", "3"])

    def test_comment_belongs_to_its_line(self):
        log = self.build(
            "\\suailist\nпервый % пояснение\n% строка целиком\nвторой, 50\\%\n"
            "\\url{https://example.com/a%20b}\n\n" + LINES
            + "\\suaitable{Т} % подпись\nA | B % шапка\n1 | 2\n"
            "\\section{Дальше} % и здесь\n" + LINES)
        self.assertEqual(re.findall(r"LINES=(\d+)", log), ["3", "2"])

    def items(self, body):
        """Пункты списка так, как они набраны, вместе со знаком в конце."""
        log = self.build(
            "\\ExplSyntaxOn\\cs_set_eq:NN \\suaiitem \\__suai_list_item:nn\n"
            "\\cs_set_protected:Npn \\__suai_list_item:nn #1#2\n"
            "  { \\suaiitem {#1} {#2} \\iow_term:x { ITEM=\\exp_not:V \\l__suai_item_tl } }\n"
            "\\ExplSyntaxOff\n" + body)
        return re.findall(r"ITEM=(.*)", log)

    def test_list_punctuation(self):
        self.assertEqual(self.items("\\suailist\nпервый\nвторой;\nтретий,\n\n"),
                         ["первый;", "второй;", "третий."])

    def test_abbreviation_keeps_its_dot(self):
        self.assertEqual(
            self.items("\\suailist\nфайлы, папки и т. д.\nотчёты и др.;\n"
                       "данные за 2026 г.\nвес 5 кг.\nпрочее и т.п.\n\n"),
            ["файлы, папки и т. д.;", "отчёты и др.;", "данные за 2026 г.;",
             "вес 5 кг;", "прочее и т.п."])

    def test_table_spacing_follows_text(self):
        """Интервал в таблицах как в тексте; \\suaitablestretch — один на все."""
        body = ("\\typeout{TEXT=\\the\\baselineskip}\n"
                "\\suaitable{Т}\nA | B\n\\typeout{AUTO=\\the\\baselineskip}x | y\n\n"
                "\\begin{tabularx}{\\textwidth}{|X|}\\hline\n"
                "\\typeout{MANUAL=\\the\\baselineskip}a\\\\\\hline\\end{tabularx}\n")
        for setup, stretch in ("", 1.25), ("\\renewcommand{\\suaitablestretch}{1}\n", 1):
            with self.subTest(setup):
                log = self.build(setup + body)
                text = float(re.search(r"TEXT=([\d.]+)pt", log).group(1))
                # \suaitable набирает ячейку ещё и при замере ширин, вне
                # таблицы: в ней самой — последний раз
                found = [float(re.findall(rf"{name}=([\d.]+)pt", log)[-1])
                         for name in ("AUTO", "MANUAL")]
                self.assertEqual(found, [text / 1.25 * stretch] * 2)

    def test_tabular_inside_paragraph_keeps_it_whole(self):
        log = self.build("\\renewcommand{\\suaitablestretch}{1}\n"
                         "\\newcount\\pars \\everypar{\\global\\advance\\pars 1 }%\n"
                         "Строка \\begin{tabular}{l}a\\end{tabular} дальше\\par"
                         "\\typeout{PARS=\\the\\pars}\n")
        self.assertIn("PARS=1", log)

    def test_appendix_bookmark_has_its_letter(self):
        # закладки пишутся сразу в PDF; без сжатия их названия читаются как есть
        self.build("\\special{dvipdfmx:config z 0}%\n"
                   "\\suaiapp{Первое}\nтекст\n\\suaiapp[справочное]{Второе}\nтекст\n")
        pdf = (self.root / "main.pdf").read_bytes()
        titles = [bytes.fromhex(t.decode()).decode("utf-16")
                  for t in re.findall(rb"/Title\s*<([0-9A-Fa-f]+)>", pdf)]
        self.assertEqual(titles, ["Приложение А. Первое", "Приложение Б. Второе"])

    def assert_highlighted(self, samples):
        log = self.build(MARKS + "".join(
            f"\\typeout{{SAMPLE {n}}}\n" + code(name, line)
            for n, (name, line) in enumerate(samples.items())))
        self.assertNotIn(UNKNOWN % "", log)
        chunks = re.split(r"SAMPLE \d+\n", log)[1:]
        for (name, line), chunk in zip(samples.items(), chunks, strict=True):
            with self.subTest(name):
                self.assertIn("KEYWORD", chunk)
                if " c" in line:
                    self.assertIn("COMMENT", chunk)

    def test_unknown_language_is_not_an_error(self):
        log = self.build(
            code("Brainfuck", "+++") + code("language=Whitespace", "x")
            + "\\begin{lstlisting}[language=Befunge]\nx\n\\end{lstlisting}\n")
        for name in "Brainfuck", "Whitespace", "Befunge":
            self.assertIn(UNKNOWN % f"'{name}' неизвестен", log)

    def test_unknown_language_has_no_highlighting(self):
        log = self.build(MARKS + "\\lstset{language=Python}\n"
                         + code("Brainfuck", "def f(): pass"))
        self.assertNotIn("KEYWORD", log)

    def test_added_languages_are_highlighted(self):
        self.assert_highlighted(LANGUAGES)

    def test_short_language_names(self):
        self.assert_highlighted(ALIASES)

    def test_yaml_apostrophe_does_not_open_string(self):
        log = self.build(MARKS + code("YAML", "note: don't stop\n  enabled: true"))
        self.assertIn("KEYWORD", log)

    def test_snippet_languages_are_known(self):
        lists = {choice for f in sorted(suai.VSCODE.glob("suai*"))
                 for choice in re.findall(r"suaicode\[\$\{\d\|([^|]+)\|",
                                          f.read_text(encoding="utf-8"))}
        self.assertEqual(len(lists), 1, "список языков в сниппетах один и тот же")
        languages = lists.pop().split(",")
        self.assertIn("JavaScript", languages)
        log = self.build("".join(code(name, "x") for name in languages))
        self.assertNotIn(UNKNOWN % "", log)


if __name__ == "__main__":
    unittest.main()
