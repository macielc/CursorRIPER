"""
Verificar range completo dos dados disponiveis
"""
import pandas as pd

df = pd.read_parquet("data/golden/WINFUT_M5_Golden_Data.parquet")
df['time'] = pd.to_datetime(df['time'])

print("=" * 80)
print("RANGE COMPLETO DOS DADOS")
print("=" * 80)

print(f"\nTotal candles: {len(df):,}")
print(f"Range: {df['time'].min()} a {df['time'].max()}")

# Calcular duracao
duracao = df['time'].max() - df['time'].min()
anos = duracao.days / 365.25
meses = duracao.days / 30.44

print(f"\nDuracao:")
print(f"  {duracao.days} dias")
print(f"  {meses:.1f} meses")
print(f"  {anos:.2f} anos")

# Filtrar 9h-15h para ver quantos candles de trading
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)]

print(f"\nApos filtro 9h-15h:")
print(f"  {len(df_filtered):,} candles")

print("=" * 80)

