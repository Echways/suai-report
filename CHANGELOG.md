# Изменения

Разделы пишутся по-английски: текст раздела уходит в GitHub Release, а при
пометке `<!-- announce -->` ещё и в рассылку CTAN. Новое пишется под
`## Unreleased`, `make release VERSION=…` сам превратит его в раздел версии.

## Unreleased

## 2.0 — 2026-09-14

<!-- announce -->
First release on CTAN.

- Title page matching the official SUAI form.
- GOST 7.32-2017 layout: headings, table of contents, captions, tables,
  figures, equations, listings, appendices, list of sources.
- Line-based block commands: `\guaptasks`, `\guaplist`, `\guapenum`,
  `\guapnum`, `\guaptable`, `\guapeq`, `\guapsources`.
