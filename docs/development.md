# Разработка

[← К оглавлению](../README.md#документация)

Страница для тех, кто правит сам шаблон.

## Устройство репозитория

```text
src/
├── suai-report.sty      пакет: всё оформление отчёта
├── template.tex         заготовка, из которой suai new делает main.tex
└── vscode/              настройки, подсказки и сниппеты; копируются в .vscode/ отчёта
scripts/
├── suai.py              команда suai
├── ctan.py              версия, архив для CTAN, текст релиза
└── ctan.json, ctan-readme.md   метаданные и README для CTAN
tests/                   тесты команды, пакета, архива и документации
docs/                    документация
└── demo/
    ├── main.tex         демо-отчёт: все команды шаблона
    └── images/, code/   его рисунки и исходный код
```

Всё, что попадает в отчёты, лежит в `src/`. `suai-report.sty` установлен
симлинком, поэтому правка в `src/` сразу действует во всех отчётах на этой
машине.

`suai-report.sty` разбит на пронумерованные разделы: пакеты, шрифты,
страница, заголовки, подписи и таблицы, листинги, приложения, титульный
лист, ссылки и рисунки, чтение строк блочных команд, перечисления, таблица,
формула, источники, `\suaicode`. Пункт ГОСТа, на который опирается
настройка, записан в комментарии рядом с ней.

## Команды `make`

| Команда | Что делает |
| --- | --- |
| `make` | собрать демо-отчёт |
| `make watch` | пересобирать демо при сохранении, в том числе `src/suai-report.sty` |
| `make open` | собрать и открыть демо |
| `make test` | тесты |
| `make check` | тесты, демо и свежая заготовка — то же, что делает CI |
| `make clean` | удалить сборку демо |
| `make new DIR=../lab-2` | новый отчёт; `TITLE="…"` — сразу с названием |
| `make install`, `make uninstall` | то же, что `suai install` и `suai uninstall` |
| `make ctan` | архив для CTAN: `dist/suai-report.zip` |
| `make release VERSION=2.8` | новая версия — см. [выпуск версии](#выпуск-версии) |

Демо собирается этими командами, а не кнопкой сборки в VS Code: в папке
шаблона нет `.vscode/` с рецептом, и LaTeX Workshop запустит `pdflatex`,
с которым пакет не работает.

В Windows вместо `make` команды вызываются напрямую:
`py scripts\suai.py build docs\demo`, `py -m unittest discover -s tests`.

## Тесты

```bash
make test
```

| Файл | Что проверяет |
| --- | --- |
| `tests/test_suai.py` | команду `suai`: создание отчёта, титул, пути, установку |
| `tests/test_sty.py` | сам пакет: собирает маленькие документы XeLaTeX и смотрит журнал. Без `xelatex` пропускается |
| `tests/test_ctan.py` | версию, CHANGELOG и состав архива для CTAN |
| `tests/test_docs.py` | документацию: каждая команда `\suai…`, ключ `\suaisetup`, подкоманда `suai` и язык листингов описаны, демо использует все команды, ссылки между страницами целы |

GitHub Actions на каждый push гоняет тесты в Linux и Windows, а затем
в контейнере TeX Live собирает демо и заготовку.

## Правка пакета

Главное требование к правкам `suai-report.sty` — отчёт должен остаться
оформленным по ГОСТ 7.32-2017.

- Изменение, которое меняет вид уже набираемого отчёта, лучше делать
  переключателем, а не новым умолчанием.
- После правки сравни демо до и после: собери его на обеих версиях
  и сравни вывод `pdftotext -bbox-layout docs/demo/build/main.pdf`.
- Новое поведение закрепляется тестом в `tests/test_sty.py`.

Новая команда или ключ — это четыре места:

1. `src/suai-report.sty` — сама команда;
2. `src/vscode/suai-report.json` — подсказка в VS Code, при необходимости
   сниппет в `src/vscode/suai.code-snippets`;
3. `docs/` — описание с примером и строка в таблице команд `README.md`;
4. `docs/demo/main.tex` — пример использования.

Про пункты 3 и 4 напомнит `tests/test_docs.py`.

## Картинки в документации

Страницы демо в `docs/images/` получены из собранного PDF командами
`pdftoppm` (poppler) и `convert` (ImageMagick), вторая рисует рамку:

```bash
make
pdftoppm -png -r 80 -f 1 -l 1 -singlefile docs/demo/build/main.pdf docs/images/title
pdftoppm -png -r 80 -f 5 -l 5 -singlefile docs/demo/build/main.pdf docs/images/text
pdftoppm -png -r 80 -f 12 -l 12 -singlefile docs/demo/build/main.pdf docs/images/listing
for n in title text listing; do
  convert docs/images/$n.png -bordercolor '#c8c8c8' -border 1 docs/images/$n.png
done
```

После заметной правки демо или оформления их стоит обновить; номера
страниц при этом могут сдвинуться.

## Выпуск версии

Изменения записываются в [CHANGELOG.md](../CHANGELOG.md) под заголовком
`## Unreleased`, по-английски: текст раздела уходит в GitHub Release,
а с пометкой `<!-- announce -->` — ещё и в объявление для CTAN.

```bash
make release VERSION=2.8
git push --follow-tags
```

`make release` ставит версию и дату в `\ProvidesPackage` и в CHANGELOG,
делает коммит и тег `v2.8`. Рабочая копия должна быть чистой, а раздел
`Unreleased` — непустым.

После отправки тега GitHub Actions прогоняет проверки, собирает
`dist/suai-report.zip` и создаёт GitHub Release с архивом, демо-PDF
и текстом раздела из CHANGELOG. На CTAN архив загружается вручную: поля
формы печатает `python3 scripts/ctan.py form`.

В архив для CTAN входят `suai-report.sty`, заготовка, демо с PDF, его
рисунками и кодом, [scripts/ctan-readme.md](../scripts/ctan-readme.md), лицензия и CHANGELOG
без раздела `Unreleased`.
