"""
Simular exatamente o que Rust faz na barra 156
"""
import pandas as pd
from pathlib import Path

df = pd.read_parquet("data/golden/WINFUT_M5_Week_Oct2025.parquet")

print("=" * 80)
print("SIMULACAO RUST - BARRA 156")
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

# Volume pode ser diferente no Parquet
if 'volume' in df.columns:
    vol_col = 'volume'
elif 'real_volume' in df.columns:
    vol_col = 'real_volume'
elif 'tick_volume' in df.columns:
    vol_col = 'tick_volume'
else:
    print("ERRO: Nenhuma coluna de volume!")
    exit(1)

print(f"\nUsando coluna de volume: {vol_col}")

# Calcular métricas
df['amplitude'] = df['high'] - df['low']
df['corpo'] = abs(df['close'] - df['open'])
df['amplitude_media'] = df['amplitude'].rolling(window=params['lookback_amplitude']).mean()
df['volume_media'] = df[vol_col].rolling(window=params['lookback_amplitude']).mean()

i = 156

print(f"\n=== PROCESSANDO BARRA {i} ===")
row = df.iloc[i]

print(f"\nBarra {i}:")
print(f"  Time: {row['time']}")
print(f"  OHLC: O={row['open']:.2f} H={row['high']:.2f} L={row['low']:.2f} C={row['close']:.2f}")

# 1) Amplitude mínima
print(f"\n[1] Amplitude minima:")
print(f"  Amplitude: {row['amplitude']:.2f}")
print(f"  Media: {row['amplitude_media']:.2f}")
print(f"  Min necessario: {row['amplitude_media'] * params['min_amplitude_mult']:.2f}")
if row['amplitude'] < row['amplitude_media'] * params['min_amplitude_mult']:
    print(f"  FALHOU! Amplitude insuficiente")
    exit()
else:
    print(f"  OK!")

# 2) Volume mínimo
print(f"\n[2] Volume minimo:")
print(f"  Volume: {row[vol_col]}")
print(f"  Media: {row['volume_media']:.2f}")
print(f"  Min necessario: {row['volume_media'] * params['min_volume_mult']:.2f}")
if row[vol_col] < row['volume_media'] * params['min_volume_mult']:
    print(f"  FALHOU! Volume insuficiente")
    exit()
else:
    print(f"  OK!")

# 3) Corpo grande
print(f"\n[3] Corpo grande:")
print(f"  Corpo: {row['corpo']:.2f}")
print(f"  Amplitude: {row['amplitude']:.2f}")
pct_corpo = row['corpo'] / row['amplitude']
print(f"  % Corpo: {pct_corpo:.2%}")
print(f"  Min necessario: {(1 - params['max_sombra_pct']):.2%}")
if pct_corpo < (1 - params['max_sombra_pct']):
    print(f"  FALHOU! Corpo muito pequeno")
    exit()
else:
    print(f"  OK!")

# 4) Horário
print(f"\n[4] Horario:")
hora = row['time'].hour
minuto = row['time'].minute
print(f"  Hora: {hora:02d}:{minuto:02d}")
print(f"  Range: {params['horario_inicio']:02d}:{params['minuto_inicio']:02d} a {params['horario_fim']:02d}:{params['minuto_fim']:02d}")

if hora < params['horario_inicio'] or (hora == params['horario_inicio'] and minuto < params['minuto_inicio']):
    print(f"  FALHOU! Antes do horario")
    exit()
if hora > params['horario_fim'] or (hora == params['horario_fim'] and minuto > params['minuto_fim']):
    print(f"  FALHOU! Depois do horario")
    exit()
print(f"  OK!")

# 5) Tipo de barra
print(f"\n[5] Tipo de barra:")
is_bullish = row['close'] > row['open']
is_bearish = row['close'] < row['open']
print(f"  Bullish: {is_bullish}")
print(f"  Bearish: {is_bearish}")

if not is_bullish and not is_bearish:
    print(f"  FALHOU! Barra DOJI")
    exit()

# 6) Verificar rompimento
print(f"\n[6] Verificar rompimento na proxima barra:")
if i + 1 >= len(df):
    print(f"  FALHOU! Nao ha proxima barra")
    exit()

next_row = df.iloc[i + 1]
print(f"\nProxima barra ({i+1}):")
print(f"  Time: {next_row['time']}")
print(f"  OHLC: O={next_row['open']:.2f} H={next_row['high']:.2f} L={next_row['low']:.2f} C={next_row['close']:.2f}")

if is_bearish:
    minima_elefante = row['low']
    print(f"\n  Barra BEARISH - verificar rompimento de minima")
    print(f"  Minima elefante: {minima_elefante:.2f}")
    print(f"  Low proxima: {next_row['low']:.2f}")
    
    if next_row['low'] < minima_elefante:
        print(f"  ROMPEU! {next_row['low']:.2f} < {minima_elefante:.2f}")
        
        # Verificar horário da barra de ENTRADA
        hora_entrada = next_row['time'].hour
        minuto_entrada = next_row['time'].minute
        print(f"\n  Verificar horario da ENTRADA:")
        print(f"    Hora entrada: {hora_entrada:02d}:{minuto_entrada:02d}")
        
        if hora_entrada < params['horario_inicio'] or (hora_entrada == params['horario_inicio'] and minuto_entrada < params['minuto_inicio']):
            print(f"    FALHOU! Antes do horario")
            exit()
        if hora_entrada > params['horario_fim'] or (hora_entrada == params['horario_fim'] and minuto_entrada > params['minuto_fim']):
            print(f"    FALHOU! Depois do horario")
            exit()
        
        print(f"    OK!")
        print(f"\n==> SINAL SHORT DETECTADO na barra {i+1}!")
    else:
        print(f"  NAO ROMPEU!")

print("\n" + "=" * 80)

