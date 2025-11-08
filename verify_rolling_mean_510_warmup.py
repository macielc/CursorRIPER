"""
Verificar rolling mean na barra 508 COM WARMUP
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader

print("=" * 80)
print("VERIFICACAO ROLLING MEAN - BARRA 508 COM WARMUP")
print("=" * 80)

# MÉTODO 1: DataLoader (dataset completo - como Python faz)
print("\n[1] PYTHON DataLoader (dataset completo 2022-2025):")
loader = DataLoader('5m')
loader.load()

df_python_full = loader.df[
    (loader.df['time'] >= '2025-10-01 00:00:00') &
    (loader.df['time'] < '2025-11-01 00:00:00')
].copy().reset_index(drop=True)

barra_508 = df_python_full.iloc[508]
print(f"  Barra 508: {barra_508['time']}")
print(f"  Amplitude: {barra_508['high'] - barra_508['low']:.2f}")
print(f"  Amplitude MA 20 (pre-computada): {barra_508['amplitude_ma_20']:.2f}")

# MÉTODO 2: Dataset com WARMUP (como Rust agora faz)
print("\n[2] RUST Dataset com WARMUP (setembro + outubro):")
df_warmup = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")

# Filtrar 9h-15h
df_warmup['hora'] = pd.to_datetime(df_warmup['time']).dt.hour
df_warmup_filtered = df_warmup[
    (df_warmup['hora'] >= 9) & (df_warmup['hora'] <= 15)
].copy().reset_index(drop=True)

# Calcular rolling mean
df_warmup_filtered['amplitude'] = df_warmup_filtered['high'] - df_warmup_filtered['low']
df_warmup_filtered['amplitude_ma_20'] = df_warmup_filtered['amplitude'].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

# Filtrar só outubro para encontrar barra 508
df_outubro = df_warmup_filtered[df_warmup_filtered['is_warmup'] == False].copy().reset_index(drop=True)

barra_508_rust = df_outubro.iloc[508]
# Precisamos encontrar o índice original (antes de filtrar outubro)
idx_original = df_warmup_filtered[
    (df_warmup_filtered['time'] == barra_508_rust['time'])
].index[0]

print(f"  Barra 508 (outubro): {barra_508_rust['time']}")
print(f"  Indice original (setembro+outubro): {idx_original}")
print(f"  Amplitude: {df_warmup_filtered.loc[idx_original, 'amplitude']:.2f}")
print(f"  Amplitude MA 20 (calculada com warmup): {df_warmup_filtered.loc[idx_original, 'amplitude_ma_20']:.2f}")

# COMPARAÇÃO
print("\n" + "=" * 80)
print("COMPARACAO")
print("=" * 80)
print(f"  Python (dataset completo 2022-2025): {barra_508['amplitude_ma_20']:.2f}")
print(f"  Rust (set+out com warmup):           {df_warmup_filtered.loc[idx_original, 'amplitude_ma_20']:.2f}")
print(f"  Diferenca:                           {abs(barra_508['amplitude_ma_20'] - df_warmup_filtered.loc[idx_original, 'amplitude_ma_20']):.2f}")

if abs(barra_508['amplitude_ma_20'] - df_warmup_filtered.loc[idx_original, 'amplitude_ma_20']) < 5.0:
    print("\n  [OK] Medias praticamente identicas!")
    print("  Problema deve estar em outro lugar...")
else:
    print("\n  [PROBLEMA] Medias ainda divergentes!")
    print("  Warmup de 1 mes nao eh suficiente!")
    print("  Python usa 3 ANOS de historico!")

print("\n" + "=" * 80)

