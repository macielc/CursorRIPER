"""
Compara resultados Python vs Rust - Verificação de Identidade
Garante que ambos motores produzem resultados idênticos
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def load_result_file(file_path: str) -> Optional[Dict]:
    """Carrega arquivo de resultado JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.FAIL}Erro ao carregar {file_path}: {e}{Colors.ENDC}")
        return None


def comparar_metricas(python_data: Dict, rust_data: Dict) -> Dict:
    """Compara métricas principais entre Python e Rust"""
    
    metricas_python = python_data.get('best_result', {}).get('metrics', {})
    metricas_rust = rust_data.get('best_result', {}).get('metrics', {})
    
    comparacao = {
        'total_trades': {
            'python': metricas_python.get('total_trades', 0),
            'rust': metricas_rust.get('total_trades', 0),
            'identico': False,
            'diff': 0,
            'diff_pct': 0.0
        },
        'win_rate': {
            'python': metricas_python.get('win_rate', 0.0),
            'rust': metricas_rust.get('win_rate', 0.0),
            'identico': False,
            'diff': 0.0,
            'diff_pct': 0.0
        },
        'sharpe_ratio': {
            'python': metricas_python.get('sharpe_ratio', 0.0),
            'rust': metricas_rust.get('sharpe_ratio', 0.0),
            'identico': False,
            'diff': 0.0,
            'diff_pct': 0.0
        },
        'profit_factor': {
            'python': metricas_python.get('profit_factor', 0.0),
            'rust': metricas_rust.get('profit_factor', 0.0),
            'identico': False,
            'diff': 0.0,
            'diff_pct': 0.0
        },
        'max_drawdown': {
            'python': metricas_python.get('max_drawdown', 0.0),
            'rust': metricas_rust.get('max_drawdown', 0.0),
            'identico': False,
            'diff': 0.0,
            'diff_pct': 0.0
        },
        'total_return': {
            'python': metricas_python.get('total_return', 0.0),
            'rust': metricas_rust.get('total_return', 0.0),
            'identico': False,
            'diff': 0.0,
            'diff_pct': 0.0
        }
    }
    
    # Calcular diferenças
    for metrica, valores in comparacao.items():
        py_val = valores['python']
        rust_val = valores['rust']
        
        if metrica == 'total_trades':
            # Inteiros: deve ser exatamente igual
            valores['identico'] = (py_val == rust_val)
            valores['diff'] = abs(py_val - rust_val)
            if py_val > 0:
                valores['diff_pct'] = (valores['diff'] / py_val) * 100
        else:
            # Floats: considerar tolerância de 0.001% (0.00001)
            tolerancia = 0.00001
            valores['diff'] = abs(py_val - rust_val)
            valores['identico'] = (valores['diff'] < tolerancia)
            if py_val != 0:
                valores['diff_pct'] = (valores['diff'] / abs(py_val)) * 100
    
    return comparacao


def comparar_trades(python_data: Dict, rust_data: Dict) -> Dict:
    """Compara trades individuais (se disponíveis)"""
    
    trades_python = python_data.get('best_result', {}).get('trades', [])
    trades_rust = rust_data.get('best_result', {}).get('trades', [])
    
    resultado = {
        'total_python': len(trades_python),
        'total_rust': len(trades_rust),
        'matches': 0,
        'discrepancias': []
    }
    
    if not trades_python or not trades_rust:
        resultado['disponivel'] = False
        return resultado
    
    resultado['disponivel'] = True
    
    # Comparar trade por trade
    max_len = min(len(trades_python), len(trades_rust))
    
    for i in range(max_len):
        trade_py = trades_python[i]
        trade_rust = trades_rust[i]
        
        # Comparar entry_time
        if trade_py.get('entry_time') == trade_rust.get('entry_time'):
            resultado['matches'] += 1
        else:
            resultado['discrepancias'].append({
                'index': i,
                'python': trade_py.get('entry_time'),
                'rust': trade_rust.get('entry_time'),
                'tipo': 'entry_time'
            })
    
    return resultado


def print_relatorio(comparacao: Dict, trades_comp: Dict, python_file: str, rust_file: str):
    """Imprime relatório de comparação"""
    
    print("\n" + "="*80)
    print(f"{Colors.HEADER}{Colors.BOLD}COMPARAÇÃO PYTHON vs RUST - Verificação de Identidade{Colors.ENDC}")
    print("="*80 + "\n")
    
    print(f"{Colors.BOLD}Arquivos Comparados:{Colors.ENDC}")
    print(f"  Python: {python_file}")
    print(f"  Rust  : {rust_file}")
    print()
    
    # Métricas principais
    print(f"{Colors.BOLD}MÉTRICAS PRINCIPAIS{Colors.ENDC}")
    print("-" * 80)
    
    identidade_perfeita = True
    
    for metrica, valores in comparacao.items():
        py_val = valores['python']
        rust_val = valores['rust']
        identico = valores['identico']
        diff = valores['diff']
        diff_pct = valores['diff_pct']
        
        # Status
        if identico:
            status = f"{Colors.OKGREEN}✓ IDÊNTICO{Colors.ENDC}"
        else:
            status = f"{Colors.FAIL}✗ DIFERENTE{Colors.ENDC}"
            identidade_perfeita = False
        
        # Nome formatado
        nome_metrica = metrica.replace('_', ' ').title()
        
        print(f"\n{Colors.BOLD}{nome_metrica}:{Colors.ENDC}")
        print(f"  Python: {py_val}")
        print(f"  Rust  : {rust_val}")
        print(f"  Diff  : {diff} ({diff_pct:.4f}%)")
        print(f"  Status: {status}")
    
    # Comparação de trades
    print("\n" + "-" * 80)
    print(f"{Colors.BOLD}TRADES INDIVIDUAIS{Colors.ENDC}")
    print("-" * 80)
    
    if not trades_comp.get('disponivel', False):
        print(f"{Colors.WARNING}Trade-by-trade não disponível nos arquivos{Colors.ENDC}")
    else:
        total_py = trades_comp['total_python']
        total_rust = trades_comp['total_rust']
        matches = trades_comp['matches']
        discrepancias = trades_comp['discrepancias']
        
        print(f"Total Trades Python: {total_py}")
        print(f"Total Trades Rust  : {total_rust}")
        print(f"Trades Coincidentes: {matches}")
        print(f"Discrepâncias      : {len(discrepancias)}")
        
        if discrepancias:
            print(f"\n{Colors.WARNING}Primeiras discrepâncias encontradas:{Colors.ENDC}")
            for disc in discrepancias[:5]:  # Mostrar apenas 5 primeiras
                print(f"  Trade #{disc['index']}: Python={disc['python']} | Rust={disc['rust']}")
            if len(discrepancias) > 5:
                print(f"  ... e mais {len(discrepancias) - 5} discrepâncias")
    
    # Decisão Final
    print("\n" + "="*80)
    print(f"{Colors.BOLD}DECISÃO FINAL{Colors.ENDC}")
    print("="*80 + "\n")
    
    if identidade_perfeita:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ IDENTIDADE 100% VERIFICADA{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Python e Rust produzem resultados IDÊNTICOS!{Colors.ENDC}")
        print(f"{Colors.OKGREEN}Pode confiar no motor Rust para produção.{Colors.ENDC}")
    else:
        print(f"{Colors.FAIL}{Colors.BOLD}✗ IDENTIDADE NÃO VERIFICADA{Colors.ENDC}")
        print(f"{Colors.FAIL}Existem diferenças entre Python e Rust!{Colors.ENDC}")
        print(f"{Colors.WARNING}AÇÃO NECESSÁRIA: Debugar discrepâncias antes de usar Rust.{Colors.ENDC}")
    
    print()


def main():
    """Executa comparação Python vs Rust"""
    
    if len(sys.argv) < 3:
        print(f"{Colors.BOLD}Uso:{Colors.ENDC}")
        print(f"  python comparar_python_rust.py <resultado_python.json> <resultado_rust.json>")
        print()
        print(f"{Colors.BOLD}Exemplo:{Colors.ENDC}")
        print(f"  python comparar_python_rust.py results/python/best_barra_elefante.json results/rust/best_barra_elefante.json")
        sys.exit(1)
    
    python_file = sys.argv[1]
    rust_file = sys.argv[2]
    
    # Verificar se arquivos existem
    if not Path(python_file).exists():
        print(f"{Colors.FAIL}Erro: Arquivo Python não encontrado: {python_file}{Colors.ENDC}")
        sys.exit(1)
    
    if not Path(rust_file).exists():
        print(f"{Colors.FAIL}Erro: Arquivo Rust não encontrado: {rust_file}{Colors.ENDC}")
        sys.exit(1)
    
    # Carregar dados
    print(f"\n{Colors.OKCYAN}Carregando resultados...{Colors.ENDC}")
    python_data = load_result_file(python_file)
    rust_data = load_result_file(rust_file)
    
    if not python_data or not rust_data:
        sys.exit(1)
    
    # Comparar métricas
    comparacao = comparar_metricas(python_data, rust_data)
    
    # Comparar trades
    trades_comp = comparar_trades(python_data, rust_data)
    
    # Imprimir relatório
    print_relatorio(comparacao, trades_comp, python_file, rust_file)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrompido pelo usuário{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.FAIL}Erro inesperado: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

