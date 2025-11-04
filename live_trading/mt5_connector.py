"""
MT5 Connector - Interface para comunicação com MetaTrader 5

Responsabilidades:
- Conectar/desconectar do MT5
- Buscar dados históricos (candles)
- Enviar ordens
- Monitorar posições abertas
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger('MT5Connector')


class MT5Connector:
    """Wrapper para API do MetaTrader5"""
    
    def __init__(self, login: Optional[int] = None, password: Optional[str] = None, server: Optional[str] = None):
        """
        Inicializa conector MT5
        
        Args:
            login: Número da conta (opcional, usa última conta se não especificado)
            password: Senha (opcional)
            server: Servidor da corretora (opcional)
        """
        self.login = login
        self.password = password
        self.server = server
        self.connected = False
        
    def connect(self) -> bool:
        """
        Conecta ao MT5
        
        Returns:
            True se conectado com sucesso
        """
        try:
            if not mt5.initialize():
                logger.error(f"MT5 initialize() failed, error code = {mt5.last_error()}")
                return False
            
            # Se credenciais fornecidas, fazer login
            if self.login and self.password and self.server:
                authorized = mt5.login(self.login, password=self.password, server=self.server)
                if not authorized:
                    logger.error(f"Login failed, error code = {mt5.last_error()}")
                    mt5.shutdown()
                    return False
            
            self.connected = True
            
            # Log info da conta
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"OK - Conectado ao MT5")
                logger.info(f"  Conta: {account_info.login}")
                logger.info(f"  Servidor: {account_info.server}")
                logger.info(f"  Saldo: R$ {account_info.balance:.2f}")
                logger.info(f"  Margem livre: R$ {account_info.margin_free:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar: {e}")
            return False
    
    def disconnect(self):
        """Desconecta do MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Desconectado do MT5")
    
    def get_candles(self, symbol: str, timeframe: int, count: int = 50) -> Optional[pd.DataFrame]:
        """
        Busca últimos N candles do símbolo
        
        Args:
            symbol: Símbolo (ex: 'WINFUT', 'WIN$')
            timeframe: Timeframe MT5 (ex: mt5.TIMEFRAME_M5)
            count: Quantidade de candles
            
        Returns:
            DataFrame com OHLCV ou None se erro
        """
        if not self.connected:
            logger.error("MT5 não conectado")
            return None
        
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"Nenhum dado retornado para {symbol}")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            return df
            
        except Exception as e:
            logger.error(f"Erro ao buscar candles: {e}")
            return None
    
    def send_order(
        self,
        symbol: str,
        order_type: int,
        volume: float,
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        comment: str = "BarraElefante",
        magic: int = 123456
    ) -> Dict:
        """
        Envia ordem para MT5
        
        Args:
            symbol: Símbolo
            order_type: mt5.ORDER_TYPE_BUY ou mt5.ORDER_TYPE_SELL
            volume: Quantidade de contratos
            price: Preço (None = market)
            sl: Stop Loss
            tp: Take Profit
            comment: Comentário da ordem
            magic: Magic number
            
        Returns:
            Dict com resultado da ordem
        """
        if not self.connected:
            return {'success': False, 'error': 'MT5 não conectado'}
        
        try:
            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            
            # Adicionar preço se fornecido (limit order)
            if price:
                request["price"] = price
            
            # Adicionar SL/TP se fornecidos
            if sl:
                request["sl"] = sl
            if tp:
                request["tp"] = tp
            
            # Enviar ordem
            result = mt5.order_send(request)
            
            if result is None:
                return {'success': False, 'error': f'order_send failed, error = {mt5.last_error()}'}
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'retcode': result.retcode,
                    'error': f'Ordem rejeitada: {result.comment}'
                }
            
            logger.info(f"✅ Ordem executada: {comment}")
            logger.info(f"  Tipo: {'BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL'}")
            logger.info(f"  Volume: {volume}")
            logger.info(f"  Preço: {result.price}")
            logger.info(f"  Ticket: {result.order}")
            
            return {
                'success': True,
                'order': result.order,
                'price': result.price,
                'volume': result.volume,
                'comment': result.comment
            }
            
        except Exception as e:
            logger.error(f"Erro ao enviar ordem: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Retorna posições abertas
        
        Args:
            symbol: Filtrar por símbolo (None = todas)
            
        Returns:
            Lista de posições
        """
        if not self.connected:
            return []
        
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            
            if positions is None:
                return []
            
            return [
                {
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'profit': pos.profit,
                    'comment': pos.comment
                }
                for pos in positions
            ]
            
        except Exception as e:
            logger.error(f"Erro ao buscar posições: {e}")
            return []
    
    def close_position(self, ticket: int) -> Dict:
        """
        Fecha posição específica
        
        Args:
            ticket: Ticket da posição
            
        Returns:
            Dict com resultado
        """
        if not self.connected:
            return {'success': False, 'error': 'MT5 não conectado'}
        
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return {'success': False, 'error': f'Posição {ticket} não encontrada'}
            
            position = position[0]
            
            # Preparar ordem de fechamento (ordem reversa)
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": ticket,
                "magic": position.magic,
                "comment": "Fechamento",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_RETURN,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {'success': False, 'error': f'Falha ao fechar: {result.comment}'}
            
            logger.info(f"✅ Posição {ticket} fechada")
            
            return {'success': True, 'ticket': ticket, 'profit': position.profit}
            
        except Exception as e:
            logger.error(f"Erro ao fechar posição: {e}")
            return {'success': False, 'error': str(e)}
    
    def close_all_positions(self, symbol: Optional[str] = None) -> int:
        """
        Fecha todas as posições abertas
        
        Args:
            symbol: Filtrar por símbolo (None = todas)
            
        Returns:
            Quantidade de posições fechadas
        """
        positions = self.get_positions(symbol)
        closed = 0
        
        for pos in positions:
            result = self.close_position(pos['ticket'])
            if result['success']:
                closed += 1
        
        return closed
    
    def get_account_info(self) -> Optional[Dict]:
        """
        Retorna informações da conta
        
        Returns:
            Dict com info da conta ou None
        """
        if not self.connected:
            return None
        
        try:
            info = mt5.account_info()
            if info is None:
                return None
            
            return {
                'login': info.login,
                'server': info.server,
                'balance': info.balance,
                'equity': info.equity,
                'margin': info.margin,
                'margin_free': info.margin_free,
                'margin_level': info.margin_level,
                'profit': info.profit
            }
            
        except Exception as e:
            logger.error(f"Erro ao buscar info da conta: {e}")
            return None

