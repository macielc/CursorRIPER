# Pipeline de Validacao - MacTester

Sistema de validacao em 6 fases para garantir robustez estatistica das estrategias.

## Arquitetura

```
pipeline/
├── run_pipeline.py              # Orquestrador principal (MENU)
├── comparar_mt5_python.py       # Comparacao Python vs MT5
└── validators/                  # Fases individuais
    ├── fase3_walkforward.py     # Walk-Forward Analysis
    ├── fase4_out_of_sample.py   # Out-of-Sample Testing
    ├── fase5_outlier_analysis.py  # Analise de Outliers
    └── fase6_relatorio_final.py   # Relatorio e Decisao
```

## Menu Principal (`run_pipeline.py`)

### Opcao 1: Testar UMA Estrategia

Execute backtest inicial:

```
1. Escolher motor:
   - Python (multicore, debug facil)
   - Rust (ultra-rapido, producao)

2. Escolher estrategia:
   - barra_elefante
   - [outras futuras]

3. Escolher periodo:
   - 1 dia (debug)
   - 1 semana (validacao basica)
   - 1 mes (validacao seria)
   - 3 meses (estendido)
   - 6 meses (pre-producao)
   - 1-5 anos (historico completo)
   - Custom (datas especificas)

4. Escolher timeframe:
   - M5 (5 minutos)
   - M15 (15 minutos)

5. Numero de testes:
   - 100 (smoke test)
   - 1.000 (validacao rapida)
   - 10.000 (otimizacao basica)
   - 100.000 (otimizacao seria)
   - 4.233.600 (grid completo)
```

Resultado salvo em:
- `../results/backtests/{motor}/{estrategia}_{timestamp}/`

### Opcao 2: Validar Resultados (Pipeline Completo)

Execute validacao em 6 fases:

```
1. Selecionar resultado salvo
2. Escolher Top N setups (ex: Top 50)
3. Escolher modo:
   - Completo (6 fases)
   - Essencial (3 fases rapidas)
```

#### Modo Completo (6 Fases)

**Fase 0: Data Loading**
- Carrega Golden Data
- Valida qualidade dos dados
- Confirma periodo disponivel

**Fase 1: Smoke Test**
- Executa 100-1000 testes rapidos
- Confirma que estrategia funciona
- Identifica erros basicos

**Fase 2: Otimizacao Massiva**
- 10k-50k testes multicore
- Identifica Top 50 setups
- Gera checkpoints a cada 1000
- Metricas: Sharpe, Win Rate, Profit Factor

**Fase 3: Walk-Forward Analysis**
- Janelas: 12 meses treino / 3 meses teste
- Detecta overfitting
- CRITERIO: Sharpe medio > 0.8 E 60%+ janelas positivas

**Fase 4: Out-of-Sample**
- Ultimos 6 meses (nunca vistos)
- CRITERIO: Min 5 trades E Sharpe > 0.5

**Fase 5: Outlier Analysis**
- Remove top/bottom 10% dos trades
- CRITERIO: Sharpe sem outliers > 0.7

**Fase 6: Relatorio Final**
- APROVADO se 3/4 criterios atendidos
- Gera relatorio markdown completo
- Sugere parametros para live trading

#### Modo Essencial (3 Fases)

Validacao rapida e essencial:

**Fase A: Otimizacao Basica**
- 1k-5k testes
- Top 10 setups

**Fase B: Walk-Forward Simplificado**
- 3 janelas apenas
- CRITERIO: 2/3 janelas positivas

**Fase C: Metricas Basicas**
- Min 20 trades
- Sharpe > 0.5
- Win Rate > 45%

Resultado salvo em:
- `../results/validation/{estrategia}_{timestamp}/`

### Opcao 3: Comparar Motores

Valida que Python e Rust produzem resultados identicos:

```
1. Selecionar estrategia
2. Selecionar periodo (recomendado: 1 mes)
3. Executar em ambos os motores
4. Comparacao trade-por-trade:
   - Numero de trades
   - Horarios de entrada/saida
   - Precos de entrada/saida
   - SL/TP
   - P&L
```

Relatorio em:
- `../results/comparison/python_vs_rust/{estrategia}_{timestamp}/`

**CRITERIO DE IDENTIDADE**: 100% dos trades devem ser IDENTICOS

### Opcao 4: Gerar EA do MT5

Gera codigo MQL5 a partir do setup aprovado:

```
1. Selecionar setup validado e aprovado
2. Escolher template de EA:
   - SIMPLES (basico, sem logs)
   - COMPLETO (logs detalhados)
   - DEBUG (ultra-verbose)
3. Gerar arquivo .mq5
```

EA gerado em:
- `../mt5_integration/generated_eas/{estrategia}_{params}.mq5`

### Opcao 5: Comparar Python/Rust com MT5

Valida que EA reproduz resultados do backtest:

```
1. Selecionar setup aprovado
2. Selecionar periodo (recomendado: 1 mes)
3. Executar:
   - Python/Rust: backtest automatico
   - MT5: instrucoes para rodar Strategy Tester
4. Comparacao trade-por-trade
```

**METODOLOGIA**:
1. Periodo CURTO (1 mes)
2. Comparacao TRADE-POR-TRADE
3. Identificar divergencias com LOGS
4. Corrigir ate IDENTIDADE PERFEITA
5. Expandir para periodos maiores

Relatorio em:
- `../results/comparison/python_vs_mt5/{estrategia}_{timestamp}/`
- `../results/comparison/rust_vs_mt5/{estrategia}_{timestamp}/`

## Criterios de Aprovacao

Uma estrategia eh **APROVADA** se atender **3 de 4 criterios**:

| Criterio | Exigencia |
|----------|-----------|
| Walk-Forward | Sharpe > 0.8 E 60%+ janelas positivas |
| Out-of-Sample | Min 5 trades E Sharpe > 0.5 |
| Outliers | Sharpe sem outliers > 0.7 |
| Volume | Min 50 trades no periodo |

## Relatorios Gerados

### Durante Pipeline

- `phase_1_smoke_test.json`
- `phase_2_optimization_results.csv`
- `phase_3_walkforward_report.json`
- `phase_4_oos_report.json`
- `phase_5_outlier_report.json`
- `phase_6_final_report.md`

### Graficos (se gerados)

- `equity_curve.png`
- `returns_distribution.png`
- `drawdown_analysis.png`
- `monthly_returns_heatmap.png`

### Comparacoes

- `comparison_summary.md`
- `trade_by_trade_comparison.csv`
- `divergences_detail.csv`

## Workflow Recomendado

### 1. Debug Inicial (1 dia)
```bash
python run_pipeline.py
# Opcao 1 -> Python -> 1 dia -> 100 testes
```

### 2. Validacao Basica (1 mes)
```bash
python run_pipeline.py
# Opcao 1 -> Python -> 1 mes -> 1000 testes
# Opcao 2 -> Modo Essencial
```

### 3. Comparacao Motores
```bash
python run_pipeline.py
# Opcao 3 -> 1 mes
# DEVE SER IDENTICO!
```

### 4. Pipeline Completo (1 ano+)
```bash
python run_pipeline.py
# Opcao 1 -> Rust -> 5 anos -> 4.2M testes
# Opcao 2 -> Modo Completo -> Top 50
```

### 5. Geracao EA
```bash
python run_pipeline.py
# Opcao 4 -> Setup aprovado
```

### 6. Validacao MT5
```bash
python run_pipeline.py
# Opcao 5 -> 1 mes -> Comparar
# DEVE SER IDENTICO!
```

## Troubleshooting

### Pipeline nao encontra resultados
```bash
# Certifique-se que backtest foi executado primeiro
cd ../engines/python
python mactester.py optimize --strategy barra_elefante --tests 1000
```

### Comparacao mostra divergencias
```bash
# Use periodo menor e logs detalhados
python run_pipeline.py
# Opcao 5 -> 1 dia -> Comparar
# Analise divergencias trade por trade
```

### Memoria insuficiente no pipeline
```bash
# Reduza numero de setups validados
python run_pipeline.py
# Opcao 2 -> Top 10 (ao inves de Top 50)
```

## Proximos Passos

1. Executar opcao 1 (backtest jan/2024)
2. Executar opcao 3 (comparar Python vs Rust)
3. Corrigir divergencias (se houver)
4. Executar opcao 2 (pipeline completo)
5. Executar opcao 4 (gerar EA)
6. Executar opcao 5 (validar EA)
7. Paper trading se tudo OK

## Referencias

- Documentacao completa: `../docs/WORKFLOW.md`
- Exemplos: `../docs/PIPELINE_PHASES.md`

