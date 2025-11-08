"""
VALIDACAO COMPLETA - FASE 4, 5 e MONTE CARLO
Executa todas as validações no setup ORIGINAL
"""
import sys
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import numpy as np

# Adicionar paths
sys.path.insert(0, str(Path(__file__).parent / 'core'))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))

from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from core.monte_carlo import MonteCarloSimulation

# ===========================
# PARAMETROS ORIGINAIS
# ===========================
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


def run_fase4_out_of_sample(df_full: pd.DataFrame):
    """FASE 4: Out-of-Sample Test"""
    print("\n" + "="*80)
    print("FASE 4: OUT-OF-SAMPLE TEST (Ultimos 6 meses)")
    print("="*80 + "\n")
    
    df_full['date'] = pd.to_datetime(df_full['time'])
    df_full = df_full.sort_values('date')
    
    end_date = df_full['date'].max()
    oos_start = end_date - pd.DateOffset(months=6)
    
    df_oos = df_full[df_full['date'] >= oos_start].copy()
    
    print(f"Periodo OOS: {oos_start.date()} ate {end_date.date()}")
    print(f"Candles: {len(df_oos):,}\n")
    
    engine_oos = BacktestEngine(df_oos)
    result_oos = engine_oos.run_strategy(STRATEGY_NAME, PARAMS_ORIGINAL)
    
    if not result_oos['success']:
        print(f"ERRO: {result_oos['error']}")
        return {'aprovado': False, 'erro': result_oos['error']}
    
    trades_oos = len(result_oos['trades'])
    sharpe_oos = result_oos['sharpe_ratio']
    wr_oos = result_oos['win_rate']
    return_oos = result_oos['total_return']
    
    print("RESULTADOS OUT-OF-SAMPLE:")
    print(f"  Trades: {trades_oos}")
    print(f"  Sharpe: {sharpe_oos:.2f}")
    print(f"  Win Rate: {wr_oos*100:.1f}%")
    print(f"  Return: {return_oos:.0f} pts")
    
    # Criterios
    criterio_trades = trades_oos >= 5
    criterio_sharpe = sharpe_oos > 0.5
    aprovado = criterio_trades and criterio_sharpe
    
    print(f"\nCRITERIO: >= 5 trades E Sharpe > 0.5")
    print(f"RESULTADO: {'[OK] APROVADO' if aprovado else '[X] REJEITADO'}")
    
    if not criterio_trades:
        print(f"  FALHOU: Apenas {trades_oos} trades (minimo 5)")
    if not criterio_sharpe:
        print(f"  FALHOU: Sharpe {sharpe_oos:.2f} (minimo 0.5)")
    
    return {
        'aprovado': bool(aprovado),
        'trades': int(trades_oos),
        'sharpe': float(sharpe_oos),
        'win_rate': float(wr_oos),
        'return': float(return_oos),
        'periodo_inicio': str(oos_start.date()),
        'periodo_fim': str(end_date.date())
    }


def run_fase5_outlier_analysis(df_full: pd.DataFrame):
    """FASE 5: Outlier Analysis"""
    print("\n" + "="*80)
    print("FASE 5: OUTLIER ANALYSIS")
    print("="*80 + "\n")
    
    # Backtest completo
    engine = BacktestEngine(df_full)
    result = engine.run_strategy(STRATEGY_NAME, PARAMS_ORIGINAL)
    
    if not result['success'] or len(result['trades']) < 20:
        print("ERRO: Poucos trades para analise de outliers (minimo 20)")
        return {'aprovado': False, 'erro': 'Poucos trades'}
    
    # Converter trades para DataFrame
    trades_df = pd.DataFrame(result['trades'])
    
    # Metricas ORIGINAIS
    sharpe_original = result['sharpe_ratio']
    wr_original = result['win_rate']
    return_original = result['total_return']
    
    print(f"METRICAS ORIGINAIS:")
    print(f"  Trades: {len(trades_df)}")
    print(f"  Sharpe: {sharpe_original:.2f}")
    print(f"  Win Rate: {wr_original*100:.1f}%")
    print(f"  Return: {return_original:.0f} pts\n")
    
    # Remover top/bottom 10%
    n_remove = int(len(trades_df) * 0.10)
    
    trades_sorted = trades_df.sort_values('pnl')
    trades_filtered = trades_sorted.iloc[n_remove:-n_remove] if n_remove > 0 else trades_sorted
    
    print(f"REMOVENDO OUTLIERS:")
    print(f"  Top {n_remove} melhores trades")
    print(f"  Bottom {n_remove} piores trades")
    print(f"  Trades restantes: {len(trades_filtered)}\n")
    
    # Recalcular metricas SEM outliers
    pnl_filtered = trades_filtered['pnl'].values
    
    # Sharpe
    if len(pnl_filtered) > 0 and pnl_filtered.std() > 0:
        sharpe_filtered = (pnl_filtered.mean() / pnl_filtered.std()) * np.sqrt(252)
    else:
        sharpe_filtered = 0
    
    # Win Rate
    wins_filtered = np.sum(pnl_filtered > 0)
    wr_filtered = wins_filtered / len(pnl_filtered) if len(pnl_filtered) > 0 else 0
    
    # Return
    return_filtered = pnl_filtered.sum()
    
    print(f"METRICAS SEM OUTLIERS:")
    print(f"  Sharpe: {sharpe_filtered:.2f}")
    print(f"  Win Rate: {wr_filtered*100:.1f}%")
    print(f"  Return: {return_filtered:.0f} pts")
    
    # Analise
    degradacao = ((sharpe_filtered - sharpe_original) / sharpe_original * 100) if sharpe_original != 0 else 0
    
    print(f"\nDEGRADACAO: {degradacao:.1f}%")
    
    # Criterio
    aprovado = sharpe_filtered > 0.7
    
    print(f"\nCRITERIO: Sharpe sem outliers > 0.7")
    print(f"RESULTADO: {'[OK] APROVADO' if aprovado else '[X] REJEITADO'}")
    
    if not aprovado:
        if sharpe_filtered < 0:
            print(f"  [!] ALERTA CRITICO: Sharpe NEGATIVO sem outliers!")
            print(f"  Estrategia DEPENDE de poucos trades extremos!")
        else:
            print(f"  Sharpe {sharpe_filtered:.2f} abaixo do minimo (0.7)")
    
    return {
        'aprovado': bool(aprovado),
        'sharpe_original': float(sharpe_original),
        'sharpe_sem_outliers': float(sharpe_filtered),
        'degradacao_pct': float(degradacao),
        'trades_removidos': int(n_remove * 2),
        'trades_restantes': int(len(trades_filtered)),
        'trades_df': trades_df  # Para Monte Carlo
    }


def run_monte_carlo(trades_df: pd.DataFrame, n_simulacoes: int = 10000):
    """Monte Carlo Simulation"""
    print("\n" + "="*80)
    print(f"MONTE CARLO SIMULATION ({n_simulacoes:,} iteracoes)")
    print("="*80 + "\n")
    
    trades_list = trades_df.to_dict('records')
    
    mc = MonteCarloSimulation(trades_list, n_simulacoes=n_simulacoes)
    stats = mc.simular(multicore=False)  # Single-core para evitar problemas
    
    print(mc.gerar_relatorio())
    
    # Criterio: >80% simulacoes terminam positivas
    aprovado = stats.get('prob_equity_positiva', 0) >= 0.80
    
    print(f"\nCRITERIO: >80% simulacoes com equity positiva")
    print(f"RESULTADO: {'[OK] APROVADO' if aprovado else '[X] REJEITADO'}")
    
    return {
        'aprovado': bool(aprovado),
        'prob_equity_positiva': float(stats.get('prob_equity_positiva', 0)),
        'sharpe_mean': float(stats.get('sharpe_mean', 0)),
        'sharpe_p5': float(stats.get('sharpe_p5', 0)),
        'sharpe_p95': float(stats.get('sharpe_p95', 0)),
        'max_dd_mean': float(stats.get('max_dd_mean', 0)),
        'max_dd_p5': float(stats.get('max_dd_p5', 0)),
        'equity_p5': float(stats.get('equity_p5', 0)),
        'equity_p50': float(stats.get('equity_p50', 0)),
        'equity_p95': float(stats.get('equity_p95', 0)),
    }


def main():
    print("\n" + "="*80)
    print("VALIDACAO COMPLETA - SETUP ORIGINAL")
    print("="*80)
    print(f"\nEstrategia: {STRATEGY_NAME}")
    print("Parametros: ORIGINAIS (mais robustos)\n")
    
    # Carregar dados
    print("[1/4] Carregando Golden Data...")
    loader = DataLoader(timeframe='5m')
    df_full = loader.load()
    print(f"      Dataset: {len(df_full):,} candles")
    print(f"      Periodo: {df_full['time'].min()} ate {df_full['time'].max()}")
    
    resultados = {
        'estrategia': STRATEGY_NAME,
        'params': PARAMS_ORIGINAL,
        'timestamp': datetime.now().isoformat()
    }
    
    # FASE 4
    print("\n[2/4] Executando FASE 4: Out-of-Sample...")
    resultado_fase4 = run_fase4_out_of_sample(df_full.copy())
    resultados['fase4'] = resultado_fase4
    
    # FASE 5
    print("\n[3/4] Executando FASE 5: Outlier Analysis...")
    resultado_fase5 = run_fase5_outlier_analysis(df_full.copy())
    trades_df = resultado_fase5.pop('trades_df')  # Remover do JSON
    resultados['fase5'] = resultado_fase5
    
    # MONTE CARLO
    print("\n[4/4] Executando Monte Carlo...")
    resultado_mc = run_monte_carlo(trades_df, n_simulacoes=10000)
    resultados['monte_carlo'] = resultado_mc
    
    # RESUMO FINAL
    print("\n" + "="*80)
    print("RESUMO FINAL")
    print("="*80 + "\n")
    
    print(f"FASE 4 (Out-of-Sample): {'[OK] APROVADO' if resultado_fase4['aprovado'] else '[X] REJEITADO'}")
    print(f"  - {resultado_fase4['trades']} trades, Sharpe {resultado_fase4['sharpe']:.2f}")
    
    print(f"\nFASE 5 (Outlier Analysis): {'[OK] APROVADO' if resultado_fase5['aprovado'] else '[X] REJEITADO'}")
    print(f"  - Sharpe sem outliers: {resultado_fase5['sharpe_sem_outliers']:.2f}")
    print(f"  - Degradacao: {resultado_fase5['degradacao_pct']:.1f}%")
    
    print(f"\nMONTE CARLO: {'[OK] APROVADO' if resultado_mc['aprovado'] else '[X] REJEITADO'}")
    print(f"  - Prob. equity positiva: {resultado_mc['prob_equity_positiva']*100:.1f}%")
    print(f"  - Sharpe medio: {resultado_mc['sharpe_mean']:.2f}")
    
    # DECISAO FINAL
    total_aprovado = sum([
        resultado_fase4['aprovado'],
        resultado_fase5['aprovado'],
        resultado_mc['aprovado']
    ])
    
    resultados['total_aprovado'] = total_aprovado
    resultados['aprovacao_final'] = total_aprovado >= 2  # 2/3 necessario
    
    print(f"\n{'='*80}")
    print(f"APROVACAO: {total_aprovado}/3 testes")
    
    if resultados['aprovacao_final']:
        print("\n[OK] ESTRATEGIA APROVADA PARA PRODUCAO!")
    else:
        print("\n[X] ESTRATEGIA REJEITADA - Necessita melhorias")
    
    print(f"{'='*80}\n")
    
    # Salvar resultado
    output_file = Path(f'results/VALIDACAO_COMPLETA_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(resultados, f, indent=2)
    
    print(f"Resultado salvo: {output_file}")


if __name__ == '__main__':
    main()

