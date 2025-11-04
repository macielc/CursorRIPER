"""
Otimizador Massivo Paralelo

Otimização de parâmetros usando multiprocessing e checkpointing
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
from tqdm import tqdm
import gc  # OTIMIZACAO: Controle de garbage collector

# SUPRIMIR WARNINGS DE OVERFLOW DO NUMPY
warnings.filterwarnings('ignore', category=RuntimeWarning)
np.seterr(all='ignore')

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator


class MassiveOptimizer:
    """
    Otimizador massivo com paralelização e checkpointing
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        strategy: str = 'power_breakout',
        n_cores: Optional[int] = None,
        checkpoint_every: int = 100000,  # OTIMIZACAO: Checkpoints a cada 100k (menos I/O)
        results_dir: str = 'results/optimization'
    ):
        """
        Args:
            data: DataFrame com dados de mercado
            strategy: Nome da estratégia ('power_breakout', 'inside_bar', etc)
            n_cores: Número de cores (None = todos disponíveis)
            checkpoint_every: Salvar checkpoint a cada N testes (default: 10000)
            results_dir: Diretório para salvar resultados
        """
        self.data = data
        self.strategy_name = strategy
        
        # CORES: Usar TODOS (RAM agora gerenciada com streaming)
        max_cores = cpu_count()
        if n_cores:
            self.n_cores = n_cores
        else:
            # Usar TODOS os cores (RAM gerenciada com streaming + limpeza)
            self.n_cores = max_cores
        
        print(f"[PERFORMANCE] Cores disponiveis: {max_cores} | Usando: {self.n_cores} (100% CPU - RAM gerenciada)")
        
        # CHECKPOINT A CADA 100000 TESTES (reduzir I/O overhead)
        self.checkpoint_every = 100000
        
        # DIRETORIO UNICO POR EXECUCAO: timestamp para organizar
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{strategy}_{timestamp}"
        self.results_dir = Path(results_dir) / self.run_id
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[ORGANIZACAO] Diretorio desta execucao: {self.results_dir}")
        
        self.metrics_calc = MetricsCalculator()
        
        # Carregar estratégia para obter grid
        self._load_strategy_class()
    
    def _load_strategy_class(self):
        """Carrega a classe da estratégia usando auto-discovery"""
        import sys
        from pathlib import Path
        
        # Adicionar strategies ao path
        strategies_path = Path(__file__).parent.parent / 'strategies'
        if str(strategies_path) not in sys.path:
            sys.path.insert(0, str(strategies_path))
        
        # Importar auto-discovery
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
        Executa otimização massiva
        
        Args:
            param_grid: Dict com ranges de parâmetros
            top_n: Número de melhores setups a retornar
            resume: Se True, tenta retomar de checkpoint
            max_tests: Limite máximo de testes (None = todas combinações)
        
        Returns:
            DataFrame com top N resultados
        """
        print("="*80)
        print("MACTESTER - OTIMIZACAO MASSIVA")
        print("="*80)
        print(f"Estrategia: {self.strategy_name}")
        print(f"Cores: {self.n_cores} (100% CPU - PERFORMANCE MAXIMA)")
        print(f"Checkpoint a cada: {self.checkpoint_every:,} testes")
        print()
        
        # LIMPAR CHECKPOINTS ANTIGOS SE NAO FOR RESUME
        if not resume:
            self._clear_checkpoints()
        
        # 1) Gerar combinações de parâmetros
        combinations = self._generate_combinations(param_grid, max_combinations=max_tests)
        total_tests = len(combinations)
        
        print(f"Total de combinacoes: {total_tests:,}")
        print(f"Tempo estimado: {self._estimate_time(total_tests)} minutos")
        print()
        
        # 2) Verificar checkpoint (se resume=True)
        results = []
        start_idx = 0
        
        if resume:
            results, start_idx = self._load_checkpoint()
            if start_idx > 0:
                print(f"Retomando do checkpoint: {start_idx:,} testes ja concluidos")
                print()
        
        # 3) Executar testes em paralelo COM BARRA UNICA
        print("Iniciando otimizacao...")
        print()
        
        # WARM-UP NUMBA: Pre-compilar funcoes antes do multiprocessing
        # Evita recompilacoes durante os testes (primeira execucao demora muito)
        if self.strategy_name == 'barra_elefante':
            print("Aquecendo funcoes Numba...")
            try:
                # Importar funcao de warm-up da estrategia
                from strategies.barra_elefante.strategy import warmup_numba
                warmup_numba()
                print("Numba compilado com sucesso!")
                print()
            except Exception as e:
                print(f"AVISO: Falha no warm-up Numba: {e}")
                print()
        
        # OTIMIZACAO: Desabilitar garbage collector durante testes
        gc.disable()
        
        start_time = time.time()
        
        # Executar TODOS de uma vez com barra única - OTIMIZADO PARA MEMORIA
        # maxtasksperchild=2000: Reciclar workers FREQUENTE para controlar RAM
        # Trade-off: pequeno overhead vs RAM controlada
        with Pool(self.n_cores, maxtasksperchild=2000) as pool:
            func = partial(self._run_single_test, self.data, self.strategy_name)
            
            # WARM-UP DOS WORKERS: Cada worker precisa compilar Numba na primeira vez
            print("\n" + "="*80)
            print(f"AQUECENDO {self.n_cores} WORKERS (Compilacao JIT Numba)...")
            print("="*80)
            sys.stdout.flush()
            
            # Criar parametros dummy para warm-up (um por worker)
            dummy_params = [combinations[0] for _ in range(self.n_cores)]
            
            # Executar warm-up em paralelo (cada worker compila uma vez)
            warmup_start = time.time()
            list(pool.map(func, dummy_params, chunksize=1))
            warmup_time = time.time() - warmup_start
            
            print(f"Workers aquecidos em {warmup_time:.1f}s!")
            print()
            sys.stdout.flush()
            
            print("="*80)
            print("INICIANDO PROCESSAMENTO")
            print("="*80)
            sys.stdout.flush()
            
            # PROCESSAR TUDO DE UMA VEZ
            batch = combinations[start_idx:]
            
            # CHUNKSIZE OTIMIZADO: Balance entre feedback e overhead IPC
            optimal_chunksize = 2000  # Sweet spot: feedback a cada ~1s + baixo overhead
            print(f"Chunksize: {optimal_chunksize}")
            print(f"Total de testes: {total_tests:,}")
            print()
            print("Aguardando primeiros resultados dos workers...")
            sys.stdout.flush()
            
            # BUFFER: Acumular 10k em RAM, depois flush em disco
            results_file = self.results_dir / "all_results_stream.jsonl"
            f_stream = open(results_file, 'w', buffering=8*1024*1024)  # Buffer 8MB
            
            print("[BUFFER] 10k em RAM -> Flush disco | Workers reciclados a cada 2k")
            print("[DEBUG] Entrando no loop...", flush=True)
            sys.stdout.flush()
            
            counter = 0
            last_print = time.time()
            buffer = []  # Buffer temporário
            
            for result in pool.imap_unordered(func, batch, chunksize=optimal_chunksize):
                if counter == 0:
                    print("[DEBUG] PRIMEIRO resultado recebido!", flush=True)
                
                # Acumular no buffer (SEM I/O ainda)
                buffer.append(result)
                counter += 1
                
                # FLUSH BUFFER a cada 10k: Escrever tudo de uma vez + Limpar RAM
                if len(buffer) >= 10000:
                    # Escrever batch inteiro de uma vez
                    for res in buffer:
                        res_json = self._convert_numpy_types(res)
                        f_stream.write(json.dumps(res_json) + '\n')
                    
                    f_stream.flush()
                    buffer.clear()  # LIMPAR buffer
                    gc.collect()  # Forçar coleta de lixo
                    print(f"[FLUSH] {counter:,} salvos | RAM liberada", flush=True)
                
                # PRINT A CADA 1000 testes OU a cada 10 segundos
                current_time = time.time()
                if counter % 1000 == 0 or (current_time - last_print) >= 10:
                    elapsed = current_time - start_time
                    velocity = counter / elapsed if elapsed > 0 else 0
                    progress_pct = (counter / total_tests) * 100
                    remaining = total_tests - counter
                    eta_sec = remaining / velocity if velocity > 0 else 0
                    eta_min = eta_sec / 60
                    
                    print(f"[{counter:,}/{total_tests:,}] {progress_pct:.1f}% | {velocity:.0f} t/s | ETA: {eta_min:.1f}min", flush=True)
                    last_print = current_time
            
            # Flush final do buffer restante
            if buffer:
                for res in buffer:
                    res_json = self._convert_numpy_types(res)
                    f_stream.write(json.dumps(res_json) + '\n')
                f_stream.flush()
                buffer.clear()
            
            # Fechar arquivo
            f_stream.close()
            
            print("\n" + "="*80)
            print(f"PROCESSAMENTO CONCLUIDO: {total_tests:,} testes")
            print("="*80)
            sys.stdout.flush()
            
            # SEM CHECKPOINT (evita travadas)
        
        # OTIMIZACAO: Reabilitar garbage collector e forcar coleta
        gc.enable()
        gc.collect()
        
        print()
        
        # 4) Carregar TODOS os resultados do stream
        print(f"\nCarregando resultados do stream...")
        results_file = self.results_dir / "all_results_stream.jsonl"
        all_results = []
        
        with open(results_file, 'r') as f:
            for line in f:
                all_results.append(json.loads(line.strip()))
        
        print(f"Carregados {len(all_results):,} resultados do disco!")
        print()
        
        # 5) Processar resultados
        print(f"Processando e ordenando para Top {top_n}...")
        results_df = self._process_results(all_results, top_n)
        
        # 6) Salvar resultados finais
        self._save_final_results(results_df, total_tests)
        
        print()
        print("="*80)
        print("OTIMIZACAO CONCLUIDA!")
        print("="*80)
        print(f"Total de testes: {total_tests:,}")
        print(f"Tempo total: {(time.time() - start_time)/60:.1f} min")
        print(f"Top {top_n} setups salvos em: {self.results_dir}")
        print()
        
        return results_df
    
    def _generate_combinations(self, param_grid: Dict, max_combinations: int = None) -> List[Dict]:
        """
        Gera combinações de parâmetros
        
        Args:
            param_grid: Grid de parâmetros
            max_combinations: Limite máximo de combinações (None = todas)
        """
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        # Calcular total de combinações possíveis
        total_possible = 1
        for v in values:
            total_possible *= len(v)
        
        # Se max_combinations é menor que o total, fazer amostragem aleatória
        if max_combinations and max_combinations < total_possible:
            print(f"Grid completo tem {total_possible:,} combinacoes")
            print(f"Limitando para {max_combinations:,} combinacoes (amostragem aleatoria)")
            print()
            
            # CORRECAO: Gerar combinações aleatórias SEM criar lista completa
            import random
            random.seed(42)  # Reproduzibilidade
            
            # Gerar combinações aleatórias diretamente
            combinations = []
            used = set()  # Para evitar duplicatas
            
            attempts = 0
            max_attempts = max_combinations * 10  # Limite de tentativas
            
            while len(combinations) < max_combinations and attempts < max_attempts:
                attempts += 1
                
                # Escolher valor aleatório de cada parâmetro
                combination = tuple(random.choice(v) for v in values)
                
                # Se já usamos essa combinação, pular
                if combination in used:
                    continue
                
                used.add(combination)
                param_dict = dict(zip(keys, combination))
                combinations.append(param_dict)
            
            if len(combinations) < max_combinations:
                print(f"AVISO: Conseguiu gerar apenas {len(combinations)} combinacoes unicas")
                
        else:
            # Gerar todas as combinações
            print(f"Gerando todas as {total_possible:,} combinacoes...")
            print()
            
            combinations = []
            for combination in itertools.product(*values):
                param_dict = dict(zip(keys, combination))
                combinations.append(param_dict)
        
        return combinations
    
    def _run_parallel_batch(self, batch: List[Dict]) -> List[Dict]:
        """Executa um batch de testes em paralelo COM BARRA DE PROGRESSO"""
        with Pool(self.n_cores) as pool:
            func = partial(self._run_single_test, self.data, self.strategy_name)
            
            # BARRA DE PROGRESSO VISUAL
            results = list(tqdm(
                pool.imap(func, batch),
                total=len(batch),
                desc=f"Batch de {len(batch)} testes",
                ncols=100,
                unit="test"
            ))
        
        return results
    
    @staticmethod
    def _run_single_test(data: pd.DataFrame, strategy_name: str, params: Dict) -> Dict:
        """Executa um único teste (função estática para pickling)"""
        # SUPRIMIR WARNINGS EM CADA WORKER
        import warnings
        warnings.filterwarnings('ignore')
        
        # PERFORMANCE: verbose=False para silenciar logs e acelerar 10x+
        engine = BacktestEngine(data, verbose=False)
        result = engine.run_strategy(strategy_name, params)
        return result
    
    def _process_results(self, results: List[Dict], top_n: int) -> pd.DataFrame:
        """Processa resultados e seleciona top N"""
        # Converter para DataFrame
        df = pd.DataFrame(results)
        
        # Filtrar resultados válidos
        df = df[df['success'] == True].copy()
        
        if len(df) == 0:
            print("AVISO: Nenhum resultado valido encontrado!")
            return pd.DataFrame()
        
        # Calcular score composto
        df['score'] = df.apply(
            lambda row: self.metrics_calc.calculate_composite_score(row.to_dict()),
            axis=1
        )
        
        # Ordenar por score
        df = df.sort_values('score', ascending=False)
        
        # Selecionar top N
        top_df = df.head(top_n).copy()
        
        return top_df
    
    def _save_checkpoint(self, results: List[Dict], iteration: int):
        """Salva checkpoint (APENAS MÉTRICAS, não trades individuais)"""
        checkpoint_dir = self.results_dir / 'checkpoints'
        checkpoint_dir.mkdir(exist_ok=True)
        
        checkpoint_file = checkpoint_dir / f'checkpoint_{iteration}.json'
        
        # Converter para formato serializável E REMOVER TRADES
        serializable_results = []
        for r in results:
            r_copy = self._make_serializable(r)
            
            # CRÍTICO: Remover lista de trades (causa checkpoint de 700+ MB!)
            if 'trades' in r_copy:
                del r_copy['trades']
            
            serializable_results.append(r_copy)
        
        with open(checkpoint_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
    
    def _load_checkpoint(self) -> tuple:
        """Carrega último checkpoint"""
        checkpoint_dir = self.results_dir / 'checkpoints'
        
        if not checkpoint_dir.exists():
            return [], 0
        
        # Encontrar último checkpoint
        checkpoints = list(checkpoint_dir.glob('checkpoint_*.json'))
        
        if not checkpoints:
            return [], 0
        
        # Ordenar por número
        checkpoints.sort(key=lambda p: int(p.stem.split('_')[1]))
        latest = checkpoints[-1]
        
        # Carregar
        with open(latest, 'r') as f:
            results = json.load(f)
        
        iteration = int(latest.stem.split('_')[1])
        
        print(f"Checkpoint carregado: {latest.name}")
        
        return results, iteration
    
    def _save_final_results(self, df: pd.DataFrame, total_tests: int):
        """Salva resultados finais"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV com todos os resultados
        csv_file = self.results_dir / f'optimization_{timestamp}.csv'
        df.to_csv(csv_file, index=False)
        
        # JSON com top 50
        top_50 = df.head(50).copy()
        json_file = self.results_dir / f'top_50_{timestamp}.json'
        
        # Preparar para JSON
        top_50_dict = []
        for idx, row in top_50.iterrows():
            entry = self._make_serializable(row.to_dict())
            top_50_dict.append(entry)
        
        with open(json_file, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'total_tests': int(total_tests),  # Converter numpy.int para Python int
                'strategy': self.strategy_name,
                'top_50': top_50_dict
            }, f, indent=2)
        
        print(f"Resultados salvos:")
        print(f"  CSV: {csv_file}")
        print(f"  JSON: {json_file}")
    
    def _clear_checkpoints(self):
        """Limpa checkpoints antigos DE VERDADE (deleta tudo e recria)"""
        import shutil
        
        checkpoint_dir = self.results_dir / 'checkpoints'
        
        # DELETAR TUDO - usa shutil.rmtree que FUNCIONA de verdade
        if checkpoint_dir.exists():
            try:
                shutil.rmtree(checkpoint_dir)
                print(f"[LIMPEZA] Diretorio {checkpoint_dir} deletado completamente")
            except Exception as e:
                print(f"[ERRO] Falha ao deletar checkpoints: {e}")
        
        # RECRIAR diretorio vazio
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        print(f"[LIMPEZA] Diretorio de checkpoints recriado vazio")
    
    def _make_serializable(self, obj: dict) -> dict:
        """Converte tipos NumPy para tipos Python nativos - RECURSIVO"""
        result = {}
        for key, value in obj.items():
            result[key] = self._convert_value(value)
        return result
    
    def _convert_value(self, value):
        """Converte um valor único para formato JSON serializável"""
        # Checar arrays PRIMEIRO
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
            # Fallback: tentar converter para string
            try:
                return str(value)
            except:
                return None
    
    def _convert_numpy_types(self, obj):
        """Converte recursivamente todos os numpy types para Python nativos (JSON compatibility)"""
        if isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return self._convert_value(obj)
    
    def _estimate_time(self, total_tests: int) -> float:
        """Estima tempo total em minutos"""
        # Assumir ~100 testes/seg com 32 cores
        tests_per_second = 100 * (self.n_cores / 32)
        total_seconds = total_tests / tests_per_second
        return total_seconds / 60


class GridSearch:
    """
    Grid de parâmetros pré-definidos para diferentes estratégias
    """
    
    @staticmethod
    def power_breakout_default() -> Dict:
        """Grid padrão para Power Breakout - ~10k combinacoes"""
        return {
            'cons_len_min': [8, 10, 12],
            'cons_len_max': [24, 28, 32],
            'cons_range_mult': [1.5, 2.0, 2.5, 3.0],
            'gatilho_pct': [0.45, 0.55, 0.65],
            'sl_buffer_mult': [0.3, 0.5, 0.7],
            'tp_risk_mult': [2.5, 3.0, 3.5, 4.0],
            # Filtros opcionais para v2.1
            'use_ma_filter': [False, True],
            'use_volume_filter': [False, True],
            'use_time_filter': [False, True],
            'use_bollinger_filter': [False, True],
        }
    
    @staticmethod
    def power_breakout_quick() -> Dict:
        """Grid reduzido para testes rápidos (~100 combinações)"""
        return {
            'cons_len_min': [8, 12, 16],
            'cons_len_max': [22, 25, 30],
            'cons_range_mult': [2.0, 3.0, 4.0],
            'gatilho_pct': [0.50, 0.60, 0.70],
            'sl_buffer_mult': [0.3, 0.5, 0.7],
            'tp_risk_mult': [2.5, 3.5, 5.0],
        }
    
    @staticmethod
    def power_breakout_massive() -> Dict:
        """Grid extenso para otimização massiva (~50k combinações)"""
        return {
            'cons_len_min': [6, 8, 10, 12, 14, 16, 18, 20],
            'cons_len_max': [20, 22, 25, 28, 30, 32, 35],
            'cons_range_mult': np.arange(1.0, 5.1, 0.15),
            'gatilho_pct': np.arange(0.35, 0.86, 0.05),
            'sl_buffer_mult': np.arange(0.1, 1.1, 0.05),
            'tp_risk_mult': np.arange(1.5, 8.1, 0.25),
        }

