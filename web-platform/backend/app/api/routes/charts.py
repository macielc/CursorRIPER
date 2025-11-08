"""
Endpoints para dados de gráficos (candles e marcadores de trades)
"""
from fastapi import APIRouter, Query, Depends, HTTPException
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
import logging

router = APIRouter(prefix="/charts", tags=["charts"])
logger = logging.getLogger(__name__)


@router.get("/candles")
def get_candles(
    symbol: str = Query("WIN$", description="Simbolo para buscar candles"),
    timeframe: int = Query(5, description="Timeframe em minutos (5, 15, 60, etc)"),
    bars: int = Query(500, description="Numero de candles para retornar")
):
    """
    Retorna candles historicos para o grafico
    
    Nota: Este endpoint requer MT5 inicializado para funcionar.
    Em ambiente de desenvolvimento, pode retornar dados mock.
    """
    try:
        import MetaTrader5 as mt5
        
        # Tentar inicializar MT5
        if not mt5.initialize():
            logger.warning("MT5 nao inicializado, retornando dados mock")
            return _get_mock_candles(bars)
        
        # Mapear timeframe para constante MT5
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1,
            240: mt5.TIMEFRAME_H4,
            1440: mt5.TIMEFRAME_D1,
        }
        
        timeframe_mt5 = timeframe_map.get(timeframe, mt5.TIMEFRAME_M5)
        
        # Buscar dados
        rates = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, bars)
        
        if rates is None or len(rates) == 0:
            mt5.shutdown()
            logger.warning(f"Nenhum dado retornado para {symbol}, usando mock")
            return _get_mock_candles(bars)
        
        # Converter para formato TradingView Lightweight Charts
        candles = []
        for rate in rates:
            candles.append({
                "time": int(rate['time']),  # Unix timestamp
                "open": float(rate['open']),
                "high": float(rate['high']),
                "low": float(rate['low']),
                "close": float(rate['close']),
            })
        
        mt5.shutdown()
        
        logger.info(f"Retornando {len(candles)} candles para {symbol} ({timeframe}m)")
        return candles
        
    except ImportError:
        logger.warning("MetaTrader5 nao instalado, retornando dados mock")
        return _get_mock_candles(bars)
    except Exception as e:
        logger.error(f"Erro ao buscar candles: {e}")
        return _get_mock_candles(bars)


@router.get("/markers")
def get_trade_markers(
    strategy: Optional[str] = Query(None, description="Filtrar por estrategia"),
    limit: int = Query(100, description="Numero maximo de trades para mostrar")
):
    """
    Retorna marcadores de trades para o grafico
    
    Os marcadores sao baseados nas ordens executadas salvas no DB.
    """
    try:
        from app.models import Order
        from app.core.database import get_db
        
        db = next(get_db())
        
        # Query ordens
        query = db.query(Order).filter(Order.status == "filled")
        
        if strategy:
            query = query.filter(Order.strategy_name == strategy)
        
        orders = query.order_by(Order.filled_at.desc()).limit(limit).all()
        
        # Converter para formato de marcadores
        markers = []
        for order in orders:
            if order.filled_at:
                marker = {
                    "time": int(order.filled_at.timestamp()),
                    "position": "belowBar" if order.action == "buy" else "aboveBar",
                    "color": "#26a69a" if order.action == "buy" else "#ef5350",
                    "shape": "arrowUp" if order.action == "buy" else "arrowDown",
                    "text": f"{order.action.upper()} @ {order.entry_price:.0f}"
                }
                markers.append(marker)
        
        logger.info(f"Retornando {len(markers)} marcadores de trades")
        return markers
        
    except Exception as e:
        logger.error(f"Erro ao buscar marcadores: {e}")
        # Retornar lista vazia em caso de erro
        return []


def _get_mock_candles(bars: int = 500) -> List[Dict]:
    """
    Gera dados mock de candles para desenvolvimento/testes
    """
    import random
    from datetime import datetime, timedelta
    
    # Preco base do WIN$
    base_price = 163000
    current_time = datetime.now().replace(second=0, microsecond=0)
    
    candles = []
    price = base_price
    
    for i in range(bars):
        # Simular movimento de preco
        open_price = price
        high_price = price + random.randint(0, 100)
        low_price = price - random.randint(0, 100)
        close_price = price + random.randint(-50, 50)
        
        # Ajustar para proximo candle
        price = close_price
        
        candle_time = current_time - timedelta(minutes=5 * (bars - i))
        
        candles.append({
            "time": int(candle_time.timestamp()),
            "open": float(open_price),
            "high": float(high_price),
            "low": float(low_price),
            "close": float(close_price),
        })
    
    return candles

