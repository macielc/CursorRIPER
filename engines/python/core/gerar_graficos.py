"""
MacTester V2.0 - Gerador de Gráficos
Cria visualizações profissionais para análise de estratégias
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from pathlib import Path

# Configurar estilo
sns.set_style("darkgrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class GeradorGraficos:
    """Gera gráficos profissionais para análise de estratégias"""
    
    def __init__(self, trades: List[Dict], df_full: pd.DataFrame, strategy_name: str):
        """
        Args:
            trades: Lista de trades do backtest
            df_full: DataFrame completo com dados de mercado
            strategy_name: Nome da estratégia
        """
        self.trades = trades
        self.df_full = df_full
        self.strategy_name = strategy_name
        self.output_dir = Path('results/graficos')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if len(trades) > 0:
            self.df_trades = self._preparar_dataframe()
        else:
            self.df_trades = pd.DataFrame()
    
    def _preparar_dataframe(self) -> pd.DataFrame:
        """Prepara DataFrame com informações dos trades"""
        df = pd.DataFrame(self.trades)
        df['exit_time'] = df['exit_idx'].apply(lambda idx: self.df_full.iloc[idx]['time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        df['date'] = df['exit_time'].dt.date
        return df.sort_values('exit_time')
    
    def curva_equity(self, save=True):
        """Gera curva de equity (capital acumulado)"""
        if len(self.df_trades) == 0:
            print("Sem trades para plotar curva de equity")
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Equity acumulada
        equity = self.df_trades['pnl'].cumsum()
        ax1.plot(equity.index, equity.values, linewidth=2, color='#2E86AB', label='Equity')
        ax1.fill_between(equity.index, 0, equity.values, alpha=0.3, color='#2E86AB')
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax1.set_title(f'{self.strategy_name} - Curva de Equity', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Número do Trade')
        ax1.set_ylabel('P&L Acumulado (pontos)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        running_max = equity.cummax()
        drawdown = equity - running_max
        ax2.fill_between(drawdown.index, 0, drawdown.values, color='#E63946', alpha=0.6)
        ax2.set_title('Drawdown', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Número do Trade')
        ax2.set_ylabel('Drawdown (pontos)')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f'{self.strategy_name}_equity.png'
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Curva de equity salva: {filepath}")
        
        plt.close()
        return fig
    
    def distribuicao_retornos(self, save=True):
        """Gera histograma de distribuição de retornos"""
        if len(self.df_trades) == 0:
            print("Sem trades para plotar distribuição")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Histograma geral
        axes[0, 0].hist(self.df_trades['pnl'], bins=50, color='#457B9D', alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[0, 0].axvline(x=self.df_trades['pnl'].mean(), color='green', linestyle='--', linewidth=2, label='Média')
        axes[0, 0].set_title('Distribuição de Retornos', fontweight='bold')
        axes[0, 0].set_xlabel('P&L (pontos)')
        axes[0, 0].set_ylabel('Frequência')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Boxplot
        axes[0, 1].boxplot([self.df_trades[self.df_trades['pnl'] > 0]['pnl'],
                            self.df_trades[self.df_trades['pnl'] < 0]['pnl']],
                           labels=['Wins', 'Losses'],
                           patch_artist=True,
                           boxprops=dict(facecolor='#A8DADC'))
        axes[0, 1].axhline(y=0, color='red', linestyle='--', linewidth=1)
        axes[0, 1].set_title('Wins vs Losses', fontweight='bold')
        axes[0, 1].set_ylabel('P&L (pontos)')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Retornos ao longo do tempo
        axes[1, 0].scatter(range(len(self.df_trades)), self.df_trades['pnl'], 
                          c=self.df_trades['pnl'], cmap='RdYlGn', alpha=0.6, s=30)
        axes[1, 0].axhline(y=0, color='black', linestyle='--', linewidth=1)
        axes[1, 0].set_title('Retornos ao Longo do Tempo', fontweight='bold')
        axes[1, 0].set_xlabel('Número do Trade')
        axes[1, 0].set_ylabel('P&L (pontos)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # QQ Plot (normalidade)
        from scipy import stats
        stats.probplot(self.df_trades['pnl'], dist="norm", plot=axes[1, 1])
        axes[1, 1].set_title('Q-Q Plot (Teste de Normalidade)', fontweight='bold')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f'{self.strategy_name}_distribuicao.png'
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Distribuição salva: {filepath}")
        
        plt.close()
        return fig
    
    def heatmap_performance(self, save=True):
        """Gera heatmap de performance por hora e dia da semana"""
        if len(self.df_trades) == 0:
            print("Sem trades para plotar heatmap")
            return None
        
        # Preparar dados
        self.df_trades['hour'] = self.df_trades['exit_time'].dt.hour
        self.df_trades['weekday'] = self.df_trades['exit_time'].dt.dayofweek
        
        # Agrupar por hora e dia
        pivot = self.df_trades.groupby(['weekday', 'hour'])['pnl'].mean().unstack(fill_value=0)
        
        fig, ax = plt.subplots(figsize=(16, 6))
        
        sns.heatmap(pivot, annot=True, fmt='.0f', cmap='RdYlGn', center=0,
                    linewidths=0.5, cbar_kws={'label': 'P&L Médio (pontos)'},
                    ax=ax)
        
        ax.set_title(f'{self.strategy_name} - Performance por Hora e Dia', 
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Hora do Dia')
        ax.set_ylabel('Dia da Semana')
        ax.set_yticklabels(['Seg', 'Ter', 'Qua', 'Qui', 'Sex'], rotation=0)
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f'{self.strategy_name}_heatmap.png'
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Heatmap salvo: {filepath}")
        
        plt.close()
        return fig
    
    def analise_drawdown_detalhada(self, save=True):
        """Análise detalhada de drawdowns"""
        if len(self.df_trades) == 0:
            print("Sem trades para analisar drawdown")
            return None
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 10))
        
        # Calcular equity e drawdown
        equity = self.df_trades['pnl'].cumsum()
        running_max = equity.cummax()
        drawdown = equity - running_max
        drawdown_pct = (drawdown / running_max * 100).fillna(0)
        
        # Gráfico 1: Equity e máximo histórico
        axes[0].plot(equity.index, equity.values, linewidth=2, color='#2E86AB', label='Equity')
        axes[0].plot(equity.index, running_max.values, linewidth=2, color='green', 
                    linestyle='--', label='Máximo Histórico', alpha=0.7)
        axes[0].fill_between(equity.index, equity.values, running_max.values, 
                            color='#E63946', alpha=0.3)
        axes[0].set_title('Equity vs Máximo Histórico', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Número do Trade')
        axes[0].set_ylabel('P&L (pontos)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Gráfico 2: Drawdown em %
        axes[1].fill_between(drawdown_pct.index, 0, drawdown_pct.values, 
                            color='#E63946', alpha=0.6)
        axes[1].axhline(y=-10, color='orange', linestyle='--', linewidth=1, label='10% DD')
        axes[1].axhline(y=-20, color='red', linestyle='--', linewidth=1, label='20% DD')
        axes[1].set_title('Drawdown Percentual', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Número do Trade')
        axes[1].set_ylabel('Drawdown (%)')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f'{self.strategy_name}_drawdown.png'
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Análise de drawdown salva: {filepath}")
        
        plt.close()
        return fig
    
    def retornos_mensais(self, save=True):
        """Gráfico de retornos mensais"""
        if len(self.df_trades) == 0:
            print("Sem trades para plotar retornos mensais")
            return None
        
        # Agrupar por mês
        self.df_trades['year_month'] = self.df_trades['exit_time'].dt.to_period('M')
        monthly = self.df_trades.groupby('year_month')['pnl'].sum()
        
        fig, ax = plt.subplots(figsize=(14, 6))
        
        colors = ['#2E86AB' if x > 0 else '#E63946' for x in monthly.values]
        ax.bar(range(len(monthly)), monthly.values, color=colors, alpha=0.7, edgecolor='black')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax.set_title(f'{self.strategy_name} - Retornos Mensais', fontsize=14, fontweight='bold')
        ax.set_xlabel('Mês')
        ax.set_ylabel('P&L (pontos)')
        ax.set_xticks(range(len(monthly)))
        ax.set_xticklabels([str(x) for x in monthly.index], rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        
        if save:
            filepath = self.output_dir / f'{self.strategy_name}_retornos_mensais.png'
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"Retornos mensais salvos: {filepath}")
        
        plt.close()
        return fig
    
    def gerar_todos_graficos(self):
        """Gera todos os gráficos de uma vez"""
        print(f"\nGerando gráficos para {self.strategy_name}...")
        print("-" * 80)
        
        self.curva_equity()
        self.distribuicao_retornos()
        self.heatmap_performance()
        self.analise_drawdown_detalhada()
        self.retornos_mensais()
        
        print("-" * 80)
        print(f"Todos os gráficos salvos em: {self.output_dir}\n")

