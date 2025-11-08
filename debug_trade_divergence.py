"""
Debug profundo: Comparar trade bar-by-bar (Python vs Rust)
Foco nos 3 trades com maior divergência de PnL
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.backtest_engine import BacktestEngine

print("=" * 80)
print("DEBUG PROFUNDO: TRADE-BY-TRADE")
print("=" * 80)

# Carregar trades
python_trades = pd.read_csv("results/validation/python_trades_month_WARMUP.csv")
rust_trades = pd.read_csv("results/validation/rust_trades_month_WARMUP_trades_detailed.csv")

# Trades com maior divergência
divergent_trades = [
    {'entry': 145375.00, 'type': 'LONG', 'py_pnl': -56.00, 'rust_pnl': 945.42},
    {'entry': 145385.00, 'type': 'LONG', 'py_pnl': 750.00, 'rust_pnl': 1750.73},
    {'entry': 148707.00, 'type': 'SHORT', 'py_pnl': 889.00, 'rust_pnl': 1608.84},
]

# Carregar dataset
df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

# Renomear atr_14 para atr
if 'atr_14' in df_filtered.columns and 'atr' not in df_filtered.columns:
    df_filtered['atr'] = df_filtered['atr_14']

print(f"\nDataset: {len(df_filtered)} candles")
print(f"Range: {df_filtered['time'].min()} a {df_filtered['time'].max()}")

for idx, trade_info in enumerate(divergent_trades, 1):
    print("\n" + "=" * 80)
    print(f"TRADE {idx}/3: {trade_info['type']} entry={trade_info['entry']:.2f}")
    print("=" * 80)
    
    # Encontrar trade no Python
    py_mask = (python_trades['type'].str.upper() == trade_info['type']) & \
              (abs(python_trades['entry'] - trade_info['entry']) < 1.0)
    
    if not py_mask.any():
        print(f"  ERRO: Trade nao encontrado no Python!")
        continue
    
    py_trade = python_trades[py_mask].iloc[0]
    
    # Encontrar trade no Rust
    rust_mask = (rust_trades['type'].str.upper() == trade_info['type']) & \
                (abs(rust_trades['entry'] - trade_info['entry']) < 1.0)
    
    if not rust_mask.any():
        print(f"  ERRO: Trade nao encontrado no Rust!")
        continue
    
    rust_trade = rust_trades[rust_mask].iloc[0]
    
    print(f"\n[PYTHON]")
    print(f"  Entry idx: {py_trade['entry_idx']}")
    print(f"  Exit idx:  {py_trade['exit_idx']}")
    print(f"  Entry:     {py_trade['entry']:.2f}")
    print(f"  Exit:      {py_trade['exit']:.2f}")
    print(f"  SL:        {py_trade.get('sl', 'N/A')}")
    print(f"  TP:        {py_trade.get('tp', 'N/A')}")
    print(f"  PnL:       {py_trade['pnl']:.2f}")
    print(f"  Reason:    {py_trade.get('exit_reason', 'N/A')}")
    
    print(f"\n[RUST]")
    print(f"  Entry idx: {rust_trade['entry_idx']}")
    print(f"  Exit idx:  {rust_trade['exit_idx']}")
    print(f"  Entry:     {rust_trade['entry']:.2f}")
    print(f"  Exit:      {rust_trade['exit']:.2f}")
    print(f"  SL:        {rust_trade.get('sl', 'N/A')}")
    print(f"  TP:        {rust_trade.get('tp', 'N/A')}")
    print(f"  PnL:       {rust_trade.get('pnl', 'N/A'):.2f}")
    print(f"  Reason:    {rust_trade.get('exit_reason', 'N/A')}")
    
    # ANÁLISE DETALHADA
    print(f"\n[DIVERGENCIAS]")
    
    # Entry
    entry_diff = abs(py_trade['entry'] - rust_trade['entry'])
    if entry_diff > 0.01:
        print(f"  Entry:  Python={py_trade['entry']:.2f} Rust={rust_trade['entry']:.2f} (diff={entry_diff:.2f})")
    else:
        print(f"  Entry:  IDENTICO ({py_trade['entry']:.2f})")
    
    # Exit
    exit_diff = abs(py_trade['exit'] - rust_trade['exit'])
    if exit_diff > 0.01:
        print(f"  Exit:   Python={py_trade['exit']:.2f} Rust={rust_trade['exit']:.2f} (diff={exit_diff:.2f}) [PROBLEMA!]")
    else:
        print(f"  Exit:   IDENTICO ({py_trade['exit']:.2f})")
    
    # SL
    if 'sl' in py_trade and 'sl' in rust_trade:
        sl_diff = abs(float(py_trade['sl']) - float(rust_trade['sl']))
        if sl_diff > 0.01:
            print(f"  SL:     Python={py_trade['sl']:.2f} Rust={rust_trade['sl']:.2f} (diff={sl_diff:.2f}) [PROBLEMA!]")
        else:
            print(f"  SL:     IDENTICO ({py_trade['sl']:.2f})")
    
    # TP
    if 'tp' in py_trade and 'tp' in rust_trade:
        tp_diff = abs(float(py_trade['tp']) - float(rust_trade['tp']))
        if tp_diff > 0.01:
            print(f"  TP:     Python={py_trade['tp']:.2f} Rust={rust_trade['tp']:.2f} (diff={tp_diff:.2f}) [PROBLEMA!]")
        else:
            print(f"  TP:     IDENTICO ({py_trade['tp']:.2f})")
    
    # Exit reason
    py_reason = str(py_trade.get('exit_reason', 'N/A'))
    rust_reason = str(rust_trade.get('exit_reason', 'N/A'))
    if py_reason != rust_reason:
        print(f"  Reason: Python={py_reason} Rust={rust_reason} [PROBLEMA!]")
    else:
        print(f"  Reason: IDENTICO ({py_reason})")
    
    # PnL
    pnl_diff = abs(py_trade['pnl'] - rust_trade['pnl'])
    print(f"  PnL:    Python={py_trade['pnl']:.2f} Rust={rust_trade['pnl']:.2f} (diff={pnl_diff:.2f}) [CRITICO!]")
    
    # Mostrar barras de entrada/saída
    print(f"\n[BARRAS DE ENTRADA/SAIDA - PYTHON]")
    
    # Python entry bar
    py_entry_idx = int(py_trade['entry_idx'])
    if py_entry_idx < len(df_filtered):
        entry_bar = df_filtered.iloc[py_entry_idx]
        print(f"  Entry bar {py_entry_idx}: {entry_bar['time']}")
        print(f"    OHLC: O={entry_bar['open']:.2f} H={entry_bar['high']:.2f} L={entry_bar['low']:.2f} C={entry_bar['close']:.2f}")
        print(f"    ATR: {entry_bar['atr']:.2f}")
    
    # Python exit bar
    py_exit_idx = int(py_trade['exit_idx'])
    if py_exit_idx < len(df_filtered):
        exit_bar = df_filtered.iloc[py_exit_idx]
        print(f"  Exit bar {py_exit_idx}: {exit_bar['time']}")
        print(f"    OHLC: O={exit_bar['open']:.2f} H={exit_bar['high']:.2f} L={exit_bar['low']:.2f} C={exit_bar['close']:.2f}")
    
    print(f"\n[BARRAS DE ENTRADA/SAIDA - RUST]")
    
    # Rust entry bar (precisa ajustar índice pois Rust tem setembro+outubro)
    rust_entry_idx = int(rust_trade['entry_idx'])
    if rust_entry_idx < len(df_filtered):
        entry_bar_rust = df_filtered.iloc[rust_entry_idx]
        print(f"  Entry bar {rust_entry_idx}: {entry_bar_rust['time']}")
        print(f"    OHLC: O={entry_bar_rust['open']:.2f} H={entry_bar_rust['high']:.2f} L={entry_bar_rust['low']:.2f} C={entry_bar_rust['close']:.2f}")
        print(f"    ATR: {entry_bar_rust['atr']:.2f}")
    
    # Rust exit bar
    rust_exit_idx = int(rust_trade['exit_idx'])
    if rust_exit_idx < len(df_filtered):
        exit_bar_rust = df_filtered.iloc[rust_exit_idx]
        print(f"  Exit bar {rust_exit_idx}: {exit_bar_rust['time']}")
        print(f"    OHLC: O={exit_bar_rust['open']:.2f} H={exit_bar_rust['high']:.2f} L={exit_bar_rust['low']:.2f} C={exit_bar_rust['close']:.2f}")

print("\n" + "=" * 80)
print("ANALISE COMPLETA")
print("=" * 80)
print("\nProximos passos:")
print("1. Identificar qual campo diverge (Exit? SL? TP? Reason?)")
print("2. Rastrear calculo especifico no codigo Python/Rust")
print("3. Corrigir logica divergente")
print("4. Re-executar validacao")
print("=" * 80)

