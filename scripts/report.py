import argparse
import filecmp
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = REPO / "template" / "main.tex"
DEMO = REPO / "demo" / "main.tex"

KIT = {
    "guap.sty": "template/guap.sty",
    ".latexmkrc": "template/.latexmkrc",
    "Makefile": "template/Makefile",
    ".vscode/settings.json": ".vscode/settings.json",
    ".vscode/guap.code-snippets": ".vscode/guap.code-snippets",
    ".vscode/extensions.json": ".vscode/extensions.json",
}
REPORT_GITIGNORE = "build/\n*.zip\n"

SETUP_RE = re.compile(r"^\\guapsetup\{.*?^\}", re.M | re.S)
TRAILING_NUM_RE = re.compile(r"(\d+)$")


def die(msg: str) -> None:
    print(f"ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def read_setup(tex: Path) -> str | None:
    m = SETUP_RE.search(tex.read_text(encoding="utf-8"))
    return m.group(0) if m else None


def find_setup_source(target: Path) -> Path:
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


def render_main(target: Path, title: str | None) -> tuple[str, Path]:
    source = find_setup_source(target)
    setup = read_setup(source)
    if setup is None:
        die(f"в {source} нет блока \\guapsetup")

    num = TRAILING_NUM_RE.search(target.name)
    setup = set_key(setup, "number", str(int(num.group(1))) if num else "")
    setup = set_key(setup, "title", title or "Название работы")
    setup = set_key(setup, "date", "today")

    skeleton = TEMPLATE.read_text(encoding="utf-8")
    return SETUP_RE.sub(lambda _: setup, skeleton, count=1), source


def install_kit(dest: Path) -> list[str]:
    changed = []
    for rel, src_rel in KIT.items():
        src, dst = REPO / src_rel, dest / rel
        if not src.exists():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel == "Makefile":
            dest_abs = dest.resolve()
            shared = os.path.commonpath([REPO, dest_abs]) != os.sep
            guap = os.path.relpath(REPO, dest_abs) if shared else str(REPO)
            text = re.sub(r"^GUAP\s*:=.*$", f"GUAP := {guap}",
                          src.read_text(encoding="utf-8"), count=1, flags=re.M)
            if dst.exists() and dst.read_text(encoding="utf-8") == text:
                continue
            dst.write_text(text, encoding="utf-8")
        else:
            if dst.exists() and filecmp.cmp(src, dst, shallow=False):
                continue
            shutil.copy2(src, dst)
        changed.append(rel)
    return changed


def open_editor(target: Path) -> None:
    if shutil.which("code"):
        subprocess.Popen(["code", str(target), str(target / "main.tex")],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_template_dir(path: Path) -> bool:
    return path.resolve() in (REPO, DEMO.parent, TEMPLATE.parent)


def cmd_new(target: Path, title: str | None, no_open: bool) -> None:
    if (target / "main.tex").exists():
        die(f"{target / 'main.tex'} уже существует")
    if is_template_dir(target):
        die("нельзя создавать отчёт внутри шаблона")

    main, source = render_main(target, title)
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
    if not no_open:
        open_editor(target)


def cmd_next(title: str | None, no_open: bool) -> None:
    cwd = Path.cwd()
    m = TRAILING_NUM_RE.search(cwd.name)
    if not m:
        die(f"имя папки «{cwd.name}» не заканчивается номером (нужно вроде lab-3)")
    digits = m.group(1)
    name = cwd.name[: m.start()] + str(int(digits) + 1).zfill(len(digits))
    cmd_new(cwd.parent / name, title, no_open)


def cmd_update() -> None:
    cwd = Path.cwd()
    if is_template_dir(cwd):
        die("это сам шаблон; update запускается в папке отчёта")
    if not (cwd / "main.tex").exists():
        die("в текущей папке нет main.tex")
    changed = install_kit(cwd)
    print("Обновлено: " + ", ".join(changed) if changed else "Всё актуально")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("new", "next"):
        p = sub.add_parser(name)
        if name == "new":
            p.add_argument("dir", type=Path)
        p.add_argument("--title")
        p.add_argument("--no-open", action="store_true", help="не открывать VS Code")
    sub.add_parser("update")
    args = parser.parse_args()

    if args.cmd == "new":
        cmd_new(args.dir, args.title, args.no_open)
    elif args.cmd == "next":
        cmd_next(args.title, args.no_open)
    else:
        cmd_update()


if __name__ == "__main__":
    main()
