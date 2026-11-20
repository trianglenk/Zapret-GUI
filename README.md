<div align="center">
  <img src="assets/icon.png" alt="Zapret GUI Icon" width="120">
  
  # Zapret GUI
  
  **Удобная графическая оболочка для управления `zapret` в Windows**

<div align="center">

| 🪟 **Windows 10/11 (x64)** | 🐍 **Python 3.11** | 🏷️ **Version 1.0.2** | ⚖️ **MIT License** |
| :---: | :---: | :---: | :---: |

</div>






---

## О приложении

# Zapret GUI

<div align="center">
  <img src="assets/banner.png" alt="Zapret GUI" width="100%">
</div>

<br>

**Zapret GUI** — графический интерфейс для Windows, упрощающий управление `zapret`: запуск, остановка, переключение профилей и обновление без ручного редактирования `.bat`-файлов и конфигураций.

## Возможности

- **Управление** — быстрый запуск, остановка и перезапуск службы или процесса.
- **Профили** — переключение между готовыми стратегиями обхода.
- **Настройка** — изменение параметров прямо из интерфейса.
- **Автообновление** — проверка и установка свежих версий через GitHub Releases.

---

## Скриншоты

<div align="center">
  <img src="screenshots/main.png" alt="Главное окно" width="48%">
  <img src="screenshots/settings.png" alt="Настройки" width="48%">
</div>

---

## Установка

1. Откройте раздел **[Releases](https://github.com/trianglenk/Zapret-GUI/releases)**.
2. Скачайте `ZapretGUI-Setup.exe` (или архив с программой) из последнего релиза.
3. Запустите установщик и следуйте инструкциям *(потребуются права администратора)*.

> **Совет:** для работы автообновления укажите в настройках репозиторий `trianglenk/Zapret-GUI`.

---

## Сборка из исходников

Понадобятся:

| Компонент | Ссылка |
| :--- | :--- |
| Python 3.11 (x64) | [python.org](https://www.python.org/downloads/windows/) *(отметьте **Add Python to PATH**)* |
| Inno Setup 6 | [jrsoftware.org](https://jrsoftware.org) или `winget install JRSoftware.InnoSetup` |
| Git for Windows | [git-scm.com](https://git-scm.com/download/win) |

```powershell
git clone https://github.com/trianglenk/Zapret-GUI.git
cd Zapret-GUI
build.bat
