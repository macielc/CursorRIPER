"""
Comparação V3 vs V4
===================
Compara rapidamente os 2 filtros em diferentes períodos.
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
from trend_filter_v4 import TrendFilterV4

STRATEGY_NAME = 'barra_elefante'

# Parâmetros base (melhor config do teste anterior)
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
    'tp_atr_mult': 5.0,  # Melhor TP do teste
    'usar_trailing': False
}

print("="*80)
print("COMPARACAO V3 vs V4")
print("="*80)

# Carrega dados
print("\n[1/3] Carregando dados...")
loader = DataLoader(timeframe='5m')
df_full = loader.load()

df_full['date'] = pd.to_datetime(df_full['time'])
df_full = df_full.sort_values('date')
end_date = df_full['date'].max()

# Períodos de teste
periods = {
    '3_MESES': (end_date - timedelta(days=90), end_date),
    '6_MESES': (end_date - timedelta(days=180), end_date),
    '1_ANO': (end_date - timedelta(days=365), end_date)
}

results_comparison = {}

for period_name, (start_date, period_end) in periods.items():
    print(f"\n{'='*80}")
    print(f"PERIODO: {period_name}")
    print(f"De {start_date.date()} ate {period_end.date()}")
    print("="*80)
    
    df = df_full[(df_full['date'] >= start_date) & (df_full['date'] <= period_end)].copy()
    print(f"Candles: {len(df)}")
    
    # Backtest SEM filtro (baseline)
    engine = BacktestEngine(df)
    result_no_filter = engine.run_strategy(STRATEGY_NAME, base_params)
    
    print(f"\nSEM FILTRO:")
    print(f"  Trades: {result_no_filter['total_trades']}")
    print(f"  PnL: {result_no_filter['total_return']:.0f}")
    print(f"  Sharpe: {result_no_filter['sharpe_ratio']:.2f}")
    
    # V3 (ADX 10)
    print(f"\nV3 (ADX 10):")
    filter_v3 = TrendFilterV3(adx_threshold=10)
    analysis_v3 = filter_v3.analyze_trend(df)
    
    print(f"  Direcoes: {analysis_v3.get('allowed_directions', [])}")
    
    if not analysis_v3.get('is_consolidation') and analysis_v3.get('allowed_directions'):
        filtered_v3 = []
        for trade in result_no_filter['trades']:
            trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            if trade_type in analysis_v3['allowed_directions']:
                filtered_v3.append(trade)
        
        pnl_v3 = sum(t['pnl'] for t in filtered_v3)
        print(f"  Trades: {len(filtered_v3)}/{result_no_filter['total_trades']}")
        print(f"  PnL: {pnl_v3:.0f}")
        
        # FASE 5 rápida
        if len(filtered_v3) >= 20:
            pnl_values = [t['pnl'] for t in filtered_v3]
            pnl_sorted = sorted(pnl_values)
            n_remove = int(len(pnl_sorted) * 0.10)
            pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
            
            sharpe_original = (np.mean(pnl_values) / np.std(pnl_values)) * np.sqrt(252) if np.std(pnl_values) > 0 else 0
            sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
            
            aprovado = sharpe_filtered > 0.7
            print(f"  FASE 5: {'[OK]' if aprovado else '[X]'} (Sharpe s/ outliers: {sharpe_filtered:.2f})")
        else:
            print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v3)})")
    else:
        print(f"  Todos bloqueados (consolidacao)")
    
    # V4 CONSERVADOR (ambos devem concordar, ADX 10)
    print(f"\nV4 CONSERVADOR (ADX 10, require_both=True):")
    filter_v4_cons = TrendFilterV4(adx_threshold=10, require_both=True)
    analysis_v4_cons = filter_v4_cons.analyze_trend(df)
    
    print(f"  Direcoes: {analysis_v4_cons.get('allowed_directions', [])}")
    print(f"  SMA: {analysis_v4_cons.get('sma_trend', 'N/A')}, EMA: {analysis_v4_cons.get('ema_trend', 'N/A')}")
    
    if not analysis_v4_cons.get('is_consolidation') and analysis_v4_cons.get('allowed_directions'):
        filtered_v4_cons = []
        for trade in result_no_filter['trades']:
            trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            if trade_type in analysis_v4_cons['allowed_directions']:
                filtered_v4_cons.append(trade)
        
        pnl_v4_cons = sum(t['pnl'] for t in filtered_v4_cons)
        print(f"  Trades: {len(filtered_v4_cons)}/{result_no_filter['total_trades']}")
        print(f"  PnL: {pnl_v4_cons:.0f}")
        
        # FASE 5
        if len(filtered_v4_cons) >= 20:
            pnl_values = [t['pnl'] for t in filtered_v4_cons]
            pnl_sorted = sorted(pnl_values)
            n_remove = int(len(pnl_sorted) * 0.10)
            pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
            
            sharpe_original = (np.mean(pnl_values) / np.std(pnl_values)) * np.sqrt(252) if np.std(pnl_values) > 0 else 0
            sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
            
            aprovado = sharpe_filtered > 0.7
            print(f"  FASE 5: {'[OK]' if aprovado else '[X]'} (Sharpe s/ outliers: {sharpe_filtered:.2f})")
        else:
            print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v4_cons)})")
    else:
        print(f"  Todos bloqueados ({analysis_v4_cons.get('trend_description', 'N/A')})")
    
    # V4 PERMISSIVO (um basta, ADX 10)
    print(f"\nV4 PERMISSIVO (ADX 10, require_both=False):")
    filter_v4_perm = TrendFilterV4(adx_threshold=10, require_both=False)
    analysis_v4_perm = filter_v4_perm.analyze_trend(df)
    
    print(f"  Direcoes: {analysis_v4_perm.get('allowed_directions', [])}")
    print(f"  SMA: {analysis_v4_perm.get('sma_trend', 'N/A')}, EMA: {analysis_v4_perm.get('ema_trend', 'N/A')}")
    
    if not analysis_v4_perm.get('is_consolidation') and analysis_v4_perm.get('allowed_directions'):
        filtered_v4_perm = []
        for trade in result_no_filter['trades']:
            trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            if trade_type in analysis_v4_perm['allowed_directions']:
                filtered_v4_perm.append(trade)
        
        pnl_v4_perm = sum(t['pnl'] for t in filtered_v4_perm)
        print(f"  Trades: {len(filtered_v4_perm)}/{result_no_filter['total_trades']}")
        print(f"  PnL: {pnl_v4_perm:.0f}")
        
        # FASE 5
        if len(filtered_v4_perm) >= 20:
            pnl_values = [t['pnl'] for t in filtered_v4_perm]
            pnl_sorted = sorted(pnl_values)
            n_remove = int(len(pnl_sorted) * 0.10)
            pnl_filtered = pnl_sorted[n_remove:-n_remove] if n_remove > 0 else pnl_sorted
            
            sharpe_original = (np.mean(pnl_values) / np.std(pnl_values)) * np.sqrt(252) if np.std(pnl_values) > 0 else 0
            sharpe_filtered = (np.mean(pnl_filtered) / np.std(pnl_filtered)) * np.sqrt(252) if np.std(pnl_filtered) > 0 else 0
            
            aprovado = sharpe_filtered > 0.7
            print(f"  FASE 5: {'[OK]' if aprovado else '[X]'} (Sharpe s/ outliers: {sharpe_filtered:.2f})")
        else:
            print(f"  FASE 5: [X] (Poucos trades: {len(filtered_v4_perm)})")
    else:
        print(f"  Todos bloqueados ({analysis_v4_perm.get('trend_description', 'N/A')})")

print(f"\n{'='*80}")
print("CONCLUSAO:")
print("Veja qual versao tem melhores resultados consistentes!")
print("="*80)

