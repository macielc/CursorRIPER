"""
Monitor Barra Elefante - Live Trading

Sistema hibrido que monitora mercado via Python e executa ordens via MT5

Autor: MacTester Team
Data: 2024-11-03
Versao: 1.0.0
"""

import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
import logging
import yaml
import pandas as pd
import MetaTrader5 as mt5
from typing import Dict, Optional

# Imports locais
from mt5_connector import MT5Connector
from signal_detector import SignalDetector

# Criar diretrio de logs se no existir
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('MonitorElefante')


class MonitorElefante:
    """Monitor principal do sistema hibrido"""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa monitor
        
        Args:
            config_path: Caminho para arquivo de configuracao
        """
        logger.info("="*80)
        logger.info("INICIANDO MACTESTER - MONITOR BARRA ELEFANTE")
        logger.info("="*80)
        
        # Definir caminho do config
        if config_path is None:
            config_path = Path(__file__).parent / 'config.yaml'
        
        # Carregar configuracao
        self.config = self._load_config(str(config_path))
        logger.info(f"OK - Configuracao carregada de {config_path}")
        
        # Inicializar componentes
        self.mt5 = MT5Connector(
            login=self.config['mt5'].get('login'),
            password=self.config['mt5'].get('password'),
            server=self.config['mt5'].get('server')
        )
        
        self.detector = SignalDetector(self.config['strategy'])
        
        # Estado do monitor
        self.running = False
        self.last_signal_time = None
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        
        # Estatisticas
        self.stats = {
            'signals_detected': 0,
            'orders_sent': 0,
            'orders_filled': 0,
            'orders_rejected': 0,
            'total_pnl': 0.0
        }
    
    def _load_config(self, path: str) -> Dict:
        """Carrega arquivo de configuracao YAML"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            raise
    
    def start(self):
        """Inicia o monitor"""
        try:
            # Conectar ao MT5
            if not self.mt5.connect():
                logger.error("ERRO - Falha ao conectar ao MT5")
                return
            
            # Verificar simbolo
            symbol = self.config['trading']['symbol']
            if not self._validate_symbol(symbol):
                logger.error(f"ERRO - Simbolo {symbol} nao disponivel")
                return
            
            logger.info("="*80)
            logger.info("CONFIGURACAO ATIVA:")
            logger.info(f"  Simbolo: {symbol}")
            logger.info(f"  Timeframe: M{self.config['trading']['timeframe']}")
            logger.info(f"  Volume: {self.config['trading']['volume']} contratos")
            logger.info(f"  Horario operacao: {self.config['strategy']['horario_inicio']}:{self.config['strategy']['minuto_inicio']:02d} - {self.config['strategy']['horario_fim']}:{self.config['strategy']['minuto_fim']:02d}")
            logger.info(f"  Dry-run: {'SIM (sem executar ordens reais)' if self.config['monitor']['dry_run'] else 'NO (ordens reais!)'}")
            logger.info("="*80)
            
            if not self.config['monitor']['dry_run']:
                logger.warning("ATENCAO: Modo REAL ativado! Ordens serao executadas de verdade!")
                time.sleep(3)
            
            # Iniciar loop principal
            self.running = True
            logger.info("OK - Monitor iniciado. Aguardando sinais...")
            self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("\nMonitor interrompido pelo usuario")
            self.stop()
        except Exception as e:
            logger.error(f"ERRO FATAL: {e}", exc_info=True)
            self.stop()
    
    def _main_loop(self):
        """Loop principal do monitor"""
        check_interval = self.config['monitor']['check_interval']
        
        while self.running:
            try:
                # Verificar horrio do monitor
                now = datetime.now()
                if not self._is_monitor_hours(now):
                    logger.debug(f"Fora do horrio de monitoramento ({now.hour}h)")
                    time.sleep(60)
                    continue
                
                # Verificar kill switch
                if self._check_kill_switch():
                    logger.critical(" KILL SWITCH ATIVADO! Encerrando monitor...")
                    self.stop()
                    break
                
                # Buscar dados
                df = self._get_market_data()
                if df is None or len(df) < 50:
                    logger.warning("Dados insuficientes, aguardando...")
                    time.sleep(check_interval)
                    continue
                
                # Detectar sinal
                signal = self.detector.detect_signal(df)
                
                if signal['action'] != 'NONE':
                    self._handle_signal(signal)
                
                # Verificar fechamento intraday
                self._check_intraday_close()
                
                # Aguardar prximo ciclo
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}", exc_info=True)
                time.sleep(check_interval)
    
    def _get_market_data(self) -> Optional[pd.DataFrame]:
        """Busca dados do mercado"""
        symbol = self.config['trading']['symbol']
        timeframe_map = {
            1: mt5.TIMEFRAME_M1,
            5: mt5.TIMEFRAME_M5,
            15: mt5.TIMEFRAME_M15,
            30: mt5.TIMEFRAME_M30,
            60: mt5.TIMEFRAME_H1
        }
        
        timeframe = timeframe_map.get(self.config['trading']['timeframe'], mt5.TIMEFRAME_M5)
        count = self.config['monitor']['lookback_candles']
        
        return self.mt5.get_candles(symbol, timeframe, count)
    
    def _handle_signal(self, signal: Dict):
        """
        Processa sinal detectado
        
        Args:
            signal: Sinal retornado pelo detector
        """
        self.stats['signals_detected'] += 1
        
        logger.info("="*80)
        logger.info(f" SINAL DETECTADO #{self.stats['signals_detected']}")
        logger.info(f"  Ao: {signal['action']}")
        logger.info(f"  Preo: {signal['price']:.2f}")
        logger.info(f"  SL: {signal['sl']:.2f}")
        logger.info(f"  TP: {signal['tp']:.2f}")
        logger.info(f"  Razo: {signal['reason']}")
        logger.info("="*80)
        
        # Validar horrio
        if not self.detector.validate_signal_time(signal):
            logger.warning("  Sinal fora do horrio permitido")
            return
        
        # Verificar se j tem posio
        positions = self.mt5.get_positions(self.config['trading']['symbol'])
        if len(positions) >= self.config['risk']['max_positions']:
            logger.warning("  J existe posio aberta, ignorando sinal")
            return
        
        # Validar margem
        if not self._check_margin():
            logger.error(" Margem insuficiente!")
            return
        
        # Executar ordem
        if self.config['monitor']['dry_run']:
            logger.info(" DRY-RUN: Ordem NO executada (modo simulao)")
            self._log_signal(signal, executed=False)
        else:
            self._execute_order(signal)
    
    def _execute_order(self, signal: Dict):
        """
        Executa ordem no MT5
        
        Args:
            signal: Sinal a ser executado
        """
        order_type = mt5.ORDER_TYPE_BUY if signal['action'] == 'BUY' else mt5.ORDER_TYPE_SELL
        
        result = self.mt5.send_order(
            symbol=self.config['trading']['symbol'],
            order_type=order_type,
            volume=self.config['trading']['volume'],
            sl=signal['sl'],
            tp=signal['tp'],
            comment=f"BarraElefante_{signal['action']}"
        )
        
        self.stats['orders_sent'] += 1
        
        if result['success']:
            self.stats['orders_filled'] += 1
            self.daily_trades += 1
            logger.info(f" Ordem executada! Ticket: {result['order']}")
            self._log_order(signal, result, success=True)
        else:
            self.stats['orders_rejected'] += 1
            logger.error(f" Ordem rejeitada: {result.get('error', 'Erro desconhecido')}")
            self._log_order(signal, result, success=False)
    
    def _check_kill_switch(self) -> bool:
        """Verifica se kill switch deve ser ativado"""
        # Verificar loss dirio
        max_loss = self.config['risk']['max_daily_loss_points']
        if self.daily_pnl < -max_loss:
            logger.critical(f" KILL SWITCH: Loss dirio excedido ({self.daily_pnl:.0f} pts)")
            return True
        
        # Verificar trades consecutivos com loss
        max_consecutive = self.config['risk']['max_consecutive_losses']
        if self.consecutive_losses >= max_consecutive:
            logger.critical(f" KILL SWITCH: {max_consecutive} losses consecutivos")
            return True
        
        return False
    
    def _check_intraday_close(self):
        """Verifica se deve fechar posicoes no final do dia"""
        now = datetime.now()
        hora_fechamento = self.config['strategy']['horario_fechamento']
        minuto_fechamento = self.config['strategy']['minuto_fechamento']
        
        if now.hour == hora_fechamento and now.minute >= minuto_fechamento:
            positions = self.mt5.get_positions(self.config['trading']['symbol'])
            
            if positions:
                logger.info(f"Horario de fechamento ({hora_fechamento}:{minuto_fechamento:02d})")
                logger.info(f"Fechando {len(positions)} posicao(oes)...")
                
                closed = self.mt5.close_all_positions(self.config['trading']['symbol'])
                logger.info(f"OK - {closed} posicao(oes) fechada(s)")
    
    def _is_monitor_hours(self, dt: datetime) -> bool:
        """Verifica se esta dentro do horario do monitor"""
        start = self.config['monitor']['monitor_start_hour']
        end = self.config['monitor']['monitor_end_hour']
        return start <= dt.hour < end
    
    def _validate_symbol(self, symbol: str) -> bool:
        """Valida se simbolo esta disponivel"""
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return False
            
            # Selecionar simbolo
            if not mt5.symbol_select(symbol, True):
                return False
            
            logger.info(f"OK - Simbolo {symbol} validado")
            logger.info(f"  Descricao: {info.description}")
            logger.info(f"  Tick size: {info.trade_tick_size}")
            logger.info(f"  Volume min: {info.volume_min}")
            
            return True
        except Exception as e:
            logger.error(f"Erro ao validar simbolo: {e}")
            return False
    
    def _check_margin(self) -> bool:
        """Verifica se ha margem disponivel"""
        account = self.mt5.get_account_info()
        if account is None:
            return False
        
        # Verificar se margem livre > 10% do saldo (seguranca)
        margin_pct = (account['margin_free'] / account['balance']) * 100
        
        if margin_pct < 10:
            logger.error(f"Margem baixa: {margin_pct:.1f}%")
            return False
        
        return True
    
    def _log_signal(self, signal: Dict, executed: bool):
        """Salva sinal em arquivo CSV"""
        if not self.config['logging']['save_signals']:
            return
        
        try:
            file_path = Path(__file__).parent / 'logs' / 'signals.csv'
            df = pd.DataFrame([{
                'timestamp': datetime.now(),
                'action': signal['action'],
                'price': signal['price'],
                'sl': signal['sl'],
                'tp': signal['tp'],
                'atr': signal['atr'],
                'reason': signal['reason'],
                'executed': executed
            }])
            
            df.to_csv(file_path, mode='a', header=not Path(file_path).exists(), index=False)
        except Exception as e:
            logger.error(f"Erro ao salvar sinal: {e}")
    
    def _log_order(self, signal: Dict, result: Dict, success: bool):
        """Salva ordem em arquivo CSV"""
        if not self.config['logging']['save_orders']:
            return
        
        try:
            file_path = Path(__file__).parent / 'logs' / 'orders.csv'
            df = pd.DataFrame([{
                'timestamp': datetime.now(),
                'action': signal['action'],
                'price': signal['price'],
                'sl': signal['sl'],
                'tp': signal['tp'],
                'success': success,
                'ticket': result.get('order', 0),
                'error': result.get('error', '')
            }])
            
            df.to_csv(file_path, mode='a', header=not Path(file_path).exists(), index=False)
        except Exception as e:
            logger.error(f"Erro ao salvar ordem: {e}")
    
    def stop(self):
        """Para o monitor"""
        logger.info("Encerrando monitor...")
        self.running = False
        
        # Fechar todas as posicoes (opcional)
        # positions = self.mt5.get_positions()
        # if positions:
        #     logger.info(f"Fechando {len(positions)} posicao(oes) abertas...")
        #     self.mt5.close_all_positions()
        
        # Desconectar MT5
        self.mt5.disconnect()
        
        # Mostrar estatisticas
        logger.info("="*80)
        logger.info("ESTATISTICAS DA SESSAO:")
        logger.info(f"  Sinais detectados: {self.stats['signals_detected']}")
        logger.info(f"  Ordens enviadas: {self.stats['orders_sent']}")
        logger.info(f"  Ordens executadas: {self.stats['orders_filled']}")
        logger.info(f"  Ordens rejeitadas: {self.stats['orders_rejected']}")
        logger.info(f"  PnL total: {self.stats['total_pnl']:.2f} pts")
        logger.info("="*80)
        logger.info("Monitor encerrado. Ate logo!")


def main():
    """Funcao principal"""
    monitor = MonitorElefante()
    monitor.start()


if __name__ == '__main__':
    main()


