"""
Otimizador usando concurrent.futures - Alternativa ao multiprocessing

ProcessPoolExecutor tem melhor scheduling que Pool no Windows
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
import ast
import time
import sys
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
import itertools
from typing import Dict, List, Optional
import warnings
import gc
from multiprocessing import cpu_count

# SUPRIMIR WARNINGS
warnings.filterwarnings('ignore', category=RuntimeWarning)
np.seterr(all='ignore')

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator


# GLOBALS
_GLOBAL_DATA = None
_GLOBAL_STRATEGY = None
_GLOBAL_ENGINE = None


def _init_worker_concurrent(data_df, strategy_name):
    """Inicializa worker"""
    global _GLOBAL_DATA, _GLOBAL_STRATEGY, _GLOBAL_ENGINE
    _GLOBAL_DATA = data_df
    _GLOBAL_STRATEGY = strategy_name
    _GLOBAL_ENGINE = BacktestEngine(_GLOBAL_DATA, verbose=False)
    
    # Warm-up
    if strategy_name == 'barra_elefante':
        try:
            from strategies.barra_elefante.strategy import warmup_numba
            warmup_numba()
        except:
            pass


def _run_single_test_concurrent(params: Dict) -> Dict:
    """Executa teste"""
    global _GLOBAL_ENGINE, _GLOBAL_STRATEGY
    
    import warnings
    warnings.filterwarnings('ignore')
    
    result = _GLOBAL_ENGINE.run_strategy(_GLOBAL_STRATEGY, params)
    
    if 'trades' in result:
        result['trades_count'] = len(result['trades'])
        del result['trades']
    
    return result


class ConcurrentOptimizer:
    """
    Otimizador usando concurrent.futures ProcessPoolExecutor
    Melhor scheduling que multiprocessing.Pool no Windows
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
        
        if n_cores:
            self.n_cores = n_cores
        else:
            # ProcessPoolExecutor funciona bem com mais workers
            self.n_cores = min(16, cpu_count())
        
        print(f"[CONCURRENT] Usando {self.n_cores} workers (ProcessPoolExecutor)")
        
        self.checkpoint_every = checkpoint_every
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{strategy}_{timestamp}"
        self.results_dir = Path(results_dir) / self.run_id
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[RESULTADOS] Diretorio: {self.results_dir}")
        
        self.metrics_calc = MetricsCalculator()
        self._load_strategy_class()
    
    def _load_strategy_class(self):
        """Carrega estratégia"""
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
        print(f"MACTESTER V2.1 - OTIMIZACAO CONCURRENT (FIXED)")
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
        
        print("Iniciando otimizacao...")
        print()
        
        gc.enable()
        print("[PERFORMANCE] Garbage Collector HABILITADO")
        print()
        
        start_time = time.time()
        
        # ProcessPoolExecutor com initializer
        print(f"Iniciando {self.n_cores} workers...")
        
        # Arquivo de resultados
        file_index = 0
        results_file = self.results_dir / f"results_stream_part{file_index:03d}.jsonl"
        f_stream = open(results_file, 'w', buffering=32*1024*1024)
        
        counter = 0
        buffer_raw = []
        BUFFER_SIZE = 20000
        
        print(f"[CONFIG] {self.n_cores} workers | Buffer {BUFFER_SIZE} | GC ON")
        print("[CONCURRENT] ProcessPoolExecutor - Melhor scheduling que Pool")
        print()
        sys.stdout.flush()
        
        # Usar ProcessPoolExecutor
        with ProcessPoolExecutor(
            max_workers=self.n_cores,
            initializer=_init_worker_concurrent,
            initargs=(self.data, self.strategy_name)
        ) as executor:
            
            print("Workers iniciados!")
            print()
            sys.stdout.flush()
            
            # Print barra inicial SEMPRE VISÍVEL
            print(f"[{'-'*50}] 0.0% | 0/{total_tests:,} | 0 t/s | ETA: calculando...", end='', flush=True)
            
            last_print = time.time()
            
            # Submeter em BATCHES para não travar (max 1000 futures pendentes)
            MAX_PENDING = 1000
            pending_futures = set()
            combo_idx = 0
            
            # Submeter batch inicial
            while combo_idx < min(MAX_PENDING, len(combinations)):
                future = executor.submit(_run_single_test_concurrent, combinations[combo_idx])
                pending_futures.add(future)
                combo_idx += 1
            
            # Processar conforme completam e submeter novos
            while pending_futures:
                # Esperar QUALQUER future completar
                done, pending_futures = concurrent.futures.wait(
                    pending_futures, 
                    return_when=concurrent.futures.FIRST_COMPLETED
                )
                
                # Processar os que completaram
                for future in done:
                    try:
                        result = future.result()
                        buffer_raw.append(result)
                        counter += 1
                        
                        # Submeter próximo teste (manter fila sempre cheia)
                        if combo_idx < len(combinations):
                            new_future = executor.submit(_run_single_test_concurrent, combinations[combo_idx])
                            pending_futures.add(new_future)
                            combo_idx += 1
                        
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
                        
                        # Print/barra a cada 100 testes OU a cada 3 segundos (MUITO frequente)
                        current_time = time.time()
                        if counter % 100 == 0 or (current_time - last_print) >= 3:
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
                
                except Exception as e:
                    print(f"\n[ERRO] Test failed: {e}")
                    continue
            
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
        """Lê resultados"""
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
        """Gera combinações"""
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
        
        # Converter total_return para total_return_pct se necessário
        if 'total_return' in df.columns and 'total_return_pct' not in df.columns:
            df['total_return_pct'] = df['total_return']
        
        df['score'] = df.apply(
            lambda row: self.metrics_calc.calculate_composite_score(row.to_dict()),
            axis=1
        )
        
        df = df.sort_values('score', ascending=False)
        
        return df
    
    def _save_top_results(self, top_df: pd.DataFrame, json_file: Path):
        """Salva top resultados"""
        top_50_dict = []
        for idx, row in top_df.iterrows():
            entry = row.to_dict()
            for key, value in entry.items():
                if isinstance(value, (np.integer, np.floating)):
                    entry[key] = float(value) if isinstance(value, np.floating) else int(value)
            top_50_dict.append(entry)
        
        with open(json_file, 'w') as f:
            json.dump(top_50_dict, f, indent=2)

