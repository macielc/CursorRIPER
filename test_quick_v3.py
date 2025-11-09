"""
Teste RÁPIDO do Filtro V3
==========================
Valida que o filtro V3 realmente permite trades.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent / 'core'))

import pandas as pd
from datetime import timedelta
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from trend_filter_v3 import TrendFilterV3

STRATEGY_NAME = 'barra_elefante'

# Parâmetros base
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
    'tp_atr_mult': 3.0,
    'usar_trailing': False
}

print("="*80)
print("TESTE RAPIDO FILTRO V3")
print("="*80)

# Carrega dados
print("\n[1/4] Carregando dados...")
loader = DataLoader(timeframe='5m')
df_full = loader.load()

df_full['date'] = pd.to_datetime(df_full['time'])
df_full = df_full.sort_values('date')
end_date = df_full['date'].max()

# Pega últimos 3 meses
start_date = end_date - timedelta(days=90)
df = df_full[(df_full['date'] >= start_date) & (df_full['date'] <= end_date)].copy()

print(f"Periodo: {start_date.date()} a {end_date.date()}")
print(f"Candles: {len(df)}")

# Backtest SEM filtro
print("\n[2/4] Backtest SEM filtro...")
engine = BacktestEngine(df)
result_no_filter = engine.run_strategy(STRATEGY_NAME, base_params)

if result_no_filter['success']:
    print(f"  Trades: {result_no_filter['total_trades']}")
    print(f"  PnL: {result_no_filter['total_return']:.0f}")
else:
    print(f"  ERRO: {result_no_filter.get('error')}")

# Teste com diferentes thresholds ADX
for adx_th in [10, 12, 15]:
    print(f"\n[3/4] Backtest COM filtro V3 (ADX {adx_th})...")
    
    trend_filter = TrendFilterV3(adx_threshold=adx_th)
    
    # Analisa GLOBAL (não trade-by-trade)
    print("  Analisando tendencia GLOBAL...")
    analysis = trend_filter.analyze_trend(df)
    
    print(f"  Resultado: {analysis.get('trend_description', 'N/A')}")
    print(f"  Consolidacao: {analysis.get('is_consolidation')}")
    print(f"  Direcoes permitidas: {analysis.get('allowed_directions', [])}")
    
    if not analysis.get('is_consolidation') and analysis.get('allowed_directions'):
        # Filtra trades do backtest original
        filtered_trades = []
        blocked = 0
        
        for trade in result_no_filter['trades']:
            trade_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            
            if trade_type in analysis['allowed_directions']:
                filtered_trades.append(trade)
            else:
                blocked += 1
        
        print(f"  Trades permitidos: {len(filtered_trades)}/{result_no_filter['total_trades']}")
        print(f"  Trades bloqueados: {blocked}")
        
        if len(filtered_trades) > 0:
            pnl = sum(t['pnl'] for t in filtered_trades)
            print(f"  PnL filtrado: {pnl:.0f}")
    else:
        print(f"  Todos os trades bloqueados (consolidacao ou sem direcao)")

print("\n"+"="*80)
print("CONCLUSAO")
print("="*80)
print("Se ADX 10 permitir trades, V3 FUNCIONA!")
print("="*80)

