"""
Signal Detector - Detecta sinais de entrada usando estratégia validada

Reutiliza a estratégia Python já testada (barra_elefante)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging

# Adicionar projeto root ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'strategies'))

from barra_elefante.strategy import BarraElefante

logger = logging.getLogger('SignalDetector')


class SignalDetector:
    """Detecta sinais de entrada baseado na estratégia Barra Elefante"""
    
    def __init__(self, params: Dict):
        """
        Inicializa detector com parâmetros da estratégia
        
        Args:
            params: Dicionário com parâmetros (mesmos do backtest)
        """
        self.params = params
        self.strategy = BarraElefante(params)
        logger.info(f"Signal Detector inicializado com parametros: {params}")
    
    def detect_signal(self, df: pd.DataFrame) -> Dict:
        """
        Detecta sinal de entrada na última barra
        
        Args:
            df: DataFrame com OHLCV (no mínimo 50 barras para lookback)
            
        Returns:
            Dict com:
            - action: 'BUY', 'SELL', ou 'NONE'
            - price: Preço atual
            - sl: Stop Loss sugerido
            - tp: Take Profit sugerido
            - atr: ATR calculado
            - reason: Motivo do sinal
        """
        try:
            # Validar DataFrame
            if len(df) < 50:
                return self._no_signal("Dados insuficientes (< 50 barras)")
            
            required_cols = ['time', 'open', 'high', 'low', 'close', 'tick_volume', 'real_volume']
            for col in required_cols:
                if col not in df.columns:
                    return self._no_signal(f"Coluna {col} faltando")
            
            # Preparar DataFrame (renomear colunas se necessário)
            df_prep = self._prepare_dataframe(df)
            
            # Gerar sinais usando estratégia validada
            signals = self.strategy.generate_signals(df_prep)
            
            # Verificar última barra
            last_idx = len(df_prep) - 1
            
            if signals['entries_long'][last_idx]:
                action = 'BUY'
                reason = f"Elefante ALTA rompido (amplitude={df_prep['high'].iloc[last_idx-1] - df_prep['low'].iloc[last_idx-1]:.0f})"
            elif signals['entries_short'][last_idx]:
                action = 'SELL'
                reason = f"Elefante BAIXA rompido (amplitude={df_prep['high'].iloc[last_idx-1] - df_prep['low'].iloc[last_idx-1]:.0f})"
            else:
                return self._no_signal("Nenhum elefante detectado")
            
            # Calcular SL/TP usando ATR
            current_price = float(df_prep['close'].iloc[last_idx])
            atr = self._calculate_atr(df_prep)
            sl, tp = self._calculate_sl_tp(action, current_price, atr)
            
            logger.info(f"🎯 SINAL DETECTADO: {action} @ {current_price:.2f}")
            logger.info(f"  Razão: {reason}")
            logger.info(f"  SL: {sl:.2f} (ATR={atr:.2f})")
            logger.info(f"  TP: {tp:.2f}")
            
            return {
                'action': action,
                'price': current_price,
                'sl': sl,
                'tp': tp,
                'atr': atr,
                'reason': reason,
                'timestamp': df_prep['time'].iloc[last_idx]
            }
            
        except Exception as e:
            logger.error(f"Erro ao detectar sinal: {e}")
            return self._no_signal(f"Erro: {str(e)}")
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepara DataFrame para estratégia
        
        Args:
            df: DataFrame original do MT5
            
        Returns:
            DataFrame preparado
        """
        df_prep = df.copy()
        
        # Renomear 'tick_volume' para 'volume' se necessário
        if 'volume' not in df_prep.columns and 'tick_volume' in df_prep.columns:
            df_prep['volume'] = df_prep['tick_volume']
        
        # Usar 'real_volume' se disponível (preferência)
        if 'real_volume' in df_prep.columns and df_prep['real_volume'].sum() > 0:
            df_prep['volume'] = df_prep['real_volume']
        
        # Adicionar colunas de data/hora se não existirem
        if 'date' not in df_prep.columns:
            df_prep['date'] = pd.to_datetime(df_prep['time']).dt.date
        if 'hora' not in df_prep.columns:
            df_prep['hora'] = pd.to_datetime(df_prep['time']).dt.hour
        if 'minuto' not in df_prep.columns:
            df_prep['minuto'] = pd.to_datetime(df_prep['time']).dt.minute
        
        return df_prep
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calcula ATR (Average True Range)
        
        Args:
            df: DataFrame com OHLC
            period: Período do ATR
            
        Returns:
            ATR médio
        """
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Calcular True Range
        tr = np.zeros(len(df))
        for i in range(1, len(df)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        # ATR = média dos últimos N true ranges
        atr = np.mean(tr[-period:])
        return atr
    
    def _calculate_sl_tp(self, action: str, price: float, atr: float) -> tuple:
        """
        Calcula Stop Loss e Take Profit baseado em ATR
        
        Args:
            action: 'BUY' ou 'SELL'
            price: Preço atual
            atr: ATR calculado
            
        Returns:
            (sl, tp)
        """
        sl_mult = self.params.get('sl_atr_mult', 2.0)
        tp_mult = self.params.get('tp_atr_mult', 3.0)
        
        if action == 'BUY':
            sl = price - (atr * sl_mult)
            tp = price + (atr * tp_mult)
        else:  # SELL
            sl = price + (atr * sl_mult)
            tp = price - (atr * tp_mult)
        
        return sl, tp
    
    def _no_signal(self, reason: str) -> Dict:
        """
        Retorna resposta de 'sem sinal'
        
        Args:
            reason: Motivo
            
        Returns:
            Dict com action='NONE'
        """
        return {
            'action': 'NONE',
            'price': 0,
            'sl': 0,
            'tp': 0,
            'atr': 0,
            'reason': reason,
            'timestamp': None
        }
    
    def validate_signal_time(self, signal: Dict) -> bool:
        """
        Valida se sinal está dentro do horário permitido
        
        Args:
            signal: Sinal detectado
            
        Returns:
            True se horário permitido
        """
        if signal['action'] == 'NONE':
            return False
        
        timestamp = signal['timestamp']
        if timestamp is None:
            return False
        
        hora = timestamp.hour
        minuto = timestamp.minute
        
        hora_inicio = self.params.get('horario_inicio', 9)
        min_inicio = self.params.get('minuto_inicio', 15)
        hora_fim = self.params.get('horario_fim', 11)
        min_fim = self.params.get('minuto_fim', 0)
        
        # Converter para minutos desde meia-noite
        time_atual = hora * 60 + minuto
        time_inicio = hora_inicio * 60 + min_inicio
        time_fim = hora_fim * 60 + min_fim
        
        if time_atual < time_inicio:
            logger.warning(f"Sinal antes do horário ({hora}:{minuto:02d} < {hora_inicio}:{min_inicio:02d})")
            return False
        
        if time_atual > time_fim:
            logger.warning(f"Sinal após horário ({hora}:{minuto:02d} > {hora_fim}:{min_fim:02d})")
            return False
        
        return True

