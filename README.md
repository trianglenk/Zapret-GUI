 <div align="center">
  <img src="assets/icon.png" alt="лого" width="70%">
</div>
# Zapret GUI

**Графическая оболочка для Windows для управления `zapret` без ручного редактирования батников и конфигов.**

![Platform](https://img.shields.io/badge/Platform-Windows-blue)
![Python](https://img.shields.io/badge/Python-3.11-yellow)
![Version](https://img.shields.io/badge/Version-1.0.2-green)

## Возможности
 <div align="center">
  <img src="assets/banner.png" alt="бан" width="60%">
</div>


- Запуск, остановка и перезапуск службы/процесса `zapret`.
- Переключение профилей и стратегий обхода.
- Настройка параметров приложения.
- Проверка и установка обновлений через GitHub Releases.

## Скриншоты

<div align="center">
  <img src="screenshots/main.png" alt="Главное окно" width="48%">
  <img src="screenshots/settings.png" alt="Настройки" width="48%">
</div>

## Установка

1. Откройте **[Releases](https://github.com/trianglenk/Zapret-GUI/releases)**.
2. Скачайте `ZapretGUI-Setup.exe` из последнего релиза.
3. Запустите установщик от имени администратора и следуйте инструкциям.

> Для автообновления укажите в настройках репозиторий: `trianglenk/Zapret-GUI`.

## Сборка из исходников

Установите:

1. **Python 3.11 x64** — [python.org](https://www.python.org/downloads/windows/)  
   При установке включите **Add Python to PATH**.
2. **Inno Setup 6** — [jrsoftware.org](https://jrsoftware.org) или:
   ```powershell
   winget install JRSoftware.InnoSetup
