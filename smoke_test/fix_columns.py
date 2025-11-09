content = open('run_smoke_test_hibrido.py', 'r', encoding='utf-8').read()

# Substituições
content = content.replace("df['pnl']", "df['total_return']")
content = content.replace("'pnl', ascending", "'total_return', ascending")
content = content.replace("['sharpe', 'pnl']", "['sharpe_ratio', 'total_return']")
content = content.replace("['pnl', 'sharpe'", "['total_return', 'sharpe_ratio'")
content = content.replace("'sharpe'", "'sharpe_ratio'")
content = content.replace("param_cols = [col for col in df.columns if col not in ['pnl', 'sharpe_ratio', 'max_drawdown', 'win_rate', 'trades']]", 
                         "param_cols = [col for col in df.columns if col not in ['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'total_trades', 'success', 'total_return_pct', 'profit_factor']]")

# Salvar
open('run_smoke_test_hibrido.py', 'w', encoding='utf-8').write(content)
print("Fixed!")

