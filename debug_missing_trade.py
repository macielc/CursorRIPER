"""
Debug: Por que Rust não detecta trade na barra 158?
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader

print("=" * 80)
print("DEBUG: TRADE FALTANDO NO RUST (entry_idx=158)")
print("=" * 80)

# Carregar dados da semana
loader = DataLoader('5m')
loader.load()
loader.df = loader.df[
    (loader.df['time'] >= '2025-10-20 00:00:00') &
    (loader.df['time'] < '2025-10-25 00:00:00')
].copy()

print(f"\nTotal candles: {len(loader.df)}")

# Analisar barras 155-165 (em torno de 158)
print("\n" + "=" * 80)
print("BARRAS 155-165 (em torno do trade faltando)")
print("=" * 80)

for i in range(155, min(165, len(loader.df))):
    row = loader.df.iloc[i]
    
    tipo = "BULLISH" if row['close'] > row['open'] else ("BEARISH" if row['close'] < row['open'] else "DOJI")
    
    print(f"\nBarra {i}:")
    print(f"  Time: {row['time']}")
    print(f"  OHLC: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    print(f"  ATR: {row.get('atr', row.get('atr_14', 'N/A')):.2f}")
    print(f"  Tipo: {tipo}")

# Carregar trades Python para ver qual foi o elefante
print("\n" + "=" * 80)
print("TRADE PYTHON #158")
print("=" * 80)

trades_py = pd.read_csv("results/validation/python_trades_week.csv")
trade_158 = trades_py[trades_py['entry_idx'] == 158]

if len(trade_158) > 0:
    t = trade_158.iloc[0]
    print(f"\nEntry idx: {t['entry_idx']}")
    print(f"Exit idx: {t['exit_idx']}")
    print(f"Type: {t['type']}")
    print(f"Entry: {t['entry']:.2f}")
    print(f"Exit: {t['exit']:.2f}")
    print(f"SL: {t['sl']:.2f}")
    print(f"TP: {t['tp']:.2f}")
    print(f"PnL: {t['pnl']:.2f}")
    
    # A entrada foi na barra 158, então o elefante deve ser na 157 (com slippage)
    # OU na 156 se houve rompimento na 157
    print("\n" + "=" * 80)
    print("ANALISE: Onde foi o sinal de elefante?")
    print("=" * 80)
    
    print("\nPython marca entrada na barra 158 (SHORT)")
    print("Com slippage de 1 barra, o sinal deve ter sido detectado na barra 157")
    print("E o elefante deve ter sido detectado na barra 156")
    
    print("\nBarra 156 (possivel elefante):")
    b156 = loader.df.iloc[156]
    print(f"  Time: {b156['time']}")
    print(f"  OHLC: O={b156['open']:.2f} H={b156['high']:.2f} L={b156['low']:.2f} C={b156['close']:.2f}")
    print(f"  Amplitude: {b156['high'] - b156['low']:.2f}")
    print(f"  Tipo: {'BULLISH' if b156['close'] > b156['open'] else 'BEARISH'}")
    
    print("\nBarra 157 (rompimento?):")
    b157 = loader.df.iloc[157]
    print(f"  Time: {b157['time']}")
    print(f"  OHLC: O={b157['open']:.2f} H={b157['high']:.2f} L={b157['low']:.2f} C={b157['close']:.2f}")
    print(f"  Low b157 < Low b156? {b157['low']} < {b156['low']} = {b157['low'] < b156['low']}")
    
    print("\nBarra 158 (entrada):")
    b158 = loader.df.iloc[158]
    print(f"  Time: {b158['time']}")
    print(f"  OHLC: O={b158['open']:.2f} H={b158['high']:.2f} L={b158['low']:.2f} C={b158['close']:.2f}")
    print(f"  Entry price: {b158['open']:.2f}")

print("\n" + "=" * 80)

