"""
Monitor Generico - Live Trading
Sistema hibrido que monitora mercado via Python e executa ordens via MT5
Totalmente modular: carrega estrategias dinamicamente

Autor: MacTester Team
Data: 2024-11-03
Versao: 2.0.0
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
import importlib

# Adicionar projeto root ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'strategies'))

# Imports locais
from mt5_connector import MT5Connector

# Criar diretorio de logs se nao existir
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

logger = logging.getLogger('MonitorGenerico')


class MonitorGenerico:
    """Monitor principal do sistema hibrido - GENERICO"""
    
    def __init__(self, motor_config_path: str = None, strategy_name: str = None, symbol: str = None):
        """
        Inicializa monitor generico
        
        Args:
            motor_config_path: Caminho para config do motor (default: config.yaml)
            strategy_name: Nome da estrategia (default: pega do config)
            symbol: Simbolo a negociar (default: pega do config)
        """
        logger.info("="*80)
        logger.info("INICIANDO MACTESTER - MONITOR GENERICO V2.0")
        logger.info("="*80)
        
        # Definir caminho do config do motor
        if motor_config_path is None:
            motor_config_path = Path(__file__).parent / 'config.yaml'
        
        # Carregar config do motor
        self.motor_config = self._load_config(str(motor_config_path))
        logger.info(f"OK - Config do motor carregado de {motor_config_path}")
        
        # Determinar estrategia ativa
        self.strategy_name = strategy_name or self.motor_config.get('active_strategy')
        if not self.strategy_name:
            raise ValueError("Estrategia nao especificada no config ou parametro")
        
        # Carregar config da estrategia
        strategy_config_path = Path(__file__).parent / 'strategies' / f'config_{self.strategy_name}.yaml'
        self.strategy_config = self._load_config(str(strategy_config_path))
        logger.info(f"OK - Config da estrategia '{self.strategy_name}' carregado")
        logger.info(f"     Estrategia: {self.strategy_config['strategy_name']}")
        
        # Determinar simbolo
        self.symbol = symbol or self.motor_config['trading']['symbol']
        logger.info(f"OK - Simbolo: {self.symbol}")
        
        # Carregar estrategia dinamicamente
        self.strategy_instance = self._load_strategy()
        logger.info(f"OK - Estrategia carregada: {self.strategy_instance.name}")
        
        # Inicializar componentes do motor
        self.mt5 = MT5Connector(
            login=self.motor_config['mt5'].get('login'),
            password=self.motor_config['mt5'].get('password'),
            server=self.motor_config['mt5'].get('server')
        )
        
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
    
    def _load_strategy(self):
        """Carrega estrategia dinamicamente baseado no config"""
        try:
            module_name = self.strategy_config['strategy_module']
            class_name = self.strategy_config['strategy_class']
            
            # Import dinamico
            logger.info(f"Importando modulo: {module_name}")
            module = importlib.import_module(module_name)
            
            # Obter classe
            strategy_class = getattr(module, class_name)
            
            # Instanciar com parametros
            params = self.strategy_config['parameters']
            strategy_instance = strategy_class(params)
            
            return strategy_instance
            
        except Exception as e:
            logger.error(f"Erro ao carregar estrategia: {e}", exc_info=True)
            raise
    
    def start(self):
        """Inicia o monitor"""
        try:
            # Conectar ao MT5
            if not self.mt5.connect():
                logger.error("ERRO - Falha ao conectar ao MT5")
                return
            
            # Verificar simbolo
            if not self._validate_symbol(self.symbol):
                logger.error(f"ERRO - Simbolo {self.symbol} nao disponivel")
                return
            
            logger.info("="*80)
            logger.info("CONFIGURACAO ATIVA:")
            logger.info(f"  Estrategia: {self.strategy_config['strategy_name']}")
            logger.info(f"  Simbolo: {self.symbol}")
            logger.info(f"  Timeframe: M{self.motor_config['trading']['timeframe']}")
            logger.info(f"  Volume: {self.motor_config['trading']['volume']} contratos")
            
            # Horarios da estrategia (podem variar por estrategia)
            params = self.strategy_config['parameters']
            if 'horario_inicio' in params:
                logger.info(f"  Horario operacao: {params['horario_inicio']}:{params['minuto_inicio']:02d} - {params['horario_fim']}:{params['minuto_fim']:02d}")
            
            dry_run = self.motor_config['monitor']['dry_run']
            logger.info(f"  Dry-run: {'SIM (sem executar ordens reais)' if dry_run else 'NAO (ordens reais!)'}")
            logger.info("="*80)
            
            if not dry_run:
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
        check_interval = self.motor_config['monitor']['check_interval']
        lookback = self.motor_config['monitor']['lookback_candles']
        
        while self.running:
            try:
                now = datetime.now()
                
                # Verificar horario do monitor
                if not self._is_monitor_hours(now):
                    logger.info(f"Fora do horario do monitor ({now.hour}h). Aguardando...")
                    time.sleep(check_interval)
                    continue
                
                # Buscar dados do MT5
                timeframe_map = {
                    1: mt5.TIMEFRAME_M1,
                    2: mt5.TIMEFRAME_M2,
                    3: mt5.TIMEFRAME_M3,
                    5: mt5.TIMEFRAME_M5,
                    15: mt5.TIMEFRAME_M15,
                    30: mt5.TIMEFRAME_M30,
                    60: mt5.TIMEFRAME_H1
                }
                
                tf = timeframe_map.get(self.motor_config['trading']['timeframe'], mt5.TIMEFRAME_M5)
                rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, lookback)
                
                if rates is None or len(rates) == 0:
                    logger.warning(f"Nenhum dado recebido para {self.symbol}")
                    time.sleep(check_interval)
                    continue
                
                # Converter para DataFrame
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                
                # Detectar sinal usando estrategia
                signal = self._detect_signal(df)
                
                if signal:
                    logger.info("="*80)
                    logger.info(f"SINAL DETECTADO: {signal['action'].upper()}")
                    logger.info(f"  Preco: {signal['price']:.2f}")
                    logger.info(f"  Stop Loss: {signal['sl']:.2f}")
                    logger.info(f"  Take Profit: {signal['tp']:.2f}")
                    logger.info("="*80)
                    
                    self.stats['signals_detected'] += 1
                    
                    # Validacoes antes de executar
                    if self._can_execute_trade():
                        executed = self._execute_order(signal)
                        
                        if executed:
                            self.stats['orders_filled'] += 1
                            logger.info("OK - Ordem executada com sucesso!")
                        else:
                            self.stats['orders_rejected'] += 1
                            logger.warning("AVISO - Ordem rejeitada")
                    else:
                        logger.info("Sinal ignorado (restricoes de risco)")
                
                # Verificar fechamento intraday
                self._check_intraday_close()
                
                # Aguardar proximo ciclo
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop principal: {e}", exc_info=True)
                time.sleep(check_interval)
    
    def _detect_signal(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Detecta sinal usando estrategia carregada
        
        Args:
            df: DataFrame com dados OHLCV
        
        Returns:
            Dict com sinal ou None
        """
        try:
            # Chamar metodo detect() da estrategia
            # Estrategias devem implementar metodo detect(df) que retorna Dict ou None
            if hasattr(self.strategy_instance, 'detect'):
                return self.strategy_instance.detect(df)
            
            # Fallback: usar metodo run() do backtest adaptado
            logger.warning("Estrategia nao tem metodo detect(), tentando adaptar...")
            return None
            
        except Exception as e:
            logger.error(f"Erro ao detectar sinal: {e}")
            return None
    
    def _can_execute_trade(self) -> bool:
        """Verifica se pode executar trade (gestao de risco)"""
        risk = self.motor_config['risk']
        
        # Verificar numero de posicoes
        positions = self.mt5.get_positions(self.symbol)
        if positions and len(positions) >= risk['max_positions']:
            logger.info(f"Limite de posicoes atingido ({risk['max_positions']})")
            return False
        
        # Verificar perdas consecutivas
        if self.consecutive_losses >= risk['max_consecutive_losses']:
            logger.error(f"Kill switch ativado! {self.consecutive_losses} perdas consecutivas")
            return False
        
        # Verificar perda diaria
        if abs(self.daily_pnl) >= risk['max_daily_loss_points']:
            logger.error(f"Loss diario maximo atingido: {self.daily_pnl:.2f} pts")
            return False
        
        # Verificar margem
        if not self._check_margin():
            return False
        
        return True
    
    def _execute_order(self, signal: Dict) -> bool:
        """Executa ordem no MT5"""
        if self.motor_config['monitor']['dry_run']:
            logger.info("DRY-RUN: Ordem simulada (nao executada)")
            return True
        
        try:
            result = self.mt5.send_order(
                symbol=self.symbol,
                action=signal['action'],
                volume=self.motor_config['trading']['volume'],
                price=signal['price'],
                sl=signal['sl'],
                tp=signal['tp'],
                comment=f"{self.strategy_name}"
            )
            
            self.stats['orders_sent'] += 1
            self.last_signal_time = datetime.now()
            
            return result.get('success', False)
            
        except Exception as e:
            logger.error(f"Erro ao executar ordem: {e}")
            return False
    
    def _check_intraday_close(self):
        """Verifica se deve fechar posicoes no final do dia"""
        params = self.strategy_config['parameters']
        
        # Nem todas estrategias tem fechamento intraday
        if 'horario_fechamento' not in params:
            return
        
        now = datetime.now()
        hora_fechamento = params['horario_fechamento']
        minuto_fechamento = params['minuto_fechamento']
        
        if now.hour == hora_fechamento and now.minute >= minuto_fechamento:
            positions = self.mt5.get_positions(self.symbol)
            
            if positions:
                logger.info(f"Horario de fechamento ({hora_fechamento}:{minuto_fechamento:02d})")
                logger.info(f"Fechando {len(positions)} posicao(oes)...")
                
                closed = self.mt5.close_all_positions(self.symbol)
                logger.info(f"OK - {closed} posicao(oes) fechada(s)")
    
    def _is_monitor_hours(self, dt: datetime) -> bool:
        """Verifica se esta dentro do horario do monitor"""
        start = self.motor_config['monitor']['monitor_start_hour']
        end = self.motor_config['monitor']['monitor_end_hour']
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
        logger.info(f"  Estrategia: {self.strategy_config['strategy_name']}")
        logger.info(f"  Simbolo: {self.symbol}")
        logger.info(f"  Sinais detectados: {self.stats['signals_detected']}")
        logger.info(f"  Ordens enviadas: {self.stats['orders_sent']}")
        logger.info(f"  Ordens executadas: {self.stats['orders_filled']}")
        logger.info(f"  Ordens rejeitadas: {self.stats['orders_rejected']}")
        logger.info(f"  PnL total: {self.stats['total_pnl']:.2f} pts")
        logger.info("="*80)
        logger.info("Monitor encerrado. Ate logo!")


def main():
    """Funcao principal com CLI interativa"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor Generico MacTester')
    parser.add_argument('--strategy', type=str, help='Nome da estrategia (ex: barra_elefante)')
    parser.add_argument('--symbol', type=str, help='Simbolo a negociar (ex: WIN$)')
    parser.add_argument('--config', type=str, help='Caminho para config do motor')
    
    args = parser.parse_args()
    
    # Se nao especificou estrategia, mostrar menu
    if not args.strategy:
        print("\n" + "="*80)
        print("MACTESTER - MONITOR GENERICO V2.0")
        print("="*80)
        
        # Listar estrategias disponiveis
        strategies_dir = Path(__file__).parent / 'strategies'
        configs = list(strategies_dir.glob('config_*.yaml'))
        
        if not configs:
            print("ERRO: Nenhuma estrategia encontrada em live_trading/strategies/")
            return
        
        print("\nEstrategias disponiveis:")
        for i, cfg in enumerate(configs, 1):
            strategy_name = cfg.stem.replace('config_', '')
            print(f"  {i}. {strategy_name}")
        
        choice = input("\nEscolha a estrategia (numero): ")
        try:
            idx = int(choice) - 1
            strategy_name = configs[idx].stem.replace('config_', '')
        except:
            print("Opcao invalida!")
            return
    else:
        strategy_name = args.strategy
    
    # Criar e iniciar monitor
    monitor = MonitorGenerico(
        motor_config_path=args.config,
        strategy_name=strategy_name,
        symbol=args.symbol
    )
    monitor.start()


if __name__ == '__main__':
    main()

