# MacTester Release 1.0

Sistema completo de backtest e validacao de estrategias de day trade para WIN$.

## Estrutura do Projeto

```
release_1.0/
├── engines/          # Motores de backtest
│   ├── python/       # Motor Python (mactester.py + core)
│   └── rust/         # Motor Rust (executaveis compilados)
│
├── strategies/       # Estrategias modulares
│   └── barra_elefante/  # Primeira estrategia validada
│
├── data/            # Dados historicos
│   └── golden/      # Golden Data do MT5 (M5 e M15)
│
├── results/         # Resultados de backtests e validacoes
│   ├── backtests/   # Resultados de backtests individuais
│   │   ├── python/  # Resultados do motor Python
│   │   └── rust/    # Resultados do motor Rust
│   ├── validation/  # Resultados do pipeline completo (6 fases)
│   └── comparison/  # Comparacoes entre motores
│       ├── python_vs_rust/
│       ├── python_vs_mt5/
│       └── rust_vs_mt5/
│
├── pipeline/        # Pipeline de validacao (6 fases)
│   ├── run_pipeline.py       # Orquestrador principal
│   ├── validators/           # Fases individuais
│   └── comparar_mt5_python.py  # Ferramenta de comparacao
│
├── mt5_integration/ # Integracao com MetaTrader 5
│   ├── ea_templates/    # Templates de EAs
│   └── generated_eas/   # EAs gerados automaticamente
│
└── docs_mactester/           # Documentacao do sistema
```

## Workflow Completo

### 1. Backtest Inicial
Execute backtest usando Python OU Rust:

**Python:**
```bash
cd engines/python
python mactester.py optimize --strategy barra_elefante --tests 4233600 --timeframe 5m
```

**Rust:**
```bash
cd engines/rust
.\optimize_batches.exe
```

### 2. Pipeline de Validacao
Execute as 6 fases de validacao nos melhores resultados:

```bash
cd pipeline
python run_pipeline.py
```

Fases:
- Fase 1: Smoke Test (100-1000 testes rapidos)
- Fase 2: Otimizacao Massiva (10k-50k testes)
- Fase 3: Walk-Forward Analysis
- Fase 4: Out-of-Sample
- Fase 5: Outlier Analysis
- Fase 6: Relatorio Final

### 3. Comparacao de Motores
Valide que Python e Rust produzem resultados identicos:

```bash
cd pipeline
python comparar_motores.py
```

### 4. Geracao de EA
Gere EA do MT5 a partir do setup aprovado:

```bash
cd pipeline
python run_pipeline.py
# Escolher opcao 4: Gerar EA
```

### 5. Validacao MT5
Compare resultados do EA com Python/Rust no mesmo periodo:

```bash
cd pipeline
python comparar_mt5_python.py --period "2024-01-01" "2024-01-31"
```

## Metodologia: Matriz Menor para Maior

Sempre inicie validacoes em periodos curtos:
1. **1 dia** - Debug inicial
2. **1 semana** - Validacao basica
3. **1 mes** - Primeira validacao seria
4. **3 meses** - Validacao estendida
5. **1 ano+** - Validacao historica completa

## Criterios de Aprovacao

Uma estrategia eh APROVADA se atender 3/4 criterios:
- Walk-Forward: Sharpe > 0.8 E 60%+ janelas positivas
- Out-of-Sample: Min 5 trades E Sharpe > 0.5
- Outliers: Sharpe sem outliers > 0.7
- Volume: Min 50 trades no periodo completo

## Golden Data

Os arquivos Golden Data contem:
- Todos os valores OHLC historicos
- Todos os indicadores pre-calculados (medias moveis, ATR, etc)
- Dados do MT5 com precisao total
- Periodo: 5 anos (2020-2025)

**NUNCA modifique os arquivos Golden Data originais!**

## Proximos Passos

1. Executar backtest de 1 mes (jan/2024)
2. Validar que Python == Rust == MT5
3. Executar pipeline completo
4. Adicionar novas estrategias modulares

## Contato e Documentacao

- Documentacao completa: `/_docs_mactester/`
- Guia de estrategias: `/docs_mactester/STRATEGY_TEMPLATE.md`
- Workflow detalhado: `/docs_mactester/WORKFLOW.md`

