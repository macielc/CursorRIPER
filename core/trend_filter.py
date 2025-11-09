"""
Filtro de Tendência Multi-Timeframe Simplificado
=================================================
Detector de tendência baseado em dados históricos para estratégias de trading.

Indicadores utilizados:
- EMA 21/50 (curto prazo)
- SMA 100/200 (longo prazo)
- ADX > 25 (força da tendência)
- Market Structure (HH/HL vs LH/LL)

Autor: MacTester V2.0
Data: 2025-11-08
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


class TrendFilter:
    """
    Filtro de tendência para validar trades
    
    Usa múltiplos timeframes (M5, M15, H1, H4) para determinar
    se a tendência é favorável para operar.
    """
    
    def __init__(self):
        """Inicializa o filtro de tendência"""
        # Períodos dos indicadores
        self.ema_fast = 21
        self.ema_slow = 50
        self.sma_fast = 100
        self.sma_slow = 200
        self.adx_period = 14
        
        # Thresholds
        self.adx_no_trend = 20
        self.adx_weak = 25
        self.adx_strong = 40
        
        # Pesos por timeframe (total = 1.0)
        self.weights = {
            'M5': 0.10,   # Menor peso - muito volátil
            'M15': 0.20,  # Peso baixo - curto prazo
            'H1': 0.30,   # Peso médio - médio prazo
            'H4': 0.40    # Maior peso - longo prazo (prevalência inversa)
        }
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula EMA (Exponential Moving Average)"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calcula SMA (Simple Moving Average)"""
        return data.rolling(window=period).mean()
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcula ADX, +DI e -DI
        
        Returns:
            (adx, plus_di, minus_di)
        """
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
        """
        Identifica estrutura de mercado (Higher Highs, Higher Lows, etc)
        
        Returns:
            Dict com análise da estrutura
        """
        # Identifica swing highs e lows
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
        
        # Analisa sequência de topos
        if len(swing_highs) >= 2:
            for i in range(1, len(swing_highs)):
                if swing_highs.iloc[i] > swing_highs.iloc[i-1]:
                    structure['higher_highs'] += 1
                else:
                    structure['lower_highs'] += 1
        
        # Analisa sequência de fundos
        if len(swing_lows) >= 2:
            for i in range(1, len(swing_lows)):
                if swing_lows.iloc[i] > swing_lows.iloc[i-1]:
                    structure['higher_lows'] += 1
                else:
                    structure['lower_lows'] += 1
        
        # Determina padrão dominante
        if structure['higher_highs'] > structure['lower_highs'] and \
           structure['higher_lows'] > structure['lower_lows']:
            structure['pattern'] = 'UPTREND'
        elif structure['lower_highs'] > structure['higher_highs'] and \
             structure['lower_lows'] > structure['higher_lows']:
            structure['pattern'] = 'DOWNTREND'
        
        return structure
    
    def analyze_single_timeframe(self, df: pd.DataFrame, timeframe: str) -> Dict:
        """
        Analisa tendência em um único timeframe
        
        Args:
            df: DataFrame com dados OHLCV
            timeframe: 'M5', 'M15', 'H1' ou 'H4'
            
        Returns:
            Dict com análise completa
        """
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
        
        # ==================== MÉDIAS MÓVEIS ====================
        
        # EMA (curto prazo)
        ema_fast = self.calculate_ema(close, self.ema_fast)
        ema_slow = self.calculate_ema(close, self.ema_slow)
        
        # SMA (longo prazo)
        sma_fast = self.calculate_sma(close, self.sma_fast)
        sma_slow = self.calculate_sma(close, self.sma_slow)
        
        # Sinal de EMA
        ema_signal = 0
        if not ema_fast.empty and not ema_slow.empty:
            if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
                ema_signal = 1
                if close.iloc[-1] > ema_fast.iloc[-1]:
                    ema_signal = 2  # Forte alta
            elif ema_fast.iloc[-1] < ema_slow.iloc[-1]:
                ema_signal = -1
                if close.iloc[-1] < ema_fast.iloc[-1]:
                    ema_signal = -2  # Forte baixa
        
        analysis['signals']['ema'] = ema_signal
        analysis['indicators']['ema_fast'] = ema_fast.iloc[-1] if not ema_fast.empty else 0
        analysis['indicators']['ema_slow'] = ema_slow.iloc[-1] if not ema_slow.empty else 0
        
        # Sinal de SMA
        sma_signal = 0
        if not sma_fast.empty and not sma_slow.empty:
            if sma_fast.iloc[-1] > sma_slow.iloc[-1]:
                sma_signal = 1
            elif sma_fast.iloc[-1] < sma_slow.iloc[-1]:
                sma_signal = -1
        
        analysis['signals']['sma'] = sma_signal
        analysis['indicators']['sma_fast'] = sma_fast.iloc[-1] if not sma_fast.empty else 0
        analysis['indicators']['sma_slow'] = sma_slow.iloc[-1] if not sma_slow.empty else 0
        
        # ==================== ADX ====================
        
        adx, plus_di, minus_di = self.calculate_adx(df, self.adx_period)
        
        adx_current = adx.iloc[-1] if not adx.empty else 0
        plus_di_current = plus_di.iloc[-1] if not plus_di.empty else 0
        minus_di_current = minus_di.iloc[-1] if not minus_di.empty else 0
        
        # Força da tendência
        if adx_current > self.adx_strong:
            analysis['strength'] = TrendStrength.VERY_STRONG
        elif adx_current > self.adx_weak:
            analysis['strength'] = TrendStrength.STRONG
        elif adx_current > self.adx_no_trend:
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
        
        # ==================== MARKET STRUCTURE ====================
        
        market_structure = self.identify_market_structure(df)
        
        structure_signal = 0
        if market_structure['pattern'] == 'UPTREND':
            structure_signal = 2
        elif market_structure['pattern'] == 'DOWNTREND':
            structure_signal = -2
        
        analysis['signals']['market_structure'] = structure_signal
        analysis['market_structure'] = market_structure
        
        # ==================== SCORE FINAL ====================
        
        # Pesos dos indicadores
        weights = {
            'ema': 0.25,
            'sma': 0.20,
            'adx_direction': 0.30,  # Maior peso
            'market_structure': 0.25
        }
        
        total_weight = 0
        weighted_signal = 0
        
        for indicator, weight in weights.items():
            if indicator in analysis['signals']:
                weighted_signal += analysis['signals'][indicator] * weight
                total_weight += weight
        
        final_score = weighted_signal / total_weight if total_weight > 0 else 0
        analysis['score'] = final_score
        
        # Determina tendência final
        if final_score >= 1.5:
            analysis['trend'] = TrendDirection.STRONG_BULLISH
        elif final_score >= 0.5:
            analysis['trend'] = TrendDirection.BULLISH
        elif final_score <= -1.5:
            analysis['trend'] = TrendDirection.STRONG_BEARISH
        elif final_score <= -0.5:
            analysis['trend'] = TrendDirection.BEARISH
        else:
            analysis['trend'] = TrendDirection.NEUTRAL
        
        # Pode operar se tendência forte E ADX > threshold
        analysis['can_trade'] = (
            analysis['strength'] in [TrendStrength.STRONG, TrendStrength.VERY_STRONG] and
            analysis['trend'] != TrendDirection.NEUTRAL
        )
        
        return analysis
    
    def resample_to_timeframe(self, df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
        """
        Reamostra dados M5 para timeframe maior
        
        Args:
            df: DataFrame M5
            target_tf: 'M15', 'H1' ou 'H4'
            
        Returns:
            DataFrame resampled
        """
        # Mapeamento de timeframes
        tf_map = {
            'M15': '15min',
            'H1': '1h',
            'H4': '4h'
        }
        
        if target_tf not in tf_map:
            logger.error(f"Timeframe {target_tf} não suportado")
            return df
        
        # Garante que 'time' é o index
        if 'time' in df.columns:
            df_copy = df.set_index('time').copy()
        else:
            df_copy = df.copy()
        
        # Reamostra
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
        Analisa tendência em múltiplos timeframes
        
        Args:
            df_m5: DataFrame com dados M5 (base)
            
        Returns:
            Dict com análise consolidada
        """
        logger.info("Iniciando análise multi-timeframe...")
        
        # Analisa cada timeframe
        analyses = {}
        
        # M5 (direto)
        analyses['M5'] = self.analyze_single_timeframe(df_m5, 'M5')
        
        # M15
        df_m15 = self.resample_to_timeframe(df_m5, 'M15')
        analyses['M15'] = self.analyze_single_timeframe(df_m15, 'M15')
        
        # H1
        df_h1 = self.resample_to_timeframe(df_m5, 'H1')
        analyses['H1'] = self.analyze_single_timeframe(df_h1, 'H1')
        
        # H4
        df_h4 = self.resample_to_timeframe(df_m5, 'H4')
        analyses['H4'] = self.analyze_single_timeframe(df_h4, 'H4')
        
        # ==================== CONSOLIDAÇÃO ====================
        
        # Calcula score ponderado
        weighted_score = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            if 'error' not in analysis:
                weight = self.weights[tf]
                weighted_score += analysis['score'] * weight
                total_weight += weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determina tendência geral
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
        
        # Verifica alinhamento
        trends = [a['trend'] for a in analyses.values() if 'error' not in a]
        
        bullish_count = sum(1 for t in trends if t in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH])
        bearish_count = sum(1 for t in trends if t in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH])
        neutral_count = sum(1 for t in trends if t == TrendDirection.NEUTRAL)
        
        # Detecta consolidação
        is_consolidation = (
            (bullish_count >= 2 and bearish_count >= 2) or  # Conflito
            neutral_count >= 2 or  # Maioria neutra
            np.mean([a['indicators'].get('adx', 0) for a in analyses.values() if 'error' not in a]) < self.adx_no_trend
        )
        
        # Determina se pode operar
        can_trade = False
        trade_direction = None
        confidence = 0
        
        if not is_consolidation:
            # Alinhamento total (4/4)
            if bullish_count == 4:
                can_trade = True
                trade_direction = "BUY"
                confidence = 100
            elif bearish_count == 4:
                can_trade = True
                trade_direction = "SELL"
                confidence = 100
            # Alinhamento forte (3/4)
            elif bullish_count >= 3 and overall_trend in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH]:
                can_trade = True
                trade_direction = "BUY"
                confidence = (bullish_count / 4) * 100
            elif bearish_count >= 3 and overall_trend in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH]:
                can_trade = True
                trade_direction = "SELL"
                confidence = (bearish_count / 4) * 100
            # Alinhamento mínimo (2/4) - MENOS RESTRITIVO
            elif bullish_count >= 2 and bullish_count > bearish_count and \
                 overall_trend in [TrendDirection.BULLISH, TrendDirection.STRONG_BULLISH]:
                can_trade = True
                trade_direction = "BUY"
                confidence = (bullish_count / 4) * 100
            elif bearish_count >= 2 and bearish_count > bullish_count and \
                 overall_trend in [TrendDirection.BEARISH, TrendDirection.STRONG_BEARISH]:
                can_trade = True
                trade_direction = "SELL"
                confidence = (bearish_count / 4) * 100
        
        result = {
            'analyses_by_timeframe': analyses,
            'overall_trend': overall_trend,
            'trend_description': trend_description,
            'final_score': final_score,
            'is_consolidation': is_consolidation,
            'can_trade': can_trade,
            'trade_direction': trade_direction,
            'confidence': confidence,
            'alignment': {
                'bullish': bullish_count,
                'bearish': bearish_count,
                'neutral': neutral_count
            }
        }
        
        return result
    
    def should_trade(self, df_m5: pd.DataFrame, bar_type: str) -> Tuple[bool, str, float]:
        """
        Determina se deve executar um trade baseado na tendência
        
        Args:
            df_m5: DataFrame com dados M5
            bar_type: 'BUY' ou 'SELL'
            
        Returns:
            (pode_operar, motivo, confianca)
        """
        analysis = self.analyze_multi_timeframe(df_m5)
        
        if analysis['is_consolidation']:
            return False, "Mercado em consolidacao - nao operar", 0
        
        if not analysis['can_trade']:
            return False, "Condicoes de tendencia nao favoraveis", 0
        
        if bar_type.upper() == 'BUY' and analysis['trade_direction'] == 'BUY':
            return True, f"Tendencia de alta confirmada (Confianca: {analysis['confidence']:.0f}%)", analysis['confidence']
        elif bar_type.upper() == 'SELL' and analysis['trade_direction'] == 'SELL':
            return True, f"Tendencia de baixa confirmada (Confianca: {analysis['confidence']:.0f}%)", analysis['confidence']
        else:
            return False, f"Trade contra a tendencia ({analysis['trade_direction']})", 0


def main():
    """Teste do filtro de tendência"""
    print("=" * 80)
    print("TESTE DO FILTRO DE TENDENCIA")
    print("=" * 80)
    
    # Carrega dados para teste
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / 'engines' / 'python'))
    from core.data_loader import DataLoader
    
    loader = DataLoader(timeframe='5m')
    df = loader.load()
    
    print(f"\nDados carregados: {len(df)} candles")
    print(f"Periodo: {df['time'].min()} ate {df['time'].max()}")
    
    # Cria filtro
    trend_filter = TrendFilter()
    
    # Analisa
    print("\nAnalisando tendencia...")
    analysis = trend_filter.analyze_multi_timeframe(df)
    
    # Resultados
    print("\n" + "=" * 80)
    print("RESULTADO DA ANALISE")
    print("=" * 80)
    
    print(f"\nTendencia Geral: {analysis['trend_description']}")
    print(f"Score: {analysis['final_score']:.2f}")
    print(f"Consolidacao: {'SIM' if analysis['is_consolidation'] else 'NAO'}")
    print(f"Pode Operar: {'SIM' if analysis['can_trade'] else 'NAO'}")
    
    if analysis['can_trade']:
        print(f"Direcao: {analysis['trade_direction']}")
        print(f"Confianca: {analysis['confidence']:.0f}%")
    
    print(f"\nAlinhamento:")
    print(f"  Bullish: {analysis['alignment']['bullish']}/4")
    print(f"  Bearish: {analysis['alignment']['bearish']}/4")
    print(f"  Neutral: {analysis['alignment']['neutral']}/4")
    
    # Analise por timeframe
    print("\n" + "=" * 80)
    print("ANALISE POR TIMEFRAME")
    print("=" * 80)
    
    for tf, tf_analysis in analysis['analyses_by_timeframe'].items():
        if 'error' in tf_analysis:
            print(f"\n{tf}: ERRO - {tf_analysis['error']}")
            continue
        
        print(f"\n{tf}:")
        print(f"  Tendencia: {tf_analysis['trend'].name}")
        print(f"  Score: {tf_analysis['score']:.2f}")
        print(f"  ADX: {tf_analysis['indicators']['adx']:.2f}")
        print(f"  Forca: {tf_analysis['strength'].name}")
        print(f"  Pode operar: {'SIM' if tf_analysis['can_trade'] else 'NAO'}")
    
    # Teste de decisão
    print("\n" + "=" * 80)
    print("TESTE DE DECISAO DE TRADE")
    print("=" * 80)
    
    for bar_type in ['BUY', 'SELL']:
        can_trade, reason, confidence = trend_filter.should_trade(df, bar_type)
        status = "[OK]" if can_trade else "[X]"
        print(f"\n{bar_type}: {status}")
        print(f"  Motivo: {reason}")
        if can_trade:
            print(f"  Confianca: {confidence:.0f}%")


if __name__ == "__main__":
    main()

