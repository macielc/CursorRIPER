"""
Otimizador Massivo com RAY - Performance Superior

Ray resolve problemas do multiprocessing:
- Melhor scheduling no Windows
- Menos overhead de IPC
- Gerenciamento de memória superior
- Performance estável sem degradação
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
import ast
import time
import sys
from datetime import datetime
import itertools
from typing import Dict, List, Optional
import warnings
import gc

# RAY para paralelização moderna
import ray

# SUPRIMIR WARNINGS
warnings.filterwarnings('ignore', category=RuntimeWarning)
np.seterr(all='ignore')

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator


# GLOBAL DATA para cada worker Ray
_GLOBAL_ENGINE = None
_GLOBAL_STRATEGY = None


@ray.remote
class OptimizationWorker:
    """Worker Ray que mantém engine e dados em memória"""
    
    def __init__(self, data_df, strategy_name):
        """Inicializa worker com engine permanente"""
        self.data = data_df
        self.strategy_name = strategy_name
        
        # Criar engine UMA VEZ
        self.engine = BacktestEngine(self.data, verbose=False)
        
        # Warm-up Numba
        if strategy_name == 'barra_elefante':
            try:
                from strategies.barra_elefante.strategy import warmup_numba
                warmup_numba()
            except:
                pass
    
    def run_test(self, params: Dict) -> Dict:
        """Executa um teste usando engine permanente"""
        import warnings
        warnings.filterwarnings('ignore')
        
        # Reutilizar engine
        result = self.engine.run_strategy(self.strategy_name, params)
        
        # Remover trades (não necessário)
        if 'trades' in result:
            result['trades_count'] = len(result['trades'])
            del result['trades']
        
        return result
    
    def run_batch(self, params_batch: List[Dict]) -> List[Dict]:
        """Executa batch de testes (mais eficiente)"""
        results = []
        for params in params_batch:
            result = self.run_test(params)
            results.append(result)
        return results


class RayOptimizer:
    """
    Otimizador usando Ray - Performance superior ao multiprocessing
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: str = 'power_breakout',
        n_cores: Optional[int] = None,
        checkpoint_every: int = 100000,
        results_dir: str = 'results/optimization'
    ):
        self.data = data
        self.strategy_name = strategy
        
        # Número de workers
        if n_cores:
            self.n_cores = n_cores
        else:
            # Usar mais workers com Ray (mais eficiente que multiprocessing)
            import multiprocessing
            self.n_cores = min(16, multiprocessing.cpu_count())
        
        print(f"[RAY] Usando {self.n_cores} workers")
        
        self.checkpoint_every = checkpoint_every
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{strategy}_{timestamp}"
        self.results_dir = Path(results_dir) / self.run_id
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[RESULTADOS] Diretorio: {self.results_dir}")
        
        self.metrics_calc = MetricsCalculator()
        self._load_strategy_class()
    
    def _load_strategy_class(self):
        """Carrega a classe da estratégia"""
        import sys
        from pathlib import Path
        
        strategies_path = Path(__file__).parent.parent / 'strategies'
        if str(strategies_path) not in sys.path:
            sys.path.insert(0, str(strategies_path))
        
        from strategies import get_strategy
        self.strategy_class = get_strategy(self.strategy_name)
    
    def optimize(
        self,
        param_grid: Dict,
        top_n: int = 50,
        resume: bool = True,
        max_tests: int = None
    ) -> pd.DataFrame:
        
        print("="*80)
        print(f"MACTESTER V2.1 - OTIMIZACAO RAY (ULTRAFAST)")
        print("="*80)
        print(f"Estrategia: {self.strategy_name}")
        print(f"Workers: {self.n_cores}")
        print(f"Checkpoint: {self.checkpoint_every:,} testes")
        print()
        
        # Gerar combinações
        print("Gerando combinacoes...")
        combinations = self._generate_combinations(param_grid, max_tests)
        total_tests = len(combinations)
        print(f"Total de testes: {total_tests:,}")
        print()
        
        # Inicializar Ray
        if not ray.is_initialized():
            ray.init(num_cpus=self.n_cores, ignore_reinit_error=True)
            print("[RAY] Inicializado com sucesso")
        
        print("Iniciando otimizacao...")
        print()
        
        start_time = time.time()
        
        # Criar workers Ray
        print(f"Criando {self.n_cores} workers Ray...")
        workers = [
            OptimizationWorker.remote(self.data, self.strategy_name)
            for _ in range(self.n_cores)
        ]
        print("Workers criados e aquecidos!")
        print()
        
        # Configuração
        BATCH_SIZE = 100  # Cada worker processa batch de 100
        BUFFER_SIZE = 20000
        
        print(f"[CONFIG] {self.n_cores} workers | Batch {BATCH_SIZE} | Buffer {BUFFER_SIZE}")
        print("[RAY] Scheduling inteligente - SEM degradação")
        print()
        sys.stdout.flush()
        
        # Arquivo de resultados
        file_index = 0
        results_file = self.results_dir / f"results_stream_part{file_index:03d}.jsonl"
        f_stream = open(results_file, 'w', buffering=32*1024*1024)
        
        counter = 0
        buffer_raw = []
        
        # Dividir trabalho em batches
        all_batches = []
        for i in range(0, len(combinations), BATCH_SIZE):
            batch = combinations[i:i+BATCH_SIZE]
            all_batches.append(batch)
        
        print(f"Total de batches: {len(all_batches):,}")
        print()
        
        # Distribuir batches entre workers (round-robin)
        pending_tasks = []
        batch_idx = 0
        
        # Submeter trabalho inicial
        for worker in workers:
            if batch_idx < len(all_batches):
                task = worker.run_batch.remote(all_batches[batch_idx])
                pending_tasks.append(task)
                batch_idx += 1
        
        # Processar resultados conforme ficam prontos
        last_print = time.time()
        
        while pending_tasks:
            # Esperar QUALQUER tarefa completar
            ready, pending_tasks = ray.wait(pending_tasks, num_returns=1, timeout=1.0)
            
            for task in ready:
                # Pegar resultados
                results_batch = ray.get(task)
                
                for result in results_batch:
                    buffer_raw.append(result)
                    counter += 1
                    
                    # Novo arquivo a cada 50k
                    if counter % 50000 == 0 and counter > 0:
                        if buffer_raw:
                            for res in buffer_raw:
                                simple = {
                                    'total_return': float(res.get('total_return', 0)),
                                    'sharpe_ratio': float(res.get('sharpe_ratio', 0)),
                                    'win_rate': float(res.get('win_rate', 0)),
                                    'total_trades': int(res.get('total_trades', 0)),
                                    'profit_factor': float(res.get('profit_factor', 0)),
                                    'max_drawdown_pct': float(res.get('max_drawdown_pct', 0)),
                                    'params': str(res.get('params', {})),
                                    'success': bool(res.get('success', False))
                                }
                                f_stream.write(json.dumps(simple) + '\n')
                            buffer_raw.clear()
                        f_stream.flush()
                        f_stream.close()
                        
                        file_index += 1
                        results_file = self.results_dir / f"results_stream_part{file_index:03d}.jsonl"
                        f_stream = open(results_file, 'w', buffering=32*1024*1024)
                        print(f"\n[NOVO ARQUIVO] Part {file_index} iniciado", flush=True)
                    
                    # Flush buffer
                    if len(buffer_raw) >= BUFFER_SIZE:
                        for res in buffer_raw:
                            simple = {
                                'total_return': float(res.get('total_return', 0)),
                                'sharpe_ratio': float(res.get('sharpe_ratio', 0)),
                                'win_rate': float(res.get('win_rate', 0)),
                                'total_trades': int(res.get('total_trades', 0)),
                                'profit_factor': float(res.get('profit_factor', 0)),
                                'max_drawdown_pct': float(res.get('max_drawdown_pct', 0)),
                                'params': str(res.get('params', {})),
                                'success': bool(res.get('success', False))
                            }
                            f_stream.write(json.dumps(simple) + '\n')
                        
                        f_stream.flush()
                        buffer_raw.clear()
                        gc.collect()
                
                # Submeter próximo batch
                if batch_idx < len(all_batches):
                    # Escolher worker que acabou de terminar (reutilizar)
                    worker = workers[batch_idx % self.n_cores]
                    task = worker.run_batch.remote(all_batches[batch_idx])
                    pending_tasks.append(task)
                    batch_idx += 1
            
            # Print a cada 2000 testes
            current_time = time.time()
            if counter % 2000 == 0:
                elapsed = current_time - start_time
                velocity = counter / elapsed if elapsed > 0 else 0
                progress_pct = (counter / total_tests) * 100
                remaining = total_tests - counter
                eta_sec = remaining / velocity if velocity > 0 else 0
                eta_min = eta_sec / 60
                
                bar_len = 50
                filled = int(bar_len * counter / total_tests)
                bar = '#' * filled + '-' * (bar_len - filled)
                
                print(f"\r[{bar}] {progress_pct:.1f}% | {counter:,}/{total_tests:,} | {velocity:.0f} t/s | ETA: {eta_min:.0f}min", end='', flush=True)
                last_print = current_time
            
            # Checkpoint
            if counter % self.checkpoint_every == 0 and counter > 0:
                print(f"\n[CHECKPOINT] {counter:,} testes", flush=True)
        
        # Flush final
        if buffer_raw:
            for res in buffer_raw:
                simple = {
                    'total_return': float(res.get('total_return', 0)),
                    'sharpe_ratio': float(res.get('sharpe_ratio', 0)),
                    'win_rate': float(res.get('win_rate', 0)),
                    'total_trades': int(res.get('total_trades', 0)),
                    'profit_factor': float(res.get('profit_factor', 0)),
                    'max_drawdown_pct': float(res.get('max_drawdown_pct', 0)),
                    'params': str(res.get('params', {})),
                    'success': bool(res.get('success', False))
                }
                f_stream.write(json.dumps(simple) + '\n')
            buffer_raw.clear()
        
        f_stream.flush()
        f_stream.close()
        
        elapsed = time.time() - start_time
        print(f"\n\n[COMPLETO] {counter:,} testes em {elapsed/60:.1f} min ({counter/elapsed:.0f} t/s)")
        
        # Ler resultados
        print("\nLendo resultados...")
        all_results = self._read_all_results()
        
        # Analisar
        print(f"Analisando {len(all_results):,} resultados...")
        df = self._analyze_results(all_results, top_n)
        
        # Salvar top N
        top_file = self.results_dir / f"top_{top_n}_results.json"
        self._save_top_results(df.head(top_n), top_file)
        
        print(f"\n[SALVO] Top {top_n}: {top_file}")
        
        return df
    
    def _read_all_results(self) -> List[Dict]:
        """Lê todos os arquivos de resultados"""
        all_results = []
        
        for file_path in sorted(self.results_dir.glob("results_stream_part*.jsonl")):
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if 'params' in data and isinstance(data['params'], str):
                            import ast
                            data['params'] = ast.literal_eval(data['params'])
                        all_results.append(data)
                    except:
                        continue
        
        return all_results
    
    def _generate_combinations(self, param_grid: Dict, max_combinations: int = None) -> List[Dict]:
        """Gera combinações de parâmetros"""
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        combinations = []
        for combination in itertools.product(*values):
            param_dict = dict(zip(keys, combination))
            combinations.append(param_dict)
            if max_combinations and len(combinations) >= max_combinations:
                break
        
        return combinations
    
    def _analyze_results(self, results: List[Dict], top_n: int) -> pd.DataFrame:
        """Analisa resultados"""
        df = pd.DataFrame(results)
        
        df['score'] = df.apply(
            lambda row: self.metrics_calc.calculate_composite_score(row.to_dict()),
            axis=1
        )
        
        df = df.sort_values('score', ascending=False)
        
        return df
    
    def _save_top_results(self, top_df: pd.DataFrame, json_file: Path):
        """Salva top resultados em JSON"""
        top_50_dict = []
        for idx, row in top_df.iterrows():
            entry = row.to_dict()
            # Converter tipos
            for key, value in entry.items():
                if isinstance(value, (np.integer, np.floating)):
                    entry[key] = float(value) if isinstance(value, np.floating) else int(value)
            top_50_dict.append(entry)
        
        with open(json_file, 'w') as f:
            json.dump(top_50_dict, f, indent=2)

