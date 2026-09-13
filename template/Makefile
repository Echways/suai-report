#  make                   собрать main.pdf
#  make watch             пересобирать при каждом сохранении (Ctrl+C — стоп)
#  make open              собрать и открыть PDF
#  make clean             удалить build/ и PDF
#  make zip               архив для Overleaf (компилятор XeLaTeX)
#  make new DIR=../lab-2  новый отчёт (TITLE="..." — сразу с названием)
#  make next              следующий отчёт рядом: lab-3 -> ../lab-4
#  make update            подтянуть свежий guap.sty и настройки из шаблона

# Путь к репозиторию шаблона; в отчётах подставляется автоматически.
GUAP := ..
REPORT = python3 $(GUAP)/scripts/report.py
TITLE_ARG = $(if $(TITLE),--title "$(TITLE)")

.PHONY: pdf watch open clean zip new next update

pdf:
	@latexmk

watch:
	@latexmk -pvc -view=none

open: pdf
	@xdg-open main.pdf >/dev/null 2>&1 &

clean:
	@rm -rf build main.pdf overleaf.zip

zip:
	@rm -f overleaf.zip
	@zip -qr overleaf.zip guap.sty main.tex $(wildcard images code *.bib)
	@echo "overleaf.zip готов (Menu → Compiler → XeLaTeX)"

new:
	@test -n "$(DIR)" || { echo "Укажи папку: make new DIR=../lab-2"; exit 1; }
	@$(REPORT) new "$(DIR)" $(TITLE_ARG)

next:
	@$(REPORT) next $(TITLE_ARG)

update:
	@$(REPORT) update
