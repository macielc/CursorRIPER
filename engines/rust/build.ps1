# Script de build automatizado para motor Rust

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "MacTester Engine Rust - Build Script" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan
Write-Host ""

# Verificar se Rust esta instalado
Write-Host "[1/4] Verificando instalacao do Rust..." -ForegroundColor Yellow
$rustVersion = cargo --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Rust nao esta instalado!" -ForegroundColor Red
    Write-Host "Instale com: winget install --id Rustlang.Rustup" -ForegroundColor Yellow
    exit 1
}
Write-Host "OK: $rustVersion" -ForegroundColor Green
Write-Host ""

# Compilar em modo release
Write-Host "[2/4] Compilando motor Rust (release mode)..." -ForegroundColor Yellow
Write-Host "Isso pode levar alguns minutos na primeira vez..." -ForegroundColor Gray
cargo build --release
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Falha na compilacao!" -ForegroundColor Red
    exit 1
}
Write-Host "OK: Compilacao concluida!" -ForegroundColor Green
Write-Host ""

# Renomear .dll para .pyd e copiar para raiz do MacTester
Write-Host "[3/4] Copiando mactester_engine.pyd..." -ForegroundColor Yellow
$dllFile = "target\release\mactester_engine.dll"
if (Test-Path $dllFile) {
    # Renomear .dll para .pyd
    $pydFile = "target\release\mactester_engine.pyd"
    Copy-Item $dllFile $pydFile -Force
    
    # Copiar para raiz
    Copy-Item $pydFile ..\ -Force
    Write-Host "OK: mactester_engine.pyd copiado para raiz do MacTester" -ForegroundColor Green
} else {
    Write-Host "ERRO: Arquivo .dll nao encontrado!" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Verificar tamanho
Write-Host "[4/4] Verificando arquivo gerado..." -ForegroundColor Yellow
$fileInfo = Get-Item ..\mactester_engine.pyd
$sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
Write-Host "OK: mactester_engine.pyd ($sizeMB MB)" -ForegroundColor Green
Write-Host ""

# Sucesso
Write-Host "="*80 -ForegroundColor Green
Write-Host "BUILD CONCLUIDO COM SUCESSO!" -ForegroundColor Green
Write-Host "="*80 -ForegroundColor Green
Write-Host ""
Write-Host "Para testar, execute:" -ForegroundColor Cyan
Write-Host "  python engine_rust\example_usage.py" -ForegroundColor White
Write-Host ""

