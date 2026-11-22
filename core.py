"""Логика без GUI: папки, обновление с GitHub, бэкапы, импорт, запуск, проверка сайтов."""
from __future__ import annotations
import copy
import ctypes
import json
import os
import re
import shutil
import ssl
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

import look

REPO = "Flowseal/zapret-discord-youtube"
REPO_URL = f"https://github.com/{REPO}"
API_LATEST = f"https://api.github.com/repos/{REPO}/releases/latest"
APP_NAME = "ZapretGUI"
try:
    from version import APP_REPO as _APP_REPO, VERSION
except Exception:
    VERSION, _APP_REPO = "0.0.0", ""
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
    "font_size": "normal",  # старые small/normal/large или непрерывное значение 9–16 pt
    "corners": "soft",      # soft | sharp
    "density": "normal",    # compact | normal | spacious
    "animations": True,
    "animation_style": "smooth",  # smooth | quick | subtle
    "collapsed_sections": {},  # индивидуальные настройки сворачивания блоков
    "sites_auto": True,     # проверять сайты после включения обхода
    "lists_auto_update": True,
    "lists_updated": "",
    "lists_checked": 0,
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


_SSL_CTX = None


def gh_open(req, timeout: int = 15):
    """urlopen для GitHub с набором сертификатов certifi (если установлен)."""
    global _SSL_CTX
    if _SSL_CTX is None:
        try:
            import certifi
            _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            _SSL_CTX = ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=_SSL_CTX)


def _strip_prefix(s: str, prefix: str) -> str:  # str.removeprefix есть только в Python 3.9+
    return s[len(prefix):] if s.startswith(prefix) else s


def _coerce(cfg: dict) -> dict:
    """Приводит значения к ожидаемым типам: старые и повреждённые настройки не должны ронять приложение."""
    for key, default in DEFAULTS.items():
        val = cfg.get(key, default)
        if isinstance(default, bool):
            val, ok = look.to_bool(val, default), True   # "false", 0, "off" и т.п. из старых/ручных файлов
        elif key == "font_size" and isinstance(val, (int, float)) and not isinstance(val, bool):
            ok = True  # новые непрерывные значения размера шрифта; старые строки тоже поддерживаются
        elif isinstance(default, (int, float)):
            ok = isinstance(val, (int, float)) and not isinstance(val, bool)
        else:
            ok = isinstance(val, type(default))
        if not ok:
            val = copy.deepcopy(default)
        cfg[key] = val
    cfg["profiles_enabled"] = [x for x in cfg["profiles_enabled"] if isinstance(x, str)]
    raw_collapsed = cfg.get("collapsed_sections", {})
    cfg["collapsed_sections"] = {str(k): look.to_bool(v, False) for k, v in raw_collapsed.items()} if isinstance(raw_collapsed, dict) else {}
    cfg["sites"] = [{"name": str(s.get("name") or s["url"]), "url": s["url"]} for s in cfg["sites"]
                    if isinstance(s, dict) and isinstance(s.get("url"), str) and s["url"].strip()]
    return look.sanitize_look(cfg)


def _load() -> dict:
    data = {}
    try:
        raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, dict):
            raise ValueError("config is not an object")
        data = raw
    except FileNotFoundError:
        pass
    except Exception:  # файл повреждён: сохраняем его копию и стартуем с настройками по умолчанию
        try:
            os.replace(str(CONFIG_FILE), str(CONFIG_FILE.with_name("config.json.bad")))
        except OSError:
            pass
    return _coerce({**copy.deepcopy(DEFAULTS), **data})


CFG = _load()


def save() -> None:
    """Запись через временный файл: при сбое посреди записи старый config.json остаётся целым."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_name("config.json.tmp")
    tmp.write_text(json.dumps(CFG, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(str(tmp), str(CONFIG_FILE))


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
    with gh_open(req, 15) as r:
        data = json.load(r)
    for a in data.get("assets", []):
        if a["name"].lower().endswith(".zip"):
            return data["tag_name"], a["browser_download_url"]
    return data["tag_name"], data["zipball_url"]


def list_zapret_releases(limit: int = 20) -> list[dict]:
    """Список релизов zapret (Flowseal), новые сверху. Каждый: tag, date, url (zip)."""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/releases?per_page={limit}",
        headers={**UA, "Accept": "application/vnd.github+json"})
    with gh_open(req, 15) as r:
        data = json.load(r)
    out = []
    for rel in data:
        if rel.get("draft"):
            continue
        asset = next((a for a in rel.get("assets", []) if a["name"].lower().endswith(".zip")), None)
        url = asset["browser_download_url"] if asset else rel.get("zipball_url")
        if not url:
            continue
        tag = rel["tag_name"]
        out.append({
            "tag": tag,
            "date": (rel.get("published_at") or "")[:10],
            "pre": bool(rel.get("prerelease")),
            "url": url,
        })
    return out


def fetch_favicon(url: str) -> bytes | None:
    """Скачать иконку сайта (favicon). Сначала Google s2, потом /favicon.ico."""
    host = site_name(url) if "://" in url else url
    host = host.split("/")[0].strip()
    if not host:
        return None
    candidates = [
        f"https://www.google.com/s2/favicons?domain={urllib.parse.quote(host)}&sz=64",
        f"https://icons.duckduckgo.com/ip3/{host}.ico",
        f"https://{host}/favicon.ico",
    ]
    for fav_url in candidates:
        try:
            req = urllib.request.Request(fav_url, headers=UA)
            with gh_open(req, 8) as r:
                data = r.read(200_000)
            if data and len(data) > 32:
                return data
        except Exception:
            continue
    return None


def _download(url: str, dest: Path, log) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with gh_open(req, 30) as r, open(dest, "wb") as f:
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
    try:
        n = update_lists(log)
        log(f"Списки: обновлено файлов {n}" if n else "Списки уже актуальны")
    except Exception as e:
        log(f"Списки не обновились: {e}")


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
    # Xbox + Microsoft Account + Minecraft (общий стек Microsoft / Xbox Live)
    "Xbox Microsoft Minecraft": [
        # Xbox Live / Game Pass
        "xbox.com", "xboxlive.com", "xboxservices.com", "xboxab.com", "xboxgamepass.com",
        "gamepass.com", "xboxplayanywhere.com", "xbx.lv",
        "xsts.auth.xboxlive.com", "user.auth.xboxlive.com", "auth.xboxlive.com",
        "titlehub.xboxlive.com", "achievements.xboxlive.com", "gamecms.xboxlive.com",
        "profile.xboxlive.com", "presence.xboxlive.com", "userpresence.xboxlive.com",
        "images-eds-ssl.xboxlive.com", "xforge.xboxlive.com",
        # Microsoft identity / account
        "live.com", "login.live.com", "account.live.com", "account.microsoft.com",
        "login.microsoftonline.com", "microsoftonline.com", "microsoft.com",
        "msauth.net", "msftauth.net", "aadcdn.msauth.net",
        # Minecraft / Mojang
        "minecraft.net", "minecraftservices.com", "api.minecraftservices.com",
        "mojang.com", "launchercontent.mojang.com", "launchermeta.mojang.com",
        "piston-meta.mojang.com", "textures.minecraft.net",
        "minecraft-services.net", "client.discovery.minecraft-services.net",
        "authorization.franchise.minecraft-services.net",
    ],
    # X (Twitter)
    "X Twitter": [
        "x.com", "twitter.com", "t.co", "twimg.com", "pscp.tv", "periscope.tv",
        "api.x.com", "api.twitter.com", "mobile.twitter.com", "abs.twimg.com",
        "pbs.twimg.com", "video.twimg.com", "upload.twitter.com", "upload.x.com",
        "abs-0.twimg.com", "static.ads-twitter.com", "syndication.twitter.com",
        "tweetdeck.com", "api.tweetdeck.com", "help.x.com", "support.twitter.com",
    ],
    # Roblox (только ключевые домены, без *.amazonaws.com / cloudfront — иначе тормозит весь интернет)
    "Roblox": [
        "roblox.com", "www.roblox.com", "robloxlabs.com", "rblx.com", "rbx.com",
        "rbxcdn.com", "setup.rbxcdn.com", "api.rbxcdn.com", "js.rbxcdn.com", "static.rbxcdn.com",
        "auth.roblox.com", "accountsettings.roblox.com", "apis.roblox.com",
        "assetgame.roblox.com", "assetdelivery.roblox.com", "catalog.roblox.com",
        "avatar.roblox.com", "economy.roblox.com", "games.roblox.com", "gamejoin.roblox.com",
        "friends.roblox.com", "groups.roblox.com", "presence.roblox.com", "realtime.roblox.com",
        "chat.roblox.com", "voice.roblox.com", "notifications.roblox.com",
        "clientsettings.api.roblox.com", "clientsettingscdn.roblox.com",
        "thumbnails.roblox.com", "inventory.roblox.com", "users.roblox.com",
        "develop.roblox.com", "studio.roblox.com", "publish.roblox.com",
        "gamepersistence.roblox.com", "matchmaking.roblox.com", "metrics.roblox.com",
        "client-telemetry.roblox.com", "telemetry.roblox.com",
        "versioncompatibility.roblox.com", "setup.roblox.com", "update.roblox.com",
        "rbxinfra.net", "rbxtrk.com",
    ],
}
_BAD_NAME = re.compile(r'[\\/:*?"<>|]')


def safe_name(name: str) -> str:
    return _BAD_NAME.sub("", name).strip()[:40]


def seed_profiles() -> None:
    """Кладём готовые шаблоны (выключенными). Можно править и удалять.
    Новые пресеты из обновления тоже появляются, если файла ещё нет."""
    created = False
    for name, domains in PRESETS.items():
        p = profiles_dir() / f"{name}.txt"
        if not p.exists():
            p.write_text("\n".join(domains) + "\n", encoding="utf-8")
            created = True
    if created or not CFG.get("profiles_seeded"):
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
def app_asset() -> str:
    """Какой файл брать из релиза: сборка для Windows 7 (на PySide2) или обычная."""
    return "ZapretGUI-Win7.exe" if "PySide2" in sys.modules else "ZapretGUI.exe"


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
    try:
        with gh_open(req, 20) as r:
            data = json.load(r)
    except urllib.error.HTTPError as exc:
        # 404 означает, что сам репозиторий не найден или недоступен (релизов нет — это HTTP 200 с []).
        if exc.code == 404:
            raise RuntimeError(f"Репозиторий GitHub {repo} не найден или закрыт. Проверь поле «владелец/репозиторий».") from exc
        if exc.code == 403:
            raise RuntimeError("GitHub временно ограничил запросы API. Попробуй проверить обновления через несколько минут.") from exc
        raise RuntimeError(f"GitHub API вернул HTTP {exc.code}: {exc.reason}") from exc
    except (urllib.error.URLError, TimeoutError, ssl.SSLError) as exc:
        reason = getattr(exc, "reason", exc)
        raise RuntimeError(f"Не удалось подключиться к GitHub: {reason}. Проверь интернет и настройки прокси.") from exc
    if not isinstance(data, list):
        raise RuntimeError("GitHub вернул неожиданный ответ при проверке релизов.")
    out = []
    with_pre = CFG.get("app_channel") == "pre"
    for rel in data:
        if rel.get("draft") or (rel.get("prerelease") and not with_pre):
            continue
        asset = next((a for a in rel.get("assets", []) if a["name"].lower() == app_asset().lower()), None)
        if asset:
            tag = rel["tag_name"]
            out.append({"tag": tag, "version": tag.lstrip("vV"), "date": (rel.get("published_at") or "")[:10],
                        "pre": bool(rel.get("prerelease")), "url": asset["browser_download_url"],
                        "notes": (rel.get("body") or "").strip()})
    if data and not out:
        raise RuntimeError(f"В {repo} есть релизы, но ни в одном нет файла {app_asset()}. Опубликуй EXE в Assets релиза.")
    out.sort(key=lambda x: parse_ver(x["version"]), reverse=True)
    return out


def list_app_backups() -> list[str]:
    """Версии приложения, сохранённые перед обновлением (кроме текущей)."""
    vers = {_strip_prefix(p.stem, "ZapretGUI-") for p in app_backup_dir().glob("ZapretGUI-*.exe")}
    vers.discard(VERSION)
    return sorted(vers, key=parse_ver, reverse=True)


def _backup_current_app() -> None:
    shutil.copy2(sys.executable, app_backup_dir() / f"ZapretGUI-{VERSION}.exe")
    files = sorted(app_backup_dir().glob("ZapretGUI-*.exe"),
                   key=lambda p: parse_ver(_strip_prefix(p.stem, "ZapretGUI-")), reverse=True)
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
    """Ждёт выхода текущего процесса, подменяет exe и запускает новую версию.
    Надёжнее: несколько попыток копирования, рабочая папка, лог при сбое."""
    q = lambda s: str(s).replace("'", "''")
    src_s, dst_s = q(src.resolve()), q(Path(sys.executable).resolve())
    work_dir = q(Path(sys.executable).resolve().parent)
    pid = os.getpid()
    log_path = q(Path(tempfile.gettempdir()) / "zapretgui-update.log")
    script = f"""$ErrorActionPreference = 'Continue'
$src = '{src_s}'
$dst = '{dst_s}'
$wd  = '{work_dir}'
$log = '{log_path}'
function W($m) {{ Add-Content -LiteralPath $log -Value ("[{{0}}] {{1}}" -f (Get-Date -Format o), $m) }}
W "update start pid={pid}"
W "src=$src"
W "dst=$dst"
try {{ Wait-Process -Id {pid} -Timeout 45 -ErrorAction SilentlyContinue }} catch {{ W "wait: $_" }}
Start-Sleep -Milliseconds 800
$ok = $false
for ($i = 0; $i -lt 90; $i++) {{
    try {{
        if (-not (Test-Path -LiteralPath $src)) {{ W "src missing"; break }}
        Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop
        $ok = $true
        W "copied on try $i"
        break
    }} catch {{
        W "copy fail $i : $_"
        Start-Sleep -Milliseconds 400
    }}
}}
if ($ok) {{
    try {{
        # Не передаём новой onefile-сборке служебные переменные PyInstaller
        # от старого процесса: иначе bootloader ищет уже завершившийся PID.
        Get-ChildItem Env: | Where-Object {{ $_.Name -like '_PYI_*' }} | ForEach-Object {{
            Remove-Item -LiteralPath ("Env:" + $_.Name) -ErrorAction SilentlyContinue
        }}
        Start-Process -FilePath $dst -WorkingDirectory $wd
        W "started with clean PyInstaller environment"
    }} catch {{ W "start fail: $_" }}
}} else {{
    W "FAILED to replace exe"
}}
Remove-Item -LiteralPath $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
"""
    ps1 = Path(tempfile.gettempdir()) / "zapretgui-update.ps1"
    ps1.write_text(script, encoding="utf-8-sig")
    subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", str(ps1)],
        creationflags=NO_WINDOW | 0x200, close_fds=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# ---------- официальные списки (Flowseal/zapret-discord-youtube, папка lists) ----------
LISTS_API = f"https://api.github.com/repos/{REPO}/contents/lists?ref=main"


def update_lists(log) -> int:
    """Скачивает актуальные списки из официального репозитория в release/lists.
    Файлы *-user.txt не трогаем. Прежняя версия изменённого файла сохраняется как <имя>.bak.
    Возвращает число обновлённых файлов."""
    req = urllib.request.Request(LISTS_API, headers={**UA, "Accept": "application/vnd.github+json"})
    with gh_open(req, 15) as r:
        items = json.load(r)
    if not isinstance(items, list):
        raise ValueError("GitHub вернул неожиданный ответ (возможно, превышен лимит запросов)")
    lists = release_dir() / "lists"
    lists.mkdir(parents=True, exist_ok=True)
    changed = 0
    for it in items:
        name = it.get("name", "")
        if it.get("type") != "file" or not name.endswith(".txt") or name.endswith("-user.txt") \
                or not it.get("download_url"):
            continue
        with gh_open(urllib.request.Request(it["download_url"], headers=UA), 30) as r:
            data = r.read()
        if not data.strip():
            continue  # пустой ответ не должен затирать рабочий список
        target = lists / name
        old = target.read_bytes() if target.exists() else b""
        if old == data:
            continue
        if old.strip():
            shutil.copy2(target, target.with_name(name + ".bak"))
        tmp = target.with_name(name + ".tmp")
        tmp.write_bytes(data)
        os.replace(str(tmp), str(target))
        changed += 1
        log(f"Список обновлён: {name}")
    CFG["lists_updated"] = time.strftime("%d.%m.%Y %H:%M")
    CFG["lists_checked"] = time.time()
    save()
    return changed


def lists_due() -> bool:
    """Пора ли автоматически обновить списки (раз в 12 часов)."""
    return bool(CFG.get("lists_auto_update")) and time.time() - float(CFG.get("lists_checked") or 0) > 12 * 3600


# ---------- диагностика ----------
def windows_name() -> str:
    v = getattr(sys, "getwindowsversion", None)
    if v is None:
        return sys.platform
    v = v()
    if v.major == 10:
        return f"Windows {'11' if v.build >= 22000 else '10'} (сборка {v.build})"
    names = {(6, 1): "Windows 7", (6, 2): "Windows 8", (6, 3): "Windows 8.1"}
    return f"{names.get((v.major, v.minor), 'Windows')} ({v.major}.{v.minor}, сборка {v.build})"


def diagnose() -> list:
    """Проверка системы: список (статус, текст). Статус: True = хорошо, False = проблема, None = заметка."""
    out = []
    out.append((None, f"Система: {windows_name()}, приложение {VERSION}"))
    try:
        out.append((bool(ctypes.windll.shell32.IsUserAnAdmin()), "Права администратора"))
    except Exception:
        out.append((False, "Права администратора: не удалось проверить"))
    rel = release_dir()
    out.append((is_installed(), f"zapret установлен: {rel}"))
    bin_names = {p.name.lower() for p in (rel / "bin").glob("*")} if (rel / "bin").exists() else set()
    out.append(("winws.exe" in bin_names, "bin\\winws.exe"))
    has_dll = "windivert.dll" in bin_names
    has_sys = "windivert64.sys" in bin_names
    out.append((has_dll and has_sys, "WinDivert.dll и WinDivert64.sys в bin"))
    if not has_dll:
        out.append((False, "bin\\WinDivert.dll отсутствует — часто удаляет антивирус. Добавь папку в исключения и переустанови zapret."))
    if not has_sys:
        out.append((False, "bin\\WinDivert64.sys отсутствует — часто удаляет антивирус. Добавь папку в исключения и переустанови zapret."))
    for name in ("list-general.txt", "ipset-all.txt"):
        p = rel / "lists" / name
        size = p.stat().st_size if p.exists() else 0
        out.append((size > 0, f"lists\\{name}: {size} байт" if size else f"lists\\{name}: пусто или нет (кнопка «Обновить списки»)"))
    # Отдельная диагностика WinDivert
    for drv in ("WinDivert", "WinDivert14"):
        try:
            q = subprocess.run(["sc", "query", drv], capture_output=True, text=True,
                               creationflags=NO_WINDOW, timeout=10).stdout
            if "RUNNING" in q:
                out.append((True, f"Драйвер {drv}: работает"))
            elif "STOPPED" in q:
                out.append((None, f"Драйвер {drv}: остановлен (нормально, если обход выключен)"))
            elif "1060" in q or "does not exist" in q.lower() or "не существует" in q.lower():
                out.append((None, f"Драйвер {drv}: не установлен (появится при первом успешном запуске)"))
            else:
                out.append((None, f"Драйвер {drv}: {q.strip().splitlines()[-1] if q.strip() else 'неизвестное состояние'}"))
        except Exception as e:
            out.append((False, f"Не удалось опросить драйвер {drv}: {e}"))
    # Проверка, не заблокирован ли файл антивирусом (попытка открыть на чтение)
    for fname in ("winws.exe", "windivert.dll", "windivert64.sys"):
        p = rel / "bin" / fname
        if p.exists():
            try:
                with open(p, "rb") as f:
                    f.read(64)
            except PermissionError:
                out.append((False, f"bin\\{fname} заблокирован (PermissionError) — почти наверняка антивирус. Добавь папку в исключения."))
            except OSError as e:
                out.append((False, f"bin\\{fname}: ошибка доступа ({e})"))
    try:
        with gh_open(urllib.request.Request("https://api.github.com/rate_limit", headers=UA), 10):
            out.append((True, "GitHub доступен"))
    except Exception as e:
        out.append((False, f"GitHub недоступен: {e}"))
    if is_installed() and CFG.get("strategy"):
        try:
            ok, text = test_launch(CFG["strategy"])
            out.append((ok, f"Пробный запуск «{CFG['strategy']}»: {text}"))
        except Exception as e:
            out.append((False, f"Пробный запуск не удался: {e}"))
    v = getattr(sys, "getwindowsversion", None)
    if v is not None and (v().major, v().minor) == (6, 1):
        out.append((None, "Windows 7: нужны обновления KB3033929 и KB4474419, а в zapret\\bin нужно заменить WinDivert.dll "
                          "и WinDivert64.sys файлами из папки win7 репозитория bol-van/zapret-win-bundle"))
        if "PySide2" not in sys.modules:
            out.append((False, "Запущена не Win7-версия приложения (ZapretGUI-Win7.exe)"))
    return out


# ---------- почему не запустилось ----------
# Коды ошибок Windows, которые winws печатает вместе с «windivert: ...»
WINDIVERT_CODES = {
    5: "Нет доступа к драйверу WinDivert (код 5). Программа должна работать от администратора; "
       "проверь, что антивирус или защита Windows не блокируют WinDivert.",
    2: "Не найден файл драйвера WinDivert64.sys (код 2). Скорее всего, его удалил антивирус: "
       "добавь папку программы в исключения и нажми «Скачать и установить» в разделе zapret.",
    3: "Не найден путь к драйверу WinDivert (код 3): переустанови zapret кнопкой «Скачать и установить».",
    87: "WinDivert не принял фильтр (код 87): стратегия не подходит к этой версии winws, выбери другую "
        "или обнови zapret.",
    577: "Windows не принимает подпись драйвера WinDivert (код 577). На Windows 7 нужны обновления "
         "KB3033929 и KB4474419 и файлы WinDivert из папки win7 (zapret-win-bundle).",
    1058: "Служба WinDivert отключена (код 1058): включи её или перезагрузи компьютер.",
    1060: "Служба WinDivert не установилась (код 1060): запусти от администратора и повтори.",
    1275: "Windows заблокировала загрузку драйвера WinDivert (код 1275). Проверь «Изоляцию ядра» → "
          "«Целостность памяти» и Smart App Control, а также антивирус.",
}
EXIT_CODES = {
    0xC0000135: "Не найдена системная библиотека: поставь Microsoft Visual C++ Redistributable 2015-2022 (x64).",
    0xC000007B: "Неверная разрядность библиотеки: нужен 64-разрядный Windows и Visual C++ Redistributable x64.",
}


def bin_problems() -> list[str]:
    """Проверяет, что нужные файлы на месте (их часто удаляет антивирус)."""
    b = release_dir() / "bin"
    names = {p.name.lower() for p in b.glob("*")} if b.exists() else set()
    out = []
    for want in ("winws.exe", "windivert.dll", "windivert64.sys"):
        if want not in names:
            out.append(f"bin\\{want} не найден: скорее всего, его удалил антивирус. Добавь папку программы "
                       "в исключения и нажми «Скачать и установить» в разделе zapret.")
    return out


def explain_output(text: str, returncode: int | None = None) -> str:
    """По тексту, который напечатал winws, пытается объяснить причину. Пустая строка = не поняли."""
    low = (text or "").lower()
    m = re.search(r"windivert[^\n]*?\(\s*(\d+)\s*\)", low) or re.search(r"error[^\n]*?\(\s*(\d+)\s*\)", low)
    if m and int(m.group(1)) in WINDIVERT_CODES:
        return WINDIVERT_CODES[int(m.group(1))]
    if returncode is not None and (returncode & 0xFFFFFFFF) in EXIT_CODES:
        return EXIT_CODES[returncode & 0xFFFFFFFF]
    if "could not read ^!" in low or "could not read !" in low:
        return "Ошибка экранирования аргументов BAT: обнови приложение до исправленной версии и повтори запуск стратегии."
    if ("hostlist" in low or "ipset" in low) and any(w in low for w in ("cannot", "failed", "open", "access")):
        return "winws не смог открыть файл списка: нажми «Обновить списки с GitHub» или переустанови zapret."
    if any(w in low for w in ("unknown option", "invalid parameter", "unrecognized", "unknown parameter")):
        return "Эта стратегия не подходит к установленной версии winws: выбери другую или обнови zapret."
    return ""


def test_launch(strategy: str, seconds: float = 4.0) -> tuple[bool, str]:
    """Запускает winws на несколько секунд и возвращает (запустился, пояснение). Работающий обход не трогает."""
    problems = bin_problems()
    if problems:
        return False, " ".join(problems)
    rel = release_dir()
    args = parse_bat(rel / strategy)
    if not args:
        return False, f"Не удалось прочитать параметры из {strategy}: выбери другую стратегию."
    if is_running():
        return True, "winws сейчас работает"
    ensure_lists(args)
    apply_profiles()
    si = None
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
    except AttributeError:
        pass
    proc = subprocess.Popen(f'"{rel / "bin" / "winws.exe"}" {args}', cwd=str(rel), creationflags=NO_WINDOW,
                            startupinfo=si, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    try:
        out, _ = proc.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:  # не завершился сам: значит, запустился
        proc.kill()
        proc.communicate()
        return True, "winws запускается нормально"
    text = out.decode("utf-8", errors="replace").strip()
    hint = explain_output(text, proc.returncode)
    tail = " | ".join(text.splitlines()[-3:]) if text else f"winws завершился с кодом {proc.returncode}"
    return False, (hint + "  [" + tail + "]") if hint else tail


# ---------- запуск / остановка ----------
LAST_PROC = None
MODE = ""


def strategies() -> list[str]:
    key = lambda s: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s.lower())]
    return sorted((p.name for p in release_dir().glob("general*.bat")), key=key)


def is_running() -> bool:
    """True, если процесс winws.exe жив.
    Сначала смотрим дескриптор LAST_PROC (если прямой запуск и он ещё наш),
    затем tasklist — чтобы ловить и запуск через .bat, и чужие экземпляры."""
    global LAST_PROC
    if LAST_PROC is not None:
        try:
            if LAST_PROC.poll() is None:
                # Процесс, который мы запустили, ещё жив.
                # Для прямого запуска это и есть winws.exe; для .bat — cmd,
                # но cmd обычно быстро завершается, поэтому ниже всё равно
                # проверяем tasklist.
                if MODE.startswith("прямой"):
                    return True
            else:
                LAST_PROC = None  # уже умер — не держим мёртвый дескриптор
        except Exception:
            LAST_PROC = None
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq winws.exe", "/NH"],
                             capture_output=True, text=True, creationflags=NO_WINDOW,
                             timeout=5).stdout
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
    # В BAT символ ^ экранирует спецсимволы cmd.exe. При прямом Popen(shell=False)
    # cmd.exe не обрабатывает аргументы, поэтому winws получал буквальный ^! и
    # пытался открыть его как имя файла (ошибка «could not read ^!»).
    # Снимаем только экранирование cmd-метасимволов, не затрагивая обычные каретки.
    args = re.sub(r"\^([!^&|<>()])", r"\1", args)
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
    """Запускает обход скрытно (без окна и значка на панели задач).
    Всегда останавливает предыдущий экземпляр и запускает заново —
    иначе смена стратегии/профилей не применяется."""
    global LAST_PROC, MODE
    # При смене BAT-стратегии завершаем только предыдущий winws.
    # Не останавливаем системные службы/драйверы WinDivert при каждом
    # переключении: их принудительная выгрузка может рвать сетевой стек и
    # оставлять браузерные HTTP/2/QUIC-сессии в подвешенном состоянии.
    # Полная остановка драйверов остаётся только для явного выключения обхода.
    stop(full=False)
    rel = release_dir()
    args = parse_bat(rel / strategy)
    ensure_lists(args or "")
    apply_profiles()
    direct = bool(args) and not force_bat
    log = open(base_dir() / ("winws.log" if direct else "winws-bat.log"), "wb")  # у каждого способа свой журнал
    si = None
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0  # SW_HIDE
    except AttributeError:
        pass
    common = dict(cwd=str(rel), creationflags=NO_WINDOW, startupinfo=si,
                  stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    try:
        if direct:
            LAST_PROC = subprocess.Popen(f'"{rel / "bin" / "winws.exe"}" {args}', **common)
            MODE = "прямой запуск winws"
        else:
            LAST_PROC = subprocess.Popen(["cmd", "/c", strategy], **common)
            MODE = "через .bat (скрытно)"
    finally:
        log.close()  # у дочернего процесса остаётся своя копия дескриптора
    return MODE


def start_error() -> str:
    """Возвращает вывод неудачного запуска и для прямого запуска, и для BAT."""
    if LAST_PROC is not None and LAST_PROC.poll() is not None:
        # cmd.exe может завершиться сразу после start, оставив winws работать.
        # В этом случае наличие winws проверяет вызывающий код; журнал нужен,
        # только если процесса winws действительно нет.
        filename = "winws-bat.log" if MODE.startswith("через") else "winws.log"
        try:
            lines = (base_dir() / filename).read_text(encoding="utf-8", errors="ignore").strip().splitlines()
            useful = [line for line in lines if line.strip()]
            if useful:
                return "\n".join(useful[-8:])
            if LAST_PROC.returncode not in (0, None):
                return f"Процесс запуска завершился с кодом {LAST_PROC.returncode}"
        except OSError:
            if LAST_PROC.returncode not in (0, None):
                return f"Процесс запуска завершился с кодом {LAST_PROC.returncode}"
    return ""


def _run(cmd: list[str], timeout: int = 20):
    """Тихий запуск системной команды; результат оставляем вызывающему коду."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              creationflags=NO_WINDOW, timeout=timeout)
    except Exception:
        return None


def flush_dns_cache() -> bool:
    """Сбрасывает только DNS-кэш Windows после смены сетевого фильтра.

    Это не закрывает активные HTTP/2 или QUIC-сессии браузера, но устраняет
    устаревшие DNS-ответы. Ошибка команды не должна мешать запуску zapret.
    """
    result = _run(["ipconfig", "/flushdns"], timeout=10)
    return bool(result is not None and result.returncode == 0)


def _wait_driver_stopped(driver: str, timeout: float = 5.0) -> bool:
    """Ждёт, пока WinDivert действительно перейдёт в STOPPED/отсутствует."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = _run(["sc", "query", driver], timeout=5)
        output = ((getattr(result, "stdout", "") or "") +
                  (getattr(result, "stderr", "") or "")).upper()
        # 1060 — служба не установлена; это также означает, что её нечему держать.
        if result is not None and ("1060" in output or "STOPPED" in output or result.returncode != 0):
            return True
        time.sleep(0.2)
    return False


def stop(full: bool = True) -> None:
    """Останавливает winws; full=True дополнительно останавливает службы при полном выключении.

    Переключение стратегий вызывает stop(full=False), чтобы не выгружать
    WinDivert из-под работающих сетевых приложений. Новый winws не запускается,
    пока старый процесс действительно не исчезнет.
    """
    global LAST_PROC, MODE
    _run(["taskkill", "/IM", "winws.exe", "/F", "/T"])
    deadline = time.monotonic() + 8.0
    while time.monotonic() < deadline:
        if not is_running():
            break
        time.sleep(0.2)
    if is_running():
        raise RuntimeError("Не удалось остановить предыдущий winws.exe за 8 секунд. Новый BAT не запущен, чтобы не создавать конфликт сетевых фильтров.")
    if full:
        _run(["sc", "stop", "zapret"])
        for drv in ("WinDivert", "WinDivert14"):
            _run(["sc", "stop", drv])
            _wait_driver_stopped(drv)
    if LAST_PROC is not None:
        try:
            if LAST_PROC.poll() is not None:
                LAST_PROC = None
        except Exception:
            LAST_PROC = None
    MODE = ""


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
    return _strip_prefix(urllib.parse.urlparse(url).netloc, "www.") or url


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


def add_site(text: str, name: str | None = None) -> bool:
    url = normalize_url(text)
    if not text.strip() or any(s["url"] == url for s in CFG["sites"]):
        return False
    CFG["sites"].append({"name": name or site_name(url), "url": url})
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
