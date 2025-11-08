"""
Converte CSV Golden Data para Parquet (10-20x mais rapido)
"""
import pandas as pd
from pathlib import Path
import time

print("=" * 80)
print("CONVERTER CSV PARA PARQUET")
print("=" * 80)

# Caminhos
csv_path = "data/golden/WINFUT_M5_Golden_Data.csv"
parquet_path = "data/golden/WINFUT_M5_Golden_Data.parquet"

print(f"\nArquivo de entrada: {csv_path}")
print(f"Arquivo de saida: {parquet_path}\n")

# Carregar CSV
print("1) Carregando CSV...")
start = time.time()
df = pd.read_csv(csv_path, low_memory=False)
csv_time = time.time() - start
csv_size = Path(csv_path).stat().st_size / 1024 / 1024

print(f"   OK - Carregado em {csv_time:.1f}s")
print(f"   Linhas: {len(df):,}")
print(f"   Tamanho: {csv_size:.1f} MB (CSV)\n")

# Salvar Parquet
print("2) Salvando Parquet...")
start = time.time()
df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
parquet_time = time.time() - start
parquet_size = Path(parquet_path).stat().st_size / 1024 / 1024

print(f"   OK - Salvo em {parquet_time:.1f}s")
print(f"   Tamanho: {parquet_size:.1f} MB (Parquet)\n")

# Testar leitura Parquet
print("3) Testando leitura Parquet...")
start = time.time()
df_test = pd.read_parquet(parquet_path)
parquet_read_time = time.time() - start

print(f"   OK - Lido em {parquet_read_time:.1f}s")
print(f"   Linhas: {len(df_test):,}\n")

# Comparacao
print("=" * 80)
print("RESULTADOS:")
print("=" * 80)
print(f"Tamanho CSV:      {csv_size:.1f} MB")
print(f"Tamanho Parquet:  {parquet_size:.1f} MB")
print(f"Compressao:       {100 * (1 - parquet_size/csv_size):.1f}% menor")
print(f"\nLeitura CSV:      {csv_time:.1f}s")
print(f"Leitura Parquet:  {parquet_read_time:.1f}s")
print(f"Ganho:            {csv_time/parquet_read_time:.1f}x mais rapido")
print("=" * 80)
