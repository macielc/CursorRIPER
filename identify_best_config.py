"""
Identificar os parametros da melhor configuracao
Baseado na posicao no grid (ordem deterministica)
"""
import pandas as pd
import itertools

print("=" * 80)
print("IDENTIFICANDO MELHOR CONFIGURACAO")
print("=" * 80)

# Grid de parametros (mesma ordem do YAML)
grid = {
    'min_amplitude_mult': [1.5, 1.75, 2.0, 2.25, 2.5, 3.0],  # 6
    'min_volume_mult': [1.2, 1.5, 2.0, 2.5],  # 4
    'max_sombra_pct': [0.3, 0.35, 0.4, 0.45, 0.5],  # 5
    'lookback_amplitude': [10, 15, 20, 25, 30],  # 5
    'sl_atr_mult': [1.5, 2.0, 2.5, 3.0],  # 4
    'tp_atr_mult': [2.0, 2.5, 3.0, 4.0, 5.0],  # 5
    'usar_trailing': [False],  # 1
    'horario_inicio': [9],
    'minuto_inicio': [0],
    'horario_fim': [14],
    'minuto_fim': [55],
    'horario_fechamento': [15],
    'minuto_fechamento': [0],
}

# Gerar todas as combinações
param_names = list(grid.keys())
param_values = list(grid.values())
all_combinations = list(itertools.product(*param_values))

print(f"\nTotal de combinacoes: {len(all_combinations):,}")

# Carregar resultados
df = pd.read_csv('results/smoke_test_24cores.csv')
print(f"Resultados no CSV: {len(df):,}")

# Encontrar TOP 10
top10_indices = df.nlargest(10, 'total_return').index.tolist()

print(f"\n{'='*80}")
print("TOP 10 CONFIGURACOES")
print(f"{'='*80}")

for rank, idx in enumerate(top10_indices, 1):
    result = df.iloc[idx]
    config = all_combinations[idx]
    
    print(f"\n{rank}. RANK #{idx} | PnL: {result['total_return']:,.2f}")
    print(f"   Trades: {int(result['total_trades'])} | WR: {result['win_rate']*100:.1f}% | PF: {result['profit_factor']:.2f} | Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"   Parametros:")
    
    for i, param_name in enumerate(param_names):
        if param_name not in ['horario_inicio', 'minuto_inicio', 'horario_fim', 'minuto_fim', 'horario_fechamento', 'minuto_fechamento', 'usar_trailing']:
            print(f"     {param_name:25s} = {config[i]}")

# Salvar TOP 10 com parametros
top10_with_params = []

for idx in top10_indices:
    result = df.iloc[idx]
    config = all_combinations[idx]
    
    row = {
        'rank': top10_indices.index(idx) + 1,
        'total_return': result['total_return'],
        'total_trades': result['total_trades'],
        'win_rate': result['win_rate'],
        'profit_factor': result['profit_factor'],
        'sharpe_ratio': result['sharpe_ratio'],
        'max_drawdown_pct': result['max_drawdown_pct'],
    }
    
    for i, param_name in enumerate(param_names):
        row[param_name] = config[i]
    
    top10_with_params.append(row)

top10_df = pd.DataFrame(top10_with_params)
top10_df.to_csv('results/smoke_test_TOP10_with_params.csv', index=False)

print(f"\n{'='*80}")
print("TOP 10 salvo com parametros em: results/smoke_test_TOP10_with_params.csv")
print(f"{'='*80}")

# Análise de sensibilidade
print(f"\n{'='*80}")
print("ANALISE DE SENSIBILIDADE")
print(f"{'='*80}")

# Para cada parâmetro variável, ver média de PnL
sensitive_params = ['min_amplitude_mult', 'min_volume_mult', 'max_sombra_pct', 'lookback_amplitude', 'sl_atr_mult', 'tp_atr_mult']

for param_name in sensitive_params:
    param_idx = param_names.index(param_name)
    values = grid[param_name]
    
    print(f"\n{param_name}:")
    for value in values:
        # Encontrar indices onde este parametro tem este valor
        indices = [i for i, combo in enumerate(all_combinations) if combo[param_idx] == value]
        avg_pnl = df.iloc[indices]['total_return'].mean()
        print(f"  {value:6} → PnL medio: {avg_pnl:10,.2f}")

