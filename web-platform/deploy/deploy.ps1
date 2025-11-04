# Script de Deploy - MacTester Web Platform
# Deploy via SSH/Git para maquina N150

param(
    [string]$RemoteHost = "",  # IP da maquina N150
    [string]$RemoteUser = "",  # Usuario SSH
    [string]$RemotePath = "C:\mactester-web",  # Path no N150
    [switch]$BuildOnly,  # Apenas build local
    [switch]$DeployOnly,  # Apenas deploy (sem build)
    [switch]$InstallDeps  # Instalar dependencias no remoto
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MACTESTER WEB PLATFORM - DEPLOY SCRIPT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Validar parametros
if (-not $BuildOnly -and (-not $RemoteHost -or -not $RemoteUser)) {
    Write-Host "ERRO: Especifique -RemoteHost e -RemoteUser para deploy" -ForegroundColor Red
    Write-Host "Uso: .\deploy.ps1 -RemoteHost 192.168.1.X -RemoteUser usuario" -ForegroundColor Yellow
    Write-Host "Ou:  .\deploy.ps1 -BuildOnly (apenas build local)" -ForegroundColor Yellow
    exit 1
}

# Step 1: Build Frontend
if (-not $DeployOnly) {
    Write-Host "[1/5] Building Frontend..." -ForegroundColor Green
    
    Push-Location ../frontend
    
    if (-not (Test-Path "node_modules")) {
        Write-Host "Instalando dependencias npm..." -ForegroundColor Yellow
        npm install
    }
    
    Write-Host "Rodando build..." -ForegroundColor Yellow
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: Build do frontend falhou!" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
    Write-Host "Frontend build OK!" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Preparar backend
if (-not $DeployOnly) {
    Write-Host "[2/5] Preparando Backend..." -ForegroundColor Green
    
    # Verificar requirements.txt
    if (-not (Test-Path "../backend/requirements.txt")) {
        Write-Host "ERRO: requirements.txt nao encontrado!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Backend OK!" -ForegroundColor Green
    Write-Host ""
}

# Step 3: Commit para Git (se tiver mudancas)
if (-not $BuildOnly) {
    Write-Host "[3/5] Verificando Git..." -ForegroundColor Green
    
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "Ha mudancas nao commitadas. Deseja commitar? (y/n)" -ForegroundColor Yellow
        $commit = Read-Host
        
        if ($commit -eq "y") {
            git add .
            $commitMsg = Read-Host "Mensagem do commit"
            git commit -m "$commitMsg"
            git push
            Write-Host "Push para repositorio OK!" -ForegroundColor Green
        }
    } else {
        Write-Host "Nenhuma mudanca para commitar" -ForegroundColor Gray
    }
    Write-Host ""
}

# Step 4: Deploy via SSH
if (-not $BuildOnly) {
    Write-Host "[4/5] Deploy para $RemoteHost..." -ForegroundColor Green
    
    # Criar diretorio remoto se nao existir
    Write-Host "Criando diretorio remoto..." -ForegroundColor Yellow
    ssh $RemoteUser@$RemoteHost "mkdir -p $RemotePath"
    
    # Copiar arquivos via SCP
    Write-Host "Copiando arquivos..." -ForegroundColor Yellow
    
    # Backend
    scp -r ../backend/* $RemoteUser@$RemoteHost:$RemotePath/backend/
    
    # Frontend (dist)
    scp -r ../frontend/dist $RemoteUser@$RemoteHost:$RemotePath/frontend/
    
    # Scripts
    scp -r ../deploy/install_service.ps1 $RemoteUser@$RemoteHost:$RemotePath/
    
    Write-Host "Arquivos copiados!" -ForegroundColor Green
    Write-Host ""
    
    # Step 5: Setup remoto
    Write-Host "[5/5] Setup remoto..." -ForegroundColor Green
    
    if ($InstallDeps) {
        Write-Host "Instalando dependencias Python..." -ForegroundColor Yellow
        ssh $RemoteUser@$RemoteHost "cd $RemotePath/backend && pip install -r requirements.txt"
    }
    
    Write-Host "Setup completo!" -ForegroundColor Green
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DEPLOY CONCLUIDO!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Proximos passos no servidor N150:" -ForegroundColor Yellow
Write-Host "1. SSH para o servidor: ssh $RemoteUser@$RemoteHost" -ForegroundColor White
Write-Host "2. Ir para: cd $RemotePath" -ForegroundColor White
Write-Host "3. Instalar servico: .\install_service.ps1" -ForegroundColor White
Write-Host "4. Iniciar: Start-Service MacTesterWeb" -ForegroundColor White
Write-Host ""
Write-Host "Acesso: http://${RemoteHost}:8000" -ForegroundColor Cyan

