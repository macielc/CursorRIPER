"""
Teste de Impacto do Filtro de Tendência
========================================
Compara a estratégia Barra Elefante COM e SEM filtro de tendência
em 3 períodos diferentes para validar a melhoria.

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

# Import do trend_filter do diretório core
trend_filter_path = Path(__file__).parent / 'core'
sys.path.insert(0, str(trend_filter_path))
from trend_filter import TrendFilter

# Parâmetros ORIGINAIS da Barra Elefante
PARAMS_ORIGINAL = {
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

STRATEGY_NAME = 'barra_elefante'


def run_backtest_with_filter(df: pd.DataFrame, use_filter: bool = False) -> dict:
    """
    Executa backtest com ou sem filtro de tendência
    
    Args:
        df: DataFrame com dados
        use_filter: Se True, aplica filtro de tendência
        
    Returns:
        Dict com resultados
    """
    if use_filter:
        print("\n  Aplicando filtro de tendencia...")
        trend_filter = TrendFilter()
        
        # Analisa tendência geral
        analysis = trend_filter.analyze_multi_timeframe(df)
        
        print(f"  Tendencia: {analysis['trend_description']}")
        print(f"  Confianca: {analysis['confidence']:.0f}%" if analysis['can_trade'] else "  Nao pode operar")
        
        # Se não pode operar, retorna vazio
        if not analysis['can_trade']:
            return {
                'success': True,
                'trades': [],
                'total_return': 0,
                'sharpe_ratio': 0,
                'win_rate': 0,
                'max_drawdown': 0,
                'total_trades': 0,
                'filter_blocked': True
            }
    
    # Executa backtest normal
    engine = BacktestEngine(df)
    result = engine.run_strategy(STRATEGY_NAME, PARAMS_ORIGINAL)
    
    if use_filter and result['success']:
        # Filtra trades pela tendência
        trend_filter = TrendFilter()
        
        # Analisa tendência para cada trade
        filtered_trades = []
        total_blocked = 0
        
        for trade in result['trades']:
            # Pega dados até o momento do trade
            trade_time = df.iloc[trade['entry_idx']]['time']
            df_until_trade = df[df['time'] <= trade_time].copy()
            
            if len(df_until_trade) < 300:
                # Dados insuficientes, permite o trade
                filtered_trades.append(trade)
                continue
            
            # Determina tipo do trade
            bar_type = 'BUY' if trade['type'] == 'LONG' else 'SELL'
            
            # Verifica se deve operar
            can_trade, reason, confidence = trend_filter.should_trade(df_until_trade, bar_type)
            
            if can_trade:
                filtered_trades.append(trade)
            else:
                total_blocked += 1
        
        print(f"  Trades bloqueados pelo filtro: {total_blocked}/{len(result['trades'])}")
        
        # Recalcula métricas com trades filtrados
        if len(filtered_trades) > 0:
            trades_df = pd.DataFrame(filtered_trades)
            
            total_return = trades_df['pnl'].sum()
            pnl_values = trades_df['pnl'].values
            
            if pnl_values.std() > 0:
                sharpe = (pnl_values.mean() / pnl_values.std()) * np.sqrt(252)
            else:
                sharpe = 0
            
            win_rate = (trades_df['pnl'] > 0).mean()
            
            # Calcula drawdown
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
        else:
            result['trades'] = []
            result['total_return'] = 0
            result['sharpe_ratio'] = 0
            result['win_rate'] = 0
            result['max_drawdown'] = 0
            result['total_trades'] = 0
            result['filter_blocked'] = total_blocked
    
    return result


def test_outlier_analysis(trades: list, label: str) -> dict:
    """
    Testa análise de outliers (FASE 5)
    
    Args:
        trades: Lista de trades
        label: Label para identificação
        
    Returns:
        Dict com análise
    """
    if len(trades) < 20:
        print(f"\n  {label}: Poucos trades para análise de outliers (< 20)")
        return {'error': 'Poucos trades'}
    
    trades_df = pd.DataFrame(trades)
    pnl_values = trades_df['pnl'].values
    
    # Métricas originais
    sharpe_original = (pnl_values.mean() / pnl_values.std()) * np.sqrt(252) if pnl_values.std() > 0 else 0
    total_pnl = pnl_values.sum()
    win_rate = (pnl_values > 0).mean()
    
    # Remove top/bottom 10%
    n_remove = int(len(trades) * 0.10)
    trades_sorted = trades_df.sort_values('pnl')
    trades_filtered = trades_sorted.iloc[n_remove:-n_remove] if n_remove > 0 else trades_sorted
    
    pnl_filtered = trades_filtered['pnl'].values
    
    # Métricas sem outliers
    sharpe_filtered = (pnl_filtered.mean() / pnl_filtered.std()) * np.sqrt(252) if pnl_filtered.std() > 0 else 0
    total_pnl_filtered = pnl_filtered.sum()
    win_rate_filtered = (pnl_filtered > 0).mean()
    
    degradacao = ((sharpe_filtered - sharpe_original) / sharpe_original * 100) if sharpe_original != 0 else 0
    
    aprovado = sharpe_filtered > 0.7
    
    print(f"\n  {label}:")
    print(f"    Trades: {len(trades)} -> {len(trades_filtered)} (removidos {n_remove*2})")
    print(f"    Sharpe: {sharpe_original:.2f} -> {sharpe_filtered:.2f}")
    print(f"    PnL: {total_pnl:.0f} -> {total_pnl_filtered:.0f}")
    print(f"    WR: {win_rate*100:.1f}% -> {win_rate_filtered*100:.1f}%")
    print(f"    Degradacao: {degradacao:.1f}%")
    print(f"    FASE 5: {'[OK] APROVADO' if aprovado else '[X] REJEITADO'}")
    
    return {
        'aprovado': aprovado,
        'sharpe_original': sharpe_original,
        'sharpe_sem_outliers': sharpe_filtered,
        'degradacao_pct': degradacao,
        'pnl_original': total_pnl,
        'pnl_sem_outliers': total_pnl_filtered
    }


def compare_periods():
    """Compara 3 períodos diferentes"""
    print("=" * 80)
    print("TESTE DE IMPACTO DO FILTRO DE TENDENCIA")
    print("=" * 80)
    print("\nComparando estratégia COM e SEM filtro em 3 períodos:\n")
    
    # Carrega dados
    print("[1/4] Carregando dados...")
    loader = DataLoader(timeframe='5m')
    df_full = loader.load()
    
    df_full['date'] = pd.to_datetime(df_full['time'])
    df_full = df_full.sort_values('date')
    
    end_date = df_full['date'].max()
    
    # Define períodos (periodos mais longos para ter mais trades)
    periods = {
        '1 MES': {
            'start': end_date - timedelta(days=30),
            'end': end_date
        },
        '3 MESES': {
            'start': end_date - timedelta(days=90),
            'end': end_date
        },
        '6 MESES': {
            'start': end_date - timedelta(days=180),
            'end': end_date
        }
    }
    
    results = {}
    
    # Testa cada período
    for period_name, period_range in periods.items():
        print(f"\n{'=' * 80}")
        print(f"PERIODO: {period_name}")
        print(f"De {period_range['start'].date()} ate {period_range['end'].date()}")
        print("=" * 80)
        
        # Filtra dados do período
        df_period = df_full[
            (df_full['date'] >= period_range['start']) &
            (df_full['date'] <= period_range['end'])
        ].copy()
        
        print(f"\nCandles no periodo: {len(df_period)}")
        
        if len(df_period) < 300:
            print("Dados insuficientes para análise")
            continue
        
        # SEM FILTRO
        print(f"\n[2/4] Executando SEM filtro...")
        result_no_filter = run_backtest_with_filter(df_period, use_filter=False)
        
        # COM FILTRO
        print(f"\n[3/4] Executando COM filtro...")
        result_with_filter = run_backtest_with_filter(df_period, use_filter=True)
        
        # COMPARAÇÃO
        print(f"\n[4/4] COMPARACAO - {period_name}")
        print("=" * 80)
        
        print(f"\nSEM FILTRO:")
        print(f"  Trades: {result_no_filter.get('total_trades', len(result_no_filter.get('trades', [])))} ")
        print(f"  PnL: {result_no_filter.get('total_return', 0):.0f} pts")
        print(f"  Sharpe: {result_no_filter.get('sharpe_ratio', 0):.2f}")
        print(f"  Win Rate: {result_no_filter.get('win_rate', 0)*100:.1f}%")
        print(f"  Max DD: {result_no_filter.get('max_drawdown', 0):.0f} pts")
        
        print(f"\nCOM FILTRO:")
        print(f"  Trades: {result_with_filter.get('total_trades', len(result_with_filter.get('trades', [])))}")
        if result_with_filter.get('filter_blocked'):
            print(f"  Bloqueados: {result_with_filter.get('filter_blocked', 0)}")
        print(f"  PnL: {result_with_filter.get('total_return', 0):.0f} pts")
        print(f"  Sharpe: {result_with_filter.get('sharpe_ratio', 0):.2f}")
        print(f"  Win Rate: {result_with_filter.get('win_rate', 0)*100:.1f}%")
        print(f"  Max DD: {result_with_filter.get('max_drawdown', 0):.0f} pts")
        
        # FASE 5: Análise de Outliers
        print(f"\n{'=' * 80}")
        print(f"FASE 5: ANALISE DE OUTLIERS - {period_name}")
        print("=" * 80)
        
        outlier_no_filter = test_outlier_analysis(
            result_no_filter.get('trades', []), 
            "SEM FILTRO"
        )
        
        outlier_with_filter = test_outlier_analysis(
            result_with_filter.get('trades', []), 
            "COM FILTRO"
        )
        
        # Salva resultados
        results[period_name] = {
            'no_filter': {
                'backtest': result_no_filter,
                'outlier_analysis': outlier_no_filter
            },
            'with_filter': {
                'backtest': result_with_filter,
                'outlier_analysis': outlier_with_filter
            }
        }
    
    # RESUMO FINAL
    print(f"\n{'=' * 80}")
    print("RESUMO FINAL - IMPACTO DO FILTRO")
    print("=" * 80)
    
    for period_name, result in results.items():
        print(f"\n{period_name}:")
        
        no_filter_sharpe = result['no_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0)
        with_filter_sharpe = result['with_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0)
        
        no_filter_aprovado = result['no_filter']['outlier_analysis'].get('aprovado', False)
        with_filter_aprovado = result['with_filter']['outlier_analysis'].get('aprovado', False)
        
        print(f"  SEM Filtro: Sharpe s/ outliers = {no_filter_sharpe:.2f} ({'APROVADO' if no_filter_aprovado else 'REJEITADO'})")
        print(f"  COM Filtro: Sharpe s/ outliers = {with_filter_sharpe:.2f} ({'APROVADO' if with_filter_aprovado else 'REJEITADO'})")
        
        if with_filter_sharpe > no_filter_sharpe:
            melhoria = ((with_filter_sharpe - no_filter_sharpe) / abs(no_filter_sharpe) * 100) if no_filter_sharpe != 0 else 999
            print(f"  Melhoria: +{melhoria:.1f}% [OK]")
        else:
            piora = ((with_filter_sharpe - no_filter_sharpe) / abs(no_filter_sharpe) * 100) if no_filter_sharpe != 0 else -999
            print(f"  Piora: {piora:.1f}% [X]")
    
    # Salva resultados
    output_file = Path(f'results/TESTE_FILTRO_TENDENCIA_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    # Converte para JSON (remove objetos não serializáveis)
    results_json = {}
    for period, data in results.items():
        results_json[period] = {
            'no_filter': {
                'sharpe_original': float(data['no_filter']['outlier_analysis'].get('sharpe_original', 0)),
                'sharpe_sem_outliers': float(data['no_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0)),
                'aprovado': 'sim' if data['no_filter']['outlier_analysis'].get('aprovado', False) else 'nao'
            },
            'with_filter': {
                'sharpe_original': float(data['with_filter']['outlier_analysis'].get('sharpe_original', 0)),
                'sharpe_sem_outliers': float(data['with_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0)),
                'aprovado': 'sim' if data['with_filter']['outlier_analysis'].get('aprovado', False) else 'nao'
            }
        }
    
    with open(output_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    
    print(f"\nResultados salvos: {output_file}")
    
    # DECISÃO FINAL
    print(f"\n{'=' * 80}")
    print("DECISAO FINAL")
    print("=" * 80)
    
    melhorias = sum(1 for period, result in results.items() 
                    if result['with_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0) > 
                       result['no_filter']['outlier_analysis'].get('sharpe_sem_outliers', 0))
    
    if melhorias >= 2:
        print("\n[OK] FILTRO MELHORA A ESTRATEGIA!")
        print("Recomendacao: PROSSEGUIR para otimizacao massiva COM filtro")
    else:
        print("\n[X] FILTRO NAO MELHORA SUFICIENTEMENTE")
        print("Recomendacao: AJUSTAR filtro ou testar outras configuracoes")
    
    print("=" * 80)


if __name__ == "__main__":
    compare_periods()

