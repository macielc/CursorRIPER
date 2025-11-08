"""
API Routes: Orders
Gerenciamento de ordens executadas
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models import Order, OrderStatus, OrderAction
from pydantic import BaseModel

router = APIRouter(prefix="/orders", tags=["orders"])


# Schemas
class OrderResponse(BaseModel):
    id: int
    mt5_order_id: str | None
    strategy_name: str
    symbol: str
    action: str
    status: str
    entry_price: float
    sl_price: float | None
    tp_price: float | None
    exit_price: float | None
    volume: float
    pnl_points: float | None
    pnl_currency: float | None
    created_at: str
    filled_at: str | None
    closed_at: str | None
    
    class Config:
        from_attributes = True


class OrderStats(BaseModel):
    total_orders: int
    total_filled: int
    total_pending: int
    total_closed: int
    winners: int
    losers: int
    win_rate: float
    total_pnl_points: float
    total_pnl_currency: float
    avg_pnl_points: float
    profit_factor: float


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    skip: int = 0,
    limit: int = 100,
    strategy_name: Optional[str] = None,
    symbol: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Lista ordens com filtros"""
    
    query = db.query(Order)
    
    if strategy_name:
        query = query.filter(Order.strategy_name == strategy_name)
    
    if symbol:
        query = query.filter(Order.symbol == symbol)
    
    if status:
        query = query.filter(Order.status == status)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Order.created_at >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < date_to_obj)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    """Obtem detalhes de uma ordem"""
    
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(status_code=404, detail="Ordem nao encontrada")
    
    return order


@router.get("/stats/summary", response_model=OrderStats)
def get_order_stats(
    strategy_name: Optional[str] = None,
    symbol: Optional[str] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Calcula estatisticas de ordens"""
    
    query = db.query(Order)
    
    if strategy_name:
        query = query.filter(Order.strategy_name == strategy_name)
    
    if symbol:
        query = query.filter(Order.symbol == symbol)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Order.created_at >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < date_to_obj)
    
    orders = query.all()
    
    # Calcular stats
    total_orders = len(orders)
    total_filled = len([o for o in orders if o.status in [OrderStatus.FILLED, OrderStatus.TP_HIT, OrderStatus.SL_HIT, OrderStatus.CLOSED]])
    total_pending = len([o for o in orders if o.status == OrderStatus.PENDING])
    total_closed = len([o for o in orders if o.status in [OrderStatus.TP_HIT, OrderStatus.SL_HIT, OrderStatus.CLOSED]])
    
    closed_orders = [o for o in orders if o.pnl_points is not None]
    winners = len([o for o in closed_orders if o.pnl_points > 0])
    losers = len([o for o in closed_orders if o.pnl_points < 0])
    
    win_rate = (winners / len(closed_orders) * 100) if closed_orders else 0.0
    
    total_pnl_points = sum([o.pnl_points for o in closed_orders if o.pnl_points])
    total_pnl_currency = sum([o.pnl_currency for o in closed_orders if o.pnl_currency])
    avg_pnl_points = total_pnl_points / len(closed_orders) if closed_orders else 0.0
    
    # Profit factor
    gross_profit = sum([o.pnl_points for o in closed_orders if o.pnl_points and o.pnl_points > 0])
    gross_loss = abs(sum([o.pnl_points for o in closed_orders if o.pnl_points and o.pnl_points < 0]))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0
    
    return OrderStats(
        total_orders=total_orders,
        total_filled=total_filled,
        total_pending=total_pending,
        total_closed=total_closed,
        winners=winners,
        losers=losers,
        win_rate=win_rate,
        total_pnl_points=total_pnl_points,
        total_pnl_currency=total_pnl_currency,
        avg_pnl_points=avg_pnl_points,
        profit_factor=profit_factor
    )


@router.post("/close-all")
def close_all_positions(db: Session = Depends(get_db)):
    """
    Fecha todas as posicoes abertas (EMERGENCIA)
    """
    # TODO: Integrar com MT5 para fechar ordens reais
    
    open_orders = db.query(Order).filter(
        Order.status.in_([OrderStatus.FILLED, OrderStatus.PENDING])
    ).all()
    
    closed_count = 0
    
    for order in open_orders:
        order.status = OrderStatus.CLOSED
        order.closed_at = datetime.utcnow()
        closed_count += 1
    
    db.commit()
    
    return {
        "message": f"{closed_count} posicoes fechadas",
        "closed_count": closed_count
    }


@router.get("/today/summary")
def get_today_summary(db: Session = Depends(get_db)):
    """Resumo das ordens do dia"""
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    orders_today = db.query(Order).filter(Order.created_at >= today_start).all()
    
    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "total_orders": len(orders_today),
        "filled": len([o for o in orders_today if o.status == OrderStatus.FILLED]),
        "closed": len([o for o in orders_today if o.status in [OrderStatus.TP_HIT, OrderStatus.SL_HIT, OrderStatus.CLOSED]]),
        "pnl_points": sum([o.pnl_points for o in orders_today if o.pnl_points]),
        "pnl_currency": sum([o.pnl_currency for o in orders_today if o.pnl_currency]),
        "orders": orders_today
    }


@router.get("/export")
def export_orders(
    format: str = Query("csv", description="Formato: csv ou excel"),
    strategy_name: Optional[str] = None,
    symbol: Optional[str] = None,
    status: Optional[OrderStatus] = None,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    Exporta ordens para CSV ou Excel
    """
    from fastapi.responses import StreamingResponse
    import pandas as pd
    import io
    
    # Buscar ordens com os mesmos filtros do list_orders
    query = db.query(Order)
    
    if strategy_name:
        query = query.filter(Order.strategy_name == strategy_name)
    
    if symbol:
        query = query.filter(Order.symbol == symbol)
    
    if status:
        query = query.filter(Order.status == status)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
        query = query.filter(Order.created_at >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
        query = query.filter(Order.created_at < date_to_obj)
    
    orders = query.order_by(Order.created_at.desc()).all()
    
    # Converter para DataFrame
    data = []
    for o in orders:
        data.append({
            'ID': o.id,
            'Data/Hora': o.created_at.strftime('%d/%m/%Y %H:%M:%S') if o.created_at else '',
            'Estrategia': o.strategy_name,
            'Simbolo': o.symbol,
            'Acao': 'COMPRA' if o.action == OrderAction.BUY else 'VENDA',
            'Preco Entrada': o.entry_price,
            'Preco Saida': o.exit_price if o.exit_price else '',
            'Stop Loss': o.sl_price if o.sl_price else '',
            'Take Profit': o.tp_price if o.tp_price else '',
            'Volume': o.volume,
            'Resultado': 'GAIN' if (o.pnl_points and o.pnl_points > 0) else ('LOSS' if (o.pnl_points and o.pnl_points < 0) else ''),
            'PnL Pontos': o.pnl_points if o.pnl_points else 0,
            'PnL Reais': o.pnl_currency if o.pnl_currency else 0,
            'Status': o.status.value if o.status else '',
            'MT5 Order ID': o.mt5_order_id if o.mt5_order_id else '',
            'Preenchida em': o.filled_at.strftime('%d/%m/%Y %H:%M:%S') if o.filled_at else '',
            'Fechada em': o.closed_at.strftime('%d/%m/%Y %H:%M:%S') if o.closed_at else '',
        })
    
    df = pd.DataFrame(data)
    
    # Gerar arquivo
    buffer = io.BytesIO()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if format.lower() == "excel":
        df.to_excel(buffer, index=False, engine='openpyxl')
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"orders_{timestamp}.xlsx"
    else:  # CSV
        df.to_csv(buffer, index=False, encoding='utf-8-sig')  # utf-8-sig para Excel abrir corretamente
        media_type = "text/csv"
        filename = f"orders_{timestamp}.csv"
    
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
