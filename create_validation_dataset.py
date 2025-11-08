"""
Criar dataset filtrado para validação (2025-10-15)
"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("CRIANDO DATASET DE VALIDACAO - 2025-10-15")
print("=" * 80)

# Carregar dataset completo
input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_file = Path("data/golden/WINFUT_M5_2025-10-15.parquet")

print(f"\nInput: {input_file}")
print(f"Output: {output_file}")

# Carregar
df = pd.read_parquet(input_file)
print(f"\nTotal candles original: {len(df):,}")

# Converter time
df['time'] = pd.to_datetime(df['time'])

# Filtrar 2025-10-15
df_filtered = df[(df['time'] >= '2025-10-15 00:00:00') & (df['time'] < '2025-10-16 00:00:00')].copy()

print(f"Candles filtrados (2025-10-15): {len(df_filtered):,}")
print(f"Range: {df_filtered['time'].min()} a {df_filtered['time'].max()}")

# Salvar
df_filtered.to_parquet(output_file, index=False)

print(f"\n✅ Dataset criado: {output_file}")
print(f"   Tamanho: {output_file.stat().st_size / 1024:.1f} KB")
print("=" * 80)

