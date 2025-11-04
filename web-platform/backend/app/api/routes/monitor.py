"""
API Routes: Monitor
Controle do monitor de live trading
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/monitor", tags=["monitor"])


# Schemas
class MonitorStartRequest(BaseModel):
    strategy_name: Optional[str] = None
    dry_run: bool = True


class MonitorStatusResponse(BaseModel):
    running: bool
    pid: Optional[int] = None
    uptime_seconds: Optional[float] = None
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


class MonitorActionResponse(BaseModel):
    success: bool
    message: str
    pid: Optional[int] = None
    dry_run: Optional[bool] = None


# Routes
@router.get("/status", response_model=MonitorStatusResponse)
def get_monitor_status():
    """Retorna status atual do monitor"""
    from app.services.monitor_service import get_monitor_service
    
    service = get_monitor_service()
    status_info = service.get_status()
    
    return status_info


@router.post("/start", response_model=MonitorActionResponse)
async def start_monitor(request: MonitorStartRequest):
    """Inicia o monitor de live trading"""
    from app.services.monitor_service import get_monitor_service
    from app.services.websocket_service import get_websocket_service
    
    service = get_monitor_service()
    result = service.start(
        strategy_name=request.strategy_name,
        dry_run=request.dry_run
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Iniciar broadcast de logs via WebSocket
    ws_service = get_websocket_service()
    await ws_service.start_monitor_broadcast()
    
    return result


@router.post("/stop", response_model=MonitorActionResponse)
async def stop_monitor(force: bool = False):
    """Para o monitor de live trading"""
    from app.services.monitor_service import get_monitor_service
    from app.services.websocket_service import get_websocket_service
    
    service = get_monitor_service()
    result = service.stop(force=force)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    # Parar broadcast via WebSocket
    ws_service = get_websocket_service()
    await ws_service.stop_monitor_broadcast()
    
    return result


@router.post("/restart", response_model=MonitorActionResponse)
def restart_monitor():
    """Reinicia o monitor de live trading"""
    from app.services.monitor_service import get_monitor_service
    
    service = get_monitor_service()
    result = service.restart()
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return result


@router.get("/logs")
def get_monitor_logs(count: int = 50):
    """Retorna ultimos logs do monitor"""
    from app.services.monitor_service import get_monitor_service
    
    service = get_monitor_service()
    logs = service.get_recent_logs(count=count)
    
    return {
        "logs": logs,
        "count": len(logs)
    }


@router.get("/diagnostics")
def get_monitor_diagnostics():
    """Retorna informacoes de diagnostico do monitor"""
    from app.services.monitor_service import get_monitor_service
    from app.core.config import settings
    import os
    
    service = get_monitor_service()
    
    return {
        "monitor_path": str(service.monitor_path),
        "monitor_path_exists": service.monitor_path.exists(),
        "monitor_script": str(service.monitor_script),
        "monitor_script_exists": service.monitor_script.exists(),
        "config_live_trading_path": str(settings.LIVE_TRADING_PATH),
        "config_live_trading_exists": settings.LIVE_TRADING_PATH.exists(),
        "config_strategies_path": str(settings.STRATEGIES_PATH),
        "config_strategies_exists": settings.STRATEGIES_PATH.exists(),
        "config_monitor_config_path": str(settings.MONITOR_CONFIG_PATH),
        "config_monitor_config_exists": settings.MONITOR_CONFIG_PATH.exists(),
        "current_working_directory": os.getcwd()
    }

