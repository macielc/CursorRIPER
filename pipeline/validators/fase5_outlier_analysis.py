"""
FASE 5: OUTLIER ANALYSIS

Remove top/bottom 10% dos trades e recalcula métricas.
Verifica se a estratégia depende de poucos trades extremos.
"""
import json
from pathlib import Path
import pandas as pd
import numpy as np
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from core.metrics import MetricsCalculator


def run_outlier_analysis(strategy_name: str, params: dict, df_full: pd.DataFrame):
    """
    Executa Outlier Analysis
    
    Args:
        strategy_name: Nome da estratégia
        params: Parâmetros do melhor setup
        df_full: DataFrame com dados completos
    
    Returns:
        Dict com resultados
    """
    print("\n" + "="*80)
    print("FASE 5: OUTLIER ANALYSIS")
    print("="*80 + "\n")
    
    # Backtest completo
    engine = BacktestEngine(df_full)
    result = engine.run_strategy(strategy_name, params)
    
    if not result['success'] or len(result['trades']) < 20:
        print("ERRO: Poucos trades para análise de outliers (minimo 20)")
        return {'aprovado': False, 'erro': 'Poucos trades'}
    
    # Converter trades para DataFrame
    trades_df = pd.DataFrame(result['trades'])
    
    # Calcular métricas ORIGINAIS manualmente (sem MetricsCalculator que está bugado)
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
    
    # Recalcular métricas SEM outliers (manualmente)
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
    
    # Análise
    degradacao = ((sharpe_filtered - sharpe_original) / sharpe_original * 100) if sharpe_original != 0 else 0
    
    print(f"\nDEGRADACAO: {degradacao:.1f}%")
    
    # Critério
    aprovado = sharpe_filtered > 0.7
    
    print(f"\nCRITERIO: Sharpe sem outliers > 0.7")
    print(f"RESULTADO: {'APROVADO' if aprovado else 'REJEITADO'}")
    
    if not aprovado:
        if sharpe_filtered < 0:
            print(f"  ALERTA CRITICO: Sharpe NEGATIVO sem outliers!")
            print(f"  Estrategia DEPENDE de poucos trades extremos!")
        else:
            print(f"  Sharpe {sharpe_filtered:.2f} abaixo do minimo (0.7)")
    
    return {
        'aprovado': bool(aprovado),
        'sharpe_original': float(sharpe_original),
        'sharpe_sem_outliers': float(sharpe_filtered),
        'degradacao_pct': float(degradacao),
        'trades_removidos': int(n_remove * 2),
        'trades_restantes': int(len(trades_filtered))
    }


def main():
    # Carregar último resultado de otimização
    results_dir = Path('results/optimization')
    top_50_files = sorted(results_dir.glob('top_50_*.json'), key=lambda p: p.stat().st_mtime)
    
    if not top_50_files:
        print("ERRO: Execute primeiro a otimizacao!")
        return
    
    ultimo = top_50_files[-1]
    print(f"Carregando: {ultimo.name}\n")
    
    with open(ultimo, 'r') as f:
        data = json.load(f)
    
    strategy_name = data.get('strategy')
    results = data['top_50'] if 'top_50' in data else data
    
    df = pd.DataFrame(results)
    df_valid = df[df['success'] == True].copy()
    promissores = df_valid[df_valid['total_trades'] >= 10].copy()
    
    if len(promissores) == 0:
        print("ERRO: Nenhum setup com 10+ trades encontrado!")
        return
    
    promissores = promissores.sort_values('sharpe_ratio', ascending=False)
    melhor = promissores.iloc[0]
    
    print(f"ESTRATEGIA: {strategy_name}")
    print(f"MELHOR SETUP: Sharpe {melhor['sharpe_ratio']:.2f}, {melhor['total_trades']:.0f} trades\n")
    
    params = melhor['params']
    
    # Carregar dados
    print("Carregando dados Golden...")
    loader = DataLoader(timeframe='5m')
    df_full = loader.load()
    
    # Executar Outlier Analysis
    resultado = run_outlier_analysis(strategy_name, params, df_full)
    
    # Salvar resultado
    output_file = Path(f'results/fase5_outliers_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(resultado, f, indent=2)
    
    print(f"\nResultado salvo: {output_file}")


if __name__ == '__main__':
    main()

