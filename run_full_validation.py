"""
VALIDACAO COMPLETA PYTHON VS RUST
Executa todos os passos em um único script
"""
import pandas as pd
import json
import ast
from pathlib import Path
import sys

# Add paths
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python'))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / 'engines' / 'python' / 'core'))

print("=" * 80)
print("VALIDACAO PYTHON VS RUST - COMPLETA")
print("=" * 80)

# ============================================================================
# PASSO 1: CRIAR DATASET FILTRADO
# ============================================================================
print("\n[1/6] CRIANDO DATASET FILTRADO (2025-10-15)...")

input_file = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
output_dataset = Path("data/golden/WINFUT_M5_2025-10-15.parquet")

df_full = pd.read_parquet(input_file)
df_full['time'] = pd.to_datetime(df_full['time'])
df_day = df_full[(df_full['time'] >= '2025-10-15 00:00:00') & (df_full['time'] < '2025-10-16 00:00:00')].copy()
df_day.to_parquet(output_dataset, index=False)

print(f"   Dataset criado: {len(df_day)} candles")
print(f"   Range: {df_day['time'].min()} a {df_day['time'].max()}")

# ============================================================================
# PASSO 2: DEFINIR CONFIG FIXA (Padrão para validação)
# ============================================================================
print("\n[2/6] DEFININDO CONFIG FIXA...")

# Config fixa para validação (valores razoáveis)
full_params = {
    'min_amplitude_mult': 2.0,
    'min_volume_mult': 1.5,
    'max_sombra_pct': 0.4,
    'lookback_amplitude': 20,
    'horario_inicio': 9,
    'minuto_inicio': 0,
    'horario_fim': 14,
    'minuto_fim': 55,
    'horario_fechamento': 15,
    'minuto_fechamento': 0,
    'sl_atr_mult': 2.0,
    'tp_atr_mult': 3.0,
    'usar_trailing': False
}

print(f"   Config validação:")
for k, v in full_params.items():
    print(f"     {k}: {v}")

# ============================================================================
# PASSO 3: EXECUTAR PYTHON BACKTEST
# ============================================================================
print("\n[3/6] EXECUTANDO PYTHON BACKTEST...")

from core.data_loader import DataLoader
from core.backtest_engine import BacktestEngine
from strategies import get_strategy

# Carregar dados
loader = DataLoader('5m')
loader.load()
loader.df = loader.df[
    (loader.df['time'] >= '2025-10-15 00:00:00') & 
    (loader.df['time'] < '2025-10-16 00:00:00')
]

print(f"   Candles carregados: {len(loader.df)}")

# Instanciar backtest engine
engine = BacktestEngine(loader.df, verbose=True)

# Executar backtest com estratégia
result = engine.run_strategy('barra_elefante', full_params)

if not result['success']:
    print(f"   ❌ Erro: {result.get('error', 'Desconhecido')}")
    sys.exit(1)

trades_python = result['trades']
print(f"   Trades gerados: {len(trades_python)}")

# Salvar
Path("results/validation").mkdir(parents=True, exist_ok=True)
trades_python_df = pd.DataFrame(trades_python)
trades_python_df.to_csv("results/validation/python_trades_20251015.csv", index=False)

print(f"   Salvos em: results/validation/python_trades_20251015.csv")

# Mostrar trades
for i, t in enumerate(trades_python, 1):
    print(f"\n   Trade #{i}:")
    print(f"     Type: {t['type']}")
    print(f"     Entry: idx {t['entry_idx']} @ {t['entry']:.2f}")
    print(f"     Exit:  idx {t['exit_idx']} @ {t['exit']:.2f}")
    print(f"     SL: {t['sl']:.2f} | TP: {t['tp']:.2f}")
    print(f"     PnL:   {t['pnl']:.2f} pts ({t['exit_reason']})")

# Métricas
print(f"\n   Métricas:")
print(f"     Total PnL: {result['total_return']:.2f} pts")
print(f"     Win Rate: {result['win_rate']*100:.1f}%")
print(f"     Sharpe: {result['sharpe_ratio']:.2f}")

# ============================================================================
# PASSO 4: CRIAR YAML PARA RUST
# ============================================================================
print("\n[4/6] CRIANDO CONFIG YAML PARA RUST...")

yaml_content = f'''strategy:
  name: "barra_elefante"
  description: "TOP 1 Python - Validacao"

param_grid:
  min_amplitude_mult:
    type: float
    values: [{full_params["min_amplitude_mult"]:.1f}]
  min_volume_mult:
    type: float
    values: [{full_params["min_volume_mult"]:.1f}]
  max_sombra_pct:
    type: float
    values: [{full_params["max_sombra_pct"]:.1f}]
  lookback_amplitude:
    type: integer
    values: [{int(full_params["lookback_amplitude"])}]
  horario_inicio:
    type: integer
    values: [{int(full_params["horario_inicio"])}]
  minuto_inicio:
    type: integer
    values: [{int(full_params["minuto_inicio"])}]
  horario_fim:
    type: integer
    values: [{int(full_params["horario_fim"])}]
  minuto_fim:
    type: integer
    values: [{int(full_params["minuto_fim"])}]
  horario_fechamento:
    type: integer
    values: [{int(full_params["horario_fechamento"])}]
  minuto_fechamento:
    type: integer
    values: [{int(full_params["minuto_fechamento"])}]
  sl_atr_mult:
    type: float
    values: [{full_params["sl_atr_mult"]:.1f}]
  tp_atr_mult:
    type: float
    values: [{full_params["tp_atr_mult"]:.1f}]
  usar_trailing:
    type: boolean
    values: [{str(full_params["usar_trailing"]).lower()}]
'''

with open('strategies/barra_elefante/config_validation.yaml', 'w', encoding='utf-8') as f:
    f.write(yaml_content)

print("   YAML criado: strategies/barra_elefante/config_validation.yaml")

# ============================================================================
# PASSO 5: EXECUTAR RUST BACKTEST
# ============================================================================
print("\n[5/6] EXECUTAR RUST BACKTEST...")
print("   AVISO: Execute o comando abaixo:")
print()
print("   cd engines\\rust")
print("   .\\target\\release\\optimize_dynamic.exe \\")
print("     --config ..\\..\\strategies\\barra_elefante\\config_validation.yaml \\")
print("     --data ..\\..\\data\\golden\\WINFUT_M5_2025-10-15.parquet \\")
print("     --output ..\\..\\results\\validation\\rust_trades_20251015.csv \\")
print("     --tests 1 \\")
print("     --cores 1")
print()

# ============================================================================
# PASSO 6: COMPARACAO
# ============================================================================
print("\n[6/6] COMPARACAO TRADE-BY-TRADE...")
print("   Aguardando resultado Rust...")
print("   Depois execute: python pipeline/comparar_engines.py")

print("\n" + "=" * 80)
print("PYTHON BACKTEST: COMPLETO")
print("=" * 80)
print(f"\nTotal Python Trades: {len(trades_python)}")
print(f"Total PnL: {result['total_return']:.2f} pts")
print(f"Win Rate: {result['win_rate']*100:.1f}%")
print(f"Sharpe: {result['sharpe_ratio']:.2f}")
print("\nProximos passos:")
print("1. Executar Rust backtest (comando acima)")
print("2. Comparar resultados trade-by-trade")
print("=" * 80)

