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
  <img src="assets/banner.png" alt="Zapret GUI Banner" width="100%">
**Zapret GUI** — удобная графическая оболочка для Windows, позволяющая управлять работой `zapret` без необходимости вручную редактировать батники и конфигурационные файлы.

### Основные возможности:
* Запуск, остановка и перезапуск службы/процесса `zapret`.
* Удобное переключение между профилями и стратегиями обхода.
* Гибкая настройка параметров приложения.
* Встроенная проверка и установка обновлений через GitHub Releases.

---

## Скриншоты интерфейса

<div align="center">
  <img src="zapret-gui-v1.0.2.png" alt="Главное окно Zapret GUI" width="42%">
  &nbsp;&nbsp;
  <img src="zapret-gui-v1.0.2%5B2%5D.png" alt="Настройки Zapret GUI" width="72%">
</div>





## Установка готовой версии

1. Перейдите в раздел **[Releases](https://github.com)** этого репозитория.
2. Скачайте файл `ZapretGUI-Setup.exe` из последнего релиза.
3. Запустите установщик и следуйте инструкциям на экране (при запросе предоставьте права администратора).

> **Примечание:** Для работы встроенного автообновления в настройках приложения укажите репозиторий в формате `trianglenk/Zapret-GUI`.

---

## Локальная сборка из исходников

Для самостоятельной сборки `.exe` и установщика установите:

1. **Python 3.11 x64** — [скачать с python.org](https://www.python.org/downloads/windows/) *(при установке обязательно отметьте галочку **Add Python to PATH**)*.
2. **Inno Setup 6** — [скачать с jrsoftware.org](https://jrsoftware.org) или установить через терминал:
   ```powershell
   winget install JRSoftware.InnoSetup
   ```
3. **Git for Windows** — [скачать с git-scm.com](https://git-scm.com/download/win).

### Процесс сборки:
1. Клонируйте репозиторий или скачайте исходный код.
2. Откройте папку проекта и запустите `build.bat`.
3. Дождитесь завершения — готовый установщик появится в папке `installer/ZapretGUI-Setup.exe`.

---

## Публикация новой версии (для разработчика)

В репозитории настроен GitHub Actions (`.github/workflows/release.yml`), который автоматически собирает релиз при отправке тега версии:

1. Убедитесь, что в настройках репозитория (**Settings → Actions → General → Workflow permissions**) выбрано **Read and write permissions**.
2. Создайте и отправьте тег версии из папки проекта:
   ```powershell
   git tag v1.0.2
   git push origin v1.0.2
   ```

GitHub Actions автоматически возьмёт номер версии из тега, соберёт `ZapretGUI.exe`, упакует его в `ZapretGUI-Setup.exe` и опубликует релиз в разделе **Releases**.

---

## Структура проекта

* `main.py` — графический интерфейс приложения.
* `core.py` — основная логика работы с `zapret`.
* `version.py` — информация о текущей версии (**1.0.2**).
* `requirements.txt` — список зависимостей Python.

```powershell
git clone https://github.com/trianglenk/Zapret-GUI.git
cd Zapret-GUI
build.bat
