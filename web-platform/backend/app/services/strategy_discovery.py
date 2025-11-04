"""
Strategy Discovery Service
Descobre e carrega estrategias disponiveis em live_trading/strategies/
"""
import os
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class StrategyDiscoveryService:
    """Servico para descobrir estrategias disponiveis no sistema"""
    
    def __init__(self):
        # Caminho relativo do backend ate live_trading
        self.base_path = Path(__file__).parent.parent.parent.parent.parent / "live_trading"
        self.strategies_path = self.base_path / "strategies"
        self.config_path = self.base_path / "config.yaml"
    
    def get_active_strategy(self) -> Optional[str]:
        """Retorna o nome da estrategia ativa no config.yaml"""
        try:
            if not self.config_path.exists():
                return None
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config.get('active_strategy')
        except Exception as e:
            print(f"Erro ao ler config.yaml: {e}")
            return None
    
    def discover_strategies(self) -> List[Dict]:
        """
        Descobre todas as estrategias disponiveis em strategies/
        
        Returns:
            Lista de dicts com informacoes das estrategias
        """
        strategies = []
        
        if not self.strategies_path.exists():
            print(f"Diretorio strategies nao encontrado: {self.strategies_path}")
            return strategies
        
        # Estrategia ativa atual
        active_strategy = self.get_active_strategy()
        
        # Listar todos os arquivos YAML em strategies/
        for yaml_file in self.strategies_path.glob("config_*.yaml"):
            try:
                strategy_info = self._parse_strategy_file(yaml_file)
                if strategy_info:
                    # Adicionar flag se eh a estrategia ativa
                    strategy_key = yaml_file.stem.replace("config_", "")
                    strategy_info['is_active'] = (strategy_key == active_strategy)
                    strategy_info['strategy_key'] = strategy_key
                    strategies.append(strategy_info)
            except Exception as e:
                print(f"Erro ao processar {yaml_file.name}: {e}")
                continue
        
        return strategies
    
    def _parse_strategy_file(self, yaml_path: Path) -> Optional[Dict]:
        """
        Parse de um arquivo YAML de estrategia
        
        Args:
            yaml_path: Caminho do arquivo YAML
            
        Returns:
            Dict com informacoes da estrategia ou None
        """
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if not config:
                return None
            
            # Extrair informacoes principais
            strategy_info = {
                'name': config.get('strategy_name', 'Unknown'),
                'class': config.get('strategy_class', 'Unknown'),
                'module': config.get('strategy_module', 'Unknown'),
                'config_file': yaml_path.name,
                'parameters': config.get('parameters', {}),
                'metadata': config.get('metadata', {}),
            }
            
            # Adicionar resumo de parametros
            params = config.get('parameters', {})
            strategy_info['parameter_summary'] = {
                'min_amplitude_mult': params.get('min_amplitude_mult'),
                'min_volume_mult': params.get('min_volume_mult'),
                'horario_inicio': params.get('horario_inicio'),
                'horario_fim': params.get('horario_fim'),
            }
            
            return strategy_info
            
        except Exception as e:
            print(f"Erro ao fazer parse de {yaml_path}: {e}")
            return None
    
    def get_strategy_by_key(self, strategy_key: str) -> Optional[Dict]:
        """
        Busca estrategia especifica por chave
        
        Args:
            strategy_key: Nome da estrategia (ex: 'barra_elefante')
            
        Returns:
            Dict com info da estrategia ou None
        """
        strategies = self.discover_strategies()
        for strategy in strategies:
            if strategy.get('strategy_key') == strategy_key:
                return strategy
        return None
    
    def set_active_strategy(self, strategy_key: str) -> bool:
        """
        Define estrategia ativa no config.yaml
        
        Args:
            strategy_key: Nome da estrategia
            
        Returns:
            True se sucesso, False caso contrario
        """
        try:
            if not self.config_path.exists():
                return False
            
            # Verificar se estrategia existe
            if not self.get_strategy_by_key(strategy_key):
                return False
            
            # Ler config atual
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Atualizar estrategia ativa
            config['active_strategy'] = strategy_key
            
            # Salvar
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            print(f"Erro ao definir estrategia ativa: {e}")
            return False


# Instancia singleton
_strategy_discovery = None

def get_strategy_discovery() -> StrategyDiscoveryService:
    """Retorna instancia singleton do servico"""
    global _strategy_discovery
    if _strategy_discovery is None:
        _strategy_discovery = StrategyDiscoveryService()
    return _strategy_discovery

