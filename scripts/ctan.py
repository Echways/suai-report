"""Выпуск suai на CTAN.

  ctan.py version              версия из \\ProvidesPackage в src/suai-report.sty
  ctan.py check-tag TAG        тег совпадает с версией, в CHANGELOG есть раздел
  ctan.py notes [--announce]   текст раздела текущей версии из CHANGELOG
  ctan.py package              dist/suai-report.zip (нужен собранный demo/main.pdf)
  ctan.py validate|upload      отправить dist/suai-report.zip в API CTAN (email в CTAN_EMAIL)
  ctan.py published            yes, если эта версия уже на CTAN
  ctan.py form                 поля для ручной загрузки через форму на ctan.org
  ctan.py release VERSION      поднять версию в suai-report.sty и CHANGELOG

Метаданные пакета лежат в ctan/ctan.json. API: https://ctan.org/help/submit
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STY = REPO / "src" / "suai-report.sty"
CHANGELOG = REPO / "CHANGELOG.md"
META = REPO / "ctan" / "ctan.json"
DIST = REPO / "dist"
ZIP = DIST / "suai-report.zip"

API = "https://ctan.org/submit"
PKG_JSON = "https://ctan.org/json/2.0/pkg/suai-report"
ANNOUNCE = "<!-- announce -->"

PROVIDES_RE = re.compile(r"(\\ProvidesPackage\{suai-report\}\[)(\d{4}/\d{2}/\d{2}) v([\d.]+)( )")
VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")
# тире в заголовке — любое: обычный дефис в «## 2.1 - 2026-09-15» раньше
# прятал весь раздел от check-tag, notes и архива для CTAN
SECTION_RE = re.compile(r"^## (\S+)(?:\s*[-–—]\s*(\d{4}-\d{2}-\d{2}))?\s*$", re.M)

FILES = {
    "README.md": "ctan/README.md",
    "LICENSE": "LICENSE",
    "suai-report.sty": "src/suai-report.sty",
    "suai-report-template.tex": "src/template.tex",
    "suai-report-demo.tex": "demo/main.tex",
    "suai-report-demo.pdf": "demo/main.pdf",
}
FIELD_LIMITS = {"summary": 128, "description": 4096, "announcement": 8192}


def die(msg: str) -> None:
    print(f"ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def sty_version(text: str | None = None) -> tuple[str, str]:
    m = PROVIDES_RE.search(text if text is not None else STY.read_text(encoding="utf-8"))
    if not m:
        die(f"в {STY.name} не найден \\ProvidesPackage{{suai-report}}[ГГГГ/ММ/ДД vX.Y ...]")
    return m.group(3), m.group(2).replace("/", "-")


def sections(text: str) -> list[tuple[str, str | None, str]]:
    found = list(SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(found):
        end = found[i + 1].start() if i + 1 < len(found) else len(text)
        out.append((m.group(1), m.group(2), text[m.end():end].strip()))
    return out


def section(text: str, version: str) -> tuple[str | None, str] | None:
    return next(((d, body) for v, d, body in sections(text) if v == version), None)


def notes(text: str, version: str, announce_only: bool = False) -> str:
    found = section(text, version)
    if found is None:
        return ""
    body = found[1]
    if announce_only and ANNOUNCE not in body:
        return ""
    return body.replace(ANNOUNCE, "").strip()


def check_tag(tag: str, sty_text: str, changelog: str) -> list[str]:
    version, date = sty_version(sty_text)
    errors = []
    if tag != f"v{version}":
        errors.append(f"тег {tag} не совпадает с версией v{version} в suai-report.sty")
    found = section(changelog, version)
    if found is None:
        errors.append(f"в CHANGELOG.md нет раздела «## {version} — {date}»")
    elif found[0] != date:
        errors.append(f"дата раздела {version} в CHANGELOG.md ({found[0]}) "
                      f"не совпадает с датой в suai-report.sty ({date})")
    elif not notes(changelog, version):
        errors.append(f"раздел {version} в CHANGELOG.md пустой")
    return errors


def changelog_for_archive(text: str) -> str:
    parts = ["# Changelog"]
    for version, date, body in sections(text):
        if version == "Unreleased":
            continue
        body = body.replace(ANNOUNCE, "").strip()
        parts.append(f"## {version} — {date}\n\n{body}" if date else f"## {version}\n\n{body}")
    return "\n\n".join(parts) + "\n"


def archive_entries(repo: Path = REPO) -> dict[str, bytes]:
    entries = {}
    for name, src in FILES.items():
        path = repo / src
        if not path.is_file():
            hint = " (собери демо: make pdf)" if src.endswith(".pdf") else ""
            die(f"нет файла {src}{hint}")
        entries[name] = path.read_bytes()
    for img in sorted((repo / "demo" / "images").iterdir()):
        if img.is_file() and not img.name.startswith("."):
            entries[f"images/{img.name}"] = img.read_bytes()
    entries["CHANGELOG.md"] = changelog_for_archive(
        (repo / "CHANGELOG.md").read_text(encoding="utf-8")).encode()
    return entries


def forbidden(name: str) -> str | None:
    parts = name.split("/")
    if any(p.startswith(".") for p in parts):
        return "скрытый файл"
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in parts[:-1]):
        return "недопустимое имя папки"
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", parts[-1]):
        return "недопустимое имя файла"
    if re.search(r"\.(aux|log|toc|out|bbl|blg|bcf|fls|fdb_latexmk|synctex(\.gz)?|xdv|run\.xml)$", name):
        return "служебный файл сборки"
    if name.endswith(".pdf") and name != "suai-report-demo.pdf":
        return "лишний PDF"
    return None


def build_zip(entries: dict[str, bytes], dest: Path, pkg: str = "suai-report") -> None:
    bad = [f"{n}: {r}" for n in entries if (r := forbidden(n))]
    if bad:
        die("CTAN не примет архив:\n  " + "\n  ".join(bad))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(entries):
            info = zipfile.ZipInfo(f"{pkg}/{name}", date_time=(2000, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, entries[name])


def load_meta() -> dict:
    return json.loads(META.read_text(encoding="utf-8"))


def fields(meta: dict, version: str, email: str, announcement: str) -> list[tuple[str, str]]:
    out = [(k, v) for k, v in meta.items() if not isinstance(v, list)]
    out += [(k, item) for k, v in meta.items() if isinstance(v, list) for item in v]
    out += [("version", version), ("email", email), ("update", "true")]
    if announcement:
        out.append(("announcement", announcement))
    for key, value in out:
        if key in FIELD_LIMITS and len(value) > FIELD_LIMITS[key]:
            die(f"поле {key} длиннее {FIELD_LIMITS[key]} символов ({len(value)})")
    return out


def multipart(form: list[tuple[str, str]], file_name: str, data: bytes) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    body = bytearray()
    for key, value in form:
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n"
                 f"{value}\r\n").encode()
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"{file_name}\"\r\nContent-Type: application/zip\r\n\r\n").encode()
    body += data + f"\r\n--{boundary}--\r\n".encode()
    return bytes(body), f"multipart/form-data; boundary={boundary}"


def parse_response(status: int, raw: bytes) -> tuple[bool, list[str]]:
    try:
        items = json.loads(raw.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return False, [f"HTTP {status}: {raw[:500].decode('utf-8', 'replace')}"]
    if not isinstance(items, list):
        items = [items]
    lines = [" ".join(str(x) for x in item) if isinstance(item, list) else str(item)
             for item in items]
    has_error = any(isinstance(i, list) and i and i[0] == "ERROR" for i in items)
    return status == 200 and not has_error, lines


def fetch(req: urllib.request.Request, attempts: int) -> tuple[int, bytes]:
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == attempts:
                die(f"нет связи с {req.full_url}: {getattr(e, 'reason', e)}")
            time.sleep(10 * attempt)
    raise AssertionError


def submit(action: str) -> None:
    email = os.environ.get("CTAN_EMAIL", "").strip()
    if not email:
        die("не задан CTAN_EMAIL (email сопровождающего пакета на CTAN)")
    if not ZIP.is_file():
        die(f"нет {ZIP.relative_to(REPO)}: сначала make ctan")
    version, _ = sty_version()
    changelog = CHANGELOG.read_text(encoding="utf-8")
    form = fields(load_meta(), version, email, notes(changelog, version, announce_only=True))
    body, ctype = multipart(form, ZIP.name, ZIP.read_bytes())
    req = urllib.request.Request(f"{API}/{action}", data=body, method="POST",
                                 headers={"Content-Type": ctype})
    # upload не повторяется: при оборванном ответе пакет мог уже уйти на CTAN
    status, raw = fetch(req, attempts=3 if action == "validate" else 1)
    ok, lines = parse_response(status, raw)
    print(f"CTAN {action} suai {version}: HTTP {status}")
    for line in lines:
        print(f"  {line}")
    if not ok:
        sys.exit(1)


def cmd_published() -> None:
    version, _ = sty_version()
    status, raw = fetch(urllib.request.Request(PKG_JSON), attempts=3)
    if status == 404:
        print("no")
        return
    if status != 200:
        die(f"CTAN вернул HTTP {status} на {PKG_JSON}")
    data = json.loads(raw)
    current = (data.get("version") or {}).get("number", "")
    print("yes" if current.strip().lstrip("v") == version else "no")


def cmd_form() -> None:
    meta = load_meta()
    version, _ = sty_version()
    rows = [("Name", meta["pkg"]), ("Version", version), ("Author", meta["author"]),
            ("Uploader", meta["uploader"]), ("Email", "(твой email)"),
            ("Home page", meta["home"]), ("Bug tracker", meta["bugtracker"]),
            ("Repository", meta["repository"]), ("License", meta["license"]),
            ("Suggested CTAN path", meta["ctanPath"]), ("Topics", ", ".join(meta["topic"])),
            ("Summary", meta["summary"]), ("Description", meta["description"]),
            ("Announcement", notes(CHANGELOG.read_text(encoding="utf-8"), version, True)),
            ("File", str(ZIP.relative_to(REPO)))]
    for key, value in rows:
        print(f"── {key}\n{value}\n")


def bump(sty_text: str, changelog: str, version: str, date: datetime.date) -> tuple[str, str]:
    if not VERSION_RE.match(version):
        die(f"версия «{version}» должна быть вида 2.1 или 2.1.3")
    current, _ = sty_version(sty_text)
    def key(v: str) -> tuple[int, ...]:
        return tuple(map(int, (v.split(".") + ["0"])[:3]))

    if key(version) <= key(current):
        die(f"версия {version} не больше текущей {current}")
    unreleased = section(changelog, "Unreleased")
    if unreleased is None or not unreleased[1]:
        die("в CHANGELOG.md пустой раздел «## Unreleased»: опиши изменения")
    new_sty = PROVIDES_RE.sub(
        lambda m: f"{m.group(1)}{date:%Y/%m/%d} v{version}{m.group(4)}", sty_text, count=1)
    new_changelog = re.sub(r"^## Unreleased[ \t]*$", f"## Unreleased\n\n## {version} — {date:%Y-%m-%d}",
                           changelog, count=1, flags=re.M)
    return new_sty, new_changelog


def cmd_release(version: str) -> None:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                           capture_output=True, text=True, check=True).stdout
    if dirty.strip():
        die("есть незакоммиченные изменения")
    new_sty, new_changelog = bump(STY.read_text(encoding="utf-8"),
                                  CHANGELOG.read_text(encoding="utf-8"),
                                  version, datetime.date.today())
    STY.write_text(new_sty, encoding="utf-8")
    CHANGELOG.write_text(new_changelog, encoding="utf-8")
    print(f"suai-report.sty и CHANGELOG.md: версия {version}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("version", "package", "validate", "upload", "published", "form"):
        sub.add_parser(name)
    sub.add_parser("check-tag").add_argument("tag")
    sub.add_parser("notes").add_argument("--announce", action="store_true")
    sub.add_parser("release").add_argument("version")
    args = parser.parse_args()

    if args.cmd == "version":
        print(sty_version()[0])
    elif args.cmd == "check-tag":
        errors = check_tag(args.tag, STY.read_text(encoding="utf-8"),
                           CHANGELOG.read_text(encoding="utf-8"))
        for e in errors:
            print(f"ошибка: {e}", file=sys.stderr)
        if errors:
            sys.exit(1)
        print(f"{args.tag}: версия и CHANGELOG в порядке")
    elif args.cmd == "notes":
        print(notes(CHANGELOG.read_text(encoding="utf-8"), sty_version()[0], args.announce))
    elif args.cmd == "package":
        build_zip(archive_entries(), ZIP)
        print(f"Готово: {ZIP.relative_to(REPO)}")
    elif args.cmd in ("validate", "upload"):
        submit(args.cmd)
    elif args.cmd == "published":
        cmd_published()
    elif args.cmd == "form":
        cmd_form()
    elif args.cmd == "release":
        cmd_release(args.version)


if __name__ == "__main__":
    main()
