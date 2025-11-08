"""
Comparar Python vs Rust (mês com WARMUP)
Versão 2: Comparar por TIMESTAMP + PRICE ao invés de apenas PRICE
"""
import pandas as pd

print("=" * 80)
print("COMPARACAO PYTHON VS RUST - V2 (TIME-BASED)")
print("=" * 80)

# Carregar trades
python_trades = pd.read_csv("results/validation/python_trades_month_WARMUP.csv")
rust_trades = pd.read_csv("results/validation/rust_trades_month_WARMUP_trades_detailed.csv")

# Carregar dataset para pegar timestamps
df = pd.read_parquet("data/golden/WINFUT_M5_Month_Oct2025_WARMUP.parquet")
df['time'] = pd.to_datetime(df['time'])
df['hour'] = df['time'].dt.hour
df_filtered = df[(df['hour'] >= 9) & (df['hour'] <= 15)].copy().reset_index(drop=True)

# Adicionar timestamps aos trades
print("\n[1/3] Adicionando timestamps aos trades...")

# Python trades
python_trades['entry_time'] = python_trades['entry_idx'].apply(
    lambda idx: df_filtered.iloc[idx]['time'] if idx < len(df_filtered) else None
)

# Rust trades
rust_trades['entry_time'] = rust_trades['entry_idx'].apply(
    lambda idx: df_filtered.iloc[idx]['time'] if idx < len(df_filtered) else None
)

print(f"  Python: {len(python_trades)} trades com timestamps")
print(f"  Rust:   {len(rust_trades)} trades com timestamps")

# Converter tipos
if 'type' in python_trades.columns:
    python_trades['type'] = python_trades['type'].str.upper()
if 'type' in rust_trades.columns:
    rust_trades['type'] = rust_trades['type'].str.upper()

print("\n[2/3] Comparando por (TIME + PRICE + TYPE)...")

# Criar dicts: (time, type, entry) -> trade
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
if len(missing_in_rust) > 0 and len(missing_in_rust) <= 10:
    print("\n  Trades faltando:")
    for key in sorted(missing_in_rust, key=lambda k: k[0])[:10]:
        trade = python_by_time[key]
        print(f"    {key[0]} {key[1]} entry={key[2]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades extras no Rust: {len(extra_in_rust)}")
if len(extra_in_rust) > 0 and len(extra_in_rust) <= 10:
    print("\n  Trades extras:")
    for key in sorted(extra_in_rust, key=lambda k: k[0])[:10]:
        trade = rust_by_time[key]
        print(f"    {key[0]} {key[1]} entry={key[2]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades comuns: {len(common_keys)}")

# Comparar PnL dos trades comuns
print("\n[3/3] Comparando PnL dos trades comuns...")

if len(common_keys) > 0:
    divergencias = 0
    for key in sorted(common_keys, key=lambda k: k[0]):
        py_trade = python_by_time[key]
        rust_trade = rust_by_time[key]
        
        py_pnl = py_trade['pnl']
        rust_pnl = rust_trade['pnl']
        
        if abs(py_pnl - rust_pnl) > 1.0:
            divergencias += 1
            if divergencias <= 5:
                print(f"\n  [DIVERGENCIA] {key[0]} {key[1]} entry={key[2]:.2f}:")
                print(f"    Python PnL: {py_pnl:.2f} (exit={py_trade['exit']:.2f}, reason={py_trade.get('exit_reason', 'N/A')})")
                print(f"    Rust PnL:   {rust_pnl:.2f} (exit={rust_trade['exit']:.2f}, reason={rust_trade.get('exit_reason', 'N/A')})")
    
    if divergencias == 0:
        print("\n  [100% IDENTICO] Todos os trades comuns tem PnL identico!")
    else:
        print(f"\n  [AVISO] {divergencias} trades com PnL divergente")

# PnL total
python_pnl_total = python_trades['pnl'].sum() if 'pnl' in python_trades.columns else 0
rust_pnl_total = rust_trades['pnl'].sum() if 'pnl' in rust_trades.columns else 0

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"  Python: {len(python_trades)} trades, PnL total: {python_pnl_total:.2f}")
print(f"  Rust:   {len(rust_trades)} trades, PnL total: {rust_pnl_total:.2f}")
print(f"  Diferenca: {len(python_trades) - len(rust_trades)} trades, {python_pnl_total - rust_pnl_total:.2f} PnL")

if len(missing_in_rust) == 0 and len(extra_in_rust) == 0:
    print("\n  [100% IDENTICO] Validacao COMPLETA!")
else:
    acuracia = (len(common_keys) / len(python_by_time)) * 100 if len(python_by_time) > 0 else 0
    print(f"\n  Acuracia: {acuracia:.1f}% ({len(common_keys)}/{len(python_by_time)})")

print("=" * 80)

