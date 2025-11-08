# SMOKE TEST 24 CORES - RELATORIO

**Data:** 2025-11-08  
**Status:** ✅ COMPLETO  
**Tempo:** 6.1 segundos  
**Combinacoes:** 12,000

---

## RESULTADO FINAL

### Melhor Configuracao Encontrada:

```
PnL: 59,455.94 pts
Melhoria vs config original: +119% (+32,377 pts)

Trades: 1,718 (vs 879 original) = 2x mais
Win Rate: 35.4%
Profit Factor: 1.15
Sharpe Ratio: 0.90
Max Drawdown: 18.96%
```

### Parametros Otimizados (TOP 1):

| Parametro | Original | Otimizado | Mudanca |
|-----------|----------|-----------|---------|
| min_amplitude_mult | 2.0 | **1.5** | -25% |
| min_volume_mult | 1.5 | **1.2** | -20% |
| max_sombra_pct | 0.4 | **0.4** | Igual |
| lookback_amplitude | 20 | **15** | -25% |
| sl_atr_mult | 2.0 | **2.5** | +25% |
| tp_atr_mult | 3.0 | **2.0** | -33% |

---

## ANALISE

### Principais Descobertas:

1. **Amplitude e Volume MENORES funcionam melhor**
   - Menos restritivo = mais trades = mais PnL

2. **Lookback menor (15) vs 20**
   - Médias móveis mais reativas

3. **SL mais largo (2.5x ATR) vs 2.0x**
   - Menos stop loss prematuros

4. **TP não importa**
   - TOP 5 são idênticos, variando apenas TP (2.0-5.0)
   - Sugere que trades fecham por intraday close, não TP

---

## TOP 10 CONFIGURACOES

Todas as configurações TOP 10 compartilham:
- lookback_amplitude = 15
- Performance similar (59k-59.4k pts)

**Padrão:** Lookback 15 é CRÍTICO!

---

## PERFORMANCE DO TESTE

```
Total combinacoes: 12,000
Tempo: 6.1 segundos
Velocidade: 1,966 testes/segundo
Cores utilizados: 24
Dataset: 3.52 anos (75,693 candles)
```

**Impressionante!** Rust é extremamente rápido!

---

## PROXIMO PASSO

✅ Smoke Test completo  
⏳ Walk-Forward Validation (validar robustez)

Usar TOP 1 config para Walk-Forward.

