"""
Monitor Service
Gerencia execucao do monitor de live trading via subprocess
"""
import subprocess
import psutil
import signal
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import threading
import queue


class MonitorService:
    """Servico para gerenciar o processo do monitor de live trading"""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.monitor_path = Path(__file__).parent.parent.parent.parent.parent / "live_trading"
        self.monitor_script = self.monitor_path / "monitor.py"
        self.log_queue = queue.Queue(maxsize=1000)
        self._log_thread: Optional[threading.Thread] = None
    
    def is_running(self) -> bool:
        """Verifica se o monitor esta rodando"""
        if self.process is None:
            return False
        
        # Verificar se processo ainda existe
        try:
            return self.process.poll() is None
        except:
            return False
    
    def get_status(self) -> Dict:
        """Retorna status detalhado do monitor"""
        if not self.is_running():
            return {
                "running": False,
                "pid": None,
                "uptime_seconds": None,
                "memory_mb": None
            }
        
        try:
            process_info = psutil.Process(self.process.pid)
            
            return {
                "running": True,
                "pid": self.process.pid,
                "uptime_seconds": (datetime.now() - datetime.fromtimestamp(process_info.create_time())).total_seconds(),
                "memory_mb": process_info.memory_info().rss / 1024 / 1024,
                "cpu_percent": process_info.cpu_percent(interval=0.1)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "running": False,
                "pid": None,
                "uptime_seconds": None,
                "memory_mb": None
            }
    
    def start(self, strategy_name: Optional[str] = None, dry_run: bool = True) -> Dict:
        """
        Inicia o monitor
        
        Args:
            strategy_name: Nome da estrategia (opcional, usa a ativa do config.yaml)
            dry_run: Se True, roda em modo simulacao
            
        Returns:
            Dict com status da operacao
        """
        if self.is_running():
            return {
                "success": False,
                "message": "Monitor ja esta rodando",
                "pid": self.process.pid
            }
        
        if not self.monitor_script.exists():
            return {
                "success": False,
                "message": f"Script monitor.py nao encontrado em {self.monitor_script}"
            }
        
        try:
            # Preparar comando
            cmd = ["python", str(self.monitor_script)]
            
            # Adicionar argumentos
            if strategy_name:
                cmd.extend(["--strategy", strategy_name])
            else:
                # Usar estrategia ativa do config.yaml
                from app.services.strategy_discovery import get_strategy_discovery
                active = get_strategy_discovery().get_active_strategy()
                if active:
                    cmd.extend(["--strategy", active])
            
            # Iniciar processo
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.monitor_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Iniciar thread para capturar logs
            self._start_log_capture()
            
            return {
                "success": True,
                "message": "Monitor iniciado com sucesso",
                "pid": self.process.pid,
                "dry_run": dry_run
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao iniciar monitor: {str(e)}"
            }
    
    def stop(self, force: bool = False) -> Dict:
        """
        Para o monitor
        
        Args:
            force: Se True, usa SIGKILL, senao usa SIGTERM
            
        Returns:
            Dict com status da operacao
        """
        if not self.is_running():
            return {
                "success": False,
                "message": "Monitor nao esta rodando"
            }
        
        try:
            if force:
                # Kill forcado
                self.process.kill()
            else:
                # Terminar gracefully
                self.process.terminate()
            
            # Aguardar ate 10 segundos
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Se nao parou, force kill
                self.process.kill()
                self.process.wait()
            
            self.process = None
            
            return {
                "success": True,
                "message": "Monitor parado com sucesso"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao parar monitor: {str(e)}"
            }
    
    def restart(self) -> Dict:
        """Reinicia o monitor"""
        stop_result = self.stop()
        if not stop_result["success"]:
            return stop_result
        
        # Aguardar um pouco
        import time
        time.sleep(2)
        
        return self.start()
    
    def _start_log_capture(self):
        """Inicia thread para capturar logs do subprocess"""
        if self._log_thread is not None and self._log_thread.is_alive():
            return
        
        def capture_logs():
            while self.is_running():
                try:
                    # Ler stdout
                    if self.process.stdout:
                        line = self.process.stdout.readline()
                        if line:
                            try:
                                self.log_queue.put_nowait({
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "INFO",
                                    "message": line.strip()
                                })
                            except queue.Full:
                                pass  # Descarta se fila cheia
                    
                    # Ler stderr
                    if self.process.stderr:
                        line = self.process.stderr.readline()
                        if line:
                            try:
                                self.log_queue.put_nowait({
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "ERROR",
                                    "message": line.strip()
                                })
                            except queue.Full:
                                pass
                except:
                    break
        
        self._log_thread = threading.Thread(target=capture_logs, daemon=True)
        self._log_thread.start()
    
    def get_recent_logs(self, count: int = 50) -> list:
        """Retorna ultimos N logs capturados"""
        logs = []
        temp_queue = queue.Queue()
        
        # Extrair logs mantendo na fila
        while not self.log_queue.empty() and len(logs) < count:
            try:
                log = self.log_queue.get_nowait()
                logs.append(log)
                temp_queue.put(log)
            except queue.Empty:
                break
        
        # Recolocar na fila
        while not temp_queue.empty():
            try:
                self.log_queue.put_nowait(temp_queue.get_nowait())
            except queue.Full:
                break
        
        return logs[-count:]  # Retornar ultimos N


# Instancia singleton
_monitor_service = None

def get_monitor_service() -> MonitorService:
    """Retorna instancia singleton do servico"""
    global _monitor_service
    if _monitor_service is None:
        _monitor_service = MonitorService()
    return _monitor_service

