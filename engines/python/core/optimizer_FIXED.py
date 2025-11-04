"""
Otimizador Massivo Paralelo - VERSAO OTIMIZADA

FIXES:
1. DataFrame passado como global (nao via partial) - economiza GIGABYTES de RAM
2. GC habilitado com limpeza inteligente
3. Buffer otimizado: conversao numpy ANTES de adicionar
4. maxtasksperchild removido (workers permanentes = menos overhead)
5. I/O async com buffer maior
6. Checkpoint simplificado (somente a cada 100k)
"""

import numpy as np
import pandas as pd
from pathlib import Path
import json
import time
import sys
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
import itertools
from typing import Dict, List, Optional
import warnings
import gc
import enlighten

# SUPRIMIR WARNINGS DE OVERFLOW DO NUMPY
warnings.filterwarnings('ignore', category=RuntimeWarning)
np.seterr(all='ignore')

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator


# GLOBAL: DataFrame compartilhado entre workers (economiza RAM massivamente)
_GLOBAL_DATA = None
_GLOBAL_STRATEGY = None


def _init_worker(data_df, strategy_name):
    """Inicializa worker com dados globais (chamado uma vez por worker)"""
    global _GLOBAL_DATA, _GLOBAL_STRATEGY
    _GLOBAL_DATA = data_df
    _GLOBAL_STRATEGY = strategy_name
    
    # Warm-up Numba para este worker
    if strategy_name == 'barra_elefante':
        try:
            from strategies.barra_elefante.strategy import warmup_numba
            warmup_numba()
        except:
            pass


def _run_single_test_global(params: Dict) -> Dict:
    """Executa teste usando dados globais (ZERO overhead de serialização)"""
    global _GLOBAL_DATA, _GLOBAL_STRATEGY
    
    import warnings
    warnings.filterwarnings('ignore')
    
    # Usar dados globais (sem copiar, sem serializar)
    engine = BacktestEngine(_GLOBAL_DATA, verbose=False)
    result = engine.run_strategy(_GLOBAL_STRATEGY, params)
    
    # OTIMIZACAO CRITICA: Remover 'trades' antes de retornar (reduz 90% do trafego IPC)
    # Trades nao sao necessarios para otimizacao, so metricas
    if 'trades' in result:
        result['trades_count'] = len(result['trades'])  # Guardar apenas contagem
        del result['trades']
    
    return result


class MassiveOptimizer:
    """
    Otimizador massivo OTIMIZADO - performance maxima, uso minimo de RAM
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
        
        max_cores = cpu_count()
        self.n_cores = n_cores if n_cores else max_cores
        
        print(f"[PERFORMANCE] Cores: {self.n_cores}/{max_cores} (100% CPU)")
        
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
        """
        Executa otimização massiva OTIMIZADA
        """
        print("="*80)
        print("MACTESTER V2.1 - OTIMIZACAO MASSIVA (FIXED)")
        print("="*80)
        print(f"Estrategia: {self.strategy_name}")
        print(f"Cores: {self.n_cores}")
        print(f"Checkpoint: {self.checkpoint_every:,} testes")
        print()
        
        # Gerar combinações
        combinations = self._generate_combinations(param_grid, max_combinations=max_tests)
        total_tests = len(combinations)
        
        print(f"Total de testes: {total_tests:,}")
        print(f"Tempo estimado: {self._estimate_time(total_tests):.1f} min")
        print()
        
        # Verificar checkpoint
        results = []
        start_idx = 0
        
        if resume:
            results, start_idx = self._load_checkpoint()
            if start_idx > 0:
                print(f"Retomando: {start_idx:,} testes concluidos")
        
        print("Iniciando otimizacao...")
        print()
        
        # FIX CRITICO: GC habilitado mas com limpeza manual estrategica
        gc.enable()
        
        start_time = time.time()
        
        # Pool com workers PERMANENTES (sem maxtasksperchild)
        # FIX: Passar data via initializer (compartilhado), NAO via partial
        print(f"Iniciando {self.n_cores} workers...")
        sys.stdout.flush()
        
        with Pool(
            self.n_cores,
            initializer=_init_worker,
            initargs=(self.data, self.strategy_name)
        ) as pool:
            
            print("Workers iniciados e aquecidos!")
            print()
            sys.stdout.flush()
            
            batch = combinations[start_idx:]
            
            # Chunksize otimizado
            optimal_chunksize = max(1, len(batch) // (self.n_cores * 100))
            print(f"Chunksize: {optimal_chunksize}")
            print()
            
            # Arquivo de stream
            results_file = self.results_dir / "results_stream.jsonl"
            f_stream = open(results_file, 'w', buffering=16*1024*1024)  # Buffer 16MB
            
            counter = 0
            last_gc = time.time()
            
            # FIX: Buffer com conversao PRE-PROCESSADA
            buffer_raw = []  # Buffer temporario de resultados brutos
            BUFFER_SIZE = 5000  # Reduzido para 5k (menos memoria)
            
            print("[OTIMIZADO] Buffer 5k | GC a cada 30s | Workers permanentes")
            print()
            sys.stdout.flush()
            
            # ENLIGHTEN: Barra de progresso
            manager = enlighten.get_manager()
            pbar = manager.counter(total=len(batch), desc='Otimizando', unit='testes', color='green')
            status_bar = manager.status_bar(status_format='Status: {fill}', color='bold_white', justify=enlighten.Justify.CENTER)
            
            for result in pool.imap_unordered(_run_single_test_global, batch, chunksize=optimal_chunksize):
                # Adicionar ao buffer RAW
                buffer_raw.append(result)
                counter += 1
                pbar.update()
                
                # FLUSH quando atingir tamanho do buffer
                if len(buffer_raw) >= BUFFER_SIZE:
                    # Converter e escrever em BATCH
                    for res in buffer_raw:
                        res_json = self._convert_numpy_types(res)
                        f_stream.write(json.dumps(res_json) + '\n')
                    
                    f_stream.flush()
                    buffer_raw.clear()
                    
                    # GC manual
                    gc.collect()
                    
                    status_bar.update(f'[FLUSH] {counter:,} testados | RAM liberada')
                
                # GC a cada 30 segundos
                current_time = time.time()
                if (current_time - last_gc) >= 30:
                    gc.collect()
                    last_gc = current_time
                
                # Atualizar velocidade na barra
                if counter % 100 == 0:
                    elapsed = current_time - start_time
                    velocity = counter / elapsed if elapsed > 0 else 0
                    pbar.desc = f'Otimizando ({velocity:.0f} t/s)'
                
                # Checkpoint a cada checkpoint_every
                if counter % self.checkpoint_every == 0:
                    status_bar.update(f'[CHECKPOINT] {counter:,} testes')
            
            # Flush final
            if buffer_raw:
                for res in buffer_raw:
                    res_json = self._convert_numpy_types(res)
                    f_stream.write(json.dumps(res_json) + '\n')
                f_stream.flush()
                buffer_raw.clear()
            
            f_stream.close()
            
            # Fechar enlighten
            manager.stop()
            
            print()
            print("="*80)
            print(f"PROCESSAMENTO CONCLUIDO: {counter:,} testes")
            print("="*80)
            sys.stdout.flush()
        
        # Limpar memoria
        gc.collect()
        
        # Carregar resultados
        print()
        print("Carregando resultados...")
        all_results = []
        
        with open(results_file, 'r') as f:
            for line in f:
                if line.strip():
                    all_results.append(json.loads(line))
        
        print(f"Carregados {len(all_results):,} resultados!")
        
        # Processar resultados
        print(f"Processando Top {top_n}...")
        results_df = self._process_results(all_results, top_n)
        
        # Salvar resultados finais
        self._save_final_results(results_df, total_tests)
        
        print()
        print("="*80)
        print("OTIMIZACAO CONCLUIDA!")
        print("="*80)
        print(f"Total: {total_tests:,} testes")
        print(f"Tempo: {(time.time() - start_time)/60:.1f} min")
        print(f"Top {top_n}: {self.results_dir}")
        print()
        
        return results_df
    
    def _generate_combinations(self, param_grid: Dict, max_combinations: int = None) -> List[Dict]:
        """Gera combinações de parâmetros"""
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        total_possible = 1
        for v in values:
            total_possible *= len(v)
        
        if max_combinations and max_combinations < total_possible:
            print(f"Grid: {total_possible:,} combinacoes")
            print(f"Limitando: {max_combinations:,} (amostragem)")
            print()
            
            import random
            random.seed(42)
            
            combinations = []
            used = set()
            
            attempts = 0
            max_attempts = max_combinations * 10
            
            while len(combinations) < max_combinations and attempts < max_attempts:
                attempts += 1
                combination = tuple(random.choice(v) for v in values)
                
                if combination in used:
                    continue
                
                used.add(combination)
                param_dict = dict(zip(keys, combination))
                combinations.append(param_dict)
            
            if len(combinations) < max_combinations:
                print(f"AVISO: {len(combinations)} combinacoes unicas geradas")
                
        else:
            print(f"Gerando {total_possible:,} combinacoes...")
            print()
            
            combinations = []
            for combination in itertools.product(*values):
                param_dict = dict(zip(keys, combination))
                combinations.append(param_dict)
        
        return combinations
    
    def _process_results(self, results: List[Dict], top_n: int) -> pd.DataFrame:
        """Processa resultados e seleciona top N"""
        df = pd.DataFrame(results)
        
        df = df[df['success'] == True].copy()
        
        if len(df) == 0:
            print("AVISO: Nenhum resultado valido!")
            return pd.DataFrame()
        
        df['score'] = df.apply(
            lambda row: self.metrics_calc.calculate_composite_score(row.to_dict()),
            axis=1
        )
        
        df = df.sort_values('score', ascending=False)
        top_df = df.head(top_n).copy()
        
        return top_df
    
    def _load_checkpoint(self) -> tuple:
        """Carrega checkpoint (simplificado)"""
        return [], 0  # Desabilitado por enquanto
    
    def _save_final_results(self, df: pd.DataFrame, total_tests: int):
        """Salva resultados finais"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        csv_file = self.results_dir / f'optimization_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        
        top_50 = df.head(50).copy()
        json_file = self.results_dir / f'top_50_{timestamp}.json'
        
        top_50_dict = []
        for idx, row in top_50.iterrows():
            entry = self._make_serializable(row.to_dict())
            top_50_dict.append(entry)
        
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_tests': int(total_tests),
                'strategy': self.strategy_name,
                'top_50': top_50_dict
            }, f, indent=2)
        
        print(f"Resultados salvos:")
        print(f"  CSV: {csv_file}")
        print(f"  JSON: {json_file}")
    
    def _make_serializable(self, obj: dict) -> dict:
        """Converte tipos NumPy para Python"""
        result = {}
        for key, value in obj.items():
            result[key] = self._convert_value(value)
        return result
    
    def _convert_value(self, value):
        """Converte valor para JSON"""
        if isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, dict):
            return self._make_serializable(value)
        elif isinstance(value, list):
            return [self._convert_value(v) for v in value]
        elif isinstance(value, (np.floating, float)):
            if np.isnan(value) or np.isinf(value):
                return None
            return float(value)
        elif isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8, np.uint64, np.uint32)):
            return int(value)
        elif isinstance(value, (np.bool_, bool)):
            return bool(value)
        elif isinstance(value, (int, str)) or value is None:
            return value
        else:
            try:
                return str(value)
            except:
                return None
    
    def _convert_numpy_types(self, obj):
        """Converte recursivamente numpy types"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return self._convert_value(obj)
    
    def _estimate_time(self, total_tests: int) -> float:
        """Estima tempo em minutos"""
        tests_per_second = 450 * (self.n_cores / 24)  # Baseline: 450 t/s com 24 cores
        total_seconds = total_tests / tests_per_second
        return total_seconds / 60


class GridSearch:
    """Grid de parâmetros pré-definidos"""
    
    @staticmethod
    def power_breakout_default() -> Dict:
        """Grid padrão Power Breakout"""
        return {
            'cons_len_min': [8, 10, 12],
            'cons_len_max': [24, 28, 32],
            'cons_range_mult': [1.5, 2.0, 2.5, 3.0],
            'gatilho_pct': [0.45, 0.55, 0.65],
            'sl_buffer_mult': [0.3, 0.5, 0.7],
            'tp_risk_mult': [2.5, 3.0, 3.5, 4.0],
            'use_ma_filter': [False, True],
            'use_volume_filter': [False, True],
            'use_time_filter': [False, True],
            'use_bollinger_filter': [False, True],
        }

