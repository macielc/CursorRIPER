#!/usr/bin/env python3
"""
MacTester - Sistema de Backtesting e Otimização de Estratégias
"""
import argparse
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Root do projeto

from core.optimizer import MassiveOptimizer
from core.data_loader import DataLoader


def optimize_command(args):
    """Executa otimização massiva de uma estratégia"""
    print(f"""
================================================================================
FASE 2: OTIMIZACAO MASSIVA (~{args.tests:,} TESTES)
================================================================================
""")
    
    # Carregar dados
    print("Carregando dados de mercado...")
    loader = DataLoader(timeframe=args.timeframe)
    
    # Verificar se há filtros de data
    start_date = getattr(args, 'start_date', None)
    end_date = getattr(args, 'end_date', None)
    
    if start_date or end_date:
        print(f"FILTRO DE DATA ATIVO:")
        if start_date:
            print(f"  Data inicial: {start_date}")
        if end_date:
            print(f"  Data final: {end_date}")
        print()
    
    df = loader.load(start_date=start_date, end_date=end_date)
    
    # Criar otimizador
    optimizer = MassiveOptimizer(
        data=df,
        strategy=args.strategy,
        n_cores=args.cores if hasattr(args, 'cores') else None
    )
    
    # Obter param_grid da estratégia
    param_grid = optimizer.strategy_class.get_param_grid(n_tests=args.tests)
    
    # Executar otimização (resume=False = SEMPRE limpa checkpoints antes)
    results = optimizer.optimize(
        param_grid=param_grid,
        max_tests=args.tests,
        resume=False  # SEMPRE começa do zero, limpando checkpoints antigos
    )
    
    
    if results is not None and len(results) > 0:
        print(f"\n[OK] Otimizacao massiva concluida!")
        print(f"    Top {len(results)} setups salvos\n")
        return 0
    else:
        print(f"\n[ERRO] Otimizacao falhou ou nenhum resultado valido!")
        return 1


def main():
    """Função principal do CLI"""
    parser = argparse.ArgumentParser(
        description='MacTester - Sistema de Backtesting e Otimização',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')
    
    # Comando: optimize
    optimize_parser = subparsers.add_parser('optimize', help='Otimização massiva de estratégia')
    optimize_parser.add_argument('--strategy', required=True, help='Nome da estratégia')
    optimize_parser.add_argument('--tests', type=int, default=1000, help='Número de testes (default: 1000)')
    optimize_parser.add_argument('--timeframe', default='5m', help='Timeframe (default: 5m)')
    optimize_parser.add_argument('--cores', type=int, help='Número de cores (default: auto)')
    optimize_parser.add_argument('--start-date', dest='start_date', help='Data inicial (YYYY-MM-DD)')
    optimize_parser.add_argument('--end-date', dest='end_date', help='Data final (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Executar comando
    if args.command == 'optimize':
        return optimize_command(args)
    else:
        print(f"Comando desconhecido: {args.command}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

