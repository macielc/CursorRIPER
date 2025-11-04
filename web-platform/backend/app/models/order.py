"""
Model: Order (Ordem executada)
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class OrderAction(str, enum.Enum):
    """Tipo de ordem"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    """Status da ordem"""
    PENDING = "pending"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    CLOSED = "closed"


class Order(Base):
    """Ordem de trading"""
    
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificacao
    mt5_order_id = Column(String(50), nullable=True, index=True)  # ID do MT5
    strategy_name = Column(String(100), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    
    # Dados da ordem
    action = Column(SQLEnum(OrderAction), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    
    # Precos
    entry_price = Column(Float, nullable=False)
    sl_price = Column(Float, nullable=True)
    tp_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    
    # Volume
    volume = Column(Float, nullable=False, default=1.0)
    
    # PnL
    pnl_points = Column(Float, nullable=True)
    pnl_currency = Column(Float, nullable=True)
    
    # Detalhes da estrategia
    elephant_bar_time = Column(DateTime, nullable=True)  # Barra elefante detectada
    signal_metadata = Column(Text, nullable=True)  # JSON com metadados do sinal
    
    # Comentarios
    comment = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), index=True)
    filled_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Order {self.id} {self.action.value} {self.symbol} @ {self.entry_price}>"

