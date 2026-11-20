"""Логика без GUI: папки, обновление с GitHub, бэкапы, импорт, запуск, проверка сайтов."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = "Flowseal/zapret-discord-youtube"
REPO_URL = f"https://github.com/{REPO}"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
APP_NAME = "ZapretGUI"
try:
    from version import APP_REPO as _APP_REPO, VERSION
except Exception:
    VERSION, _APP_REPO = "0.0.0", ""
APP_ASSET = "ZapretGUI.exe"   # файл, который лежит в релизе на GitHub
MAX_APP_BACKUPS = 5
TASK_NAME = "ZapretGUI"
UA = {"User-Agent": "ZapretGUI/2.0"}
NO_WINDOW = 0x08000000  # CREATE_NO_WINDOW
MAX_BACKUPS = 3
USER_GLOB = "lists/*-user.txt"  # пользовательские списки переживают обновление
EDITABLE_LISTS = ["list-general-user.txt", "list-exclude-user.txt",
                  "ipset-exclude-user.txt", "ipset-all.txt"]

# ---------- всё лежит рядом с программой: ZapretGUI.exe, release, backup, downloads, config.json ----------
APP_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_DIR = APP_DIR
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULTS = {
    "base_dir": "",          # пусто = папка программы
    "version": "",
    "strategy": "",
    "auto_update": True,
    "autostart": False,
    "close_to_tray": True,
    "theme": "violet",      # violet | green | light | light-green | auto
    "accent": "",           # свой цвет акцента (#rrggbb) или пусто
    "font_size": "normal",  # small | normal | large
    "corners": "soft",      # soft | sharp
    "app_repo": "",
    "app_channel": "stable",   # stable | pre (пререлизы)
    "app_auto_update": False,
    "app_ignore": "",
    "resume_after_update": False,
    "profiles_enabled": [],
    "profiles_seeded": False,
    "stop_on_exit": True,
    "game_filter": False,
    "auto_start_bypass": False,
    "sites": [
        {"name": "YouTube", "url": "https://www.youtube.com"},
        {"name": "Discord", "url": "https://discord.com"},
        {"name": "Cloudflare", "url": "https://www.cloudflare.com"},
    ],
}


def _load() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return {**DEFAULTS, **data}


CFG = _load()


def save() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(CFG, ensure_ascii=False, indent=2), encoding="utf-8")


def bg(fn) -> None:
    threading.Thread(target=fn, daemon=True).start()


# ---------- папки ----------
def base_dir() -> Path:
    p = Path(CFG["base_dir"]) if CFG["base_dir"] else APP_DIR
    p.mkdir(parents=True, exist_ok=True)
    return p


def release_dir() -> Path:    # рабочая (релизная) версия
    return base_dir() / "release"


def backup_dir() -> Path:     # бэкапы старых версий
    return base_dir() / "backup"


def downloads_dir() -> Path:  # скачанные архивы
    return base_dir() / "downloads"


def profiles_dir() -> Path:   # профили: наборы доменов, по одному .txt на профиль
    p = base_dir() / "profiles"
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_base_dir(path: str) -> None:
    stop()
    CFG["base_dir"] = path
    CFG["version"] = ""
    save()


# ---------- GitHub ----------
def latest_release() -> tuple[str, str]:
    req = urllib.request.Request(API_LATEST, headers={**UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    for a in data.get("assets", []):
        if a["name"].lower().endswith(".zip"):
            return data["tag_name"], a["browser_download_url"]
    return data["tag_name"], data["zipball_url"]


def _download(url: str, dest: Path, log) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or 0)
        done, mark = 0, 25
        while chunk := r.read(64 * 1024):
            f.write(chunk)
            done += len(chunk)
            if total and done * 100 // total >= mark:
                log(f"Загрузка: {done * 100 // total}%")
                mark += 25


# ---------- установка / бэкап / импорт ----------
def is_valid_zapret(p: Path) -> bool:
    return any(p.glob("general*.bat")) or (p / "bin" / "winws.exe").exists()


def _find_root(staging: Path) -> Path:
    items = list(staging.iterdir())
    if not any(staging.glob("general*.bat")) and len(items) == 1 and items[0].is_dir():
        return items[0]
    return staging


def is_installed() -> bool:
    return release_dir().exists() and any(release_dir().glob("general*.bat"))


def _prune_backups() -> None:
    dirs = sorted((d for d in backup_dir().iterdir() if d.is_dir()),
                  key=lambda d: d.stat().st_mtime, reverse=True)
    for d in dirs[MAX_BACKUPS:]:
        shutil.rmtree(d, ignore_errors=True)


def _replace_release(staging: Path, version: str, log) -> None:
    """Старую версию -> backup/<версия>_<время>, новую -> release, списки *-user.txt переносим."""
    rel = release_dir()
    saved = {}
    if rel.exists() and not is_valid_zapret(rel):
        shutil.rmtree(rel, ignore_errors=True)  # пустая заготовка, бэкапить нечего
    if rel.exists():
        for p in rel.glob(USER_GLOB):
            saved[p.relative_to(rel)] = p.read_bytes()
        backup_dir().mkdir(parents=True, exist_ok=True)
        dest = backup_dir() / f"{CFG['version'] or 'unknown'}_{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.move(str(rel), str(dest))
        log(f"Бэкап старой версии: {dest}")
        _prune_backups()
    shutil.move(str(staging), str(rel))
    for relpath, content in saved.items():
        t = rel / relpath
        t.parent.mkdir(parents=True, exist_ok=True)
        t.write_bytes(content)
    CFG["version"] = version
    save()


def install_release(url: str, tag: str, log) -> None:
    stop()
    zip_path = downloads_dir() / f"zapret-{tag}.zip"
    log(f"Скачиваю {tag} в {downloads_dir()}")
    _download(url, zip_path, log)
    for old in downloads_dir().glob("zapret-*.zip"):  # храним только последний архив
        if old != zip_path:
            old.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(dir=base_dir()) as tmp:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(Path(tmp) / "x")
        _replace_release(_find_root(Path(tmp) / "x"), tag, log)
    log(f"Установлено: {tag}")


def import_folder(src: Path, log) -> None:
    if not is_valid_zapret(src):
        raise ValueError("В папке нет файлов general*.bat или bin\\winws.exe")
    stop()
    with tempfile.TemporaryDirectory(dir=base_dir()) as tmp:
        staging = Path(tmp) / "x"
        shutil.copytree(src, staging)
        _replace_release(staging, "своя", log)
    log(f"Импортирована папка: {src}")


def import_zip(path: Path, log) -> None:
    stop()
    with tempfile.TemporaryDirectory(dir=base_dir()) as tmp:
        with zipfile.ZipFile(path) as z:
            z.extractall(Path(tmp) / "x")
        root = _find_root(Path(tmp) / "x")
        if not is_valid_zapret(root):
            raise ValueError("В архиве нет файлов general*.bat или bin\\winws.exe")
        _replace_release(root, "своя", log)
    log(f"Импортирован архив: {path.name}")


def list_backups() -> list[str]:
    if not backup_dir().exists():
        return []
    dirs = sorted((d for d in backup_dir().iterdir() if d.is_dir()),
                  key=lambda d: d.stat().st_mtime, reverse=True)
    return [d.name for d in dirs]


def restore_backup(name: str, log) -> None:
    stop()
    with tempfile.TemporaryDirectory(dir=base_dir()) as tmp:
        staging = Path(tmp) / "x"
        shutil.move(str(backup_dir() / name), str(staging))
        _replace_release(staging, name.rsplit("_", 1)[0], log)
    log(f"Восстановлена версия из бэкапа: {name}")


# ---------- профили (наборы доменов) ----------
PRESETS = {
    "Telegram": ["telegram.org", "t.me", "telegram.me", "telegram.dog", "telesco.pe", "tg.dev",
                 "cdn-telegram.org", "telegra.ph", "graph.org", "tdesktop.com", "fragment.com"],
    "Discord": ["discord.com", "discord.gg", "discord.media", "discordapp.com", "discordapp.net",
                "discord.gift", "discord.new", "discordstatic.com", "discordcdn.com", "dis.gd"],
    "YouTube": ["youtube.com", "youtu.be", "googlevideo.com", "ytimg.com", "ggpht.com",
                "youtubei.googleapis.com", "youtube-nocookie.com"],
}
_BAD_NAME = re.compile(r'[\\/:*?"<>|]')


def safe_name(name: str) -> str:
    return _BAD_NAME.sub("", name).strip()[:40]


def seed_profiles() -> None:
    """При первом запуске кладём готовые шаблоны (выключенными): их можно править и удалять."""
    if CFG.get("profiles_seeded"):
        return
    for name, domains in PRESETS.items():
        p = profiles_dir() / f"{name}.txt"
        if not p.exists():
            p.write_text("\n".join(domains) + "\n", encoding="utf-8")
    CFG["profiles_seeded"] = True
    save()


def list_profiles() -> list[str]:
    return sorted((p.stem for p in profiles_dir().glob("*.txt")), key=str.lower)


def read_profile(name: str) -> str:
    p = profiles_dir() / f"{name}.txt"
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def write_profile(name: str, text: str) -> None:
    (profiles_dir() / f"{name}.txt").write_text(text.strip() + "\n", encoding="utf-8")


def delete_profile(name: str) -> None:
    (profiles_dir() / f"{name}.txt").unlink(missing_ok=True)
    CFG["profiles_enabled"] = [n for n in CFG["profiles_enabled"] if n != name]
    save()


def is_enabled(name: str) -> bool:
    return name in CFG["profiles_enabled"]


def set_enabled(name: str, on: bool) -> None:
    names = [n for n in CFG["profiles_enabled"] if n != name]
    CFG["profiles_enabled"] = names + [name] if on else names
    save()


def parse_domains(text: str) -> list[str]:
    """Один домен на строку; допускаются ссылки и комментарии после #. IP-адреса сюда не берём."""
    out, seen = [], set()
    for line in text.splitlines():
        s = line.split("#", 1)[0].strip().lower()
        s = re.sub(r"^[a-z][a-z0-9+.-]*://", "", s).split("/")[0].split(":")[0].lstrip("*.").strip()
        if not s or re.fullmatch(r"[\d./]+", s) or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


BLOCK_BEGIN = "# >>> profiles (блок создаёт программа, не правь между метками)"
BLOCK_END = "# <<< profiles"


def apply_profiles() -> None:
    """Дописывает домены включённых профилей в конец lists/list-general-user.txt между метками.
    Строки, которые ты добавил вручную, остаются на месте."""
    domains, seen = [], set()
    for name in CFG["profiles_enabled"]:
        for d in parse_domains(read_profile(name)):
            if d not in seen:
                seen.add(d)
                domains.append(d)
    p = list_path("list-general-user.txt", create=True)
    text = p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""
    text = re.sub(re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END) + r"\s*", "", text, flags=re.S)
    manual = [ln.rstrip() for ln in text.splitlines()
              if ln.strip() and ln.strip() != PLACEHOLDER_HOST]
    lines = manual[:]
    if domains:
        lines += [BLOCK_BEGIN, *domains, BLOCK_END]
    if not lines:
        lines = [PLACEHOLDER_HOST]  # пустой список winws понимает как «без фильтра»
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------- обновление самого приложения (GitHub Releases) ----------
def app_repo() -> str:
    return (CFG.get("app_repo") or _APP_REPO or "").strip()


def parse_ver(s: str) -> tuple:
    """1.0.10 > 1.0.9; стабильная 1.0.3 новее своего пререлиза 1.0.3-beta.2, а пререлиз новее 1.0.2."""
    s = s.strip().lstrip("vV")
    base, _, pre = s.partition("-")
    nums = ([int(x) for x in re.findall(r"\d+", base)] + [0, 0, 0])[:3]
    if not pre:
        return (*nums, 1, 0)
    digits = re.findall(r"\d+", pre)
    return (*nums, 0, int(digits[0]) if digits else 0)


def can_self_update() -> bool:
    return bool(getattr(sys, "frozen", False))  # только для собранного ZapretGUI.exe


def app_backup_dir() -> Path:
    p = base_dir() / "app_backup"
    p.mkdir(parents=True, exist_ok=True)
    return p


def app_releases() -> list[dict]:
    """Список релизов приложения с GitHub (новые сверху). Берутся только релизы с файлом ZapretGUI.exe."""
    repo = app_repo()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise ValueError("не указан репозиторий GitHub в виде «владелец/репозиторий»")
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/releases?per_page=15",
                                 headers={**UA, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    out = []
    with_pre = CFG.get("app_channel") == "pre"
    for rel in data:
        if rel.get("draft") or (rel.get("prerelease") and not with_pre):
            continue
        asset = next((a for a in rel.get("assets", []) if a["name"].lower() == APP_ASSET.lower()), None)
        if asset:
            tag = rel["tag_name"]
            out.append({"tag": tag, "version": tag.lstrip("vV"), "date": (rel.get("published_at") or "")[:10],
                        "pre": bool(rel.get("prerelease")), "url": asset["browser_download_url"]})
    out.sort(key=lambda x: parse_ver(x["version"]), reverse=True)
    return out


def list_app_backups() -> list[str]:
    """Версии приложения, сохранённые перед обновлением (кроме текущей)."""
    vers = {p.stem.removeprefix("ZapretGUI-") for p in app_backup_dir().glob("ZapretGUI-*.exe")}
    vers.discard(VERSION)
    return sorted(vers, key=parse_ver, reverse=True)


def _backup_current_app() -> None:
    shutil.copy2(sys.executable, app_backup_dir() / f"ZapretGUI-{VERSION}.exe")
    files = sorted(app_backup_dir().glob("ZapretGUI-*.exe"),
                   key=lambda p: parse_ver(p.stem.removeprefix("ZapretGUI-")), reverse=True)
    for p in files[MAX_APP_BACKUPS:]:
        p.unlink(missing_ok=True)


def _clean_app_downloads(keep: Path) -> None:
    for pat in ("ZapretGUI-*.exe", "rollback-*.exe"):
        for p in downloads_dir().glob(pat):
            if p != keep:
                p.unlink(missing_ok=True)


def prepare_app_install(rel: dict, log) -> Path:
    """Скачивает новую версию и сохраняет текущую в app_backup. Возвращает путь к скачанному exe."""
    new = downloads_dir() / f"ZapretGUI-{rel['version']}.exe"
    log(f"Скачиваю приложение {rel['tag']}…")
    _download(rel["url"], new, log)
    if new.stat().st_size < 1_000_000:
        new.unlink(missing_ok=True)
        raise ValueError("скачанный файл слишком маленький, обновление отменено")
    _backup_current_app()
    _clean_app_downloads(new)
    log(f"Версия {VERSION} сохранена в бэкап: {app_backup_dir()}")
    return new


def prepare_app_rollback(version: str, log) -> Path:
    src = app_backup_dir() / f"ZapretGUI-{version}.exe"
    if not src.exists():
        raise FileNotFoundError(f"бэкап версии {version} не найден")
    tmp = downloads_dir() / f"rollback-{version}.exe"
    downloads_dir().mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, tmp)
    _backup_current_app()  # текущую тоже сохраняем, чтобы можно было вернуться обратно
    _clean_app_downloads(tmp)
    log(f"Откат на версию {version}")
    return tmp


def launch_updater(src: Path) -> None:
    """Запускает скрытый скрипт: ждёт закрытия программы, подменяет ZapretGUI.exe и запускает его заново."""
    q = lambda s: str(s).replace("'", "''")
    script = f"""$ErrorActionPreference = 'SilentlyContinue'
$src = '{q(src)}'
$dst = '{q(sys.executable)}'
try {{ Wait-Process -Id {os.getpid()} -Timeout 30 }} catch {{}}
for ($i = 0; $i -lt 60; $i++) {{
    try {{ Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop; break }}
    catch {{ Start-Sleep -Milliseconds 500 }}
}}
Start-Process -FilePath $dst
Remove-Item -LiteralPath $PSCommandPath -Force
"""
    ps1 = Path(tempfile.gettempdir()) / "zapretgui-update.ps1"
    ps1.write_text(script, encoding="utf-8-sig")
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(ps1)],
        creationflags=NO_WINDOW | 0x200, close_fds=True,  # 0x200 = CREATE_NEW_PROCESS_GROUP
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- запуск / остановка ----------
LAST_PROC = None
MODE = ""


def strategies() -> list[str]:
    key = lambda s: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s.lower())]
    return sorted((p.name for p in release_dir().glob("general*.bat")), key=key)


def is_running() -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq winws.exe", "/NH"],
                             capture_output=True, text=True, creationflags=NO_WINDOW).stdout
        return "winws.exe" in out.lower()
    except Exception:
        return False


def parse_bat(bat: Path) -> str | None:
    """Достаёт аргументы winws.exe из general*.bat и подставляет переменные.
    None, если разобрать не удалось (тогда запускаем сам .bat скрытно)."""
    try:
        raw = bat.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("cp1251", errors="ignore")
    except OSError:
        return None
    text = re.sub(r"\^[ \t]*\r?\n", " ", text)  # строки, продолженные символом ^
    args = None
    for line in text.splitlines():
        s = line.strip().lower()
        if "winws.exe" in s and (s.startswith("start") or s.startswith('"')):
            m = re.search(r'winws\.exe"?\s+(.*)$', line, re.I)
            if m:
                args = m.group(1).strip()
                break
    if not args:
        return None
    rel = str(release_dir()) + "\\"
    gf = "1024-65535" if CFG["game_filter"] else "12"
    table = {"%bin%": rel + "bin\\", "%lists%": rel + "lists\\", "%~dp0": rel,
             "%gamefilter%": gf, "%gamefiltertcp%": gf, "%gamefilterudp%": gf}
    args = re.sub(r"%~?[A-Za-z0-9_]+%?", lambda m: table.get(m.group(0).lower(), m.group(0)), args)
    if re.search(r"%[A-Za-z~]", args):  # осталась неизвестная переменная
        return None
    return args


PLACEHOLDER_HOST = "domain.example.abc"
PLACEHOLDER_IP = "203.0.113.113/32"


def ensure_lists(args: str = "") -> None:
    """winws падает, если файл списка из командной строки не существует. Релиз не содержит *-user.txt,
    их создаёт service.bat; мы запускаем winws напрямую, поэтому создаём недостающие файлы сами.
    Пустой список winws понимает как «без фильтра», поэтому кладём безобидную заглушку."""
    lists = release_dir() / "lists"
    lists.mkdir(parents=True, exist_ok=True)
    names = {"list-general-user.txt", "list-exclude-user.txt", "ipset-exclude-user.txt"}
    for m in re.finditer(r'--(?:hostlist|ipset)(?:-exclude)?="?([^"\s]+)"?', args):
        names.add(re.split(r"[\\/]", m.group(1))[-1])
    for name in names:
        p = lists / name
        blank = not p.exists() or (name.endswith("-user.txt") and not p.read_text(encoding="utf-8", errors="ignore").strip())
        if blank:
            p.write_text((PLACEHOLDER_IP if "ipset" in name.lower() else PLACEHOLDER_HOST) + "\n", encoding="utf-8")


def start(strategy: str, force_bat: bool = False) -> str:
    """Запускает обход скрытно (без окна и значка на панели задач)."""
    global LAST_PROC, MODE
    stop(full=False)
    rel = release_dir()
    args = parse_bat(rel / strategy)
    ensure_lists(args or "")
    apply_profiles()
    log = open(base_dir() / "winws.log", "wb")
    si = None
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
    except AttributeError:
        pass
    common = dict(cwd=str(rel), creationflags=NO_WINDOW, startupinfo=si,
                  stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    if args and not force_bat:
        LAST_PROC = subprocess.Popen(f'"{rel / "bin" / "winws.exe"}" {args}', **common)
        MODE = "прямой запуск winws"
    else:
        LAST_PROC = subprocess.Popen(["cmd", "/c", strategy], **common)
        MODE = "через .bat (скрытно)"
    return MODE


def start_error() -> str:
    """Если winws сразу завершился, возвращает конец его журнала."""
    if LAST_PROC is not None and MODE.startswith("прямой") and LAST_PROC.poll() is not None:
        try:
            lines = (base_dir() / "winws.log").read_text(encoding="utf-8", errors="ignore").strip().splitlines()
            return "\n".join(lines[-5:]) or f"winws завершился с кодом {LAST_PROC.returncode}"
        except OSError:
            return f"winws завершился с кодом {LAST_PROC.returncode}"
    return ""


def _run(cmd: list[str]) -> None:
    try:
        subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW, timeout=20)
    except Exception:
        pass


def stop(full: bool = True) -> None:
    """Выключает обход. full=True: убивает winws, останавливает службу zapret и драйвер WinDivert,
    так что в системе ничего не остаётся. full=False: только процесс (для быстрого перезапуска)."""
    _run(["taskkill", "/IM", "winws.exe", "/F", "/T"])
    if full:
        _run(["sc", "stop", "zapret"])
        for drv in ("WinDivert", "WinDivert14"):
            _run(["sc", "stop", drv])
    for _ in range(15):  # ждём, пока процесс действительно исчезнет
        if not is_running():
            break
        time.sleep(0.2)


def auto_select(log) -> str | None:
    """Пробует стратегии по очереди и возвращает первую, при которой открываются все сайты из списка
    (или лучшую по числу открывшихся)."""
    names = strategies()
    sites = [s["url"] for s in CFG["sites"]][:5]
    if not names or not sites:
        return None
    best_score, best = -1, None
    for i, name in enumerate(names, 1):
        log(f"Проверяю {i}/{len(names)}: {name}")
        start(name)
        time.sleep(4)  # даём winws загрузиться
        if start_error():
            continue
        with ThreadPoolExecutor(max_workers=len(sites)) as ex:
            score = sum(1 for r in ex.map(probe, sites) if r["ok"])
        if score == len(sites):
            return name
        if score > best_score:
            best_score, best = score, name
    return best


# ---------- сайты для проверки ----------
def normalize_url(text: str) -> str:
    text = text.strip()
    return text if re.match(r"^https?://", text, re.I) else "https://" + text


def site_name(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.removeprefix("www.") or url


def probe(url: str) -> dict:
    t0 = time.perf_counter()
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=8)
        code = r.status
        r.close()
    except urllib.error.HTTPError as e:   # сервер ответил -> сайт доступен
        code = e.code
    except Exception as e:
        return {"ok": False, "code": None, "ms": None, "error": str(e)}
    return {"ok": True, "code": code, "ms": int((time.perf_counter() - t0) * 1000)}


def add_site(text: str) -> bool:
    url = normalize_url(text)
    if not text.strip() or any(s["url"] == url for s in CFG["sites"]):
        return False
    CFG["sites"].append({"name": site_name(url), "url": url})
    save()
    return True


def remove_site(url: str) -> None:
    CFG["sites"] = [s for s in CFG["sites"] if s["url"] != url]
    save()


# ---------- автозапуск (задача планировщика с правами администратора) ----------
def set_autostart(on: bool) -> bool:
    if on:
        exe = f'"{sys.executable}"' if getattr(sys, "frozen", False) \
            else f'"{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        cmd = ["schtasks", "/create", "/tn", TASK_NAME, "/tr", f"{exe} --minimized",
               "/sc", "onlogon", "/rl", "highest", "/f"]
    else:
        cmd = ["schtasks", "/delete", "/tn", TASK_NAME, "/f"]
    try:
        ok = subprocess.run(cmd, capture_output=True, creationflags=NO_WINDOW).returncode == 0
    except Exception:
        ok = False
    if ok:
        CFG["autostart"] = on
        save()
    return ok


# ---------- списки ----------
def list_path(name: str, create: bool = False) -> Path:
    p = release_dir() / "lists" / name
    if create:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p
