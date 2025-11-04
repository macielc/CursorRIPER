"""
Compara resultados MT5 vs Python
"""

import sys
from pathlib import Path
from bs4 import BeautifulSoup

if len(sys.argv) < 2:
    print("Uso: python comparar_mt5_python.py <arquivo_html_mt5>")
    sys.exit(1)

html_file = sys.argv[1]

print("")
print("=" * 80)
print("COMPARACAO MT5 vs PYTHON")
print("=" * 80)
print("")

# Ler HTML MT5
print(f"Lendo: {html_file}")
with open(html_file, 'r', encoding='latin-1') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Extrair informações chave
def extract_value(soup, text):
    """Extrai valor de uma linha da tabela"""
    for row in soup.find_all('tr'):
        cells = row.find_all('td')
        if len(cells) >= 2:
            if text.lower() in cells[0].get_text().lower():
                return cells[1].get_text().strip()
    return "N/A"

# Resultados MT5
print("")
print("=" * 80)
print("RESULTADOS MT5")
print("=" * 80)

total_trades_mt5 = extract_value(soup, "total de")
profit_mt5 = extract_value(soup, "lucro l")
balance_mt5 = extract_value(soup, "balan")
drawdown_mt5 = extract_value(soup, "rebaixamento")
win_rate_mt5 = extract_value(soup, "negocia")
profit_factor_mt5 = extract_value(soup, "fator de")

print(f"Total de Trades: {total_trades_mt5}")
print(f"Lucro Liquido: {profit_mt5}")
print(f"Balanco Final: {balance_mt5}")
print(f"Drawdown: {drawdown_mt5}")
print(f"Win Rate: {win_rate_mt5}")
print(f"Profit Factor: {profit_factor_mt5}")

# Resultados Python
print("")
print("=" * 80)
print("RESULTADOS PYTHON")
print("=" * 80)
print(f"Total de Trades: 508")
print(f"Lucro Liquido: -51,723 pontos = -R$ 10,344.60")
print(f"Win Rate: 18%")
print(f"Profit Factor: 0.67")

# Comparação
print("")
print("=" * 80)
print("COMPARACAO")
print("=" * 80)

# Tentar extrair número de trades do MT5
try:
    trades_mt5_num = int(total_trades_mt5.split()[0])
    trades_python_num = 508
    
    diff = abs(trades_mt5_num - trades_python_num)
    diff_pct = (diff / trades_python_num) * 100
    
    print(f"Trades MT5: {trades_mt5_num}")
    print(f"Trades Python: {trades_python_num}")
    print(f"Diferenca: {diff} trades ({diff_pct:.1f}%)")
    print("")
    
    if diff == 0:
        print("ALINHAMENTO PERFEITO!")
        print("MT5 e Python geraram EXATAMENTE o mesmo numero de trades!")
    elif diff_pct < 5:
        print("ALINHAMENTO BOM!")
        print("Diferenca < 5% - praticamente identico")
    elif diff_pct < 10:
        print("ALINHAMENTO ACEITAVEL")
        print("Diferenca < 10% - pode haver pequenas diferencas de logica")
    else:
        print("ALINHAMENTO RUIM")
        print("Diferenca > 10% - ainda existem discrepancias significativas")
except:
    print("Nao foi possivel extrair numero de trades do MT5")
    print(f"MT5 reportou: {total_trades_mt5}")

print("")
print("=" * 80)
print("PARAMETROS USADOS")
print("=" * 80)

# Tentar extrair parâmetros
params_section = soup.find(string=lambda text: text and 'parâmetros' in text.lower())
if params_section:
    # Procurar tabela de parâmetros
    params_table = params_section.find_parent('table')
    if params_table:
        print("Parametros encontrados no relatorio:")
        for row in params_table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                print(f"  {cells[0].get_text().strip()}: {cells[1].get_text().strip()}")
else:
    print("Parametros esperados:")
    print("  InpMinAmplitudeMult = 1.35")
    print("  InpMinVolumeMult = 1.3")
    print("  InpMaxSombraPct = 0.30")
    print("  InpHorarioFim = 17")
    print("  InpLookbackAmplitude = 25")
    print("  InpSL_ATR_Mult = 2.0")
    print("  InpTP_ATR_Mult = 3.0")
    print("  InpUsarTrailing = false")

print("")

