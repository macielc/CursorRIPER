# Instalar MacTester Web como Servico Windows
# Requer: NSSM (Non-Sucking Service Manager)
# Download: https://nssm.cc/download

param(
    [switch]$Uninstall,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Restart,
    [switch]$Status
)

$ServiceName = "MacTesterWeb"
$AppPath = "C:\mactester-web\backend"
$PythonExe = "python.exe"  # Ou caminho completo: C:\Python311\python.exe
$AppScript = "app\main.py"

# Verificar se eh admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERRO: Execute como Administrador!" -ForegroundColor Red
    exit 1
}

# Funcoes
function Install-Service {
    Write-Host "Instalando servico $ServiceName..." -ForegroundColor Green
    
    # Verificar se NSSM esta instalado
    $nssmPath = Get-Command nssm -ErrorAction SilentlyContinue
    
    if (-not $nssmPath) {
        Write-Host "NSSM nao encontrado. Instalando via Chocolatey..." -ForegroundColor Yellow
        
        # Tentar instalar via chocolatey
        if (Get-Command choco -ErrorAction SilentlyContinue) {
            choco install nssm -y
        } else {
            Write-Host "ERRO: Chocolatey nao instalado." -ForegroundColor Red
            Write-Host "Instale NSSM manualmente de: https://nssm.cc/download" -ForegroundColor Yellow
            Write-Host "E adicione ao PATH" -ForegroundColor Yellow
            exit 1
        }
    }
    
    # Remover servico se ja existir
    $existing = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Servico ja existe. Removendo..." -ForegroundColor Yellow
        nssm stop $ServiceName
        nssm remove $ServiceName confirm
    }
    
    # Instalar servico
    Push-Location $AppPath
    
    nssm install $ServiceName $PythonExe $AppScript
    nssm set $ServiceName AppDirectory $AppPath
    nssm set $ServiceName DisplayName "MacTester Web Platform"
    nssm set $ServiceName Description "Plataforma web para gerenciamento de trading"
    nssm set $ServiceName Start SERVICE_AUTO_START
    
    # Configurar logs
    $LogPath = "$AppPath\logs"
    if (-not (Test-Path $LogPath)) {
        New-Item -ItemType Directory -Force -Path $LogPath | Out-Null
    }
    
    nssm set $ServiceName AppStdout "$LogPath\service-out.log"
    nssm set $ServiceName AppStderr "$LogPath\service-error.log"
    nssm set $ServiceName AppStdoutCreationDisposition 4
    nssm set $ServiceName AppStderrCreationDisposition 4
    
    # Configurar auto-restart
    nssm set $ServiceName AppExit Default Restart
    nssm set $ServiceName AppRestartDelay 5000
    
    Pop-Location
    
    Write-Host "Servico instalado com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para iniciar: Start-Service $ServiceName" -ForegroundColor Cyan
    Write-Host "Para parar:   Stop-Service $ServiceName" -ForegroundColor Cyan
    Write-Host "Status:       Get-Service $ServiceName" -ForegroundColor Cyan
}

function Uninstall-Service {
    Write-Host "Removendo servico $ServiceName..." -ForegroundColor Yellow
    
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
    
    Write-Host "Servico removido!" -ForegroundColor Green
}

function Start-AppService {
    Write-Host "Iniciando servico..." -ForegroundColor Green
    Start-Service $ServiceName
    Write-Host "Servico iniciado!" -ForegroundColor Green
    Get-Service $ServiceName
}

function Stop-AppService {
    Write-Host "Parando servico..." -ForegroundColor Yellow
    Stop-Service $ServiceName
    Write-Host "Servico parado!" -ForegroundColor Green
}

function Restart-AppService {
    Write-Host "Reiniciando servico..." -ForegroundColor Cyan
    Restart-Service $ServiceName
    Write-Host "Servico reiniciado!" -ForegroundColor Green
    Get-Service $ServiceName
}

function Get-ServiceStatus {
    Get-Service $ServiceName | Format-List
    
    Write-Host ""
    Write-Host "Logs:" -ForegroundColor Cyan
    Write-Host "  Out:   $AppPath\logs\service-out.log" -ForegroundColor White
    Write-Host "  Error: $AppPath\logs\service-error.log" -ForegroundColor White
}

# Main
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MACTESTER WEB - SERVICE MANAGER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

switch ($true) {
    $Uninstall { Uninstall-Service }
    $Start { Start-AppService }
    $Stop { Stop-AppService }
    $Restart { Restart-AppService }
    $Status { Get-ServiceStatus }
    default { Install-Service }
}

Write-Host ""
Write-Host "Concluido!" -ForegroundColor Green

