"""
Debug: Analisar por que 5 trades estão faltando no Rust
"""
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

from core.data_loader import DataLoader

print("=" * 80)
print("DEBUG: TRADES FALTANDO NO RUST")
print("=" * 80)

# Carregar dados do mês
loader = DataLoader('5m')
loader.load()
loader.df = loader.df[
    (loader.df['time'] >= '2025-10-01 00:00:00') &
    (loader.df['time'] < '2025-11-01 00:00:00')
].copy()

print(f"\nTotal candles: {len(loader.df)}")

# Trades faltando
missing_trades = [
    {'entry_idx': 510, 'type': 'LONG', 'entry': 145457.00, 'pnl': -283.43},
    {'entry_idx': 868, 'type': 'SHORT', 'entry': 145175.00, 'pnl': -370.00},
    {'entry_idx': 941, 'type': 'LONG', 'entry': 146730.00, 'pnl': -406.43},
    {'entry_idx': 1305, 'type': 'LONG', 'entry': 150305.00, 'pnl': -506.43},
    {'entry_idx': 1373, 'type': 'LONG', 'entry': 149395.00, 'pnl': 942.86},
]

# Parâmetros
params = {
    'min_amplitude_mult': 2.0,
    'min_volume_mult': 1.5,
    'max_sombra_pct': 0.4,
    'lookback_amplitude': 20,
    'horario_inicio': 9,
    'minuto_inicio': 0,
    'horario_fim': 14,
    'minuto_fim': 55,
}

# Volume column
if 'volume' in loader.df.columns:
    vol_col = 'volume'
elif 'real_volume' in loader.df.columns:
    vol_col = 'real_volume'
elif 'tick_volume' in loader.df.columns:
    vol_col = 'tick_volume'
else:
    print("ERRO: Nenhuma coluna de volume!")
    sys.exit(1)

# Calcular métricas
loader.df['amplitude'] = loader.df['high'] - loader.df['low']
loader.df['corpo'] = abs(loader.df['close'] - loader.df['open'])
loader.df['amplitude_media'] = loader.df['amplitude'].rolling(window=params['lookback_amplitude']).mean().shift(1)
loader.df['volume_media'] = loader.df[vol_col].rolling(window=params['lookback_amplitude']).mean().shift(1)

for trade_info in missing_trades:
    entry_idx = trade_info['entry_idx']
    
    print("\n" + "=" * 80)
    print(f"TRADE FALTANDO: Entry idx {entry_idx} ({trade_info['type']})")
    print("=" * 80)
    
    # Com slippage de 1, entrada é na barra entry_idx
    # Sinal foi detectado na barra entry_idx-1
    # Elefante foi detectado na barra entry_idx-2
    
    signal_idx = entry_idx - 1
    elephant_idx = entry_idx - 2
    
    print(f"\nBarra ELEFANTE esperada: {elephant_idx}")
    print(f"Barra SINAL esperada: {signal_idx}")
    print(f"Barra ENTRADA: {entry_idx}")
    
    # Analisar barra elefante
    if elephant_idx >= 0 and elephant_idx < len(loader.df):
        elephant = loader.df.iloc[elephant_idx]
        
        print(f"\nBarra {elephant_idx} (Elefante?):")
        print(f"  Time: {elephant['time']}")
        print(f"  OHLC: O={elephant['open']:.2f} H={elephant['high']:.2f} L={elephant['low']:.2f} C={elephant['close']:.2f}")
        print(f"  Amplitude: {elephant['amplitude']:.2f} (média: {elephant['amplitude_media']:.2f})")
        print(f"  Volume: {elephant[vol_col]:.0f} (média: {elephant['volume_media']:.2f})")
        print(f"  Corpo: {elephant['corpo']:.2f} ({(elephant['corpo']/elephant['amplitude']*100):.1f}%)")
        print(f"  Tipo: {'BULLISH' if elephant['close'] > elephant['open'] else 'BEARISH'}")
        
        # Testes
        print(f"\n  [1] Amplitude >= média × {params['min_amplitude_mult']}?")
        print(f"      {elephant['amplitude']:.2f} >= {elephant['amplitude_media'] * params['min_amplitude_mult']:.2f}: {elephant['amplitude'] >= elephant['amplitude_media'] * params['min_amplitude_mult']}")
        
        print(f"  [2] Volume >= média × {params['min_volume_mult']}?")
        print(f"      {elephant[vol_col]:.0f} >= {elephant['volume_media'] * params['min_volume_mult']:.2f}: {elephant[vol_col] >= elephant['volume_media'] * params['min_volume_mult']}")
        
        print(f"  [3] Corpo >= {(1-params['max_sombra_pct'])*100:.0f}% da amplitude?")
        pct_corpo = elephant['corpo'] / elephant['amplitude'] if elephant['amplitude'] > 0 else 0
        print(f"      {pct_corpo*100:.1f}% >= {(1-params['max_sombra_pct'])*100:.0f}%: {pct_corpo >= (1-params['max_sombra_pct'])}")
        
        hora = elephant['time'].hour
        minuto = elephant['time'].minute
        print(f"  [4] Horário OK ({hora:02d}:{minuto:02d})?")
        horario_ok = (hora > params['horario_inicio'] or (hora == params['horario_inicio'] and minuto >= params['minuto_inicio'])) and \
                     (hora < params['horario_fim'] or (hora == params['horario_fim'] and minuto <= params['minuto_fim']))
        print(f"      {horario_ok}")
    
    # Analisar barra de sinal (rompimento)
    if signal_idx >= 0 and signal_idx < len(loader.df):
        signal = loader.df.iloc[signal_idx]
        
        print(f"\nBarra {signal_idx} (Sinal/Rompimento?):")
        print(f"  Time: {signal['time']}")
        print(f"  OHLC: O={signal['open']:.2f} H={signal['high']:.2f} L={signal['low']:.2f} C={signal['close']:.2f}")
        
        if trade_info['type'] == 'LONG':
            print(f"  High signal ({signal['high']:.2f}) > High elephant ({elephant['high']:.2f})? {signal['high'] > elephant['high']}")
        else:
            print(f"  Low signal ({signal['low']:.2f}) < Low elephant ({elephant['low']:.2f})? {signal['low'] < elephant['low']}")
    
    # Analisar barra de entrada
    if entry_idx >= 0 and entry_idx < len(loader.df):
        entry = loader.df.iloc[entry_idx]
        
        print(f"\nBarra {entry_idx} (Entrada):")
        print(f"  Time: {entry['time']}")
        print(f"  OHLC: O={entry['open']:.2f} H={entry['high']:.2f} L={entry['low']:.2f} C={entry['close']:.2f}")
        print(f"  Entry esperado: {trade_info['entry']:.2f}")
        print(f"  Entry real (OPEN): {entry['open']:.2f}")
        print(f"  Match? {abs(entry['open'] - trade_info['entry']) < 1.0}")

print("\n" + "=" * 80)

