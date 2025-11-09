import pandas as pd

# Carregar resultados
df = pd.read_csv('../results/smoke_test/fase1a_results_20251108_222234.csv')
df = df[df['success'] == True].copy()
df = df[df['total_trades'] >= 100].copy()
df = df.sort_values(['sharpe_ratio', 'total_return'], ascending=False)

print("=" * 80)
print("TOP 3 SETUPS (com 100+ trades)")
print("=" * 80)

# Colunas de parâmetros (excluir métricas)
metric_cols = ['success', 'total_return', 'total_return_pct', 'sharpe_ratio', 
               'max_drawdown_pct', 'win_rate', 'total_trades', 'profit_factor']
param_cols = [c for c in df.columns if c not in metric_cols]

for i in range(min(3, len(df))):
    row = df.iloc[i]
    print(f"\n{'='*80}")
    print(f"RANK #{i+1}")
    print(f"{'='*80}")
    
    print("\nPARAMETROS:")
    for col in param_cols:
        print(f"  {col:25s}: {row[col]}")
    
    print("\nRESULTADOS:")
    print(f"  PnL:            {row['total_return']:10,.2f}")
    print(f"  Sharpe:         {row['sharpe_ratio']:10.2f}")
    print(f"  Max Drawdown:   {row['max_drawdown_pct']:10.2f}%")
    print(f"  Win Rate:       {row['win_rate']*100:10.1f}%")
    print(f"  Profit Factor:  {row['profit_factor']:10.2f}")
    print(f"  Total Trades:   {int(row['total_trades']):10,}")

