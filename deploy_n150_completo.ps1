# ================================================================================
# DEPLOY COMPLETO MACTESTER NO N150
# Script automatizado para instalacao do zero
# ================================================================================

$ErrorActionPreference = "Stop"

Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host "MACTESTER - DEPLOY COMPLETO NO N150" -ForegroundColor Cyan
Write-Host "=================================================================================" -ForegroundColor Cyan
Write-Host ""

# Configuracoes
$INSTALL_DIR = "C:\MacTester"
$REPO_URL = "https://github.com/macielc/CursorRIPER.git"
$PYTHON_VERSION = "3.13.0"
$NODE_VERSION = "20.18.1"

# ================================================================================
# FUNCOES AUXILIARES
# ================================================================================

function Write-Step {
    param($message)
    Write-Host ""
    Write-Host ">>> $message" -ForegroundColor Yellow
    Write-Host ""
}

function Write-Success {
    param($message)
    Write-Host "OK $message" -ForegroundColor Green
}

function Write-Error {
    param($message)
    Write-Host "ERRO $message" -ForegroundColor Red
}

function Test-Command {
    param($command)
    try {
        if (Get-Command $command -ErrorAction Stop) {
            return $true
        }
    } catch {
        return $false
    }
}

# ================================================================================
# PASSO 1: VERIFICAR PERMISSOES ADMIN
# ================================================================================

Write-Step "Verificando permissoes de administrador..."

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Error "Este script precisa ser executado como Administrador!"
    Write-Host "Clique com botao direito no PowerShell e selecione 'Executar como Administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Success "Executando como Administrador"

# ================================================================================
# PASSO 2: INSTALAR CHOCOLATEY (gerenciador de pacotes)
# ================================================================================

Write-Step "Instalando Chocolatey (gerenciador de pacotes)..."

if (Test-Command choco) {
    Write-Success "Chocolatey ja instalado"
} else {
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    if (Test-Command choco) {
        Write-Success "Chocolatey instalado"
    } else {
        Write-Error "Falha ao instalar Chocolatey"
        exit 1
    }
}

# ================================================================================
# PASSO 3: INSTALAR PYTHON
# ================================================================================

Write-Step "Instalando Python $PYTHON_VERSION..."

if (Test-Command python) {
    $pythonVer = python --version
    Write-Success "Python ja instalado: $pythonVer"
} else {
    choco install python -y --version=$PYTHON_VERSION
    refreshenv
    
    if (Test-Command python) {
        Write-Success "Python instalado"
    } else {
        Write-Error "Falha ao instalar Python"
        exit 1
    }
}

# ================================================================================
# PASSO 4: INSTALAR NODE.JS
# ================================================================================

Write-Step "Instalando Node.js $NODE_VERSION..."

if (Test-Command node) {
    $nodeVer = node --version
    Write-Success "Node.js ja instalado: $nodeVer"
} else {
    choco install nodejs -y --version=$NODE_VERSION
    refreshenv
    
    if (Test-Command node) {
        Write-Success "Node.js instalado"
    } else {
        Write-Error "Falha ao instalar Node.js"
        exit 1
    }
}

# ================================================================================
# PASSO 5: INSTALAR GIT
# ================================================================================

Write-Step "Instalando Git..."

if (Test-Command git) {
    $gitVer = git --version
    Write-Success "Git ja instalado: $gitVer"
} else {
    choco install git -y
    refreshenv
    
    if (Test-Command git) {
        Write-Success "Git instalado"
    } else {
        Write-Error "Falha ao instalar Git"
        exit 1
    }
}

# ================================================================================
# PASSO 6: CLONAR PROJETO
# ================================================================================

Write-Step "Clonando projeto do GitHub..."

if (Test-Path $INSTALL_DIR) {
    Write-Host "Diretorio $INSTALL_DIR ja existe" -ForegroundColor Yellow
    $resposta = Read-Host "Deseja sobrescrever? (s/n)"
    if ($resposta -eq "s") {
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
    } else {
        Write-Host "Usando diretorio existente..." -ForegroundColor Yellow
    }
}

if (-not (Test-Path $INSTALL_DIR)) {
    git clone $REPO_URL $INSTALL_DIR
    
    if (Test-Path $INSTALL_DIR) {
        Write-Success "Projeto clonado"
    } else {
        Write-Error "Falha ao clonar projeto"
        exit 1
    }
} else {
    Write-Success "Projeto ja existe"
}

# ================================================================================
# PASSO 7: INSTALAR DEPENDENCIAS PYTHON
# ================================================================================

Write-Step "Instalando dependencias Python (backend)..."

Set-Location "$INSTALL_DIR\release_1.0\web-platform\backend"

python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Success "Dependencias Python instaladas"

# ================================================================================
# PASSO 8: INSTALAR DEPENDENCIAS NODE
# ================================================================================

Write-Step "Instalando dependencias Node.js (frontend)..."

Set-Location "$INSTALL_DIR\release_1.0\web-platform\frontend"

npm install

Write-Success "Dependencias Node.js instaladas"

# ================================================================================
# PASSO 9: CRIAR ARQUIVO .ENV BACKEND
# ================================================================================

Write-Step "Criando arquivo de configuracao backend (.env)..."

Set-Location "$INSTALL_DIR\release_1.0\web-platform\backend"

if (-not (Test-Path ".env")) {
    @"
# MacTester Backend Config
APP_NAME=MacTester Web Platform
APP_VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./mactester.db

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/backend.log

# Paths
LIVE_TRADING_PATH=../../live_trading
STRATEGIES_PATH=../../live_trading/strategies
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Success "Arquivo .env criado"
} else {
    Write-Success "Arquivo .env ja existe"
}

# ================================================================================
# PASSO 10: BUILD FRONTEND (PRODUCAO)
# ================================================================================

Write-Step "Fazendo build de producao do frontend..."

Set-Location "$INSTALL_DIR\release_1.0\web-platform\frontend"

npm run build

if (Test-Path "dist") {
    Write-Success "Frontend build completo"
} else {
    Write-Error "Falha ao fazer build do frontend"
    exit 1
}

# ================================================================================
# PASSO 11: TESTAR BACKEND
# ================================================================================

Write-Step "Testando backend (5 segundos)..."

Set-Location "$INSTALL_DIR\release_1.0\web-platform\backend"

$backendJob = Start-Job -ScriptBlock {
    param($dir)
    Set-Location $dir
    $env:PYTHONPATH = "."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
} -ArgumentList (Get-Location)

Start-Sleep -Seconds 5

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Success "Backend funcionando"
    }
} catch {
    Write-Error "Backend nao respondeu"
}

Stop-Job $backendJob
Remove-Job $backendJob

# ================================================================================
# PASSO 12: CRIAR SCRIPT DE INICIALIZACAO
# ================================================================================

Write-Step "Criando scripts de inicializacao..."

# Script para iniciar backend
$backendScript = @"
`$env:PYTHONPATH = "."
Set-Location "$INSTALL_DIR\release_1.0\web-platform\backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
"@

$backendScript | Out-File -FilePath "$INSTALL_DIR\release_1.0\start_backend.ps1" -Encoding UTF8

# Script para iniciar tudo
$startScript = @"
Write-Host "Iniciando MacTester..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-File", "$INSTALL_DIR\release_1.0\start_backend.ps1"
Write-Host "Backend iniciado na porta 8000" -ForegroundColor Green
Write-Host "Acesse: http://localhost:8000" -ForegroundColor Yellow
"@

$startScript | Out-File -FilePath "$INSTALL_DIR\release_1.0\START_MACTESTER.ps1" -Encoding UTF8

Write-Success "Scripts criados"

# ================================================================================
# PASSO 13: CRIAR ATALHO NA AREA DE TRABALHO
# ================================================================================

Write-Step "Criando atalho na area de trabalho..."

$desktopPath = [Environment]::GetFolderPath("Desktop")
$shortcutPath = "$desktopPath\MacTester.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$INSTALL_DIR\release_1.0\START_MACTESTER.ps1`""
$shortcut.WorkingDirectory = "$INSTALL_DIR\release_1.0"
$shortcut.Description = "MacTester Web Platform"
$shortcut.Save()

Write-Success "Atalho criado na area de trabalho"

# ================================================================================
# RESUMO FINAL
# ================================================================================

Write-Host ""
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host "INSTALACAO COMPLETA!" -ForegroundColor Green
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Instalado em: $INSTALL_DIR" -ForegroundColor Cyan
Write-Host ""
Write-Host "COMO USAR:" -ForegroundColor Yellow
Write-Host "  1. Clique duas vezes no atalho 'MacTester' na area de trabalho" -ForegroundColor White
Write-Host "  2. Aguarde o backend iniciar" -ForegroundColor White
Write-Host "  3. Abra navegador: http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "OU execute manualmente:" -ForegroundColor Yellow
Write-Host "  powershell -File '$INSTALL_DIR\release_1.0\START_MACTESTER.ps1'" -ForegroundColor White
Write-Host ""
Write-Host "PROXIMO PASSO:" -ForegroundColor Yellow
Write-Host "  Testar integracao com MT5!" -ForegroundColor White
Write-Host ""
Write-Host "=================================================================================" -ForegroundColor Green
Write-Host ""

pause

