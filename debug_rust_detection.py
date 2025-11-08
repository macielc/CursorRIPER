"""
Debug Rust - Simular detecção manualmente
"""
import pandas as pd
import numpy as np
from pathlib import Path

df = pd.read_parquet("data/golden/WINFUT_M5_2025-10-15.parquet")

print("=" * 80)
print("DEBUG RUST - SIMULACAO MANUAL")
print("=" * 80)

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

# Calcular amplitude e corpo
df['amplitude'] = df['high'] - df['low']
df['corpo'] = abs(df['close'] - df['open'])

# Calcular médias
df['amplitude_media'] = df['amplitude'].rolling(window=params['lookback_amplitude']).mean()

# Volume pode ser 'volume', 'real_volume' ou 'tick_volume'
if 'volume' in df.columns:
    vol_col = 'volume'
elif 'real_volume' in df.columns:
    vol_col = 'real_volume'
elif 'tick_volume' in df.columns:
    vol_col = 'tick_volume'
else:
    raise ValueError("Nenhuma coluna de volume encontrada!")

df['volume_media'] = df[vol_col].rolling(window=params['lookback_amplitude']).mean()

print(f"\nTotal candles: {len(df)}")
print(f"\nTestando barras 60-70...")

for i in range(60, min(70, len(df))):
    row = df.iloc[i]
    
    # 1) Amplitude mínima
    if row['amplitude'] < row['amplitude_media'] * params['min_amplitude_mult']:
        continue
    
    # 2) Volume mínimo
    if row[vol_col] < row['volume_media'] * params['min_volume_mult']:
        continue
    
    # 3) Corpo grande
    if row['amplitude'] > 0:
        pct_corpo = row['corpo'] / row['amplitude']
        if pct_corpo < (1 - params['max_sombra_pct']):
            continue
    else:
        continue
    
    # 4) Filtro horário
    hora = row['time'].hour
    minuto = row['time'].minute
    if hora < params['horario_inicio'] or (hora == params['horario_inicio'] and minuto < params['minuto_inicio']):
        continue
    if hora > params['horario_fim'] or (hora == params['horario_fim'] and minuto > params['minuto_fim']):
        continue
    
    # 5) Tipo de barra
    is_bullish = row['close'] > row['open']
    is_bearish = row['close'] < row['open']
    
    if not is_bullish and not is_bearish:
        continue
    
    print(f"\n" + "=" * 80)
    print(f"BARRA ELEFANTE DETECTADA: Índice {i}")
    print("=" * 80)
    print(f"  Time: {row['time']}")
    print(f"  OHLC: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")
    print(f"  Amplitude: {row['amplitude']:.2f} (media: {row['amplitude_media']:.2f})")
    print(f"  Volume: {row[vol_col]} (media: {row['volume_media']:.2f})")
    print(f"  Corpo: {row['corpo']:.2f} ({(row['corpo']/row['amplitude']*100):.1f}%)")
    print(f"  Tipo: {'BULLISH' if is_bullish else 'BEARISH'}")
    
    # 6) Verificar rompimento na próxima barra
    if i + 1 < len(df):
        next_row = df.iloc[i + 1]
        
        print(f"\n  Próxima barra (i+1={i+1}):")
        print(f"    Time: {next_row['time']}")
        print(f"    OHLC: O={next_row['open']:.2f} H={next_row['high']:.2f} L={next_row['low']:.2f} C={next_row['close']:.2f}")
        
        if is_bullish:
            maxima_elefante = row['high']
            print(f"\n    Máxima elefante: {maxima_elefante:.2f}")
            print(f"    High próxima: {next_row['high']:.2f}")
            
            if next_row['high'] > maxima_elefante:
                print(f"    ROMPEU! Sinal LONG")
            else:
                print(f"    NÃO rompeu (diff: {maxima_elefante - next_row['high']:.2f} pts)")
        
        elif is_bearish:
            minima_elefante = row['low']
            print(f"\n    Mínima elefante: {minima_elefante:.2f}")
            print(f"    Low próxima: {next_row['low']:.2f}")
            
            if next_row['low'] < minima_elefante:
                print(f"    ROMPEU! Sinal SHORT")
            else:
                print(f"    NÃO rompeu (diff: {next_row['low'] - minima_elefante:.2f} pts)")

print("\n" + "=" * 80)

