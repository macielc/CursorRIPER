# Dados Historicos - MacTester

Este diretorio contem os dados historicos (Golden Data) extraidos do MetaTrader 5.

## Golden Data

### O que eh Golden Data?

Golden Data sao dados historicos COMPLETOS e IMUTAVEIS extraidos diretamente do MT5, contendo:

- **OHLCV**: Open, High, Low, Close, Volume
- **Indicadores Pre-Calculados**: MM21, RSI, ATR, Volume_MA, etc
- **Precisao Total**: Valores exatos do MT5
- **Periodo Completo**: 5 anos (2020-2025)
- **Timeframes**: M5 (5min) e M15 (15min)

### Por que "Golden"?

- Sao a **fonte da verdade** para todos os backtests
- **Imutaveis** - nunca devem ser modificados
- **Reproduziveis** - sempre produzem mesmos resultados
- **Realistas** - dados reais de mercado, nao simulados

## Arquivos

### `golden/WINFUT_M5_Golden_Data.csv`

Dados do WIN$ (Futuro de Mini-Indice) em timeframe M5 (5 minutos).

**Colunas**:
- `datetime` - Data/hora do candle (formato: YYYY-MM-DD HH:MM:SS)
- `open` - Preco de abertura
- `high` - Maxima do periodo
- `low` - Minima do periodo
- `close` - Preco de fechamento
- `volume` - Volume negociado
- `tick_volume` - Volume de ticks
- `ma_21` - Media Movel 21 periodos
- `rsi_14` - RSI 14 periodos
- `atr_14` - ATR 14 periodos
- `volume_ma_20` - Media de volume 20 periodos
- [outros indicadores...]

**Tamanho**: ~500 MB (5 anos de dados M5)
**Linhas**: ~1.5 milhoes de candles

### `golden/WINFUT_M15_Golden_Data.csv`

Dados do WIN$ em timeframe M15 (15 minutos).

**Colunas**: Mesmas do M5
**Tamanho**: ~170 MB (5 anos de dados M15)
**Linhas**: ~500 mil candles

## Como Foram Extraidos

### Script MT5

Os dados foram extraidos usando script MQL5:

```mql5
// ExportarDadosCompleto_MT5.mq5
// Exporta OHLCV + todos indicadores para CSV
```

### Periodo de Extracao

- **Inicio**: 01/01/2020 00:00:00
- **Fim**: 31/12/2024 23:59:59
- **Horario de Pregao**: 09:00 - 18:00 (BRT)
- **Dias Uteis**: Segunda a Sexta

### Indicadores Incluidos

Todos calculados pelo MT5 com precisao total:

1. **Media Movel (MA)**:
   - MA_21: Media Simples 21 periodos
   - MA_50: Media Simples 50 periodos (se disponivel)

2. **RSI (Relative Strength Index)**:
   - RSI_14: 14 periodos

3. **ATR (Average True Range)**:
   - ATR_14: 14 periodos
   - Usado para SL/TP dinamicos

4. **Volume**:
   - Volume: Volume negociado real
   - Tick_Volume: Numero de alteracoes de preco
   - Volume_MA_20: Media de volume 20 periodos

5. **Outros** (se disponivel):
   - MACD
   - Bandas de Bollinger
   - Estocástico

## Uso nos Backtests

### Python

```python
import pandas as pd

# Carregar Golden Data M5
df = pd.read_csv('data/golden/WINFUT_M5_Golden_Data.csv', 
                 parse_dates=['datetime'])

# Filtrar periodo especifico
mask = (df['datetime'] >= '2024-01-01') & (df['datetime'] <= '2024-01-31')
df_jan = df[mask]

# Rodar backtest
# ...
```

### Rust

```rust
// Carregar via csv crate
let mut rdr = csv::Reader::from_path("data/golden/WINFUT_M5_Golden_Data.csv")?;

for result in rdr.deserialize() {
    let candle: Candle = result?;
    // Processar candle
}
```

## Validacao de Qualidade

### Checagens Automaticas

Os dados foram validados para:

1. **Sem Gaps**: Nao ha lacunas nos horarios de pregao
2. **Ordem Cronologica**: Dados ordenados corretamente
3. **Valores Validos**: Nao ha NaN, Inf ou valores negativos
4. **OHLC Consistente**: High >= Open/Close, Low <= Open/Close
5. **Indicadores Validos**: Todos calculados corretamente

### Script de Validacao

```bash
cd data
python ver_colunas.py
```

Verifica:
- Numero de linhas
- Colunas presentes
- Tipos de dados
- Range de datas
- Estatisticas basicas

## Atualizacao dos Dados

### IMPORTANTE: NAO modificar os arquivos originais!

Se precisar atualizar ou estender os dados:

1. Extrair novos dados do MT5
2. Salvar em arquivo separado com timestamp
3. Validar qualidade
4. Substituir apenas se necessario
5. Manter backup do original

### Script de Atualizacao (Futuro)

```bash
# AINDA NAO IMPLEMENTADO
cd ../
python scripts/update_golden_data.py --start 2025-01-01 --end 2025-12-31
```

## Espaco em Disco

Total utilizado: ~670 MB

- WINFUT_M5_Golden_Data.csv: ~500 MB
- WINFUT_M15_Golden_Data.csv: ~170 MB

**Nota**: Arquivos grandes! Git LFS recomendado se versionar.

## Troubleshooting

### Erro ao carregar arquivo

```python
# Memoria insuficiente? Carregar em chunks
chunks = pd.read_csv('WINFUT_M5_Golden_Data.csv', chunksize=100000)
for chunk in chunks:
    # Processar chunk
    pass
```

### Dados corrompidos

```bash
# Re-extrair do MT5
# Ou restaurar backup
```

### Faltam indicadores

Alguns indicadores podem nao estar presentes. Verificar com:

```python
import pandas as pd
df = pd.read_csv('WINFUT_M5_Golden_Data.csv', nrows=5)
print(df.columns.tolist())
```

Se faltar, calcular manualmente:

```python
# Exemplo: Calcular MA21
df['ma_21'] = df['close'].rolling(window=21).mean()
```

## Formato Parquet (Opcional)

Para melhor performance, considere converter para Parquet:

```python
import pandas as pd

df = pd.read_csv('WINFUT_M5_Golden_Data.csv')
df.to_parquet('WINFUT_M5_Golden_Data.parquet', compression='snappy')
```

Vantagens:
- 5-10x menor em disco
- 10-100x mais rapido para carregar
- Tipos de dados preservados

## Proximos Passos

1. Validar qualidade dos dados existentes
2. Documentar cada coluna detalhadamente
3. Criar scripts de atualizacao automatica
4. Considerar conversao para Parquet
5. Implementar versionamento (Git LFS)

## Referencias

- Script de extracao: `../mt5_integration/export_data.mq5` (se disponivel)
- Validacao: `ver_colunas.py`
- Documentacao MT5: https://www.mql5.com/

