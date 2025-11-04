"""
Configuracoes do Backend MacTester Web Platform
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """Configuracoes da aplicacao"""
    
    # App
    APP_NAME: str = "MacTester Web Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str = "sqlite:///./mactester.db"
    
    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite dev
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]
    
    # Live Trading Integration
    LIVE_TRADING_PATH: Path = Path("../../live_trading")
    STRATEGIES_PATH: Path = LIVE_TRADING_PATH / "strategies"
    MONITOR_CONFIG_PATH: Path = LIVE_TRADING_PATH / "config.yaml"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # segundos
    
    # Backup
    BACKUP_ENABLED: bool = True
    BACKUP_DIR: Path = Path("./backups")
    BACKUP_RETENTION_DAYS: int = 30
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = Path("./logs/backend.log")
    
    # Security (para acesso externo)
    SECRET_KEY: str = "change-me-in-production-please"  # Trocar em producao!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas
    
    # Telegram (opcional)
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_ignore_empty = True
        case_sensitive = False
        extra = "ignore"


# Instancia global
settings = Settings()

# Criar diretorios necessarios
settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

