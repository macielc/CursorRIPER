"""
Validação completa Python vs Rust - 1 SEMANA
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine

print("=" * 80)
print("VALIDACAO PYTHON - SEMANA COMPLETA (20-24 OUT 2025)")
print("=" * 80)

# Parâmetros fixos
params = {
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

print("\nCarregando dados...")
loader = DataLoader('5m')
loader.load()

# Filtrar para a semana
loader.df = loader.df[
    (loader.df['time'] >= '2025-10-20 00:00:00') &
    (loader.df['time'] < '2025-10-25 00:00:00')
].copy()

print(f"Candles carregados: {len(loader.df)}")
print(f"Período: {loader.df['time'].min()} a {loader.df['time'].max()}")

print("\nExecutando backtest...")
engine = BacktestEngine(loader.df, verbose=True)
result = engine.run_strategy('barra_elefante', params)

if not result['success']:
    print(f"\nERRO: {result.get('error_msg', 'Desconhecido')}")
    sys.exit(1)

trades = result.get('trades', [])
metrics = result.get('metrics', {})

if len(trades) == 0:
    print("\nNenhum trade gerado!")
    sys.exit(0)

print("\n" + "=" * 80)
print("RESULTADOS PYTHON")
print("=" * 80)

print(f"\nTotal Trades: {len(trades)}")

# Métricas podem ser dict ou objeto
if isinstance(metrics, dict):
    print(f"Win Rate: {metrics.get('win_rate', 0):.2%}")
    print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    print(f"Total PnL: {metrics.get('total_return', 0):.2f} pts")
    print(f"Avg Trade: {metrics.get('avg_trade', 0):.2f} pts")
    print(f"Max DD: {metrics.get('max_drawdown_pct', 0):.2%}")
else:
    print(f"Win Rate: {getattr(metrics, 'win_rate', 0):.2%}")
    print(f"Profit Factor: {getattr(metrics, 'profit_factor', 0):.2f}")
    print(f"Total PnL: {getattr(metrics, 'total_return', 0):.2f} pts")
    print(f"Avg Trade: {getattr(metrics, 'avg_trade', 0):.2f} pts")
    print(f"Max DD: {getattr(metrics, 'max_drawdown_pct', 0):.2%}")

# Salvar trades
output_dir = Path("results/validation")
output_dir.mkdir(parents=True, exist_ok=True)

trades_df = pd.DataFrame(trades)
trades_df.to_csv(output_dir / "python_trades_week.csv", index=False)

print(f"\nTrades salvos: {output_dir / 'python_trades_week.csv'}")

# Resumo por dia
if len(trades_df) > 0:
    print("\n" + "=" * 80)
    print("TRADES POR DIA")
    print("=" * 80)
    
    # Adicionar coluna de data
    entry_times = []
    for idx in trades_df['entry_idx']:
        entry_times.append(loader.df.iloc[int(idx)]['time'])
    
    trades_df['entry_time'] = entry_times
    trades_df['date'] = pd.to_datetime(trades_df['entry_time']).dt.date
    
    for date, group in trades_df.groupby('date'):
        pnl_total = group['pnl'].sum()
        wins = len(group[group['pnl'] > 0])
        losses = len(group[group['pnl'] <= 0])
        print(f"\n{date}:")
        print(f"  Trades: {len(group)} ({wins}W / {losses}L)")
        print(f"  PnL: {pnl_total:.2f} pts")

print("\n" + "=" * 80)
print("PRÓXIMO: Execute o Rust backtest")
print("=" * 80)
print("\nComando:")
print("cd engines\\rust")
print(".\\target\\release\\optimize_dynamic.exe \\")
print("  --config ..\\..\\strategies\\barra_elefante\\config_validation.yaml \\")
print("  --data ..\\..\\data\\golden\\WINFUT_M5_Week_Oct2025.parquet \\")
print("  --output ..\\..\\results\\validation\\rust_trades_week.csv \\")
print("  --tests 1 \\")
print("  --cores 1")
print("\n" + "=" * 80)

