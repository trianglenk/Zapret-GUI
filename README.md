<div align="center">

![Zapret GUI — README banner](docs/media/readme-banner.png)

# Zapret GUI

**Графический интерфейс Windows для управления zapret**

[![Windows](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)](https://www.microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PySide6-41CD52)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/license-see_repository-lightgrey)](LICENSE)

</div>

> [!NOTE]
> README описывает текущую структуру репозитория. Проект рассчитан на Windows. Перед публикацией проверьте, что лицензии используемых компонентов и самого zapret соблюдены.

## Содержание

- [Возможности](#возможности)
- [Скриншоты и GIF](#скриншоты-и-gif)
- [Установка готовой версии](#установка-готовой-версии)
- [Сборка из исходников](#сборка-из-исходников)
- [Публикация на GitHub](#публикация-на-github)
- [Обновление приложения](#обновление-приложения)
- [Структура проекта](#структура-проекта)
- [Решение проблем](#решение-проблем)
- [Безопасность и ответственность](#безопасность-и-ответственность)

## Возможности

- Графическое управление установленным zapret.
- Загрузка и обновление файлов zapret из настроенного upstream-репозитория.
- Работа с профилями и пользовательскими списками (если эти функции включены в сборку).
- Настройки оформления и поведения приложения.
- Импорт локальной папки или ZIP-архива zapret.
- Резервное копирование предыдущей рабочей версии при замене.
- Проверка GitHub Releases **самого Zapret GUI** и загрузка опубликованного установщика.

Функции и доступность отдельных пунктов зависят от версии приложения и конфигурации Windows.

## Скриншоты и GIF

Ниже — схема публикации обновления. Это обучающая иллюстрация, а не запись реального окна приложения.

![Схема обновления через GitHub Releases](docs/media/release-flow.gif)

### Скриншоты настоящего приложения

Добавьте реальные снимки экрана в `screenshots/` и обновите пути ниже. Рекомендуемые имена:

| Файл | Что показать |
|---|---|
| `screenshots/main.png` | Главное окно |
| `screenshots/profiles.png` | Страница профилей |
| `screenshots/settings.png` | Настройки, поле GitHub-репозитория и кнопку обновления |
| `screenshots/about.png` | Название и номер версии внизу настроек |

Пример разметки для добавления после создания файлов:

```markdown
![Главное окно](screenshots/main.png)
![Настройки](screenshots/settings.png)
```

## Установка готовой версии

1. Откройте вкладку **Releases** этого GitHub-репозитория.
2. Выберите последний стабильный релиз.
3. В разделе **Assets** скачайте `ZapretGUI-Setup.exe`.
4. Запустите установщик. Windows может запросить подтверждение прав администратора — это необходимо для операций, требующих повышенных прав.
5. Следуйте шагам мастера установки и запустите **Zapret GUI** из меню «Пуск» или с рабочего стола.

> [!WARNING]
> Скачивайте установщик только из Releases вашего доверенного репозитория. Не запускайте неизвестные EXE-файлы из сторонних источников.

## Сборка из исходников

### Требования

- Windows 10/11 x64.
- **Python 3.11 x64**: [python.org/downloads](https://www.python.org/downloads/). В установщике Python отметьте `Add Python to PATH`.
- **Inno Setup 6** — нужен только для создания установщика: [официальная загрузка](https://jrsoftware.org/isdl.php).
- **Git for Windows** — нужен для клонирования и публикации репозитория: [git-scm.com](https://git-scm.com/download/win).

`PySide6` и `PyInstaller` устанавливаются через `build.bat` из `requirements.txt` и команды сборки. Отдельно скачивать их вручную не требуется. Интернет нужен для установки Python-пакетов.

### Шаги

1. Скачайте ZIP исходников из GitHub или клонируйте репозиторий.
2. Распакуйте проект в папку без кириллицы в пути, например `C:\Projects\ZapretGUI`.
3. Установите Python 3.11 x64 и Inno Setup 6.
4. Откройте папку проекта.
5. Дважды запустите `build.bat` либо выполните его из CMD.

Скрипт:
- установит зависимости из `requirements.txt` и PyInstaller;
- соберёт `dist\ZapretGUI.exe`;
- если найден Inno Setup 6, создаст `installer\ZapretGUI-Setup.exe`;
- создаст ZIP-архив установщика `installer\ZapretGUI-Setup.zip`.

Если Inno Setup не установлен, EXE приложения всё равно будет собран в `dist\`, но установщик не появится.

### Ручная сборка

```powershell
py -3.11 -m pip install --upgrade pip
py -3.11 -m pip install -r requirements.txt pyinstaller
py -3.11 -m PyInstaller --noconfirm --onefile --windowed --uac-admin --icon icon.ico --add-data "icon.ico;." --name ZapretGUI main.py
```

Затем откройте `installer.iss` в Inno Setup Compiler и нажмите **Compile**.

## Публикация на GitHub

### 1. Создайте репозиторий

На GitHub создайте новый пустой репозиторий, например `ZapretGUI`. Не добавляйте README через сайт, если он уже есть в локальной папке проекта.

### 2. Отправьте исходники

Откройте PowerShell в папке, где находится `main.py`, и выполните команды (замените `USERNAME` на свой логин GitHub):

```powershell
git init
git add .
git commit -m "Zapret GUI 1.0.5"
git branch -M main
git remote add origin https://github.com/USERNAME/ZapretGUI.git
git push -u origin main
```

Если Git сообщает, что `origin` уже существует, используйте:

```powershell
git remote set-url origin https://github.com/USERNAME/ZapretGUI.git
```

### 3. Разрешите публикацию релизов через Actions

В репозитории откройте:

**Settings → Actions → General → Workflow permissions**

Выберите **Read and write permissions** и сохраните. Это нужно workflow, чтобы создать GitHub Release и загрузить в него установщик.

### 4. Выпустите новую версию

После отправки исходников создайте тег. Например, для версии `1.0.6`:

```powershell
git tag v1.0.6
git push origin v1.0.6
```

Перейдите во вкладку **Actions** и дождитесь успешного завершения сборки. Workflow `.github/workflows/release.yml` должен собрать приложение и опубликовать релиз с файлами:

- `ZapretGUI-Setup.exe` — установщик Windows;
- `ZapretGUI-Source.zip` — архив исходников.

> [!IMPORTANT]
> Workflow запускается при отправке тега `vX.Y.Z`. Используйте формат из трёх числовых частей, например `v1.0.6`. Перед выпуском убедитесь, что workflow успешно проходит на GitHub Actions.

## Обновление приложения

Обновление самого GUI и обновление файлов zapret — разные операции.

Чтобы приложение могло проверить новую версию GUI:

1. Опубликуйте GitHub Release в своём репозитории.
2. Убедитесь, что в **Assets** этого релиза лежит файл `ZapretGUI-Setup.exe`.
3. Откройте в Zapret GUI страницу **Настройки**.
4. В поле репозитория укажите `USERNAME/ZapretGUI` — без `https://github.com/`.
5. Сохраните настройки и нажмите кнопку проверки/обновления приложения.

Приложение использует GitHub Releases API и ищет последний опубликованный релиз. Если установщик отсутствует в Assets, обновление не сможет скачать его.

**Примечание:** автоматическая проверка обновлений не означает бесшумную установку. Скачанный установщик может потребовать подтверждения пользователя и прав администратора.

## Структура проекта

```text
ZapretGUI/
├── .github/
│   └── workflows/
│       └── release.yml       # сборка и публикация релизов
├── docs/
│   └── media/                # изображения README и GIF
├── screenshots/              # реальные скриншоты приложения
├── icon.ico                  # иконка Windows
├── icon.png                  # исходное изображение иконки
├── main.py                   # интерфейс PySide6
├── core.py                   # логика, загрузки и GitHub API
├── requirements.txt          # зависимости Python
├── build.bat                 # локальная сборка
├── installer.iss             # сценарий Inno Setup
└── README.md
```

## Решение проблем

**`python` или `py` не найден**

Переустановите Python 3.11 и отметьте `Add Python to PATH`. После установки откройте новое окно терминала.

**`PySide6` или `PyInstaller` не найден**

В папке проекта выполните:

```powershell
py -3.11 -m pip install -r requirements.txt pyinstaller
```

**Не создаётся установщик**

Проверьте, что установлен Inno Setup 6. `build.bat` ищет компилятор `ISCC.exe` в стандартных каталогах.

**GitHub Actions не может создать Release**

Проверьте `Settings → Actions → General → Workflow permissions`: должны быть разрешены `Read and write permissions`. Убедитесь, что workflow-файл загружен в ветку `main`, а тег имеет вид `v1.0.6`.

**Кнопка обновления не находит установщик**

Проверьте правильность `USERNAME/REPOSITORY`, наличие опубликованного (не Draft) релиза и файл `ZapretGUI-Setup.exe` в его Assets.

## Безопасность и ответственность

- Проверяйте исходный код и релизы перед запуском.
- Не публикуйте в репозитории `config.json`, личные данные, токены и другие секреты.
- Не добавляйте в релиз чужие бинарные файлы без проверки происхождения и лицензии.
- Изменение сетевых настроек и запуск компонентов обхода могут влиять на работу сети и сторонних программ. Используйте ПО только там, где это разрешено применимыми правилами и законодательством.
- Название и логотип zapret принадлежат соответствующим правообладателям; этот GUI не заявляет об официальной связи с upstream-проектом.

---

<div align="center">

**Zapret GUI · README для версии исходников 1.0.5**

</div>
