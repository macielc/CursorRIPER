"""
Verificar diferença no cálculo de rolling mean - Trade 510
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader

print("=" * 80)
print("VERIFICACAO ROLLING MEAN - BARRA 508")
print("=" * 80)

# MÉTODO 1: DataLoader (como Python faz)
print("\n[1] PYTHON DataLoader (dataset completo):")
loader = DataLoader('5m')
loader.load()

# Filtrar para outubro
df_python_full = loader.df[
    (loader.df['time'] >= '2025-10-01 00:00:00') &
    (loader.df['time'] < '2025-11-01 00:00:00')
].copy()

barra_508 = df_python_full.iloc[508]
print(f"  Barra 508: {barra_508['time']}")
print(f"  Amplitude: {barra_508['high'] - barra_508['low']:.2f}")
print(f"  Amplitude MA 20 (pré-computada): {barra_508['amplitude_ma_20']:.2f}")

# MÉTODO 2: Parquet direto (como Rust faz)
print("\n[2] RUST Parquet direto (só outubro):")
df_rust = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025.parquet")

# Filtrar 9h-15h (como Rust faz internamente)
df_rust['hora'] = pd.to_datetime(df_rust['time']).dt.hour
df_rust_filtered = df_rust[
    (df_rust['hora'] >= 9) & (df_rust['hora'] <= 15)
].copy().reset_index(drop=True)

barra_508_rust = df_rust_filtered.iloc[508]

# Calcular rolling mean manualmente
df_rust_filtered['amplitude'] = df_rust_filtered['high'] - df_rust_filtered['low']
df_rust_filtered['amplitude_ma_20'] = df_rust_filtered['amplitude'].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

print(f"  Barra 508: {barra_508_rust['time']}")
print(f"  Amplitude: {df_rust_filtered.iloc[508]['amplitude']:.2f}")
print(f"  Amplitude MA 20 (calculada inline): {df_rust_filtered.iloc[508]['amplitude_ma_20']:.2f}")

# COMPARAÇÃO
print("\n" + "=" * 80)
print("COMPARACAO")
print("=" * 80)
print(f"  Python (dataset completo): {barra_508['amplitude_ma_20']:.2f}")
print(f"  Rust (só outubro):         {df_rust_filtered.iloc[508]['amplitude_ma_20']:.2f}")
print(f"  Diferença:                 {abs(barra_508['amplitude_ma_20'] - df_rust_filtered.iloc[508]['amplitude_ma_20']):.2f}")

if abs(barra_508['amplitude_ma_20'] - df_rust_filtered.iloc[508]['amplitude_ma_20']) > 1.0:
    print("\n  DIVERGENCIA CONFIRMADA!")
    print("  Causa: Python usa histórico completo, Rust só usa outubro")
    print("\n  SOLUCAO:")
    print("  - Rust precisa receber dados anteriores a outubro")
    print("  - OU calcular médias com warmup (lookback antes de outubro)")
else:
    print("\n  Médias são idênticas - problema está em outro lugar!")

print("\n" + "=" * 80)

