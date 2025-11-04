"""
Backtest Engine Otimizado

Engine de backtesting vetorizado com NumPy para máxima performance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Union
from .metrics import MetricsCalculator
from .strategy_base import StrategyBase


class BacktestEngine:
    """
    Engine de backtesting vetorizado e otimizado
    """
    
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000.0, verbose: bool = False):
        """
        Args:
            data: DataFrame com OHLCV + ATR
            initial_capital: Capital inicial
            verbose: Se True, printa logs de debug (desabilitar para otimização massiva)
        """
        # OTIMIZACAO CRITICA: Não copiar DataFrame em modo otimização (economiza RAM)
        # Com 32 workers, .copy() multiplica uso de memória por 32x
        if verbose:
            self.df = data.copy()  # Modo debug: copiar para segurança
        else:
            self.df = data  # Modo otimização: usar referência direta (read-only)
        
        self.initial_capital = initial_capital
        self.verbose = verbose
        self.metrics_calc = MetricsCalculator()
        
        # Pre-calcular arrays NumPy para performance
        self.open = self.df['open'].values  # CORRECAO #10: Adicionar OPEN para slippage realista
        self.high = self.df['high'].values
        self.low = self.df['low'].values
        self.close = self.df['close'].values
        self.atr = self.df['atr'].values
        self.n_candles = len(self.df)
        
        # CORRECAO #11: Armazenar timestamps para fechamento intraday
        if 'time' in self.df.columns:
            self.timestamps = pd.to_datetime(self.df['time'])
        else:
            self.timestamps = None
    
    def run_strategy(self, strategy: Union[StrategyBase, str], params: Dict) -> Dict:
        """
        Executa backtest de qualquer estratégia
        
        Args:
            strategy: Instância de StrategyBase ou nome da estratégia
            params: Parâmetros da estratégia
        
        Returns:
            Dict com trades e métricas
        """
        # Se receber string, carregar estratégia
        if isinstance(strategy, str):
            strategy = self._load_strategy(strategy, params)
        elif not isinstance(strategy, StrategyBase):
            # Se recebeu params, criar estratégia com params
            strategy_class = strategy
            strategy = strategy_class(params)
        
        try:
            # Gerar sinais usando a estratégia
            signals = strategy.generate_signals(self.df)
            
            # Simular trades
            # MODULAR: SL/TP podem ser fixos (float) ou dinâmicos (arrays)
            sl_buffer = signals.get('sl_buffer_mult')
            tp_risk = signals.get('tp_risk_mult')
            sl_array = signals.get('sl_prices')  # Array de SL específicos (opcional)
            tp_array = signals.get('tp_prices')  # Array de TP específicos (opcional)
            
            # CORRECAO #12: Passar tuple (hora, minuto) para fechamento
            hora_fechamento = params.get('horario_fechamento', 12)
            minuto_fechamento = params.get('minuto_fechamento', 15)
            
            trades = self._simulate_trades(
                signals['entries_long'],
                signals['entries_short'],
                sl_buffer,
                tp_risk,
                start_idx=signals['start_idx'],
                sl_prices=sl_array,
                tp_prices=tp_array,
                fechar_intraday=True,
                horario_fim=(hora_fechamento, minuto_fechamento)
            )
            
            # Calcular métricas
            if len(trades) == 0:
                return self._empty_result(params, "Nenhum trade gerado")
            
            metrics = self.metrics_calc.calculate_all(trades)
            metrics['params'] = params
            metrics['success'] = True
            metrics['strategy'] = strategy.name
            metrics['trades'] = trades  # IMPORTANTE: Incluir lista de trades!
            
            return metrics
            
        except Exception as e:
            return self._empty_result(params, str(e))
    
    def _load_strategy(self, strategy_name: str, params: Dict) -> StrategyBase:
        """Carrega estratégia por nome usando auto-discovery"""
        import sys
        from pathlib import Path
        
        # Adicionar strategies ao path
        strategies_path = Path(__file__).parent.parent / 'strategies'
        if str(strategies_path) not in sys.path:
            sys.path.insert(0, str(strategies_path))
        
        # Importar auto-discovery
        from strategies import get_strategy
        
        strategy_class = get_strategy(strategy_name)
        return strategy_class(params)
    
    def run_power_breakout(self, params: Dict) -> Dict:
        """
        DEPRECATED: Use run_strategy('power_breakout', params)
        
        Mantido para compatibilidade com código antigo
        """
        """
        Executa backtest da estratégia Power Breakout
        
        Args:
            params: Dicionário com parâmetros da estratégia
                - cons_len_min: Comprimento mínimo de consolidação
                - cons_len_max: Comprimento máximo de consolidação
                - cons_range_mult: Multiplicador ATR para range de consolidação
                - gatilho_pct: Percentual dos últimos candles para gatilho
                - sl_buffer_mult: Multiplicador ATR para stop loss
                - tp_risk_mult: Multiplicador do risco para take profit
        
        Returns:
            Dict com trades e métricas
        """
        try:
            # Parâmetros
            cons_len = int((params['cons_len_min'] + params['cons_len_max']) / 2)
            cons_range_mult = params['cons_range_mult']
            gatilho_pct = params['gatilho_pct']
            sl_buffer_mult = params['sl_buffer_mult']
            tp_risk_mult = params['tp_risk_mult']
            
            # Validação
            if cons_len >= self.n_candles - 10:
                return self._empty_result(params, "cons_len muito grande")
            
            # 1) Detectar consolidações (vetorizado)
            rolling_high = pd.Series(self.high).rolling(window=cons_len).max().values
            rolling_low = pd.Series(self.low).rolling(window=cons_len).min().values
            rolling_range = rolling_high - rolling_low
            
            limite = self.atr * cons_range_mult
            is_consolidation = rolling_range <= limite
            
            # 2) Calcular gatilhos
            n_ultimos = max(1, int(cons_len * gatilho_pct))
            gatilho_high = pd.Series(self.high).rolling(window=n_ultimos).max().shift(1).values
            gatilho_low = pd.Series(self.low).rolling(window=n_ultimos).min().shift(1).values
            
            # 3) Sinais de entrada (vetorizado)
            entries_long = (self.high >= gatilho_high) & np.roll(is_consolidation, 1)
            entries_short = (self.low <= gatilho_low) & np.roll(is_consolidation, 1)
            
            # 4) Simular trades (loop necessário para SL/TP)
            # CORRECAO #12: Passar tuple (hora, minuto) para fechamento
            hora_fechamento = params.get('horario_fechamento', 12)
            minuto_fechamento = params.get('minuto_fechamento', 15)
            
            trades = self._simulate_trades(
                entries_long, 
                entries_short,
                sl_buffer_mult,
                tp_risk_mult,
                start_idx=cons_len + 10,
                fechar_intraday=True,
                horario_fim=(hora_fechamento, minuto_fechamento)
            )
            
            # 5) Calcular métricas
            if len(trades) == 0:
                return self._empty_result(params, "Nenhum trade gerado")
            
            metrics = self.metrics_calc.calculate_all(trades)
            metrics['params'] = params
            metrics['success'] = True
            
            return metrics
            
        except Exception as e:
            return self._empty_result(params, str(e))
    
    def _simulate_trades(
        self,
        entries_long: np.ndarray,
        entries_short: np.ndarray,
        sl_buffer_mult: float,
        tp_risk_mult: float,
        start_idx: int = 0,
        sl_prices: np.ndarray = None,
        tp_prices: np.ndarray = None,
        fechar_intraday: bool = True,
        horario_fim: int = 17
    ) -> List[Dict]:
        """
        Simula trades com SL e TP
        
        MODULAR: Suporta SL/TP fixos (mult) ou dinâmicos (arrays)
        
        Args:
            sl_buffer_mult, tp_risk_mult: Multiplicadores fixos (se sl_prices/tp_prices = None)
            sl_prices, tp_prices: Arrays de SL/TP específicos por candle (opcional)
            fechar_intraday: Fechar posições ao final do dia (INTRADAY)
            horario_fim: Hora para fechamento intraday (default 17h)
        """
        trades = []
        position = None
        same_candle_entries = 0  # DEBUG: contar entradas no mesmo candle após fechamento
        slippage_entries = 0  # DEBUG: contar entradas com slippage de 1 barra
        pending_entry = None  # CORRECAO #10: Simular slippage de 1 barra (entrar na proxima barra)
        
        for i in range(start_idx, self.n_candles):
            trade_just_closed = False
            
            # CORRECAO #10: Processar entrada pendente da barra anterior
            # Simula slippage de 1 barra: detecta sinal em i-1, entra no OPEN de i
            if pending_entry is not None:
                # Se ja tem posicao, descartar pending_entry
                if position is not None:
                    pending_entry = None
            
            if pending_entry is not None and position is None:
                entry_type = pending_entry['type']
                entry_price = self.open[i]  # OPEN da barra atual (1 barra apos deteccao)
                
                # Calcular SL/TP
                if sl_prices is not None and tp_prices is not None:
                    # Usar SL/TP da barra de deteccao (i-1)
                    sl = pending_entry['sl']
                    tp = pending_entry['tp']
                else:
                    # Fallback: calcular por ATR
                    atr_val = self.atr[i]
                    if entry_type == 'LONG':
                        sl = entry_price - (atr_val * sl_buffer_mult)
                        risk = entry_price - sl
                        with np.errstate(over='ignore', invalid='ignore'):
                            tp = entry_price + (risk * tp_risk_mult)
                            tp = np.nan_to_num(tp, nan=0, posinf=1e10, neginf=-1e10)
                    else:  # SHORT
                        sl = entry_price + (atr_val * sl_buffer_mult)
                        risk = sl - entry_price
                        with np.errstate(over='ignore', invalid='ignore'):
                            tp = entry_price - (risk * tp_risk_mult)
                            tp = np.nan_to_num(tp, nan=0, posinf=1e10, neginf=-1e10)
                
                position = {
                    'entry_idx': i,  # Entra na barra atual, nao na de deteccao
                    'type': entry_type,
                    'entry': entry_price,
                    'sl': sl,
                    'tp': tp
                }
                
                slippage_entries += 1  # DEBUG: contar entrada com slippage
                pending_entry = None  # Limpar entrada pendente
            
            # CORRECAO #11/#12: Fechar posicao ao final do dia (INTRADAY!) as 12h15
            if fechar_intraday and position is not None and self.timestamps is not None:
                current_time = self.timestamps.iloc[i]
                hora_atual = current_time.hour
                minuto_atual = current_time.minute
                
                # CORRECAO #12: horario_fim agora é um tuple (hora, minuto)
                # Ex: (12, 15) = 12h15
                hora_fechamento, minuto_fechamento = horario_fim if isinstance(horario_fim, tuple) else (horario_fim, 0)
                
                # Se atingiu horario de fechamento (12h15), fechar posicao
                if hora_atual > hora_fechamento or (hora_atual == hora_fechamento and minuto_atual >= minuto_fechamento):
                    exit_price = self.close[i]
                    pnl = (exit_price - position['entry']) if position['type'] == 'LONG' else (position['entry'] - exit_price)
                    
                    trades.append({
                        'entry_idx': position['entry_idx'],
                        'exit_idx': i,
                        'type': position['type'],
                        'entry': position['entry'],
                        'exit': exit_price,
                        'sl': position['sl'],
                        'tp': position['tp'],
                        'pnl': pnl,
                        'exit_reason': 'INTRADAY_CLOSE'
                    })
                    
                    position = None
                    trade_just_closed = True
                    # Nao fazer continue - permitir novo sinal no mesmo candle
            
            # Se já tem posição, verificar saída
            if position is not None:
                exit_signal = False
                exit_price = None
                exit_reason = None
                
                if position['type'] == 'LONG':
                    # SL atingido
                    if self.low[i] <= position['sl']:
                        exit_price = position['sl']
                        exit_reason = 'SL'
                        exit_signal = True
                    # TP atingido
                    elif self.high[i] >= position['tp']:
                        exit_price = position['tp']
                        exit_reason = 'TP'
                        exit_signal = True
                
                else:  # SHORT
                    # SL atingido
                    if self.high[i] >= position['sl']:
                        exit_price = position['sl']
                        exit_reason = 'SL'
                        exit_signal = True
                    # TP atingido
                    elif self.low[i] <= position['tp']:
                        exit_price = position['tp']
                        exit_reason = 'TP'
                        exit_signal = True
                
                if exit_signal:
                    pnl = (exit_price - position['entry']) if position['type'] == 'LONG' else (position['entry'] - exit_price)
                    
                    trades.append({
                        'entry_idx': position['entry_idx'],
                        'exit_idx': i,
                        'type': position['type'],
                        'entry': position['entry'],
                        'exit': exit_price,
                        'sl': position['sl'],
                        'tp': position['tp'],
                        'pnl': pnl,
                        'exit_reason': exit_reason
                    })
                    
                    position = None
                    trade_just_closed = True
                    # CRÍTICO: NÃO fazer continue aqui!
                    # Precisamos re-checar sinais no MESMO candle após fechar trade
                    # (cair no código de entrada abaixo)
                
                # Se ainda tem posição, não entra em novo trade
                if position is not None:
                    continue
            
            # Se não tem posição, verificar entrada
            if position is None and pending_entry is None:
                # CORRECAO #10: Ao inves de entrar imediatamente, armazenar entrada pendente
                # Na proxima barra, entrara no OPEN (simulando slippage realista)
                
                # LONG
                if entries_long[i]:
                    if trade_just_closed:
                        same_candle_entries += 1
                    
                    # Armazenar SL/TP se disponíveis
                    if sl_prices is not None and tp_prices is not None:
                        sl = sl_prices[i]
                        tp = tp_prices[i]
                    else:
                        sl = None
                        tp = None
                    
                    pending_entry = {
                        'type': 'LONG',
                        'sl': sl,
                        'tp': tp
                    }
                
                # SHORT
                elif entries_short[i]:
                    if trade_just_closed:
                        same_candle_entries += 1
                    
                    # Armazenar SL/TP se disponíveis
                    if sl_prices is not None and tp_prices is not None:
                        sl = sl_prices[i]
                        tp = tp_prices[i]
                    else:
                        sl = None
                        tp = None
                    
                    pending_entry = {
                        'type': 'SHORT',
                        'sl': sl,
                        'tp': tp
                    }
        
        # DEBUG: printar estatísticas (só se verbose=True)
        if self.verbose:
            if same_candle_entries > 0:
                print(f"  [DEBUG] Entradas no mesmo candle apos fechamento: {same_candle_entries}")
            if slippage_entries > 0:
                print(f"  [REALISMO] Entradas com slippage de 1 barra (OPEN): {slippage_entries} de {len(trades)}")
        
        return trades
    
    def run_custom_strategy(
        self, 
        strategy_func: callable, 
        params: Dict
    ) -> Dict:
        """
        Executa backtest de estratégia customizada
        
        Args:
            strategy_func: Função que recebe (df, params) e retorna sinais
            params: Parâmetros da estratégia
        
        Returns:
            Dict com trades e métricas
        """
        try:
            # Chamar função da estratégia
            signals = strategy_func(self.df, params)
            
            # signals deve retornar: entries_long, entries_short, sl_buffer, tp_mult
            entries_long = signals['entries_long']
            entries_short = signals['entries_short']
            sl_buffer = signals.get('sl_buffer_mult', 0.5)
            tp_mult = signals.get('tp_risk_mult', 2.0)
            
            # Simular trades
            # CORRECAO #12: Passar tuple (hora, minuto) para fechamento
            hora_fechamento = params.get('horario_fechamento', 12)
            minuto_fechamento = params.get('minuto_fechamento', 15)
            
            trades = self._simulate_trades(
                entries_long,
                entries_short,
                sl_buffer,
                tp_mult,
                start_idx=signals.get('start_idx', 0),
                fechar_intraday=True,
                horario_fim=(hora_fechamento, minuto_fechamento)
            )
            
            # Calcular métricas
            if len(trades) == 0:
                return self._empty_result(params, "Nenhum trade gerado")
            
            metrics = self.metrics_calc.calculate_all(trades)
            metrics['params'] = params
            metrics['success'] = True
            
            return metrics
            
        except Exception as e:
            return self._empty_result(params, str(e))
    
    def _empty_result(self, params: Dict, error_msg: str) -> Dict:
        """Resultado vazio em caso de erro"""
        metrics = self.metrics_calc._empty_metrics()
        metrics['params'] = params
        metrics['success'] = False
        metrics['error'] = error_msg
        return metrics

