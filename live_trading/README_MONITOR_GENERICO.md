# MONITOR GENERICO V2.0

Sistema modular de live trading com carregamento dinamico de estrategias.

---

## ARQUITETURA MODULAR

```
live_trading/
├── monitor.py                          # Monitor GENERICO (usa qualquer estrategia)
├── config.yaml                         # Config do MOTOR (generico)
├── strategies/
│   ├── config_barra_elefante.yaml      # Config especifico da estrategia
│   ├── config_inside_bar.yaml          # Outra estrategia
│   └── config_power_breakout.yaml      # Outra estrategia
├── mt5_connector.py                    # Interface MT5
└── logs/                               # Logs de execucao
```

---

## USO

### 1. MODO INTERATIVO (MENU)

```bash
python monitor.py
```

O sistema mostrara menu com estrategias disponiveis:

```
MACTESTER - MONITOR GENERICO V2.0

Estrategias disponiveis:
  1. barra_elefante
  2. inside_bar
  3. power_breakout

Escolha a estrategia (numero): 1
```

### 2. LINHA DE COMANDO

```bash
# Rodar estrategia especifica
python monitor.py --strategy barra_elefante

# Rodar em simbolo diferente
python monitor.py --strategy barra_elefante --symbol WDO$

# Usar config customizado
python monitor.py --strategy barra_elefante --config meu_config.yaml
```

---

## CRIAR NOVA ESTRATEGIA

### 1. Criar arquivo de config

`live_trading/strategies/config_minha_estrategia.yaml`:

```yaml
strategy_name: "Minha Estrategia"
strategy_class: "MinhaEstrategia"
strategy_module: "minha_estrategia.strategy"

parameters:
  param1: 10
  param2: 20
  horario_inicio: 9
  minuto_inicio: 15
  horario_fim: 17
  minuto_fim: 0
  sl_atr_mult: 2.0
  tp_atr_mult: 3.0
```

### 2. Implementar classe da estrategia

A estrategia DEVE ter metodo `detect(df: pd.DataFrame)`:

```python
class MinhaEstrategia:
    def __init__(self, params: Dict):
        self.name = "Minha Estrategia"
        self.param1 = params['param1']
        self.param2 = params['param2']
    
    def detect(self, df: pd.DataFrame) -> Dict:
        """
        Analisa ultimos candles e retorna sinal ou None
        
        Returns:
            {
                'action': 'buy' ou 'sell',
                'price': float,
                'sl': float,
                'tp': float
            }
            ou None se nao houver sinal
        """
        # Sua logica aqui
        if condicao_buy:
            return {
                'action': 'buy',
                'price': preco_entrada,
                'sl': stop_loss,
                'tp': take_profit
            }
        
        return None
```

### 3. Pronto!

```bash
python monitor.py --strategy minha_estrategia
```

---

## ALTERAR PARAMETROS

### Para mudar parametros da ESTRATEGIA:

Edite: `live_trading/strategies/config_NOME_ESTRATEGIA.yaml`

```yaml
parameters:
  min_amplitude_mult: 1.5  # Era 1.35
  sl_atr_mult: 2.5         # Era 2.0
```

### Para mudar config do MOTOR:

Edite: `live_trading/config.yaml`

```yaml
trading:
  symbol: "WDO$"      # Mudar simbolo
  volume: 2.0         # Mudar volume

monitor:
  dry_run: false      # Ativar modo REAL (CUIDADO!)
  check_interval: 30  # Verificar a cada 30 segundos
```

---

## MULTI-INSTANCIA (RODAR VARIAS ESTRATEGIAS)

Rode multiplas instancias simultaneamente:

```bash
# Terminal 1
python monitor.py --strategy barra_elefante --symbol WIN$

# Terminal 2
python monitor.py --strategy inside_bar --symbol WIN$

# Terminal 3
python monitor.py --strategy barra_elefante --symbol WDO$
```

---

## SEGURANCA

1. SEMPRE comece com `dry_run: true`
2. Teste em DEMO antes de usar REAL
3. Verifique parametros antes de ativar
4. Sistema tem kill switch (max_consecutive_losses)
5. Respeita horarios de monitor (8h-18h por padrao)

---

## LOGS

- **monitor.log**: Log principal
- **signals.csv**: Todos sinais detectados
- **orders.csv**: Ordens executadas

---

## ARQUIVOS OBSOLETOS

- `monitor_elefante.py` - SUBSTITUIDO por `monitor.py`
- `signal_detector.py` - SUBSTITUIDO por metodo `detect()` nas estrategias

---

## VANTAGENS

OK - Modularidade total
OK - Motor nao sabe nada sobre estrategias
OK - Facil trocar estrategia
OK - Novos gatilhos: so criar config
OK - Sem editar motor
OK - Backtest ↔ Live alinhados
OK - Multi-ativo e multi-estrategia

