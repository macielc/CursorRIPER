# 🔗 PLANO: Sistema Híbrido Python Monitor + MT5 Executor

*Criado: 2024-11-03*
*Modo: Ω₄·EXECUTE*
*Status: Em implementação*

---

## 🎯 OBJETIVO

Criar sistema onde:
- **Python**: Monitora mercado, detecta sinais, calcula SL/TP
- **MT5**: Apenas executa ordens recebidas do Python

**Vantagens**:
- ✅ Usa Python já validado (27 trades em janeiro)
- ✅ Sem necessidade de identidade Python ↔ MT5
- ✅ Fácil debugar e evoluir
- ✅ Flexível (mudar parâmetros sem recompilar)

---

## 🏗️ ARQUITETURA

```
┌─────────────────────────────────────┐
│   PYTHON MONITOR (Cérebro)         │
│                                     │
│  1. Conecta ao MT5 (via API)       │
│  2. Busca últimos candles M5       │
│  3. Detecta barra elefante         │
│  4. Calcula SL/TP (ATR)            │
│  5. Envia ordem para MT5           │
│                                     │
└──────────────┬──────────────────────┘
               │ MetaTrader5 Python API
               │ (via mt5.py)
               ↓
┌─────────────────────────────────────┐
│   MT5 (Mãos - Executor)             │
│                                     │
│  1. Recebe ordem do Python         │
│  2. Valida (horário, margem, etc)  │
│  3. Executa ordem                  │
│  4. Gerencia SL/TP                 │
│  5. Envia status de volta          │
│                                     │
└─────────────────────────────────────┘
```

---

## 📦 COMPONENTES

### **1. Python Monitor** (`live_trading/monitor_elefante.py`)
- Loop principal de monitoramento
- Conexão com MT5 via API oficial
- Lógica de detecção (reutiliza strategy.py)
- Cálculo de SL/TP
- Sistema de logs

### **2. MT5 Executor** (`mt5_integration/EA_Executor_Hibrido.mq5`)
- EA SIMPLES (50-100 linhas)
- Recebe ordens do Python via API
- Executa market orders
- Gerencia posições abertas
- Opcional: pode funcionar sem EA (Python faz tudo)

### **3. Configuração** (`live_trading/config.yaml`)
- Parâmetros da estratégia
- Horários de operação
- Risk management
- Símbolos a monitorar

### **4. Sistema de Logs** (`live_trading/logs/`)
- Sinais detectados
- Ordens executadas
- Erros e warnings
- Performance tracking

---

## 🔧 IMPLEMENTAÇÃO - FASE 1: SETUP

### **Tarefa 1.1**: Instalar biblioteca MetaTrader5
```bash
pip install MetaTrader5
```

### **Tarefa 1.2**: Criar estrutura de diretórios
```
live_trading/
  ├── monitor_elefante.py      # Monitor principal
  ├── mt5_connector.py          # Wrapper para MT5 API
  ├── signal_detector.py        # Detecção de sinais
  ├── risk_manager.py           # Gestão de risco
  ├── config.yaml               # Configurações
  ├── logs/                     # Logs do sistema
  └── tests/                    # Testes unitários
```

### **Tarefa 1.3**: Testar conexão Python → MT5
```python
import MetaTrader5 as mt5

# Testar conexão
if mt5.initialize():
    print("✅ Conectado ao MT5")
    print(f"Conta: {mt5.account_info().login}")
    print(f"Servidor: {mt5.account_info().server}")
else:
    print("❌ Erro na conexão")
```

---

## 🔧 IMPLEMENTAÇÃO - FASE 2: PYTHON MONITOR

### **Tarefa 2.1**: Criar `mt5_connector.py`
```python
import MetaTrader5 as mt5
from datetime import datetime

class MT5Connector:
    def __init__(self):
        self.connected = False
    
    def connect(self):
        if not mt5.initialize():
            raise Exception("MT5 não inicializado")
        self.connected = True
    
    def get_candles(self, symbol, timeframe, count=50):
        """Busca últimos N candles"""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        return pd.DataFrame(rates)
    
    def send_order(self, symbol, order_type, volume, sl, tp):
        """Envia ordem para MT5"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "sl": sl,
            "tp": tp,
            "magic": 123456,
            "comment": "BarraElefante",
        }
        result = mt5.order_send(request)
        return result
```

### **Tarefa 2.2**: Criar `signal_detector.py`
```python
from strategies.barra_elefante.strategy import BarraElefante

class SignalDetector:
    def __init__(self, params):
        self.strategy = BarraElefante(params)
    
    def detect_signal(self, df):
        """
        Detecta sinal de entrada
        Retorna: {'action': 'BUY'/'SELL'/'NONE', 'price': float}
        """
        signals = self.strategy.generate_signals(df)
        
        # Verifica última barra
        if signals['entries_long'][-1]:
            return {'action': 'BUY', 'price': df['close'].iloc[-1]}
        elif signals['entries_short'][-1]:
            return {'action': 'SELL', 'price': df['close'].iloc[-1]}
        else:
            return {'action': 'NONE', 'price': 0}
```

### **Tarefa 2.3**: Criar `monitor_elefante.py` (loop principal)
```python
import time
from datetime import datetime
from mt5_connector import MT5Connector
from signal_detector import SignalDetector

def main():
    # Setup
    mt5 = MT5Connector()
    mt5.connect()
    
    detector = SignalDetector({
        'min_amplitude_mult': 1.35,
        'min_volume_mult': 1.3,
        'max_sombra_pct': 0.30,
        'lookback_amplitude': 25,
        'lookback_volume': 20,
        'horario_inicio': 9,
        'minuto_inicio': 15,
        'horario_fim': 11,
        'minuto_fim': 0,
        'sl_atr_mult': 2.0,
        'tp_atr_mult': 3.0,
    })
    
    print("🚀 Monitor iniciado!")
    
    # Loop principal
    while True:
        now = datetime.now()
        
        # Verificar horário de operação (9h - 17h)
        if 9 <= now.hour < 17:
            
            # Buscar dados
            df = mt5.get_candles('WINFUT', mt5.TIMEFRAME_M5, 50)
            
            # Detectar sinal
            signal = detector.detect_signal(df)
            
            if signal['action'] != 'NONE':
                print(f"🎯 SINAL: {signal['action']} @ {signal['price']}")
                
                # Calcular SL/TP
                atr = calculate_atr(df)
                sl, tp = calculate_sl_tp(signal, atr)
                
                # Enviar ordem
                result = mt5.send_order(
                    symbol='WINFUT',
                    order_type=mt5.ORDER_TYPE_BUY if signal['action'] == 'BUY' else mt5.ORDER_TYPE_SELL,
                    volume=1.0,
                    sl=sl,
                    tp=tp
                )
                
                print(f"✅ Ordem enviada: {result}")
        
        # Aguardar próximo candle (300s = 5min)
        time.sleep(300)

if __name__ == '__main__':
    main()
```

---

## 🔧 IMPLEMENTAÇÃO - FASE 3: SAFEGUARDS

### **Tarefa 3.1**: Sistema de validação de ordens
```python
class OrderValidator:
    def validate(self, order):
        # 1. Horário permitido?
        if not self.is_trading_hours():
            return False, "Fora do horário"
        
        # 2. Já tem posição aberta?
        if self.has_open_position():
            return False, "Já tem posição"
        
        # 3. Margem suficiente?
        if not self.has_margin(order):
            return False, "Margem insuficiente"
        
        return True, "OK"
```

### **Tarefa 3.2**: Sistema de logs detalhado
```python
import logging

logger = logging.getLogger('MonitorElefante')
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler('live_trading/logs/monitor.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

# Console handler
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(ch)
```

### **Tarefa 3.3**: Kill switch de emergência
```python
# Se perder X pontos, parar tudo
MAX_LOSS_POINTS = 1000

def check_kill_switch():
    daily_pnl = get_daily_pnl()
    if daily_pnl < -MAX_LOSS_POINTS:
        logger.critical(f"🚨 KILL SWITCH! Loss: {daily_pnl} pts")
        mt5.close_all_positions()
        sys.exit(1)
```

---

## 🧪 IMPLEMENTAÇÃO - FASE 4: TESTES

### **Tarefa 4.1**: Teste de conexão
```python
def test_connection():
    mt5 = MT5Connector()
    assert mt5.connect() == True
    print("✅ Conexão OK")
```

### **Tarefa 4.2**: Teste de detecção (histórico)
```python
def test_detection_january():
    # Carregar dados de janeiro/2024
    df = load_golden_data('2024-01-01', '2024-01-31')
    
    detector = SignalDetector(params)
    signals = detector.detect_all_signals(df)
    
    # Deve detectar 27 sinais
    assert len(signals) == 27
    print("✅ Detecção OK - 27 sinais")
```

### **Tarefa 4.3**: Teste dry-run (sem executar)
```python
def test_dry_run():
    # Roda monitor sem enviar ordens de verdade
    monitor = Monitor(dry_run=True)
    monitor.run_for_minutes(60)  # Roda 1 hora
    
    print(f"Sinais detectados: {monitor.signals_count}")
    print(f"Ordens (simuladas): {monitor.orders_count}")
```

---

## 📊 IMPLEMENTAÇÃO - FASE 5: VALIDAÇÃO EM DEMO

### **Tarefa 5.1**: Configurar conta demo
- Abrir conta demo na corretora
- Configurar MT5 com conta demo
- Testar com dinheiro virtual

### **Tarefa 5.2**: Rodar 1 semana em demo
```
Segunda: Monitorar, detectar sinais, executar
Terça: Avaliar resultados, ajustar se necessário
...
Sexta: Review semanal
```

### **Tarefa 5.3**: Comparar resultados demo vs backtest
```python
# Comparar:
- Quantidade de sinais (deve ser similar)
- Win rate (deve ser similar)
- Slippage real vs esperado
- Latência de execução
```

---

## ✅ CRITÉRIOS DE SUCESSO

### **Fase 2-3 (Implementação)**:
- ✅ Python conecta ao MT5
- ✅ Busca candles em tempo real
- ✅ Detecta sinais corretamente
- ✅ Envia ordens para MT5
- ✅ Logs funcionando

### **Fase 4 (Testes)**:
- ✅ Detecção histórica = 27 sinais (janeiro)
- ✅ Dry-run sem erros
- ✅ Validações funcionando

### **Fase 5 (Demo)**:
- ✅ 1 semana sem crashes
- ✅ Resultados similares ao backtest
- ✅ Slippage < 10 pontos/trade

---

## ⏱️ CRONOGRAMA

```
Fase 1 (Setup):           30 min
Fase 2 (Monitor):         2 horas
Fase 3 (Safeguards):      1 hora
Fase 4 (Testes):          1 hora
Fase 5 (Demo):            1 semana

Total dev: ~4-5 horas
Total validação: 1 semana
```

---

## 🚀 PRÓXIMOS PASSOS IMEDIATOS

1. Criar diretório `live_trading/`
2. Instalar `pip install MetaTrader5`
3. Testar conexão Python → MT5
4. Implementar `mt5_connector.py`
5. Implementar `monitor_elefante.py`

---

*Plano aprovado em Ω₃·PLAN, agora executando em Ω₄·EXECUTE*

