import pandas as pd
import glob

files = glob.glob('../results/smoke_test/fase1a_results_*.csv')
df = pd.read_csv(max(files))
# success pode ser booleano True ou string 'true'
df = df[(df['success'] == True) | (df['success'] == 'true')].copy()
df['total_trades'] = pd.to_numeric(df['total_trades'], errors='coerce')

print("DISTRIBUICAO DE TRADES:")
print(f"Min: {df['total_trades'].min()}")
print(f"Max: {df['total_trades'].max()}")
print(f"Media: {df['total_trades'].mean():.1f}")
print(f"Mediana: {df['total_trades'].median():.0f}")
print(f"\nSetups com 100+ trades: {len(df[df['total_trades'] >= 100])}")
print(f"Setups com 50+ trades: {len(df[df['total_trades'] >= 50])}")
print(f"Setups com 10+ trades: {len(df[df['total_trades'] >= 10])}")
print(f"Setups com 5+ trades: {len(df[df['total_trades'] >= 5])}")

# Mostrar o melhor independente do número de trades
df['sharpe_ratio'] = pd.to_numeric(df['sharpe_ratio'])
df['total_return'] = pd.to_numeric(df['total_return'])
df = df.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print("\n" + "=" * 80)
print("TOP 1 SETUP (sem filtro de trades):")
print("=" * 80)
row = df.iloc[0]
print(f"Trades: {int(row['total_trades'])}")
print(f"PnL: {float(row['total_return']):,.2f}")
print(f"Sharpe: {float(row['sharpe_ratio']):.2f}")

