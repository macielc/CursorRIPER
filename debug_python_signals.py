"""
Debug Python - Analisar sinais e ATR barra-a-barra
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from strategies import get_strategy

print("=" * 80)
print("DEBUG PYTHON - SINAIS BARRA-A-BARRA")
print("=" * 80)

# Parâmetros de validação
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

# Carregar dados
print("\nCarregando dados...")
loader = DataLoader('5m')
loader.load()
loader.df = loader.df[
    (loader.df['time'] >= '2025-10-15 00:00:00') & 
    (loader.df['time'] < '2025-10-16 00:00:00')
]

print(f"Candles: {len(loader.df)}")

# Instanciar estratégia
StrategyClass = get_strategy('barra_elefante')
strategy = StrategyClass(params=params)

# Gerar sinais
signals = strategy.generate_signals(loader.df)

print("\n" + "=" * 80)
print("ANÁLISE ATR - BARRAS 60-70")
print("=" * 80)

for i in range(60, min(70, len(loader.df))):
    row = loader.df.iloc[i]
    atr_val = row.get('atr', row.get('atr_14', 'N/A'))
    
    print(f"\nBarra {i}:")
    print(f"  Time: {row['time']}")
    print(f"  OHLC: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    print(f"  ATR: {atr_val:.2f}" if atr_val != 'N/A' else f"  ATR: N/A")
    print(f"  Volume: {row.get('real_volume', row.get('volume', 'N/A'))}")
    
    # Verificar se é sinal de entrada
    if i < len(signals['entries_long']):
        if signals['entries_long'][i]:
            print(f"  >>> SINAL LONG <<<")
        if signals['entries_short'][i]:
            print(f"  >>> SINAL SHORT <<<")

print("\n" + "=" * 80)
print("SINAIS DETECTADOS")
print("=" * 80)

long_signals = [i for i, val in enumerate(signals['entries_long']) if val]
short_signals = [i for i, val in enumerate(signals['entries_short']) if val]

print(f"\nLONG signals nos indices: {long_signals}")
print(f"SHORT signals nos indices: {short_signals}")

print("\n" + "=" * 80)
print("DETALHES DO TRADE PYTHON")
print("=" * 80)

# Executar backtest para ver o trade
engine = BacktestEngine(loader.df, verbose=True)
result = engine.run_strategy('barra_elefante', params)

if result['success'] and len(result['trades']) > 0:
    trade = result['trades'][0]
    
    entry_idx = trade['entry_idx']
    exit_idx = trade['exit_idx']
    
    print(f"\nTrade #1:")
    print(f"  Entry Idx: {entry_idx}")
    print(f"  Exit Idx: {exit_idx}")
    
    # Dados da barra de entrada
    entry_candle = loader.df.iloc[entry_idx]
    print(f"\n  Barra de ENTRADA ({entry_idx}):")
    print(f"    Time: {entry_candle['time']}")
    print(f"    OHLC: O={entry_candle['open']:.2f} H={entry_candle['high']:.2f} L={entry_candle['low']:.2f} C={entry_candle['close']:.2f}")
    print(f"    ATR: {entry_candle.get('atr', entry_candle.get('atr_14', 'N/A')):.2f}")
    
    # Barra ANTERIOR (onde detecta elefante?)
    if entry_idx > 0:
        signal_candle = loader.df.iloc[entry_idx - 1]
        print(f"\n  Barra de SINAL ({entry_idx - 1}):")
        print(f"    Time: {signal_candle['time']}")
        print(f"    OHLC: O={signal_candle['open']:.2f} H={signal_candle['high']:.2f} L={signal_candle['low']:.2f} C={signal_candle['close']:.2f}")
        print(f"    ATR: {signal_candle.get('atr', signal_candle.get('atr_14', 'N/A')):.2f}")
    
    # Dados da barra de saída
    exit_candle = loader.df.iloc[exit_idx]
    print(f"\n  Barra de SAÍDA ({exit_idx}):")
    print(f"    Time: {exit_candle['time']}")
    print(f"    OHLC: O={exit_candle['open']:.2f} H={exit_candle['high']:.2f} L={exit_candle['low']:.2f} C={exit_candle['close']:.2f}")
    
    print(f"\n  Trade Details:")
    print(f"    Type: {trade['type']}")
    print(f"    Entry: {trade['entry']:.2f}")
    print(f"    Exit: {trade['exit']:.2f}")
    print(f"    SL: {trade['sl']:.2f}")
    print(f"    TP: {trade['tp']:.2f}")
    print(f"    PnL: {trade['pnl']:.2f} pts")
    print(f"    Exit Reason: {trade['exit_reason']}")
    
    # Verificar cálculo de SL
    if trade['type'] == 'SHORT':
        atr_entry = entry_candle.get('atr', entry_candle.get('atr_14'))
        expected_sl = trade['entry'] + (atr_entry * params['sl_atr_mult'])
        print(f"\n  Verificação SL (SHORT):")
        print(f"    Entry: {trade['entry']:.2f}")
        print(f"    ATR: {atr_entry:.2f}")
        print(f"    sl_atr_mult: {params['sl_atr_mult']}")
        print(f"    SL Esperado: {trade['entry']:.2f} + ({atr_entry:.2f} * {params['sl_atr_mult']}) = {expected_sl:.2f}")
        print(f"    SL Real: {trade['sl']:.2f}")
        print(f"    Diferença: {abs(expected_sl - trade['sl']):.2f} pts")

else:
    print("\n❌ Nenhum trade gerado!")

print("\n" + "=" * 80)

