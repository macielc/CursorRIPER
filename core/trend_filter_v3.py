"""
Filtro de Tendência V3 - SIMPLIFICADO
======================================
Versão ultra-simplificada que REALMENTE FUNCIONA.

Mudanças da V2:
- USA APENAS H1 (remove D1 que precisa de muitos dados)
- Threshold ADX = 15 (mais permissivo)
- Permite operar com tendência FRACA também
- Análise GLOBAL (não trade-by-trade para evitar "dados insuficientes")

Autor: MacTester V2.0
Data: 2025-11-08
Versão: 3.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendFilterV3:
    """
    Filtro V3 - Simplificado e funcional
    
    USA APENAS H1 para definir tendência.
    Permite trades em AMBAS direções baseado em EMA + ADX.
    """
    
    def __init__(self, adx_threshold: int = 15):
        """
        Args:
            adx_threshold: Threshold mínimo ADX (default: 15 - permissivo)
        """
        self.ema_fast = 21
        self.ema_slow = 50
        self.adx_period = 14
        self.adx_threshold = adx_threshold
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
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
    
    def analyze_trend(self, df_m5: pd.DataFrame) -> Dict:
        """
        Analisa tendência usando APENAS H1
        
        Returns:
            Dict com direções permitidas
        """
        logger.info("Analisando tendencia V3 (H1 simplificado)...")
        
        # Reamostra para H1
        df_h1 = self.resample_to_h1(df_m5)
        
        if len(df_h1) < 100:
            logger.warning(f"Poucos candles H1: {len(df_h1)} (min: 100)")
            return {
                'error': 'Dados insuficientes',
                'allowed_directions': [],
                'is_consolidation': True
            }
        
        close = df_h1['close']
        
        # EMA
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
        close_current = close.iloc[-1]
        
        logger.info(f"  EMA21: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}")
        logger.info(f"  Close: {close_current:.2f}, ADX: {adx_current:.2f}")
        logger.info(f"  +DI: {plus_di_current:.2f}, -DI: {minus_di_current:.2f}")
        
        # Detecta consolidação
        is_consolidation = adx_current < self.adx_threshold
        
        if is_consolidation:
            logger.info(f"  => CONSOLIDACAO (ADX {adx_current:.2f} < {self.adx_threshold})")
            return {
                'allowed_directions': [],
                'is_consolidation': True,
                'adx': adx_current,
                'trend_description': 'CONSOLIDACAO'
            }
        
        # Determina direções permitidas
        allowed_directions = []
        
        # Tendência de ALTA
        if ema_fast_current > ema_slow_current and plus_di_current > minus_di_current:
            allowed_directions.append('BUY')
            logger.info(f"  => ALTA permitida (EMA21 > EMA50 E +DI > -DI)")
        
        # Tendência de BAIXA
        if ema_fast_current < ema_slow_current and minus_di_current > plus_di_current:
            allowed_directions.append('SELL')
            logger.info(f"  => BAIXA permitida (EMA21 < EMA50 E -DI > +DI)")
        
        # Se nenhuma direção clara
        if not allowed_directions:
            logger.info(f"  => SEM TENDENCIA CLARA")
            return {
                'allowed_directions': [],
                'is_consolidation': True,
                'adx': adx_current,
                'trend_description': 'INDEFINIDO'
            }
        
        trend_desc = " e ".join(allowed_directions)
        logger.info(f"  => Direcoes permitidas: {trend_desc}")
        
        return {
            'allowed_directions': allowed_directions,
            'is_consolidation': False,
            'adx': adx_current,
            'trend_description': trend_desc,
            'ema_fast': ema_fast_current,
            'ema_slow': ema_slow_current
        }
    
    def should_trade(self, df_m5: pd.DataFrame, bar_type: str) -> Tuple[bool, str]:
        """
        Determina se deve executar trade
        
        Args:
            df_m5: DataFrame M5
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo)
        """
        analysis = self.analyze_trend(df_m5)
        
        if 'error' in analysis:
            return False, analysis['error']
        
        if analysis['is_consolidation']:
            return False, f"Consolidacao (ADX {analysis.get('adx', 0):.2f})"
        
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type} confirmada"
        else:
            allowed = ", ".join(analysis['allowed_directions']) if analysis['allowed_directions'] else "Nenhuma"
            return False, f"Contra tendencia (permitido: {allowed})"


def main():
    """Teste rápido"""
    print("="*80)
    print("TESTE FILTRO V3 - SIMPLIFICADO")
    print("="*80)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles M5")
    
    # Testa diferentes thresholds
    for adx_th in [10, 15, 20]:
        print(f"\n{'='*80}")
        print(f"ADX THRESHOLD = {adx_th}")
        print("="*80)
        
        filter_v3 = TrendFilterV3(adx_threshold=adx_th)
        result = filter_v3.analyze_trend(df)
        
        print(f"\nResultado:")
        print(f"  Consolidacao: {result.get('is_consolidation')}")
        print(f"  Direcoes: {result.get('allowed_directions', [])}")
        print(f"  ADX: {result.get('adx', 0):.2f}")
        
        # Testa decisão
        for bar_type in ['BUY', 'SELL']:
            can_trade, reason = filter_v3.should_trade(df, bar_type)
            status = "[OK]" if can_trade else "[X]"
            print(f"  {bar_type}: {status} - {reason}")


if __name__ == "__main__":
    main()

