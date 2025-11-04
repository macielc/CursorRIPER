# Estrategias Modulares - MacTester

Este diretorio contem as estrategias de trading testadas no MacTester.

## Principio de Isolamento

As estrategias sao MODULARES e ISOLADAS do motor de backtest.

### Por que isso importa?

- Motor de backtest NAO deve ser modificado para cada estrategia
- Estrategias se "acoplam" ao motor sem alterar codigo base
- Facil adicionar novas estrategias sem quebrar existentes
- Testes reproduziveis e confiaveis

## Estrutura de uma Estrategia

Cada estrategia deve ter seu proprio diretorio:

```
strategies/
└── nome_estrategia/
    ├── __init__.py
    ├── strategy.py         # Logica principal
    ├── params.json         # Parametros testaveis
    └── README.md          # Documentacao
```

### Arquivo `strategy.py`

Deve implementar a classe base com metodos:

```python
class NomeEstrategia:
    def __init__(self, params):
        # Inicializar com parametros
        pass
    
    def detect_signal(self, df, idx):
        # Detectar sinais de entrada
        # Retorna: (has_signal, direction, stop_loss, take_profit)
        pass
    
    def get_parameter_grid(self):
        # Retornar grid de parametros a testar
        pass
```

### Arquivo `params.json`

Define os parametros testaveis:

```json
{
    "min_body_percent": [0.60, 0.65, 0.70, 0.75, 0.80],
    "min_volume_mult": [1.2, 1.5, 2.0, 2.5, 3.0],
    "use_trend_filter": [true, false]
}
```

## Estrategias Implementadas

### 1. Barra Elefante

**Status**: Implementada e funcional

**Descricao**: Detecta barras de grande amplitude (elefantes) com corpo forte e volume elevado.

**Criterios**:
- Corpo deve ser X% da amplitude total
- Volume deve ser Y vezes a media
- Filtros opcionais: MM21, RSI, ATR, Tendencia

**Parametros Testaveis**: 4.233.600 combinacoes

Ver: `barra_elefante/README.md`

### 2. Inside Bar (Planejada)

**Status**: Nao implementada ainda

**Descricao**: Candle filho menor que candle mae, rompimento indica direcao.

### 3. Power Breakout (Planejada)

**Status**: Nao implementada ainda

**Descricao**: Rompimento de topo/fundo com volume e forca.

## Como Adicionar Nova Estrategia

### Passo 1: Criar Estrutura

```bash
mkdir strategies/minha_estrategia
cd strategies/minha_estrategia
touch __init__.py strategy.py params.json README.md
```

### Passo 2: Implementar Logica

Edite `strategy.py` seguindo o template:

```python
import numpy as np
import pandas as pd

class MinhaEstrategia:
    def __init__(self, params):
        self.params = params
    
    def detect_signal(self, df, idx):
        # Implementar logica de deteccao
        
        if condicao_compra:
            return (True, 1, stop_loss, take_profit)  # LONG
        elif condicao_venda:
            return (True, -1, stop_loss, take_profit)  # SHORT
        else:
            return (False, 0, 0, 0)  # SEM SINAL
    
    def get_parameter_grid(self):
        return {
            'param1': [val1, val2, val3],
            'param2': [valA, valB, valC]
        }
```

### Passo 3: Definir Parametros

Edite `params.json`:

```json
{
    "param1": [1.0, 1.5, 2.0],
    "param2": [10, 20, 30],
    "filtro_ativo": [true, false]
}
```

### Passo 4: Documentar

Edite `README.md` explicando:
- O que a estrategia faz
- Criterios de entrada/saida
- Parametros e seus significados
- Exemplos visuais (se possivel)

### Passo 5: Testar

```bash
# Teste inicial (periodo pequeno)
cd ../../engines/python
python mactester.py optimize --strategy minha_estrategia --tests 100 --timeframe 5m

# Validar resultados
cd ../../pipeline
python run_pipeline.py
```

## Metodologia de Teste

### Matriz Menor para Maior

1. **Debug (1 dia)**: Confirmar logica basica funciona
2. **Validacao (1 mes)**: Primeiros resultados estatisticos
3. **Teste Estendido (3-6 meses)**: Validacao seria
4. **Teste Historico (1-5 anos)**: Validacao completa

### Criterios de Sucesso

Uma estrategia deve:
- Gerar minimo 50 trades no periodo de teste
- Sharpe Ratio > 0.8 (Walk-Forward)
- Win Rate > 50%
- Profit Factor > 1.5
- Passar em 3/4 criterios do pipeline

## Boas Praticas

### DO:
- Manter estrategia autocontida em seu diretorio
- Documentar TODOS os parametros
- Testar em periodo pequeno primeiro
- Validar Python == Rust == MT5

### DON'T:
- Modificar motor de backtest para sua estrategia
- Hardcodar valores sem justificativa
- Pular etapas de validacao
- Assumir que backtest = sucesso garantido

## Proximos Passos

1. Validar completamente `barra_elefante`
2. Implementar `inside_bar` usando mesmo padrao
3. Implementar `power_breakout`
4. Criar template automatizado de estrategia

## Referencias

- Guia completo: `/docs/STRATEGY_TEMPLATE.md`
- Exemplos: `barra_elefante/`
- Motor: `../engines/`

