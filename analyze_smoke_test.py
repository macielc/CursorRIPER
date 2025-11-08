"""
Analisar resultados do Smoke Test
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("ANALISE SMOKE TEST - 24 CORES")
print("=" * 80)

# Carregar resultados
df = pd.read_csv('results/smoke_test_24cores.csv')

print(f"\nTotal configuracoes testadas: {len(df):,}")

# Filtrar apenas resultados válidos (mínimo de trades)
df_valid = df[df['total_trades'] >= 50].copy()
print(f"Configuracoes validas (>=50 trades): {len(df_valid):,}")

if len(df_valid) == 0:
    print("\nNENHUMA configuracao valida encontrada!")
    print("Mostrando todas as configuracoes:")
    df_valid = df.copy()

# Estatísticas gerais
print(f"\n{'='*80}")
print("ESTATISTICAS GERAIS")
print(f"{'='*80}")
print(f"PnL médio: {df_valid['total_pnl'].mean():,.2f}")
print(f"PnL mediano: {df_valid['total_pnl'].median():,.2f}")
print(f"PnL min: {df_valid['total_pnl'].min():,.2f}")
print(f"PnL max: {df_valid['total_pnl'].max():,.2f}")
print(f"Win Rate médio: {df_valid['win_rate'].mean()*100:.1f}%")

# TOP 10 por PnL
print(f"\n{'='*80}")
print("TOP 10 POR PnL TOTAL")
print(f"{'='*80}")

top10_pnl = df_valid.nlargest(10, 'total_pnl')

for rank, (idx, row) in enumerate(top10_pnl.iterrows(), 1):
    print(f"\n{rank}. PnL: {row['total_pnl']:,.2f}")
    print(f"   Trades: {int(row['total_trades'])} | WR: {row['win_rate']*100:.1f}% | PF: {row['profit_factor']:.2f}")
    print(f"   Sharpe: {row.get('sharpe_ratio', 0):.2f} | Max DD: {row.get('max_drawdown', 0):,.2f}")
    print(f"   Params: amp={row['min_amplitude_mult']:.2f} vol={row['min_volume_mult']:.2f} " 
          f"sombra={row['max_sombra_pct']:.2f} lookback={int(row['lookback_amplitude'])} "
          f"sl={row['sl_atr_mult']:.2f} tp={row['tp_atr_mult']:.2f}")

# TOP 10 por Profit Factor
print(f"\n{'='*80}")
print("TOP 10 POR PROFIT FACTOR")
print(f"{'='*80}")

top10_pf = df_valid[df_valid['profit_factor'] > 0].nlargest(10, 'profit_factor')

for rank, (idx, row) in enumerate(top10_pf.iterrows(), 1):
    print(f"\n{rank}. PF: {row['profit_factor']:.2f}")
    print(f"   Trades: {int(row['total_trades'])} | WR: {row['win_rate']*100:.1f}% | PnL: {row['total_pnl']:,.2f}")
    print(f"   Params: amp={row['min_amplitude_mult']:.2f} vol={row['min_volume_mult']:.2f} " 
          f"sombra={row['max_sombra_pct']:.2f} lookback={int(row['lookback_amplitude'])} "
          f"sl={row['sl_atr_mult']:.2f} tp={row['tp_atr_mult']:.2f}")

# Análise de sensibilidade dos parâmetros
print(f"\n{'='*80}")
print("ANALISE DE SENSIBILIDADE (Correlacao com PnL)")
print(f"{'='*80}")

params = ['min_amplitude_mult', 'min_volume_mult', 'max_sombra_pct', 'lookback_amplitude', 'sl_atr_mult', 'tp_atr_mult']
correlations = {}

for param in params:
    if param in df_valid.columns:
        corr = df_valid[param].corr(df_valid['total_pnl'])
        correlations[param] = corr
        print(f"{param:25s}: {corr:+.3f}")

# Salvar TOP 100
top100 = df_valid.nlargest(100, 'total_pnl')
top100.to_csv('results/smoke_test_TOP100.csv', index=False)

print(f"\n{'='*80}")
print(f"TOP 100 salvo em: results/smoke_test_TOP100.csv")
print(f"{'='*80}")

