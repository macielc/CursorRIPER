"""
Validação Estatística

Testes de permutação, bootstrap e outras validações estatísticas
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from multiprocessing import Pool, cpu_count
from functools import partial

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator


class StatisticalValidator:
    """
    Validação estatística de estratégias de trading
    """
    
    def __init__(self, data: pd.DataFrame, n_cores: int = None, strategy_name: str = 'power_breakout_2_0'):
        """
        Args:
            data: DataFrame com dados de mercado
            n_cores: Número de cores para paralelização
            strategy_name: Nome da estratégia a validar
        """
        self.data = data
        self.n_cores = n_cores if n_cores else min(cpu_count(), 32)
        self.metrics_calc = MetricsCalculator()
        self.strategy_name = strategy_name
    
    def permutation_test(
        self,
        params: Dict,
        n_permutations: int = 1000,
        alpha: float = 0.05
    ) -> Dict:
        """
        Teste de permutação para validar significância estatística
        
        Args:
            params: Parâmetros da estratégia
            n_permutations: Número de permutações
            alpha: Nível de significância (0.05 = 5%)
        
        Returns:
            Dict com resultados do teste
        """
        print(f"Executando teste de permutacao...")
        print(f"  Permutacoes: {n_permutations:,}")
        print(f"  Usando {self.n_cores} cores")
        print()
        
        # 1) Backtest real
        print("  [1/3] Executando backtest real...")
        engine = BacktestEngine(self.data)
        real_result = engine.run_strategy(self.strategy_name, params)
        
        if not real_result['success']:
            return {
                'success': False,
                'error': 'Backtest real falhou',
                'real_result': real_result
            }
        
        # Extrair trades reais
        # Precisamos rodar novamente para pegar os trades
        trades = self._get_trades(params, self.strategy_name)
        
        if len(trades) == 0:
            return {
                'success': False,
                'error': 'Nenhum trade gerado',
                'real_result': real_result
            }
        
        real_returns = np.array([t['pnl'] for t in trades])
        
        real_sharpe = real_result['sharpe_ratio']
        real_total_return = real_result['total_return']
        real_win_rate = real_result['win_rate']
        
        print(f"     Trades: {len(trades)}")
        print(f"     Sharpe: {real_sharpe:.2f}")
        print(f"     Return: {real_total_return:.2f}")
        print(f"     Win Rate: {real_win_rate:.2%}")
        print()
        
        # 2) Executar permutações em paralelo
        print(f"  [2/3] Executando {n_permutations:,} permutacoes...")
        print(f"     Usando {self.n_cores} cores em paralelo...")
        
        perm_func = partial(StatisticalValidator._run_single_permutation, real_returns)
        
        with Pool(self.n_cores) as pool:
            perm_results = pool.map(perm_func, range(n_permutations))
        
        # 3) Calcular p-values
        print("  [3/3] Calculando p-values...")
        
        perm_sharpes = [r['sharpe'] for r in perm_results]
        perm_returns = [r['total_return'] for r in perm_results]
        perm_wrs = [r['win_rate'] for r in perm_results]
        
        # P-value: proporção de permutações >= resultado real
        p_sharpe = np.sum(np.array(perm_sharpes) >= real_sharpe) / n_permutations
        p_return = np.sum(np.array(perm_returns) >= real_total_return) / n_permutations
        p_wr = np.sum(np.array(perm_wrs) >= real_win_rate) / n_permutations
        
        # Conclusões
        is_sharpe_significant = p_sharpe < alpha
        is_return_significant = p_return < alpha
        is_wr_significant = p_wr < alpha
        
        result = {
            'success': True,
            'params': params,
            'real_metrics': {
                'sharpe': real_sharpe,
                'total_return': real_total_return,
                'win_rate': real_win_rate,
                'total_trades': len(trades)
            },
            'permutation_stats': {
                'sharpe_mean': np.mean(perm_sharpes),
                'sharpe_std': np.std(perm_sharpes),
                'return_mean': np.mean(perm_returns),
                'return_std': np.std(perm_returns),
                'wr_mean': np.mean(perm_wrs),
                'wr_std': np.std(perm_wrs)
            },
            'p_values': {
                'sharpe': p_sharpe,
                'total_return': p_return,
                'win_rate': p_wr
            },
            'significance': {
                'sharpe': is_sharpe_significant,
                'total_return': is_return_significant,
                'win_rate': is_wr_significant,
                'alpha': alpha
            },
            'n_permutations': n_permutations
        }
        
        print()
        print("  Resultados:")
        print(f"    Sharpe: p={p_sharpe:.4f} {'[OK] SIGNIFICATIVO' if is_sharpe_significant else '[X] NAO SIGNIFICATIVO'}")
        print(f"    Return: p={p_return:.4f} {'[OK] SIGNIFICATIVO' if is_return_significant else '[X] NAO SIGNIFICATIVO'}")
        print(f"    Win Rate: p={p_wr:.4f} {'[OK] SIGNIFICATIVO' if is_wr_significant else '[X] NAO SIGNIFICATIVO'}")
        print()
        
        return result
    
    def _get_trades(self, params: Dict, strategy_name: str = 'power_breakout_2_0') -> List[Dict]:
        """
        Executa backtest e retorna lista de trades
        
        Args:
            params: Parâmetros da estratégia
            strategy_name: Nome da estratégia a usar
        
        Returns:
            Lista de trades
        """
        engine = BacktestEngine(self.data)
        result = engine.run_strategy(strategy_name, params)
        
        if not result.get('success'):
            return []
        
        return result.get('trades', [])
    
    @staticmethod
    def _run_single_permutation(real_returns: np.ndarray, dummy_arg) -> Dict:
        """Executa uma única permutação (função estática para pickling)"""
        # Embaralhar retornos
        permuted_returns = np.random.permutation(real_returns)
        
        # Calcular métricas
        calc = MetricsCalculator()
        
        # Criar trades fake com todos os campos necessários
        fake_trades = [{
            'pnl': pnl,
            'type': 'LONG' if pnl > 0 else 'SHORT',  # Tipo fake baseado no resultado
            'return_pct': pnl,  # Simplificado
            'exit_reason': 'TP' if pnl > 0 else 'SL'  # Fake exit reason
        } for pnl in permuted_returns]
        
        metrics = calc.calculate_all(fake_trades)
        
        return {
            'sharpe': metrics['sharpe_ratio'],
            'total_return': metrics['total_return'],
            'win_rate': metrics['win_rate']
        }
    
    def bootstrap_confidence_intervals(
        self,
        params: Dict,
        n_bootstrap: int = 1000,
        confidence: float = 0.95
    ) -> Dict:
        """
        Bootstrap para intervalos de confiança
        
        Args:
            params: Parâmetros da estratégia
            n_bootstrap: Número de amostras bootstrap
            confidence: Nível de confiança (0.95 = 95%)
        
        Returns:
            Dict com intervalos de confiança
        """
        print(f"Executando bootstrap ({n_bootstrap:,} amostras)...")
        
        # Obter trades
        trades = self._get_trades(params, self.strategy_name)
        
        if len(trades) == 0:
            return {'success': False, 'error': 'Nenhum trade gerado'}
        
        returns = np.array([t['pnl'] for t in trades])
        
        # Executar bootstrap em paralelo
        bootstrap_func = partial(self._run_single_bootstrap, returns)
        
        with Pool(self.n_cores) as pool:
            bootstrap_results = pool.map(bootstrap_func, range(n_bootstrap))
        
        # Calcular intervalos de confiança
        sharpes = [r['sharpe'] for r in bootstrap_results]
        total_returns = [r['total_return'] for r in bootstrap_results]
        win_rates = [r['win_rate'] for r in bootstrap_results]
        
        alpha = 1 - confidence
        lower_pct = (alpha / 2) * 100
        upper_pct = (1 - alpha / 2) * 100
        
        result = {
            'success': True,
            'confidence': confidence,
            'n_bootstrap': n_bootstrap,
            'intervals': {
                'sharpe': {
                    'mean': np.mean(sharpes),
                    'lower': np.percentile(sharpes, lower_pct),
                    'upper': np.percentile(sharpes, upper_pct)
                },
                'total_return': {
                    'mean': np.mean(total_returns),
                    'lower': np.percentile(total_returns, lower_pct),
                    'upper': np.percentile(total_returns, upper_pct)
                },
                'win_rate': {
                    'mean': np.mean(win_rates),
                    'lower': np.percentile(win_rates, lower_pct),
                    'upper': np.percentile(win_rates, upper_pct)
                }
            }
        }
        
        print("  Intervalos de confianca (95%):")
        print(f"    Sharpe: [{result['intervals']['sharpe']['lower']:.2f}, {result['intervals']['sharpe']['upper']:.2f}]")
        print(f"    Return: [{result['intervals']['total_return']['lower']:.2f}, {result['intervals']['total_return']['upper']:.2f}]")
        print(f"    Win Rate: [{result['intervals']['win_rate']['lower']:.2%}, {result['intervals']['win_rate']['upper']:.2%}]")
        print()
        
        return result
    
    @staticmethod
    def _run_single_bootstrap(returns: np.ndarray, dummy_arg) -> Dict:
        """Executa uma única amostra bootstrap"""
        # Resample com reposição
        sample = np.random.choice(returns, size=len(returns), replace=True)
        
        # Calcular métricas
        calc = MetricsCalculator()
        fake_trades = [{'pnl': pnl} for pnl in sample]
        metrics = calc.calculate_all(fake_trades)
        
        return {
            'sharpe': metrics['sharpe_ratio'],
            'total_return': metrics['total_return'],
            'win_rate': metrics['win_rate']
        }

