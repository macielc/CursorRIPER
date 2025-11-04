"""
Model: Strategy (Estrategia)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from app.core.database import Base


class Strategy(Base):
    """Estrategia de trading"""
    
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Estado
    is_active = Column(Boolean, default=False)
    is_enabled = Column(Boolean, default=True)  # Pode ser desabilitada sem deletar
    
    # Trading
    symbol = Column(String(20), nullable=False, default="WIN$")
    timeframe = Column(Integer, nullable=False, default=5)  # Minutos
    volume = Column(Float, nullable=False, default=1.0)
    
    # Parametros (JSON como string)
    parameters = Column(Text, nullable=False)  # JSON serializado
    
    # Metadados
    config_file = Column(String(200), nullable=False)  # Path para config YAML
    strategy_class = Column(String(100), nullable=False)
    strategy_module = Column(String(200), nullable=False)
    
    # Stats
    total_signals = Column(Integer, default=0)
    total_orders = Column(Integer, default=0)
    last_signal_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Strategy {self.name} ({self.symbol})>"

