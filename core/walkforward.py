"""
Walk-Forward Analysis

Análise de robustez temporal através de janelas móveis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

from .backtest_engine import BacktestEngine
from .metrics import MetricsCalculator
from .optimizer import MassiveOptimizer


class WalkForwardAnalyzer:
    """
    Walk-Forward Analysis para validação temporal
    """
    
    def __init__(
        self,
        data: pd.DataFrame,
        train_months: int = 12,
        test_months: int = 3,
        step_months: int = 3,
        top_n: int = 5
    ):
        """
        Args:
            data: DataFrame com dados de mercado
            train_months: Meses para treinamento (in-sample)
            test_months: Meses para teste (out-of-sample)
            step_months: Passo entre janelas
            top_n: Número de melhores setups a testar no OOS
        """
        self.data = data
        self.train_months = train_months
        self.test_months = test_months
        self.step_months = step_months
        self.top_n = top_n
        
        self.metrics_calc = MetricsCalculator()
    
    def run_analysis(
        self,
        param_grid: Dict,
        min_trades: int = 10
    ) -> Dict:
        """
        Executa Walk-Forward Analysis completa
        
        Args:
            param_grid: Grid de parâmetros para otimização
            min_trades: Número mínimo de trades para validar um setup
        
        Returns:
            Dict com resultados da análise
        """
        print("="*80)
        print("WALK-FORWARD ANALYSIS")
        print("="*80)
        print(f"Janela de treino: {self.train_months} meses")
        print(f"Janela de teste: {self.test_months} meses")
        print(f"Passo: {self.step_months} meses")
        print(f"Top N setups: {self.top_n}")
        print()
        
        # 1) Gerar janelas temporais
        windows = self._generate_windows()
        
        print(f"Total de janelas: {len(windows)}")
        print()
        
        # 2) Executar análise em cada janela
        results_per_window = []
        
        for i, (train_start, train_end, test_start, test_end) in enumerate(windows):
            print(f"Janela {i+1}/{len(windows)}")
            print(f"  Treino: {train_start.date()} ate {train_end.date()}")
            print(f"  Teste:  {test_start.date()} ate {test_end.date()}")
            print()
            
            # Executar análise na janela
            window_result = self._analyze_window(
                train_start, train_end,
                test_start, test_end,
                param_grid,
                min_trades
            )
            
            results_per_window.append(window_result)
            
            print()
        
        # 3) Consolidar resultados
        summary = self._consolidate_results(results_per_window)
        
        print("="*80)
        print("RESUMO WALK-FORWARD")
        print("="*80)
        print(f"Janelas analisadas: {len(windows)}")
        print(f"Taxa de sucesso: {summary['success_rate']:.1%}")
        print(f"Sharpe medio OOS: {summary['avg_oos_sharpe']:.2f}")
        print(f"Return medio OOS: {summary['avg_oos_return']:.2f}")
        print(f"Win Rate medio OOS: {summary['avg_oos_wr']:.1%}")
        print()
        
        return {
            'windows': results_per_window,
            'summary': summary
        }
    
    def _generate_windows(self) -> List[Tuple]:
        """Gera janelas de treino/teste"""
        windows = []
        
        data_start = self.data['time'].min()
        data_end = self.data['time'].max()
        
        current_start = data_start
        
        while True:
            # Janela de treino
            train_start = current_start
            train_end = train_start + pd.DateOffset(months=self.train_months)
            
            # Janela de teste
            test_start = train_end
            test_end = test_start + pd.DateOffset(months=self.test_months)
            
            # Verificar se cabe no dataset
            if test_end > data_end:
                break
            
            windows.append((train_start, train_end, test_start, test_end))
            
            # Avançar
            current_start = current_start + pd.DateOffset(months=self.step_months)
        
        return windows
    
    def _analyze_window(
        self,
        train_start: datetime,
        train_end: datetime,
        test_start: datetime,
        test_end: datetime,
        param_grid: Dict,
        min_trades: int
    ) -> Dict:
        """Analisa uma janela específica"""
        
        # 1) Separar dados
        train_data = self.data[
            (self.data['time'] >= train_start) &
            (self.data['time'] < train_end)
        ].copy()
        
        test_data = self.data[
            (self.data['time'] >= test_start) &
            (self.data['time'] < test_end)
        ].copy()
        
        print(f"    Candles treino: {len(train_data)}")
        print(f"    Candles teste: {len(test_data)}")
        
        # 2) Otimizar no período de treino (in-sample)
        print("    Otimizando no periodo de treino...")
        
        optimizer = MassiveOptimizer(
            train_data,
            n_cores=None,
            checkpoint_every=500,
            results_dir='../results/walkforward/temp'
        )
        
        # Usar grid reduzido para velocidade
        from .optimizer import GridSearch
        quick_grid = GridSearch.power_breakout_quick()
        
        top_setups = optimizer.optimize(
            quick_grid,
            top_n=self.top_n,
            resume=False
        )
        
        if len(top_setups) == 0:
            return {
                'success': False,
                'error': 'Nenhum setup encontrado no treino'
            }
        
        # 3) Testar no período OOS (out-of-sample)
        print(f"    Testando top {self.top_n} no periodo OOS...")
        
        oos_results = []
        
        for idx, row in top_setups.iterrows():
            params = row['params']
            
            # Backtest no OOS
            engine = BacktestEngine(test_data)
            oos_result = engine.run_power_breakout(params)
            
            if oos_result['success'] and oos_result['total_trades'] >= min_trades:
                oos_results.append({
                    'params': params,
                    'is_sharpe': row['sharpe_ratio'],
                    'is_return': row['total_return'],
                    'is_wr': row['win_rate'],
                    'oos_sharpe': oos_result['sharpe_ratio'],
                    'oos_return': oos_result['total_return'],
                    'oos_wr': oos_result['win_rate'],
                    'oos_trades': oos_result['total_trades']
                })
        
        # 4) Analisar degradação
        if len(oos_results) > 0:
            avg_oos_sharpe = np.mean([r['oos_sharpe'] for r in oos_results])
            avg_oos_return = np.mean([r['oos_return'] for r in oos_results])
            avg_oos_wr = np.mean([r['oos_wr'] for r in oos_results])
            
            print(f"    OOS Results ({len(oos_results)} setups validos):")
            print(f"      Sharpe medio: {avg_oos_sharpe:.2f}")
            print(f"      Return medio: {avg_oos_return:.2f}")
            print(f"      Win Rate medio: {avg_oos_wr:.1%}")
        else:
            print("    AVISO: Nenhum setup gerou trades suficientes no OOS")
            avg_oos_sharpe = 0
            avg_oos_return = 0
            avg_oos_wr = 0
        
        return {
            'success': len(oos_results) > 0,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': test_start,
            'test_end': test_end,
            'top_setups_is': top_setups.to_dict('records'),
            'oos_results': oos_results,
            'avg_oos_sharpe': avg_oos_sharpe,
            'avg_oos_return': avg_oos_return,
            'avg_oos_wr': avg_oos_wr
        }
    
    def _consolidate_results(self, results: List[Dict]) -> Dict:
        """Consolida resultados de todas as janelas"""
        
        successful_windows = [r for r in results if r['success']]
        
        if len(successful_windows) == 0:
            return {
                'success_rate': 0,
                'avg_oos_sharpe': 0,
                'avg_oos_return': 0,
                'avg_oos_wr': 0
            }
        
        success_rate = len(successful_windows) / len(results)
        
        avg_oos_sharpe = np.mean([r['avg_oos_sharpe'] for r in successful_windows])
        avg_oos_return = np.mean([r['avg_oos_return'] for r in successful_windows])
        avg_oos_wr = np.mean([r['avg_oos_wr'] for r in successful_windows])
        
        # Calcular degradação média (IS vs OOS)
        all_oos = []
        for r in successful_windows:
            all_oos.extend(r['oos_results'])
        
        if len(all_oos) > 0:
            degradation_sharpe = np.mean([
                (o['is_sharpe'] - o['oos_sharpe']) / o['is_sharpe']
                for o in all_oos if o['is_sharpe'] != 0
            ])
            
            degradation_return = np.mean([
                (o['is_return'] - o['oos_return']) / o['is_return']
                for o in all_oos if o['is_return'] != 0
            ])
        else:
            degradation_sharpe = 0
            degradation_return = 0
        
        return {
            'success_rate': success_rate,
            'avg_oos_sharpe': avg_oos_sharpe,
            'avg_oos_return': avg_oos_return,
            'avg_oos_wr': avg_oos_wr,
            'degradation_sharpe': degradation_sharpe,
            'degradation_return': degradation_return,
            'total_windows': len(results),
            'successful_windows': len(successful_windows)
        }

