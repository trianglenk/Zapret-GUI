<p align="center">
  <img src="assets/banner.png" alt="Zapret GUI" width="100%">
</p>

<p align="center">
  <a href="https://github.com/trianglenk/Zapret-GUI/releases/latest"><img alt="Релиз" src="https://img.shields.io/github/v/release/trianglenk/Zapret-GUI?label=%D1%80%D0%B5%D0%BB%D0%B8%D0%B7&color=7c5cff"></a>
  <a href="https://github.com/trianglenk/Zapret-GUI/releases"><img alt="Скачиваний" src="https://img.shields.io/github/downloads/trianglenk/Zapret-GUI/total?label=%D1%81%D0%BA%D0%B0%D1%87%D0%B8%D0%B2%D0%B0%D0%BD%D0%B8%D0%B9&color=2ee6c5"></a>
  <img alt="Windows" src="https://img.shields.io/badge/Windows-10%20%7C%2011-0c0d12">
  <a href="LICENSE"><img alt="Лицензия" src="https://img.shields.io/badge/%D0%BB%D0%B8%D1%86%D0%B5%D0%BD%D0%B7%D0%B8%D1%8F-MIT-lightgrey"></a>
</p>

# Zapret GUI

Графическая оболочка для [zapret-discord-youtube](https://github.com/Flowseal/zapret-discord-youtube): включение обхода в один клик, без окон `.bat` и значков на панели задач.

> Сам zapret в этом репозитории не хранится. Программа скачивает его из репозитория Flowseal и обновляет оттуда же. Проект не связан с авторами zapret.

## Возможности

- **Включение одной кнопкой**, обход работает скрыто (без окна `winws`). Выключение полностью останавливает `winws`, службу `zapret` и драйвер WinDivert.
- **Значок в трее**: зелёный круг, когда обход работает, красный, когда выключен. Закрытие окна сворачивает программу в трей.
- **Стратегии**: переключение между `general (ALT…)`, автоматический подбор рабочей, при смене сервис перезапускается сам.
- **Профили доменов** (Telegram, Discord, свои) и редактор списков.
- **Сайты**: карточки со статусом и временем ответа, сводка «доступно N из M», быстрое добавление популярных сайтов, автопроверка после включения обхода.
- **zapret и его списки обновляются сами** с GitHub (списки берутся из официальной папки `lists`), старые версии сохраняются в `backup`.
- **Диагностика**: права, файлы zapret, WinDivert, списки, доступ к GitHub.
- **Приложение обновляется само** из релизов этого репозитория (стабильные или пререлизы), с бэкапами и откатом на прежнюю версию.
- Темы (фиолетовая, зелёная, светлые, как в системе), цвет акцента, шрифт, углы, плотность, отключаемые анимации. Адаптивный вид: узкое окно как в телефоне, широкое с боковой панелью.

## Скриншоты

### Главное окно

<!-- Вставьте сюда изображение главной страницы -->
![Главное окно Zapret GUI](assets/ГлавноеокноZapretGUI.png)

*Главное окно: статус обхода, стратегия и сводка по сайтам.*

### Профили

<!-- Вставьте сюда изображение страницы профилей -->
![Профили доменов](assets/Профилидоменов.png)

*Профили доменов: Telegram, Discord и собственные списки.*

### Список

<!-- Вставьте сюда изображение списка сайтов -->
![Список](assets/Список.png)

### Cайтов

![сайтов](assets/сайтов.png)

### Настройки](assets/sd.png)

![Настройки](assets/sites-list.png)


*Список сайтов: статус, время ответа и быстрые действия.*

> Чтобы скриншоты отобразились, положите файлы `main-window.png`, `profiles-page.png` и `sites-list.png` в папку `assets/` вашего репозитория (рядом с `banner.png`).

## Установка

1. Скачай `ZapretGUI-Setup.zip` из [последнего релиза](https://github.com/trianglenk/Zapret-GUI/releases/latest) и распакуй.
2. Запусти `ZapretGUI-Setup.exe`, выбери папку (по умолчанию `C:\Program Files\Zapret GUI`).
3. Запускай через меню «Пуск» или ярлык. Программа попросит права администратора: они нужны драйверу WinDivert.

В установленной папке лежит всё вместе:

```text
Zapret GUI
├── ZapretGUI.exe   программа
├── release\        рабочая версия zapret
├── backup\         бэкапы старых версий zapret
├── app_backup\     бэкапы старых версий приложения
├── downloads\      скачанные архивы
├── profiles\       профили доменов
└── config.json     настройки
```
    Используйте код с осторожностью.

Windows 7

Для Windows 7 есть отдельная сборка ZapretGUI-Win7.exe (Python 3.8 и Qt 5.15: PySide6 на Windows 7 не запускается), она лежит в тех же релизах. Что ещё нужно:

    Windows 7 SP1 x64 с обновлениями KB3033929 и KB4474419 (подпись драйверов SHA-2).

    В release\bin заменить WinDivert.dll и WinDivert64.sys файлами из папки win7 репозитория bol-van/zapret-win-bundle.

Работу zapret на Windows 7 гарантировать нельзя: набор Flowseal рассчитан на Windows 10/11. Приложение при обновлении само берёт файл ZapretGUI-Win7.exe.

Если антивирус ругается на свежескачанный .exe, добавь папку установки в исключения: программы на PyInstaller и драйвер WinDivert часто попадают под ложные срабатывания.
Обновления и откат

Ещё → Приложение: проверка новой версии, выбор канала (стабильные или пререлизы), установка любой версии из списка релизов. Перед обновлением текущая версия сохраняется в app_backup, и на неё можно вернуться кнопкой «Откатиться на выбранную».
Запуск из исходников
bash

python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe main.py

Сборка .exe и установщика: build.bat (нужны Python и Inno Setup 6). Для Windows 7: build-win7.bat (нужен Python 3.8 x64).
Выпуск новой версии

Проще всего скриптом: подними VERSION в version.py, допиши CHANGELOG.md и запусти publish.bat. Он сделает коммит, отправит его в main и создаст тег v<версия>.

## Локальная сборка из исходников

Для самостоятельной сборки `.exe` и установщика установите:

1. **Python 3.11 x64** — [скачать с python.org](https://www.python.org/downloads/windows/) *(при установке обязательно отметьте галочку **Add Python to PATH**)*.
2. **Inno Setup 6** — [скачать с jrsoftware.org](https://jrsoftware.org) или установить через терминал:
   ```powershell
   winget install JRSoftware.InnoSetup
   ```
3. **Git for Windows** — [скачать с git-scm.com](https://git-scm.com/download/win).



Лицензия

MIT
Обновление интерфейса 1.0.2.2

    Обновлены элементы управления, визуальное оформление и отображение статуса в основном окне (main.py).

    Улучшена общая стабильность работы и адаптивность интерфейса на разных разрешениях экрана.

    Актуализирована версия приложения и конфигурация сборки (v1.0.2.2).
