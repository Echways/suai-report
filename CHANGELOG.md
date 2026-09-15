# Изменения

Разделы пишутся по-английски: текст раздела уходит в GitHub Release, а при
пометке `<!-- announce -->` ещё и в рассылку CTAN. Новое пишется под
`## Unreleased`, `make release VERSION=…` сам превратит его в раздел версии.

## 2.1 - 2026-09-15

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
