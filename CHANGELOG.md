## Unreleased

## 2.7.2 — 2026-10-07

- Listings: keywords are no longer bold. GOST 7.32-2017 (6.1.1) keeps bold
  type for headings, and the package said so, but the default of `listings`
  was still in effect. The line breaks of a listing do not change. To get
  bold keywords back: `\lstset{keywordstyle=\bfseries}`.
- A nested `enumerate` numbers its second level with Russian letters, `а)`,
  `б)`, like the first level of `gostenum`, instead of the Latin `(a)`,
  `(b)`.
- Documentation: the README is now a short entry page, the details moved
  to `docs/`: installation, the `suai` command, the title page, every
  command with an example, settings for a department's own rules, VS Code,
  what the package sets up by GOST 7.32-2017, troubleshooting and
  development notes.
- The demo report is rewritten: it now uses every command of the package,
  including `\suaienum`, `\suainum`, `\suaisection`, `\suaiapp`, a listing
  read from a file and a table and a listing that run over a page. The CTAN
  archive ships the `code/` folder of the demo next to `images/`.

## 2.7.1 — 2026-10-06

- Listings: a captioned listing that runs over a page now starts each next
  page with `Продолжение листинга N`, the way a table does. The frame is
  closed at the bottom of the page and opened again under that line. This
  holds for `\suaicode` and `lstlisting` alike; a listing that fits on its
  page is typeset exactly as before. To switch the line off:
  `\renewcommand{\suailistingcontinued}{}`.
- Listings: a caption no longer stays at the bottom of a page without its
  code. A listing needs room for three lines of text under the caption,
  otherwise it moves to the next page as a whole, and `\pageref` to it
  gives that page.

## 2.7 — 2026-10-05

- A block (`\suailist`, `\suaitable`, `\suaieq`, …) now really ends at a
  line starting with `\section`, `\begin`, `\end`, `\par`, `\clearpage`
  and the like, as it always did at `\suai…`. Before, such a line was read
  as one more item, and a block right above `\end{document}` stopped the
  build with `File ended while scanning use of \__suai_line:w`.
- A `lstlisting` (or an environment made with `\lstnewenvironment`) right
  below a block or below the code of `\suaicode`, with no blank line in
  between, keeps its first line of code.
- A block or the code under `\suaicode` may be the last thing in a file
  read with `\input`: the end of the file ends it.
- `\suaitable`: a cell with spaces inside a formula, such as `$a + b$` or
  `\( a + b \)`, no longer fails with `Missing $ inserted`. The longest
  word of a column is now measured by typesetting the cell instead of
  cutting it at spaces, so `\textbf{several words}` counts as several
  words too. Column widths of other tables are unchanged.
- Listings: an unknown language no longer stops the build with
  `Couldn't load requested language`. The code is typeset without
  highlighting and the log gets the warning `Язык листинга '…' неизвестен`.
  This holds for `\suaicode`, `\lstset{language=…}` and `lstlisting` alike.
- Listings: JavaScript, TypeScript, Kotlin, Rust, JSON, YAML and Dockerfile
  are defined by the package (comments, strings, main keywords), next to
  the languages of `listings` itself.
- Listings: short language names `cpp`, `cs`, `csharp`, `js`, `ts`, `py`,
  `kt`, `rs`, `yml`, `docker`; `\suaicode[C#]{…}` works as written.
- VS Code: the `lst` and `code` snippets and the `\suaicode` completion
  offer the new languages, C# and Go.
- Tables typed by hand (`tabular`, `tabularx`, `longtable`) are set with
  the line spacing of the text, like `\suaitable` always was: GOST 7.32-2017
  names no other spacing for tables. They used to be single-spaced, and
  the `\singlespacing` behind it broke the paragraph around a `tabular`
  and put an empty line above every such table.
  `\renewcommand{\suaitablestretch}{1}` makes all tables, `\suaitable`
  included, single-spaced.
- Lists and `\suaieq`: the full stop of an abbreviation at the end of an
  item (`и т. д.`, `и т. п.`, `и др.`, `и пр.`, `г.`, `гг.`, `вв.`, `руб.`,
  `коп.`, `тыс.`, `шт.`, `экз.`, `стр.`) is kept: `и т. д.;` instead of
  `и т. д;`.
- A `%` comment in a line of a block belongs to that line only. Before, it
  swallowed the line end and glued the line to the next one. A line that is
  only a comment is skipped, `%` inside braces (`\url{…a%20b}`) is kept.
- `\suaitable`, `\suaieq`: a `|` inside a formula (`$|x|$`, `\( a | b \)`)
  no longer splits the cell.
- The PDF bookmark of an appendix carries its letter: `Приложение А. Title`.
- `suai new --title` and `suai next --title`: `& _ ^` and a lone `$` in
  the title are escaped like `%` and `#`, `$…$` stays a formula, and a title
  with `=` is put in braces. Such titles used to stop the build.

## 2.6 — 2026-10-02

- Windows: the build no longer calls `cp` from a shell. The finished PDF
  is copied next to `main.tex` by latexmk itself, so the VS Code recipe and
  `suai build` work the same on Linux, macOS and Windows. Existing reports
  get it with `suai update`.
- Windows: `python scripts\suai.py install` works without `make`. Where
  symlinks are not allowed `suai-report.sty` is copied (and refreshed by
  `suai install`, `suai new` and `suai update`), the `suai` command is a
  `suai.cmd` that runs the Python it was installed with, and its folder is
  added to the user's `PATH`. MiKTeX gets its root registered and its file
  name database refreshed. `suai open` uses the system viewer on Windows
  and macOS, and VS Code is found when it is `code.cmd`.
- `suai install` lists the missing tools (`xelatex`, `latexmk`, `biber`,
  and Perl with MiKTeX). Files written by `suai` always have LF line ends.
- The package no longer uses `\peek_catcode_ignore_spaces:NTF`, deprecated
  in expl3 since 2022, nor `\use:x`. The typeset report is unchanged.

## 2.5 — 2026-09-29

- Code in the text is written with `\suaicode` too: `\suaicode[bash, backup]{Caption}`
  followed by indented lines. Blank lines inside the code are kept, the
  code ends at the first line without indentation, the common indentation
  is removed and tabs count as 4 columns. `%`, `#`, `\` and braces need no
  escaping. The first argument of the file form also takes
  `[language, label]` and listings keys. `\begin{code}` still works but is
  no longer documented; the VS Code `lst` snippet inserts `\suaicode`.
- Listings under XeLaTeX: a Cyrillic word at the start of a code line
  jumped to the end of the previous line. Cyrillic letters, dashes, quotes
  and `№` now go through listings like ASCII.

## 2.4 — 2026-09-29

- Lists are set like ordinary paragraphs, as GUAP's standards check
  requires: the label starts at the paragraph indent, and the following
  lines of an item go back to the left margin instead of lining up under
  the text after the label. Nested lists start at 2 cm, whatever the list
  type (`itemize` inside `enumerate` used to sit at the first level).

## 2.3 — 2026-09-29

- Tables no longer run over the rules with long entries such as formulas,
  cell ranges or identifiers (`='Журнал'!I6>СРЗНАЧ(БД_Фильтр)`). Each column
  is measured at four widths — whole cell, whole words, pieces between
  break points, syllables — and the table takes the widest level that
  fits, sharing the rest by how much each column still wants. Words are
  broken only when there is no other way, syllables last; a column holding
  a long number or date is never narrower than it. Manual `\allowbreak`
  in cells is no longer needed.
- A line may break inside a long space-free "word" after `_ / = + ! -`, and
  in monospaced text also after `. , ; : ? &` and before `(`/`[`
  (`center.yandex.cloud`, `UPPER(TRIM(...))`), at the cost of a hyphen.
  Not before a digit, so `1,5` and `01.01.2025` stay whole. Switch off
  with `\XeTeXinterchartokenstate=0`.
- `\tolerance=1000` and `\emergencystretch=3em`: a slightly looser line
  instead of one running into the margin.
- Listings break long lines without spaces too (`breakatwhitespace=false`).
- `\suaiimg` never makes a figure wider than the text block.
- VS Code: LaTeX Workshop now knows the package (`.vscode/suai-report.json`)
  and suggests `\suai...` commands with their arguments and a description,
  and the keys of `\suaisetup`. Snippets are listed after LaTeX Workshop's
  suggestions: with `"top"`, typing `\it` or `\begin{eq` and pressing Tab
  inserted a template instead of `\item`. Only the templates that also write
  the reference in the text are left (`img`, `tab`, `eq`, `lst`, `code`);
  the `code` and `img` ones derive the label from the file name.
  References suggest the labels of the last build (`fig:`, `tab:`, `eq:`,
  `lst:`) instead of bare figure names next to prefixed duplicates.
  `mathematic.vscode-latex` is marked as unwanted.
- The finished PDF is named after the subject and report folders:
  `Databases/lab-3/main.tex` gives `Databases-lab-3.pdf` instead of
  `main.pdf`, ready to send. The build output and the VS Code preview stay
  in `build/main.pdf`. `suai open` and `suai clean` know the new name;
  `suai clean` also removes an old `main.pdf`. Existing reports get it
  with `suai update`.

## 2.2 — 2026-09-21

- Table columns are measured by the width of the typeset text instead of the
  number of characters, so nothing runs over the rules any more. Every column
  is at least as wide as its longest word, and what is left over is shared
  out by how much width each column still wants. A narrow column such as
  `НДФЛ` used to be squeezed below the width of its own heading.
- A word that is still too long for its column is hyphenated rather than left
  hanging over the rule: cells now begin with `\hspace{0pt}`, which is what
  lets TeX break the first word of a cell.
- Section headings start at the paragraph indent again (GOST 7.32-2017,
  6.2.3). The indent was written as `\hspace*{\parindent}` inside the
  title label, where `\raggedright` had already zeroed `\parindent`.
- Equations are surrounded by at least one blank line (6.8.1), and
  multi-line figure captions are set with single line spacing (6.5.8).
- Captions use an em dash — `Рисунок 1 — Название` — as the standard itself
  does. The old en dash: `\captionsetup{labelsep=endash}`.
- Appendix headings are no longer uppercased (6.17.3), and the table of
  contents lists the appendix status, e.g. `ПРИЛОЖЕНИЕ А (обязательное)`
  (6.17.7).
- Listings: the block spans from margin to margin like a table, line
  numbers moved inside the frame, and the caption is left aligned above it.
- Bold is left to headings only (6.1.1): dropped from table header rows and
  from listing keywords. To bring it back: `\lstset{keywordstyle=\bfseries}`.
- `\suaicode{backup.sh}` labels the listing `lst:backup`, matching
  `\suaiimg`; `\lstref{backup}` used to come out as `??`.
- `multirow` is no longer loaded by the package: nothing in it used the macro.
  Reports that need merged cells add `\usepackage{multirow}` themselves.
- Removed the undocumented `\suaititlepage` alias for `\maketitle`.
- CHANGELOG headings may separate version and date with any dash. A plain
  `-` used to hide the whole section from `check-tag`, `notes` and the CTAN
  archive.
- `suai next` takes the title page from the current report instead of
  whichever neighbouring report was edited last.
- `suai new` no longer crashes without TeX Live installed, and escapes `%`
  and `#` in `--title`.
- VS Code: figure names are suggested inside `\figref{...}`; snippets for
  `\suaitoc`, `\suaisection` and the `*ref` commands; the listing snippets
  now fill the label first so the reference next to them matches.

## 2.1 — 2026-09-15

- `\suaisetup` values may contain commas without braces, e.g.
  `teacher-post = доцент, канд. техн. наук`.
- Text too wide for a title page field wraps upwards instead of overflowing.

## 2.0 — 2026-09-14

<!-- announce -->
First release on CTAN.

- Title page matching the official SUAI form.
- GOST 7.32-2017 layout: headings, table of contents, captions, tables,
  figures, equations, listings, appendices, list of sources.
- Line-based block commands: `\suaitasks`, `\suailist`, `\suaienum`,
  `\suainum`, `\suaitable`, `\suaieq`, `\suaisources`.
