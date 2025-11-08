"""
Executar Python backtest para 6 meses (Maio-Outubro 2025)
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.backtest_engine import BacktestEngine

print("=" * 80)
print("PYTHON BACKTEST - 6 MESES (Maio-Outubro 2025)")
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

print("\n[1/3] CARREGANDO DATASET...")
df = pd.read_parquet("data/golden/WINFUT_M5_6Months_2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour

print(f"   Total candles: {len(df)}")
print(f"   Range: {df['time'].min()} a {df['time'].max()}")

# Filtrar 9h-15h
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy()

print(f"\n   Apos filtro 9h-15h: {len(df_filtered)} candles")
print(f"   Warmup: {df_filtered['is_warmup'].sum()}")
print(f"   Target: {(~df_filtered['is_warmup']).sum()}")

# Pre-computar medias
print("\n[2/3] CALCULANDO MEDIAS MOVEIS...")

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

# Executar backtest
print("\n[3/3] EXECUTANDO BACKTEST...")
engine = BacktestEngine(df_filtered, verbose=False)
result = engine.run_strategy('barra_elefante', full_params)

trades_all = result['trades']

# Filtrar trades: Apenas target period (Maio-Out)
df_filtered = df_filtered.reset_index(drop=True)
trades_target = []

for trade in trades_all:
    entry_idx = trade['entry_idx']
    if entry_idx < len(df_filtered) and not df_filtered.iloc[entry_idx]['is_warmup']:
        trades_target.append(trade)

print(f"\n   Trades totais (com warmup): {len(trades_all)}")
print(f"   Trades no target period: {len(trades_target)}")

# Salvar
output_file = "results/validation/python_trades_6months.csv"
Path(output_file).parent.mkdir(parents=True, exist_ok=True)
trades_df = pd.DataFrame(trades_target)
trades_df.to_csv(output_file, index=False)

print(f"\n   Trades salvos: {output_file}")

# Resumo
if len(trades_target) > 0:
    pnl_total = sum([t['pnl'] for t in trades_target])
    wins = sum([1 for t in trades_target if t['pnl'] > 0])
    losses = sum([1 for t in trades_target if t['pnl'] < 0])
    win_rate = (wins / len(trades_target)) * 100 if len(trades_target) > 0 else 0
    
    print(f"\n   PnL total: {pnl_total:.2f}")
    print(f"   Trades: {len(trades_target)}")
    print(f"   Wins: {wins} ({win_rate:.1f}%)")
    print(f"   Losses: {losses}")

print("\n" + "=" * 80)
print("PROXIMO PASSO: Executar Rust backtest")
print("=" * 80)

