"""
Teste COMPLETO do Filtro V5 - Rolling Window
============================================
Compara V3 (análise global) vs V5 (rolling window) em períodos longos.
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
from trend_filter_v3 import TrendFilterV3
from trend_filter_v5 import TrendFilterV5

STRATEGY_NAME = 'barra_elefante'

# Parâmetros base (melhor do teste anterior)
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
    
    sharpe_original = (np.mean(pnl_values) / np.std(pnl_values)) * np.sqrt(252) if np.std(pnl_values) > 0 else 0
    sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
    
    aprovado = sharpe_filtered > 0.7
    
    return {
        'aprovado': aprovado,
        'sharpe_original': sharpe_original,
        'sharpe_sem_outliers': sharpe_filtered
    }


print("="*80)
print("TESTE V5 - ROLLING WINDOW vs V3 - GLOBAL")
print("="*80)

# Carrega dados
print("\n[1/2] Carregando dados...")
loader = DataLoader(timeframe='5m')
df_full = loader.load()

df_full['date'] = pd.to_datetime(df_full['time'])
df_full = df_full.sort_values('date')
end_date = df_full['date'].max()

# Períodos de teste (só os longos onde V3 falhou)
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
    print(f"  Trades: {result_no_filter['total_trades']}")
    print(f"  PnL: {result_no_filter['total_return']:.0f}")
    print(f"  Sharpe: {result_no_filter['sharpe_ratio']:.2f}")
    
    fase5_no_filter = test_fase5(result_no_filter['trades'])
    print(f"  FASE 5: {'[OK]' if fase5_no_filter['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_no_filter['sharpe_sem_outliers']:.2f})")
    
    # V3 (ADX 10, análise GLOBAL)
    print(f"\n[V3 GLOBAL] ADX 10:")
    filter_v3 = TrendFilterV3(adx_threshold=10)
    analysis_v3 = filter_v3.analyze_trend(df)
    
    print(f"  Tendencia detectada: {analysis_v3.get('trend_description', 'N/A')}")
    print(f"  Direcoes permitidas: {analysis_v3.get('allowed_directions', [])}")
    
    if not analysis_v3.get('is_consolidation') and analysis_v3.get('allowed_directions'):
        filtered_v3 = []
        blocked_v3 = {'BUY': 0, 'SELL': 0}
        
        for trade in result_no_filter['trades']:
            trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            if trade_type in analysis_v3['allowed_directions']:
                filtered_v3.append(trade)
            else:
                blocked_v3[trade_type] += 1
        
        pnl_v3 = sum(t['pnl'] for t in filtered_v3)
        print(f"  Trades: {len(filtered_v3)}/{result_no_filter['total_trades']} (BUY bloqueados: {blocked_v3['BUY']}, SELL bloqueados: {blocked_v3['SELL']})")
        print(f"  PnL: {pnl_v3:.0f}")
        
        if len(filtered_v3) >= 20:
            fase5_v3 = test_fase5(filtered_v3)
            print(f"  FASE 5: {'[OK]' if fase5_v3['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_v3['sharpe_sem_outliers']:.2f})")
        else:
            print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v3)})")
    else:
        print(f"  Todos bloqueados (consolidacao)")
    
    # V5 ROLLING (60 dias, ADX 12, EMA apenas)
    print(f"\n[V5 ROLLING] 60 dias, ADX 12, EMA apenas:")
    filter_v5 = TrendFilterV5(window_days=60, adx_threshold=12, use_sma=False)
    
    filtered_v5 = []
    blocked_v5 = {'BUY': 0, 'SELL': 0}
    
    print("  Filtrando trades (rolling window)...")
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5.append(trade)
        else:
            blocked_v5[trade_type] += 1
    
    pnl_v5 = sum(t['pnl'] for t in filtered_v5)
    print(f"  Trades: {len(filtered_v5)}/{result_no_filter['total_trades']} (BUY bloqueados: {blocked_v5['BUY']}, SELL bloqueados: {blocked_v5['SELL']})")
    print(f"  PnL: {pnl_v5:.0f}")
    
    if len(filtered_v5) >= 20:
        fase5_v5 = test_fase5(filtered_v5)
        print(f"  FASE 5: {'[OK]' if fase5_v5['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_v5['sharpe_sem_outliers']:.2f})")
    else:
        print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v5)})")
    
    # V5 ROLLING (90 dias, ADX 10, EMA apenas)
    print(f"\n[V5 ROLLING] 90 dias, ADX 10, EMA apenas:")
    filter_v5_90 = TrendFilterV5(window_days=90, adx_threshold=10, use_sma=False)
    
    filtered_v5_90 = []
    blocked_v5_90 = {'BUY': 0, 'SELL': 0}
    
    print("  Filtrando trades (rolling window)...")
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5_90.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5_90.append(trade)
        else:
            blocked_v5_90[trade_type] += 1
    
    pnl_v5_90 = sum(t['pnl'] for t in filtered_v5_90)
    print(f"  Trades: {len(filtered_v5_90)}/{result_no_filter['total_trades']} (BUY bloqueados: {blocked_v5_90['BUY']}, SELL bloqueados: {blocked_v5_90['SELL']})")
    print(f"  PnL: {pnl_v5_90:.0f}")
    
    if len(filtered_v5_90) >= 20:
        fase5_v5_90 = test_fase5(filtered_v5_90)
        print(f"  FASE 5: {'[OK]' if fase5_v5_90['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_v5_90['sharpe_sem_outliers']:.2f})")
    else:
        print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v5_90)})")
    
    # V5 ROLLING (60 dias, ADX 12, COM SMA) - MAIS CONSERVADOR
    print(f"\n[V5 ROLLING] 60 dias, ADX 12, COM SMA 100/200:")
    filter_v5_sma = TrendFilterV5(window_days=60, adx_threshold=12, use_sma=True)
    
    filtered_v5_sma = []
    blocked_v5_sma = {'BUY': 0, 'SELL': 0}
    
    print("  Filtrando trades (rolling window)...")
    for trade in result_no_filter['trades']:
        trade_idx = trade['entry_idx']
        trade_time = df.iloc[trade_idx]['time']
        trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        can_trade, reason = filter_v5_sma.should_trade(df, trade_time, trade_type)
        
        if can_trade:
            filtered_v5_sma.append(trade)
        else:
            blocked_v5_sma[trade_type] += 1
    
    pnl_v5_sma = sum(t['pnl'] for t in filtered_v5_sma)
    print(f"  Trades: {len(filtered_v5_sma)}/{result_no_filter['total_trades']} (BUY bloqueados: {blocked_v5_sma['BUY']}, SELL bloqueados: {blocked_v5_sma['SELL']})")
    print(f"  PnL: {pnl_v5_sma:.0f}")
    
    if len(filtered_v5_sma) >= 20:
        fase5_v5_sma = test_fase5(filtered_v5_sma)
        print(f"  FASE 5: {'[OK]' if fase5_v5_sma['aprovado'] else '[X]'} (Sharpe s/ outliers: {fase5_v5_sma['sharpe_sem_outliers']:.2f})")
    else:
        print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v5_sma)})")

print(f"\n{'='*80}")
print("CONCLUSAO:")
print("Se V5 ROLLING passar FASE 5 em periodos longos, eh a solucao!")
print("="*80)

