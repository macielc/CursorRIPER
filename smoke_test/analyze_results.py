import pandas as pd

# Carregar resultados
df = pd.read_csv('../results/smoke_test/fase1a_results_20251108_222234.csv')

# Filtrar apenas sucesso
df_success = df[df['success'] == True].copy()

# Ordenar por Sharpe e PnL
df_sorted = df_success.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print("=" * 80)
print("TOP 10 SETUPS - FASE 1A")
print("=" * 80)
print(df_sorted.head(10)[['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'total_trades']].to_string())

print("\n" + "=" * 80)
print("ESTATISTICAS GERAIS")
print("=" * 80)
print(f"Total testados: {len(df):,}")
print(f"Com sucesso: {len(df_success):,}")
print(f"PnL Medio: {df_success['total_return'].mean():.2f}")
print(f"PnL Maximo: {df_success['total_return'].max():.2f}")
print(f"PnL Minimo: {df_success['total_return'].min():.2f}")
print(f"Sharpe Maximo: {df_success['sharpe_ratio'].max():.2f}")
print(f"Sharpe Medio: {df_success['sharpe_ratio'].mean():.2f}")
print(f"Win Rate Medio: {df_success['win_rate'].mean()*100:.1f}%")
print(f"Trades Medio: {df_success['total_trades'].mean():.1f}")

# Distribuição de resultados
print("\n" + "=" * 80)
print("DISTRIBUICAO DE RESULTADOS")
print("=" * 80)
positivos = len(df_success[df_success['total_return'] > 0])
negativos = len(df_success[df_success['total_return'] <= 0])
print(f"Setups com PnL positivo: {positivos:,} ({positivos/len(df_success)*100:.1f}%)")
print(f"Setups com PnL negativo: {negativos:,} ({negativos/len(df_success)*100:.1f}%)")

