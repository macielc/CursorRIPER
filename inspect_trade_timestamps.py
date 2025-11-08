"""
Inspecionar timestamps dos trades Python vs Rust
"""
import pandas as pd

# Carregar trades
python_trades = pd.read_csv("results/validation/python_trades_month_WARMUP.csv")
rust_trades = pd.read_csv("results/validation/rust_trades_month_WARMUP_trades_detailed.csv")

# Carregar dataset
df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

print("=" * 80)
print("INSPECAO DE TIMESTAMPS")
print("=" * 80)

# Python
print("\n[PYTHON] Primeiros 10 trades:")
for i in range(min(10, len(python_trades))):
    trade = python_trades.iloc[i]
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        time = df_filtered.iloc[idx]['time']
        print(f"  {i+1}. idx={idx} time={time} {trade['type']} entry={trade['entry']:.2f} pnl={trade['pnl']:.2f}")

# Rust
print("\n[RUST] Primeiros 10 trades:")
for i in range(min(10, len(rust_trades))):
    trade = rust_trades.iloc[i]
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        time = df_filtered.iloc[idx]['time']
        is_warmup = df_filtered.iloc[idx].get('is_warmup', False)
        warmup_flag = "[WARMUP!]" if is_warmup else ""
        print(f"  {i+1}. idx={idx} time={time} {trade['type']} entry={trade['entry']:.2f} pnl={trade['pnl']:.2f} {warmup_flag}")

# Verificar se Rust está salvando trades de setembro (warmup)
print("\n[VERIFICACAO] Rust salvando trades do warmup?")
rust_warmup_count = 0
for _, trade in rust_trades.iterrows():
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered) and df_filtered.iloc[idx].get('is_warmup', False):
        rust_warmup_count += 1

if rust_warmup_count > 0:
    print(f"  PROBLEMA: Rust salvou {rust_warmup_count} trades do periodo de warmup (setembro)!")
    print(f"  Rust deveria salvar APENAS trades de outubro (is_warmup=False)")
else:
    print(f"  OK: Rust nao salvou trades do warmup")

# Verificar range de datas
print("\n[RANGE DE DATAS]")
python_times = []
for _, trade in python_trades.iterrows():
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        python_times.append(df_filtered.iloc[idx]['time'])

rust_times = []
for _, trade in rust_trades.iterrows():
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        rust_times.append(df_filtered.iloc[idx]['time'])

if python_times:
    print(f"  Python: {min(python_times)} a {max(python_times)}")
if rust_times:
    print(f"  Rust:   {min(rust_times)} a {max(rust_times)}")

print("=" * 80)

