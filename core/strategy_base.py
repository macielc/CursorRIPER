"""
Base para Estratégias Customizadas

Define a interface que todas as estratégias devem implementar
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, Tuple


class StrategyBase(ABC):
    """
    Classe base para todas as estratégias
    
    Todas as estratégias devem herdar desta classe e implementar:
    - get_param_grid(): Retorna grid de parâmetros para otimização
    - generate_signals(): Gera sinais de entrada/saída
    """
    
    def __init__(self, params: Dict):
        """
        Args:
            params: Dicionário com parâmetros da estratégia
        """
        self.params = params
        self.name = self.__class__.__name__
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        """
        Gera sinais de entrada e saída
        
        Args:
            df: DataFrame com dados OHLCV + indicadores
        
        Returns:
            Dict com:
                - entries_long: np.ndarray (bool) - Sinais de entrada LONG
                - entries_short: np.ndarray (bool) - Sinais de entrada SHORT
                - sl_buffer_mult: float - Multiplicador ATR para stop loss
                - tp_risk_mult: float - Multiplicador de risco para take profit
                - start_idx: int - Índice inicial para começar trades
        """
        pass
    
    @staticmethod
    @abstractmethod
    def get_param_grid(n_tests: int = None, grid_type: str = None) -> Dict:
        """
        Retorna grid de parâmetros para otimização
        
        MODULAR: A estratégia decide internamente qual grid usar!
        
        Args:
            n_tests: Número aproximado de testes desejado (preferencial)
            grid_type: 'quick', 'default', 'massive' (fallback se n_tests não fornecido)
        
        Returns:
            Dict com ranges de parâmetros
            
        Nota:
            Se n_tests for fornecido, a estratégia deve retornar um grid
            apropriado para esse número de testes. Se grid_type for fornecido,
            usar como fallback.
        """
        pass
    
    def validate_params(self) -> bool:
        """
        Valida se os parâmetros são válidos
        
        Returns:
            True se válidos, False caso contrário
        """
        return True
    
    def get_description(self) -> str:
        """
        Retorna descrição da estratégia
        
        Returns:
            String com descrição
        """
        return f"{self.name} - Parâmetros: {self.params}"


class PowerBreakoutStrategy(StrategyBase):
    """
    Estratégia Power Breakout
    
    Detecta consolidações e opera rompimentos
    """
    
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        """
        Gera sinais de entrada para Power Breakout
        """
        # Extrair parâmetros
        cons_len_min = self.params.get('cons_len_min', 10)
        cons_len_max = self.params.get('cons_len_max', 25)
        cons_range_mult = self.params.get('cons_range_mult', 3.0)
        gatilho_pct = self.params.get('gatilho_pct', 0.6)
        sl_buffer_mult = self.params.get('sl_buffer_mult', 0.5)
        tp_risk_mult = self.params.get('tp_risk_mult', 2.0)
        
        # Calcular cons_len médio
        cons_len = int((cons_len_min + cons_len_max) / 2)
        
        # Validar
        if cons_len >= len(df) - 10:
            return self._empty_signals(len(df))
        
        # Arrays NumPy
        high = df['high'].values
        low = df['low'].values
        atr = df['atr'].values
        
        # 1) Detectar consolidações
        rolling_high = pd.Series(high).rolling(window=cons_len).max().values
        rolling_low = pd.Series(low).rolling(window=cons_len).min().values
        rolling_range = rolling_high - rolling_low
        
        limite = atr * cons_range_mult
        is_consolidation = rolling_range <= limite
        
        # 2) Calcular gatilhos
        n_ultimos = max(1, int(cons_len * gatilho_pct))
        gatilho_high = pd.Series(high).rolling(window=n_ultimos).max().shift(1).values
        gatilho_low = pd.Series(low).rolling(window=n_ultimos).min().shift(1).values
        
        # 3) Sinais de entrada
        entries_long = (high >= gatilho_high) & np.roll(is_consolidation, 1)
        entries_short = (low <= gatilho_low) & np.roll(is_consolidation, 1)
        
        return {
            'entries_long': entries_long,
            'entries_short': entries_short,
            'sl_buffer_mult': sl_buffer_mult,
            'tp_risk_mult': tp_risk_mult,
            'start_idx': cons_len + 10
        }
    
    @staticmethod
    def get_param_grid(grid_type: str = 'default') -> Dict:
        """
        Retorna grid de parâmetros para Power Breakout
        """
        if grid_type == 'quick':
            return {
                'cons_len_min': [8, 12, 16],
                'cons_len_max': [22, 25, 30],
                'cons_range_mult': [2.0, 3.0, 4.0],
                'gatilho_pct': [0.50, 0.60, 0.70],
                'sl_buffer_mult': [0.3, 0.5, 0.7],
                'tp_risk_mult': [2.5, 3.5, 5.0],
            }
        elif grid_type == 'massive':
            return {
                'cons_len_min': [6, 8, 10, 12, 14, 16, 18, 20],
                'cons_len_max': [20, 22, 25, 28, 30, 32, 35],
                'cons_range_mult': np.arange(1.0, 5.1, 0.15),
                'gatilho_pct': np.arange(0.35, 0.86, 0.05),
                'sl_buffer_mult': np.arange(0.1, 1.1, 0.05),
                'tp_risk_mult': np.arange(1.5, 8.1, 0.25),
            }
        else:  # default
            return {
                'cons_len_min': [6, 8, 10, 12, 14, 16],
                'cons_len_max': [20, 22, 25, 28, 30],
                'cons_range_mult': np.arange(1.0, 4.5, 0.2),
                'gatilho_pct': np.arange(0.40, 0.81, 0.05),
                'sl_buffer_mult': np.arange(0.1, 1.0, 0.1),
                'tp_risk_mult': np.arange(2.0, 7.5, 0.5),
            }
    
    def _empty_signals(self, length: int) -> Dict:
        """Retorna sinais vazios"""
        return {
            'entries_long': np.zeros(length, dtype=bool),
            'entries_short': np.zeros(length, dtype=bool),
            'sl_buffer_mult': 0.5,
            'tp_risk_mult': 2.0,
            'start_idx': 0
        }


class InsideBarStrategy(StrategyBase):
    """
    Estratégia Inside Bar
    
    Opera rompimentos de inside bars (candle dentro do anterior)
    """
    
    def generate_signals(self, df: pd.DataFrame) -> Dict:
        """
        Gera sinais de entrada para Inside Bar
        """
        # Parâmetros
        min_mother_size = self.params.get('min_mother_size', 2.0)  # ATR mult
        sl_buffer_mult = self.params.get('sl_buffer_mult', 0.3)
        tp_risk_mult = self.params.get('tp_risk_mult', 2.5)
        
        # Arrays
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        atr = df['atr'].values
        
        n = len(df)
        entries_long = np.zeros(n, dtype=bool)
        entries_short = np.zeros(n, dtype=bool)
        
        # Detectar inside bars
        for i in range(2, n):
            # Mother candle (i-1)
            mother_high = high[i-1]
            mother_low = low[i-1]
            mother_range = mother_high - mother_low
            
            # Inside bar (i)
            inside_high = high[i]
            inside_low = low[i]
            
            # Verificar se é inside bar
            is_inside = (inside_high <= mother_high) and (inside_low >= mother_low)
            
            # Verificar tamanho mínimo da mother
            min_size = atr[i-1] * min_mother_size
            size_ok = mother_range >= min_size
            
            if is_inside and size_ok:
                # Próximo candle (i+1) - verificar rompimento
                if i+1 < n:
                    # LONG: rompe máxima da mother
                    if high[i+1] > mother_high:
                        entries_long[i+1] = True
                    
                    # SHORT: rompe mínima da mother
                    elif low[i+1] < mother_low:
                        entries_short[i+1] = True
        
        return {
            'entries_long': entries_long,
            'entries_short': entries_short,
            'sl_buffer_mult': sl_buffer_mult,
            'tp_risk_mult': tp_risk_mult,
            'start_idx': 3
        }
    
    @staticmethod
    def get_param_grid(grid_type: str = 'default') -> Dict:
        """
        Retorna grid de parâmetros para Inside Bar
        """
        if grid_type == 'quick':
            return {
                'min_mother_size': [1.5, 2.0, 2.5],
                'sl_buffer_mult': [0.2, 0.3, 0.5],
                'tp_risk_mult': [2.0, 2.5, 3.0],
            }
        elif grid_type == 'massive':
            return {
                'min_mother_size': np.arange(1.0, 3.1, 0.2),
                'sl_buffer_mult': np.arange(0.1, 0.8, 0.1),
                'tp_risk_mult': np.arange(1.5, 4.1, 0.25),
            }
        else:  # default
            return {
                'min_mother_size': np.arange(1.5, 3.0, 0.25),
                'sl_buffer_mult': np.arange(0.2, 0.6, 0.1),
                'tp_risk_mult': np.arange(2.0, 4.0, 0.5),
            }

