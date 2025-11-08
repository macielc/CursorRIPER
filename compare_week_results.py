"""
Comparar resultados Python vs Rust - Semana completa
"""
import pandas as pd
from pathlib import Path

print("=" * 80)
print("COMPARACAO PYTHON VS RUST - SEMANA COMPLETA")
print("=" * 80)

# Carregar trades
py_file = Path("results/validation/python_trades_week.csv")
rust_file = Path("results/validation/rust_trades_week_trades_detailed.csv")

df_py = pd.read_csv(py_file)
df_rust = pd.read_csv(rust_file)

print(f"\nPYTHON: {len(df_py)} trades")
print(f"RUST:   {len(df_rust)} trades")

if len(df_py) != len(df_rust):
    print("\nDIVERGENCIA: Numero de trades diferente!")
    print("\nTrades Python:")
    print(df_py[['entry_idx', 'exit_idx', 'type', 'entry', 'exit', 'pnl', 'exit_reason']])
    
    print("\nTrades Rust:")
    print(df_rust[['entry_idx', 'exit_idx', 'type', 'entry', 'exit', 'pnl', 'exit_reason']])
    
    # Identificar qual trade está faltando/sobrando
    print("\n" + "=" * 80)
    print("ANALISE DE DIVERGENCIA")
    print("=" * 80)
    
    py_indices = set(df_py['entry_idx'].values)
    rust_indices = set(df_rust['entry_idx'].values)
    
    missing_in_rust = py_indices - rust_indices
    extra_in_rust = rust_indices - py_indices
    
    if missing_in_rust:
        print(f"\nFALTANDO NO RUST (entry_idx): {missing_in_rust}")
        for idx in missing_in_rust:
            trade = df_py[df_py['entry_idx'] == idx].iloc[0]
            print(f"\nTrade Python #{idx}:")
            print(f"  Entry: {trade['entry']:.2f}")
            print(f"  Exit: {trade['exit']:.2f}")
            print(f"  PnL: {trade['pnl']:.2f}")
            print(f"  Type: {trade['type']}")
    
    if extra_in_rust:
        print(f"\nEXTRA NO RUST (entry_idx): {extra_in_rust}")
        for idx in extra_in_rust:
            trade = df_rust[df_rust['entry_idx'] == idx].iloc[0]
            print(f"\nTrade Rust #{idx}:")
            print(f"  Entry: {trade['entry']:.2f}")
            print(f"  Exit: {trade['exit']:.2f}")
            print(f"  PnL: {trade['pnl']:.2f}")
            print(f"  Type: {trade['type']}")

else:
    print("\nOK: Mesmo numero de trades!")
    
    print("\n" + "=" * 80)
    print("COMPARACAO TRADE-BY-TRADE")
    print("=" * 80)
    
    # Ordenar por entry_idx
    df_py = df_py.sort_values('entry_idx').reset_index(drop=True)
    df_rust = df_rust.sort_values('entry_idx').reset_index(drop=True)
    
    all_match = True
    
    for i in range(len(df_py)):
        py_trade = df_py.iloc[i]
        rust_trade = df_rust.iloc[i]
        
        entry_match = abs(py_trade['entry'] - rust_trade['entry']) < 0.1
        exit_match = abs(py_trade['exit'] - rust_trade['exit']) < 0.1
        pnl_match = abs(py_trade['pnl'] - rust_trade['pnl']) < 1.0
        
        if not (entry_match and exit_match and pnl_match):
            all_match = False
            print(f"\nDIVERGENCIA Trade #{i+1}:")
            print(f"  Entry idx: Py={py_trade['entry_idx']} | Rust={rust_trade['entry_idx']}")
            print(f"  Entry:     Py={py_trade['entry']:.2f} | Rust={rust_trade['entry']:.2f}")
            print(f"  Exit:      Py={py_trade['exit']:.2f} | Rust={rust_trade['exit']:.2f}")
            print(f"  PnL:       Py={py_trade['pnl']:.2f} | Rust={rust_trade['pnl']:.2f}")
        else:
            print(f"\nOK: Trade #{i+1} IDENTICO:")
            print(f"  Entry idx: {py_trade['entry_idx']}")
            print(f"  Entry:     {py_trade['entry']:.2f}")
            print(f"  PnL:       {py_trade['pnl']:.2f} pts")
    
    if all_match:
        print("\n" + "=" * 80)
        print("OK: TODOS OS TRADES SAO IDENTICOS!")
        print("=" * 80)

# Resumo final
print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

py_pnl_total = df_py['pnl'].sum()
rust_pnl_total = df_rust['pnl'].sum()

print(f"\nPython Total PnL: {py_pnl_total:.2f} pts")
print(f"Rust Total PnL:   {rust_pnl_total:.2f} pts")
print(f"Diferenca:        {abs(py_pnl_total - rust_pnl_total):.2f} pts")

if abs(py_pnl_total - rust_pnl_total) < 1.0:
    print("\nOK: PnL TOTAL IDENTICO!")
else:
    print(f"\nDIVERGENCIA: {abs(py_pnl_total - rust_pnl_total):.2f} pts")

print("\n" + "=" * 80)

