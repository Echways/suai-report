# Демо собирается с настройками и guap.sty прямо из template/.
# Текущая папка идёт первой, иначе найдётся template/main.tex.
do '../template/.latexmkrc';
ensure_path('TEXINPUTS', '../template//', '.');
