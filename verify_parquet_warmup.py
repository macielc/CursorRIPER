"""
Verificar se coluna is_warmup está correta no Parquet
"""
import pandas as pd

df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour

print("=" * 80)
print("VERIFICACAO COLUNA is_warmup NO PARQUET")
print("=" * 80)

# Verificar se coluna existe
if 'is_warmup' not in df.columns:
    print("\nERRO: Coluna 'is_warmup' NAO EXISTE no Parquet!")
    print(f"Colunas disponiveis: {list(df.columns)}")
else:
    print("\nOK: Coluna 'is_warmup' existe")
    
    # Verificar valores
    print(f"\nTotal candles: {len(df)}")
    print(f"is_warmup=True: {df['is_warmup'].sum()}")
    print(f"is_warmup=False: {(~df['is_warmup']).sum()}")
    
    # Verificar range de datas
    df_warmup = df[df['is_warmup'] == True]
    df_target = df[df['is_warmup'] == False]
    
    if len(df_warmup) > 0:
        print(f"\nWarmup (is_warmup=True):")
        print(f"  Range: {df_warmup['time'].min()} a {df_warmup['time'].max()}")
        print(f"  Candles: {len(df_warmup)}")
    
    if len(df_target) > 0:
        print(f"\nTarget (is_warmup=False):")
        print(f"  Range: {df_target['time'].min()} a {df_target['time'].max()}")
        print(f"  Candles: {len(df_target)}")
    
    # Filtrar 9h-15h e verificar novamente
    df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy()
    
    print(f"\n\nAPOS FILTRO 9h-15h:")
    print(f"Total candles: {len(df_filtered)}")
    print(f"is_warmup=True: {df_filtered['is_warmup'].sum()}")
    print(f"is_warmup=False: {(~df_filtered['is_warmup']).sum()}")
    
    df_warmup_filt = df_filtered[df_filtered['is_warmup'] == True]
    df_target_filt = df_filtered[df_filtered['is_warmup'] == False]
    
    if len(df_warmup_filt) > 0:
        print(f"\nWarmup (is_warmup=True) apos filtro:")
        print(f"  Range: {df_warmup_filt['time'].min()} a {df_warmup_filt['time'].max()}")
        print(f"  Candles: {len(df_warmup_filt)}")
    
    if len(df_target_filt) > 0:
        print(f"\nTarget (is_warmup=False) apos filtro:")
        print(f"  Range: {df_target_filt['time'].min()} a {df_target_filt['time'].max()}")
        print(f"  Candles: {len(df_target_filt)}")

print("=" * 80)

