"""
Criar dataset de 1 semana completa para validação robusta
"""
import pandas as pd
from pathlib import Path

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_Week_Oct2025.parquet")

# Período: 20-24 Outubro 2025 (1 semana)
start_date = "2025-10-20"
end_date = "2025-10-25"  # Exclusivo

print("=" * 80)
print(f"CRIANDO DATASET SEMANAL: {start_date} a {end_date}")
print("=" * 80)

df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])

# Filtrar período (SEMFILTRO horário - deixar Rust/Python filtrar)
df_week = df_full[
    (df_full['time'] >= start_date) &
    (df_full['time'] < end_date)
].copy()

# Reset index
df_week = df_week.reset_index(drop=True)

df_week.to_parquet(output_dataset, index=False)

# Análise por dia
print(f"\nTotal candles: {len(df_week)}")
print(f"Range: {df_week['time'].min()} a {df_week['time'].max()}")

print("\nCandles por dia:")
df_week['date'] = df_week['time'].dt.date
for date, group in df_week.groupby('date'):
    print(f"  {date}: {len(group)} candles")

print("\n" + "=" * 80)
print(f"Dataset salvo: {output_dataset}")
print("=" * 80)

