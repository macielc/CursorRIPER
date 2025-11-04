# 🖥️ DEPLOY MANUAL NO N150

Guia passo a passo para instalar MacTester no N150 do zero.

---

## 📋 PRÉ-REQUISITOS

- [ ] Acesso RDP/SSH ao N150
- [ ] Conexão com internet
- [ ] MT5 já instalado e funcionando

---

## 🚀 INSTALAÇÃO

### **PASSO 1: Abrir PowerShell como Administrador**

1. Pressione `Win + X`
2. Selecione "Windows PowerShell (Admin)"

---

### **PASSO 2: Instalar Chocolatey** (gerenciador de pacotes)

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

Aguarde a instalação (~2 minutos)

---

### **PASSO 3: Instalar Python**

```powershell
choco install python -y
refreshenv
python --version
```

Deve mostrar: `Python 3.13.x`

---

### **PASSO 4: Instalar Node.js**

```powershell
choco install nodejs -y
refreshenv
node --version
npm --version
```

Deve mostrar: `v20.x.x` e `10.x.x`

---

### **PASSO 5: Instalar Git**

```powershell
choco install git -y
refreshenv
git --version
```

Deve mostrar: `git version 2.x.x`

---

### **PASSO 6: Clonar Projeto**

```powershell
cd C:\
git clone https://github.com/macielc/CursorRIPER.git MacTester
cd MacTester\release_1.0
```

---

### **PASSO 7: Instalar Dependências Backend**

```powershell
cd web-platform\backend
pip install -r requirements.txt
```

Aguarde instalação (~5 minutos)

---

### **PASSO 8: Criar arquivo .env**

Crie `web-platform\backend\.env`:

```env
APP_NAME=MacTester Web Platform
APP_VERSION=1.0.0
DEBUG=False
HOST=0.0.0.0
PORT=8000

DATABASE_URL=sqlite:///./mactester.db

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

LOG_LEVEL=INFO
LOG_FILE=logs/backend.log

LIVE_TRADING_PATH=../../live_trading
STRATEGIES_PATH=../../live_trading/strategies
```

---

### **PASSO 9: Instalar Dependências Frontend**

```powershell
cd ..\frontend
npm install
```

Aguarde instalação (~3 minutos)

---

### **PASSO 10: Build Produção Frontend**

```powershell
npm run build
```

Aguarde build (~1 minuto)

Deve criar pasta `dist/`

---

### **PASSO 11: Testar Backend**

```powershell
cd ..\backend
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Abra navegador: `http://localhost:8000`

Deve mostrar: `{"app":"MacTester Web Platform","version":"1.0.0","status":"online"}`

Pressione `Ctrl + C` para parar

---

### **PASSO 12: Testar Integração Completa**

```powershell
# Terminal 1 (Backend)
cd C:\MacTester\release_1.0\web-platform\backend
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Abra navegador: http://localhost:8000
```

Deve abrir a interface web completa!

---

## ✅ VALIDAÇÃO

### **Checklist:**

- [ ] Backend responde em `http://localhost:8000`
- [ ] Interface web carrega
- [ ] Menu lateral aparece (Dashboard, Estratégias, Monitor, Histórico)
- [ ] Página "Monitor" abre
- [ ] Badge "WS Conectado" está verde
- [ ] Status mostra "Parado"
- [ ] Botão "Iniciar" está habilitado

---

## 🧪 TESTAR COM MT5

### **1. Verificar MT5**

1. Abra o MetaTrader 5
2. Certifique-se de estar logado
3. Verifique se símbolo WIN$ está disponível

### **2. Testar Conexão**

```powershell
cd C:\MacTester\release_1.0\live_trading
python test_connection.py
```

Deve mostrar: `OK TODOS OS TESTES PASSARAM!`

### **3. Testar Monitor via Web**

1. Abra interface web: `http://localhost:8000`
2. Vá em "Monitor"
3. Clique em "Iniciar"
4. Status deve mudar para "Rodando"
5. Logs devem aparecer em tempo real

---

## 🔧 TROUBLESHOOTING

### **Problema: Python não encontrado**

```powershell
refreshenv
# Ou feche e abra novo PowerShell
```

### **Problema: npm não encontrado**

```powershell
refreshenv
# Ou feche e abra novo PowerShell
```

### **Problema: Git não encontrado**

```powershell
refreshenv
# Ou adicione manualmente ao PATH
```

### **Problema: Backend não inicia**

```powershell
# Verificar dependências
cd C:\MacTester\release_1.0\web-platform\backend
pip list

# Verificar se falta alguma
pip install -r requirements.txt --upgrade
```

### **Problema: Frontend não carrega**

```powershell
# Rebuild
cd C:\MacTester\release_1.0\web-platform\frontend
npm run build
```

---

## 📞 PRÓXIMOS PASSOS

Após tudo funcionando:

1. ✅ Configurar como serviço Windows (auto-start)
2. ✅ Setup backup automático
3. ✅ Instalar VPN (Tailscale)
4. ✅ Validar em dry-run por 1 dia
5. ✅ Considerar produção

---

**Tempo total estimado:** 30-40 minutos

**Boa sorte!** 🚀

