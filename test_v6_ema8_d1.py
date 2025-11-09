"""
Teste V6 - EMA 8 no D1
======================
Testa EMA 8 no timeframe DIÁRIO:
- Modo GLOBAL (análise única)
- Modo ROLLING (janelas de 30, 60, 90 dias)

Compara com baseline (sem filtro) no histórico completo.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent / 'core'))

import pandas as pd
import numpy as np
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from trend_filter_v6 import TrendFilterV6

STRATEGY_NAME = 'barra_elefante'

base_params = {
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
    'tp_atr_mult': 5.0,
    'usar_trailing': False
}


def test_fase5(trades: list) -> dict:
    """FASE 5"""
    if len(trades) < 20:
        return {'aprovado': False, 'sharpe_sem_outliers': 0}
    
    pnl_values = [t['pnl'] for t in trades]
    pnl_sorted = sorted(pnl_values)
    n_remove = int(len(pnl_sorted) * 0.10)
    pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
    
    sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
    aprovado = sharpe_filtered > 0.7
    
    return {'aprovado': aprovado, 'sharpe_sem_outliers': sharpe_filtered}


print("="*80)
print("TESTE V6 - EMA 8 NO D1")
print("="*80)

loader = DataLoader(timeframe='5m')
df = loader.load()

df['date'] = pd.to_datetime(df['time'])
df = df.sort_values('date')

start_date = df['date'].min()
end_date = df['date'].max()
days_total = (end_date - start_date).days

print(f"\nPERIODO COMPLETO:")
print(f"  De: {start_date.date()}")
print(f"  Ate: {end_date.date()}")
print(f"  Total: {days_total} dias (~{days_total/365:.1f} anos)")
print(f"  Candles: {len(df)}")

# BASELINE
print(f"\n{'='*80}")
print("[1/5] SEM FILTRO (BASELINE)")
print("="*80)

engine = BacktestEngine(df)
result_no_filter = engine.run_strategy(STRATEGY_NAME, base_params)

print(f"Trades: {result_no_filter['total_trades']}")
print(f"PnL: {result_no_filter['total_return']:.0f}")
print(f"Sharpe: {result_no_filter['sharpe_ratio']:.2f}")

fase5_no_filter = test_fase5(result_no_filter['trades'])
print(f"FASE 5: {'[OK]' if fase5_no_filter['aprovado'] else '[X]'} (Sharpe: {fase5_no_filter['sharpe_sem_outliers']:.2f})")

# V6 GLOBAL - EMA 8
print(f"\n{'='*80}")
print("[2/5] V6 GLOBAL - EMA 8 no D1")
print("="*80)

filter_v6_global = TrendFilterV6(ema_period=8, rolling_window_days=None)
analysis_v6 = filter_v6_global.analyze_trend(df)

print(f"Tendencia detectada: {analysis_v6.get('trend_description', 'N/A')}")
print(f"Direcoes: {analysis_v6.get('allowed_directions', [])}")
print(f"Close: {analysis_v6.get('close', 0):.2f}, EMA8: {analysis_v6.get('ema', 0):.2f}")

if not analysis_v6.get('is_consolidation') and analysis_v6.get('allowed_directions'):
    filtered_v6_global = []
    blocked_v6 = {'BUY': 0, 'SELL': 0}
    
    for trade in result_no_filter['trades']:
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        if trade_type in analysis_v6['allowed_directions']:
            filtered_v6_global.append(trade)
        else:
            blocked_v6[trade_type] += 1
    
    pnl_v6_global = sum(t['pnl'] for t in filtered_v6_global)
    print(f"Trades: {len(filtered_v6_global)}/{result_no_filter['total_trades']} " +
          f"(BUY bloq: {blocked_v6['BUY']}, SELL bloq: {blocked_v6['SELL']})")
    print(f"PnL: {pnl_v6_global:.0f}")
    
    fase5_v6_global = test_fase5(filtered_v6_global)
    print(f"FASE 5: {'[OK]' if fase5_v6_global['aprovado'] else '[X]'} (Sharpe: {fase5_v6_global['sharpe_sem_outliers']:.2f})")
else:
    print("Todos bloqueados ou neutro")

# V6 ROLLING - Várias janelas
rolling_configs = [
    (30, "30 dias"),
    (60, "60 dias"),
    (90, "90 dias")
]

for idx, (window_days, desc) in enumerate(rolling_configs, start=3):
    print(f"\n{'='*80}")
    print(f"[{idx}/5] V6 ROLLING - EMA 8 D1, janela {desc}")
    print("="*80)
    
    filter_v6_rolling = TrendFilterV6(ema_period=8, rolling_window_days=window_days)
    
    filtered_v6_rolling = []
    blocked_v6_rolling = {'BUY': 0, 'SELL': 0}
    
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v6_rolling.should_trade(df, trade_time=trade_time, bar_type=trade_type)
        
        if can_trade:
            filtered_v6_rolling.append(trade)
        else:
            blocked_v6_rolling[trade_type] += 1
    
    pnl_v6_rolling = sum(t['pnl'] for t in filtered_v6_rolling)
    print(f"Trades: {len(filtered_v6_rolling)}/{result_no_filter['total_trades']} " +
          f"(BUY bloq: {blocked_v6_rolling['BUY']}, SELL bloq: {blocked_v6_rolling['SELL']})")
    print(f"PnL: {pnl_v6_rolling:.0f}")
    
    if len(filtered_v6_rolling) >= 20:
        fase5_v6_rolling = test_fase5(filtered_v6_rolling)
        print(f"FASE 5: {'[OK]' if fase5_v6_rolling['aprovado'] else '[X]'} (Sharpe: {fase5_v6_rolling['sharpe_sem_outliers']:.2f})")
    else:
        print(f"FASE 5: [X] (Poucos trades: {len(filtered_v6_rolling)})")

print(f"\n{'='*80}")
print("RESUMO FINAL")
print("="*80)
print("EMA 8 no D1 - Resultados acima!")
print("="*80)

