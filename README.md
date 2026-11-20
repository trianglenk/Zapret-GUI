<div align="center">
  <img src="assets/icon.png" alt="Zapret GUI Icon" width="120">
  
  # Zapret GUI
  
  **Удобная графическая оболочка для управления `zapret` в Windows**

<div align="center">
  <h2>
    <kbd>🪟 Windows 10/11 (x64)</kbd> &nbsp;
    <kbd>🐍 Python 3.11</kbd> &nbsp;
    <kbd>🏷️ Version 1.0.2</kbd> &nbsp;
    <kbd>⚖️ MIT License</kbd>
  </h2>
</div>





---

## О приложении

<div align="center">
  <img src="assets/banner.png" alt="Zapret GUI Banner" width="100%">
</div>

<br>

**Zapret GUI** — приложение с графическим интерфейсом для Windows, позволяющее управлять работой `zapret` без необходимости вручную редактировать `.bat`-файлы и конфигурации.

### Основные возможности
* **Управление работой:** быстрый запуск, остановка и перезапуск службы или процесса `zapret`.
* **Гибкие профили:** удобное переключение между готовыми профилями и стратегиями обхода.
* **Тонкая настройка:** изменение параметров работы программы прямо из интерфейса.
* **Автообновление:** встроенная проверка и установка свежих версий через GitHub Releases.

---

## Скриншоты интерфейса

<div align="center">
  <img src="screenshots/main.png" alt="Главное окно Zapret GUI" width="48%">
  <img src="screenshots/settings.png" alt="Настройки Zapret GUI" width="48%">
</div>

---

## Установка готовой версии

1. Перейдите в раздел **[Releases](https://github.com)** этого репозитория.
2. Скачайте файл `ZapretGUI-Setup.exe` (или архив с программой) из последнего релиза.
3. Запустите установщик и следуйте инструкциям на экране *(при запросе предоставьте права администратора)*.

> **Совет:** Для работы встроенного автообновления укажите в настройках приложения репозиторий в формате `trianglenk/Zapret-GUI`.

---

## Локальная сборка из исходников

Для самостоятельной сборки `.exe` и установщика вам понадобятся:

1. **Python 3.11 (x64)** — [скачать с python.org](https://www.python.org/downloads/windows/) *(при установке обязательно отметьте галочку **Add Python to PATH**)*.
2. **Inno Setup 6** — [скачать с jrsoftware.org](https://jrsoftware.org) или установить через PowerShell:
   ```powershell
   winget install JRSoftware.InnoSetup
   ```
3. **Git for Windows** — [скачать с git-scm.com](https://git-scm.com/download/win).

### Инструкция по сборке
1. Клонируйте репозиторий или скачайте исходный код:
   ```powershell
   git clone https://github.com/trianglenk/Zapret-GUI.git
   cd Zapret-GUI
   ```
2. Запустите файл `build.bat`.
3. Дождитесь окончания сборки — готовый установщик появится по пути `installer/ZapretGUI-Setup.exe`.

---

## Публикация новой версии (для разработчика)

В репозитории настроен GitHub Actions (`.github/workflows/release.yml`), который автоматически собирает релиз при отправке тега:

1. Убедитесь, что в настройках репозитория (**Settings → Actions → General → Workflow permissions**) выбрано **Read and write permissions**.
2. Создайте и отправьте тег версии из папки проекта:
   ```powershell
   git tag v1.0.2
   git push origin v1.0.2
   ```

После этого GitHub Actions автоматически подставит номер версии из тега, соберёт `ZapretGUI.exe`, упакует его в `ZapretGUI-Setup.exe` и опубликует в разделе **Releases**.

---

## Структура проекта

| Файл / Папка | Назначение |
| :--- | :--- |
| `main.py` | Графический интерфейс приложения |
| `core.py` | Основная логика взаимодействия с `zapret` |
| `version.py` | Информация о текущей версии (**1.0.2**) |
| `requirements.txt` | Список необходимых библиотек Python |
| `build.bat` | Скрипт автоматической локальной сборки |
| `installer.iss` | Сценарий создания установщика для Inno Setup |
| `assets/`, `icon.ico` | Баннер и иконки приложения |
| `screenshots/` | Скриншоты интерфейса для `README.md` |
