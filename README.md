# suai-report

Шаблон отчёта ГУАП по ГОСТ 7.32-2017 на XeLaTeX. Титульный лист совпадает
с официальным бланком, остальное оформление ставится само — в `main.tex`
пишется только текст.

Пример готового отчёта: [demo/main.tex](demo/main.tex).

## Установка

Нужны TeX Live (`xelatex`, `latexmk`, `biber`), Python 3 и VS Code
с расширением LaTeX Workshop.

```bash
git clone https://github.com/Echways/suai-report
cd suai-report
make install
```

`suai-report.sty` ставится в `~/texmf` симлинком, команда `suai` —
в `~/.local/bin`. После `git pull` обновления сразу действуют во всех отчётах.

## Новый отчёт

```bash
suai new ../lab-1 --title "Название работы"
```

Откроется VS Code. В `main.tex` нажми **Ctrl+Alt+V** — справа появится PDF,
который пересобирается при каждом сохранении.

Данные титула берутся из соседнего отчёта, номер работы — из имени папки
(`lab-4` → 4). Следующую лабу удобно делать из папки текущей:

```bash
suai next            # lab-4 -> ../lab-5 с тем же титулом
```

Остальные команды: `suai build`, `suai watch`, `suai open`, `suai clean`,
`suai update` (обновить настройки VS Code в отчёте).

## Титульный лист

```latex
\suaisetup{
  department   = 41,
  teacher-post = Ассистент,
  teacher      = И. И. Иванов,
  type         = Отчет о лабораторной работе,
  number       = 1,
  title        = Название работы,
  course       = Название дисциплины,
  group        = 4414,
  student      = И. И. Студентов,
  date         = today,
}
```

- Пустой `number` — без номера (курсовая, доклад).
- Без `date` остаются пустые линии, чтобы вписать дату от руки.
- Несколько студентов: `student = {А. А. Иванов, Б. Б. Петров}`.
- Ещё есть `course-label` (по умолчанию «по курсу:») и `year`.

## Текст отчёта

Главное правило: **блочная команда читает строки под собой до пустой
строки**. Каждая строка становится пунктом списка, строкой таблицы или
пояснением к формуле.

```latex
\suaiintro

Цель работы — изучить Obsidian.

\suaitasks
установить Obsidian
настроить синхронизацию

\section{Ход работы}

Окно программы показано на~\figref{scheme}.

\suaiimg{scheme}{Главное окно Obsidian}

\suaitable[sync]{Способы синхронизации}
Способ        | Стоимость | Шифрование
Obsidian Sync | 4 \$      | да
Яндекс Диск   | бесплатно | нет

\suaieq[size]{V = N \cdot \bar{s}}
V | объём хранилища, КБ
N | число заметок

\begin{code}[bash, backup]{Резервное копирование}
tar -czf vault.tar.gz ~/Vault
\end{code}

\suaiconclusion

Работа выполнена.

\suaisources
Obsidian Help. URL: https://help.obsidian.md (дата обращения: 12.09.2026).
```

| Команда | Что делает |
| --- | --- |
| `\suaitoc` | содержание |
| `\suaiintro`, `\suaiconclusion` | введение, заключение |
| `\suaisection{Название}` | другой структурный элемент без номера |
| `\suaitasks` | «Для достижения цели…» и задачи а), б), в) |
| `\suaienum` / `\suailist` / `\suainum` | список а) б) / через дефис / 1) 2) |
| `\suaitable[метка]{Название}` | таблица: ячейки через `\|`, первая строка — шапка |
| `\suaiimg[ширина]{файл}{Подпись}` | рисунок из `images/` |
| `\suaieq[метка]{формула}` | формула, строки `обозначение \| смысл` дают «где …» |
| `\begin{code}[язык, метка]{Подпись}` | листинг в тексте |
| `\suaicode[язык]{файл}{Подпись}` | листинг из файла (ищется и в `code/`) |
| `\suaisources` | список источников, по одному на строку |
| `\suaiapp[справочное]{Название}` | приложение А, Б, … |
| `\figref`, `\tabref`, `\lstref`, `\formref` | «рисунке 1», «таблице 1», «листинге 1», «формуле (1)» |

Пунктуация в списках (`;` и `.` в конце) расставляется сама, со звёздочкой
(`\suailist*`) — не трогается. Префикс метки писать не нужно:
`\figref{scheme}` найдёт `fig:scheme`.

В VS Code для всех команд есть сниппеты: набери `\suaita` (или `tab`, `img`,
`eq`, `lst`) и нажми **Tab**.

## Настройка под методичку

Пишется в преамбуле `main.tex`:

| Что | Строка |
| --- | --- |
| Правое поле 10 мм | `\geometry{right=10mm}` |
| Интервал как «1,5» в Word | `\setstretch{1.25}` |
| Формулы по разделам (1.1) | `\numberwithin{equation}{section}` |
| Заголовки без полужирного | `\renewcommand{\suaiheadfont}{\normalfont\fontsize{14}{17}\selectfont}` |
| Цветные листинги | `\lstset{style=gostcolor}` |

Для ссылок `\cite{…}` через biblatex:

```latex
\usepackage[backend=biber,style=gost-numeric,language=auto,
            autolang=other,sorting=none]{biblatex}
\addbibresource{sources.bib}
```

и `\suaisources` без строк под ним.

## Лицензия

MIT
