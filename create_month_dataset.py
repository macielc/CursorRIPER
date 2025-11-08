"""
Criar dataset de 1 mês completo para validação robusta
"""
import pandas as pd
from pathlib import Path

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_Month_Oct2025.parquet")

# Período: Outubro 2025 completo (1-31)
start_date = "2025-10-01"
end_date = "2025-11-01"  # Exclusivo

print("=" * 80)
print(f"CRIANDO DATASET MENSAL: {start_date} a {end_date}")
print("=" * 80)

df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])

df_month = df_full[
    (df_full['time'] >= start_date) &
    (df_full['time'] < end_date)
].copy()

# Reset index
df_month = df_month.reset_index(drop=True)

df_month.to_parquet(output_dataset, index=False)

# Análise por dia
print(f"\nTotal candles: {len(df_month)}")
print(f"Range: {df_month['time'].min()} a {df_month['time'].max()}")

print("\nCandles por dia:")
df_month['date'] = df_month['time'].dt.date
daily_counts = df_month.groupby('date').size()
print(f"  Total dias: {len(daily_counts)}")
print(f"  Média candles/dia: {daily_counts.mean():.0f}")
print(f"  Min: {daily_counts.min()} | Max: {daily_counts.max()}")

print("\nPrimeiros 5 dias:")
for i, (date, count) in enumerate(daily_counts.head().items()):
    print(f"  {date}: {count} candles")

print("\nÚltimos 5 dias:")
for i, (date, count) in enumerate(daily_counts.tail().items()):
    print(f"  {date}: {count} candles")

print("\n" + "=" * 80)
print(f"Dataset salvo: {output_dataset}")
print("=" * 80)

