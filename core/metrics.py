"""
Módulo de Cálculo de Métricas

Calcula todas as métricas de performance de backtesting
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional


class MetricsCalculator:
    """
    Calcula métricas de performance de trading
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Args:
            risk_free_rate: Taxa livre de risco anual (ex: 0.1 = 10%)
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_all(self, trades: List[Dict]) -> Dict:
        """
        Calcula todas as métricas
        
        Args:
            trades: Lista de trades com 'pnl', 'type', 'exit_reason', etc.
        
        Returns:
            Dict com todas as métricas
        """
        if not trades:
            return self._empty_metrics()
        
        trades_df = pd.DataFrame(trades)
        
        # Retornos
        returns = trades_df['pnl'].values
        
        # Métricas básicas
        total_return = returns.sum()
        total_trades = len(trades)
        
        winning_trades = trades_df[trades_df['pnl'] > 0]
        losing_trades = trades_df[trades_df['pnl'] < 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0
        avg_loss = losing_trades['pnl'].mean() if len(losing_trades) > 0 else 0
        
        # Profit Factor
        gross_profit = winning_trades['pnl'].sum() if len(winning_trades) > 0 else 0
        gross_loss = abs(losing_trades['pnl'].sum()) if len(losing_trades) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss != 0 else 0
        
        # Sharpe Ratio
        sharpe = self._calculate_sharpe(returns)
        
        # Sortino Ratio
        sortino = self._calculate_sortino(returns)
        
        # Max Drawdown
        equity_curve = np.cumsum(returns)
        max_dd, max_dd_pct = self._calculate_max_drawdown(equity_curve)
        
        # Consecutive wins/losses
        max_consecutive_wins = self._max_consecutive(trades_df, 'win')
        max_consecutive_losses = self._max_consecutive(trades_df, 'loss')
        
        # Expectancy
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # LONG vs SHORT
        long_trades = trades_df[trades_df['type'] == 'LONG']
        short_trades = trades_df[trades_df['type'] == 'SHORT']
        
        # SL vs TP
        sl_trades = trades_df[trades_df.get('exit_reason', '') == 'SL']
        tp_trades = trades_df[trades_df.get('exit_reason', '') == 'TP']
        
        return {
            # Retorno
            'total_return': total_return,
            'total_return_pct': (total_return / 10000) * 100 if total_return != 0 else 0,
            
            # Trades
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            
            # Médias
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_trade': returns.mean(),
            
            # Performance
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            
            # Drawdown
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            
            # Consecutivos
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            
            # LONG vs SHORT
            'long_trades': len(long_trades),
            'long_win_rate': len(long_trades[long_trades['pnl'] > 0]) / len(long_trades) if len(long_trades) > 0 else 0,
            'long_pnl': long_trades['pnl'].sum() if len(long_trades) > 0 else 0,
            
            'short_trades': len(short_trades),
            'short_win_rate': len(short_trades[short_trades['pnl'] > 0]) / len(short_trades) if len(short_trades) > 0 else 0,
            'short_pnl': short_trades['pnl'].sum() if len(short_trades) > 0 else 0,
            
            # SL vs TP
            'sl_count': len(sl_trades),
            'tp_count': len(tp_trades),
            'sl_pct': len(sl_trades) / total_trades if total_trades > 0 else 0,
            'tp_pct': len(tp_trades) / total_trades if total_trades > 0 else 0,
        }
    
    def _calculate_sharpe(self, returns: np.ndarray) -> float:
        """Calcula Sharpe Ratio"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0.0
        
        # Anualizar (assumindo trades diários, ajustar se necessário)
        sharpe = (mean_return - self.risk_free_rate) / std_return
        sharpe_annualized = sharpe * np.sqrt(252)  # 252 dias de trading
        
        return sharpe_annualized
    
    def _calculate_sortino(self, returns: np.ndarray) -> float:
        """Calcula Sortino Ratio (penaliza apenas downside)"""
        if len(returns) < 2:
            return 0.0
        
        mean_return = returns.mean()
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return 0.0
        
        downside_std = downside_returns.std()
        
        if downside_std == 0:
            return 0.0
        
        sortino = (mean_return - self.risk_free_rate) / downside_std
        sortino_annualized = sortino * np.sqrt(252)
        
        return sortino_annualized
    
    def _calculate_max_drawdown(self, equity_curve: np.ndarray) -> tuple:
        """Calcula Max Drawdown absoluto e percentual"""
        if len(equity_curve) == 0:
            return 0.0, 0.0
        
        # Adicionar capital inicial
        equity = 10000 + equity_curve
        
        # Running maximum
        running_max = np.maximum.accumulate(equity)
        
        # Drawdown
        drawdown = equity - running_max
        
        # Max drawdown absoluto
        max_dd = drawdown.min()
        
        # Max drawdown percentual
        max_dd_idx = drawdown.argmin()
        peak_value = running_max[max_dd_idx]
        max_dd_pct = (max_dd / peak_value) * 100 if peak_value != 0 else 0
        
        return max_dd, abs(max_dd_pct)
    
    def _max_consecutive(self, trades_df: pd.DataFrame, trade_type: str) -> int:
        """Calcula sequência máxima de wins ou losses"""
        if trade_type == 'win':
            mask = trades_df['pnl'] > 0
        else:
            mask = trades_df['pnl'] < 0
        
        max_streak = 0
        current_streak = 0
        
        for is_match in mask:
            if is_match:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _empty_metrics(self) -> Dict:
        """Retorna métricas vazias"""
        return {
            'total_return': 0,
            'total_return_pct': 0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_trade': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'profit_factor': 0,
            'expectancy': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'long_trades': 0,
            'long_win_rate': 0,
            'long_pnl': 0,
            'short_trades': 0,
            'short_win_rate': 0,
            'short_pnl': 0,
            'sl_count': 0,
            'tp_count': 0,
            'sl_pct': 0,
            'tp_pct': 0,
        }
    
    def calculate_composite_score(
        self, 
        metrics: Dict,
        weights: Optional[Dict] = None
    ) -> float:
        """
        Calcula score composto ponderado
        
        Args:
            metrics: Dict com métricas
            weights: Pesos personalizados (opcional)
        
        Returns:
            Score composto (0-100)
        """
        if weights is None:
            weights = {
                'sharpe': 0.30,
                'win_rate': 0.20,
                'profit_factor': 0.20,
                'total_return': 0.15,
                'max_drawdown': 0.15,
            }
        
        # Normalizar métricas (0-100)
        sharpe_norm = min(100, max(0, metrics['sharpe_ratio'] * 10))  # Sharpe 0-10 -> 0-100
        wr_norm = metrics['win_rate'] * 100  # 0-1 -> 0-100
        pf_norm = min(100, max(0, (metrics['profit_factor'] - 1) * 20))  # PF 1-6 -> 0-100
        ret_norm = min(100, max(0, metrics['total_return_pct']))  # Return direto
        dd_norm = max(0, 100 - metrics['max_drawdown_pct'])  # Inverter (menor DD = melhor)
        
        # Score ponderado
        score = (
            sharpe_norm * weights['sharpe'] +
            wr_norm * weights['win_rate'] +
            pf_norm * weights['profit_factor'] +
            ret_norm * weights['total_return'] +
            dd_norm * weights['max_drawdown']
        )
        
        return score

