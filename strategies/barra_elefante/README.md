# Estrategia: Barra Elefante

## Descricao

A estrategia "Barra Elefante" identifica candles de grande amplitude com corpo forte e volume elevado, indicando momentum significativo no mercado.

## Logica de Entrada

### Criterios Obrigatorios

1. **Corpo Forte**: O corpo do candle deve representar pelo menos X% da amplitude total
   - Corpo = |Close - Open|
   - Amplitude = High - Low
   - Corpo >= min_body_percent × Amplitude

2. **Volume Elevado**: O volume deve ser Y vezes a media dos ultimos N candles
   - Volume >= min_volume_mult × Media_Volume

3. **Direcao Clara**:
   - LONG: Close > Open (candle verde/bullish)
   - SHORT: Close < Open (candle vermelho/bearish)

### Filtros Opcionais

Cada filtro pode ser ativado/desativado:

1. **Filtro MM21** (`use_mm21_filter`):
   - LONG: Preco deve estar acima da MM21
   - SHORT: Preco deve estar abaixo da MM21

2. **Filtro RSI** (`use_rsi_filter`):
   - LONG: RSI nao pode estar em zona de sobrecompra (< 70)
   - SHORT: RSI nao pode estar em zona de sobrevenda (> 30)

3. **Filtro Volume** (`use_volume_filter`):
   - Volume deve estar consistentemente acima da media

4. **Filtro ATR** (`use_atr_filter`):
   - Volatilidade (ATR) deve estar dentro de range aceitavel

5. **Filtro Tendencia** (`use_trend_filter`):
   - LONG: Tendencia de alta identificada
   - SHORT: Tendencia de baixa identificada

## Gerenciamento de Risco

### Stop Loss
```
SL = sl_mult × ATR
```
- Posicionado a X vezes o ATR do momento de entrada
- Dinamico baseado em volatilidade

### Take Profit
```
TP = tp_mult × ATR
```
- Posicionado a Y vezes o ATR
- Risk/Reward ratio = tp_mult / sl_mult

### Sequencia de Perdas
```
max_sequential_losses
```
- Sistema para de operar apos N perdas consecutivas
- Protege contra periodos desfavoraveis

### Sequencia de Candles
```
min_candles_sequence
```
- Minimo de candles consecutivos confirmando padrao
- Reduz sinais falsos

## Parametros Testaveis

### Grid Completo (4.233.600 combinacoes)

| Parametro | Valores Possiveis | Qtd |
|-----------|------------------|-----|
| min_body_percent | [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95] | 8 |
| min_volume_mult | [1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] | 7 |
| sl_mult | [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] | 7 |
| tp_mult | [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] | 7 |
| min_candles_sequence | [1, 2, 3, 4, 5] | 5 |
| max_sequential_losses | [2, 3, 4, 5, 6] | 5 |
| use_mm21_filter | [true, false] | 2 |
| use_rsi_filter | [true, false] | 2 |
| use_volume_filter | [true, false] | 2 |
| use_atr_filter | [true, false] | 2 |
| use_trend_filter | [true, false] | 2 |

**Total**: 8 × 7 × 7 × 7 × 5 × 5 × 2^5 = 4.233.600

## Indicadores Necessarios

A estrategia requer que o Golden Data contenha:

- OHLCV basico (Open, High, Low, Close, Volume)
- MM21 (Media Movel 21 periodos)
- RSI (14 periodos)
- ATR (14 periodos)
- Volume_MA (Media de volume)

**Todos ja estao presentes no Golden Data M5/M15**

## Exemplo Visual

```
Barra Elefante BULLISH:

    |
    |  <- Pavio superior pequeno
  ████  <- Corpo forte (> 60-95% da amplitude)
  ████
  ████
  ████
    |  <- Pavio inferior pequeno
    |
    
Close >> Open
Volume >> Media
```

## Resultados Esperados

### Metricas Alvo (Validacao Completa)

- **Sharpe Ratio**: > 0.8
- **Win Rate**: > 50%
- **Profit Factor**: > 1.5
- **Max Drawdown**: < 20%
- **Trades Minimos**: 50+ no periodo

### Performance Historica (2020-2025)

*Aguardando validacao completa do pipeline*

## Status de Desenvolvimento

- [x] Logica implementada em Python
- [x] Logica implementada em Rust
- [x] Grid de parametros definido
- [x] Integrado ao motor de backtest
- [ ] Validacao Python vs Rust (em andamento)
- [ ] Pipeline completo executado
- [ ] EA do MT5 validado
- [ ] Aprovado para live trading

## Como Testar

### Teste Rapido (1 mes)
```bash
cd ../../engines/python
python mactester.py optimize --strategy barra_elefante --tests 1000 --timeframe 5m --period "2024-01-01" "2024-01-31"
```

### Teste Completo (4.2M combinacoes)
```bash
cd ../../engines/rust
.\optimize_batches.exe
```

### Pipeline de Validacao
```bash
cd ../../pipeline
python run_pipeline.py
# Escolher opcao 2: Validar Resultados
```

## Otimizacoes Implementadas

### Python:
- Numba JIT compilation
- Vetorizacao com NumPy
- Multiprocessing (Pool)
- Cache de indicadores

### Rust:
- Rayon parallelism
- Zero-copy data structures
- SIMD operations
- Memory-efficient iterators

## Proximos Passos

1. Executar backtest jan/2024 (Python e Rust)
2. Comparar resultados trade-por-trade
3. Executar pipeline completo nos Top 50 setups
4. Validar EA no MT5
5. Preparar para paper trading

## Referencias

- Implementacao: `strategy.py`
- Versao otimizada: `strategy_optimized.py`
- Documentacao geral: `../README.md`

