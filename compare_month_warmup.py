"""
Comparar resultados Python vs Rust (mês com WARMUP)
"""
import pandas as pd

print("=" * 80)
print("COMPARACAO PYTHON VS RUST - MES COM WARMUP")
print("=" * 80)

# Carregar trades (ambos COM WARMUP agora)
python_trades = pd.read_csv("results/validation/python_trades_month_WARMUP.csv")
rust_trades = pd.read_csv("results/validation/rust_trades_month_WARMUP_trades_detailed.csv")

print(f"\nTotal trades:")
print(f"  Python: {len(python_trades)}")
print(f"  Rust:   {len(rust_trades)}")

# Converter tipos para comparação
if 'type' in python_trades.columns:
    python_trades['type'] = python_trades['type'].str.upper()
if 'type' in rust_trades.columns:
    rust_trades['type'] = rust_trades['type'].str.upper()

# Comparar por ENTRY PRICE (índices são diferentes devido ao warmup)
print("\nOBS: Comparando por ENTRY PRICE (indices diferentes devido ao warmup)")

# Criar dicts: entry_price -> trade
python_by_price = {}
for _, trade in python_trades.iterrows():
    key = (trade['type'], round(trade['entry'], 2))
    python_by_price[key] = trade

rust_by_price = {}
for _, trade in rust_trades.iterrows():
    key = (trade['type'], round(trade['entry'], 2))
    rust_by_price[key] = trade

# Trades comuns
common_keys = set(python_by_price.keys()) & set(rust_by_price.keys())
missing_in_rust = set(python_by_price.keys()) - set(rust_by_price.keys())
extra_in_rust = set(rust_by_price.keys()) - set(python_by_price.keys())

print(f"\nTrades faltando no Rust: {len(missing_in_rust)}")
if missing_in_rust:
    print("\n  Trades faltando:")
    for key in sorted(missing_in_rust, key=lambda k: python_by_price[k]['entry_idx']):
        trade = python_by_price[key]
        print(f"    {key[0]} entry={key[1]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades extras no Rust: {len(extra_in_rust)}")
if extra_in_rust:
    print("\n  Trades extras:")
    for key in sorted(extra_in_rust, key=lambda k: rust_by_price[k]['entry_idx'])[:5]:
        trade = rust_by_price[key]
        print(f"    {key[0]} entry={key[1]:.2f} pnl={trade['pnl']:.2f}")

print(f"\nTrades comuns: {len(common_keys)}")

if len(common_keys) > 0:
    # Comparar trades comuns
    divergencias = 0
    for key in sorted(common_keys, key=lambda k: python_by_price[k]['entry_idx']):
        py_trade = python_by_price[key]
        rust_trade = rust_by_price[key]
        
        # Comparar PnL
        py_pnl = py_trade['pnl']
        rust_pnl = rust_trade['pnl']
        
        if abs(py_pnl - rust_pnl) > 1.0:
            divergencias += 1
            if divergencias <= 5:  # Mostrar primeiras 5 divergências
                print(f"\n  [DIVERGENCIA] {key[0]} entry={key[1]:.2f}:")
                print(f"    Python PnL: {py_pnl:.2f}")
                print(f"    Rust PnL:   {rust_pnl:.2f}")
    
    if divergencias == 0:
        print("\n  [OK] Todos os trades comuns tem PnL identico!")
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
    acuracia = (len(common_keys) / len(python_by_price)) * 100 if len(python_by_price) > 0 else 0
    print(f"\n  Acuracia: {acuracia:.1f}% ({len(common_keys)}/{len(python_by_price)})")

print("=" * 80)

