"""
Debug Rust - Ler Parquet e simular detecção de sinais
"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("DEBUG RUST - ANÁLISE DE SINAIS")
print("=" * 80)

# Carregar dados
data_file = Path("data/golden/WINFUT_M5_2025-10-15.parquet")
df = pd.read_parquet(data_file)

print(f"\nTotal candles: {len(df)}")
print(f"\nPrimeiras 5 barras:")
print(df.head())

# Filtrar barras de interesse (60-70)
print("\n" + "=" * 80)
print("BARRAS 60-70 (onde está o trade)")
print("=" * 80)

for i in range(60, min(70, len(df))):
    row = df.iloc[i]
    print(f"\nBarra {i}:")
    print(f"  Time: {row.get('time', 'N/A')}")
    print(f"  OHLC: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    print(f"  ATR: {row.get('atr', row.get('atr_14', 'N/A')):.2f}")
    print(f"  Volume: {row.get('volume', 'N/A')}")
    
    # Detectar tipo de barra
    is_bullish = row['close'] > row['open']
    is_bearish = row['close'] < row['open']
    
    if is_bullish:
        print(f"  Tipo: BULLISH")
    elif is_bearish:
        print(f"  Tipo: BEARISH")
    else:
        print(f"  Tipo: DOJI")

print("\n" + "=" * 80)
print("TRADE RUST (do CSV)")
print("=" * 80)

rust_trades = pd.read_csv("results/validation/rust_trades_20251015_v2_trades_detailed.csv")
print(rust_trades)

if len(rust_trades) > 0:
    trade = rust_trades.iloc[0]
    
    entry_idx = int(trade['entry_idx'])
    exit_idx = int(trade['exit_idx'])
    
    print(f"\nTrade Rust:")
    print(f"  Entry Idx: {entry_idx}")
    print(f"  Exit Idx: {exit_idx}")
    print(f"  Entry Price: {trade['entry']:.2f}")
    print(f"  SL: {trade['sl']:.2f}")
    print(f"  Exit Price: {trade['exit']:.2f}")
    print(f"  PnL: {trade['pnl']:.2f}")
    
    print(f"\nBarra de ENTRADA Rust (idx={entry_idx}):")
    entry_candle = df.iloc[entry_idx]
    print(f"  Time: {entry_candle.get('time', 'N/A')}")
    print(f"  OHLC: O={entry_candle['open']:.2f} H={entry_candle['high']:.2f} L={entry_candle['low']:.2f} C={entry_candle['close']:.2f}")
    print(f"  ATR: {entry_candle.get('atr', entry_candle.get('atr_14', 'N/A')):.2f}")
    
    print(f"\nBarra de SAÍDA Rust (idx={exit_idx}):")
    exit_candle = df.iloc[exit_idx]
    print(f"  Time: {exit_candle.get('time', 'N/A')}")
    print(f"  OHLC: O={exit_candle['open']:.2f} H={exit_candle['high']:.2f} L={exit_candle['low']:.2f} C={exit_candle['close']:.2f}")
    
    print(f"\n❌ PROBLEMA:")
    print(f"  Rust está entrando na barra {entry_idx}, mas Python entra na barra 64!")
    print(f"  Rust usa Entry = {trade['entry']:.2f}, mas deveria ser OPEN da barra 64 = {df.iloc[64]['open']:.2f}")

print("\n" + "=" * 80)

