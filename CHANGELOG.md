# Изменения

Разделы пишутся по-английски: текст раздела уходит в GitHub Release, а при
пометке `<!-- announce -->` ещё и в рассылку CTAN. Новое пишется под
`## Unreleased`, `make release VERSION=…` сам превратит его в раздел версии.

## Unreleased

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
