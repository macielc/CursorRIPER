import pandas as pd
import glob

# Pegar arquivo mais recente
files = glob.glob('../results/smoke_test/fase1a_results_*.csv')
latest_file = max(files, key=lambda x: x)

print(f"Analisando: {latest_file}\n")

# Carregar
df = pd.read_csv(latest_file)
df = df[(df['success'] == True) | (df['success'] == 'true')].copy()
df['total_trades'] = pd.to_numeric(df['total_trades'], errors='coerce')
df = df[df['total_trades'] >= 100].copy()

# Converter para numérico
df['sharpe_ratio'] = pd.to_numeric(df['sharpe_ratio'])
df['total_return'] = pd.to_numeric(df['total_return'])

# Ordenar
df = df.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print("=" * 80)
print("TOP 1 SETUP (com 100+ trades)")
print("=" * 80)

row = df.iloc[0]

print("\nPARAMETROS:")
param_cols = ['min_amplitude_mult', 'min_volume_mult', 'max_sombra_pct', 'lookback_amplitude',
              'horario_inicio', 'minuto_inicio', 'horario_fim', 'minuto_fim',
              'horario_fechamento', 'minuto_fechamento', 'sl_atr_mult', 'tp_atr_mult', 'usar_trailing']

for col in param_cols:
    print(f"  {col:25s}: {row[col]}")

print("\nRESULTADOS:")
print(f"  PnL:            {float(row['total_return']):10,.2f}")
print(f"  Sharpe:         {float(row['sharpe_ratio']):10.2f}")
print(f"  Drawdown:       {float(row['max_drawdown_pct']):10.2f}%")
print(f"  Win Rate:       {float(row['win_rate'])*100:10.1f}%")
print(f"  Profit Factor:  {float(row['profit_factor']):10.2f}")
print(f"  Trades:         {int(row['total_trades']):10,}")

