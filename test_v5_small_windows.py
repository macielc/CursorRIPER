"""
Teste V5 - Janelas PEQUENAS (15 e 30 dias)
==========================================
Testa se janelas menores funcionam melhor.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent / 'core'))

import pandas as pd
import numpy as np
from datetime import timedelta
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from trend_filter_v5 import TrendFilterV5

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
    """FASE 5 simplificada"""
    if len(trades) < 20:
        return {'aprovado': False, 'sharpe_sem_outliers': 0, 'error': 'Poucos trades'}
    
    pnl_values = [t['pnl'] for t in trades]
    pnl_sorted = sorted(pnl_values)
    n_remove = int(len(pnl_sorted) * 0.10)
    pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
    
    sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
    aprovado = sharpe_filtered > 0.7
    
    return {
        'aprovado': aprovado,
        'sharpe_sem_outliers': sharpe_filtered
    }


print("="*80)
print("TESTE V5 - JANELAS PEQUENAS (15d e 30d)")
print("="*80)

loader = DataLoader(timeframe='5m')
df_full = loader.load()

df_full['date'] = pd.to_datetime(df_full['time'])
df_full = df_full.sort_values('date')
end_date = df_full['date'].max()

# Testa em 6 meses e 1 ano (onde V5 60d/90d falharam)
periods = {
    '6_MESES': (end_date - timedelta(days=180), end_date),
    '1_ANO': (end_date - timedelta(days=365), end_date)
}

for period_name, (start_date, period_end) in periods.items():
    print(f"\n{'='*80}")
    print(f"PERIODO: {period_name}")
    print(f"De {start_date.date()} ate {period_end.date()}")
    print("="*80)
    
    df = df_full[(df_full['date'] >= start_date) & (df_full['date'] <= period_end)].copy()
    print(f"Candles: {len(df)}")
    
    # Backtest SEM filtro
    engine = BacktestEngine(df)
    result_no_filter = engine.run_strategy(STRATEGY_NAME, base_params)
    
    print(f"\n[BASELINE] SEM FILTRO:")
    print(f"  Trades: {result_no_filter['total_trades']}, PnL: {result_no_filter['total_return']:.0f}")
    
    fase5_no_filter = test_fase5(result_no_filter['trades'])
    print(f"  FASE 5: {'[OK]' if fase5_no_filter['aprovado'] else '[X]'} (Sharpe: {fase5_no_filter['sharpe_sem_outliers']:.2f})")
    
    # V5 ROLLING - 15 DIAS
    print(f"\n[V5 ROLLING] 15 dias, ADX 10, EMA apenas:")
    filter_v5_15 = TrendFilterV5(window_days=15, adx_threshold=10, use_sma=False)
    
    filtered_v5_15 = []
    blocked_v5_15 = {'BUY': 0, 'SELL': 0}
    
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5_15.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5_15.append(trade)
        else:
            blocked_v5_15[trade_type] += 1
    
    pnl_v5_15 = sum(t['pnl'] for t in filtered_v5_15)
    print(f"  Trades: {len(filtered_v5_15)}/{result_no_filter['total_trades']} " +
          f"(BUY bloq: {blocked_v5_15['BUY']}, SELL bloq: {blocked_v5_15['SELL']})")
    print(f"  PnL: {pnl_v5_15:.0f}")
    
    if len(filtered_v5_15) >= 20:
        fase5_v5_15 = test_fase5(filtered_v5_15)
        print(f"  FASE 5: {'[OK]' if fase5_v5_15['aprovado'] else '[X]'} (Sharpe: {fase5_v5_15['sharpe_sem_outliers']:.2f})")
    else:
        print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v5_15)})")
    
    # V5 ROLLING - 30 DIAS
    print(f"\n[V5 ROLLING] 30 dias, ADX 10, EMA apenas:")
    filter_v5_30 = TrendFilterV5(window_days=30, adx_threshold=10, use_sma=False)
    
    filtered_v5_30 = []
    blocked_v5_30 = {'BUY': 0, 'SELL': 0}
    
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5_30.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5_30.append(trade)
        else:
            blocked_v5_30[trade_type] += 1
    
    pnl_v5_30 = sum(t['pnl'] for t in filtered_v5_30)
    print(f"  Trades: {len(filtered_v5_30)}/{result_no_filter['total_trades']} " +
          f"(BUY bloq: {blocked_v5_30['BUY']}, SELL bloq: {blocked_v5_30['SELL']})")
    print(f"  PnL: {pnl_v5_30:.0f}")
    
    if len(filtered_v5_30) >= 20:
        fase5_v5_30 = test_fase5(filtered_v5_30)
        print(f"  FASE 5: {'[OK]' if fase5_v5_30['aprovado'] else '[X]'} (Sharpe: {fase5_v5_30['sharpe_sem_outliers']:.2f})")
    else:
        print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v5_30)})")

print(f"\n{'='*80}")
print("FIM DO TESTE")
print("="*80)

