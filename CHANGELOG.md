# Изменения

Разделы пишутся по-английски: текст раздела уходит в GitHub Release, а при
пометке `<!-- announce -->` ещё и в рассылку CTAN. Новое пишется под
`## Unreleased`, `make release VERSION=…` сам превратит его в раздел версии.

## Unreleased

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
