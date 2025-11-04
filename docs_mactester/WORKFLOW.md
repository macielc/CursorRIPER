# Workflow Completo - MacTester

Guia passo-a-passo do processo completo de validacao de estrategias.

## Visao Geral

```
1. Criar Estrategia
   ↓
2. Smoke Test (1 dia)
   ↓
3. Backtest Inicial (1 mes)
   ↓
4. Comparar Motores (Python vs Rust)
   ↓
5. Pipeline Completo (validacao)
   ↓
6. Gerar EA MT5
   ↓
7. Validar MT5 (Python vs MT5)
   ↓
8. Paper Trading
   ↓
9. Live Trading
```

## Fase 1: Criar Estrategia

### 1.1. Definir Logica

Documentar claramente:
- O que caracteriza o setup/gatilho?
- Quais sao os criterios de entrada?
- Como calcular SL/TP?
- Quais filtros opcionais usar?

### 1.2. Implementar Codigo

```bash
cd strategies
mkdir minha_estrategia
cd minha_estrategia
```

Criar arquivos:
- `__init__.py`
- `strategy.py` (logica principal)
- `params.json` (parametros testaveis)
- `README.md` (documentacao)

Ver template: `strategies/README.md`

### 1.3. Definir Grid de Parametros

Em `params.json`:

```json
{
    "param1": [val1, val2, val3],
    "param2": [valA, valB, valC],
    "filtro_x": [true, false]
}
```

Calcular total de combinacoes:
```
Total = len(param1) × len(param2) × len(filtro_x)
```

## Fase 2: Smoke Test (1 dia)

**Objetivo**: Confirmar que estrategia funciona basicamente.

### 2.1. Teste Minimo

```bash
cd ../engines/python
python mactester.py optimize --strategy minha_estrategia --tests 10 --timeframe 5m --period "2024-01-02" "2024-01-02"
```

### 2.2. Verificar

- Script rodou sem erros?
- Gerou pelo menos 1 trade?
- Metricas fazem sentido?

### 2.3. Debug

Se nao funcionar:
- Adicionar prints na logica
- Verificar dados disponiveis
- Testar calculo de indicadores

## Fase 3: Backtest Inicial (1 mes)

**Objetivo**: Primeiros resultados estatisticos.

### 3.1. Backtest Python (1000 testes)

```bash
cd ../engines/python
python mactester.py optimize --strategy minha_estrategia --tests 1000 --timeframe 5m --period "2024-01-01" "2024-01-31"
```

Tempo estimado: 5-30 minutos

### 3.2. Analisar Top 10

```bash
# Resultados em:
cd ../../results/backtests/python/minha_estrategia_TIMESTAMP/

# Ver top 10
head -10 top_50.csv
```

Verificar:
- Sharpe > 0.5?
- Win Rate > 45%?
- Profit Factor > 1.2?
- Numero de trades razoavel (>= 10)?

### 3.3. Ajustar se Necessario

Se resultados ruins:
- Revisar logica
- Ajustar ranges de parametros
- Adicionar/remover filtros
- Repetir smoke test

## Fase 4: Comparar Motores

**Objetivo**: Garantir Python == Rust (100%)

### 4.1. Backtest Python

```bash
cd engines/python
python mactester.py optimize --strategy minha_estrategia --tests 1 --timeframe 5m --period "2024-01-01" "2024-01-31" --params "{'param1': val1, 'param2': val2}"
```

### 4.2. Backtest Rust

```bash
cd ../rust
# Configurar mesmos parametros no fonte
.\validate_single.exe
```

### 4.3. Comparar

```bash
cd ../../pipeline
python comparar_motores.py --python ../results/.../python/ --rust ../results/.../rust/
```

### 4.4. Criterio de Aprovacao

**100% IDENTICO**:
- Mesmo numero de trades
- Mesmos horarios de entrada/saida
- Mesmos precos
- Mesmo P&L

### 4.5. Corrigir Divergencias

Se houver diferenca:
1. Logs detalhados em ambos
2. Comparar trade-por-trade
3. Identificar causa (indicador? timing? arredondamento?)
4. Corrigir codigo
5. Re-testar

**NAO prosseguir ate identidade perfeita!**

## Fase 5: Pipeline Completo

**Objetivo**: Validacao estatistica rigorosa (6 fases)

### 5.1. Otimizacao Massiva

Usar Rust para velocidade:

```bash
cd engines/rust
.\optimize_batches.exe
```

Tempo estimado: 15-60 minutos (4.2M testes)

### 5.2. Executar Pipeline

```bash
cd ../../pipeline
python run_pipeline.py

# Escolher:
# Opcao 2: Validar Resultados
# Modo: Completo
# Top N: 50
```

### 5.3. Fases Executadas

1. **Walk-Forward Analysis**
   - 12 meses treino / 3 meses teste
   - Criterio: Sharpe > 0.8 E 60%+ janelas positivas

2. **Out-of-Sample**
   - Ultimos 6 meses (nunca vistos)
   - Criterio: Min 5 trades E Sharpe > 0.5

3. **Outlier Analysis**
   - Remove top/bottom 10%
   - Criterio: Sharpe sem outliers > 0.7

4. **Relatorio Final**
   - APROVADO se 3/4 criterios OK

### 5.4. Revisar Relatorio

```bash
cd ../results/validation/minha_estrategia_TIMESTAMP/
cat phase_6_final_report.md
```

Verificar:
- Status: APROVADO ou REPROVADO?
- Quais criterios passou?
- Metricas finais
- Parametros recomendados

### 5.5. Se REPROVADO

- Analisar quais criterios falharam
- Ajustar estrategia/parametros
- Voltar a Fase 3

### 5.6. Se APROVADO

Prosseguir para Fase 6!

## Fase 6: Gerar EA MT5

**Objetivo**: Criar codigo MQL5 automaticamente

### 6.1. Gerar EA

```bash
cd pipeline
python run_pipeline.py

# Escolher:
# Opcao 4: Gerar EA
# Setup: [selecionar setup aprovado]
# Template: SIMPLES (para producao) ou DEBUG (para validacao)
```

### 6.2. Compilar EA

1. Abrir MetaEditor no MT5
2. Abrir arquivo gerado em `mt5_integration/generated_eas/`
3. Compilar (F7)
4. Verificar erros

### 6.3. Documentar Parametros

Anotar parametros do setup aprovado:
- param1 = X
- param2 = Y
- filtro_z = true/false

## Fase 7: Validar MT5

**Objetivo**: Garantir Python == MT5 (100%)

### 7.1. Backtest Python

```bash
cd engines/python
python mactester.py optimize --strategy minha_estrategia --tests 1 --timeframe 5m --period "2024-01-01" "2024-01-31" --params "{...}"
```

### 7.2. Backtest MT5

1. Abrir Strategy Tester (Ctrl+R)
2. Configurar:
   - EA: [EA gerado]
   - Symbol: WIN$
   - Period: M5
   - Dates: 2024.01.01 - 2024.01.31
   - Model: Every tick
3. Rodar
4. Exportar resultados para CSV

### 7.3. Comparar

```bash
cd pipeline
python comparar_mt5_python.py --period "2024-01-01" "2024-01-31"
```

### 7.4. Criterio de Aprovacao

**100% IDENTICO** (novamente!)

### 7.5. Corrigir Divergencias

Processo identico a Fase 4, mas agora Python vs MT5.

**Metodologia**:
- Periodo curtissimo (1 dia ideal)
- Logs detalhados em ambos
- Comparar candle-por-candle
- Identificar causa raiz
- Corrigir
- Re-testar

**NAO prosseguir ate identidade perfeita!**

## Fase 8: Paper Trading

**Objetivo**: Testar em conta demo com dados reais (nao historicos)

### 8.1. Conta Demo

1. Abrir conta demo na corretora
2. Instalar EA no MT5 conectado a demo
3. Configurar parametros aprovados
4. Ativar EA

### 8.2. Monitoramento

Durante 1-2 meses:
- Acompanhar TODOS os trades
- Comparar com expectativa do backtest
- Verificar slippage, spreads, custos
- Monitorar drawdown

### 8.3. Logs e Analises

```bash
# Exportar trades da demo
# Analisar performance

cd pipeline
python analisar_paper_trading.py --trades demo_trades.csv
```

### 8.4. Criterios de Aprovacao

- Performance condizente com backtest?
- Drawdown dentro do esperado?
- Sem erros tecnicos?
- Psicologicamente confortavel?

### 8.5. Se Insatisfatorio

- Nao ir para live
- Revisar estrategia
- Ajustar parametros
- Voltar a fase 5 ou 6

## Fase 9: Live Trading

**CUIDADO MAXIMO!**

### 9.1. Pre-requisitos

- [ ] Backtest validado
- [ ] Python == Rust
- [ ] Python == MT5
- [ ] Pipeline aprovado (3/4)
- [ ] Paper trading bem-sucedido (1-2 meses)
- [ ] Capital disponivel (risco controlado)
- [ ] Psicologico preparado

### 9.2. Configuracao Segura

1. **Position Sizing Conservador**
   ```
   Tamanho = Capital × 1% / (SL em pontos × valor do ponto)
   ```

2. **Horarios Restritos**
   - Apenas 09:30 - 17:30 (evitar abertura/fechamento)

3. **Stop Loss Sempre**
   - NUNCA operar sem SL
   - SL conforme validado no backtest

4. **Monitoramento**
   - Logs em tempo real
   - Alertas configurados
   - Kill switch pronto

### 9.3. Inicio Gradual

- Mes 1: 1 micro-contrato
- Mes 2: Se OK, aumentar gradualmente
- Mes 3+: Ajustar conforme performance

### 9.4. Monitoramento Continuo

- Revisar TODOS os trades diariamente
- Manter log de decisoes
- Analisar performance semanal/mensal
- Comparar com backtest

### 9.5. Criterios de Parada

**PARAR IMEDIATAMENTE se**:
- Drawdown > 20% (ou conforme backtest)
- 5+ perdas consecutivas (revisar)
- Comportamento inesperado do EA
- Slippage excessivo
- Problemas tecnicos recorrentes

### 9.6. Ajustes e Melhorias

- NÃO fazer ajustes freneticos
- Aguardar amostra estatistica (50+ trades)
- Se necessario ajustar, voltar para paper trading
- Documentar TUDO

## Matriz: Menor para Maior

Em TODAS as fases, sempre:

```
1 dia -> 1 semana -> 1 mes -> 3 meses -> 6 meses -> 1+ anos
```

**NUNCA pular etapas!**

## Checklist de Aprovacao

### Antes de Live Trading

- [ ] Estrategia implementada e documentada
- [ ] Smoke test passou (1 dia)
- [ ] Backtest inicial OK (1 mes, 1000 testes)
- [ ] Python == Rust (100% identico)
- [ ] Pipeline completo APROVADO (3/4 criterios)
- [ ] EA gerado e compilado
- [ ] Python == MT5 (100% identico)
- [ ] Paper trading bem-sucedido (1-2 meses)
- [ ] Capital e psicologico prontos
- [ ] Sistema de monitoramento ativo
- [ ] Kill switch pronto

## Proximos Passos

1. Seguir workflow para barra_elefante
2. Documentar aprendizados
3. Criar templates automatizados
4. Expandir para outras estrategias

## Referencias

- Pipeline: `../pipeline/README.md`
- Estrategias: `../strategies/README.md`
- Motores: `../engines/`
- MT5: `../mt5_integration/README.md`

