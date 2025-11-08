"""
Verificar alinhamento de dados entre Python e Rust
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader

print("=" * 80)
print("VERIFICACAO DE ALINHAMENTO")
print("=" * 80)

# PYTHON: DataLoader
print("\n[PYTHON] Carregando via DataLoader...")
loader = DataLoader('5m')
loader.load()
df_python_full = loader.df.copy()

# Filtrar para 2025-10-15
df_python_filtered = df_python_full[
    (df_python_full['time'] >= '2025-10-15 00:00:00') & 
    (df_python_full['time'] < '2025-10-16 00:00:00')
].copy()

print(f"Total candles Python (filtrado): {len(df_python_filtered)}")

# RUST: Parquet direto
print("\n[RUST] Carregando Parquet diretamente...")
df_rust = pd.read_parquet("data/golden/WINFUT_M5_2025-10-15.parquet")
print(f"Total candles Rust: {len(df_rust)}")

# Comparar barra 63
print("\n" + "=" * 80)
print("COMPARACAO BARRA 63")
print("=" * 80)

print("\nPYTHON Barra 63:")
if len(df_python_filtered) > 63:
    py_63 = df_python_filtered.iloc[63]
    print(f"  Time: {py_63['time']}")
    print(f"  OHLC: O={py_63['open']:.2f} H={py_63['high']:.2f} L={py_63['low']:.2f} C={py_63['close']:.2f}")
    print(f"  Tipo: {'BULLISH' if py_63['close'] > py_63['open'] else 'BEARISH'}")
else:
    print("  FORA DO RANGE!")

print("\nRUST Barra 63:")
if len(df_rust) > 63:
    rust_63 = df_rust.iloc[63]
    print(f"  Time: {rust_63['time']}")
    print(f"  OHLC: O={rust_63['open']:.2f} H={rust_63['high']:.2f} L={rust_63['low']:.2f} C={rust_63['close']:.2f}")
    print(f"  Tipo: {'BULLISH' if rust_63['close'] > rust_63['open'] else 'BEARISH'}")
else:
    print("  FORA DO RANGE!")

# Comparar barra 64
print("\n" + "=" * 80)
print("COMPARACAO BARRA 64")
print("=" * 80)

print("\nPYTHON Barra 64:")
if len(df_python_filtered) > 64:
    py_64 = df_python_filtered.iloc[64]
    print(f"  Time: {py_64['time']}")
    print(f"  OHLC: O={py_64['open']:.2f} H={py_64['high']:.2f} L={py_64['low']:.2f} C={py_64['close']:.2f}")
    print(f"  Tipo: {'BULLISH' if py_64['close'] > py_64['open'] else 'BEARISH'}")
else:
    print("  FORA DO RANGE!")

print("\nRUST Barra 64:")
if len(df_rust) > 64:
    rust_64 = df_rust.iloc[64]
    print(f"  Time: {rust_64['time']}")
    print(f"  OHLC: O={rust_64['open']:.2f} H={rust_64['high']:.2f} L={rust_64['low']:.2f} C={rust_64['close']:.2f}")
    print(f"  Tipo: {'BULLISH' if rust_64['close'] > rust_64['open'] else 'BEARISH'}")
else:
    print("  FORA DO RANGE!")

# Verificar se times estao alinhados
print("\n" + "=" * 80)
print("PRIMEIRAS 10 BARRAS")
print("=" * 80)

print("\nPYTHON:")
print(df_python_filtered[['time', 'open', 'high', 'low', 'close']].head(10))

print("\nRUST:")
print(df_rust[['time', 'open', 'high', 'low', 'close']].head(10))

print("\n" + "=" * 80)

