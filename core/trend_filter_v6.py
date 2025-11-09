"""
Filtro de Tendência V6 - EMA 8 no D1 (SUPER SIMPLES)
=====================================================
Usa apenas EMA 8 no timeframe DIÁRIO para detectar tendência.

Lógica:
- Preço acima EMA 8 (D1) = Permite BUY
- Preço abaixo EMA 8 (D1) = Permite SELL
- Análise GLOBAL (uma vez) ou ROLLING (trade-by-trade)

Autor: MacTester V2.0
Data: 2025-11-08
Versão: 6.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendFilterV6:
    """
    Filtro V6 - EMA 8 no D1
    
    Super simples: Preço vs EMA 8 no diário define a tendência.
    """
    
    def __init__(self, ema_period: int = 8, rolling_window_days: int = None):
        """
        Args:
            ema_period: Período da EMA (default: 8)
            rolling_window_days: Se None, análise GLOBAL. Se número, análise ROLLING.
        """
        self.ema_period = ema_period
        self.rolling_window_days = rolling_window_days
        
        mode = "ROLLING" if rolling_window_days else "GLOBAL"
        logger.info(f"Filtro V6 inicializado: EMA{ema_period} no D1, modo {mode}")
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
    def resample_to_d1(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reamostra M5 para D1"""
        if 'time' in df.columns:
            df_copy = df.set_index('time').copy()
        else:
            df_copy = df.copy()
        
        resampled = df_copy.resample('1D').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum' if 'volume' in df_copy.columns else 'sum'
        }).dropna()
        
        return resampled
    
    def analyze_trend(self, df_m5: pd.DataFrame) -> Dict:
        """
        Analisa tendência usando EMA 8 no D1
        
        Args:
            df_m5: DataFrame M5
            
        Returns:
            Dict com análise
        """
        # Reamostra para D1
        df_d1 = self.resample_to_d1(df_m5)
        
        if len(df_d1) < self.ema_period + 5:
            return {
                'error': f'Poucos dados D1: {len(df_d1)} < {self.ema_period + 5}',
                'allowed_directions': [],
                'is_consolidation': True
            }
        
        close = df_d1['close']
        
        # EMA 8
        ema = self.calculate_ema(close, self.ema_period)
        
        # Últimos valores
        close_current = close.iloc[-1]
        ema_current = ema.iloc[-1] if not ema.empty else 0
        
        # Determina direção
        allowed_directions = []
        
        if close_current > ema_current:
            allowed_directions.append('BUY')
            trend_desc = "ALTA"
        elif close_current < ema_current:
            allowed_directions.append('SELL')
            trend_desc = "BAIXA"
        else:
            trend_desc = "NEUTRO"
        
        logger.info(f"  Close D1: {close_current:.2f}, EMA{self.ema_period}: {ema_current:.2f} => {trend_desc}")
        
        return {
            'allowed_directions': allowed_directions,
            'is_consolidation': len(allowed_directions) == 0,
            'trend_description': trend_desc,
            'close': close_current,
            'ema': ema_current
        }
    
    def should_trade_global(self, df_m5: pd.DataFrame, bar_type: str) -> Tuple[bool, str]:
        """
        Análise GLOBAL (uma vez para todo período)
        
        Args:
            df_m5: DataFrame M5 completo
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo)
        """
        analysis = self.analyze_trend(df_m5)
        
        if 'error' in analysis:
            return False, analysis['error']
        
        if analysis['is_consolidation']:
            return False, "Neutro (preco = EMA)"
        
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type} (EMA{self.ema_period} D1)"
        else:
            allowed = ", ".join(analysis['allowed_directions']) if analysis['allowed_directions'] else "Nenhuma"
            return False, f"Contra tendencia (permitido: {allowed})"
    
    def should_trade_rolling(self, df_m5: pd.DataFrame, trade_time: pd.Timestamp, bar_type: str) -> Tuple[bool, str]:
        """
        Análise ROLLING (janela deslizante)
        
        Args:
            df_m5: DataFrame M5 completo
            trade_time: Timestamp do trade
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo)
        """
        # Define janela
        window_start = trade_time - timedelta(days=self.rolling_window_days)
        
        # Filtra dados da janela
        if 'time' in df_m5.columns:
            df_window = df_m5[(df_m5['time'] > window_start) & (df_m5['time'] <= trade_time)].copy()
        else:
            df_window = df_m5[(df_m5.index > window_start) & (df_m5.index <= trade_time)].copy()
        
        # Analisa
        analysis = self.analyze_trend(df_window)
        
        if 'error' in analysis:
            return False, analysis['error']
        
        if analysis['is_consolidation']:
            return False, "Neutro"
        
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type}"
        else:
            allowed = ", ".join(analysis['allowed_directions']) if analysis['allowed_directions'] else "Nenhuma"
            return False, f"Contra tendencia (permitido: {allowed})"
    
    def should_trade(self, df_m5: pd.DataFrame, trade_time: pd.Timestamp = None, bar_type: str = None) -> Tuple[bool, str]:
        """
        Wrapper que decide se usa análise GLOBAL ou ROLLING
        
        Args:
            df_m5: DataFrame M5
            trade_time: Timestamp do trade (obrigatório se ROLLING)
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo)
        """
        if self.rolling_window_days is None:
            # Modo GLOBAL
            return self.should_trade_global(df_m5, bar_type)
        else:
            # Modo ROLLING
            if trade_time is None:
                return False, "trade_time obrigatorio para modo ROLLING"
            return self.should_trade_rolling(df_m5, trade_time, bar_type)


def main():
    """Teste rápido"""
    print("="*80)
    print("TESTE FILTRO V6 - EMA 8 NO D1")
    print("="*80)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles M5")
    
    # Testa GLOBAL
    print(f"\n{'='*80}")
    print("MODO GLOBAL (analisa periodo completo)")
    print("="*80)
    
    filter_v6_global = TrendFilterV6(ema_period=8, rolling_window_days=None)
    
    for bar_type in ['BUY', 'SELL']:
        can_trade, reason = filter_v6_global.should_trade(df, bar_type=bar_type)
        status = "[OK]" if can_trade else "[X]"
        print(f"  {bar_type}: {status} - {reason}")
    
    # Testa ROLLING
    print(f"\n{'='*80}")
    print("MODO ROLLING (janela 60 dias)")
    print("="*80)
    
    filter_v6_rolling = TrendFilterV6(ema_period=8, rolling_window_days=60)
    
    # Testa com última data
    if 'time' in df.columns:
        last_time = df['time'].max()
    else:
        last_time = df.index.max()
    
    print(f"Última data: {last_time}")
    
    for bar_type in ['BUY', 'SELL']:
        can_trade, reason = filter_v6_rolling.should_trade(df, trade_time=last_time, bar_type=bar_type)
        status = "[OK]" if can_trade else "[X]"
        print(f"  {bar_type}: {status} - {reason}")


if __name__ == "__main__":
    main()

