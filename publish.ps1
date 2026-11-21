# Публикация проекта на GitHub и выпуск релиза.
# Запуск: двойной щелчок по publish.bat
# Что делает: коммитит изменения, отправляет их в main и создаёт тег v<VERSION> (версия берётся из version.py).
# Тег запускает GitHub Actions: они соберут ZapretGUI.exe (и версию для Windows 7) и опубликуют релиз.
param([string]$Message = "")
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Repo = "https://github.com/trianglenk/Zapret-GUI.git"

function Fail($text) {
    Write-Host ""
    Write-Host "ОШИБКА: $text" -ForegroundColor Red
    exit 1
}
function Run($cmd) {
    Write-Host "> $cmd" -ForegroundColor DarkGray
    Invoke-Expression $cmd
    if ($LASTEXITCODE -ne 0) { Fail "команда завершилась с ошибкой: $cmd" }
}

# --- версия из version.py ---
$line = Select-String -Path "version.py" -Pattern 'VERSION\s*=\s*"([^"]+)"' | Select-Object -First 1
if (-not $line) { Fail "в version.py не найдена строка VERSION" }
$version = $line.Matches[0].Groups[1].Value
$tag = "v$version"
Write-Host "Версия: $version, тег: $tag" -ForegroundColor Cyan

# --- Git ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git не найден, ставлю через winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    Fail "Git установлен. Закрой это окно и запусти publish.bat ещё раз (PATH обновится только в новом окне)."
}
if (-not (git config user.name)) {
    $n = Read-Host "Имя для коммитов (например, trianglenk)"
    git config --global user.name $n
}
if (-not (git config user.email)) {
    $e = Read-Host "Почта для коммитов"
    git config --global user.email $e
}

# --- репозиторий ---
if (-not (Test-Path ".git")) {
    Run "git init"
    Run "git branch -M main"
}
if ((git remote) -contains "origin") { Run "git remote set-url origin $Repo" } else { Run "git remote add origin $Repo" }

# --- коммит и отправка ---
Run "git add -A"
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    $msg = if ($Message) { $Message } else { "Zapret GUI $version" }
    Run "git commit -m `"$msg`""
} else {
    Write-Host "Новых изменений нет, коммит не нужен." -ForegroundColor Yellow
}
Run "git push -u origin main"

# --- тег = релиз ---
$remoteTag = git ls-remote --tags origin $tag
if ($remoteTag) {
    Write-Host ""
    Write-Host "Тег $tag уже есть на GitHub, значит релиз с этой версией уже выпускался." -ForegroundColor Yellow
    Write-Host "Чтобы выпустить новый, увеличь VERSION в version.py и запусти скрипт снова." -ForegroundColor Yellow
} else {
    if (-not (git tag -l $tag)) { Run "git tag $tag" }
    Run "git push origin $tag"
    Write-Host ""
    Write-Host "Готово. Релиз $tag собирается: https://github.com/trianglenk/Zapret-GUI/actions" -ForegroundColor Green
}
