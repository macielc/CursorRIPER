"""
Walk-Forward Validation
Testar config otimizada vs original em diferentes períodos
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.backtest_engine import BacktestEngine

print("=" * 80)
print("WALK-FORWARD VALIDATION")
print("=" * 80)

# Carregar dataset completo
df = pd.read_parquet("data/golden/WINFUT_M5_FULL_HISTORY_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy()

# Renomear ATR
if 'atr_14' in df_filtered.columns and 'atr' not in df_filtered.columns:
    df_filtered['atr'] = df_filtered['atr_14']

# Pre-computar médias
df_filtered['amplitude'] = df_filtered['high'] - df_filtered['low']
df_filtered['amplitude_ma_20'] = df_filtered['amplitude'].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

if 'volume' in df_filtered.columns:
    vol_col = 'volume'
elif 'real_volume' in df_filtered.columns:
    vol_col = 'real_volume'
else:
    vol_col = 'tick_volume'

df_filtered['volume_ma_20'] = df_filtered[vol_col].rolling(
    window=20, min_periods=1
).mean().shift(1).fillna(0)

print(f"\nDataset: {len(df_filtered):,} candles")
print(f"Range: {df_filtered['time'].min()} a {df_filtered['time'].max()}")

# Configurações a testar
configs = {
    'ORIGINAL': {
        'min_amplitude_mult': 2.0,
        'min_volume_mult': 1.5,
        'max_sombra_pct': 0.4,
        'lookback_amplitude': 20,
        'horario_inicio': 9,
        'minuto_inicio': 0,
        'horario_fim': 14,
        'minuto_fim': 55,
        'horario_fechamento': 15,
        'minuto_fechamento': 0,
        'sl_atr_mult': 2.0,
        'tp_atr_mult': 3.0,
        'usar_trailing': False
    },
    'OTIMIZADO_TOP1': {
        'min_amplitude_mult': 1.5,
        'min_volume_mult': 1.2,
        'max_sombra_pct': 0.4,
        'lookback_amplitude': 15,
        'horario_inicio': 9,
        'minuto_inicio': 0,
        'horario_fim': 14,
        'minuto_fim': 55,
        'horario_fechamento': 15,
        'minuto_fechamento': 0,
        'sl_atr_mult': 2.5,
        'tp_atr_mult': 2.0,
        'usar_trailing': False
    }
}

# Períodos de teste (out-of-sample)
periods = [
    {'name': '2023', 'start': '2023-01-01', 'end': '2024-01-01'},
    {'name': '2024', 'start': '2024-01-01', 'end': '2025-01-01'},
    {'name': '2025', 'start': '2025-01-01', 'end': '2025-11-01'},
]

print(f"\n{'='*80}")
print("TESTANDO EM PERIODOS OUT-OF-SAMPLE")
print(f"{'='*80}")

results = []

for period in periods:
    print(f"\n[PERIODO: {period['name']}]")
    print(f"  {period['start']} a {period['end']}")
    
    # Filtrar período
    df_period = df_filtered[
        (df_filtered['time'] >= period['start']) &
        (df_filtered['time'] < period['end'])
    ].copy()
    
    print(f"  Candles: {len(df_period):,}")
    
    if len(df_period) < 1000:
        print(f"  [SKIP] Periodo muito curto")
        continue
    
    for config_name, params in configs.items():
        print(f"\n  Config: {config_name}")
        
        # Executar backtest
        engine = BacktestEngine(df_period, verbose=False)
        result = engine.run_strategy('barra_elefante', params)
        
        trades = result.get('trades', [])
        metrics = result.get('metrics', {})
        
        if len(trades) > 0:
            pnl = sum([t['pnl'] for t in trades])
            wins = sum([1 for t in trades if t['pnl'] > 0])
            wr = (wins / len(trades)) * 100
            
            print(f"    Trades: {len(trades)}")
            print(f"    PnL: {pnl:,.2f}")
            print(f"    Win Rate: {wr:.1f}%")
            
            results.append({
                'period': period['name'],
                'config': config_name,
                'trades': len(trades),
                'pnl': pnl,
                'win_rate': wr
            })
        else:
            print(f"    [NENHUM TRADE]")

# Resumo
print(f"\n{'='*80}")
print("RESUMO WALK-FORWARD")
print(f"{'='*80}")

results_df = pd.DataFrame(results)

if len(results_df) > 0:
    # Agrupar por config
    for config_name in configs.keys():
        config_results = results_df[results_df['config'] == config_name]
        
        if len(config_results) > 0:
            total_pnl = config_results['pnl'].sum()
            total_trades = config_results['trades'].sum()
            avg_wr = config_results['win_rate'].mean()
            
            print(f"\n{config_name}:")
            print(f"  PnL Total (out-of-sample): {total_pnl:,.2f}")
            print(f"  Trades Total: {total_trades}")
            print(f"  Win Rate Medio: {avg_wr:.1f}%")
            print(f"\n  Por periodo:")
            for _, row in config_results.iterrows():
                print(f"    {row['period']}: {row['pnl']:,.2f} ({row['trades']} trades)")
    
    # Salvar
    results_df.to_csv('results/walk_forward_results.csv', index=False)
    print(f"\n{'='*80}")
    print("Resultados salvos em: results/walk_forward_results.csv")
    print(f"{'='*80}")

print("\n[WALK-FORWARD COMPLETO]")

