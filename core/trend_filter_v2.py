"""
Filtro de Tendência V2 - Médio/Longo Prazo
===========================================
Versão ajustada focada em tendências de médio (1-4 semanas) 
e longo prazo (1-3 meses) para definir DIREÇÃO da operação.

Mudanças da V1:
- Remove M5/M15 (muito volátil)
- Usa apenas H1, H4, D1
- Permite trades em AMBAS as direções (compra E venda)
- Filtro define DIREÇÃO permitida, não se deve ou não operar

Autor: MacTester V2.0
Data: 2025-11-08
Versão: 2.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Direção da tendência"""
    STRONG_BULLISH = 2
    BULLISH = 1
    NEUTRAL = 0
    BEARISH = -1
    STRONG_BEARISH = -2


class TrendStrength(Enum):
    """Força da tendência"""
    VERY_STRONG = 3  # ADX > 40
    STRONG = 2       # ADX > 25
    WEAK = 1         # ADX > 20
    NO_TREND = 0     # ADX <= 20


class TrendFilterV2:
    """
    Filtro de tendência V2 - Médio/Longo Prazo
    
    Identifica a direção da tendência dominante e permite
    operar APENAS na direção da tendência identificada.
    """
    
    def __init__(self, adx_threshold: int = 20):
        """
        Inicializa o filtro V2
        
        Args:
            adx_threshold: Threshold mínimo para considerar tendência (default: 20)
        """
        # Períodos dos indicadores
        self.ema_fast = 21
        self.ema_slow = 50
        self.sma_fast = 100
        self.sma_slow = 200
        self.adx_period = 14
        
        # Threshold ADX (configurável)
        self.adx_threshold = adx_threshold
        
        # Pesos por timeframe (total = 1.0)
        # FOCO em médio/longo prazo!
        self.weights = {
            'H1': 0.25,   # 1 semana
            'H4': 0.35,   # 2-4 semanas
            'D1': 0.40    # 1-3 meses (maior peso)
        }
        
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
    
    def identify_market_structure(self, df: pd.DataFrame, lookback: int = 20) -> Dict:
        """Identifica estrutura de mercado"""
        highs = df['high'].rolling(window=3, center=True).max() == df['high']
        lows = df['low'].rolling(window=3, center=True).min() == df['low']
        
        swing_highs = df[highs]['high'].tail(lookback)
        swing_lows = df[lows]['low'].tail(lookback)
        
        structure = {
            'higher_highs': 0,
            'higher_lows': 0,
            'lower_highs': 0,
            'lower_lows': 0,
            'pattern': 'NEUTRAL'
        }
        
        if len(swing_highs) >= 2:
            for i in range(1, len(swing_highs)):
                if swing_highs.iloc[i] > swing_highs.iloc[i-1]:
                    structure['higher_highs'] += 1
                else:
                    structure['lower_highs'] += 1
        
        if len(swing_lows) >= 2:
            for i in range(1, len(swing_lows)):
                if swing_lows.iloc[i] > swing_lows.iloc[i-1]:
                    structure['higher_lows'] += 1
                else:
                    structure['lower_lows'] += 1
        
        if structure['higher_highs'] > structure['lower_highs'] and \
           structure['higher_lows'] > structure['lower_lows']:
            structure['pattern'] = 'UPTREND'
        elif structure['lower_highs'] > structure['higher_highs'] and \
             structure['lower_lows'] > structure['higher_lows']:
            structure['pattern'] = 'DOWNTREND'
        
        return structure
    
    def analyze_single_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """Analisa tendência em um único timeframe"""
        if len(df) < self.sma_slow + 10:
            logger.warning(f"Dados insuficientes para análise em {timeframe}")
            return {
                'timeframe': timeframe,
                'trend': TrendDirection.NEUTRAL,
                'strength': TrendStrength.NO_TREND,
                'score': 0,
                'can_trade': False,
                'error': 'Dados insuficientes'
            }
        
        analysis = {
            'timeframe': timeframe,
            'trend': TrendDirection.NEUTRAL,
            'strength': TrendStrength.NO_TREND,
            'score': 0,
            'signals': {},
            'indicators': {},
            'can_trade': False
        }
        
        close = df['close']
        
        # EMA
        ema_fast = self.calculate_ema(close, self.ema_fast)
        ema_slow = self.calculate_ema(close, self.ema_slow)
        
        # SMA
        sma_fast = self.calculate_sma(close, self.sma_fast)
        sma_slow = self.calculate_sma(close, self.sma_slow)
        
        # Sinal EMA
        ema_signal = 0
        if not ema_fast.empty and not ema_slow.empty:
            if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
                ema_signal = 1
                if close.iloc[-1] > ema_fast.iloc[-1]:
                    ema_signal = 2
            elif ema_fast.iloc[-1] < ema_slow.iloc[-1]:
                ema_signal = -1
                if close.iloc[-1] < ema_fast.iloc[-1]:
                    ema_signal = -2
        
        analysis['signals']['ema'] = ema_signal
        analysis['indicators']['ema_fast'] = ema_fast.iloc[-1] if not ema_fast.empty else 0
        analysis['indicators']['ema_slow'] = ema_slow.iloc[-1] if not ema_slow.empty else 0
        
        # Sinal SMA
        sma_signal = 0
        if not sma_fast.empty and not sma_slow.empty:
            if sma_fast.iloc[-1] > sma_slow.iloc[-1]:
                sma_signal = 1
            elif sma_fast.iloc[-1] < sma_slow.iloc[-1]:
                sma_signal = -1
        
        analysis['signals']['sma'] = sma_signal
        analysis['indicators']['sma_fast'] = sma_fast.iloc[-1] if not sma_fast.empty else 0
        analysis['indicators']['sma_slow'] = sma_slow.iloc[-1] if not sma_slow.empty else 0
        
        # ADX
        adx, plus_di, minus_di = self.calculate_adx(df, self.adx_period)
        
        adx_current = adx.iloc[-1] if not adx.empty else 0
        plus_di_current = plus_di.iloc[-1] if not plus_di.empty else 0
        minus_di_current = minus_di.iloc[-1] if not minus_di.empty else 0
        
        # Força
        if adx_current > 40:
            analysis['strength'] = TrendStrength.VERY_STRONG
        elif adx_current > 25:
            analysis['strength'] = TrendStrength.STRONG
        elif adx_current > self.adx_threshold:
            analysis['strength'] = TrendStrength.WEAK
        else:
            analysis['strength'] = TrendStrength.NO_TREND
        
        # Direção via +DI/-DI
        adx_direction = 0
        if plus_di_current > minus_di_current:
            adx_direction = 1
        elif plus_di_current < minus_di_current:
            adx_direction = -1
        
        analysis['signals']['adx_direction'] = adx_direction
        analysis['indicators']['adx'] = adx_current
        analysis['indicators']['plus_di'] = plus_di_current
        analysis['indicators']['minus_di'] = minus_di_current
        
        # Market Structure
        market_structure = self.identify_market_structure(df)
        
        structure_signal = 0
        if market_structure['pattern'] == 'UPTREND':
            structure_signal = 2
        elif market_structure['pattern'] == 'DOWNTREND':
            structure_signal = -2
        
        analysis['signals']['market_structure'] = structure_signal
        analysis['market_structure'] = market_structure
        
        # Score final
        weights = {
            'ema': 0.25,
            'sma': 0.20,
            'adx_direction': 0.30,
            'market_structure': 0.25
        }
        
        weighted_signal = sum(analysis['signals'][ind] * weight 
                            for ind, weight in weights.items())
        
        analysis['score'] = weighted_signal
        
        # Tendência final
        if weighted_signal >= 1.5:
            analysis['trend'] = TrendDirection.STRONG_BULLISH
        elif weighted_signal >= 0.5:
            analysis['trend'] = TrendDirection.BULLISH
        elif weighted_signal <= -1.5:
            analysis['trend'] = TrendDirection.STRONG_BEARISH
        elif weighted_signal <= -0.5:
            analysis['trend'] = TrendDirection.BEARISH
        else:
            analysis['trend'] = TrendDirection.NEUTRAL
        
        # Pode operar se tendência forte E ADX > threshold
        analysis['can_trade'] = (
            analysis['strength'] in [TrendStrength.WEAK, TrendStrength.STRONG, TrendStrength.VERY_STRONG] and
            analysis['trend'] != TrendDirection.NEUTRAL
        )
        
        return analysis
    
    def resample_to_timeframe(self, df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
        """Reamostra M5 para timeframe maior"""
        tf_map = {
            'H1': '1h',
            'H4': '4h',
            'D1': '1D'
        }
        
        if target_tf not in tf_map:
            logger.error(f"Timeframe {target_tf} não suportado")
            return df
        
        if 'time' in df.columns:
            df_copy = df.set_index('time').copy()
        else:
            df_copy = df.copy()
        
        resampled = df_copy.resample(tf_map[target_tf]).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum' if 'volume' in df_copy.columns else 'sum'
        }).dropna()
        
        return resampled
    
    def analyze_multi_timeframe(self, df_m5: pd.DataFrame) -> Dict:
        """
        Analisa tendência em múltiplos timeframes (médio/longo prazo)
        
        Returns:
            Dict com análise e direção permitida
        """
        logger.info("Iniciando análise multi-timeframe V2 (médio/longo prazo)...")
        
        analyses = {}
        
        # H1 (1 semana)
        df_h1 = self.resample_to_timeframe(df_m5, 'H1')
        analyses['H1'] = self.analyze_single_timeframe(df_h1, 'H1')
        
        # H4 (2-4 semanas)
        df_h4 = self.resample_to_timeframe(df_m5, 'H4')
        analyses['H4'] = self.analyze_single_timeframe(df_h4, 'H4')
        
        # D1 (1-3 meses)
        df_d1 = self.resample_to_timeframe(df_m5, 'D1')
        analyses['D1'] = self.analyze_single_timeframe(df_d1, 'D1')
        
        # Score ponderado
        weighted_score = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            if 'error' not in analysis:
                weight = self.weights[tf]
                weighted_score += analysis['score'] * weight
                total_weight += weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Tendência geral
        if final_score >= 1.0:
            overall_trend = TrendDirection.STRONG_BULLISH
            trend_description = "FORTE ALTA"
        elif final_score >= 0.3:
            overall_trend = TrendDirection.BULLISH
            trend_description = "ALTA"
        elif final_score <= -1.0:
            overall_trend = TrendDirection.STRONG_BEARISH
            trend_description = "FORTE BAIXA"
        elif final_score <= -0.3:
            overall_trend = TrendDirection.BEARISH
            trend_description = "BAIXA"
        else:
            overall_trend = TrendDirection.NEUTRAL
            trend_description = "NEUTRO/CONSOLIDACAO"
        
        # Contagem de tendências
        trends = [a['trend'] for a in analyses.values() if 'error' not in a]
        
        bullish_count = sum(1 for t in trends if t in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH])
        bearish_count = sum(1 for t in trends if t in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH])
        neutral_count = sum(1 for t in trends if t == TrendDirection.NEUTRAL)
        
        # Detecta consolidação
        avg_adx = np.mean([a['indicators'].get('adx', 0) for a in analyses.values() if 'error' not in a])
        is_consolidation = (
            neutral_count >= 2 or  # Maioria neutra
            avg_adx < self.adx_threshold  # ADX baixo
        )
        
        # Determina direção permitida
        # MUDANÇA CRÍTICA: Permite trades em AMBAS as direções!
        allowed_directions = []
        confidence = 0
        
        if not is_consolidation:
            # Se maioria bullish, permite COMPRAS
            if bullish_count >= 2:
                allowed_directions.append("BUY")
                confidence = (bullish_count / 3) * 100
            
            # Se maioria bearish, permite VENDAS
            if bearish_count >= 2:
                allowed_directions.append("SELL")
                confidence = max(confidence, (bearish_count / 3) * 100)
        
        result = {
            'analyses_by_timeframe': analyses,
            'overall_trend': overall_trend,
            'trend_description': trend_description,
            'final_score': final_score,
            'is_consolidation': is_consolidation,
            'allowed_directions': allowed_directions,  # Lista de direções permitidas
            'confidence': confidence,
            'alignment': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            },
            'avg_adx': avg_adx
        }
        
        return result
    
    def should_trade(self, df_m5: pd.DataFrame, bar_type: str) -> Tuple[bool, str, float]:
        """
        Determina se deve executar trade baseado na tendência
        
        Args:
            df_m5: DataFrame M5
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo, confianca)
        """
        analysis = self.analyze_multi_timeframe(df_m5)
        
        if analysis['is_consolidation']:
            return False, "Mercado em consolidacao - nao operar", 0
        
        if not analysis['allowed_directions']:
            return False, "Sem tendencia definida", 0
        
        # Verifica se a direção do trade está permitida
        if bar_type.upper() in analysis['allowed_directions']:
            return True, f"Tendencia {bar_type} confirmada (Confianca: {analysis['confidence']:.0f}%)", analysis['confidence']
        else:
            allowed_str = " ou ".join(analysis['allowed_directions'])
            return False, f"Trade contra tendencia (permitido: {allowed_str})", 0


def main():
    """Teste do filtro V2"""
    print("=" * 80)
    print("TESTE DO FILTRO V2 - MEDIO/LONGO PRAZO")
    print("=" * 80)
    
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles")
    
    # Testa com diferentes thresholds ADX
    for adx_threshold in [15, 20, 25]:
        print(f"\n{'='*80}")
        print(f"TESTE COM ADX THRESHOLD = {adx_threshold}")
        print(f"{'='*80}")
        
        trend_filter = TrendFilterV2(adx_threshold=adx_threshold)
        analysis = trend_filter.analyze_multi_timeframe(df)
        
        print(f"\nTendencia: {analysis['trend_description']}")
        print(f"Score: {analysis['final_score']:.2f}")
        print(f"Consolidacao: {'SIM' if analysis['is_consolidation'] else 'NAO'}")
        print(f"Direcoes permitidas: {', '.join(analysis['allowed_directions']) if analysis['allowed_directions'] else 'Nenhuma'}")
        print(f"Confianca: {analysis['confidence']:.0f}%")
        print(f"ADX medio: {analysis['avg_adx']:.2f}")
        
        print(f"\nAlinhamento:")
        print(f"  Bullish: {analysis['alignment']['bullish']}/3")
        print(f"  Bearish: {analysis['alignment']['bearish']}/3")
        print(f"  Neutral: {analysis['alignment']['neutral']}/3")
        
        # Teste de decisão
        for bar_type in ['BUY', 'SELL']:
            can_trade, reason, confidence = trend_filter.should_trade(df, bar_type)
            status = "[OK]" if can_trade else "[X]"
            print(f"\n{bar_type}: {status} - {reason}")


if __name__ == "__main__":
    main()

