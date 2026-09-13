# XeLaTeX + Biber. Всё служебное (и PDF с synctex для VS Code) — в build/,
# готовый main.pdf копируется рядом с main.tex.
@default_files = ('main.tex');
$pdf_mode      = 5;          # xelatex -> xdv -> pdf
$bibtex_use    = 2;          # biber, если есть \addbibresource
$out_dir       = 'build';
$xelatex       = 'xelatex -synctex=1 -interaction=nonstopmode -file-line-error -halt-on-error %O %S';
$xdvipdfmx     = 'xdvipdfmx -E -o %D %O %S && cp %D %R.pdf';
$pdf_previewer = 'xdg-open %S';
