"""
Criar dataset completo (TODO o historico) com warmup de 1 mes
"""
import pandas as pd
from pathlib import Path

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_FULL_HISTORY_WARMUP.parquet")

print("=" * 80)
print("CRIANDO DATASET COMPLETO - TODO O HISTORICO")
print("=" * 80)

# Carregar dataset completo
print(f"\nCarregando: {input_file}")
df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])

print(f"Total candles: {len(df_full):,}")
print(f"Range: {df_full['time'].min()} a {df_full['time'].max()}")

# Usar todo o dataset, mas adicionar flag warmup
# Warmup: Primeiro mes (ate 2022-04-24)
# Target: Resto (de 2022-04-24 em diante)

warmup_end = df_full['time'].min() + pd.Timedelta(days=30)
df_full['is_warmup'] = df_full['time'] < warmup_end

print(f"\nWarmup period: {df_full['time'].min()} a {warmup_end}")
print(f"Target period: {warmup_end} a {df_full['time'].max()}")

print(f"\nCandles totais: {len(df_full):,}")
print(f"  Warmup (primeiro mes): {df_full['is_warmup'].sum():,}")
print(f"  Target (resto): {(~df_full['is_warmup']).sum():,}")

# Calcular duracao do target
target_df = df_full[~df_full['is_warmup']]
duracao = target_df['time'].max() - target_df['time'].min()
anos = duracao.days / 365.25
meses = duracao.days / 30.44

print(f"\nDuracao do target period:")
print(f"  {duracao.days} dias")
print(f"  {meses:.1f} meses")
print(f"  {anos:.2f} anos")

# Salvar
df_full.to_parquet(output_dataset, index=False)
print(f"\n[OK] Dataset salvo: {output_dataset}")
print(f"   Tamanho: {output_dataset.stat().st_size / 1024 / 1024:.2f} MB")

print("\n" + "=" * 80)
print("PROXIMOS PASSOS:")
print("=" * 80)
print("1. Executar Python backtest (pode levar alguns minutos)")
print("2. Executar Rust backtest")
print("3. Comparar resultados")
print("=" * 80)

