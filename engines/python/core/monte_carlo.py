"""
MacTester V2.0 - Simulação Monte Carlo
Valida robustez estatística embaralhando ordem dos trades
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from tqdm import tqdm
from multiprocessing import Pool, cpu_count


class MonteCarloSimulation:
    """Simulação Monte Carlo para validação estatística"""
    
    def __init__(self, trades: List[Dict], n_simulacoes: int = 10000):
        """
        Args:
            trades: Lista de trades do backtest
            n_simulacoes: Número de simulações (default: 10,000)
        """
        self.trades = trades
        self.n_simulacoes = n_simulacoes
        self.df_trades = pd.DataFrame(trades) if len(trades) > 0 else pd.DataFrame()
        self.resultados = None
    
    def simular(self, multicore: bool = True) -> Dict:
        """
        Executa simulação Monte Carlo embaralhando ordem dos trades
        
        Args:
            multicore: Usar multiprocessing (Windows requires if __name__ == '__main__')
        
        Returns:
            Dict com estatísticas das simulações
        """
        if len(self.df_trades) == 0:
            return {'erro': 'Nenhum trade para simular'}
        
        # Extrair retornos dos trades
        retornos = self.df_trades['pnl'].values
        
        print(f"\nRodando {self.n_simulacoes:,} simulações Monte Carlo...")
        print(f"Trades: {len(retornos)}")
        print(f"Multicore: {'Sim' if multicore else 'Não'}\n")
        
        if multicore and __name__ == '__main__':
            # Multicore
            with Pool(cpu_count()) as pool:
                resultados = list(tqdm(
                    pool.imap(self._simular_single, range(self.n_simulacoes)),
                    total=self.n_simulacoes,
                    desc="Monte Carlo",
                    ncols=80
                ))
        else:
            # Single core
            resultados = []
            for i in tqdm(range(self.n_simulacoes), desc="Monte Carlo", ncols=80):
                resultados.append(self._simular_single(i))
        
        # Processar resultados
        self.resultados = pd.DataFrame(resultados)
        
        # Calcular estatísticas
        return self._calcular_estatisticas()
    
    def _simular_single(self, seed: int) -> Dict:
        """Executa uma única simulação"""
        np.random.seed(seed)
        
        # Embaralhar ordem dos trades
        retornos_embaralhados = np.random.permutation(self.df_trades['pnl'].values)
        
        # Calcular métricas
        equity = np.cumsum(retornos_embaralhados)
        running_max = np.maximum.accumulate(equity)
        drawdown = equity - running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        wins = np.sum(retornos_embaralhados > 0)
        win_rate = wins / len(retornos_embaralhados)
        
        # Sharpe (simplificado - anualizado assumindo 252 dias)
        if retornos_embaralhados.std() > 0:
            sharpe = (retornos_embaralhados.mean() / retornos_embaralhados.std()) * np.sqrt(252)
        else:
            sharpe = 0
        
        return {
            'final_equity': equity[-1],
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'sharpe': sharpe,
            'max_equity': equity.max(),
            'min_equity': equity.min()
        }
    
    def _calcular_estatisticas(self) -> Dict:
        """Calcula estatísticas das simulações"""
        if self.resultados is None or len(self.resultados) == 0:
            return {}
        
        # Estatísticas do backtest original
        equity_original = self.df_trades['pnl'].cumsum().values[-1]
        max_dd_original = (self.df_trades['pnl'].cumsum() - 
                          self.df_trades['pnl'].cumsum().cummax()).min()
        
        # Calcular percentis
        stats = {
            # Equity final
            'equity_original': equity_original,
            'equity_mean': self.resultados['final_equity'].mean(),
            'equity_std': self.resultados['final_equity'].std(),
            'equity_p5': self.resultados['final_equity'].quantile(0.05),
            'equity_p25': self.resultados['final_equity'].quantile(0.25),
            'equity_p50': self.resultados['final_equity'].quantile(0.50),
            'equity_p75': self.resultados['final_equity'].quantile(0.75),
            'equity_p95': self.resultados['final_equity'].quantile(0.95),
            
            # Drawdown máximo
            'max_dd_original': max_dd_original,
            'max_dd_mean': self.resultados['max_drawdown'].mean(),
            'max_dd_std': self.resultados['max_drawdown'].std(),
            'max_dd_p5': self.resultados['max_drawdown'].quantile(0.05),
            'max_dd_p50': self.resultados['max_drawdown'].quantile(0.50),
            'max_dd_p95': self.resultados['max_drawdown'].quantile(0.95),
            
            # Sharpe
            'sharpe_mean': self.resultados['sharpe'].mean(),
            'sharpe_std': self.resultados['sharpe'].std(),
            'sharpe_p5': self.resultados['sharpe'].quantile(0.05),
            'sharpe_p95': self.resultados['sharpe'].quantile(0.95),
            
            # Probabilidades
            'prob_equity_positiva': (self.resultados['final_equity'] > 0).mean(),
            'prob_equity_melhor_original': (self.resultados['final_equity'] >= equity_original).mean(),
            'prob_dd_pior_original': (self.resultados['max_drawdown'] <= max_dd_original).mean(),
        }
        
        return stats
    
    def gerar_relatorio(self) -> str:
        """Gera relatório textual das simulações"""
        if self.resultados is None:
            return "Execute simular() primeiro!"
        
        stats = self._calcular_estatisticas()
        
        relatorio = []
        relatorio.append("\n" + "="*80)
        relatorio.append("SIMULACAO MONTE CARLO (10,000 ITERACOES)")
        relatorio.append("="*80 + "\n")
        
        relatorio.append("EQUITY FINAL:")
        relatorio.append("-" * 80)
        relatorio.append(f"  Original: {stats['equity_original']:,.0f} pts")
        relatorio.append(f"  Media simulacoes: {stats['equity_mean']:,.0f} pts")
        relatorio.append(f"  Desvio padrao: {stats['equity_std']:,.0f} pts")
        relatorio.append(f"  Percentis:")
        relatorio.append(f"    P5:  {stats['equity_p5']:,.0f} pts")
        relatorio.append(f"    P25: {stats['equity_p25']:,.0f} pts")
        relatorio.append(f"    P50: {stats['equity_p50']:,.0f} pts (mediana)")
        relatorio.append(f"    P75: {stats['equity_p75']:,.0f} pts")
        relatorio.append(f"    P95: {stats['equity_p95']:,.0f} pts")
        relatorio.append(f"  Prob. equity > 0: {stats['prob_equity_positiva']*100:.1f}%")
        relatorio.append(f"  Prob. equity >= original: {stats['prob_equity_melhor_original']*100:.1f}%\n")
        
        relatorio.append("DRAWDOWN MAXIMO:")
        relatorio.append("-" * 80)
        relatorio.append(f"  Original: {stats['max_dd_original']:,.0f} pts")
        relatorio.append(f"  Media simulacoes: {stats['max_dd_mean']:,.0f} pts")
        relatorio.append(f"  Desvio padrao: {stats['max_dd_std']:,.0f} pts")
        relatorio.append(f"  Percentis:")
        relatorio.append(f"    P5:  {stats['max_dd_p5']:,.0f} pts (pior caso 5%)")
        relatorio.append(f"    P50: {stats['max_dd_p50']:,.0f} pts (mediana)")
        relatorio.append(f"    P95: {stats['max_dd_p95']:,.0f} pts (melhor caso 5%)")
        relatorio.append(f"  Prob. DD pior que original: {stats['prob_dd_pior_original']*100:.1f}%\n")
        
        relatorio.append("SHARPE RATIO:")
        relatorio.append("-" * 80)
        relatorio.append(f"  Media simulacoes: {stats['sharpe_mean']:.2f}")
        relatorio.append(f"  Desvio padrao: {stats['sharpe_std']:.2f}")
        relatorio.append(f"  Intervalo 90%: [{stats['sharpe_p5']:.2f}, {stats['sharpe_p95']:.2f}]\n")
        
        relatorio.append("INTERPRETACAO:")
        relatorio.append("-" * 80)
        
        if stats['prob_equity_positiva'] >= 0.95:
            relatorio.append("  Excelente! >95% das simulacoes terminam positivas.")
        elif stats['prob_equity_positiva'] >= 0.80:
            relatorio.append("  Bom! 80-95% das simulacoes terminam positivas.")
        elif stats['prob_equity_positiva'] >= 0.60:
            relatorio.append("  Aceitavel. 60-80% das simulacoes terminam positivas.")
        else:
            relatorio.append("  ALERTA! <60% das simulacoes terminam positivas.")
        
        if abs(stats['max_dd_p5']) > abs(stats['max_dd_original']) * 1.5:
            relatorio.append("  ALERTA! Drawdown pode ser 50% PIOR que o original.")
        elif abs(stats['max_dd_p5']) > abs(stats['max_dd_original']) * 1.2:
            relatorio.append("  Atenção: Drawdown pode ser 20% pior que o original.")
        else:
            relatorio.append("  Drawdown dentro do esperado.")
        
        relatorio.append("\n" + "="*80 + "\n")
        
        return "\n".join(relatorio)


def _worker_simular(args):
    """Worker para multiprocessing"""
    seed, retornos = args
    np.random.seed(seed)
    
    retornos_embaralhados = np.random.permutation(retornos)
    equity = np.cumsum(retornos_embaralhados)
    running_max = np.maximum.accumulate(equity)
    drawdown = equity - running_max
    max_drawdown = drawdown.min()
    
    wins = np.sum(retornos_embaralhados > 0)
    win_rate = wins / len(retornos_embaralhados)
    
    if retornos_embaralhados.std() > 0:
        sharpe = (retornos_embaralhados.mean() / retornos_embaralhados.std()) * np.sqrt(252)
    else:
        sharpe = 0
    
    return {
        'final_equity': equity[-1],
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'sharpe': sharpe,
        'max_equity': equity.max(),
        'min_equity': equity.min()
    }

