import pandas as pd

# Carregar resultados
df = pd.read_csv('../results/smoke_test/fase1a_results_20251108_222234.csv')
df_success = df[df['success'] == True].copy()

print("=" * 80)
print("ANALISE POR NUMERO DE TRADES")
print("=" * 80)

# Filtrar setups com pelo menos 50 trades (estatisticamente relevante)
df_50plus = df_success[df_success['total_trades'] >= 50].copy()
df_50plus = df_50plus.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print(f"\nSetups com 50+ trades: {len(df_50plus):,}")

if len(df_50plus) > 0:
    print("\nTOP 10 (com 50+ trades):")
    print(df_50plus.head(10)[['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'total_trades']].to_string())
    
    print("\n" + "=" * 80)
    print("ESTATISTICAS (50+ trades)")
    print("=" * 80)
    print(f"PnL Medio: {df_50plus['total_return'].mean():.2f}")
    print(f"PnL Maximo: {df_50plus['total_return'].max():.2f}")
    print(f"Sharpe Maximo: {df_50plus['sharpe_ratio'].max():.2f}")
    print(f"Sharpe Medio: {df_50plus['sharpe_ratio'].mean():.2f}")
    print(f"Win Rate Medio: {df_50plus['win_rate'].mean()*100:.1f}%")
    print(f"Trades Medio: {df_50plus['total_trades'].mean():.1f}")
    
    positivos = len(df_50plus[df_50plus['total_return'] > 0])
    print(f"\nSetups lucrativos: {positivos:,} ({positivos/len(df_50plus)*100:.1f}%)")

# Filtrar setups com 100+ trades
df_100plus = df_success[df_success['total_trades'] >= 100].copy()
df_100plus = df_100plus.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print("\n" + "=" * 80)
print(f"ANALISE COM 100+ TRADES")
print("=" * 80)
print(f"Setups com 100+ trades: {len(df_100plus):,}")

if len(df_100plus) > 0:
    print("\nTOP 10 (com 100+ trades):")
    print(df_100plus.head(10)[['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'total_trades']].to_string())
    
    print(f"\nPnL Maximo: {df_100plus['total_return'].max():.2f}")
    print(f"Sharpe Maximo: {df_100plus['sharpe_ratio'].max():.2f}")
    
    positivos = len(df_100plus[df_100plus['total_return'] > 0])
    print(f"Setups lucrativos: {positivos:,} ({positivos/len(df_100plus)*100:.1f}%)")

# Distribuição por faixas de trades
print("\n" + "=" * 80)
print("DISTRIBUICAO POR FAIXAS DE TRADES")
print("=" * 80)
bins = [0, 10, 50, 100, 200, 500, 1000, 10000]
labels = ['0-10', '10-50', '50-100', '100-200', '200-500', '500-1000', '1000+']
df_success['trade_bin'] = pd.cut(df_success['total_trades'], bins=bins, labels=labels)

for label in labels:
    bin_data = df_success[df_success['trade_bin'] == label]
    if len(bin_data) > 0:
        positivos = len(bin_data[bin_data['total_return'] > 0])
        print(f"{label:10s}: {len(bin_data):5,} setups | Lucrativos: {positivos/len(bin_data)*100:5.1f}% | PnL Medio: {bin_data['total_return'].mean():10,.2f}")

