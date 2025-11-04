"""
MacTester V2.0 - Módulo de Análise Temporal
Analisa performance por hora, dia da semana, mês
"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime


class AnaliseTemporal:
    """Analisa padrões temporais nos trades"""
    
    def __init__(self, trades: List[Dict], df_full: pd.DataFrame):
        """
        Args:
            trades: Lista de trades do backtest
            df_full: DataFrame completo com dados de mercado
        """
        self.trades = trades
        self.df_full = df_full
        self.df_trades = self._preparar_dataframe()
    
    def _preparar_dataframe(self) -> pd.DataFrame:
        """Prepara DataFrame com informações temporais"""
        if len(self.trades) == 0:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.trades)
        
        # Converter índices para timestamps
        df['entry_time'] = df['entry_idx'].apply(lambda idx: self.df_full.iloc[idx]['time'])
        df['exit_time'] = df['exit_idx'].apply(lambda idx: self.df_full.iloc[idx]['time'])
        
        # Converter para datetime
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        # Extrair componentes temporais
        df['entry_hour'] = df['entry_time'].dt.hour
        df['entry_minute'] = df['entry_time'].dt.minute
        df['entry_weekday'] = df['entry_time'].dt.dayofweek  # 0=Segunda, 4=Sexta
        df['entry_weekday_name'] = df['entry_time'].dt.day_name()
        df['entry_month'] = df['entry_time'].dt.month
        df['entry_month_name'] = df['entry_time'].dt.month_name()
        df['entry_year'] = df['entry_time'].dt.year
        
        # Calcular duração do trade
        df['duracao_minutos'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 60
        
        # Classificar resultado
        df['win'] = df['pnl'] > 0
        
        return df
    
    def analisar_por_hora(self) -> pd.DataFrame:
        """Analisa performance por hora do dia"""
        if len(self.df_trades) == 0:
            return pd.DataFrame()
        
        analise = self.df_trades.groupby('entry_hour').agg({
            'pnl': ['count', 'sum', 'mean', 'std'],
            'win': 'mean',
        }).round(2)
        
        analise.columns = ['trades', 'total_pnl', 'avg_pnl', 'std_pnl', 'win_rate']
        analise['win_rate'] = analise['win_rate'] * 100
        
        # Calcular Sharpe por hora (simplificado)
        analise['sharpe'] = (analise['avg_pnl'] / analise['std_pnl']).fillna(0)
        
        return analise.sort_index()
    
    def analisar_por_dia_semana(self) -> pd.DataFrame:
        """Analisa performance por dia da semana"""
        if len(self.df_trades) == 0:
            return pd.DataFrame()
        
        analise = self.df_trades.groupby('entry_weekday_name').agg({
            'pnl': ['count', 'sum', 'mean', 'std'],
            'win': 'mean',
        }).round(2)
        
        analise.columns = ['trades', 'total_pnl', 'avg_pnl', 'std_pnl', 'win_rate']
        analise['win_rate'] = analise['win_rate'] * 100
        analise['sharpe'] = (analise['avg_pnl'] / analise['std_pnl']).fillna(0)
        
        # Ordenar por dia da semana
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        analise = analise.reindex([d for d in dias_ordem if d in analise.index])
        
        return analise
    
    def analisar_por_mes(self) -> pd.DataFrame:
        """Analisa performance por mês"""
        if len(self.df_trades) == 0:
            return pd.DataFrame()
        
        analise = self.df_trades.groupby('entry_month_name').agg({
            'pnl': ['count', 'sum', 'mean'],
            'win': 'mean',
        }).round(2)
        
        analise.columns = ['trades', 'total_pnl', 'avg_pnl', 'win_rate']
        analise['win_rate'] = analise['win_rate'] * 100
        
        return analise
    
    def analisar_duracao_trades(self) -> Dict:
        """Analisa duração dos trades"""
        if len(self.df_trades) == 0:
            return {}
        
        return {
            'duracao_media_min': self.df_trades['duracao_minutos'].mean(),
            'duracao_mediana_min': self.df_trades['duracao_minutos'].median(),
            'duracao_min_min': self.df_trades['duracao_minutos'].min(),
            'duracao_max_min': self.df_trades['duracao_minutos'].max(),
            'duracao_std_min': self.df_trades['duracao_minutos'].std(),
        }
    
    def identificar_melhores_periodos(self) -> Dict:
        """Identifica os melhores períodos para operar"""
        if len(self.df_trades) == 0:
            return {}
        
        # Por hora
        por_hora = self.analisar_por_hora()
        melhor_hora = por_hora.sort_values('sharpe', ascending=False).head(1)
        pior_hora = por_hora.sort_values('sharpe', ascending=True).head(1)
        
        # Por dia
        por_dia = self.analisar_por_dia_semana()
        melhor_dia = por_dia.sort_values('sharpe', ascending=False).head(1)
        pior_dia = por_dia.sort_values('sharpe', ascending=True).head(1)
        
        return {
            'melhor_hora': {
                'hora': melhor_hora.index[0],
                'sharpe': melhor_hora['sharpe'].values[0],
                'win_rate': melhor_hora['win_rate'].values[0],
                'trades': melhor_hora['trades'].values[0]
            },
            'pior_hora': {
                'hora': pior_hora.index[0],
                'sharpe': pior_hora['sharpe'].values[0],
                'win_rate': pior_hora['win_rate'].values[0],
                'trades': pior_hora['trades'].values[0]
            },
            'melhor_dia': {
                'dia': melhor_dia.index[0],
                'sharpe': melhor_dia['sharpe'].values[0],
                'win_rate': melhor_dia['win_rate'].values[0],
                'trades': melhor_dia['trades'].values[0]
            },
            'pior_dia': {
                'dia': pior_dia.index[0],
                'sharpe': pior_dia['sharpe'].values[0],
                'win_rate': pior_dia['win_rate'].values[0],
                'trades': pior_dia['trades'].values[0]
            }
        }
    
    def gerar_relatorio_temporal(self) -> str:
        """Gera relatório textual completo"""
        if len(self.df_trades) == 0:
            return "Nenhum trade para analisar."
        
        relatorio = []
        relatorio.append("\n" + "="*80)
        relatorio.append("ANALISE TEMPORAL DETALHADA")
        relatorio.append("="*80 + "\n")
        
        # Análise por hora
        relatorio.append("POR HORA DO DIA:")
        relatorio.append("-" * 80)
        por_hora = self.analisar_por_hora()
        relatorio.append(por_hora.to_string())
        relatorio.append("\n")
        
        # Análise por dia da semana
        relatorio.append("POR DIA DA SEMANA:")
        relatorio.append("-" * 80)
        por_dia = self.analisar_por_dia_semana()
        relatorio.append(por_dia.to_string())
        relatorio.append("\n")
        
        # Duração dos trades
        relatorio.append("DURACAO DOS TRADES:")
        relatorio.append("-" * 80)
        duracao = self.analisar_duracao_trades()
        relatorio.append(f"Media: {duracao['duracao_media_min']:.1f} minutos")
        relatorio.append(f"Mediana: {duracao['duracao_mediana_min']:.1f} minutos")
        relatorio.append(f"Min-Max: {duracao['duracao_min_min']:.1f} - {duracao['duracao_max_min']:.1f} minutos")
        relatorio.append("\n")
        
        # Melhores períodos
        relatorio.append("MELHORES/PIORES PERIODOS:")
        relatorio.append("-" * 80)
        periodos = self.identificar_melhores_periodos()
        
        relatorio.append(f"Melhor hora: {periodos['melhor_hora']['hora']}h "
                        f"(Sharpe {periodos['melhor_hora']['sharpe']:.2f}, "
                        f"WR {periodos['melhor_hora']['win_rate']:.1f}%, "
                        f"{periodos['melhor_hora']['trades']} trades)")
        
        relatorio.append(f"Pior hora: {periodos['pior_hora']['hora']}h "
                        f"(Sharpe {periodos['pior_hora']['sharpe']:.2f}, "
                        f"WR {periodos['pior_hora']['win_rate']:.1f}%, "
                        f"{periodos['pior_hora']['trades']} trades)")
        
        relatorio.append(f"\nMelhor dia: {periodos['melhor_dia']['dia']} "
                        f"(Sharpe {periodos['melhor_dia']['sharpe']:.2f}, "
                        f"WR {periodos['melhor_dia']['win_rate']:.1f}%, "
                        f"{periodos['melhor_dia']['trades']} trades)")
        
        relatorio.append(f"Pior dia: {periodos['pior_dia']['dia']} "
                        f"(Sharpe {periodos['pior_dia']['sharpe']:.2f}, "
                        f"WR {periodos['pior_dia']['win_rate']:.1f}%, "
                        f"{periodos['pior_dia']['trades']} trades)")
        
        relatorio.append("\n" + "="*80 + "\n")
        
        return "\n".join(relatorio)

