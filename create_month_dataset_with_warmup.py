"""
Criar dataset de OUTUBRO com WARMUP de 30 dias (Setembro)
Para garantir que médias móveis sejam calculadas corretamente
"""
import pandas as pd
from pathlib import Path

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")

print("=" * 80)
print("CRIANDO DATASET OUTUBRO COM WARMUP")
print("=" * 80)

# Carregar dataset completo
print(f"\nCarregando: {input_file}")
df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])

# Filtrar: SETEMBRO + OUTUBRO (warmup + target)
# Warmup: 2025-09-01 a 2025-09-30
# Target: 2025-10-01 a 2025-10-31
df_warmup = df_full[
    (df_full['time'] >= '2025-09-01 00:00:00') &
    (df_full['time'] < '2025-11-01 00:00:00')
].copy()

# Adicionar flag para identificar período de warmup vs target
df_warmup['is_warmup'] = df_warmup['time'] < '2025-10-01 00:00:00'

print(f"\nCandles totais: {len(df_warmup)}")
print(f"  Warmup (Setembro): {df_warmup['is_warmup'].sum()}")
print(f"  Target (Outubro):  {(~df_warmup['is_warmup']).sum()}")
print(f"\nRange: {df_warmup['time'].min()} a {df_warmup['time'].max()}")

# Salvar
df_warmup.to_parquet(output_dataset, index=False)
print(f"\n[OK] Dataset salvo: {output_dataset}")
print(f"   Tamanho: {output_dataset.stat().st_size / 1024 / 1024:.2f} MB")

print("\n" + "=" * 80)
print("PROXIMOS PASSOS:")
print("=" * 80)
print("1. Modificar Rust para:")
print("   - Carregar dataset com warmup")
print("   - Calcular medias em TODO o dataset (warmup + target)")
print("   - So salvar trades de outubro (is_warmup == false)")
print("\n2. Re-executar validacao mensal")
print("=" * 80)

