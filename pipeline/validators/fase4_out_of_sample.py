"""
FASE 4: OUT-OF-SAMPLE TEST

Testa a estratégia nos últimos 6 meses (dados NUNCA vistos).
Validação final em dados "futuros".
"""
import json
from pathlib import Path
import pandas as pd
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine


def run_out_of_sample(strategy_name: str, params: dict, df_full: pd.DataFrame):
    """
    Executa Out-of-Sample Test
    
    Args:
        strategy_name: Nome da estratégia
        params: Parâmetros do melhor setup
        df_full: DataFrame com dados completos
    
    Returns:
        Dict com resultados
    """
    print("\n" + "="*80)
    print("FASE 4: OUT-OF-SAMPLE TEST")
    print("="*80 + "\n")
    
    df_full['date'] = pd.to_datetime(df_full['time'])
    df_full = df_full.sort_values('date')
    
    end_date = df_full['date'].max()
    oos_start = end_date - pd.DateOffset(months=6)
    
    df_oos = df_full[df_full['date'] >= oos_start].copy()
    
    print(f"Periodo OOS: {oos_start.date()} ate {end_date.date()}")
    print(f"Candles: {len(df_oos):,}\n")
    
    engine_oos = BacktestEngine(df_oos)
    result_oos = engine_oos.run_strategy(strategy_name, params)
    
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
    
    # Critérios
    criterio_trades = trades_oos >= 5
    criterio_sharpe = sharpe_oos > 0.5
    aprovado = criterio_trades and criterio_sharpe
    
    print(f"\nCRITERIO: >= 5 trades E Sharpe > 0.5")
    print(f"RESULTADO: {'APROVADO' if aprovado else 'REJEITADO'}")
    
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
    
    # Executar OOS
    resultado = run_out_of_sample(strategy_name, params, df_full)
    
    # Salvar resultado
    output_file = Path(f'results/fase4_oos_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(resultado, f, indent=2)
    
    print(f"\nResultado salvo: {output_file}")


if __name__ == '__main__':
    main()

