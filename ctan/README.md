# guap — SUAI reports following GOST 7.32-2017

The `guap` package typesets student reports (lab works, coursework,
practice reports) for Saint Petersburg State University of Aerospace
Instrumentation (SUAI, ГУАП) according to GOST 7.32-2017 and GOST 2.105-2019.

- The title page reproduces the official university form.
- Page layout, headings, table of contents, captions, tables, figures,
  equations, listings, appendices and the list of sources follow the
  standard without any configuration.
- Line-based block commands keep the source short: every line below
  `\guaptasks`, `\guaptable`, `\guapeq` or `\guapsources` becomes a list
  item, a table row or an explanation of a symbol.

The package requires XeLaTeX. Times New Roman, Liberation Sans and
Liberation Mono are used when installed, otherwise TeX Gyre Termes, Heros
and Cursor.

## Files

| File | Contents |
| --- | --- |
| `guap.sty` | the package |
| `guap-template.tex` | an empty report to start from |
| `guap-demo.tex`, `guap-demo.pdf` | a report showing every feature (in Russian) |
| `images/scheme.png` | a picture used by the demo |

## Usage

```latex
\documentclass[a4paper,14pt]{extarticle}
\usepackage{guap}

\guapsetup{
  department = 41,
  teacher    = И. И. Иванов,
  type       = Отчет о лабораторной работе,
  number     = 1,
  title      = Название работы,
  course     = Название дисциплины,
  group      = 4414,
  student    = И. И. Студентов,
  date       = today,
}

\begin{document}
\maketitle
\guaptoc
...
\end{document}
```

Compile with `latexmk -xelatex` (add `biber` if you use biblatex).

Full documentation (in Russian), the `guap` command-line tool that creates
and builds reports, and VS Code settings with snippets are in the
repository: https://github.com/Echways/suai-report

## Кратко по-русски

Шаблон отчёта ГУАП по ГОСТ 7.32-2017 на XeLaTeX: титульный лист по
официальному бланку, оформление ставится само, в `main.tex` пишется только
текст. Пример — `guap-demo.tex` и `guap-demo.pdf`, заготовка —
`guap-template.tex`. Полное описание, команда `guap` и настройки VS Code —
в репозитории по ссылке выше.

## License

MIT, see `LICENSE`.

Copyright (c) 2026 Grigorii Moiseev
