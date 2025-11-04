# Integracao MT5 - MacTester

Este diretorio gerencia a integracao com o MetaTrader 5, incluindo geracao automatica de EAs e validacao de resultados.

## Objetivo

Garantir que estrategias validadas no Python/Rust possam ser executadas no MT5 com **resultados IDENTICOS**.

## Estrutura

```
mt5_integration/
├── ea_templates/      # Templates MQL5 base
│   ├── EA_BarraElefante_SIMPLES.mq5
│   ├── EA_BarraElefante_NOVO.mq5
│   ├── EA_BarraElefante_Python.mq5
│   └── EA_BarraElefante_CORRIGIDO.mq5
│
└── generated_eas/     # EAs gerados automaticamente
    └── (gerados pelo pipeline)
```

## Templates de EA

### 1. EA_BarraElefante_SIMPLES.mq5

**Uso**: Producao / Live Trading

**Caracteristicas**:
- Codigo limpo e otimizado
- Sem logs excessivos
- Performance maxima
- Apenas funcionalidades essenciais

**Quando usar**: Depois de tudo validado, para live trading.

### 2. EA_BarraElefante_NOVO.mq5

**Uso**: Versao atualizada com melhorias

**Caracteristicas**:
- Implementacoes mais recentes
- Otimizacoes de codigo
- Melhor gerenciamento de posicoes

**Quando usar**: Testes e validacao de novas features.

### 3. EA_BarraElefante_Python.mq5

**Uso**: Espelhar logica Python exatamente

**Caracteristicas**:
- Logica identica ao Python
- Calculos usando mesmas formulas
- Facilita comparacao

**Quando usar**: Validacao de alinhamento Python <-> MT5.

### 4. EA_BarraElefante_CORRIGIDO.mq5

**Uso**: Versao com correcoes especificas

**Caracteristicas**:
- Corrige bugs conhecidos
- Ajustes finos de timing
- Alinhamento de indicadores

**Quando usar**: Apos identificar divergencias.

## Geracao Automatica de EAs

### Via Pipeline

```bash
cd ../pipeline
python run_pipeline.py
# Escolher opcao 4: Gerar EA
```

### Processo

1. **Selecionar Setup Aprovado**:
   - Escolhe setup que passou em 3/4 criterios
   - Parametros otimizados

2. **Escolher Template**:
   - SIMPLES: Para producao
   - DEBUG: Para validacao
   - CUSTOM: Personalizado

3. **Geracao Automatica**:
   - Substitui parametros no template
   - Gera arquivo .mq5 pronto
   - Salva em `generated_eas/`

4. **Compilacao** (manual no MT5):
   - Abrir MT5 MetaEditor
   - Compilar o EA gerado
   - Verificar erros

## Validacao MT5 vs Python/Rust

### Metodologia RIGOROSA

**Regra Absoluta**: Resultados devem ser **100% IDENTICOS**

Nao aceitar:
- "Quase igual"
- "Diferenca de 5%"
- "Similar"

### Processo de Validacao

#### 1. Periodo Curto (1 mes)

```bash
# Python
cd ../engines/python
python mactester.py optimize --strategy barra_elefante --tests 1 --timeframe 5m --period "2024-01-01" "2024-01-31"

# MT5
# Rodar Strategy Tester com mesmo periodo

# Comparar
cd ../pipeline
python comparar_mt5_python.py --period "2024-01-01" "2024-01-31"
```

#### 2. Comparacao Trade-por-Trade

Verificar para CADA trade:
- Data/hora de entrada (exata)
- Preco de entrada
- Direcao (LONG/SHORT)
- Stop Loss
- Take Profit
- Data/hora de saida
- Preco de saida
- Razao de saida (SL/TP/outro)
- P&L

#### 3. Identificar Divergencias

Se houver diferenca:

**A. Logs Detalhados**

Python:
```python
# Adicionar prints em strategy.py
print(f"[{datetime}] Detectou elefante: corpo={corpo}, volume={vol}")
print(f"[{datetime}] Filtros: MM21={mm21_ok}, RSI={rsi_ok}")
print(f"[{datetime}] ENTRADA: preco={preco}, SL={sl}, TP={tp}")
```

MT5 (adicionar no EA):
```mql5
Print("Detectou elefante: corpo=", corpo, " volume=", vol);
Print("Filtros: MM21=", mm21_ok, " RSI=", rsi_ok);
Print("ENTRADA: preco=", preco, " SL=", sl, " TP=", tp);
```

**B. Comparar Logs Lado-a-Lado**

```bash
# Extrair logs
cd ../pipeline
python extrair_logs.py --python ../logs/python.log --mt5 ../logs/mt5.log

# Comparar
python comparar_logs.py
```

**C. Corrigir Causa Raiz**

Causas comuns de divergencia:
1. **Indicadores**: Calculo diferente (ex: MA no Python vs MT5)
2. **Timing**: Barra fechada vs barra aberta
3. **Arredondamento**: Precisao numerica
4. **Filtros**: Ordem de aplicacao diferente
5. **Volume**: Volume real vs tick volume

#### 4. Iterar Ate Identidade

Repetir:
1. Identificar divergencia
2. Criar logs detalhados
3. Comparar calculo por calculo
4. Corrigir codigo (Python OU MT5)
5. Re-testar
6. **Ate 100% identico**

## Exportacao de Dados do MT5

### Para Validacao

Script MQL5 para exportar trades:

```mql5
// Script_ExportarTrades.mq5
// Exporta historico de trades para CSV

// Uso:
// 1. Rodar backtest no Strategy Tester
// 2. Executar este script
// 3. Arquivo salvo em MQL5/Files/
```

### Formato de Export

CSV com colunas:
```
datetime_entry, price_entry, direction, sl, tp, datetime_exit, price_exit, exit_reason, pnl
```

## Instalacao de EA no MT5

### Passo 1: Copiar Arquivo

```bash
# Copiar EA gerado para pasta do MT5
copy generated_eas\EA_BarraElefante_Setup123.mq5 "C:\Users\...\MQL5\Experts\"
```

### Passo 2: Compilar

1. Abrir MetaEditor (F4 no MT5)
2. Abrir arquivo copiado
3. Clicar em "Compile" (F7)
4. Verificar erros/warnings

### Passo 3: Testar no Strategy Tester

1. View -> Strategy Tester (Ctrl+R)
2. Selecionar o EA
3. Configurar:
   - Symbol: WIN$N (ou atual)
   - Period: M5
   - Dates: 2024.01.01 - 2024.01.31
   - Model: Every tick (based on real ticks)
4. Start
5. Aguardar resultado

### Passo 4: Exportar Resultados

1. Backtest completo -> Aba "Results"
2. Botao direito -> "Export to CSV"
3. Salvar em `../../results/comparison/mt5/`

## Live Trading (CUIDADO!)

### APENAS apos:
1. Backtest Python validado
2. Backtest Rust validado
3. Python == Rust (100%)
4. MT5 == Python (100%)
5. Pipeline completo aprovado
6. Paper trading bem-sucedido

### Configuracao Segura

1. **Conta Demo Primeiro**
   - NUNCA comecar em conta real
   - Testar por 1-2 meses em demo

2. **Position Sizing Conservador**
   - Iniciar com 1 micro-contrato
   - Aumentar gradualmente

3. **Stop Loss Sempre Ativo**
   - NUNCA operar sem SL
   - SL baseado em ATR (conforme validado)

4. **Monitoramento 24/7**
   - Logs em tempo real
   - Alertas de problemas
   - Kill switch pronto

5. **Horarios Restritos**
   - Apenas horarios de pregao
   - Evitar abertura/fechamento
   - Evitar Roll de contratos

## Hibrido: Python + MT5

### Arquitetura Recomendada

```
Python (Cerebro)         MT5 (Executor)
    |                        |
    | <- Monitora mercado    |
    | <- Detecta sinais      |
    | ---> Envia ordem  ---> |
    |                   <--- | Confirma execucao
    | <--- Le posicao   <--- |
```

### Vantagens

- Python: Logica validada, facil ajustar
- MT5: Execucao robusta, baixa latencia
- Separacao: Decisao vs Execucao

### Implementacao (Futuro)

```python
# monitor.py
import MetaTrader5 as mt5

while True:
    # Detectar sinal
    if barra_elefante_detectada():
        # Enviar ordem ao MT5
        mt5.order_send(...)
    
    time.sleep(1)
```

EA no MT5:
```mql5
// EA_Executor.mq5
// Apenas executa ordens recebidas
// Nao tem logica de decisao
```

## Troubleshooting

### EA nao compila

- Verificar sintaxe MQL5
- Verificar versao do MT5
- Verificar includes necessarios

### Resultados divergentes

- Usar periodo curtissimo (1 dia)
- Logs ultra-detalhados
- Comparar candle por candle

### EA nao gera trades

- Verificar simbolo correto (WIN$N vs WIN$)
- Verificar horario de pregao
- Verificar dados disponíveis

## Proximos Passos

1. Gerar EA do setup aprovado
2. Testar em jan/2024
3. Comparar com Python
4. Corrigir divergencias
5. Re-testar ate identidade
6. Preparar para paper trading

## Referencias

- Templates: `ea_templates/`
- Gerador: `../pipeline/run_pipeline.py`
- Comparacao: `../pipeline/comparar_mt5_python.py`
- Documentacao MQL5: https://www.mql5.com/en/docs

