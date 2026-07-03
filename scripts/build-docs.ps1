# Genera site/ y site.zip para Vercel Drop.
# Uso desde la raiz del proyecto:
#   .\scripts\build-docs.ps1
# O doble clic en build-docs.bat

$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $ProjectRoot

Write-Host ""
Write-Host "=== Build documentacion ===" -ForegroundColor Cyan
Write-Host "Directorio: $ProjectRoot"
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: python no esta en el PATH." -ForegroundColor Red
    Write-Host "Instala Python o activa el venv antes de continuar."
    exit 1
}

if (-not (Test-Path "requirements-docs.txt")) {
    Write-Host "ERROR: ejecuta esto desde la raiz del proyecto agent_femturisme." -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] Instalando mkdocs..." -ForegroundColor Yellow
python -m pip install -r requirements-docs.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: pip install fallo." -ForegroundColor Red
    exit 1
}

Write-Host "[2/3] Generando site/ ..." -ForegroundColor Yellow
python -m mkdocs build --clean
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: mkdocs build fallo." -ForegroundColor Red
    exit 1
}

$sitePath = Join-Path $ProjectRoot "site"
if (-not (Test-Path $sitePath)) {
    Write-Host "ERROR: no se creo la carpeta site." -ForegroundColor Red
    exit 1
}

$fileCount = (Get-ChildItem $sitePath -Recurse -File).Count
$zipPath = Join-Path $ProjectRoot "site.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $sitePath -DestinationPath $zipPath

Write-Host "[3/3] Listo." -ForegroundColor Green
Write-Host ""
Write-Host "  $sitePath  ($fileCount archivos)"
Write-Host "  $zipPath"
Write-Host ""
Write-Host "Vercel Drop: https://vercel.com/drop" -ForegroundColor Yellow
Write-Host "  Arrastra la carpeta 'site' O el archivo 'site.zip'"
Write-Host "  NO arrastres todo el proyecto."
Write-Host ""
Write-Host "Vista previa: python -m mkdocs serve" -ForegroundColor DarkGray
Write-Host ""
