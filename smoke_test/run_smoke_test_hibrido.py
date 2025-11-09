"""
SISTEMA DE SMOKE TEST H BRIDO
==============================
FASE 1A: Grid Coarse (41k combos) - Identificar regi es
FASE 1B: Refinamento (500k combos) - Valores intermedi rios

Autor: MacTester
Data: 2025
"""

import subprocess
import pandas as pd
import numpy as np
import yaml
import json
from pathlib import Path
from datetime import datetime
from itertools import product
import time

# =====================================================
# CONFIGURA O
# =====================================================

DATA_FILE = Path("data/golden/WINFUT_M5_Golden_Data.parquet")
RUST_BIN = Path("engines/rust/target/release/optimize_dynamic.exe")
OUTPUT_DIR = Path("results/smoke_test")

# =====================================================
# FASE 1A: SMOKE TEST COARSE
# =====================================================

def run_fase1a():
    """
    Executa smoke test com grid espa ado
    """
    print("=" * 80)
    print("FASE 1A: SMOKE TEST COARSE")
    print("=" * 80)
    
    # Criar config YAML tempor rio
    config = {
        'strategy': {
            'name': 'barra_elefante',
            'description': 'Smoke Test COARSE - Grid espacado',
            'version': '1.0'
        },
        'param_grid': {
            'min_amplitude_mult': {'type': 'float', 'values': [1.0, 2.0, 3.0, 4.0]},
            'min_volume_mult': {'type': 'float', 'values': [0.0, 1.5, 3.0]},
            'max_sombra_pct': {'type': 'float', 'values': [0.0, 0.25, 0.50, 1.0]},
            'lookback_amplitude': {'type': 'integer', 'values': [5, 15, 30]},
            'horario_inicio': {'type': 'integer', 'values': [9, 10]},
            'minuto_inicio': {'type': 'integer', 'values': [0]},
            'horario_fim': {'type': 'integer', 'values': [12, 14]},
            'minuto_fim': {'type': 'integer', 'values': [0]},
            'horario_fechamento': {'type': 'integer', 'values': [14, 15]},
            'minuto_fechamento': {'type': 'integer', 'values': [0]},
            'sl_atr_mult': {'type': 'float', 'values': [1.0, 2.0, 3.0]},
            'tp_atr_mult': {'type': 'float', 'values': [2.0, 3.0, 5.0]},
            'usar_trailing': {'type': 'boolean', 'values': [False, True]},
        },
        'execution': {
            'max_tests': 0,
            'randomize': False
        }
    }
    
    # Salvar config
    config_file = OUTPUT_DIR / "fase1a_config.yaml"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    # Calcular total de combina es
    total_combos = 1
    for param, vals in config['param_grid'].items():
        total_combos *= len(vals['values'])
    
    print(f"\n  Configura o:")
    print(f"   Total de combina es: {total_combos:,}")
    print(f"   Cores: 24")
    print(f"   Dataset: {DATA_FILE}")
    
    # Executar Rust
    output_csv = OUTPUT_DIR / f"fase1a_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    cmd = [
        str(RUST_BIN),
        "--config", str(config_file),
        "--data", str(DATA_FILE),
        "--output", str(output_csv),
        "--tests", str(total_combos),
        "--cores", "24"
    ]
    
    print(f"\n  Executando Rust...")
    print(f"   Comando: {' '.join(cmd)}")
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"\n  ERRO na execu o:")
        print(result.stderr)
        return None
    
    print(f"\n  FASE 1A Conclu da em {elapsed/60:.1f} minutos")
    print(f"   Resultados salvos em: {output_csv}")
    
    # Carregar resultados
    df = pd.read_csv(output_csv)
    print(f"\n  Estat sticas:")
    print(f"   Combos testados: {len(df):,}")
    print(f"   PnL m dio: {df['total_return'].mean():.2f}")
    print(f"   PnL m ximo: {df['total_return'].max():.2f}")
    print(f"   Sharpe m ximo: {df['sharpe_ratio'].max():.2f}")
    
    return df, output_csv


# =====================================================
# AN LISE DE REGI ES PROMISSORAS
# =====================================================

def analyze_top_regions(df: pd.DataFrame, top_n: int = 100):
    """
    Analisa os top N setups para identificar regi es de par metros
    """
    print("\n" + "=" * 80)
    print(f"AN LISE DAS {top_n} MELHORES REGI ES")
    print("=" * 80)
    
    # Ranquear por Sharpe (prim rio) e PnL (secund rio)
    df_sorted = df.sort_values(['sharpe_ratio', 'total_return'], ascending=False)
    top_setups = df_sorted.head(top_n)
    
    print(f"\n  Top {top_n} Setups:")
    print(f"   PnL Range: {top_setups['total_return'].min():.2f} - {top_setups['total_return'].max():.2f}")
    print(f"   Sharpe Range: {top_setups['sharpe_ratio'].min():.2f} - {top_setups['sharpe_ratio'].max():.2f}")
    
    # Identificar valores mais comuns nos top setups
    param_cols = [col for col in df.columns if col not in ['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'trades']]
    
    regions = {}
    for param in param_cols:
        if param in top_setups.columns:
            # Valores  nicos nos top setups
            unique_vals = sorted(top_setups[param].unique())
            
            # Se tem apenas 1 valor, n o precisa refinar
            if len(unique_vals) <= 1:
                regions[param] = unique_vals
            else:
                # Calcular range min/max
                min_val = top_setups[param].min()
                max_val = top_setups[param].max()
                regions[param] = {'min': min_val, 'max': max_val, 'unique': unique_vals}
            
            print(f"\n   {param}:")
            print(f"      Valores  nicos: {unique_vals}")
            if len(unique_vals) > 1:
                print(f"      Range: {min_val} - {max_val}")
    
    return regions, top_setups


# =====================================================
# FASE 1B: REFINAMENTO
# =====================================================

def generate_refined_grid(regions: dict, original_config: dict):
    """
    Gera grid refinado baseado nas regi es promissoras
    """
    print("\n" + "=" * 80)
    print("FASE 1B: GERANDO GRID REFINADO")
    print("=" * 80)
    
    refined_config = {
        'strategy': {
            'name': 'barra_elefante',
            'description': 'Smoke Test REFINADO - Valores intermediarios',
            'version': '1.0'
        },
        'param_grid': {},
        'execution': {
            'max_tests': 0,
            'randomize': False
        }
    }
    
    for param, region_data in regions.items():
        if isinstance(region_data, dict) and 'min' in region_data:
            # Par metro num rico - criar valores intermedi rios
            min_val = region_data['min']
            max_val = region_data['max']
            unique_vals = region_data['unique']
            
            # Adicionar valores intermedi rios
            new_vals = set(unique_vals)
            
            for i in range(len(unique_vals) - 1):
                v1 = unique_vals[i]
                v2 = unique_vals[i + 1]
                
                # Adicionar 1-2 valores intermedi rios
                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    diff = v2 - v1
                    if diff > 0.2:  # Se diferen a significativa
                        if isinstance(v1, int):
                            # Inteiro
                            for mid in range(int(v1) + 1, int(v2)):
                                new_vals.add(mid)
                        else:
                            # Float
                            mid = (v1 + v2) / 2
                            new_vals.add(round(mid, 2))
            
            # Determinar tipo
            param_type = 'integer' if all(isinstance(v, int) for v in new_vals) else 'float'
            refined_config['param_grid'][param] = {'type': param_type, 'values': sorted(list(new_vals))}
            print(f"\n   {param}: {len(new_vals)} valores")
            print(f"      {sorted(list(new_vals))}")
        
        else:
            # Par metro categ rico ou com 1 valor - manter
            # Determinar tipo
            if isinstance(list(region_data)[0], bool):
                param_type = 'boolean'
            elif isinstance(list(region_data)[0], int):
                param_type = 'integer'
            elif isinstance(list(region_data)[0], float):
                param_type = 'float'
            else:
                param_type = 'string'
            
            refined_config['param_grid'][param] = {'type': param_type, 'values': list(region_data)}
            print(f"\n   {param}: {region_data} (fixo)")
    
    # Calcular total de combina es
    total_refined = 1
    for param, vals in refined_config['param_grid'].items():
        total_refined *= len(vals['values'])
    
    print(f"\n  Total de combina es refinadas: {total_refined:,}")
    
    return refined_config, total_refined


def run_fase1b(refined_config: dict):
    """
    Executa smoke test com grid refinado
    """
    print("\n" + "=" * 80)
    print("FASE 1B: SMOKE TEST REFINADO")
    print("=" * 80)
    
    # Salvar config refinado
    config_file = OUTPUT_DIR / "fase1b_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(refined_config, f)
    
    # Calcular total
    total_combos = 1
    for param, vals in refined_config['param_grid'].items():
        total_combos *= len(vals['values'])
    
    print(f"\n  Configura o:")
    print(f"   Total de combina es: {total_combos:,}")
    print(f"   Cores: 24")
    
    # Executar Rust
    output_csv = OUTPUT_DIR / f"fase1b_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    cmd = [
        str(RUST_BIN),
        "--config", str(config_file),
        "--data", str(DATA_FILE),
        "--output", str(output_csv),
        "--tests", str(total_combos),
        "--cores", "24"
    ]
    
    print(f"\n  Executando Rust...")
    
    start = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"\n  ERRO na execu o:")
        print(result.stderr)
        return None
    
    print(f"\n  FASE 1B Conclu da em {elapsed/60:.1f} minutos")
    print(f"   Resultados salvos em: {output_csv}")
    
    # Carregar resultados
    df = pd.read_csv(output_csv)
    print(f"\n  Estat sticas:")
    print(f"   Combos testados: {len(df):,}")
    print(f"   PnL m dio: {df['total_return'].mean():.2f}")
    print(f"   PnL m ximo: {df['total_return'].max():.2f}")
    print(f"   Sharpe m ximo: {df['sharpe_ratio'].max():.2f}")
    
    return df, output_csv


# =====================================================
# CONSOLIDA O FINAL
# =====================================================

def consolidate_results(df_1a: pd.DataFrame, df_1b: pd.DataFrame):
    """
    Consolida resultados de FASE 1A e 1B
    """
    print("\n" + "=" * 80)
    print("CONSOLIDA O FINAL")
    print("=" * 80)
    
    # Combinar ambos os DataFrames
    df_combined = pd.concat([df_1a, df_1b], ignore_index=True)
    
    # Remover duplicatas (mesmos par metros)
    param_cols = [col for col in df_combined.columns if col not in ['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'trades']]
    df_combined = df_combined.drop_duplicates(subset=param_cols, keep='first')
    
    # Ordenar por Sharpe + PnL
    df_combined = df_combined.sort_values(['sharpe_ratio', 'total_return'], ascending=False)
    
    # Salvar consolidado
    output_file = OUTPUT_DIR / f"smoke_test_consolidated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_combined.to_csv(output_file, index=False)
    
    print(f"\n  Estat sticas Finais:")
    print(f"   Total de setups  nicos: {len(df_combined):,}")
    print(f"   PnL m ximo: {df_combined['total_return'].max():.2f}")
    print(f"   Sharpe m ximo: {df_combined['sharpe_ratio'].max():.2f}")
    print(f"\n  Resultados salvos em: {output_file}")
    
    # Mostrar Top 10
    print(f"\n  TOP 10 SETUPS:")
    print(df_combined.head(10)[['total_return', 'sharpe_ratio', 'max_drawdown_pct', 'win_rate', 'trades']].to_string())
    
    return df_combined, output_file


# =====================================================
# MAIN
# =====================================================

def main():
    print("=" * 80)
    print(" " * 20 + "SMOKE TEST HIBRIDO - BARRA ELEFANTE")
    print("=" * 80)
    
    # Verificar arquivos
    if not DATA_FILE.exists():
        print(f"[ERRO] Dataset nao encontrado: {DATA_FILE}")
        return
    
    if not RUST_BIN.exists():
        print(f"[ERRO] Binario Rust nao encontrado: {RUST_BIN}")
        print("   Execute: cd engines/rust && cargo build --release --bin optimize_dynamic")
        return
    
    start_total = time.time()
    
    # FASE 1A: Coarse
    df_1a, csv_1a = run_fase1a()
    if df_1a is None:
        return
    
    # An lise das regi es
    regions, top_setups = analyze_top_regions(df_1a, top_n=100)
    
    # FASE 1B: Refinamento
    original_config = {}  # N o usado
    refined_config, total_refined = generate_refined_grid(regions, original_config)
    
    # Perguntar ao usu rio se quer prosseguir
    print(f"\n   FASE 1B ir  testar {total_refined:,} combina es")
    response = input("   Prosseguir? (s/n): ")
    
    if response.lower() != 's':
        print("\n   FASE 1B cancelada. Resultados da FASE 1A salvos.")
        return
    
    df_1b, csv_1b = run_fase1b(refined_config)
    if df_1b is None:
        return
    
    # Consolida o
    df_final, csv_final = consolidate_results(df_1a, df_1b)
    
    elapsed_total = time.time() - start_total
    
    print("\n" + "=" * 80)
    print("  SMOKE TEST H BRIDO CONCLU DO")
    print("=" * 80)
    print(f"   Tempo total: {elapsed_total/60:.1f} minutos")
    print(f"   Setups  nicos: {len(df_final):,}")
    print(f"   Melhor PnL: {df_final['total_return'].max():.2f}")
    print(f"   Melhor Sharpe: {df_final['sharpe_ratio'].max():.2f}")
    print(f"\n  Arquivos gerados:")
    print(f"   - {csv_1a}")
    print(f"   - {csv_1b}")
    print(f"   - {csv_final}")


if __name__ == "__main__":
    main()

