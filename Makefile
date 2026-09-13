#  make                   собрать демо-отчёт demo/main.pdf
#  make watch             пересобирать демо при каждом сохранении (Ctrl+C — стоп)
#  make open              собрать и открыть демо
#  make clean             удалить сборку демо
#  make new DIR=../lab-2  новый отчёт (TITLE="..." — сразу с названием)
#
#  Makefile для отчётов лежит в template/ и копируется при make new.

REPORT = python3 scripts/report.py
TITLE_ARG = $(if $(TITLE),--title "$(TITLE)")

.PHONY: pdf watch open clean new

pdf:
	@$(MAKE) -s -C demo -f ../template/Makefile pdf

watch:
	@$(MAKE) -s -C demo -f ../template/Makefile watch

open:
	@$(MAKE) -s -C demo -f ../template/Makefile open

clean:
	@$(MAKE) -s -C demo -f ../template/Makefile clean

new:
	@test -n "$(DIR)" || { echo "Укажи папку: make new DIR=../lab-2"; exit 1; }
	@$(REPORT) new "$(DIR)" $(TITLE_ARG)
