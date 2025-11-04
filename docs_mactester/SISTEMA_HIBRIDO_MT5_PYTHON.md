# Sistema Híbrido: MT5 + Python Monitor

**Versão**: 1.0  
**Data**: 2025-11-03  
**Status**: PLANEJAMENTO

## 📋 Visão Geral

Sistema híbrido que combina:
- **Python**: Monitoramento de condições, cálculos complexos, decision-making
- **MT5**: Execução de ordens, gerenciamento de posições, conexão com broker

## 🎯 Objetivo

Criar um sistema que:
1. Mantém a **precisão do Python** (backtest validado)
2. Usa **infraestrutura do MT5** (execução confiável, regulada)
3. Permite **ajustes em tempo real** sem recompilar EA
4. Facilita **monitoramento e logging** avançado

## 🏗️ Arquitetura Proposta

```
┌─────────────────────────────────────────────────────┐
│                SISTEMA HÍBRIDO                       │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐          ┌───────────────┐       │
│  │   PYTHON     │          │     MT5       │       │
│  │   MONITOR    │◄────────►│      EA       │       │
│  │              │   IPC    │               │       │
│  └──────────────┘          └───────────────┘       │
│         │                          │                │
│         │                          │                │
│         ▼                          ▼                │
│  ┌──────────────┐          ┌───────────────┐       │
│  │  Decision    │          │    Broker     │       │
│  │   Engine     │          │   (Clear)     │       │
│  │              │          │               │       │
│  └──────────────┘          └───────────────┘       │
│         │                          │                │
│         │                          │                │
│         ▼                          ▼                │
│  ┌──────────────────────────────────────────┐      │
│  │     LOGS & MONITORING SYSTEM             │      │
│  └──────────────────────────────────────────┘      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

## 🔗 Comunicação Python ↔️ MT5

### **Opção 1: Arquivos Compartilhados** (Mais Simples)
**Funcionamento**:
- Python escreve sinal em arquivo `.txt` ou `.json`
- EA do MT5 lê arquivo a cada tick/segundo
- Quando sinal encontrado, MT5 executa ordem

**Vantagens**:
- Simples de implementar
- Não requer bibliotecas complexas
- Funciona em qualquer sistema

**Desvantagens**:
- Latência de I/O disco (~10-50ms)
- Possível race condition (arquivo sendo lido enquanto escrito)

**Implementação**:
```
signals/
├── barra_elefante_signal.json
```

**Formato JSON**:
```json
{
  "timestamp": "2024-11-03T09:15:00",
  "signal": "BUY",
  "params": {
    "sl": 105000,
    "tp": 110000,
    "lots": 1.0
  },
  "strategy": "barra_elefante",
  "confidence": 0.85
}
```

### **Opção 2: Named Pipes** (Mais Rápido)
**Funcionamento**:
- Python cria named pipe (Windows: `\\.\pipe\mactester`)
- EA conecta ao pipe
- Comunicação bidirecional em tempo real

**Vantagens**:
- Latência baixa (~1-5ms)
- Comunicação direta, sem arquivo

**Desvantagens**:
- Mais complexo de implementar
- Requer DLL no MT5

### **Opção 3: MetaTrader Python API** (Mais Integrado)
**Funcionamento**:
- Usa biblioteca `MetaTrader5` do Python
- Python controla MT5 diretamente via API

**Vantagens**:
- Total controle do Python sobre MT5
- Sem necessidade de EA customizado

**Desvantagens**:
- Python precisa estar rodando SEMPRE
- Se Python cair, system para completamente

## 📐 Proposta: Arquitetura Híbrida (Opção 1 + Safeguards)

### Componentes

#### **1. Python Monitor (`monitor_live.py`)**
```python
"""
Monitor live trading - Detecta condições e gera sinais
"""
import time
import json
from datetime import datetime
from pathlib import Path

def monitor_market():
    while True:
        # 1. Ler dados do MT5 (via CSV exportado ou API)
        data = load_latest_data()
        
        # 2. Rodar lógica da estratégia (EXATA do backtest)
        signal = detect_elephant_bar(data)
        
        # 3. Se sinal detectado, escrever arquivo
        if signal:
            write_signal_file(signal)
            log_signal(signal)
        
        # 4. Aguardar próximo candle
        time.sleep(60)  # 1 minuto para M5
```

#### **2. MT5 EA (`EA_Hybrid_Reader.mq5`)**
```cpp
//--- Parâmetros
input string SignalFilePath = "signals/barra_elefante_signal.json";
input int CheckInterval = 5;  // Checar a cada 5 segundos

datetime lastSignalTime = 0;

void OnTick()
{
   static datetime lastCheck = 0;
   
   // Checar arquivo apenas a cada CheckInterval segundos
   if(TimeCurrent() - lastCheck < CheckInterval)
      return;
   
   lastCheck = TimeCurrent();
   
   // Ler arquivo de sinal
   string signalJson = ReadFile(SignalFilePath);
   
   if(signalJson == "")
      return;
   
   // Parsear JSON
   Signal sig = ParseSignal(signalJson);
   
   // Verificar se é sinal novo
   if(sig.timestamp <= lastSignalTime)
      return;
   
   // Executar ordem
   ExecuteSignal(sig);
   lastSignalTime = sig.timestamp;
   
   // Limpar arquivo (sinal consumido)
   DeleteFile(SignalFilePath);
}
```

### Fluxo de Operação

#### **Fase 1: Detecção (Python)**
1. Python monitora dados em tempo real
2. Detecta barra elefante (lógica IDÊNTICA ao backtest)
3. Calcula SL/TP baseado em ATR
4. Escreve sinal em arquivo JSON
5. Log detalhado para auditoria

#### **Fase 2: Execução (MT5)**
1. EA lê arquivo de sinal a cada 5s
2. Valida sinal (timestamp, formato, parâmetros)
3. Verifica condições de segurança:
   - Horário permitido
   - Sem posição aberta
   - Capital disponível
4. Executa ordem no broker
5. Remove arquivo de sinal

#### **Fase 3: Monitoramento (Python)**
1. Python lê posições abertas do MT5
2. Monitora trailing stop (se aplicável)
3. Verifica fechamento intraday
4. Log de trades executados

## 🛡️ Safeguards (Segurança)

### **1. Validação de Sinal**
```cpp
bool ValidateSignal(Signal sig)
{
   // Timestamp não pode ser futuro
   if(sig.timestamp > TimeCurrent())
      return false;
   
   // Timestamp não pode ser muito antigo (>5 min)
   if(TimeCurrent() - sig.timestamp > 300)
      return false;
   
   // SL/TP devem ser razoáveis
   double atr = CalculateATR();
   if(MathAbs(sig.sl - sig.entry) > atr * 5)
      return false;
   
   return true;
}
```

### **2. Limite de Perdas Diário**
```cpp
input double MaxDailyLoss = 1000.0;  // R$ 1000

if(GetDailyPnL() < -MaxDailyLoss)
{
   Print("LIMITE DE PERDA DIÁRIO ATINGIDO!");
   return;  // Não executar mais trades hoje
}
```

### **3. Kill Switch**
```cpp
// Arquivo de emergência
if(FileIsExist("signals/KILL_SWITCH.txt"))
{
   Print("KILL SWITCH ATIVADO! Fechando todas as posições.");
   CloseAllPositions();
   ExpertRemove();  // Remove EA
}
```

## 📊 Logging e Monitoramento

### **Python Logging**
```python
import logging

logging.basicConfig(
    filename='logs/monitor_live.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

logging.info(f"Elefante detectado: {signal}")
logging.warning(f"Condição anormal: {condition}")
logging.error(f"Erro crítico: {error}")
```

### **MT5 Logging**
```cpp
void LogTrade(Signal sig, double entry, double sl, double tp)
{
   int handle = FileOpen("logs/mt5_trades.csv", FILE_WRITE|FILE_READ|FILE_CSV, ',');
   
   FileSeek(handle, 0, SEEK_END);
   FileWrite(handle, 
             TimeToString(TimeCurrent()),
             sig.signal,
             DoubleToString(entry, 2),
             DoubleToString(sl, 2),
             DoubleToString(tp, 2)
   );
   
   FileClose(handle);
}
```

## 🧪 Plano de Testes

### **Fase 1: Teste em Vazio (Sem Broker)**
1. Python gera sinais simulados
2. EA lê e "executa" (apenas log, sem ordem real)
3. Validar comunicação Python ↔️ EA
4. Verificar latência e confiabilidade

### **Fase 2: Teste em Conta Demo**
1. Conectar EA à conta demo (Clear)
2. Python monitora mercado REAL
3. Executar trades reais em demo
4. Período: 1-2 meses
5. Comparar resultados vs backtest:
   - Número de trades deve ser similar
   - Sharpe deve ser próximo
   - Slippage e custos reais

### **Fase 3: Paper Trading Avançado**
1. Simular todos os cenários extremos:
   - Gap de abertura
   - Notícia repentina
   - Problema de conexão
   - Falha no Python
2. Validar todos os safeguards
3. Testar kill switch

### **Fase 4: Live Trading (Se Fase 3 OK)**
1. Começar com **1 contrato apenas**
2. Monitoramento 24/7 (primeira semana)
3. Comparação diária: Real vs Esperado
4. Aumentar gradualmente se tudo OK

## 🔧 Implementação Técnica

### **Estrutura de Diretórios**
```
release_1.0/
├── live_trading/
│   ├── monitor_live.py      # Python monitor
│   ├── ea_hybrid_reader.mq5 # EA leitor
│   ├── signals/              # Arquivos de sinal
│   │   └── .gitignore
│   ├── logs/                 # Logs Python e MT5
│   │   ├── monitor_live.log
│   │   └── mt5_trades.csv
│   └── README.md
```

### **Requisitos**
- **Python**: 3.8+, mesmas bibliotecas do backtest
- **MT5**: Build 3000+
- **Broker**: Conta Clear (demo primeiro)
- **Sistema**: Windows 10+, sempre ligado
- **Conexão**: Cabeada, estável

### **Cronograma Estimado**
1. **Semana 1-2**: Implementar comunicação básica
2. **Semana 3**: Testes em vazio
3. **Semana 4**: Conectar conta demo
4. **Meses 2-3**: Paper trading e ajustes
5. **Mês 4+**: Live trading (se aprovado)

## ⚠️ Riscos e Mitigações

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Python trava | ALTO | Watchdog que reinicia Python automaticamente |
| EA não lê sinal | MÉDIO | Timeout + alerta por Telegram |
| Slippage alto | MÉDIO | Monitorar e ajustar expectativas |
| Divergência backtest vs live | ALTO | Comparação diária, interromper se >10% diferença |
| Falha de conexão | ALTO | MT5 tem reconexão automática |
| Erro de lógica | CRÍTICO | Testes exaustivos em demo primeiro |

## 📞 Alertas e Notificações

### **Telegram Bot (Opcional)**
```python
import requests

def send_telegram_alert(message):
    bot_token = "SEU_BOT_TOKEN"
    chat_id = "SEU_CHAT_ID"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    requests.post(url, data={
        "chat_id": chat_id,
        "text": message
    })

# Uso
send_telegram_alert("🐘 Elefante detectado! BUY signal gerado.")
send_telegram_alert("❌ Erro crítico: Python monitor travou!")
```

## 📈 Métricas de Sucesso

Para considerar o sistema híbrido **BEM-SUCEDIDO**:
1. **Identidade Trades**: 95%+ dos trades do backtest reproduzidos
2. **Slippage**: < 5 pontos em média
3. **Latência**: Sinal → Execução < 10 segundos
4. **Uptime**: 99%+ (falhas < 1% do tempo)
5. **Sharpe Real**: > 70% do Sharpe do backtest

## 🎯 Próximos Passos

1. ✅ Validar estratégia em backtest (Python == Rust == MT5)
2. ⏳ Implementar Python monitor básico
3. ⏳ Implementar EA hybrid reader básico
4. ⏳ Testar comunicação em vazio
5. ⏳ Conectar conta demo
6. ⏳ Paper trading 1-2 meses
7. ⏳ Avaliar go/no-go para live

---

**IMPORTANTE**: Este sistema NÃO elimina risco de trading. Mesmo com validação rigorosa, mercado real sempre difere do backtest. Começar pequeno, monitorar intensamente, ajustar conforme necessário.

