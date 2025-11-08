"""
Verificar campo is_warmup para índices específicos (1659, 1682)
"""
import pandas as pd

df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour

# Filtrar 9h-15h (como Rust faz)
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

print("=" * 80)
print("VERIFICACAO is_warmup PARA INDICES ESPECIFICOS")
print("=" * 80)

# Índices problemáticos
problematic_indices = [1659, 1682]

for idx in problematic_indices:
    if idx < len(df_filtered):
        row = df_filtered.iloc[idx]
        print(f"\nIndice {idx}:")
        print(f"  Time: {row['time']}")
        print(f"  is_warmup: {row['is_warmup']}")
        print(f"  Open: {row['open']:.2f}")
        
        if row['is_warmup']:
            print(f"  STATUS: WARMUP (setembro) - deveria ser IGNORADO!")
        else:
            print(f"  STATUS: TARGET (outubro) - OK salvar")
    else:
        print(f"\nIndice {idx}: FORA DO RANGE (max: {len(df_filtered)-1})")

# Verificar transição setembro -> outubro
print(f"\n\n" + "=" * 80)
print("TRANSICAO SETEMBRO -> OUTUBRO")
print("=" * 80)

# Encontrar primeira barra de outubro
first_october_idx = df_filtered[df_filtered['is_warmup'] == False].index[0]
print(f"\nPrimeira barra de outubro: idx={first_october_idx}")
print(f"  Time: {df_filtered.iloc[first_october_idx]['time']}")

# Mostrar barras ao redor da transição
print(f"\nBarras ao redor da transição (1840-1860):")
for idx in range(max(0, first_october_idx-10), min(len(df_filtered), first_october_idx+10)):
    row = df_filtered.iloc[idx]
    warmup_str = "[WARMUP]" if row['is_warmup'] else "[TARGET]"
    print(f"  {idx}: {row['time']} {warmup_str}")

print("=" * 80)

