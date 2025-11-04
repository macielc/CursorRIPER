# Script para iniciar o frontend contornando problema do # no diretorio

# Obtem o diretorio do script
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navega para o diretorio do frontend
Set-Location $ScriptDir

Write-Host "Iniciando Vite dev server..." -ForegroundColor Green
Write-Host "Diretorio: $(Get-Location)" -ForegroundColor Cyan

# Inicia o npm run dev
npm run dev

