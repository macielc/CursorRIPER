"""
FASE 3: WALK-FORWARD ANALYSIS

Testa robustez temporal da estratégia em janelas móveis.
Detecta overfitting e valida consistência ao longo do tempo.
"""
import json
from pathlib import Path
import pandas as pd
import sys
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial

sys.path.insert(0, str(Path(__file__).parent))
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine


def _process_window(args):
    """Processa uma janela individual (para paralelizacao)"""
    df_test, strategy_name, params, train_end, test_end = args
    
    if len(df_test) < 100:
        return None
    
    engine_wf = BacktestEngine(df_test)
    result_wf = engine_wf.run_strategy(strategy_name, params)
    
    if result_wf['success'] and len(result_wf['trades']) > 0:
        return {
            'start': train_end.date(),
            'end': test_end.date(),
            'trades': len(result_wf['trades']),
            'sharpe': result_wf['sharpe_ratio'],
            'win_rate': result_wf['win_rate'],
            'return': result_wf['total_return']
        }
    return None


def run_walkforward(strategy_name: str, params: dict, df_full: pd.DataFrame):
    """
    Executa Walk-Forward Analysis
    
    Args:
        strategy_name: Nome da estratégia
        params: Parâmetros do melhor setup
        df_full: DataFrame com dados completos
    
    Returns:
        Dict com resultados
    """
    print("\n" + "="*80)
    print("FASE 3: WALK-FORWARD ANALYSIS")
    print("="*80 + "\n")
    
    df_full['date'] = pd.to_datetime(df_full['time'])
    df_full = df_full.sort_values('date')
    
    start_date = df_full['date'].min()
    end_date = df_full['date'].max()
    
    print(f"Periodo: {start_date.date()} ate {end_date.date()}")
    print("Janelas: 12 meses treino / 3 meses teste\n")
    
    train_months = 12
    test_months = 3
    window_months = train_months + test_months
    
    # PREPARAR TODAS AS JANELAS PRIMEIRO (para processamento paralelo)
    windows = []
    current_date = start_date
    while current_date + pd.DateOffset(months=window_months) <= end_date:
        train_end = current_date + pd.DateOffset(months=train_months)
        test_end = train_end + pd.DateOffset(months=test_months)
        
        df_test = df_full[(df_full['date'] >= train_end) & (df_full['date'] < test_end)].copy()
        
        if len(df_test) >= 100:
            windows.append((df_test, strategy_name, params, train_end, test_end))
        
        current_date += pd.DateOffset(months=test_months)
    
    print(f"Preparadas {len(windows)} janelas para teste")
    print("Processando em paralelo (todos os cores)...\n")
    
    # PROCESSAR JANELAS EM PARALELO (90% CPU)
    n_cores = cpu_count()
    with Pool(n_cores) as pool:
        results = pool.map(_process_window, windows)
    
    # Filtrar resultados válidos
    wf_results = [r for r in results if r is not None]
    
    # Exibir resultados
    print(f"Janelas testadas: {len(wf_results)}\n")
    print("RESULTADOS POR JANELA:")
    print("-" * 80)
    
    janelas_positivas = 0
    for r in wf_results:
        status = "OK  " if r['sharpe'] > 0 else "FAIL"
        if r['sharpe'] > 0:
            janelas_positivas += 1
        
        print(f"[{status}] {r['start']} - {r['end']}    "
              f"|  Trades: {r['trades']:3d}  "
              f"|  Sharpe: {r['sharpe']:6.2f}  "
              f"|  WR: {r['win_rate']*100:5.1f}%")
    
    # Métricas agregadas
    sharpe_medio = sum(r['sharpe'] for r in wf_results) / len(wf_results) if wf_results else 0
    wr_medio = sum(r['win_rate'] for r in wf_results) / len(wf_results) if wf_results else 0
    trades_medio = sum(r['trades'] for r in wf_results) / len(wf_results) if wf_results else 0
    pct_positivas = (janelas_positivas / len(wf_results) * 100) if wf_results else 0
    
    print(f"\nMETRICAS WALK-FORWARD:")
    print(f"  Sharpe medio: {sharpe_medio:.2f}")
    print(f"  Win Rate medio: {wr_medio*100:.1f}%")
    print(f"  Janelas positivas: {janelas_positivas}/{len(wf_results)} ({pct_positivas:.0f}%)")
    print(f"  Trades medio: {trades_medio:.1f}")
    
    # Critério
    criterio_sharpe = sharpe_medio > 0.8
    criterio_janelas = pct_positivas >= 60
    aprovado = criterio_sharpe and criterio_janelas
    
    print(f"\nCRITERIO: Sharpe > 0.8 E >= 60% janelas positivas")
    print(f"RESULTADO: {'APROVADO' if aprovado else 'REJEITADO'}")
    
    return {
        'aprovado': aprovado,
        'sharpe_medio': sharpe_medio,
        'janelas_positivas': janelas_positivas,
        'total_janelas': len(wf_results),
        'pct_positivas': pct_positivas,
        'trades_medio': trades_medio,
        'resultados_detalhados': wf_results
    }


def main():
    # Carregar último resultado de otimização
    results_dir = Path('results/optimization')
    top_50_files = sorted(results_dir.glob('top_50_*.json'), key=lambda p: p.stat().st_mtime)
    
    if not top_50_files:
        print("ERRO: Execute primeiro a otimizacao!")
        print("  python mactester.py optimize --strategy <nome> --tests 1000")
        return
    
    ultimo = top_50_files[-1]
    print(f"Carregando: {ultimo.name}\n")
    
    with open(ultimo, 'r') as f:
        data = json.load(f)
    
    strategy_name = data.get('strategy')
    results = data['top_50'] if 'top_50' in data else data
    
    # Filtrar setups válidos
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
    
    # Executar Walk-Forward
    resultado = run_walkforward(strategy_name, params, df_full)
    
    # Salvar resultado
    output_file = Path(f'results/fase3_walkforward_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(resultado, f, indent=2, default=str)
    
    print(f"\nResultado salvo: {output_file}")
    
    if not resultado['aprovado']:
        print("\nESTRATEGIA REJEITADA: Falhou no Walk-Forward")
        print("Nao adianta continuar para proximas fases.")


if __name__ == '__main__':
    main()

