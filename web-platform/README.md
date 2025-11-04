# MACTESTER WEB PLATFORM

Plataforma web para gerenciamento e monitoramento do sistema de live trading MacTester.

---

## VISAO GERAL

Interface web acessivel via navegador para:
- Gerenciar estrategias de trading
- Monitorar execucao em tempo real
- Visualizar ordens e performance
- Controlar parametros e configuracoes
- Acessar historico e relatorios

---

## ARQUITETURA

```
web-platform/
├── backend/          # FastAPI + SQLite + WebSocket
├── frontend/         # React + Ant Design + TradingView
├── deploy/           # Scripts de deploy e servico
└── docs/             # Documentacao
```

**Stack:**
- Backend: Python 3.8+, FastAPI, SQLAlchemy, WebSocket
- Frontend: React 18, Ant Design, Vite, TradingView Charts
- Database: SQLite
- Deploy: Windows nativo (servico Windows via NSSM)

---

## INSTALACAO

### Requisitos

**Maquina de desenvolvimento (onde estamos agora):**
- Python 3.8+
- Node.js 18+
- Git

**Maquina N150 (servidor):**
- Windows 11
- Python 3.8+
- Git
- SSH habilitado
- NSSM (instalado via Chocolatey ou manual)

### Setup Local (Dev)

```powershell
# 1. Backend
cd backend
pip install -r requirements.txt
python app/main.py

# 2. Frontend (terminal separado)
cd frontend
npm install
npm run dev

# Acessa: http://localhost:3000
```

### Deploy para N150

```powershell
cd deploy

# Deploy completo
.\deploy.ps1 -RemoteHost 192.168.1.X -RemoteUser usuario -InstallDeps

# Apenas build local
.\deploy.ps1 -BuildOnly
```

**No servidor N150 (via SSH):**

```powershell
cd C:\mactester-web

# Instalar como servico Windows
.\install_service.ps1

# Iniciar servico
Start-Service MacTesterWeb

# Verificar status
Get-Service MacTesterWeb

# Logs
tail -f logs/backend.log
```

---

## ACESSO

### Rede Local
```
http://192.168.1.X:8000
```

### Acesso Externo (VPN)

**Recomendacao: Tailscale** (VPN automatica)

1. Instalar Tailscale no N150 e nos devices que vao acessar
2. Criar conta em https://tailscale.com
3. Devices na mesma rede Tailscale podem acessar via IP Tailscale

```
http://100.x.x.x:8000  # IP Tailscale do N150
```

**Alternativa: Port Forwarding** (menos seguro)
- Configurar router para encaminhar porta 8000 para IP do N150
- Usar DynDNS se IP publico for dinamico
- SEMPRE usar HTTPS (certificado Let's Encrypt)

---

## DESENVOLVIMENTO

### Backend

```powershell
cd backend

# Rodar em modo dev (auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Criar migracao (se alterar models)
alembic revision --autogenerate -m "descricao"
alembic upgrade head

# Testes
pytest
```

**Endpoints principais:**
- `GET /api/strategies` - Listar estrategias
- `POST /api/strategies` - Criar estrategia
- `GET /api/orders` - Listar ordens
- `GET /api/orders/stats/summary` - Estatisticas
- `WS /ws` - WebSocket real-time

### Frontend

```powershell
cd frontend

# Dev server
npm run dev

# Build producao
npm run build

# Preview build
npm run preview
```

**Estrutura de componentes:**
- `pages/` - Paginas principais (Dashboard, Strategies, Monitor, etc)
- `components/` - Componentes reutilizaveis
- `services/` - API calls e WebSocket
- `hooks/` - Custom React hooks
- `utils/` - Utilidades

---

## CONFIGURACAO

### Backend (.env)

```env
# App
DEBUG=False
HOST=0.0.0.0
PORT=8000

# Database
DATABASE_URL=sqlite:///./mactester.db

# Live Trading
LIVE_TRADING_PATH=../live_trading

# Security
SECRET_KEY=trocar-em-producao

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id
```

### Frontend (vite.config.js)

```javascript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

---

## BACKUP

Backup automatico configurado em `backend/app/services/backup_service.py`:

- **Configs**: Diario
- **Database**: A cada trade
- **Logs**: Semanal
- **Retencao**: 30 dias

Backups salvos em: `backend/backups/`

---

## MONITORAMENTO

### Logs

```powershell
# Backend
tail -f backend/logs/backend.log

# Servico Windows
tail -f C:\mactester-web\logs\service-out.log
tail -f C:\mactester-web\logs\service-error.log

# Live trading (integrado)
tail -f ../live_trading/logs/monitor.log
```

### Metricas

Dashboard web mostra:
- Status do monitor
- Saldo e margem MT5
- PnL do dia
- Trades executados
- Posicoes abertas
- Grafico de equity

---

## TROUBLESHOOTING

### Backend nao inicia

```powershell
# Verificar se porta esta ocupada
netstat -ano | findstr :8000

# Ver logs
cat backend/logs/backend.log
```

### Frontend nao conecta

```powershell
# Verificar se backend esta rodando
curl http://localhost:8000/health

# Verificar proxy no vite.config.js
```

### Servico Windows nao inicia

```powershell
# Verificar status
Get-Service MacTesterWeb

# Ver logs do servico
cat C:\mactester-web\logs\service-error.log

# Reinstalar
.\install_service.ps1 -Uninstall
.\install_service.ps1
```

### WebSocket nao conecta

```powershell
# Verificar se WebSocket endpoint responde
wscat -c ws://localhost:8000/ws

# Verificar CORS no backend
```

---

## PROXIMOS PASSOS

Ver: `docs/IMPLEMENTATION_STATUS.md` para lista completa do que foi implementado e o que falta.

**Prioridades:**
1. Completar componentes React faltantes
2. Implementar integracao MT5 real
3. Testar em producao no N150
4. Configurar backup automatico
5. Adicionar autenticacao (se necessario)

---

## SUPORTE

- Documentacao: `docs/`
- Issues: GitHub
- Contato: [seu email]

---

**MacTester Web Platform v1.0.0**

