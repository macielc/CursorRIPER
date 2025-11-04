"""
Debug: Verificar quantos elefantes existem com parâmetros relaxados
"""
import pandas as pd
import numpy as np

date = '2024-06-12'

print(f"Analisando dia {date}...")
df = pd.read_csv('data/golden/WINFUT_M5_Golden_Data.csv')
df['time'] = pd.to_datetime(df['time'])

target_date = pd.to_datetime(date)
df_day = df[df['time'].dt.date == target_date.date()].copy()
df_day = df_day[(df_day['time'].dt.hour >= 9) & (df_day['time'].dt.hour <= 14)].copy()

print(f"Candles: {len(df_day)}")

# Calcular amplitude e volume
df_day['amplitude'] = df_day['high'] - df_day['low']
df_day['body'] = abs(df_day['close'] - df_day['open'])

# Médias
df_day['amp_ma25'] = df_day['amplitude'].rolling(window=25).mean()
df_day['vol_ma20'] = df_day['real_volume'].rolling(window=20).mean()

# Verificar quantos candles atendem cada critério
print(f"\nANALISE DE CRITERIOS:")

count_amp = 0
count_vol = 0
count_body = 0
count_todos = 0

for i in range(25, len(df_day)):
    row = df_day.iloc[i]
    
    amp_ok = row['amplitude'] > row['amp_ma25'] * 1.35
    vol_ok = row['real_volume'] > row['vol_ma20'] * 1.3
    body_pct = row['body'] / row['amplitude'] if row['amplitude'] > 0 else 0
    body_ok = body_pct > 0.7  # 1 - 0.30
    
    if amp_ok:
        count_amp += 1
    if vol_ok:
        count_vol += 1
    if body_ok:
        count_body += 1
    if amp_ok and vol_ok and body_ok:
        count_todos += 1
        print(f"\n  ELEFANTE DETECTADO em {row['time']}!")
        print(f"    Amplitude: {row['amplitude']:.2f} (MA: {row['amp_ma25']:.2f}, Mult: {row['amplitude']/row['amp_ma25']:.2f}x)")
        print(f"    Volume: {row['real_volume']:,.0f} (MA: {row['vol_ma20']:,.0f}, Mult: {row['real_volume']/row['vol_ma20']:.2f}x)")
        print(f"    Corpo%: {body_pct:.1%} (Min: 70%)")

print(f"\nCandles que atendem:")
print(f"  Amplitude > 1.35x MA: {count_amp}")
print(f"  Volume > 1.3x MA: {count_vol}")
print(f"  Corpo > 70%: {count_body}")
print(f"  TODOS criterios: {count_todos}")

# Tentar com parametros mais relaxados
print(f"\n\nTESTE COM PARAMETROS RELAXADOS (1.2x amp, 1.2x vol, 60% corpo):")
count_relaxed = 0
for i in range(25, len(df_day)):
    row = df_day.iloc[i]
    
    amp_ok = row['amplitude'] > row['amp_ma25'] * 1.2
    vol_ok = row['real_volume'] > row['vol_ma20'] * 1.2
    body_pct = row['body'] / row['amplitude'] if row['amplitude'] > 0 else 0
    body_ok = body_pct > 0.6
    
    if amp_ok and vol_ok and body_ok:
        count_relaxed += 1

print(f"  Elefantes com parametros relaxados: {count_relaxed}")

