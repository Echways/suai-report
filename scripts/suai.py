"""suai — отчёты ГУАП.

  suai install            один раз: suai-report.sty в ~/texmf, команда suai в ~/.local/bin
  suai new DIR [--title]  новый отчёт
  suai next [--title]     следующий отчёт рядом: lab-3 -> ../lab-4
  suai update             обновить .vscode в текущем отчёте
  suai build|watch|open|clean [DIR]

Всё, что попадает в отчёты, лежит в src/: suai-report.sty, template.tex, vscode/.
"""

import argparse
import filecmp
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
STY = SRC / "suai-report.sty"
TEMPLATE = SRC / "template.tex"
VSCODE = SRC / "vscode"  # копируется в .vscode/ отчёта
DEMO = REPO / "demo" / "main.tex"

REPORT_GITIGNORE = "build/\n"
BIN = Path.home() / ".local" / "bin" / "suai"

SETUP_RE = re.compile(r"^\\suaisetup\{.*?^\}", re.M | re.S)
TRAILING_NUM_RE = re.compile(r"(\d+)$")


def die(msg: str) -> None:
    print(f"ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def read_setup(tex: Path) -> str | None:
    m = SETUP_RE.search(tex.read_text(encoding="utf-8"))
    return m.group(0) if m else None


def read_setup_dir(d: Path) -> str | None:
    return read_setup(d / "main.tex") if (d / "main.tex").is_file() else None


def tex_value(text: str) -> str:
    """% и # в значении \\suaisetup закомментировали бы строку целиком."""
    return re.sub(r"(?<!\\)([%#])", r"\\\1", text)


def find_setup_source(target: Path, prefer: Path | None = None) -> Path:
    """Титул из prefer (для next — из текущего отчёта), иначе из самого
    свежего соседнего, иначе из демо."""
    if prefer is not None and read_setup_dir(prefer):
        return prefer / "main.tex"
    siblings = [
        p for p in target.parent.glob("*/main.tex")
        if p.parent.resolve() != target.resolve() and read_setup(p)
    ]
    if siblings:
        return max(siblings, key=lambda p: p.stat().st_mtime)
    return DEMO


def split_comment(line: str) -> tuple[str, str]:
    m = re.search(r"(?<!\\)%", line)
    return (line[: m.start()], line[m.start():]) if m else (line, "")


def set_key(block: str, key: str, value: str) -> str:
    lines = block.splitlines()
    for i, line in enumerate(lines):
        code, comment = split_comment(line)
        m = re.match(rf"^(\s*{re.escape(key)}\s*=\s*)", code)
        if not m:
            continue
        new_code = f"{m.group(1)}{value},"
        if comment:
            new_code = new_code.ljust(len(code) - 1) + " "
        lines[i] = (new_code + comment).rstrip()
        return "\n".join(lines)
    lines.insert(len(lines) - 1, f"  {key:<12} = {value},")
    return "\n".join(lines)


def render_main(target: Path, title: str | None,
                prefer: Path | None = None) -> tuple[str, Path]:
    source = find_setup_source(target, prefer)
    setup = read_setup(source)
    if setup is None:
        die(f"в {source} нет блока \\suaisetup")

    num = TRAILING_NUM_RE.search(target.name)
    setup = set_key(setup, "number", str(int(num.group(1))) if num else "")
    setup = set_key(setup, "title", tex_value(title) if title else "Название работы")
    setup = set_key(setup, "date", "today")

    skeleton = TEMPLATE.read_text(encoding="utf-8")
    return SETUP_RE.sub(lambda _: setup, skeleton, count=1), source


def install_kit(dest: Path) -> list[str]:
    changed = []
    for src in sorted(VSCODE.iterdir()):
        rel = f".vscode/{src.name}"
        dst = dest / rel
        if dst.exists() and filecmp.cmp(src, dst, shallow=False):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        changed.append(rel)
    return changed


def latexmk_args() -> list[str]:
    settings = VSCODE / "settings.json"
    text = "\n".join(l for l in settings.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("//"))
    tools = json.loads(text)["latex-workshop.latex.tools"]
    tool = next(t for t in tools if t["name"] == "suai-latexmk")
    return [a for a in tool["args"] if a != "%DOC_EXT%"]


def texmf_sty() -> Path:
    try:
        home = subprocess.run(["kpsewhich", "-var-value", "TEXMFHOME"],
                              capture_output=True, text=True).stdout.strip()
    except OSError:
        home = ""                       # TeX Live не установлен
    return Path(home or Path.home() / "texmf") / "tex" / "latex" / "suai-report" / "suai-report.sty"


def symlink(link: Path, target: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target)
    print(f"  {link} -> {target}")


def open_editor(target: Path) -> None:
    if shutil.which("code") is None:
        print("  VS Code (code) не найден — открой папку сам")
        return
    subprocess.Popen(["code", str(target), str(target / "main.tex")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_template_dir(path: Path) -> bool:
    return path.resolve() in (REPO, DEMO.parent, SRC)


def report_dir(path: Path | None) -> Path:
    d = path or Path.cwd()
    if not (d / "main.tex").exists():
        die(f"в {d} нет main.tex")
    return d


def cmd_install() -> None:
    symlink(texmf_sty(), STY)
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.unlink(missing_ok=True)
    BIN.write_text(f'#!/bin/sh\nexec python3 "{Path(__file__).resolve()}" "$@"\n')
    BIN.chmod(0o755)
    print(f"  {BIN}")
    if shutil.which("suai") is None:
        print(f"  добавь {BIN.parent} в PATH")
    print("Готово")


def cmd_uninstall() -> None:
    for path in (texmf_sty(), BIN):
        if path.is_symlink() or path.exists():
            path.unlink()
            print(f"  удалено {path}")


def cmd_new(target: Path, title: str | None, no_open: bool,
            prefer: Path | None = None) -> None:
    if (target / "main.tex").exists():
        die(f"{target / 'main.tex'} уже существует")
    if is_template_dir(target):
        die("нельзя создавать отчёт внутри шаблона")

    main, source = render_main(target, title, prefer)
    (target / "images").mkdir(parents=True, exist_ok=True)
    install_kit(target)
    (target / "main.tex").write_text(main, encoding="utf-8")
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(REPORT_GITIGNORE, encoding="utf-8")

    print(f"Готово: {target}")
    print(f"  титул взят из {source}")
    if not title:
        print("  заполни title в main.tex")
    if not texmf_sty().exists():
        print("  suai-report.sty не установлен: выполни make install в репозитории шаблона")
    if not no_open:
        open_editor(target)


def cmd_next(title: str | None, no_open: bool) -> None:
    cwd = Path.cwd()
    m = TRAILING_NUM_RE.search(cwd.name)
    if not m:
        die(f"имя папки «{cwd.name}» не заканчивается номером (нужно вроде lab-3)")
    digits = m.group(1)
    name = cwd.name[: m.start()] + str(int(digits) + 1).zfill(len(digits))
    cmd_new(cwd.parent / name, title, no_open, prefer=cwd)


def cmd_update() -> None:
    cwd = Path.cwd()
    if is_template_dir(cwd):
        die("это сам шаблон; update запускается в папке отчёта")
    report_dir(cwd)
    changed = install_kit(cwd)
    print(f"Обновлено: {', '.join(changed)}" if changed else "Всё актуально")


def run_latexmk(d: Path, *extra: str) -> None:
    # «.» первой, иначе kpathsea может найти чужой main.tex
    env = dict(os.environ, TEXINPUTS=os.pathsep.join([".", str(SRC), ""]))
    try:
        subprocess.run(["latexmk", *latexmk_args(), *extra, "main.tex"],
                       cwd=d, env=env, check=True)
    except FileNotFoundError:
        die("не найден latexmk — нужен TeX Live")
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        pass


HELP = {
    "new":       "новый отчёт в папке DIR",
    "next":      "следующий отчёт рядом: lab-3 -> ../lab-4",
    "install":   "suai-report.sty в ~/texmf, команда suai в ~/.local/bin",
    "uninstall": "убрать установленное",
    "update":    "обновить .vscode в текущем отчёте",
    "build":     "собрать main.pdf",
    "watch":     "пересобирать при каждом сохранении",
    "open":      "собрать и открыть PDF",
    "clean":     "удалить build/ и main.pdf",
}


def cmd_watch(d: Path) -> None:
    run_latexmk(d, "-pvc", "-view=none")


def cmd_open(d: Path) -> None:
    run_latexmk(d)
    subprocess.Popen(["xdg-open", str(d / "main.pdf")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def cmd_clean(d: Path) -> None:
    shutil.rmtree(d / "build", ignore_errors=True)
    (d / "main.pdf").unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True, metavar="КОМАНДА")
    for name in ("new", "next"):
        p = sub.add_parser(name, help=HELP[name])
        if name == "new":
            p.add_argument("dir", type=Path, help="папка нового отчёта")
        p.add_argument("--title", help="название работы")
        p.add_argument("--no-open", action="store_true", help="не открывать VS Code")
    for name in ("install", "uninstall", "update"):
        sub.add_parser(name, help=HELP[name])
    for name in ("build", "watch", "open", "clean"):
        sub.add_parser(name, help=HELP[name]).add_argument(
            "dir", type=Path, nargs="?", help="папка отчёта (по умолчанию текущая)")
    args = parser.parse_args()

    if args.cmd == "new":
        cmd_new(args.dir, args.title, args.no_open)
    elif args.cmd == "next":
        cmd_next(args.title, args.no_open)
    elif args.cmd == "install":
        cmd_install()
    elif args.cmd == "uninstall":
        cmd_uninstall()
    elif args.cmd == "update":
        cmd_update()
    else:
        {"build": run_latexmk, "watch": cmd_watch,
         "open": cmd_open, "clean": cmd_clean}[args.cmd](report_dir(args.dir))


if __name__ == "__main__":
    main()
