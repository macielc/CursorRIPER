"""
Criar dataset de 6 meses (Maio-Outubro 2025) com warmup de Abril
"""
import pandas as pd
from pathlib import Path

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_6Months_2025_WARMUP.parquet")

print("=" * 80)
print("CRIANDO DATASET 6 MESES COM WARMUP")
print("=" * 80)

# Carregar dataset completo
print(f"\nCarregando: {input_file}")
df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])

# Filtrar: ABRIL (warmup) + MAIO-OUTUBRO (target)
# Warmup: 2025-04-01 a 2025-04-30
# Target: 2025-05-01 a 2025-10-31
df_6months = df_full[
    (df_full['time'] >= '2025-04-01 00:00:00') &
    (df_full['time'] < '2025-11-01 00:00:00')
].copy()

# Adicionar flag warmup
df_6months['is_warmup'] = df_6months['time'] < '2025-05-01 00:00:00'

print(f"\nCandles totais: {len(df_6months)}")
print(f"  Warmup (Abril): {df_6months['is_warmup'].sum()}")
print(f"  Target (Maio-Out):  {(~df_6months['is_warmup']).sum()}")
print(f"\nRange: {df_6months['time'].min()} a {df_6months['time'].max()}")

# Salvar
df_6months.to_parquet(output_dataset, index=False)
print(f"\n[OK] Dataset salvo: {output_dataset}")
print(f"   Tamanho: {output_dataset.stat().st_size / 1024 / 1024:.2f} MB")

print("\n" + "=" * 80)
print("PROXIMOS PASSOS:")
print("=" * 80)
print("1. Executar Python backtest")
print("2. Executar Rust backtest")
print("3. Comparar resultados (TIME-BASED)")
print("=" * 80)

