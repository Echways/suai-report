# Установка

[← К оглавлению](../README.md#документация)

## Что нужно

| Что | Зачем |
| --- | --- |
| TeX Live с `xelatex`, `latexmk`, `biber` | сборка отчёта; пакет работает только с XeLaTeX |
| Python 3.10 или новее | команда `suai` |
| VS Code и расширение LaTeX Workshop | предпросмотр и подсказки; не обязательно |

Ubuntu и Debian:

```bash
sudo apt install texlive-xetex texlive-latex-extra texlive-lang-cyrillic \
                 texlive-fonts-recommended texlive-bibtex-extra biber latexmk \
                 fonts-liberation
```

macOS — [MacTeX](https://tug.org/mactex/), Windows —
[TeX Live](https://tug.org/texlive/windows.html). Вместо TeX Live в Windows
подойдёт MiKTeX, но к нему нужен [Strawberry Perl](https://strawberryperl.com):
без него не работает `latexmk`.

## Шрифты

| Где | Шрифт | Если не установлен |
| --- | --- | --- |
| текст | Times New Roman | TeX Gyre Termes |
| без засечек | Liberation Sans | TeX Gyre Heros |
| листинги и `\texttt` | Liberation Mono | TeX Gyre Cursor |

Титульный лист выверен по бланку ГУАП с Times New Roman, поэтому лучше
поставить его: в Windows и macOS он есть, в Ubuntu это пакет
`ttf-mscorefonts-installer`. Когда шрифта нет, сборка не останавливается,
а в журнале остаётся предупреждение
`Шрифт 'Times New Roman' не найден, используется 'TeX Gyre Termes'`.

## Установка шаблона

Linux и macOS:

```bash
git clone https://github.com/Echways/suai-report
cd suai-report
make install
```

Windows (PowerShell или cmd; `make` не нужен):

```bat
git clone https://github.com/Echways/suai-report
cd suai-report
py scripts\suai.py install
```

Если команды `py` нет, вместо неё пишется `python`. После установки открой
новый терминал — в нём уже есть команда `suai`.

Что делает установка:

- ставит `suai-report.sty` в личное дерево TeX — `~/texmf/tex/latex/suai-report/`
  (точное место показывает `kpsewhich -var-value TEXMFHOME`). Это симлинк на
  файл в репозитории, поэтому папку с шаблоном после установки не удаляй;
- кладёт команду `suai` в `~/.local/bin`. Если этой папки нет в `PATH`,
  установка напишет об этом;
- проверяет, что есть `xelatex`, `latexmk` и `biber`, и называет то, чего
  не нашла.

В Windows то же самое лежит в `%USERPROFILE%\texmf` и
`%USERPROFILE%\.local\bin`, папка с командой сама добавляется в `PATH`
пользователя. Симлинк там получается только в режиме разработчика, иначе
`suai-report.sty` копируется. Для MiKTeX установка сама регистрирует дерево
`texmf` и обновляет базу имён файлов.

## Обновление

```bash
cd suai-report
git pull
```

Если `suai-report.sty` установлен симлинком, обновление сразу действует
во всех отчётах. Если копией (Windows без режима разработчика) — повтори
`suai install`; устаревшую копию заодно обновляют `suai new`, `suai next`
и `suai update`.

Настройки VS Code лежат в каждом отчёте отдельно. После обновления шаблона
их освежает `suai update`, запущенная в папке отчёта.

## Удаление

```bash
suai uninstall        # или make uninstall в папке шаблона
```

Убирает `suai-report.sty` из `texmf` и команду `suai`. Отчёты и папка
с шаблоном остаются.

## Без команды `suai`

Команда `suai` — удобство, а не требование: для отчёта нужен только файл
[src/suai-report.sty](../src/suai-report.sty).

1. Положи `suai-report.sty` рядом с `main.tex`.
2. Возьми за основу [src/template.tex](../src/template.tex).
3. Собирай: `latexmk -xelatex main.tex`. Если источники оформлены через
   biblatex, `latexmk` сам запустит `biber`.

Так же шаблон работает в Overleaf: загрузи `suai-report.sty` в проект
и выбери компилятор XeLaTeX.

Дальше: [команда `suai`](cli.md) и [текст отчёта](writing.md).
