"""
Executar Python backtest com MESMO dataset de warmup que Rust
Para validação "apples-to-apples"
"""
import pandas as pd
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.backtest_engine import BacktestEngine

print("=" * 80)
print("PYTHON BACKTEST COM WARMUP (Setembro + Outubro)")
print("=" * 80)

# Parametros
full_params = {
    'min_amplitude_mult': 2.0,
    'min_volume_mult': 1.5,
    'max_sombra_pct': 0.4,
    'lookback_amplitude': 20,
    'horario_inicio': 9,
    'minuto_inicio': 0,
    'horario_fim': 14,
    'minuto_fim': 55,
    'horario_fechamento': 15,
    'minuto_fechamento': 0,
    'sl_atr_mult': 2.0,
    'tp_atr_mult': 3.0,
    'usar_trailing': False
}

print("\n[1/3] CARREGANDO DATASET COM WARMUP...")
print("   Dataset: WINFUT_M5_Month_Oct2025_WARMUP.parquet")

# Carregar dataset com warmup
df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])

print(f"   Total candles: {len(df)}")
print(f"   Warmup (setembro): {df['is_warmup'].sum()}")
print(f"   Target (outubro):  {(~df['is_warmup']).sum()}")
print(f"   Range: {df['time'].min()} a {df['time'].max()}")

# Filtrar 9h-15h (como Rust faz)
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy()

print(f"\n   Apos filtro 9h-15h: {len(df_filtered)} candles")
print(f"   Warmup: {df_filtered['is_warmup'].sum()}")
print(f"   Target: {(~df_filtered['is_warmup']).sum()}")

# Pre-computar medias (rolling mean com shift)
print("\n[2/3] CALCULANDO MEDIAS MOVEIS (com warmup)...")

# Renomear atr_14 para atr se necessário
if 'atr_14' in df_filtered.columns and 'atr' not in df_filtered.columns:
    df_filtered['atr'] = df_filtered['atr_14']

df_filtered['amplitude'] = df_filtered['high'] - df_filtered['low']
df_filtered['amplitude_ma_20'] = df_filtered['amplitude'].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

if 'volume' in df_filtered.columns:
    vol_col = 'volume'
elif 'real_volume' in df_filtered.columns:
    vol_col = 'real_volume'
elif 'tick_volume' in df_filtered.columns:
    vol_col = 'tick_volume'
else:
    print("ERRO: Nenhuma coluna de volume!")
    sys.exit(1)

df_filtered['volume_ma_20'] = df_filtered[vol_col].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

print("   OK - Medias calculadas")

# Executar backtest em TODO o dataset (warmup + target)
print("\n[3/3] EXECUTANDO BACKTEST...")
engine = BacktestEngine(df_filtered, verbose=False)
result = engine.run_strategy('barra_elefante', full_params)

trades_all = result['trades']

# Filtrar trades: Apenas trades cuja ENTRADA foi em outubro (is_warmup=False)
df_filtered = df_filtered.reset_index(drop=True)
trades_outubro = []

for trade in trades_all:
    entry_idx = trade['entry_idx']
    if entry_idx < len(df_filtered) and not df_filtered.iloc[entry_idx]['is_warmup']:
        trades_outubro.append(trade)

print(f"\n   Trades totais: {len(trades_all)}")
print(f"   Trades em outubro: {len(trades_outubro)}")

# Salvar
output_file = "results/validation/python_trades_month_WARMUP.csv"
Path(output_file).parent.mkdir(parents=True, exist_ok=True)
trades_df = pd.DataFrame(trades_outubro)
trades_df.to_csv(output_file, index=False)

print(f"\n   Trades salvos: {output_file}")

# Resumo
if len(trades_outubro) > 0:
    pnl_total = sum([t['pnl'] for t in trades_outubro])
    print(f"\n   PnL total: {pnl_total:.2f}")
    print(f"   Trades: {len(trades_outubro)}")
    
    # Mostrar primeiros 5
    print("\n   Primeiros 5 trades:")
    for i, trade in enumerate(trades_outubro[:5]):
        print(f"      {i+1}. Entry {trade['entry_idx']}: {trade['type']} entry={trade['entry']:.2f} pnl={trade['pnl']:.2f}")

print("\n" + "=" * 80)
print("PROXIMO PASSO: python compare_month_warmup.py")
print("=" * 80)

