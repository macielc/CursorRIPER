"""
MacTester - Pipeline Automatizado
Executa todas as fases (2-6) sequencialmente com visibilidade completa
"""
import subprocess
import sys
import json
import time
import os
import platform
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Detectar se eh Windows e se o terminal suporta ANSI
def _suporta_cores():
    """Detecta se o terminal suporta cores ANSI"""
    # Se FORCE_COLOR estiver definido, sempre usar cores
    if os.environ.get('FORCE_COLOR'):
        return True
    
    # Se NO_COLOR estiver definido, nunca usar cores
    if os.environ.get('NO_COLOR'):
        return False
    
    # Windows: tentar habilitar ANSI
    if platform.system() == 'Windows':
        try:
            # Tentar habilitar modo ANSI no Windows 10+
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            return True
        except:
            # Se falhar, desabilitar cores
            return False
    
    # Unix/Linux: geralmente suportam
    return True

# Cores para terminal (habilitadas apenas se suportado)
_CORES_HABILITADAS = _suporta_cores()

class Colors:
    if _CORES_HABILITADAS:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
    else:
        # Sem cores
        HEADER = ''
        OKBLUE = ''
        OKCYAN = ''
        OKGREEN = ''
        WARNING = ''
        FAIL = ''
        ENDC = ''
        BOLD = ''
        UNDERLINE = ''

def print_header(text: str):
    """Imprime cabeçalho destacado"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_phase(phase_num: int, phase_name: str):
    """Imprime título da fase"""
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}[FASE {phase_num}] {phase_name}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*80}{Colors.ENDC}")

def print_success(text: str):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.OKGREEN}[OK] {text}{Colors.ENDC}")

def print_error(text: str):
    """Imprime mensagem de erro"""
    print(f"{Colors.FAIL}[ERRO] {text}{Colors.ENDC}")

def print_warning(text: str):
    """Imprime mensagem de aviso"""
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")

def run_command(cmd: str) -> tuple[int, str]:
    """Executa comando e retorna código de saída e saída completa"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        output = result.stdout + result.stderr
        # Remove caracteres problemáticos para Windows
        output = output.encode('ascii', 'replace').decode('ascii')
        return result.returncode, output
    except Exception as e:
        return 1, str(e)

def get_latest_result_file(pattern: str) -> Optional[Path]:
    """Busca o arquivo de resultado mais recente"""
    results_dir = Path('results')
    if not results_dir.exists():
        return None
    
    files = list(results_dir.glob(pattern))
    if not files:
        return None
    
    return max(files, key=lambda f: f.stat().st_mtime)

def list_strategies() -> List[str]:
    """Lista todas as estratégias disponíveis"""
    strategies_dir = Path('strategies')
    if not strategies_dir.exists():
        return []
    
    strategies = []
    for item in strategies_dir.iterdir():
        if item.is_dir() and (item / 'strategy.py').exists():
            strategies.append(item.name)
    
    return sorted(strategies)

def run_phase2(strategy: str, n_tests: int, timeframe: str = '5m') -> bool:
    """Executa Fase 2: Otimização (LEGADO - mantido para compatibilidade)"""
    return run_phase2_python(strategy, n_tests, timeframe, None, None)

def run_phase2_python(strategy: str, n_tests: int, timeframe: str = '5m',
                      periodo_start: Optional[str] = None, periodo_end: Optional[str] = None) -> bool:
    """Executa Fase 2: Otimização com Python"""
    print_phase(2, f"OTIMIZACAO (PYTHON) - {strategy}")
    
    # Comando base
    cmd = f'python mactester.py optimize --strategy {strategy} --tests {n_tests} --timeframe {timeframe}'
    
    # Adicionar período se especificado
    if periodo_start and periodo_end:
        cmd += f' --period "{periodo_start}" "{periodo_end}"'
    
    print(f"Comando: {cmd}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    if returncode == 0:
        print_success(f"Fase 2 (Python) concluida em {elapsed:.1f}s")
        return True
    else:
        print_error(f"Fase 2 (Python) FALHOU (exit code: {returncode})")
        return False

def run_phase2_rust(strategy: str, n_tests: int, timeframe: str = '5m',
                    periodo_start: Optional[str] = None, periodo_end: Optional[str] = None) -> bool:
    """Executa Fase 2: Otimização com Rust"""
    print_phase(2, f"OTIMIZACAO (RUST) - {strategy}")
    
    # Localizar executável Rust
    rust_exe = Path('engines/rust/optimize_batches.exe')
    if not rust_exe.exists():
        rust_exe = Path('../engines/rust/optimize_batches.exe')
    
    if not rust_exe.exists():
        print_error("Executável Rust não encontrado!")
        print_error("Caminho esperado: engines/rust/optimize_batches.exe")
        return False
    
    # Comando Rust
    cmd = f'{rust_exe.absolute()}'
    
    # Rust aceita parâmetros por argumentos ou env vars (verificar documentação)
    # Por enquanto, executa padrão
    print(f"Comando: {cmd}\n")
    if periodo_start and periodo_end:
        print(f"{Colors.WARNING}NOTA: Período específico para Rust ainda não implementado{Colors.ENDC}")
        print(f"{Colors.WARNING}Executando com dataset completo{Colors.ENDC}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    if returncode == 0:
        print_success(f"Fase 2 (Rust) concluida em {elapsed:.1f}s")
        return True
    else:
        print_error(f"Fase 2 (Rust) FALHOU (exit code: {returncode})")
        return False

def run_phase3(strategy: str) -> Dict:
    """Executa Fase 3: Walk-Forward Analysis"""
    print_phase(3, "WALK-FORWARD ANALYSIS")
    
    cmd = 'python fase3_walkforward.py'
    print(f"Comando: {cmd}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    result = {'aprovado': False, 'tempo': elapsed}
    
    # Tenta carregar o resultado
    result_file = get_latest_result_file(f'fase3_walkforward_{strategy}_*.json')
    if result_file and result_file.exists():
        with open(result_file, 'r') as f:
            result.update(json.load(f))
    
    if returncode == 0:
        print_success(f"Fase 3 concluida em {elapsed:.1f}s")
    else:
        print_error(f"Fase 3 FALHOU (exit code: {returncode})")
    
    return result

def run_phase4(strategy: str) -> Dict:
    """Executa Fase 4: Out-of-Sample Test"""
    print_phase(4, "OUT-OF-SAMPLE TEST")
    
    cmd = 'python fase4_out_of_sample.py'
    print(f"Comando: {cmd}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    result = {'aprovado': False, 'tempo': elapsed}
    
    # Tenta carregar o resultado
    result_file = get_latest_result_file(f'fase4_oos_{strategy}_*.json')
    if result_file and result_file.exists():
        with open(result_file, 'r') as f:
            result.update(json.load(f))
    
    if returncode == 0:
        print_success(f"Fase 4 concluida em {elapsed:.1f}s")
    else:
        print_error(f"Fase 4 FALHOU (exit code: {returncode})")
    
    return result

def run_phase5(strategy: str) -> Dict:
    """Executa Fase 5: Outlier Analysis"""
    print_phase(5, "OUTLIER ANALYSIS")
    
    cmd = 'python fase5_outlier_analysis.py'
    print(f"Comando: {cmd}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    result = {'aprovado': False, 'tempo': elapsed}
    
    # Tenta carregar o resultado
    result_file = get_latest_result_file(f'fase5_outliers_{strategy}_*.json')
    if result_file and result_file.exists():
        with open(result_file, 'r') as f:
            result.update(json.load(f))
    
    if returncode == 0:
        print_success(f"Fase 5 concluida em {elapsed:.1f}s")
    else:
        print_error(f"Fase 5 FALHOU (exit code: {returncode})")
    
    return result

def run_phase6(strategy: str) -> Dict:
    """Executa Fase 6: Relatório Final"""
    print_phase(6, "RELATORIO FINAL")
    
    cmd = 'python fase6_relatorio_final.py'
    print(f"Comando: {cmd}\n")
    
    start = time.time()
    returncode, output = run_command(cmd)
    elapsed = time.time() - start
    
    print(output)
    
    result = {'decisao': 'DESCONHECIDO', 'tempo': elapsed}
    
    # Tenta carregar o resultado
    result_file = get_latest_result_file(f'RELATORIO_FINAL_{strategy}_*.json')
    if result_file and result_file.exists():
        with open(result_file, 'r') as f:
            result.update(json.load(f))
    
    if returncode == 0:
        print_success(f"Fase 6 concluida em {elapsed:.1f}s")
    else:
        print_error(f"Fase 6 FALHOU (exit code: {returncode})")
    
    return result

def run_full_pipeline(strategy: str, n_tests: int, timeframe: str = '5m', 
                      motor: str = 'python', periodo_start: Optional[str] = None, 
                      periodo_end: Optional[str] = None, modo_validacao: str = 'completo',
                      top_n: int = 1) -> Dict:
    """Executa pipeline completo para uma estratégia"""
    print_header(f"PIPELINE: {strategy.upper()} ({motor.upper()})")
    print(f"Testes: {n_tests} | Timeframe: {timeframe} | Modo: {modo_validacao.upper()}")
    if periodo_start and periodo_end:
        print(f"Período: {periodo_start} até {periodo_end}")
    
    pipeline_start = time.time()
    
    results = {
        'strategy': strategy,
        'motor': motor,
        'n_tests': n_tests,
        'timeframe': timeframe,
        'periodo_start': periodo_start,
        'periodo_end': periodo_end,
        'modo_validacao': modo_validacao,
        'top_n': top_n,
        'start_time': datetime.now().isoformat(),
        'phases': {}
    }
    
    # FASE 2: Otimização (Backtest)
    if motor == 'python':
        # Python: mactester.py
        if not run_phase2_python(strategy, n_tests, timeframe, periodo_start, periodo_end):
            print_error("Pipeline ABORTADO na Fase 2 (Python)")
            results['status'] = 'ERRO_FASE_2'
            return results
    else:
        # Rust: executável
        if not run_phase2_rust(strategy, n_tests, timeframe, periodo_start, periodo_end):
            print_error("Pipeline ABORTADO na Fase 2 (Rust)")
            results['status'] = 'ERRO_FASE_2'
            return results
    
    # Validações conforme modo escolhido
    if modo_validacao == 'essencial':
        # Modo ESSENCIAL: 3 fases críticas
        print(f"\n{Colors.WARNING}Modo ESSENCIAL: Executando apenas fases críticas{Colors.ENDC}")
        
        # FASE 3: Walk-Forward (crítico para detectar overfitting)
        results['phases']['fase3'] = run_phase3(strategy)
        
        # FASE 4: Out-of-Sample (crítico para validação em período não visto)
        results['phases']['fase4'] = run_phase4(strategy)
        
        # Relatório simplificado
        results['phases']['fase6'] = {'decisao': 'ESSENCIAL_CONCLUIDO'}
        
    else:
        # Modo COMPLETO: Todas as 6 fases
        # FASE 3: Walk-Forward
        results['phases']['fase3'] = run_phase3(strategy)
        
        # FASE 4: Out-of-Sample
        results['phases']['fase4'] = run_phase4(strategy)
        
        # FASE 5: Outlier Analysis
        results['phases']['fase5'] = run_phase5(strategy)
        
        # FASE 6: Relatório Final
        results['phases']['fase6'] = run_phase6(strategy)
    
    # Resumo final
    total_time = time.time() - pipeline_start
    results['total_time'] = total_time
    results['end_time'] = datetime.now().isoformat()
    
    print_header("RESUMO DO PIPELINE")
    print(f"Estrategia: {Colors.BOLD}{strategy}{Colors.ENDC}")
    print(f"Tempo total: {Colors.BOLD}{total_time:.1f}s{Colors.ENDC}")
    print(f"\nResultados por fase:")
    
    for phase_name, phase_result in results['phases'].items():
        if phase_name == 'fase6':
            # Priorizar decisao_final sobre decisao
            decisao = phase_result.get('decisao_final', phase_result.get('decisao', 'DESCONHECIDO'))
            color = Colors.OKGREEN if decisao == 'APROVADO' else Colors.FAIL
            print(f"  {phase_name.upper()}: {color}{decisao}{Colors.ENDC}")
        else:
            # Tratar string "False"/"True" como booleano
            aprovado = phase_result.get('aprovado', False)
            if isinstance(aprovado, str):
                aprovado = aprovado.lower() == 'true'
            status = f"{Colors.OKGREEN}APROVADO{Colors.ENDC}" if aprovado else f"{Colors.FAIL}REJEITADO{Colors.ENDC}"
            print(f"  {phase_name.upper()}: {status}")
    
    # Decisão final
    decisao_final = results['phases']['fase6'].get('decisao_final', results['phases']['fase6'].get('decisao', 'DESCONHECIDO'))
    results['decisao_final'] = decisao_final
    
    if decisao_final == 'APROVADO':
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}ESTRATEGIA APROVADA!{Colors.ENDC}")
    elif decisao_final == 'REJEITADO':
        print(f"\n{Colors.FAIL}{Colors.BOLD}ESTRATEGIA REJEITADA{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}STATUS DESCONHECIDO{Colors.ENDC}")
    
    return results

def executar_refinamento(strategy: str, auto_default: bool = False):
    """Executa refinamento automatico de estrategia"""
    print(f"\n{Colors.WARNING}{'='*80}{Colors.ENDC}")
    print(f"{Colors.WARNING}{Colors.BOLD}REFINAMENTO AUTOMATICO DISPONIVEL{Colors.ENDC}")
    print(f"{Colors.WARNING}{'='*80}{Colors.ENDC}")
    print(f"\nA estrategia '{Colors.BOLD}{strategy}{Colors.ENDC}' foi REJEITADA.")
    print("Deseja tentar refinar automaticamente para melhorar os resultados?")
    print(f"\n{Colors.OKCYAN}[ENTER]{Colors.ENDC} - Sim, refinar agora")
    print(f"{Colors.WARNING}[n]{Colors.ENDC} - Nao, voltar ao menu")
    
    refinar = input(f"\n{Colors.OKCYAN}Refinar estrategia? [S/n]: {Colors.ENDC}").strip().lower()
    
    if refinar in ['n', 'nao', 'no']:
        print("Refinamento cancelado.")
        return False
    
    # Parametros do refinamento
    print(f"\n{Colors.BOLD}Configuracao do refinamento:{Colors.ENDC}")
    
    # Numero de iteracoes
    n_iter_input = input(f"{Colors.OKCYAN}Numero de iteracoes [3]: {Colors.ENDC}").strip()
    n_iteracoes = int(n_iter_input) if n_iter_input else 3
    
    # Numero de testes por iteracao
    n_tests_input = input(f"{Colors.OKCYAN}Numero de testes por iteracao [1000]: {Colors.ENDC}").strip()
    n_tests = int(n_tests_input) if n_tests_input else 1000
    
    # Modo automatico
    if auto_default:
        auto_mode = True
        print(f"{Colors.OKCYAN}Modo: AUTOMATICO (sem pausas){Colors.ENDC}")
    else:
        auto_input = input(f"{Colors.OKCYAN}Modo automatico (sem pausas)? [s/N]: {Colors.ENDC}").strip().lower()
        auto_mode = auto_input in ['s', 'sim', 'y', 'yes']
    
    # Tipo de parametros
    print(f"\n{Colors.BOLD}Tipo de parametros a modificar:{Colors.ENDC}")
    print("  [1] Apenas AJUSTAVEIS (SL, TP, volume, horario) - Padrao")
    print("  [2] Apenas IDENTIDADE (conceito core) - Ajuste fino")
    print("  [3] AMBOS (ajustaveis + identidade)")
    
    modo_input = input(f"{Colors.OKCYAN}Opcao [1]: {Colors.ENDC}").strip()
    
    if modo_input == '2':
        modo_params = 'identidade'
        modo_desc = 'IDENTIDADE'
    elif modo_input == '3':
        modo_params = 'ambos'
        modo_desc = 'AMBOS'
    else:
        modo_params = 'ajustaveis'
        modo_desc = 'AJUSTAVEIS'
    
    # Densidade
    print(f"\n{Colors.BOLD}Densidade (quantidade de valores):{Colors.ENDC}")
    print("  [1] MINIMA  [2] BAIXA  [3] MEDIA (padrao)  [4] ALTA  [5] MAXIMA")
    densidade_input = input(f"{Colors.OKCYAN}Opcao [3]: {Colors.ENDC}").strip()
    densidade = int(densidade_input) if densidade_input and densidade_input.isdigit() and 1 <= int(densidade_input) <= 5 else 3
    
    # Distanciamento
    print(f"\n{Colors.BOLD}Distanciamento (range de valores):{Colors.ENDC}")
    print("  [1] MINIMO  [2] BAIXO  [3] MEDIO (padrao)  [4] ALTO  [5] MAXIMO")
    distanciamento_input = input(f"{Colors.OKCYAN}Opcao [3]: {Colors.ENDC}").strip()
    distanciamento = int(distanciamento_input) if distanciamento_input and distanciamento_input.isdigit() and 1 <= int(distanciamento_input) <= 5 else 3
    
    # Confirmar
    print(f"\n{Colors.BOLD}Resumo:{Colors.ENDC}")
    print(f"  Estrategia: {strategy}")
    print(f"  Iteracoes: {n_iteracoes}")
    print(f"  Testes: {n_tests}")
    print(f"  Modo: {'AUTO' if auto_mode else 'INTERATIVO'}")
    print(f"  Parametros: {modo_desc}")
    print(f"  Densidade: {densidade}/5")
    print(f"  Distanciamento: {distanciamento}/5")
    
    confirmar = input(f"\n{Colors.OKCYAN}Confirmar refinamento? [S/n]: {Colors.ENDC}").strip().lower()
    if confirmar in ['n', 'nao', 'no']:
        print("Refinamento cancelado.")
        return False
    
    # Executar refinamento
    print_header(f"REFINAMENTO AUTOMATICO: {strategy.upper()}")
    
    cmd = f'python refinar_estrategia.py {strategy} --max-iteracoes {n_iteracoes} --n-tests {n_tests} --modo-params {modo_params} --densidade {densidade} --distanciamento {distanciamento}'
    if auto_mode:
        cmd += ' --auto'
    
    print(f"\n{Colors.OKCYAN}Executando: {cmd}{Colors.ENDC}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}Refinamento concluido com sucesso!{Colors.ENDC}")
            return True
        else:
            print(f"\n{Colors.WARNING}Refinamento finalizado (codigo: {result.returncode}){Colors.ENDC}")
            return False
    
    except Exception as e:
        print_error(f"Erro ao executar refinamento: {e}")
        return False

def main():
    # Informar sobre status de cores
    if not _CORES_HABILITADAS:
        print("NOTA: Cores desabilitadas (terminal nao suporta ANSI)")
        print("      Para forcar cores: set FORCE_COLOR=1")
        print()
    
    print_header("MACTESTER - PIPELINE AUTOMATIZADO")
    
    # Lista estratégias disponíveis
    strategies = list_strategies()
    if not strategies:
        print_error("Nenhuma estrategia encontrada!")
        sys.exit(1)
    
    print(f"Estrategias disponiveis: {len(strategies)}")
    for i, strat in enumerate(strategies, 1):
        print(f"  {i:2}. {strat}")
    
    # Menu principal
    print(f"\n{Colors.BOLD}Escolha uma opcao:{Colors.ENDC}")
    print("  [1] Testar UMA estrategia")
    print("  [2] Testar TODAS as estrategias")
    print("  [3] Gerar VARIACOES de uma estrategia (Refinamento)")
    print("  [4] VALIDAR estrategia (padrao + indicadores)")
    print("  [5] EXCLUIR estrategia")
    print("  [6] GERAR BOT MT5 de uma estrategia")
    print("  [7] ANALISAR REFINAMENTOS (comparar versoes)")
    print("  [0] Sair")
    
    choice = input(f"\n{Colors.OKCYAN}Opcao: {Colors.ENDC}").strip()
    
    if choice == '0':
        print("Saindo...")
        sys.exit(0)
    
    elif choice == '1':
        # Testar uma estratégia
        print(f"\n{Colors.BOLD}Digite o nome ou numero da estrategia:{Colors.ENDC}")
        strat_input = input(f"{Colors.OKCYAN}Estrategia: {Colors.ENDC}").strip()
        
        # Aceita número ou nome
        if strat_input.isdigit():
            idx = int(strat_input) - 1
            if 0 <= idx < len(strategies):
                strategy = strategies[idx]
            else:
                print_error("Numero invalido!")
                sys.exit(1)
        else:
            if strat_input in strategies:
                strategy = strat_input
            else:
                print_error(f"Estrategia '{strat_input}' nao encontrada!")
                sys.exit(1)
        
        # NOVO: Escolher motor (Python ou Rust)
        print(f"\n{Colors.BOLD}Escolha o motor de backtest:{Colors.ENDC}")
        print("  [1] Python (mais lento, mais confiável)")
        print("  [2] Rust (10-50x mais rápido, requer validação)")
        motor_input = input(f"{Colors.OKCYAN}Motor [1]: {Colors.ENDC}").strip()
        motor = 'rust' if motor_input == '2' else 'python'
        
        # NOVO: Escolher período específico
        print(f"\n{Colors.BOLD}Escolha o período:{Colors.ENDC}")
        print("  [1] Todo o dataset (padrão)")
        print("  [2] Período específico (Matriz Menor)")
        periodo_input = input(f"{Colors.OKCYAN}Opção [1]: {Colors.ENDC}").strip()
        
        periodo_start = None
        periodo_end = None
        
        if periodo_input == '2':
            print(f"\n{Colors.WARNING}Formato de data: YYYY-MM-DD{Colors.ENDC}")
            periodo_start = input(f"{Colors.OKCYAN}Data inicial (ex: 2024-01-02): {Colors.ENDC}").strip()
            periodo_end = input(f"{Colors.OKCYAN}Data final (ex: 2024-01-02): {Colors.ENDC}").strip()
            
            if not periodo_start or not periodo_end:
                print_error("Datas não fornecidas, usando dataset completo")
                periodo_start = None
                periodo_end = None
        
        # Número de testes
        n_tests_input = input(f"{Colors.OKCYAN}Numero de testes [100]: {Colors.ENDC}").strip()
        n_tests = int(n_tests_input) if n_tests_input else 100
        
        # Timeframe
        timeframe_input = input(f"{Colors.OKCYAN}Timeframe [5m]: {Colors.ENDC}").strip()
        timeframe = timeframe_input if timeframe_input else '5m'
        
        # NOVO: Modo de validação (Completo ou Essencial)
        print(f"\n{Colors.BOLD}Modo de validação:{Colors.ENDC}")
        print("  [1] COMPLETO (6 fases: Smoke → Mass → WF → OOS → Outlier → Final)")
        print("  [2] ESSENCIAL (3 fases críticas: Smoke → WF → OOS)")
        modo_input = input(f"{Colors.OKCYAN}Modo [1]: {Colors.ENDC}").strip()
        modo_validacao = 'essencial' if modo_input == '2' else 'completo'
        
        # NOVO: Quantos melhores resultados validar
        if modo_validacao == 'essencial':
            top_n_input = input(f"{Colors.OKCYAN}Quantos melhores resultados validar? [5]: {Colors.ENDC}").strip()
            top_n = int(top_n_input) if top_n_input else 5
        else:
            top_n = 1  # Pipeline completo valida apenas o melhor
        
        # Executar
        result = run_full_pipeline(
            strategy, 
            n_tests, 
            timeframe, 
            motor=motor,
            periodo_start=periodo_start,
            periodo_end=periodo_end,
            modo_validacao=modo_validacao,
            top_n=top_n
        )
        
        # Salvar log
        log_file = Path('results') / f'pipeline_log_{strategy}_{motor}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        log_file.parent.mkdir(exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n{Colors.OKGREEN}Log salvo: {log_file}{Colors.ENDC}")
        
        # Se rejeitada, oferecer refinamento
        decisao_final = result.get('decisao_final', 'DESCONHECIDO')
        if decisao_final == 'REJEITADO':
            executar_refinamento(strategy)
    
    elif choice == '2':
        # Testar todas
        n_tests_input = input(f"{Colors.OKCYAN}Numero de testes por estrategia [1000]: {Colors.ENDC}").strip()
        n_tests = int(n_tests_input) if n_tests_input else 1000
        
        timeframe_input = input(f"{Colors.OKCYAN}Timeframe [5m]: {Colors.ENDC}").strip()
        timeframe = timeframe_input if timeframe_input else '5m'
        
        pause_input = input(f"{Colors.OKCYAN}Pausar entre estrategias? [s/N]: {Colors.ENDC}").strip().lower()
        pause_between = pause_input in ['s', 'sim', 'y', 'yes']
        
        # Executar todas
        all_results = []
        approved = []
        rejected = []
        errors = []
        
        total_start = time.time()
        
        for i, strategy in enumerate(strategies, 1):
            print(f"\n{Colors.BOLD}[{i}/{len(strategies)}] Processando: {strategy}{Colors.ENDC}")
            
            result = run_full_pipeline(strategy, n_tests, timeframe)
            all_results.append(result)
            
            decisao = result.get('decisao_final', 'DESCONHECIDO')
            if decisao == 'APROVADO':
                approved.append(strategy)
            elif decisao == 'REJEITADO':
                rejected.append(strategy)
            else:
                errors.append(strategy)
            
            # Pausar se solicitado
            if pause_between and i < len(strategies):
                input(f"\n{Colors.WARNING}Pressione ENTER para continuar...{Colors.ENDC}")
        
        total_time = time.time() - total_start
        
        # Resumo geral
        print_header("RESUMO GERAL - TODAS AS ESTRATEGIAS")
        print(f"Tempo total: {Colors.BOLD}{total_time/60:.1f} minutos{Colors.ENDC}")
        print(f"Estrategias testadas: {len(strategies)}")
        print(f"\n{Colors.OKGREEN}APROVADAS: {len(approved)}{Colors.ENDC}")
        for strat in approved:
            print(f"  - {strat}")
        
        print(f"\n{Colors.FAIL}REJEITADAS: {len(rejected)}{Colors.ENDC}")
        for strat in rejected:
            print(f"  - {strat}")
        
        if errors:
            print(f"\n{Colors.WARNING}ERROS/DESCONHECIDO: {len(errors)}{Colors.ENDC}")
            for strat in errors:
                print(f"  - {strat}")
        
        # Salvar log consolidado
        summary = {
            'timestamp': datetime.now().isoformat(),
            'n_tests': n_tests,
            'timeframe': timeframe,
            'total_time': total_time,
            'total_strategies': len(strategies),
            'approved': approved,
            'rejected': rejected,
            'errors': errors,
            'detailed_results': all_results
        }
        
        log_file = Path('results') / f'pipeline_summary_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(log_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n{Colors.OKGREEN}Log consolidado salvo: {log_file}{Colors.ENDC}")
        
        # Oferecer refinamento das rejeitadas
        if rejected:
            print(f"\n{Colors.WARNING}{'='*80}{Colors.ENDC}")
            print(f"{Colors.WARNING}{Colors.BOLD}REFINAMENTO DAS ESTRATEGIAS REJEITADAS{Colors.ENDC}")
            print(f"{Colors.WARNING}{'='*80}{Colors.ENDC}")
            print(f"\n{len(rejected)} estrategias foram REJEITADAS:")
            for i, strat in enumerate(rejected, 1):
                print(f"  {i}. {strat}")
            
            refinar_input = input(f"\n{Colors.OKCYAN}Deseja refinar alguma estrategia? [s/N]: {Colors.ENDC}").strip().lower()
            
            if refinar_input in ['s', 'sim', 'y', 'yes']:
                while True:
                    print(f"\n{Colors.BOLD}Estrategias rejeitadas:{Colors.ENDC}")
                    for i, strat in enumerate(rejected, 1):
                        print(f"  {i}. {strat}")
                    print(f"  0. Finalizar")
                    
                    escolha = input(f"\n{Colors.OKCYAN}Numero da estrategia para refinar (0 para sair): {Colors.ENDC}").strip()
                    
                    if escolha == '0' or not escolha:
                        break
                    
                    try:
                        idx = int(escolha) - 1
                        if 0 <= idx < len(rejected):
                            estrategia_escolhida = rejected[idx]
                            executar_refinamento(estrategia_escolhida, auto_default=True)
                        else:
                            print_error("Numero invalido!")
                    except ValueError:
                        print_error("Digite um numero valido!")
                    
                    continuar = input(f"\n{Colors.OKCYAN}Refinar outra estrategia? [s/N]: {Colors.ENDC}").strip().lower()
                    if continuar not in ['s', 'sim', 'y', 'yes']:
                        break
    
    elif choice == '3':
        # Gerar variacoes (refinamento)
        print(f"\n{Colors.BOLD}Digite o nome ou numero da estrategia:{Colors.ENDC}")
        strat_input = input(f"{Colors.OKCYAN}Estrategia: {Colors.ENDC}").strip()
        
        # Aceita número ou nome
        if strat_input.isdigit():
            idx = int(strat_input) - 1
            if 0 <= idx < len(strategies):
                strategy = strategies[idx]
            else:
                print_error("Numero invalido!")
                sys.exit(1)
        else:
            if strat_input in strategies:
                strategy = strat_input
            else:
                print_error(f"Estrategia '{strat_input}' nao encontrada!")
                sys.exit(1)
        
        # Número de iterações
        n_iter_input = input(f"{Colors.OKCYAN}Numero de iteracoes [3]: {Colors.ENDC}").strip()
        n_iteracoes = int(n_iter_input) if n_iter_input else 3
        
        # Número de testes por iteração
        n_tests_input = input(f"{Colors.OKCYAN}Numero de testes por iteracao [1000]: {Colors.ENDC}").strip()
        n_tests = int(n_tests_input) if n_tests_input else 1000
        
        # Modo automático?
        auto_input = input(f"{Colors.OKCYAN}Modo automatico (sem pausas)? [s/N]: {Colors.ENDC}").strip().lower()
        auto_mode = auto_input in ['s', 'sim', 'y', 'yes']
        
        # Tipo de parâmetros a modificar
        print(f"\n{Colors.BOLD}Tipo de parametros a modificar:{Colors.ENDC}")
        print("  [1] Apenas AJUSTAVEIS (SL, TP, volume, horario) - Padrao")
        print("  [2] Apenas IDENTIDADE (conceito core) - Ajuste fino ±10%")
        print("  [3] AMBOS (ajustaveis + identidade)")
        
        modo_input = input(f"{Colors.OKCYAN}Opcao [1]: {Colors.ENDC}").strip()
        
        if modo_input == '2':
            modo_params = 'identidade'
            modo_desc = 'IDENTIDADE (ajuste fino)'
        elif modo_input == '3':
            modo_params = 'ambos'
            modo_desc = 'AMBOS'
        else:
            modo_params = 'ajustaveis'
            modo_desc = 'AJUSTAVEIS'
        
        # Densidade (quantidade de valores)
        print(f"\n{Colors.BOLD}Densidade (quantidade de valores novos a testar):{Colors.ENDC}")
        print("  [1] MINIMA (3 valores)     - Testes rapidos")
        print("  [2] BAIXA (5 valores)      - Exploracao leve")
        print("  [3] MEDIA (7 valores)      - Balanceado (padrao)")
        print("  [4] ALTA (10 valores)      - Exploracao intensa")
        print("  [5] MAXIMA (15+ valores)   - Exploracao exhaustiva")
        
        densidade_input = input(f"{Colors.OKCYAN}Opcao [3]: {Colors.ENDC}").strip()
        densidade = int(densidade_input) if densidade_input and densidade_input.isdigit() and 1 <= int(densidade_input) <= 5 else 3
        
        # Distanciamento (range de valores)
        print(f"\n{Colors.BOLD}Distanciamento (quao distantes os novos valores):{Colors.ENDC}")
        print("  [1] MINIMO (±10%)    - Valores muito proximos")
        print("  [2] BAIXO (±20%)     - Valores proximos")
        print("  [3] MEDIO (±40%)     - Exploracao moderada (padrao)")
        print("  [4] ALTO (±70%)      - Valores distantes")
        print("  [5] MAXIMO (±100%)   - Valores muito distantes")
        
        distanciamento_input = input(f"{Colors.OKCYAN}Opcao [3]: {Colors.ENDC}").strip()
        distanciamento = int(distanciamento_input) if distanciamento_input and distanciamento_input.isdigit() and 1 <= int(distanciamento_input) <= 5 else 3
        
        print_header(f"REFINAMENTO AUTOMATICO: {strategy.upper()}")
        print(f"Iteracoes: {n_iteracoes} | Testes: {n_tests}")
        print(f"Modo: {'AUTO' if auto_mode else 'INTERATIVO'} | Parametros: {modo_desc}")
        print(f"Densidade: {densidade}/5 | Distanciamento: {distanciamento}/5")
        
        # Perguntar se quer forçar refinamento (para estratégias já aprovadas)
        print(f"\n{Colors.BOLD}Forcar refinamento mesmo se ja estiver aprovada?{Colors.ENDC}")
        print("  (Util para explorar parametros alternativos)")
        forcar_input = input(f"{Colors.OKCYAN}Forcar? [s/N]: {Colors.ENDC}").strip().lower()
        forcar = forcar_input in ['s', 'sim', 'y', 'yes']
        
        # Executar refinamento
        cmd = f'python refinar_estrategia.py {strategy} --max-iteracoes {n_iteracoes} --n-tests {n_tests} --modo-params {modo_params} --densidade {densidade} --distanciamento {distanciamento}'
        if auto_mode:
            cmd += ' --auto'
        if forcar:
            cmd += ' --forcar'
        
        print(f"\n{Colors.OKCYAN}Executando: {cmd}{Colors.ENDC}\n")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode == 0:
                print(f"\n{Colors.OKGREEN}Refinamento concluido com sucesso!{Colors.ENDC}")
            else:
                print(f"\n{Colors.WARNING}Refinamento finalizado (codigo: {result.returncode}){Colors.ENDC}")
        
        except Exception as e:
            print_error(f"Erro ao executar refinamento: {e}")
            sys.exit(1)
    
    elif choice == '4':
        # Validar estratégia (padrão + indicadores)
        print(f"\n{Colors.BOLD}Digite o nome ou numero da estrategia:{Colors.ENDC}")
        strat_input = input(f"{Colors.OKCYAN}Estrategia: {Colors.ENDC}").strip()
        
        # Aceita número ou nome
        if strat_input.isdigit():
            idx = int(strat_input) - 1
            if 0 <= idx < len(strategies):
                strategy = strategies[idx]
            else:
                print_error("Numero invalido!")
                sys.exit(1)
        else:
            if strat_input in strategies:
                strategy = strat_input
            else:
                print_error(f"Estrategia '{strat_input}' nao encontrada!")
                sys.exit(1)
        
        print_header(f"VALIDACAO COMPLETA: {strategy.upper()}")
        
        # 1. Validar padrão
        print(f"\n{Colors.BOLD}[1/2] Validando padrao de estrategia...{Colors.ENDC}\n")
        cmd_padrao = f'python validar_padrao_estrategia.py {strategy}'
        returncode_padrao, output_padrao = run_command(cmd_padrao)
        print(output_padrao)
        
        validacao_padrao = returncode_padrao == 0
        
        # 2. Validar indicadores
        print(f"\n{Colors.BOLD}[2/2] Verificando indicadores disponiveis...{Colors.ENDC}\n")
        cmd_ind = f'python verificar_indicadores.py {strategy}'
        returncode_ind, output_ind = run_command(cmd_ind)
        print(output_ind)
        
        validacao_indicadores = returncode_ind == 0
        
        # Resumo
        print("\n" + "="*80)
        print("RESULTADO DA VALIDACAO")
        print("="*80)
        
        if validacao_padrao:
            print(f"{Colors.OKGREEN}Padrao: VALIDO{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}Padrao: INVALIDO{Colors.ENDC}")
        
        if validacao_indicadores:
            print(f"{Colors.OKGREEN}Indicadores: DISPONIVEIS{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}Indicadores: FALTANTES (baixar do MT5){Colors.ENDC}")
        
        print("="*80)
        
        if validacao_padrao and validacao_indicadores:
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}ESTRATEGIA PRONTA PARA USO!{Colors.ENDC}")
        elif validacao_padrao:
            print(f"\n{Colors.WARNING}{Colors.BOLD}ESTRATEGIA VALIDA mas requer dados adicionais{Colors.ENDC}")
            print("Baixe os indicadores faltantes do MT5 antes de testar.")
        else:
            print(f"\n{Colors.FAIL}{Colors.BOLD}ESTRATEGIA INVALIDA{Colors.ENDC}")
            print("Corrija os erros de padrao antes de usar.")
    
    elif choice == '5':
        # Excluir estratégia
        print(f"\n{Colors.BOLD}Digite o nome ou numero da estrategia a EXCLUIR:{Colors.ENDC}")
        strat_input = input(f"{Colors.OKCYAN}Estrategia: {Colors.ENDC}").strip()
        
        # Aceita número ou nome
        if strat_input.isdigit():
            idx = int(strat_input) - 1
            if 0 <= idx < len(strategies):
                strategy = strategies[idx]
            else:
                print_error("Numero invalido!")
                sys.exit(1)
        else:
            if strat_input in strategies:
                strategy = strat_input
            else:
                print_error(f"Estrategia '{strat_input}' nao encontrada!")
                sys.exit(1)
        
        # Confirmar exclusão
        print(f"\n{Colors.WARNING}{Colors.BOLD}ATENCAO: Esta acao NAO pode ser desfeita!{Colors.ENDC}")
        print(f"Estrategia a excluir: {Colors.FAIL}{strategy}{Colors.ENDC}")
        print(f"Diretorio: strategies/{strategy}/")
        
        confirm = input(f"\n{Colors.WARNING}Digite 'EXCLUIR' para confirmar: {Colors.ENDC}").strip()
        
        if confirm != 'EXCLUIR':
            print("Operacao cancelada.")
            sys.exit(0)
        
        # Excluir
        import shutil
        import stat
        import time
        strategy_path = Path('strategies') / strategy
        
        def force_remove_readonly(func, path, exc_info):
            """Handler para remover arquivos readonly no Windows"""
            import os
            os.chmod(path, stat.S_IWRITE)
            func(path)
        
        try:
            if strategy_path.exists():
                # Usar onerror para forçar exclusão de arquivos readonly
                shutil.rmtree(strategy_path, onerror=force_remove_readonly)
                print(f"\n{Colors.OKGREEN}Estrategia '{strategy}' excluida com sucesso!{Colors.ENDC}")
                
                # Verificar e excluir resultados relacionados
                results_dir = Path('results')
                if results_dir.exists():
                    deleted_files = []
                    for result_file in results_dir.rglob(f'*{strategy}*'):
                        if result_file.is_file():
                            result_file.unlink()
                            deleted_files.append(result_file.name)
                    
                    if deleted_files:
                        print(f"\n{len(deleted_files)} arquivos de resultados tambem foram excluidos:")
                        for fname in deleted_files[:10]:  # Mostrar até 10
                            print(f"  - {fname}")
                        if len(deleted_files) > 10:
                            print(f"  ... e mais {len(deleted_files) - 10} arquivos")
            else:
                print_error(f"Diretorio da estrategia nao encontrado: {strategy_path}")
                sys.exit(1)
        
        except Exception as e:
            print_error(f"Erro ao excluir estrategia: {e}")
            sys.exit(1)
    
    elif choice == '6':
        # Gerar bot MT5
        print(f"\n{Colors.BOLD}Digite o nome ou numero da estrategia:{Colors.ENDC}")
        strat_input = input(f"{Colors.OKCYAN}Estrategia: {Colors.ENDC}").strip()
        
        # Aceita número ou nome
        if strat_input.isdigit():
            idx = int(strat_input) - 1
            if 0 <= idx < len(strategies):
                strategy = strategies[idx]
            else:
                print_error("Numero invalido!")
                sys.exit(1)
        else:
            if strat_input in strategies:
                strategy = strat_input
            else:
                print_error(f"Estrategia '{strat_input}' nao encontrada!")
                sys.exit(1)
        
        # Perguntar se quer usar parametros otimizados
        usar_otimizados = input(f"{Colors.OKCYAN}Usar parametros otimizados (top_50)? [S/n]: {Colors.ENDC}").strip().lower()
        sem_otimizacao = usar_otimizados in ['n', 'nao', 'no']
        
        print_header(f"GERANDO BOT MT5: {strategy.upper()}")
        
        # Executar gerador
        cmd = f'python gerador_bot_mt5.py {strategy}'
        if sem_otimizacao:
            cmd += ' --sem-otimizacao'
        
        print(f"{Colors.OKCYAN}Executando: {cmd}{Colors.ENDC}\n")
        
        try:
            returncode, output = run_command(cmd)
            print(output)
            
            if returncode == 0:
                print(f"\n{Colors.OKGREEN}{Colors.BOLD}Bot MT5 gerado com sucesso!{Colors.ENDC}")
                print(f"\n{Colors.OKCYAN}Arquivo gerado em: bots_mt5/{strategy}_EA.mq5{Colors.ENDC}")
                print(f"\n{Colors.WARNING}LEMBRETE:{Colors.ENDC}")
                print("  1. Abra o MetaEditor (MT5)")
                print(f"  2. Abra o arquivo: bots_mt5/{strategy}_EA.mq5")
                print("  3. IMPLEMENTE a logica especifica da estrategia na funcao VerificarSinais()")
                print("  4. Compile (F7)")
                print("  5. Anexe ao grafico no MT5")
                print(f"\n{Colors.WARNING}IMPORTANTE:{Colors.ENDC} O codigo gerado eh um TEMPLATE.")
                print("Voce precisa implementar a logica especifica da estrategia!")
            else:
                print(f"\n{Colors.FAIL}Erro ao gerar bot MT5 (codigo: {returncode}){Colors.ENDC}")
        
        except Exception as e:
            print_error(f"Erro ao executar gerador: {e}")
            sys.exit(1)
    
    elif choice == '7':
        # Analisar refinamentos
        print_header("ANALISADOR DE REFINAMENTOS")
        
        # Executar analisador em modo interativo
        cmd = 'python analisar_refinamento.py'
        
        print(f"{Colors.OKCYAN}Executando analisador...{Colors.ENDC}\n")
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                print(f"\n{Colors.WARNING}Analisador finalizado (codigo: {result.returncode}){Colors.ENDC}")
        
        except Exception as e:
            print_error(f"Erro ao executar analisador: {e}")
            sys.exit(1)
    
    else:
        print_error("Opcao invalida!")
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Interrompido pelo usuario{Colors.ENDC}")
        sys.exit(130)
    except Exception as e:
        print_error(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

