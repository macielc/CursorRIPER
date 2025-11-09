"""
Filtro de Tendência V5 - ROLLING WINDOW (Janela Deslizante)
=============================================================
Analisa tendência usando uma JANELA MÓVEL de 2-3 meses.

Diferença das versões anteriores:
- V3/V4: Analisam todo o período de uma vez (ESTÁTICO)
- V5: Analisa últimos 2-3 meses ANTES DE CADA TRADE (DINÂMICO)

Isso permite adaptar conforme o mercado muda!

Autor: MacTester V2.0
Data: 2025-11-08
Versão: 5.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendFilterV5:
    """
    Filtro V5 - Rolling Window (Janela Deslizante)
    
    Analisa tendência dos últimos N dias antes de cada trade.
    Permite adaptação dinâmica em períodos longos.
    """
    
    def __init__(self, window_days: int = 60, adx_threshold: int = 15, use_sma: bool = True):
        """
        Args:
            window_days: Tamanho da janela em dias (default: 60 = ~2-3 meses)
            adx_threshold: Threshold mínimo ADX (default: 15)
            use_sma: Se True, usa SMA 100/200 também. Se False, só EMA 21/50 (default: True)
        """
        self.window_days = window_days
        self.adx_threshold = adx_threshold
        self.use_sma = use_sma
        
        # Indicadores
        self.ema_fast = 21
        self.ema_slow = 50
        self.sma_fast = 100
        self.sma_slow = 200
        self.adx_period = 14
        
        logger.info(f"Filtro V5 inicializado: window={window_days} dias, ADX>={adx_threshold}, SMA={'sim' if use_sma else 'nao'}")
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula SMA"""
        return data.rolling(window=period).mean()
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calcula ADX, +DI e -DI"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_dm = pd.Series(plus_dm, index=df.index)
        minus_dm = pd.Series(minus_dm, index=df.index)
        
        # Smoothed DM
        plus_dm_smooth = plus_dm.rolling(window=period).mean()
        minus_dm_smooth = minus_dm.rolling(window=period).mean()
        
        # Directional Indicators
        plus_di = 100 * (plus_dm_smooth / atr)
        minus_di = 100 * (minus_dm_smooth / atr)
        
        # ADX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di
    
    def resample_to_h1(self, df: pd.DataFrame) -> pd.DataFrame:
        """Reamostra M5 para H1"""
        if 'time' in df.columns:
            df_copy = df.set_index('time').copy()
        else:
            df_copy = df.copy()
        
        resampled = df_copy.resample('1h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum' if 'volume' in df_copy.columns else 'sum'
        }).dropna()
        
        return resampled
    
    def analyze_window(self, df_m5: pd.DataFrame) -> Dict:
        """
        Analisa tendência em uma janela específica
        
        Args:
            df_m5: DataFrame M5 da janela
            
        Returns:
            Dict com análise
        """
        # Reamostra para H1
        df_h1 = self.resample_to_h1(df_m5)
        
        # Verifica dados suficientes
        min_required = self.sma_slow + 10 if self.use_sma else self.ema_slow + 10
        
        if len(df_h1) < min_required:
            return {
                'error': f'Poucos dados H1: {len(df_h1)} < {min_required}',
                'allowed_directions': [],
                'is_consolidation': True
            }
        
        close = df_h1['close']
        
        # EMA (sempre usa)
        ema_fast = self.calculate_ema(close, self.ema_fast)
        ema_slow = self.calculate_ema(close, self.ema_slow)
        
        # ADX
        adx, plus_di, minus_di = self.calculate_adx(df_h1, self.adx_period)
        
        # Últimos valores
        ema_fast_current = ema_fast.iloc[-1] if not ema_fast.empty else 0
        ema_slow_current = ema_slow.iloc[-1] if not ema_slow.empty else 0
        adx_current = adx.iloc[-1] if not adx.empty else 0
        plus_di_current = plus_di.iloc[-1] if not plus_di.empty else 0
        minus_di_current = minus_di.iloc[-1] if not minus_di.empty else 0
        
        # Detecta consolidação
        if adx_current < self.adx_threshold:
            return {
                'allowed_directions': [],
                'is_consolidation': True,
                'adx': adx_current,
                'trend_description': 'CONSOLIDACAO'
            }
        
        # Analisa EMA
        ema_bullish = ema_fast_current > ema_slow_current and plus_di_current > minus_di_current
        ema_bearish = ema_fast_current < ema_slow_current and minus_di_current > plus_di_current
        
        allowed_directions = []
        
        if self.use_sma:
            # Usa SMA também (mais conservador)
            sma_fast = self.calculate_sma(close, self.sma_fast)
            sma_slow = self.calculate_sma(close, self.sma_slow)
            
            sma_fast_current = sma_fast.iloc[-1] if not sma_fast.empty else 0
            sma_slow_current = sma_slow.iloc[-1] if not sma_slow.empty else 0
            
            sma_bullish = sma_fast_current > sma_slow_current
            sma_bearish = sma_fast_current < sma_slow_current
            
            # Ambos devem concordar
            if ema_bullish and sma_bullish:
                allowed_directions.append('BUY')
            if ema_bearish and sma_bearish:
                allowed_directions.append('SELL')
            
            trend_desc = f"EMA:{'ALTA' if ema_bullish else 'BAIXA' if ema_bearish else 'NEUTRO'}, SMA:{'ALTA' if sma_bullish else 'BAIXA' if sma_bearish else 'NEUTRO'}"
        else:
            # Usa apenas EMA (mais permissivo)
            if ema_bullish:
                allowed_directions.append('BUY')
            if ema_bearish:
                allowed_directions.append('SELL')
            
            trend_desc = f"EMA:{'ALTA' if ema_bullish else 'BAIXA' if ema_bearish else 'NEUTRO'}"
        
        if not allowed_directions:
            return {
                'allowed_directions': [],
                'is_consolidation': True,
                'adx': adx_current,
                'trend_description': f'DIVERGENTE ({trend_desc})'
            }
        
        return {
            'allowed_directions': allowed_directions,
            'is_consolidation': False,
            'adx': adx_current,
            'trend_description': ", ".join(allowed_directions),
            'details': trend_desc
        }
    
    def should_trade(self, df_m5: pd.DataFrame, trade_time: pd.Timestamp, bar_type: str) -> Tuple[bool, str]:
        """
        Determina se deve executar trade usando janela rolling
        
        Args:
            df_m5: DataFrame M5 completo
            trade_time: Timestamp do trade
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo)
        """
        # Define janela: últimos N dias antes do trade
        window_start = trade_time - timedelta(days=self.window_days)
        
        # Filtra dados da janela
        if 'time' in df_m5.columns:
            df_window = df_m5[(df_m5['time'] > window_start) & (df_m5['time'] <= trade_time)].copy()
        else:
            df_window = df_m5[(df_m5.index > window_start) & (df_m5.index <= trade_time)].copy()
        
        # Analisa janela
        analysis = self.analyze_window(df_window)
        
        if 'error' in analysis:
            return False, analysis['error']
        
        if analysis['is_consolidation']:
            return False, f"{analysis.get('trend_description', 'Consolidacao')} (ADX {analysis.get('adx', 0):.2f})"
        
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type} (janela {self.window_days}d)"
        else:
            allowed = ", ".join(analysis['allowed_directions']) if analysis['allowed_directions'] else "Nenhuma"
            return False, f"Contra tendencia (permitido: {allowed})"


def main():
    """Teste rápido"""
    print("="*80)
    print("TESTE FILTRO V5 - ROLLING WINDOW")
    print("="*80)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles M5")
    
    # Testa diferentes janelas
    configs = [
        (60, 15, True, "2 meses + SMA + ADX 15"),
        (90, 15, True, "3 meses + SMA + ADX 15"),
        (60, 12, False, "2 meses + EMA apenas + ADX 12"),
        (90, 10, False, "3 meses + EMA apenas + ADX 10")
    ]
    
    # Pega última data
    if 'time' in df.columns:
        last_time = df['time'].max()
    else:
        last_time = df.index.max()
    
    print(f"Última data: {last_time}")
    
    for window_days, adx_th, use_sma, desc in configs:
        print(f"\n{'='*80}")
        print(f"CONFIG: {desc}")
        print("="*80)
        
        filter_v5 = TrendFilterV5(window_days=window_days, adx_threshold=adx_th, use_sma=use_sma)
        
        # Testa com última data
        for bar_type in ['BUY', 'SELL']:
            can_trade, reason = filter_v5.should_trade(df, last_time, bar_type)
            status = "[OK]" if can_trade else "[X]"
            print(f"  {bar_type}: {status} - {reason}")


if __name__ == "__main__":
    main()

