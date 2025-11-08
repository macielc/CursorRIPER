"""
Strategies Package - Strategy Discovery

Provides centralized access to all trading strategies.
"""

def get_strategy(strategy_name: str):
    """
    Retorna a classe da estratégia pelo nome
    
    Args:
        strategy_name: Nome da estratégia (ex: 'barra_elefante', 'power_breakout')
    
    Returns:
        Classe da estratégia
    
    Raises:
        ValueError: Se estratégia não encontrada
    """
    if strategy_name == 'barra_elefante':
        from strategies.barra_elefante.strategy import BarraElefanteStrategy
        return BarraElefanteStrategy
    # elif strategy_name == 'power_breakout':
    #     from strategies.power_breakout.strategy import PowerBreakoutStrategy
    #     return PowerBreakoutStrategy
    # elif strategy_name == 'inside_bar':
    #     from strategies.inside_bar.strategy import InsideBarStrategy
    #     return InsideBarStrategy
    else:
        raise ValueError(f"Estratégia não encontrada: {strategy_name}")


__all__ = ['get_strategy']

