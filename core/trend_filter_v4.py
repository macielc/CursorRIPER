"""
Filtro de Tendência V4 - HÍBRIDO (EMA + SMA + ADX)
===================================================
Combina:
- SMA 100/200 (H1) → Tendência de LONGO PRAZO (1-3 meses)
- EMA 21/50 (H1) → Tendência de MÉDIO PRAZO (1-2 semanas)
- ADX (H1) → Força da tendência

Lógica:
1. SMA 100/200 define BIAS de longo prazo (bullish/bearish)
2. EMA 21/50 confirma tendência de médio prazo
3. ADX valida se há força suficiente
4. Permite trades quando médio E longo prazo CONCORDAM

Autor: MacTester V2.0
Data: 2025-11-08
Versão: 4.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendFilterV4:
    """
    Filtro V4 - Híbrido com SMA 100/200 + EMA 21/50 + ADX
    
    Usa múltiplos timeframes para validação cruzada:
    - SMA 100/200 → Longo prazo
    - EMA 21/50 → Médio prazo
    - ADX → Força
    """
    
    def __init__(self, adx_threshold: int = 15, require_both: bool = True):
        """
        Args:
            adx_threshold: Threshold mínimo ADX (default: 15)
            require_both: Se True, exige alinhamento SMA E EMA. Se False, apenas 1 (default: True)
        """
        # Médio prazo (EMA)
        self.ema_fast = 21
        self.ema_slow = 50
        
        # Longo prazo (SMA)
        self.sma_fast = 100
        self.sma_slow = 200
        
        # ADX
        self.adx_period = 14
        self.adx_threshold = adx_threshold
        
        # Lógica de combinação
        self.require_both = require_both  # True = ambos devem concordar, False = um basta
        
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
    
    def analyze_trend(self, df_m5: pd.DataFrame) -> Dict:
        """
        Analisa tendência usando EMA (médio) + SMA (longo) + ADX
        
        Returns:
            Dict com direções permitidas
        """
        logger.info("Analisando tendencia V4 (EMA + SMA + ADX)...")
        
        # Reamostra para H1
        df_h1 = self.resample_to_h1(df_m5)
        
        if len(df_h1) < 250:  # Precisa de pelo menos 200 para SMA 200 + margem
            logger.warning(f"Poucos candles H1: {len(df_h1)} (min: 250 para SMA 200)")
            return {
                'error': 'Dados insuficientes para SMA 200',
                'allowed_directions': [],
                'is_consolidation': True
            }
        
        close = df_h1['close']
        
        # EMA (médio prazo)
        ema_fast = self.calculate_ema(close, self.ema_fast)
        ema_slow = self.calculate_ema(close, self.ema_slow)
        
        # SMA (longo prazo)
        sma_fast = self.calculate_sma(close, self.sma_fast)
        sma_slow = self.calculate_sma(close, self.sma_slow)
        
        # ADX
        adx, plus_di, minus_di = self.calculate_adx(df_h1, self.adx_period)
        
        # Últimos valores
        ema_fast_current = ema_fast.iloc[-1] if not ema_fast.empty else 0
        ema_slow_current = ema_slow.iloc[-1] if not ema_slow.empty else 0
        sma_fast_current = sma_fast.iloc[-1] if not sma_fast.empty else 0
        sma_slow_current = sma_slow.iloc[-1] if not sma_slow.empty else 0
        adx_current = adx.iloc[-1] if not adx.empty else 0
        plus_di_current = plus_di.iloc[-1] if not plus_di.empty else 0
        minus_di_current = minus_di.iloc[-1] if not minus_di.empty else 0
        close_current = close.iloc[-1]
        
        logger.info(f"  EMA21: {ema_fast_current:.2f}, EMA50: {ema_slow_current:.2f}")
        logger.info(f"  SMA100: {sma_fast_current:.2f}, SMA200: {sma_slow_current:.2f}")
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
        
        # Analisa SMA (longo prazo)
        sma_bullish = sma_fast_current > sma_slow_current
        sma_bearish = sma_fast_current < sma_slow_current
        
        # Analisa EMA (médio prazo)
        ema_bullish = ema_fast_current > ema_slow_current and plus_di_current > minus_di_current
        ema_bearish = ema_fast_current < ema_slow_current and minus_di_current > plus_di_current
        
        logger.info(f"  LONGO PRAZO (SMA100/200): {'ALTA' if sma_bullish else 'BAIXA' if sma_bearish else 'NEUTRO'}")
        logger.info(f"  MEDIO PRAZO (EMA21/50+DI): {'ALTA' if ema_bullish else 'BAIXA' if ema_bearish else 'NEUTRO'}")
        
        # Determina direções permitidas
        allowed_directions = []
        
        if self.require_both:
            # Modo CONSERVADOR: Ambos devem concordar
            if sma_bullish and ema_bullish:
                allowed_directions.append('BUY')
                logger.info(f"  => COMPRA permitida (SMA E EMA alinhados em ALTA)")
            
            if sma_bearish and ema_bearish:
                allowed_directions.append('SELL')
                logger.info(f"  => VENDA permitida (SMA E EMA alinhados em BAIXA)")
        else:
            # Modo PERMISSIVO: Um basta (prioriza longo prazo)
            if sma_bullish or ema_bullish:
                allowed_directions.append('BUY')
                if sma_bullish and ema_bullish:
                    logger.info(f"  => COMPRA permitida (SMA E EMA em ALTA)")
                elif sma_bullish:
                    logger.info(f"  => COMPRA permitida (SMA em ALTA, EMA neutro/baixa)")
                else:
                    logger.info(f"  => COMPRA permitida (EMA em ALTA, SMA neutro/baixa)")
            
            if sma_bearish or ema_bearish:
                allowed_directions.append('SELL')
                if sma_bearish and ema_bearish:
                    logger.info(f"  => VENDA permitida (SMA E EMA em BAIXA)")
                elif sma_bearish:
                    logger.info(f"  => VENDA permitida (SMA em BAIXA, EMA neutro/alta)")
                else:
                    logger.info(f"  => VENDA permitida (EMA em BAIXA, SMA neutro/alta)")
        
        # Se nenhuma direção clara
        if not allowed_directions:
            logger.info(f"  => SEM ALINHAMENTO (SMA vs EMA divergentes)")
            return {
                'allowed_directions': [],
                'is_consolidation': True,
                'adx': adx_current,
                'trend_description': 'DIVERGENTE',
                'sma_trend': 'ALTA' if sma_bullish else 'BAIXA',
                'ema_trend': 'ALTA' if ema_bullish else 'BAIXA'
            }
        
        trend_desc = " e ".join(allowed_directions)
        logger.info(f"  => Direcoes permitidas: {trend_desc}")
        
        return {
            'allowed_directions': allowed_directions,
            'is_consolidation': False,
            'adx': adx_current,
            'trend_description': trend_desc,
            'sma_trend': 'ALTA' if sma_bullish else 'BAIXA' if sma_bearish else 'NEUTRO',
            'ema_trend': 'ALTA' if ema_bullish else 'BAIXA' if ema_bearish else 'NEUTRO',
            'ema_fast': ema_fast_current,
            'ema_slow': ema_slow_current,
            'sma_fast': sma_fast_current,
            'sma_slow': sma_slow_current
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
            reason = analysis.get('trend_description', 'Consolidacao')
            return False, f"{reason} (ADX {analysis.get('adx', 0):.2f})"
        
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type} confirmada"
        else:
            allowed = ", ".join(analysis['allowed_directions']) if analysis['allowed_directions'] else "Nenhuma"
            return False, f"Contra tendencia (permitido: {allowed})"


def main():
    """Teste rápido"""
    print("="*80)
    print("TESTE FILTRO V4 - HIBRIDO (EMA + SMA + ADX)")
    print("="*80)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles M5")
    
    # Testa diferentes configurações
    configs = [
        (15, True, "CONSERVADOR (ambos devem concordar)"),
        (15, False, "PERMISSIVO (um basta)"),
        (12, True, "ADX 12 + CONSERVADOR"),
        (10, False, "ADX 10 + PERMISSIVO")
    ]
    
    for adx_th, require_both, desc in configs:
        print(f"\n{'='*80}")
        print(f"CONFIG: {desc}")
        print(f"ADX Threshold: {adx_th}, Require Both: {require_both}")
        print("="*80)
        
        filter_v4 = TrendFilterV4(adx_threshold=adx_th, require_both=require_both)
        result = filter_v4.analyze_trend(df)
        
        print(f"\nResultado:")
        print(f"  Consolidacao: {result.get('is_consolidation')}")
        print(f"  Direcoes: {result.get('allowed_directions', [])}")
        print(f"  ADX: {result.get('adx', 0):.2f}")
        print(f"  Tendencia SMA: {result.get('sma_trend', 'N/A')}")
        print(f"  Tendencia EMA: {result.get('ema_trend', 'N/A')}")
        
        # Testa decisão
        for bar_type in ['BUY', 'SELL']:
            can_trade, reason = filter_v4.should_trade(df, bar_type)
            status = "[OK]" if can_trade else "[X]"
            print(f"  {bar_type}: {status} - {reason}")


if __name__ == "__main__":
    main()

