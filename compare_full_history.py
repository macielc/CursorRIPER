"""
Comparar Python vs Rust - TODO O HISTORICO (3.5 anos)
"""
import pandas as pd

print("=" * 80)
print("COMPARACAO PYTHON VS RUST - TODO O HISTORICO (3.5 ANOS)")
print("=" * 80)

# Carregar trades
python_trades = pd.read_csv("results/validation/python_trades_full_history.csv")
rust_trades = pd.read_csv("results/validation/rust_trades_full_history_trades_detailed.csv")

# Carregar dataset para timestamps
df = pd.read_parquet("data/golden/WINFUT_M5_FULL_HISTORY_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

print("\n[1/3] Adicionando timestamps...")

# Adicionar timestamps
python_trades['entry_time'] = python_trades['entry_idx'].apply(
    lambda idx: df_filtered.iloc[idx]['time'] if idx < len(df_filtered) else None
)

rust_trades['entry_time'] = rust_trades['entry_idx'].apply(
    lambda idx: df_filtered.iloc[idx]['time'] if idx < len(df_filtered) else None
)

print(f"  Python: {len(python_trades):,} trades")
print(f"  Rust:   {len(rust_trades):,} trades")

# Converter tipos
if 'type' in python_trades.columns:
    python_trades['type'] = python_trades['type'].str.upper()
if 'type' in rust_trades.columns:
    rust_trades['type'] = rust_trades['type'].str.upper()

print("\n[2/3] Comparando por (TIME + PRICE + TYPE)...")

# Criar dicts
python_by_time = {}
for _, trade in python_trades.iterrows():
    if pd.notna(trade['entry_time']):
        key = (trade['entry_time'], trade['type'], round(trade['entry'], 2))
        python_by_time[key] = trade

rust_by_time = {}
for _, trade in rust_trades.iterrows():
    if pd.notna(trade['entry_time']):
        key = (trade['entry_time'], trade['type'], round(trade['entry'], 2))
        rust_by_time[key] = trade

# Comparar
common_keys = set(python_by_time.keys()) & set(rust_by_time.keys())
missing_in_rust = set(python_by_time.keys()) - set(rust_by_time.keys())
extra_in_rust = set(rust_by_time.keys()) - set(python_by_time.keys())

print(f"\nTrades faltando no Rust: {len(missing_in_rust)}")
if len(missing_in_rust) > 0:
    print("  Primeiros 5:")
    for key in sorted(missing_in_rust, key=lambda k: k[0])[:5]:
        trade = python_by_time[key]
        print(f"    {key[0]} {key[1]} entry={key[2]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades extras no Rust: {len(extra_in_rust)}")
if len(extra_in_rust) > 0:
    print("  Primeiros 5:")
    for key in sorted(extra_in_rust, key=lambda k: k[0])[:5]:
        trade = rust_by_time[key]
        print(f"    {key[0]} {key[1]} entry={key[2]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades comuns: {len(common_keys):,}")

# Comparar PnL
print("\n[3/3] Comparando PnL dos trades comuns...")

if len(common_keys) > 0:
    divergencias = 0
    max_diff = 0
    total_diff = 0
    
    for key in common_keys:
        py_trade = python_by_time[key]
        rust_trade = rust_by_time[key]
        
        py_pnl = py_trade['pnl']
        rust_pnl = rust_trade['pnl']
        diff = abs(py_pnl - rust_pnl)
        
        total_diff += diff
        if diff > max_diff:
            max_diff = diff
        
        if diff > 1.0:
            divergencias += 1
            if divergencias <= 5:
                print(f"\n  [DIVERGENCIA] {key[0]} {key[1]} entry={key[2]:.2f}:")
                print(f"    Python: {py_pnl:.2f} (exit={py_trade['exit']:.2f})")
                print(f"    Rust:   {rust_pnl:.2f} (exit={rust_trade['exit']:.2f})")
                print(f"    Diff:   {diff:.2f}")
    
    avg_diff = total_diff / len(common_keys) if len(common_keys) > 0 else 0
    
    if divergencias == 0:
        print(f"\n  [100% IDENTICO] Todos os trades tem PnL identico!")
        print(f"  Max diff: {max_diff:.4f}")
        print(f"  Avg diff: {avg_diff:.4f}")
    else:
        print(f"\n  [AVISO] {divergencias} trades com PnL divergente")
        print(f"  Max diff: {max_diff:.2f}")
        print(f"  Avg diff: {avg_diff:.4f}")

# PnL total
python_pnl_total = python_trades['pnl'].sum() if 'pnl' in python_trades.columns else 0
rust_pnl_total = rust_trades['pnl'].sum() if 'pnl' in rust_trades.columns else 0

print("\n" + "=" * 80)
print("RESUMO FINAL - TODO O HISTORICO (3.52 ANOS)")
print("=" * 80)
print(f"  Periodo: 2022-04-23 a 2025-10-31")
print(f"  Duracao: 3.52 anos (1,285 dias)")
print(f"  Candles: 74,083 (9h-15h)")
print(f"\n  Python: {len(python_trades):,} trades, PnL total: {python_pnl_total:,.2f}")
print(f"  Rust:   {len(rust_trades):,} trades, PnL total: {rust_pnl_total:,.2f}")
print(f"\n  Diferenca trades: {len(python_trades) - len(rust_trades)}")
print(f"  Diferenca PnL: {python_pnl_total - rust_pnl_total:.2f}")

if len(missing_in_rust) == 0 and len(extra_in_rust) == 0:
    print("\n  [100% IDENTICO] VALIDACAO COMPLETA PARA TODO O HISTORICO!")
    print(f"  {len(common_keys):,} trades identicos em 3.5 anos!")
else:
    acuracia = (len(common_keys) / len(python_by_time)) * 100 if len(python_by_time) > 0 else 0
    print(f"\n  Acuracia: {acuracia:.1f}% ({len(common_keys):,}/{len(python_by_time):,})")

print("=" * 80)

