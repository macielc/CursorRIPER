# Motor Python - MacTester

Motor de backtest principal em Python com suporte a multicore.

## Arquivos

- `mactester.py` - Script principal de execucao
- `config.yaml` - Configuracoes globais
- `requirements.txt` - Dependencias Python
- `core/` - Modulos do motor
  - `backtest_engine.py` - Engine de backtest
  - `optimizer.py` - Otimizador multicore
  - `data_loader.py` - Carregador de Golden Data
  - `metrics.py` - Calculo de metricas
  - `walkforward.py` - Walk-Forward Analysis
  - `monte_carlo.py` - Simulacoes Monte Carlo
  - `reporter.py` - Geracao de relatorios

## Instalacao

```bash
pip install -r requirements.txt
```

## Uso Basico

### Backtest Simples
```bash
python mactester.py optimize --strategy barra_elefante --tests 1000 --timeframe 5m
```

### Backtest Completo (4.2M testes)
```bash
python mactester.py optimize --strategy barra_elefante --tests 4233600 --timeframe 5m
```

### Parametros Principais

- `--strategy` - Nome da estrategia (ex: barra_elefante)
- `--tests` - Numero de combinacoes a testar
- `--timeframe` - Timeframe (5m ou 15m)
- `--period` - Periodo customizado (ex: "2024-01-01" "2024-12-31")

## Performance

- Multicore: Usa todos os cores disponiveis (Pool)
- Barra de Progresso: Enlighten (tempo real)
- Checkpoint: Salva a cada 1000 testes
- Velocidade: ~100-500 testes/segundo (32 cores)

## Resultados

Resultados sao salvos em:
- `../../results/backtests/python/{strategy}_{timestamp}/`

Arquivos gerados:
- `results.csv` - Todos os testes
- `top_50.csv` - Top 50 setups por Sharpe
- `metrics_summary.json` - Resumo estatistico
- `trades_detail.csv` - Detalhes de cada trade

## Troubleshooting

### "No module named 'core'"
```bash
# Certifique-se de estar no diretorio correto
cd engines/python
```

### Memoria insuficiente
```bash
# Reduza o numero de testes ou processe em batches
python mactester.py optimize --strategy barra_elefante --tests 10000 --timeframe 5m
```

### Barra de progresso nao aparece
```bash
# Instale enlighten
pip install enlighten
```

