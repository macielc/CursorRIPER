"""
WebSocket Service
Gerencia broadcast de eventos em tempo real para clientes conectados
"""
import asyncio
from typing import Dict, Optional
from datetime import datetime


class WebSocketService:
    """Servico para gerenciar broadcasts via WebSocket"""
    
    def __init__(self, connection_manager):
        self.manager = connection_manager
        self._broadcast_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def broadcast_event(self, event_type: str, data: dict):
        """
        Broadcast de um evento para todos os clientes conectados
        
        Args:
            event_type: Tipo do evento (monitor_log, monitor_status, order_update, etc)
            data: Dados do evento
        """
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        await self.manager.broadcast(message)
    
    async def start_monitor_broadcast(self):
        """Inicia task de broadcast periodico de logs do monitor"""
        if self._running:
            return
        
        self._running = True
        self._broadcast_task = asyncio.create_task(self._monitor_broadcast_loop())
    
    async def stop_monitor_broadcast(self):
        """Para task de broadcast"""
        self._running = False
        if self._broadcast_task:
            self._broadcast_task.cancel()
            try:
                await self._broadcast_task
            except asyncio.CancelledError:
                pass
            self._broadcast_task = None
    
    async def _monitor_broadcast_loop(self):
        """Loop que envia logs do monitor periodicamente"""
        from app.services.monitor_service import get_monitor_service
        
        monitor_service = get_monitor_service()
        last_log_count = 0
        
        while self._running:
            try:
                # Verificar se monitor esta rodando
                if monitor_service.is_running():
                    # Buscar novos logs
                    logs = monitor_service.get_recent_logs(count=100)
                    
                    # Se tiver novos logs, enviar
                    if len(logs) > last_log_count:
                        new_logs = logs[last_log_count:]
                        for log in new_logs:
                            await self.broadcast_event("monitor_log", log)
                        last_log_count = len(logs)
                    
                    # Enviar status do monitor
                    status = monitor_service.get_status()
                    await self.broadcast_event("monitor_status", status)
                else:
                    # Monitor parou, reset contador
                    if last_log_count > 0:
                        await self.broadcast_event("monitor_stopped", {
                            "message": "Monitor foi parado"
                        })
                    last_log_count = 0
                
                # Aguardar antes de proxima verificacao
                await asyncio.sleep(2)  # Broadcast a cada 2 segundos
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Erro no broadcast loop: {e}")
                await asyncio.sleep(5)  # Aguardar mais em caso de erro
    
    async def broadcast_order_update(self, order_data: dict):
        """Broadcast de atualização de ordem"""
        await self.broadcast_event("order_update", order_data)
    
    async def broadcast_signal_detected(self, signal_data: dict):
        """Broadcast de sinal detectado"""
        await self.broadcast_event("signal_detected", signal_data)
    
    async def broadcast_strategy_change(self, strategy_name: str, active: bool):
        """Broadcast de mudanca de estrategia"""
        await self.broadcast_event("strategy_change", {
            "strategy": strategy_name,
            "active": active
        })


# Singleton (sera inicializado no startup do app)
_websocket_service: Optional[WebSocketService] = None

def get_websocket_service() -> WebSocketService:
    """Retorna instancia singleton do servico"""
    global _websocket_service
    if _websocket_service is None:
        raise RuntimeError("WebSocketService nao inicializado. Chame init_websocket_service() primeiro.")
    return _websocket_service

def init_websocket_service(connection_manager):
    """Inicializa o servico WebSocket"""
    global _websocket_service
    _websocket_service = WebSocketService(connection_manager)
    return _websocket_service

