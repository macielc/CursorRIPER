"""
Teste Automatizado de TODAS as Combinações
==========================================
Testa 13+ combinações de:
- Filtro V2 (ADX threshold: 15, 20, 25)
- TP variável (3.0, 3.5, 4.0, 5.0)
- Trailing Stop (sim/não)
- Filtro de horário (sim/não)

Autor: MacTester V2.0
Data: 2025-11-08
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
import json
from itertools import product

# Import filtro V3
trend_filter_path = Path(__file__).parent / 'core'
sys.path.insert(0, str(trend_filter_path))
from trend_filter_v3 import TrendFilterV3

STRATEGY_NAME = 'barra_elefante'


def create_config(base_params: dict, tp_mult: float, use_trailing: bool, 
                  trailing_activation: float, filter_hours: str) -> dict:
    """Cria configuração de parâmetros"""
    params = base_params.copy()
    params['tp_atr_mult'] = tp_mult
    params['usar_trailing'] = use_trailing
    
    if use_trailing:
        params['trailing_activation_atr'] = trailing_activation
    
    # Filtro de horário
    if filter_hours == 'inicio':
        params['horario_inicio'] = 9
        params['minuto_inicio'] = 30  # Evita 9h-9h30
    elif filter_hours == 'fim':
        params['horario_fim'] = 14
        params['minuto_fim'] = 30  # Evita 14h30-15h
    elif filter_hours == 'ambos':
        params['horario_inicio'] = 9
        params['minuto_inicio'] = 30
        params['horario_fim'] = 14
        params['minuto_fim'] = 30
    
    return params


def run_backtest_with_filter_v3(df: pd.DataFrame, params: dict, 
                                  adx_threshold: int = 10) -> dict:
    """
    Executa backtest com filtro V3 (ANÁLISE GLOBAL)
    
    Args:
        df: DataFrame com dados
        params: Parâmetros da estratégia
        adx_threshold: Threshold ADX para filtro
        
    Returns:
        Dict com resultados
    """
    trend_filter = TrendFilterV3(adx_threshold=adx_threshold)
    
    # Analisa tendência GLOBAL (uma vez só!)
    analysis = trend_filter.analyze_trend(df)
    
    # Se erro ou consolidação, retorna vazio
    if 'error' in analysis or analysis.get('is_consolidation', True):
        return {
            'success': True,
            'trades': [],
            'total_return': 0,
            'sharpe_ratio': 0,
            'win_rate': 0,
            'max_drawdown': 0,
            'total_trades': 0,
            'filter_blocked': 0,
            'blocked_by_direction': {'BUY': 0, 'SELL': 0},
            'filter_reason': analysis.get('trend_description', 'Consolidação')
        }
    
    allowed_directions = analysis.get('allowed_directions', [])
    
    # Executa backtest
    engine = BacktestEngine(df)
    result = engine.run_strategy(STRATEGY_NAME, params)
    
    if not result['success']:
        return result
    
    # Filtra trades pela tendência GLOBAL
    filtered_trades = []
    total_blocked = 0
    blocked_by_direction = {'BUY': 0, 'SELL': 0}
    
    for trade in result['trades']:
        # Tipo do trade
        bar_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
        
        # Verifica se direção está permitida
        if bar_type in allowed_directions:
            filtered_trades.append(trade)
        else:
            total_blocked += 1
            blocked_by_direction[bar_type] += 1
    
    # Recalcula métricas
    if len(filtered_trades) > 0:
        trades_df = pd.DataFrame(filtered_trades)
        
        total_return = trades_df['pnl'].sum()
        pnl_values = trades_df['pnl'].values
        
        sharpe = (pnl_values.mean() / pnl_values.std()) * np.sqrt(252) if pnl_values.std() > 0 else 0
        win_rate = (trades_df['pnl'] > 0).mean()
        
        equity = trades_df['pnl'].cumsum()
        running_max = equity.cummax()
        drawdown = equity - running_max
        max_dd = drawdown.min()
        
        result['trades'] = filtered_trades
        result['total_return'] = total_return
        result['sharpe_ratio'] = sharpe
        result['win_rate'] = win_rate
        result['max_drawdown'] = max_dd
        result['total_trades'] = len(filtered_trades)
        result['filter_blocked'] = total_blocked
        result['blocked_by_direction'] = blocked_by_direction
    else:
        result['trades'] = []
        result['total_return'] = 0
        result['sharpe_ratio'] = 0
        result['win_rate'] = 0
        result['max_drawdown'] = 0
        result['total_trades'] = 0
        result['filter_blocked'] = total_blocked
        result['blocked_by_direction'] = blocked_by_direction
    
    return result


def test_outlier_analysis(trades: list) -> dict:
    """FASE 5: Análise de Outliers"""
    if len(trades) < 20:
        return {'error': 'Poucos trades', 'aprovado': False}
    
    trades_df = pd.DataFrame(trades)
    pnl_values = trades_df['pnl'].values
    
    # Original
    sharpe_original = (pnl_values.mean() / pnl_values.std()) * np.sqrt(252) if pnl_values.std() > 0 else 0
    
    # Remove top/bottom 10%
    n_remove = int(len(trades) * 0.10)
    trades_sorted = trades_df.sort_values('pnl')
    trades_filtered = trades_sorted.iloc[n_remove:-n_remove] if n_remove > 0 else trades_sorted
    
    pnl_filtered = trades_filtered['pnl'].values
    sharpe_filtered = (pnl_filtered.mean() / pnl_filtered.std()) * np.sqrt(252) if pnl_filtered.std() > 0 else 0
    
    degradacao = ((sharpe_filtered - sharpe_original) / sharpe_original * 100) if sharpe_original != 0 else 0
    aprovado = sharpe_filtered > 0.7
    
    return {
        'aprovado': aprovado,
        'sharpe_original': sharpe_original,
        'sharpe_sem_outliers': sharpe_filtered,
        'degradacao_pct': degradacao,
        'trades_testados': len(trades),
        'trades_apos_filtro': len(trades_filtered)
    }


def test_single_combination(df: pd.DataFrame, combo_name: str, params: dict, 
                            adx_threshold: int) -> dict:
    """Testa uma combinação específica"""
    print(f"\n  Testando: {combo_name}")
    print(f"    ADX: {adx_threshold}, TP: {params['tp_atr_mult']:.1f}, " +
          f"Trailing: {'Sim' if params.get('usar_trailing') else 'Nao'}")
    
    result = run_backtest_with_filter_v3(df, params, adx_threshold)
    
    if not result['success']:
        return {'error': result.get('error'), 'combo_name': combo_name}
    
    # FASE 5
    outlier_result = test_outlier_analysis(result['trades'])
    
    print(f"    Trades: {result['total_trades']} " +
          f"(bloqueados: {result.get('filter_blocked', 0)})")
    print(f"    PnL: {result['total_return']:.0f}, Sharpe: {result['sharpe_ratio']:.2f}")
    print(f"    FASE 5: {'[OK]' if outlier_result.get('aprovado') else '[X]'} " +
          f"(Sharpe s/ outliers: {outlier_result.get('sharpe_sem_outliers', 0):.2f})")
    
    return {
        'combo_name': combo_name,
        'params': params,
        'adx_threshold': adx_threshold,
        'backtest': {
            'trades': result['total_trades'],
            'pnl': result['total_return'],
            'sharpe': result['sharpe_ratio'],
            'win_rate': result['win_rate'],
            'max_dd': result['max_drawdown'],
            'blocked': result.get('filter_blocked', 0),
            'blocked_by_direction': result.get('blocked_by_direction', {})
        },
        'fase5': outlier_result
    }


def run_all_tests():
    """Executa TODOS os testes"""
    print("=" * 80)
    print("TESTE AUTOMATIZADO DE TODAS AS COMBINACOES")
    print("=" * 80)
    
    # Carrega dados
    print("\n[1/3] Carregando dados...")
    loader = DataLoader(timeframe='5m')
    df_full = loader.load()
    
    df_full['date'] = pd.to_datetime(df_full['time'])
    df_full = df_full.sort_values('date')
    end_date = df_full['date'].max()
    
    # Períodos de teste
    periods = {
        '3_MESES': {
            'start': end_date - timedelta(days=90),
            'end': end_date
        },
        '6_MESES': {
            'start': end_date - timedelta(days=180),
            'end': end_date
        },
        '1_ANO': {
            'start': end_date - timedelta(days=365),
            'end': end_date
        }
    }
    
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
        'usar_trailing': False
    }
    
    # Define combinações a testar
    print("\n[2/3] Definindo combinacoes...")
    
    combinations = []
    
    # GRUPO A: Filtro + TP variável
    for tp in [3.0, 3.5, 4.0, 5.0]:
        for adx in [10, 12, 15]:  # ADX V3: mais permissivo
            params = base_params.copy()
            params['tp_atr_mult'] = tp
            combinations.append({
                'name': f"A_TP{tp:.1f}_ADX{adx}",
                'params': params,
                'adx': adx,
                'group': 'A_Filtro+TP'
            })
    
    # GRUPO B: Filtro + TP + Trailing
    for tp, trail_act in [(3.0, 2.0), (4.0, 2.5), (5.0, 3.0)]:
        for adx in [10, 12, 15]:  # ADX V3: mais permissivo
            params = base_params.copy()
            params['tp_atr_mult'] = tp
            params['usar_trailing'] = True
            params['trailing_activation_atr'] = trail_act
            combinations.append({
                'name': f"B_TP{tp:.1f}_Trail{trail_act:.1f}_ADX{adx}",
                'params': params,
                'adx': adx,
                'group': 'B_Filtro+TP+Trailing'
            })
    
    # GRUPO C: Filtro + TP + Trailing + Horário
    for hour_filter in ['inicio', 'fim', 'ambos']:
        for adx in [10, 12]:  # Reduz combos aqui
            params = base_params.copy()
            params['tp_atr_mult'] = 4.0
            params['usar_trailing'] = True
            params['trailing_activation_atr'] = 2.5
            
            if hour_filter == 'inicio':
                params['minuto_inicio'] = 30
            elif hour_filter == 'fim':
                params['minuto_fim'] = 30
            else:  # ambos
                params['minuto_inicio'] = 30
                params['minuto_fim'] = 30
            
            combinations.append({
                'name': f"C_TP4_Trail_Hora{hour_filter}_ADX{adx}",
                'params': params,
                'adx': adx,
                'group': 'C_Filtro+TP+Trailing+Horario'
            })
    
    print(f"Total de combinacoes: {len(combinations)}")
    print(f"Total de testes: {len(combinations) * len(periods)}")
    
    # Executa testes
    print("\n[3/3] Executando testes...")
    all_results = {}
    
    for period_name, period_range in periods.items():
        print(f"\n{'='*80}")
        print(f"PERIODO: {period_name}")
        print(f"De {period_range['start'].date()} ate {period_range['end'].date()}")
        print("=" * 80)
        
        df_period = df_full[
            (df_full['date'] >= period_range['start']) &
            (df_full['date'] <= period_range['end'])
        ].copy()
        
        print(f"Candles: {len(df_period)}")
        
        if len(df_period) < 300:
            print("Dados insuficientes!")
            continue
        
        period_results = []
        
        for combo in combinations:
            try:
                result = test_single_combination(
                    df_period,
                    combo['name'],
                    combo['params'],
                    combo['adx']
                )
                result['group'] = combo['group']
                period_results.append(result)
            except Exception as e:
                print(f"    ERRO: {e}")
                continue
        
        all_results[period_name] = period_results
    
    # Análise de resultados
    print(f"\n{'='*80}")
    print("ANALISE DE RESULTADOS")
    print("=" * 80)
    
    # Encontra os melhores
    best_overall = []
    
    for period_name, results in all_results.items():
        print(f"\n{period_name}:")
        
        # Filtra aprovados na FASE 5
        aprovados = [r for r in results if r.get('fase5', {}).get('aprovado', False)]
        
        print(f"  Aprovados na FASE 5: {len(aprovados)}/{len(results)}")
        
        if aprovados:
            # Ordena por Sharpe sem outliers
            aprovados_sorted = sorted(aprovados, 
                                     key=lambda x: x['fase5']['sharpe_sem_outliers'], 
                                     reverse=True)
            
            print(f"\n  TOP 5 {period_name}:")
            for i, r in enumerate(aprovados_sorted[:5], 1):
                print(f"    {i}. {r['combo_name']}")
                print(f"       Sharpe s/ outliers: {r['fase5']['sharpe_sem_outliers']:.2f}")
                print(f"       Trades: {r['backtest']['trades']}, " +
                      f"PnL: {r['backtest']['pnl']:.0f}")
                
                best_overall.append({
                    'period': period_name,
                    'combo': r['combo_name'],
                    'score': r['fase5']['sharpe_sem_outliers']
                })
    
    # Melhores gerais
    if best_overall:
        print(f"\n{'='*80}")
        print("TOP 10 MELHORES GERAIS (todos os periodos)")
        print("=" * 80)
        
        best_sorted = sorted(best_overall, key=lambda x: x['score'], reverse=True)
        
        for i, r in enumerate(best_sorted[:10], 1):
            print(f"{i:2}. {r['combo']:40} | {r['period']:10} | Sharpe: {r['score']:.2f}")
    
    # Salva resultados
    output_file = Path(f'results/TESTE_TODAS_COMBINACOES_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    # Converte para JSON
    results_json = {}
    for period, results in all_results.items():
        results_json[period] = []
        for r in results:
            if 'error' not in r:
                results_json[period].append({
                    'combo': r['combo_name'],
                    'group': r['group'],
                    'adx_threshold': r['adx_threshold'],
                    'trades': r['backtest']['trades'],
                    'pnl': float(r['backtest']['pnl']),
                    'sharpe': float(r['backtest']['sharpe']),
                    'fase5_aprovado': 'sim' if r['fase5'].get('aprovado', False) else 'nao',  # Fix bool
                    'fase5_sharpe_sem_outliers': float(r['fase5'].get('sharpe_sem_outliers', 0))
                })
    
    with open(output_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    print(f"\nResultados salvos: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()

