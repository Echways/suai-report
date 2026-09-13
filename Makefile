#  make install           один раз: guap.sty в ~/texmf, команда guap в ~/.local/bin
#  make                   собрать демо-отчёт demo/main.pdf
#  make watch             пересобирать демо при сохранении, в том числе src/guap.sty
#  make open              собрать и открыть демо
#  make check             собрать демо и свежую заготовку (как CI)
#  make clean             удалить сборку демо
#  make new DIR=../lab-2  новый отчёт (TITLE="..." — сразу с названием)
#
#  Всё, что правится, лежит в src/. В отчётах Makefile нет: там команда guap.

GUAP = python3 scripts/guap.py
TITLE_ARG = $(if $(TITLE),--title "$(TITLE)")

.PHONY: pdf watch open check clean new install uninstall

pdf:
	@$(GUAP) build demo

watch:
	@$(GUAP) watch demo

open:
	@$(GUAP) open demo

check: pdf
	@tmp=$$(mktemp -d) && trap 'rm -rf "$$tmp"' EXIT && \
	  $(GUAP) new "$$tmp/lab-1" --no-open --title "Проверка" >/dev/null && \
	  $(GUAP) build "$$tmp/lab-1" && echo "check: демо и заготовка собираются"

clean:
	@$(GUAP) clean demo

new:
	@test -n "$(DIR)" || { echo "Укажи папку: make new DIR=../lab-2"; exit 1; }
	@$(GUAP) new "$(DIR)" $(TITLE_ARG)

install:
	@$(GUAP) install

uninstall:
	@$(GUAP) uninstall
