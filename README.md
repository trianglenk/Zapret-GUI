# Zapret GUI

Windows-приложение с графическим интерфейсом для управления zapret.

## Что нужно установить для локальной сборки

1. **Python 3.11 x64** — https://www.python.org/downloads/windows/
   Во время установки включите `Add Python to PATH`.
2. **Inno Setup 6** — `winget install JRSoftware.InnoSetup`
3. **Git for Windows** — https://git-scm.com/download/win

После установки откройте папку проекта и запустите `build.bat`.
Готовый установщик появится в `installer/ZapretGUI-Setup.exe`.

## Публикация на GitHub

1. Создайте пустой репозиторий на GitHub.
2. Загрузите в него всё содержимое этой папки, включая `.github/workflows/release.yml`.
3. В GitHub откройте **Settings → Actions → General** и разрешите Actions создавать Releases
   (обычно достаточно `Read and write permissions` для workflow).
4. Создайте и отправьте тег версии из папки проекта:

   ```powershell
   git tag v1.0.6
   git push origin v1.0.6
   ```

GitHub Actions автоматически:
- возьмёт номер версии из тега;
- соберёт `ZapretGUI.exe`;
- создаст `ZapretGUI-Setup.exe`;
- опубликует GitHub Release с установщиком.

Важно: в настройках приложения укажите репозиторий в формате `владелец/имя`.
После публикации следующего Release кнопка «Проверить обновление» найдёт его.
Для работы автообновления в Assets релиза должен присутствовать `ZapretGUI-Setup.exe`.

## Скриншоты и иконка

- `icon.ico` — иконка Windows-приложения и установщика.
- `icon.png` — исходное изображение иконки.
- `screenshots/` — папка для скриншотов; они необязательны для сборки.

## Версия

Текущая версия исходного проекта: **1.0.5**.
Версия отображается внизу страницы «Настройки».
