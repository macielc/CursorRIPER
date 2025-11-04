"""
MacTester - Pipeline de Validação Pré-Live Trading

Módulos principais para validação rigorosa de estratégias.
"""

__version__ = "1.0.0"
__author__ = "MacTester Team"

from .data_loader import DataLoader
from .metrics import MetricsCalculator
from .backtest_engine import BacktestEngine
from .optimizer import MassiveOptimizer, GridSearch
from .statistical import StatisticalValidator
from .walkforward import WalkForwardAnalyzer
from .reporter import ReportGenerator
from .strategy_base import StrategyBase, PowerBreakoutStrategy, InsideBarStrategy

__all__ = [
    'DataLoader',
    'MetricsCalculator',
    'BacktestEngine',
    'MassiveOptimizer',
    'GridSearch',
    'StatisticalValidator',
    'WalkForwardAnalyzer',
    'ReportGenerator',
    'StrategyBase',
    'PowerBreakoutStrategy',
    'InsideBarStrategy',
]

