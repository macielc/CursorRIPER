"""
Comparar resultados Python vs Rust - Mês completo
"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("COMPARACAO PYTHON VS RUST - MES COMPLETO (OUTUBRO 2025)")
print("=" * 80)

# Carregar trades
py_file = Path("results/validation/python_trades_month.csv")
rust_file = Path("results/validation/rust_trades_month_trades_detailed.csv")

df_py = pd.read_csv(py_file)
df_rust = pd.read_csv(rust_file)

print(f"\nPYTHON: {len(df_py)} trades")
print(f"RUST:   {len(df_rust)} trades")
print(f"DIFERENCA: {abs(len(df_py) - len(df_rust))} trades")

if len(df_py) != len(df_rust):
    print("\nDIVERGENCIA: Numero de trades diferente!")
    
    # Identificar quais trades estão diferentes
    py_indices = set(df_py['entry_idx'].values)
    rust_indices = set(df_rust['entry_idx'].values)
    
    missing_in_rust = py_indices - rust_indices
    extra_in_rust = rust_indices - py_indices
    
    if missing_in_rust:
        print(f"\nFALTANDO NO RUST ({len(missing_in_rust)} trades):")
        for idx in sorted(missing_in_rust):
            trade = df_py[df_py['entry_idx'] == idx].iloc[0]
            print(f"  Entry idx {idx}: {trade['type']}, Entry={trade['entry']:.2f}, PnL={trade['pnl']:.2f}")
    
    if extra_in_rust:
        print(f"\nEXTRA NO RUST ({len(extra_in_rust)} trades):")
        for idx in sorted(extra_in_rust):
            trade = df_rust[df_rust['entry_idx'] == idx].iloc[0]
            print(f"  Entry idx {idx}: {trade['type']}, Entry={trade['entry']:.2f}, PnL={trade['pnl']:.2f}")
    
    # Trades em comum
    common_indices = py_indices & rust_indices
    print(f"\nTRADES EM COMUM: {len(common_indices)}")
    
    # Verificar se os trades em comum são idênticos
    mismatches = 0
    for idx in sorted(common_indices):
        py_trade = df_py[df_py['entry_idx'] == idx].iloc[0]
        rust_trade = df_rust[df_rust['entry_idx'] == idx].iloc[0]
        
        pnl_diff = abs(py_trade['pnl'] - rust_trade['pnl'])
        if pnl_diff > 1.0:
            mismatches += 1
            print(f"\n  Divergencia no trade {idx}:")
            print(f"    Python: PnL={py_trade['pnl']:.2f}")
            print(f"    Rust:   PnL={rust_trade['pnl']:.2f}")
            print(f"    Diff:   {pnl_diff:.2f} pts")
    
    if mismatches == 0:
        print("  Todos os trades em comum sao identicos! OK")

else:
    print("\nOK: Mesmo numero de trades!")
    
    # Comparar trade-by-trade
    df_py = df_py.sort_values('entry_idx').reset_index(drop=True)
    df_rust = df_rust.sort_values('entry_idx').reset_index(drop=True)
    
    all_match = True
    for i in range(len(df_py)):
        py_trade = df_py.iloc[i]
        rust_trade = df_rust.iloc[i]
        
        pnl_match = abs(py_trade['pnl'] - rust_trade['pnl']) < 1.0
        
        if not pnl_match:
            all_match = False
            print(f"\nDivergencia Trade #{i+1} (entry_idx={py_trade['entry_idx']}):")
            print(f"  PnL: Py={py_trade['pnl']:.2f} | Rust={rust_trade['pnl']:.2f}")
    
    if all_match:
        print("\nOK: TODOS OS TRADES SAO IDENTICOS!")

# Resumo PnL
print("\n" + "=" * 80)
print("RESUMO PnL")
print("=" * 80)

py_pnl_total = df_py['pnl'].sum()
rust_pnl_total = df_rust['pnl'].sum()

print(f"\nPython Total PnL: {py_pnl_total:.2f} pts")
print(f"Rust Total PnL:   {rust_pnl_total:.2f} pts")
print(f"Diferenca:        {abs(py_pnl_total - rust_pnl_total):.2f} pts")

if abs(py_pnl_total - rust_pnl_total) < 10.0:
    print("\nOK: PnL muito proximo!")
else:
    print(f"\nDIVERGENCIA: {abs(py_pnl_total - rust_pnl_total):.2f} pts")

print("\n" + "=" * 80)

