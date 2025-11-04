# PLAN - PLATAFORMA WEB MACTESTER
*Modo: PLAN (Omega_3) | Data: 2025-11-03*

## VISAO GERAL

Plataforma web para monitoramento e controle do sistema de live trading MacTester.
Interface acessivel via navegador para gerenciar estrategias, parametros, execucao e monitoramento em tempo real.

---

## OBJETIVOS

### Primarios
1. Interface web para selecionar e ativar estrategias
2. Painel de edicao de parametros dinamico por estrategia
3. Dashboard de monitoramento em tempo real
4. Controle de execucao (start/stop/pause)
5. Visualizacao de trades executados
6. Gestao de multiplos ativos simultaneamente

### Secundarios
1. Graficos de performance
2. Alertas e notificacoes
3. Logs em tempo real
4. Backtesting integrado
5. Gestao de risco configuravel
6. Historico de operacoes

---

## ARQUITETURA PROPOSTA

### Stack Tecnologico

**Backend:**
- Python (Flask ou FastAPI)
- WebSocket para dados em tempo real
- SQLite/PostgreSQL para persistencia
- Redis para cache e pub/sub

**Frontend:**
- React ou Vue.js
- TailwindCSS para UI
- Chart.js ou TradingView Lightweight Charts
- WebSocket client para real-time

**Infraestrutura:**
- Docker para containerizacao
- Nginx como reverse proxy
- Sistema rodando local (mesma maquina que MT5)

---

## ESTRUTURA DE DIRETORIOS

```
mactester-web/
├── backend/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── strategies.py      # CRUD estrategias
│   │   │   ├── monitor.py         # Controle monitor
│   │   │   ├── orders.py          # Historico ordens
│   │   │   └── dashboard.py       # Metricas real-time
│   │   ├── models/
│   │   │   ├── strategy.py
│   │   │   ├── order.py
│   │   │   └── session.py
│   │   └── services/
│   │       ├── monitor_service.py # Integra com live_trading/monitor.py
│   │       ├── mt5_service.py     # Acesso MT5
│   │       └── websocket_service.py
│   ├── config.py
│   ├── app.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StrategySelector/
│   │   │   ├── ParameterEditor/
│   │   │   ├── Dashboard/
│   │   │   ├── OrdersTable/
│   │   │   ├── Chart/
│   │   │   └── RiskManager/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Strategies.jsx
│   │   │   ├── Monitor.jsx
│   │   │   └── History.jsx
│   │   ├── services/
│   │   │   ├── api.js
│   │   │   └── websocket.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml
└── README.md
```

---

## FUNCIONALIDADES DETALHADAS

### 1. PAGINA INICIAL (Dashboard)

**Widgets:**
- Status do monitor (Rodando/Parado/Erro)
- Conta MT5 conectada (login, saldo, margem)
- Estrategias ativas (nome, simbolo, status)
- PnL do dia (pontos, R$, %)
- Numero de trades (executados, pendentes)
- Grafico de equity intraday

**Acoes rapidas:**
- Start/Stop monitor
- Pausar todas estrategias
- Fechar todas posicoes (emergencia)

---

### 2. GESTAO DE ESTRATEGIAS

**Tela de listagem:**
```
+------------------------------------------------------------------+
| ESTRATEGIAS DISPONIVEIS                                          |
+------------------------------------------------------------------+
| Nome              | Status    | Simbolo | Ultimo Sinal | Acoes  |
+------------------------------------------------------------------+
| Barra Elefante    | ATIVO     | WIN$    | 10:35        | [Edit] |
| Inside Bar        | INATIVO   | -       | -            | [Edit] |
| Power Breakout    | ATIVO     | WDO$    | 11:02        | [Edit] |
+------------------------------------------------------------------+
| [+ Nova Estrategia]                                              |
+------------------------------------------------------------------+
```

**Acao: [Edit]**
- Abre modal com formulario dinamico
- Campos gerados automaticamente do config YAML
- Validacao de valores (min/max)
- Preview de mudancas
- Botao "Salvar e Reiniciar" ou "Salvar para Proxima Sessao"

**Campos do formulario (exemplo Barra Elefante):**
```
PARAMETROS DA ESTRATEGIA: Barra Elefante

Deteccao:
  min_amplitude_mult:    [1.35] (1.0 - 3.0)
  min_volume_mult:       [1.30] (1.0 - 3.0)
  max_sombra_pct:        [0.30] (0.0 - 1.0)
  lookback_amplitude:    [25]   (10 - 100)
  lookback_volume:       [20]   (10 - 100)

Horarios:
  horario_inicio:        [09:15]
  horario_fim:           [11:00]
  horario_fechamento:    [12:15]

Stop/Target:
  sl_atr_mult:           [2.0]  (1.0 - 5.0)
  tp_atr_mult:           [3.0]  (1.0 - 10.0)

Trading:
  simbolo:               [WIN$] [Dropdown: WIN$, WDO$, ...]
  volume:                [1.0]  (1.0 - 10.0)
  
[Cancelar] [Salvar]
```

---

### 3. MONITOR EM TEMPO REAL

**Painel principal:**

```
+------------------------------------------------------------------+
| MONITOR LIVE TRADING                              Status: ATIVO  |
+------------------------------------------------------------------+
| Estrategia        | Simbolo | Ultimo Check | Sinais | Ordens    |
+------------------------------------------------------------------+
| Barra Elefante    | WIN$    | 11:05:32     | 3      | 2         |
| Power Breakout    | WDO$    | 11:05:30     | 1      | 1         |
+------------------------------------------------------------------+

ORDENS EXECUTADAS HOJE:

+------------------------------------------------------------------+
| Horario  | Estrategia      | Simbolo | Tipo | Preco  | Status    |
+------------------------------------------------------------------+
| 10:35:12 | Barra Elefante  | WIN$    | BUY  | 163367 | TP HIT    |
| 10:50:45 | Barra Elefante  | WIN$    | SELL | 162806 | SL HIT    |
| 11:02:18 | Power Breakout  | WDO$    | BUY  | 5245   | ABERTA    |
+------------------------------------------------------------------+

POSICOES ABERTAS:

+------------------------------------------------------------------+
| Estrategia      | Simbolo | Tipo | Entrada | SL     | TP     | P&L |
+------------------------------------------------------------------+
| Power Breakout  | WDO$    | BUY  | 5245    | 5230   | 5275   | +8  |
+------------------------------------------------------------------+
```

**Grafico (TradingView Lightweight Charts):**
- Candles do ativo selecionado
- Marcadores de sinais detectados
- Linhas de entrada/SL/TP
- Zoom e navegacao temporal

---

### 4. HISTORICO E RELATORIOS

**Filtros:**
- Data (range picker)
- Estrategia (multi-select)
- Simbolo (multi-select)
- Status (Ganhadores/Perdedores/Todos)

**Tabela de trades:**
- Todos os campos relevantes
- Export para CSV/Excel
- Calculo automatico de metricas

**Metricas calculadas:**
- Total de trades
- Win rate
- Profit factor
- Drawdown maximo
- Sharpe ratio
- Maior sequencia de ganhos/perdas
- PnL por estrategia
- PnL por simbolo
- PnL por horario

---

### 5. GESTAO DE RISCO

**Configuracoes globais:**
```
LIMITES DE RISCO:

Loss Diario:
  Max loss (pontos):     [1000]
  Max loss (R$):         [Calculado: ~500]
  
Por Trade:
  Max loss (pontos):     [500]
  Max volume:            [2.0] contratos
  
Kill Switch:
  Max perdas seguidas:   [5]
  
Restricoes:
  Max posicoes simultaneas:  [3]
  Max exposicao (R$):        [10000]
  
[Aplicar] [Resetar para Padrao]
```

**Alertas:**
- Notificacao quando atingir 70% do loss diario
- Alerta quando 2 perdas seguidas
- Warning quando margem < 20%

---

### 6. CONFIGURACOES

**MT5:**
- Status da conexao
- Conta conectada
- Botao "Reconectar"

**Monitor:**
- Intervalo de verificacao (segundos)
- Horario de funcionamento
- Modo dry-run (toggle)

**Notificacoes:**
- Email (configurar SMTP)
- Telegram (bot token)
- Som no navegador

**Sistema:**
- Backup de configuracoes
- Restaurar configuracao
- Exportar logs

---

## API REST (Backend)

### Endpoints principais:

**Estrategias:**
```
GET    /api/strategies              # Listar todas
GET    /api/strategies/:name        # Detalhes de uma
POST   /api/strategies              # Criar nova
PUT    /api/strategies/:name        # Atualizar parametros
DELETE /api/strategies/:name        # Deletar
POST   /api/strategies/:name/start  # Ativar
POST   /api/strategies/:name/stop   # Desativar
```

**Monitor:**
```
GET    /api/monitor/status          # Status do monitor
POST   /api/monitor/start           # Iniciar monitor
POST   /api/monitor/stop            # Parar monitor
POST   /api/monitor/restart         # Reiniciar
GET    /api/monitor/logs            # Logs em tempo real
```

**Ordens:**
```
GET    /api/orders                  # Listar ordens (com filtros)
GET    /api/orders/:id              # Detalhes de ordem
GET    /api/orders/stats            # Estatisticas
POST   /api/orders/close-all        # Fechar todas posicoes
```

**Dashboard:**
```
GET    /api/dashboard/summary       # Resumo do dia
GET    /api/dashboard/equity        # Serie temporal de equity
GET    /api/dashboard/positions     # Posicoes abertas
```

**MT5:**
```
GET    /api/mt5/status              # Status conexao
GET    /api/mt5/account             # Info da conta
POST   /api/mt5/reconnect           # Reconectar
GET    /api/mt5/symbols             # Simbolos disponiveis
```

---

## WEBSOCKET (Dados em Tempo Real)

**Canais de subscricao:**

```javascript
// Cliente se conecta
ws://localhost:8000/ws

// Subscribe em canal
{
  "action": "subscribe",
  "channel": "orders"  // ou "signals", "positions", "account"
}

// Mensagens recebidas:
{
  "channel": "orders",
  "data": {
    "id": "123",
    "strategy": "barra_elefante",
    "symbol": "WIN$",
    "action": "buy",
    "price": 163367,
    "status": "filled",
    "timestamp": "2024-11-03 10:35:12"
  }
}
```

**Canais disponiveis:**
- `orders` - Novas ordens executadas
- `signals` - Sinais detectados
- `positions` - Mudancas em posicoes
- `account` - Atualizacoes de saldo/margem
- `logs` - Logs do sistema

---

## INTEGRACAO COM SISTEMA EXISTENTE

**Comunicacao Backend <-> live_trading/monitor.py:**

**Opcao 1: Via arquivos** (mais simples)
- Backend le/escreve configs YAML
- Backend envia sinal para reiniciar monitor
- Monitor grava ordens em SQLite
- Backend le SQLite para exibir

**Opcao 2: Via IPC/Redis** (mais robusto)
- Monitor publica eventos em Redis
- Backend subscreve eventos
- Comunicacao bidirecional

**Opcao 3: Monitor como subprocesso** (mais integrado)
- Backend inicia monitor.py como subprocess
- Comunicacao via stdin/stdout (JSON)
- Backend controla ciclo de vida

**RECOMENDACAO: Opcao 2 (Redis)**
- Desacoplamento
- Suporta multiplas instancias
- Real-time nativo
- Escalavel

---

## SEGURANCA

1. Autenticacao (login/senha)
2. Token JWT para API
3. HTTPS obrigatorio em producao
4. Rate limiting
5. CORS configurado
6. Logs de auditoria
7. Senha do MT5 criptografada

---

## FASES DE IMPLEMENTACAO

### Fase 1 - MVP (2-3 semanas)
- [ ] Backend basico (Flask + API REST)
- [ ] Frontend minimo (React + TailwindCSS)
- [ ] Listar estrategias
- [ ] Editar parametros basicos
- [ ] Start/Stop monitor
- [ ] Visualizar ordens em tabela

### Fase 2 - Real-time (1-2 semanas)
- [ ] WebSocket backend
- [ ] WebSocket frontend
- [ ] Dashboard com metricas ao vivo
- [ ] Notificacoes em tempo real
- [ ] Graficos basicos

### Fase 3 - Avancado (2-3 semanas)
- [ ] Grafico de candles + marcadores
- [ ] Historico completo
- [ ] Relatorios e exports
- [ ] Gestao de risco avancada
- [ ] Multi-estrategia/multi-ativo

### Fase 4 - Producao (1 semana)
- [ ] Autenticacao
- [ ] Docker
- [ ] Testes
- [ ] Documentacao
- [ ] Deploy

**TOTAL: 6-9 semanas**

---

## TECNOLOGIAS DETALHADAS

### Backend Stack:
```
fastapi==0.104.1
uvicorn==0.24.0
websockets==12.0
sqlalchemy==2.0.23
pydantic==2.5.0
redis==5.0.1
pyyaml==6.0.1
MetaTrader5==5.0.45
```

### Frontend Stack:
```json
{
  "react": "^18.2.0",
  "vite": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "react-router-dom": "^6.20.0",
  "axios": "^1.6.0",
  "lightweight-charts": "^4.1.0",
  "socket.io-client": "^4.6.0"
}
```

---

## PROXIMOS PASSOS

1. **Aprovar plano**
2. **Definir prioridades** (MVP vs Full)
3. **Escolher stack** (confirmar tecnologias)
4. **Criar estrutura de diretorios**
5. **Implementar Fase 1** (MVP)

---

## PERGUNTAS PARA O USUARIO

1. Prefere MVP rapido ou sistema completo?
2. Vai usar sozinho ou compartilhar com outros? (autenticacao?)
3. Prefere Flask (simples) ou FastAPI (moderno)?
4. Precisa mobile ou apenas desktop?
5. Budget de tempo? (pode implementar em fases?)
6. Conta MT5 e REAL ou DEMO? (seguranca)

---

## OBSERVACOES

- Sistema deve rodar LOCAL (mesma maquina que MT5)
- Navegador acessa via `http://localhost:3000`
- Backend roda em `http://localhost:8000`
- Redis opcional mas recomendado
- Docker facilita deploy mas nao e obrigatorio

---

*Plano criado em modo PLAN (Omega_3)*
*Proximo modo: EXECUTE (Omega_4) para implementacao*

