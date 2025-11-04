"""
Model: MonitorSession (Sessao do monitor de trading)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class MonitorSession(Base):
    """Sessao de monitoramento (cada vez que inicia/para)"""
    
    __tablename__ = "monitor_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Estado
    is_active = Column(Boolean, default=True, index=True)
    
    # Configuracao
    strategies_active = Column(Text, nullable=True)  # JSON: lista de estrategias ativas
    dry_run = Column(Boolean, default=True)
    
    # MT5
    mt5_account = Column(String(50), nullable=True)
    mt5_server = Column(String(100), nullable=True)
    
    # Stats da sessao
    total_signals = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    total_filled = Column(Integer, default=0)
    total_rejected = Column(Integer, default=0)
    
    # PnL da sessao
    pnl_points = Column(Float, default=0.0)
    pnl_currency = Column(Float, default=0.0)
    
    # Timestamps
    started_at = Column(DateTime, server_default=func.now(), index=True)
    stopped_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<MonitorSession {self.id} ({'ATIVO' if self.is_active else 'PARADO'})>"

