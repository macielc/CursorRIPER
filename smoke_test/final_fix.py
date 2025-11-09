import re

content = open('run_smoke_test_hibrido.py', 'r', encoding='utf-8').read()

# Substituir todas as referências
content = re.sub(r"\['pnl'\]", "['total_return']", content)
content = re.sub(r'"pnl"', '"total_return"', content)
content = re.sub(r"'pnl'", "'total_return'", content)

# Max drawdown
content = re.sub(r"'max_drawdown'", "'max_drawdown_pct'", content)

# Trades
content = re.sub(r"\['trades'\]", "['total_trades']", content)

# Win rate já está correto

open('run_smoke_test_hibrido.py', 'w', encoding='utf-8').write(content)
print("All fixed!")

