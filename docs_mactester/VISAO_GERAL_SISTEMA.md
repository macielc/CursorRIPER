# Visao Geral do Sistema - MacTester

## O que eh o MacTester?

MacTester eh um sistema completo e profissional para:
1. Testar estrategias de day trade em dados historicos (backtest)
2. Validar robustez estatistica das estrategias
3. Comparar resultados entre diferentes motores (Python, Rust, MT5)
4. Gerar Expert Advisors (EAs) automaticamente para live trading

## Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                     MACTESTER SYSTEM                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │   ENGINES   │  │ STRATEGIES  │  │    DATA     │       │
│  │             │  │             │  │             │       │
│  │ • Python    │  │ • Modulares │  │ • Golden    │       │
│  │ • Rust      │  │ • Isoladas  │  │ • Imutavel  │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PIPELINE (6 fases)                     │   │
│  │  1. Smoke Test                                      │   │
│  │  2. Otimizacao Massiva                              │   │
│  │  3. Walk-Forward Analysis                           │   │
│  │  4. Out-of-Sample                                   │   │
│  │  5. Outlier Analysis                                │   │
│  │  6. Relatorio Final                                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           INTEGRACAO MT5                            │   │
│  │  • Geracao automatica de EAs                        │   │
│  │  • Comparacao Python/Rust vs MT5                    │   │
│  │  • Templates MQL5                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Principios Fundamentais

### 1. Isolamento Motor <-> Estrategia

**Problema**: Se misturar motor com estrategia, precisa reescrever codigo a cada novo setup.

**Solucao**: Estrategias sao MODULOS independentes que se "acoplam" ao motor.

```
Motor (fixo, robusto)  +  Estrategia (modular, trocavel)  =  Backtest
```

### 2. Matriz Menor para Maior

**Problema**: Testar 5 anos direto pode mascarar problemas ou demorar muito.

**Solucao**: SEMPRE comecar pequeno e crescer gradualmente.

```
1 dia -> 1 semana -> 1 mes -> 3 meses -> 6 meses -> anos
```

### 3. Identidade Perfeita entre Motores

**Problema**: Se Python diz uma coisa e MT5 outra, qual confiar?

**Solucao**: Validar que todos produzem resultados IDENTICOS (100%).

```
Python == Rust == MT5  (trade por trade)
```

### 4. Validacao Rigorosa

**Problema**: Backtest bonito nao garante sucesso no live.

**Solucao**: Pipeline de 6 fases detecta overfitting, outliers, e valida robustez.

```
Backtest -> Pipeline (6 fases) -> APROVADO/REPROVADO
```

## Fluxo de Dados

```
1. MT5 (fonte) 
   ↓
2. Exporta dados historicos
   ↓
3. Golden Data (CSV)
   ↓
4. Engines (Python/Rust) leem Golden Data
   ↓
5. Estrategia detecta sinais
   ↓
6. Engine simula trades
   ↓
7. Metricas calculadas
   ↓
8. Resultados salvos
   ↓
9. Pipeline valida
   ↓
10. EA gerado
    ↓
11. MT5 executa (live)
```

## Por que Rust E Python?

### Python
- **Prototipagem rapida**
- **Debug facil**
- **Bibliotecas ricas** (pandas, numpy, matplotlib)
- **Flexibilidade**

### Rust
- **10-50x mais rapido**
- **Producao robusta**
- **Menor uso de memoria**
- **Sem GIL** (paralelismo real)

### Estrategia
1. Desenvolver e debugar em Python
2. Validar em Rust (velocidade)
3. Garantir identidade Python == Rust
4. Usar o melhor de cada mundo

## Golden Data: A Fonte da Verdade

### O que eh?

Dados historicos COMPLETOS extraidos do MT5, incluindo:
- OHLCV (Open, High, Low, Close, Volume)
- TODOS os indicadores (MA, RSI, ATR, etc)
- Valores EXATOS do MT5
- 5 anos de historico

### Por que importante?

- **Reproduzibilidade**: Sempre mesmos resultados
- **Realismo**: Dados reais, nao simulados
- **Imutabilidade**: Nunca mudam, sao "golden"
- **Comparabilidade**: Python e Rust usam mesma fonte

## Pipeline de Validacao

### Fase 0: Data Loading
Carrega e valida qualidade dos dados

### Fase 1: Smoke Test
100-1000 testes rapidos para confirmar funcionamento basico

### Fase 2: Otimizacao Massiva
10k-50k testes para encontrar melhores parametros

### Fase 3: Walk-Forward Analysis
Detecta overfitting usando janelas deslizantes (12m treino / 3m teste)

**CRITERIO**: Sharpe > 0.8 E 60%+ janelas positivas

### Fase 4: Out-of-Sample
Testa em periodo nunca visto (ultimos 6 meses)

**CRITERIO**: Min 5 trades E Sharpe > 0.5

### Fase 5: Outlier Analysis
Remove trades extremos e recalcula metricas

**CRITERIO**: Sharpe sem outliers > 0.7

### Fase 6: Relatorio Final
**APROVADO** se 3 de 4 criterios atendidos

## Integracao com MT5

### Por que importante?

- MT5 eh a plataforma de execucao (live trading)
- Precisa garantir que EA reproduz backtest
- Validacao critica antes de arriscar capital real

### Processo

1. Gerar EA automaticamente do setup aprovado
2. Testar EA no MT5 Strategy Tester
3. Comparar resultados Python vs MT5 (trade-por-trade)
4. Corrigir divergencias ate identidade perfeita
5. Paper trading em conta demo
6. Live trading (se tudo OK)

## Estrategias Modulares

### Estrutura

Cada estrategia vive em seu proprio diretorio:

```
strategies/nome_estrategia/
├── __init__.py
├── strategy.py        # Logica
├── params.json        # Parametros
└── README.md         # Docs
```

### Vantagens

- **Facil adicionar novas** sem quebrar existentes
- **Motor nao muda** ao trocar estrategia
- **Testes reproduziveis**
- **Organizacao clara**

## Metricas Principais

### Sharpe Ratio
```
Sharpe = (Retorno Medio - Taxa Livre de Risco) / Desvio Padrao
```
- Mede retorno ajustado ao risco
- Ideal: > 1.0, Bom: > 0.8, Aceitavel: > 0.5

### Win Rate
```
Win Rate = Trades Vencedores / Total Trades
```
- % de trades positivos
- Ideal: > 55%, Aceitavel: > 50%

### Profit Factor
```
Profit Factor = Lucro Total / Perda Total
```
- Relacao lucro/perda
- Ideal: > 2.0, Bom: > 1.5, Aceitavel: > 1.2

### Max Drawdown
```
Max DD = Maior queda do pico ao vale
```
- Pior perda acumulada
- Ideal: < 10%, Aceitavel: < 20%

## Gestao de Risco

### Position Sizing
```
Tamanho = Capital × %Risco / (SL_pontos × valor_ponto)
```

Exemplo:
- Capital: R$ 100.000
- Risco: 1% = R$ 1.000
- SL: 500 pontos
- Valor ponto WIN$: R$ 0.20
- Tamanho = 1000 / (500 × 0.20) = 10 contratos

### Stop Loss Dinamico
```
SL = ATR × multiplicador
```
- Baseado em volatilidade atual
- Adapta-se ao mercado

### Take Profit
```
TP = ATR × multiplicador
Risk/Reward = TP_mult / SL_mult
```

## Workflow Resumido

```
1. Implementar estrategia (Python)
   ↓
2. Smoke test (1 dia, 10 testes)
   ↓
3. Backtest inicial (1 mes, 1k testes)
   ↓
4. Comparar Python vs Rust (IDENTICO)
   ↓
5. Pipeline completo (6 fases)
   ↓ (se APROVADO)
6. Gerar EA MT5
   ↓
7. Validar Python vs MT5 (IDENTICO)
   ↓
8. Paper trading (1-2 meses demo)
   ↓ (se bem-sucedido)
9. Live trading (gradual, conservador)
```

## Criterios de Aprovacao Final

Uma estrategia esta pronta para live se:

- [ ] Pipeline APROVADO (3/4 criterios)
- [ ] Python == Rust (100% identico)
- [ ] Python == MT5 (100% identico)
- [ ] Paper trading bem-sucedido (1-2 meses)
- [ ] Metricas confiaveis:
  - Sharpe > 0.8
  - Win Rate > 50%
  - Profit Factor > 1.5
  - Min 50 trades validados
- [ ] Psicologico e capital prontos

## Proximos Passos

1. Validar estrategia `barra_elefante` completamente
2. Seguir workflow rigoroso
3. Documentar aprendizados
4. Expandir para novas estrategias

## Recursos

- **Documentacao completa**: `/docs/`
- **Workflow detalhado**: `WORKFLOW.md`
- **Guia de estrategias**: `../strategies/README.md`
- **README principal**: `../README.md`

---

**LEMBRE-SE**: Backtest bom NAO garante sucesso no live. O sistema MacTester existe para VALIDAR rigorosamente e MINIMIZAR riscos, mas trading sempre envolve risco. Opere com responsabilidade.

