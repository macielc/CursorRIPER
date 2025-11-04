"""
Teste de Conexão - Valida setup do sistema híbrido

Execute este script antes de rodar o monitor pela primeira vez
"""

import sys
from pathlib import Path
import logging

# Setup básico de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('TestConnection')


def test_imports():
    """Testa se todas as bibliotecas estão instaladas"""
    logger.info("="*80)
    logger.info("TESTE 1: Verificando imports...")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        logger.info("✅ MetaTrader5 instalado")
    except ImportError:
        logger.error("❌ MetaTrader5 NÃO instalado!")
        logger.error("   Execute: pip install MetaTrader5")
        return False
    
    try:
        import pandas as pd
        logger.info("✅ Pandas instalado")
    except ImportError:
        logger.error("❌ Pandas NÃO instalado!")
        return False
    
    try:
        import numpy as np
        logger.info("✅ Numpy instalado")
    except ImportError:
        logger.error("❌ Numpy NÃO instalado!")
        return False
    
    try:
        import yaml
        logger.info("✅ PyYAML instalado")
    except ImportError:
        logger.error("❌ PyYAML NÃO instalado!")
        logger.error("   Execute: pip install pyyaml")
        return False
    
    return True


def test_mt5_connection():
    """Testa conexão com MT5"""
    logger.info("\n" + "="*80)
    logger.info("TESTE 2: Testando conexão com MT5...")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        
        # Tentar inicializar
        if not mt5.initialize():
            logger.error("❌ MT5.initialize() falhou!")
            logger.error(f"   Erro: {mt5.last_error()}")
            logger.error("   VERIFIQUE:")
            logger.error("   1. MT5 está instalado?")
            logger.error("   2. MT5 está rodando?")
            logger.error("   3. Você já fez login no MT5?")
            return False
        
        logger.info("✅ MT5 inicializado com sucesso!")
        
        # Buscar info da conta
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("❌ Não foi possível obter info da conta")
            return False
        
        logger.info(f"✅ Conta conectada:")
        logger.info(f"   Login: {account_info.login}")
        logger.info(f"   Servidor: {account_info.server}")
        logger.info(f"   Saldo: R$ {account_info.balance:.2f}")
        logger.info(f"   Margem livre: R$ {account_info.margin_free:.2f}")
        logger.info(f"   Tipo: {'DEMO' if account_info.trade_mode == mt5.ACCOUNT_TRADE_MODE_DEMO else 'REAL'}")
        
        # Encerrar
        mt5.shutdown()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar MT5: {e}")
        return False


def test_symbol():
    """Testa se símbolo está disponível"""
    logger.info("\n" + "="*80)
    logger.info("TESTE 3: Testando símbolo...")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            logger.error("❌ Não foi possível inicializar MT5")
            return False
        
        # Testar símbolos comuns
        symbols_to_test = ['WINFUT', 'WIN$', 'WINM25', 'WINN25']
        
        found_symbol = None
        for symbol in symbols_to_test:
            info = mt5.symbol_info(symbol)
            if info is not None:
                found_symbol = symbol
                logger.info(f"✅ Símbolo encontrado: {symbol}")
                logger.info(f"   Descrição: {info.description}")
                logger.info(f"   Tick size: {info.trade_tick_size}")
                logger.info(f"   Volume mín: {info.volume_min}")
                break
        
        if found_symbol is None:
            logger.warning("⚠️  Nenhum símbolo WIN$ encontrado!")
            logger.warning("   Você precisará configurar o símbolo correto no config.yaml")
            logger.warning("   Verifique na Market Watch do MT5 qual símbolo está disponível")
        
        mt5.shutdown()
        return found_symbol is not None
        
    except Exception as e:
        logger.error(f"❌ Erro ao testar símbolo: {e}")
        return False


def test_data_retrieval():
    """Testa busca de dados históricos"""
    logger.info("\n" + "="*80)
    logger.info("TESTE 4: Testando busca de dados...")
    logger.info("="*80)
    
    try:
        import MetaTrader5 as mt5
        import pandas as pd
        
        if not mt5.initialize():
            logger.error("❌ Não foi possível inicializar MT5")
            return False
        
        # Tentar buscar dados
        symbols = ['WINFUT', 'WIN$']
        for symbol in symbols:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
            
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                logger.info(f"✅ Dados recuperados para {symbol}:")
                logger.info(f"   Quantidade: {len(df)} candles")
                logger.info(f"   Último candle: {pd.to_datetime(df['time'].iloc[-1], unit='s')}")
                logger.info(f"   Close atual: {df['close'].iloc[-1]:.2f}")
                mt5.shutdown()
                return True
        
        logger.error("❌ Não foi possível buscar dados de nenhum símbolo")
        mt5.shutdown()
        return False
        
    except Exception as e:
        logger.error(f"❌ Erro ao buscar dados: {e}")
        return False


def test_strategy_import():
    """Testa se consegue importar estratégia"""
    logger.info("\n" + "="*80)
    logger.info("TESTE 5: Testando import da estratégia...")
    logger.info("="*80)
    
    try:
        # Adicionar projeto root ao path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / 'strategies'))
        
        from barra_elefante.strategy import BarraElefante
        
        logger.info("✅ Estratégia importada com sucesso")
        
        # Testar instanciação
        params = {
            'min_amplitude_mult': 1.35,
            'min_volume_mult': 1.3,
            'max_sombra_pct': 0.30,
            'lookback_amplitude': 25,
            'lookback_volume': 20,
        }
        
        strategy = BarraElefante(params)
        logger.info(f"✅ Estratégia instanciada: {strategy.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro ao importar estratégia: {e}")
        return False


def main():
    """Executa todos os testes"""
    logger.info("\n")
    logger.info("🧪 TESTE DE CONEXÃO - SISTEMA HÍBRIDO MACTESTER")
    logger.info("\n")
    
    tests = [
        ("Imports", test_imports),
        ("Conexão MT5", test_mt5_connection),
        ("Símbolo", test_symbol),
        ("Busca de dados", test_data_retrieval),
        ("Import estratégia", test_strategy_import),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ Erro no teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Resumo
    logger.info("\n" + "="*80)
    logger.info("RESUMO DOS TESTES:")
    logger.info("="*80)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        logger.info(f"  {test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    logger.info("="*80)
    if all_passed:
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("   Sistema pronto para uso!")
        logger.info("   Execute: python live_trading/monitor_elefante.py")
    else:
        logger.error("❌ ALGUNS TESTES FALHARAM!")
        logger.error("   Corrija os problemas antes de rodar o monitor")
    logger.info("="*80)
    
    return all_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

