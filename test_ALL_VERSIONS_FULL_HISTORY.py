"""
TESTE MEGA - TODAS AS VERSÕES NO HISTÓRICO COMPLETO
====================================================
Testa TODAS as abordagens no período INTEGRAL (~3.5 anos):
- SEM FILTRO (baseline)
- V3 GLOBAL (ADX 10, 12, 15)
- V5 ROLLING (15d, 30d, 60d, 90d) - ADX 10
- V5 ROLLING com SMA (60d, 90d) - ADX 12
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent / 'core'))

import pandas as pd
import numpy as np
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from trend_filter_v3 import TrendFilterV3
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
    """FASE 5"""
    if len(trades) < 20:
        return {'aprovado': False, 'sharpe_sem_outliers': 0, 'trades': len(trades)}
    
    pnl_values = [t['pnl'] for t in trades]
    pnl_sorted = sorted(pnl_values)
    n_remove = int(len(pnl_sorted) * 0.10)
    pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
    
    sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
    aprovado = sharpe_filtered > 0.7
    
    return {
        'aprovado': aprovado,
        'sharpe_sem_outliers': sharpe_filtered,
        'trades': len(trades)
    }


print("="*80)
print("TESTE MEGA - TODAS VERSOES - HISTORICO COMPLETO (~3.5 ANOS)")
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

# BASELINE - SEM FILTRO
print(f"\n{'='*80}")
print("[1/11] SEM FILTRO (BASELINE)")
print("="*80)

engine = BacktestEngine(df)
result_no_filter = engine.run_strategy(STRATEGY_NAME, base_params)

print(f"Trades: {result_no_filter['total_trades']}")
print(f"PnL: {result_no_filter['total_return']:.0f}")
print(f"Sharpe: {result_no_filter['sharpe_ratio']:.2f}")

fase5_no_filter = test_fase5(result_no_filter['trades'])
print(f"FASE 5: {'[OK]' if fase5_no_filter['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_no_filter['sharpe_sem_outliers']:.2f})")

# V3 GLOBAL - ADX 10
print(f"\n{'='*80}")
print("[2/11] V3 GLOBAL - ADX 10")
print("="*80)

filter_v3_10 = TrendFilterV3(adx_threshold=10)
analysis_v3_10 = filter_v3_10.analyze_trend(df)

print(f"Tendencia detectada: {analysis_v3_10.get('trend_description', 'N/A')}")
print(f"Direcoes: {analysis_v3_10.get('allowed_directions', [])}")

if not analysis_v3_10.get('is_consolidation') and analysis_v3_10.get('allowed_directions'):
    filtered_v3_10 = []
    for trade in result_no_filter['trades']:
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        if trade_type in analysis_v3_10['allowed_directions']:
            filtered_v3_10.append(trade)
    
    pnl_v3_10 = sum(t['pnl'] for t in filtered_v3_10)
    print(f"Trades: {len(filtered_v3_10)}/{result_no_filter['total_trades']}")
    print(f"PnL: {pnl_v3_10:.0f}")
    
    fase5_v3_10 = test_fase5(filtered_v3_10)
    print(f"FASE 5: {'[OK]' if fase5_v3_10['aprovado'] else '[X]'} (Sharpe: {fase5_v3_10['sharpe_sem_outliers']:.2f})")
else:
    print("Todos bloqueados")

# V3 GLOBAL - ADX 12
print(f"\n{'='*80}")
print("[3/11] V3 GLOBAL - ADX 12")
print("="*80)

filter_v3_12 = TrendFilterV3(adx_threshold=12)
analysis_v3_12 = filter_v3_12.analyze_trend(df)

print(f"Tendencia: {analysis_v3_12.get('trend_description', 'N/A')}")
print(f"Direcoes: {analysis_v3_12.get('allowed_directions', [])}")

if not analysis_v3_12.get('is_consolidation') and analysis_v3_12.get('allowed_directions'):
    filtered_v3_12 = []
    for trade in result_no_filter['trades']:
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        if trade_type in analysis_v3_12['allowed_directions']:
            filtered_v3_12.append(trade)
    
    pnl_v3_12 = sum(t['pnl'] for t in filtered_v3_12)
    print(f"Trades: {len(filtered_v3_12)}/{result_no_filter['total_trades']}")
    print(f"PnL: {pnl_v3_12:.0f}")
    
    fase5_v3_12 = test_fase5(filtered_v3_12)
    print(f"FASE 5: {'[OK]' if fase5_v3_12['aprovado'] else '[X]'} (Sharpe: {fase5_v3_12['sharpe_sem_outliers']:.2f})")
else:
    print("Todos bloqueados")

# V3 GLOBAL - ADX 15
print(f"\n{'='*80}")
print("[4/11] V3 GLOBAL - ADX 15")
print("="*80)

filter_v3_15 = TrendFilterV3(adx_threshold=15)
analysis_v3_15 = filter_v3_15.analyze_trend(df)

print(f"Tendencia: {analysis_v3_15.get('trend_description', 'N/A')}")
print(f"Direcoes: {analysis_v3_15.get('allowed_directions', [])}")

if not analysis_v3_15.get('is_consolidation') and analysis_v3_15.get('allowed_directions'):
    filtered_v3_15 = []
    for trade in result_no_filter['trades']:
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        if trade_type in analysis_v3_15['allowed_directions']:
            filtered_v3_15.append(trade)
    
    pnl_v3_15 = sum(t['pnl'] for t in filtered_v3_15)
    print(f"Trades: {len(filtered_v3_15)}/{result_no_filter['total_trades']}")
    print(f"PnL: {pnl_v3_15:.0f}")
    
    fase5_v3_15 = test_fase5(filtered_v3_15)
    print(f"FASE 5: {'[OK]' if fase5_v3_15['aprovado'] else '[X]'} (Sharpe: {fase5_v3_15['sharpe_sem_outliers']:.2f})")
else:
    print("Todos bloqueados")

# V5 ROLLING - Varias janelas
rolling_configs = [
    (15, 10, False, "15 dias, ADX 10, EMA"),
    (30, 10, False, "30 dias, ADX 10, EMA"),
    (60, 10, False, "60 dias, ADX 10, EMA"),
    (90, 10, False, "90 dias, ADX 10, EMA"),
    (60, 12, True, "60 dias, ADX 12, SMA"),
    (90, 12, True, "90 dias, ADX 12, SMA"),
    (120, 10, False, "120 dias (4 meses), ADX 10, EMA")
]

for idx, (window_days, adx_th, use_sma, desc) in enumerate(rolling_configs, start=5):
    print(f"\n{'='*80}")
    print(f"[{idx}/11] V5 ROLLING - {desc}")
    print("="*80)
    
    filter_v5 = TrendFilterV5(window_days=window_days, adx_threshold=adx_th, use_sma=use_sma)
    
    filtered_v5 = []
    
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5.append(trade)
    
    pnl_v5 = sum(t['pnl'] for t in filtered_v5)
    print(f"Trades: {len(filtered_v5)}/{result_no_filter['total_trades']}")
    print(f"PnL: {pnl_v5:.0f}")
    
    fase5_v5 = test_fase5(filtered_v5)
    print(f"FASE 5: {'[OK]' if fase5_v5['aprovado'] else '[X]'} (Sharpe: {fase5_v5['sharpe_sem_outliers']:.2f})")

print(f"\n{'='*80}")
print("RESUMO FINAL")
print("="*80)
print("Veja qual versao tem melhores metricas no periodo COMPLETO!")
print("="*80)

