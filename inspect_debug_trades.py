"""
Inspecionar trades DEBUG (nova execução com filtro corrigido)
"""
import pandas as pd

# Carregar trades DEBUG (nova execução)
rust_trades = pd.read_csv("results/validation/rust_trades_month_WARMUP_DEBUG_trades_detailed.csv")

# Carregar dataset
df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

print("=" * 80)
print("INSPECAO TRADES DEBUG (Nova Execucao)")
print("=" * 80)

print(f"\nTotal trades: {len(rust_trades)}")

# Rust
print("\n[RUST DEBUG] Primeiros 10 trades:")
for i in range(min(10, len(rust_trades))):
    trade = rust_trades.iloc[i]
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        time = df_filtered.iloc[idx]['time']
        is_warmup = df_filtered.iloc[idx].get('is_warmup', False)
        warmup_flag = "[WARMUP!]" if is_warmup else ""
        print(f"  {i+1}. idx={idx} time={time} {trade['type']} entry={trade['entry']:.2f} pnl={trade['pnl']:.2f} {warmup_flag}")

# Verificar se tem trades do warmup
rust_warmup_count = 0
for _, trade in rust_trades.iterrows():
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered) and df_filtered.iloc[idx].get('is_warmup', False):
        rust_warmup_count += 1

if rust_warmup_count > 0:
    print(f"\n[PROBLEMA] Rust salvou {rust_warmup_count} trades do warmup!")
else:
    print(f"\n[OK] Rust NAO salvou trades do warmup! Filtro funcionando corretamente!")

# Range de datas
rust_times = []
for _, trade in rust_trades.iterrows():
    idx = int(trade['entry_idx'])
    if idx < len(df_filtered):
        rust_times.append(df_filtered.iloc[idx]['time'])

if rust_times:
    print(f"\n[RANGE] {min(rust_times)} a {max(rust_times)}")

print("=" * 80)

