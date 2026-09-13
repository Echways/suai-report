#  make install           один раз: guap.sty в ~/texmf, команда guap в ~/.local/bin
#  make                   собрать демо-отчёт demo/main.pdf
#  make watch             пересобирать демо при сохранении, в том числе src/guap.sty
#  make open              собрать и открыть демо
#  make test              тесты команды guap (без TeX)
#  make check             тесты, демо и свежая заготовка (как CI)
#  make clean             удалить сборку демо
#  make new DIR=../lab-2  новый отчёт (TITLE="..." — сразу с названием)
#  make ctan              архив для CTAN: dist/guap.zip
#  make release VERSION=2.1  версия в guap.sty и CHANGELOG, коммит и тег v2.1
#
#  Всё, что правится, лежит в src/. В отчётах Makefile нет: там команда guap.

GUAP = python3 scripts/guap.py
TITLE_ARG = $(if $(TITLE),--title "$(TITLE)")

.PHONY: pdf watch open test check clean new install uninstall ctan release

pdf:
	@$(GUAP) build demo

watch:
	@$(GUAP) watch demo

open:
	@$(GUAP) open demo

test:
	@python3 -m unittest discover -s tests

check: test pdf
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

ctan: pdf
	@python3 scripts/ctan.py package

# Тег уходит в GitHub только после git push --follow-tags,
# дальше CTAN-загрузка ждёт подтверждения в Actions
release:
	@test -n "$(VERSION)" || { echo "Укажи версию: make release VERSION=2.1"; exit 1; }
	@python3 scripts/ctan.py release "$(VERSION)"
	@git commit -q -am "release v$(VERSION)"
	@git tag -a "v$(VERSION)" -m "guap v$(VERSION)"
	@echo "Тег v$(VERSION) создан. Отправка: git push --follow-tags"
