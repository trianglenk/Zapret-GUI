
readme = """<div align="center">

![Zapret GUI](docs/media/readme-banner.png)

# Zapret GUI

**Графический интерфейс Windows для управления zapret**

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/GUI-PySide6-41CD52)

</div>

## О приложении

Zapret GUI — графическое приложение для Windows, предназначенное для управления zapret.

Возможности зависят от текущей сборки и могут включать:
- управление zapret и его профилями;
- настройку параметров приложения;
- обновление файлов zapret;
- проверку новых версий Zapret GUI через GitHub Releases.

## Установка готовой версии

1. Откройте раздел **Releases** этого репозитория.
2. Скачайте `ZapretGUI-Setup.exe` из последнего релиза.
3. Запустите установщик и следуйте инструкциям.
4. При необходимости подтвердите запрос Windows на права администратора.

Скачивайте установщик только из релизов доверенного репозитория.

## Что нужно для сборки из исходников

Для самостоятельной сборки на Windows установите:

1. **Windows 10 или 11 (64-bit)**.
2. **Python 3.11 (64-bit)** — https://www.python.org/downloads/  
   При установке отметьте **Add Python to PATH**.
3. **Inno Setup 6** — https://jrsoftware.org/isdl.php  
   Нужен для создания установщика `Setup.exe`.
4. **Git for Windows** — https://git-scm.com/download/win  
   Нужен для клонирования и отправки проекта на GitHub.

`PySide6` и `PyInstaller` устанавливаются через Python из файла `requirements.txt` и скрипта сборки. Отдельно скачивать их не нужно.

## Сборка

1. Скачайте или клонируйте репозиторий.
2. Распакуйте проект в отдельную папку.
3. Откройте папку проекта.
4. Запустите `build.bat`.
5. Дождитесь завершения сборки.

Готовые файлы появятся в папках `dist` и `installer` (установщик создаётся при установленном Inno Setup 6).

## Публикация новой версии

Проект содержит GitHub Actions workflow для автоматической сборки релиза по тегу версии.

Пример для версии `1.0.6`:

```powershell
git tag v1.0.6
git push origin v1.0.6
```

В настройках репозитория GitHub Actions должны быть разрешены **Read and write permissions**. После успешной сборки проверьте, что в разделе **Releases → Assets** появился `ZapretGUI-Setup.exe`.

## Обновление приложения

Обновление Zapret GUI и обновление файлов zapret — разные операции. Для проверки обновления самого приложения укажите в настройках GUI репозиторий в формате `USERNAME/REPOSITORY`. Новая версия должна быть опубликована в GitHub Releases, а установщик `ZapretGUI-Setup.exe` должен быть прикреплён к релизу.

## Скриншоты

GIF-схема процесса выпуска релиза: [release-flow.gif](docs/media/release-flow.gif).

Для скриншотов реального интерфейса добавьте изображения в папку `screenshots/` и вставьте их в этот раздел.

## Структура проекта

- `main.py` — интерфейс приложения.
- `core.py` — основная логика.
- `requirements.txt` — Python-зависимости.
- `build.bat` — скрипт сборки.
- `installer.iss` — сценарий Inno Setup.
- `icon.ico` и `icon.png` — иконки.
- `.github/workflows/release.yml` — автоматическая сборка GitHub Releases.
- `docs/media/` — баннер и GIF для README.

## Важно

Используйте программу и сетевые инструменты в соответствии с законодательством и правилами вашей сети. Перед запуском проверяйте исходный код и файлы релизов. Этот графический интерфейс не заявляет об официальной связи с upstream-проектом zapret.
"""
(root / "README.md").write_text(readme, encoding="utf-8")

readme_out = Path("/mnt/data/README-ZapretGUI.md")
readme_out.write_text(readme, encoding="utf-8")

zip_out = Path("/mnt/data/ZapretGUI-1.0.5-GitHub-upload.zip")
with zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob("*"):
        if p.is_file():
            z.write(p, p.relative_to(base))

print("Созданы файлы:")
print(readme_out, readme_out.stat().st_size, "bytes")
print(zip_out, zip_out.stat().st_size, "bytes")
