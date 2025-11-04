"""
API Routes: Strategies
CRUD completo de estrategias
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import yaml
import json

from app.core.database import get_db
from app.models import Strategy
from pydantic import BaseModel, Field

router = APIRouter(prefix="/strategies", tags=["strategies"])


# Schemas Pydantic
class StrategyBase(BaseModel):
    name: str
    display_name: str
    description: str | None = None
    symbol: str = "WIN$"
    timeframe: int = 5
    volume: float = 1.0
    parameters: dict = Field(..., description="Parametros da estrategia")


class StrategyCreate(StrategyBase):
    pass


class StrategyUpdate(BaseModel):
    display_name: str | None = None
    description: str | None = None
    symbol: str | None = None
    timeframe: int | None = None
    volume: float | None = None
    parameters: dict | None = None
    is_enabled: bool | None = None


class StrategyResponse(StrategyBase):
    id: int
    is_active: bool
    is_enabled: bool
    config_file: str
    strategy_class: str
    strategy_module: str
    total_signals: int
    total_orders: int
    last_signal_at: str | None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[StrategyResponse])
def list_strategies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """Lista todas as estrategias"""
    query = db.query(Strategy)
    
    if active_only:
        query = query.filter(Strategy.is_active == True)
    
    strategies = query.offset(skip).limit(limit).all()
    return strategies


@router.get("/{strategy_name}", response_model=StrategyResponse)
def get_strategy(strategy_name: str, db: Session = Depends(get_db)):
    """Obtem detalhes de uma estrategia"""
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estrategia '{strategy_name}' nao encontrada"
        )
    
    return strategy


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
def create_strategy(strategy: StrategyCreate, db: Session = Depends(get_db)):
    """Cria uma nova estrategia"""
    
    # Verifica se ja existe
    existing = db.query(Strategy).filter(Strategy.name == strategy.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estrategia '{strategy.name}' ja existe"
        )
    
    # Cria no banco
    db_strategy = Strategy(
        name=strategy.name,
        display_name=strategy.display_name,
        description=strategy.description,
        symbol=strategy.symbol,
        timeframe=strategy.timeframe,
        volume=strategy.volume,
        parameters=json.dumps(strategy.parameters),
        config_file=f"strategies/config_{strategy.name}.yaml",
        strategy_class="TBD",  # Sera atualizado do YAML
        strategy_module="TBD"
    )
    
    db.add(db_strategy)
    db.commit()
    db.refresh(db_strategy)
    
    return db_strategy


@router.put("/{strategy_name}", response_model=StrategyResponse)
def update_strategy(
    strategy_name: str,
    strategy_update: StrategyUpdate,
    db: Session = Depends(get_db)
):
    """Atualiza parametros de uma estrategia"""
    
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estrategia '{strategy_name}' nao encontrada"
        )
    
    # Atualizar campos fornecidos
    update_data = strategy_update.dict(exclude_unset=True)
    
    # Se atualizar parametros, converter para JSON
    if "parameters" in update_data:
        update_data["parameters"] = json.dumps(update_data["parameters"])
    
    for field, value in update_data.items():
        setattr(strategy, field, value)
    
    db.commit()
    db.refresh(strategy)
    
    return strategy


@router.delete("/{strategy_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(strategy_name: str, db: Session = Depends(get_db)):
    """Deleta uma estrategia"""
    
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estrategia '{strategy_name}' nao encontrada"
        )
    
    # Nao permite deletar se estiver ativa
    if strategy.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao e possivel deletar estrategia ativa. Desative primeiro."
        )
    
    db.delete(strategy)
    db.commit()
    
    return None


@router.post("/{strategy_name}/activate", response_model=StrategyResponse)
def activate_strategy(strategy_name: str, db: Session = Depends(get_db)):
    """Ativa uma estrategia"""
    
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estrategia '{strategy_name}' nao encontrada"
        )
    
    strategy.is_active = True
    db.commit()
    db.refresh(strategy)
    
    # TODO: Notificar monitor via WebSocket
    
    return strategy


@router.post("/{strategy_name}/deactivate", response_model=StrategyResponse)
def deactivate_strategy(strategy_name: str, db: Session = Depends(get_db)):
    """Desativa uma estrategia"""
    
    strategy = db.query(Strategy).filter(Strategy.name == strategy_name).first()
    
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estrategia '{strategy_name}' nao encontrada"
        )
    
    strategy.is_active = False
    db.commit()
    db.refresh(strategy)
    
    # TODO: Notificar monitor via WebSocket
    
    return strategy


@router.get("/discover/available")
def discover_strategies():
    """
    Descobre estrategias disponiveis no diretorio live_trading/strategies
    Usa o StrategyDiscoveryService para parsing robusto
    """
    from app.services.strategy_discovery import get_strategy_discovery
    
    service = get_strategy_discovery()
    strategies = service.discover_strategies()
    
    return {
        "strategies": strategies,
        "count": len(strategies),
        "active_strategy": service.get_active_strategy()
    }

