"""suai — отчёты ГУАП.

  suai install            один раз: suai-report.sty в ~/texmf, команда suai в ~/.local/bin
  suai new DIR [--title]  новый отчёт
  suai next [--title]     следующий отчёт рядом: lab-3 -> ../lab-4
  suai update             обновить .vscode в текущем отчёте
  suai build|watch|open|clean [DIR]

Работает в Linux, macOS и Windows (там ~ — это %USERPROFILE%).
"""

import argparse
import filecmp
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 10):
    sys.exit("suai: нужен Python 3.10 или новее")

WINDOWS = os.name == "nt"

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
STY = SRC / "suai-report.sty"
TEMPLATE = SRC / "template.tex"
VSCODE = SRC / "vscode"
DEMO = REPO / "docs" / "demo" / "main.tex"

REPORT_GITIGNORE = "build/\n"
LEGACY_PDF_NAME = "main.pdf"
BIN = Path.home() / ".local" / "bin" / ("suai.cmd" if WINDOWS else "suai")
CMD_FILE_ENCODING = "oem"

SETUP_RE = re.compile(r"^\\suaisetup\{.*?^\}", re.M | re.S)
TRAILING_NUM_RE = re.compile(r"(\d+)$")
UNESCAPED_DOLLAR_RE = re.compile(r"(?<!\\)\$")

TEXT_SPECIALS = "%#&_^"
MATH_SPECIALS = "%#"

HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002


def die(msg: str) -> None:
    print(f"ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def write_text_lf(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8"))


def read_setup(tex: Path) -> str | None:
    m = SETUP_RE.search(tex.read_text(encoding="utf-8"))
    return m.group(0) if m else None


def read_setup_dir(d: Path) -> str | None:
    return read_setup(d / "main.tex") if (d / "main.tex").is_file() else None


def tex_escape(text: str, chars: str) -> str:
    return re.sub(rf"(?<!\\)([{re.escape(chars)}])",
                  lambda m: r"\^{}" if m.group(1) == "^" else "\\" + m.group(1), text)


def tex_value(text: str) -> str:
    parts = UNESCAPED_DOLLAR_RE.split(text)
    dollars_are_paired = len(parts) % 2 == 1
    if dollars_are_paired:
        text = "$".join(
            tex_escape(part, MATH_SPECIALS if inside_formula else TEXT_SPECIALS)
            for part, inside_formula in zip(parts, itertools.cycle([False, True])))
    else:
        text = tex_escape(text, TEXT_SPECIALS + "$")
    would_be_read_as_key = "=" in text
    return f"{{{text}}}" if would_be_read_as_key else text


def find_setup_source(target: Path, prefer: Path | None = None) -> Path:
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


def pdf_path(d: Path) -> Path:
    d = d.resolve()
    return d / f"{d.parent.name}-{d.name}.pdf"


def is_miktex() -> bool:
    return shutil.which("initexmf") is not None


def texmf_home() -> Path:
    home = ""
    kpsewhich = shutil.which("kpsewhich")
    if kpsewhich and not is_miktex():
        try:
            home = subprocess.run([kpsewhich, "-var-value", "TEXMFHOME"],
                                  capture_output=True, text=True).stdout.strip()
        except OSError:
            pass
    return Path(home) if home else Path.home() / "texmf"


def texmf_sty() -> Path:
    return texmf_home() / "tex" / "latex" / "suai-report" / "suai-report.sty"


def miktex_refresh(register: bool) -> None:
    initexmf = shutil.which("initexmf")
    if initexmf is None:
        return
    steps = [["--update-fndb"]]
    if register:
        steps.insert(0, [f"--register-root={texmf_home()}"])
    for args in steps:
        try:
            done = subprocess.run([initexmf, *args], capture_output=True, text=True)
        except OSError as e:
            print(f"  initexmf {args[0]}: {e}")
            continue
        if done.returncode:
            print(f"  initexmf {args[0]}: {done.stderr.strip() or done.returncode}")


def link_sty(link: Path, target: Path) -> bool:
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        link.unlink()
    try:
        link.symlink_to(target)
    except OSError:
        shutil.copyfile(target, link)
        print(f"  {link} (копия)")
        return False
    print(f"  {link} -> {target}")
    return True


def refresh_sty() -> str:
    installed = texmf_sty()
    if not installed.exists():
        return "missing"
    is_current = installed.is_symlink() or filecmp.cmp(STY, installed, shallow=False)
    if is_current:
        return "ok"
    shutil.copyfile(STY, installed)
    return "updated"


def launcher() -> bytes:
    script = Path(__file__).resolve()
    if not WINDOWS:
        return f'#!/bin/sh\nexec python3 "{script}" "$@"\n'.encode()
    text = f'@"{sys.executable}" "{script}" %*\r\n'
    try:
        return text.encode(CMD_FILE_ENCODING)
    except (UnicodeEncodeError, LookupError):
        return ("@chcp 65001 >nul\r\n" + text).encode("utf-8")


def in_path(d: Path, path: str, sep: str = os.pathsep) -> bool:
    def norm(p: str) -> str:
        return os.path.normcase(os.path.normpath(os.path.expandvars(p.strip('"'))))
    return norm(str(d)) in (norm(p) for p in path.split(sep) if p)


def add_to_user_path(d: Path) -> bool:
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value, kind = "", winreg.REG_EXPAND_SZ
        if in_path(d, value, ";"):
            return False
        value = f"{value.rstrip(';')};{d}" if value.strip(";") else str(d)
        winreg.SetValueEx(key, "Path", 0, kind, value)
    notify_running_programs_of_new_environment()
    return True


def notify_running_programs_of_new_environment() -> None:
    import ctypes
    try:
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            SMTO_ABORTIFHUNG, 5000, None)
    except (AttributeError, OSError):
        pass


def path_hint(d: Path) -> str:
    if WINDOWS:
        try:
            if add_to_user_path(d):
                return f"{d} добавлена в PATH — открой новый терминал"
            return "открой новый терминал, чтобы заработала команда suai"
        except OSError:
            pass
    return f"добавь {d} в PATH"


def missing_tools() -> list[str]:
    tools = ["xelatex", "latexmk", "biber"]
    if is_miktex():
        tools.append("perl")
    return [t for t in tools if shutil.which(t) is None]


def open_editor(target: Path) -> None:
    code = shutil.which("code")
    if code is None:
        print("  VS Code (code) не найден — открой папку сам")
        return
    subprocess.Popen([code, str(target), str(target / "main.tex")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_file(path: Path) -> None:
    if WINDOWS:
        os.startfile(path)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def is_template_dir(path: Path) -> bool:
    return path.resolve() in (REPO, DEMO.parent, SRC)


def report_dir(path: Path | None) -> Path:
    d = path or Path.cwd()
    if not (d / "main.tex").exists():
        die(f"в {d} нет main.tex")
    return d


def cmd_install() -> None:
    linked = link_sty(texmf_sty(), STY)
    miktex_refresh(register=True)
    BIN.parent.mkdir(parents=True, exist_ok=True)
    BIN.unlink(missing_ok=True)
    BIN.write_bytes(launcher())
    BIN.chmod(0o755)
    print(f"  {BIN}")
    if not in_path(BIN.parent, os.environ.get("PATH", "")):
        print(f"  {path_hint(BIN.parent)}")
    if not linked:
        print("  после git pull повтори install: suai-report.sty установлен копией")
    missing = missing_tools()
    if missing:
        print(f"  не найдено: {', '.join(missing)} — без них отчёт не соберётся")
    print("Готово")


def cmd_uninstall() -> None:
    for path in (texmf_sty(), BIN):
        if path.is_symlink() or path.exists():
            path.unlink()
            print(f"  удалено {path}")
    miktex_refresh(register=False)


def cmd_new(target: Path, title: str | None, no_open: bool,
            prefer: Path | None = None) -> None:
    if (target / "main.tex").exists():
        die(f"{target / 'main.tex'} уже существует")
    if is_template_dir(target):
        die("нельзя создавать отчёт внутри шаблона")

    main, source = render_main(target, title, prefer)
    (target / "images").mkdir(parents=True, exist_ok=True)
    install_kit(target)
    write_text_lf(target / "main.tex", main)
    gitignore = target / ".gitignore"
    if not gitignore.exists():
        write_text_lf(gitignore, REPORT_GITIGNORE)

    print(f"Готово: {target}")
    print(f"  титул взят из {source}")
    if not title:
        print("  заполни title в main.tex")
    report_sty_state()
    if not no_open:
        open_editor(target)


def report_sty_state() -> None:
    state = refresh_sty()
    if state == "missing":
        print(f"  suai-report.sty не установлен: выполни python {Path(__file__).resolve()} install")
    elif state == "updated":
        print("  suai-report.sty обновлён")


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
    report_sty_state()


def texinputs() -> str:
    report_dir_first = [".", str(SRC), ""]
    return os.pathsep.join(report_dir_first)


def run_latexmk(d: Path, *extra: str) -> None:
    env = dict(os.environ, TEXINPUTS=texinputs())
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        die("не найден latexmk — нужен TeX Live или MiKTeX")
    try:
        subprocess.run([latexmk, *latexmk_args(), *extra, "main.tex"],
                       cwd=d, env=env, check=True)
    except OSError as e:
        die(f"latexmk не запускается: {e}")
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
    "build":     "собрать PDF (Предмет/lab-3 -> Предмет-lab-3.pdf)",
    "watch":     "пересобирать при каждом сохранении",
    "open":      "собрать и открыть PDF",
    "clean":     "удалить build/ и PDF",
}


def cmd_watch(d: Path) -> None:
    run_latexmk(d, "-pvc", "-view=none")


def cmd_open(d: Path) -> None:
    run_latexmk(d)
    open_file(pdf_path(d))


def cmd_clean(d: Path) -> None:
    shutil.rmtree(d / "build", ignore_errors=True)
    pdf_path(d).unlink(missing_ok=True)
    (d / LEGACY_PDF_NAME).unlink(missing_ok=True)


def survive_output_encoding_without_cyrillic() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


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
    survive_output_encoding_without_cyrillic()
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
