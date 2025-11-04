# Motor Rust - MacTester

Motor de backtest ultra-rapido em Rust com Rayon (paralelizacao massiva).

## Estrutura do Projeto

```
rust/
├── Cargo.toml              # Configuracao do projeto
├── Cargo.lock              # Lock de dependencias
├── build.ps1               # Script de compilacao
├── ARQUITETURA.md          # Documentacao da arquitetura
├── src/                    # Codigo fonte
│   ├── lib.rs              # Biblioteca principal
│   ├── backtest_engine.rs  # Motor de backtest
│   ├── metrics.rs          # Calculo de metricas
│   ├── optimizer.rs        # Otimizador
│   ├── strategy.rs         # Interface de estrategia
│   ├── types.rs            # Tipos de dados
│   └── bin/                # Binarios executaveis
│       ├── optimize_batches.rs
│       ├── optimize_standalone.rs
│       ├── optimize_threads.rs
│       └── validate_single.rs
├── examples/               # Exemplos de uso
│   ├── test_100k_candles.rs
│   ├── test_multicore.rs
│   └── test_multicore_pesado.rs
└── *.exe                   # Executaveis compilados
```

## Executaveis Pre-Compilados

Todos os executaveis estao pre-compilados e prontos para uso:

1. **validate_single.exe** - Valida um setup especifico
2. **optimize_standalone.exe** - Otimizacao standalone (single run)
3. **optimize_threads.exe** - Otimizacao com threads manuais
4. **optimize_batches.exe** - Otimizacao em batches (RECOMENDADO)

## Uso

### 1. Validacao Simples

Valida um setup especifico para conferir resultados:

```powershell
.\validate_single.exe
```

Este comando:
- Testa 1 configuracao especifica
- Exibe metricas detalhadas
- Gera arquivo `validation_rust_trades.csv`
- Gera arquivo `validation_rust_metrics.csv`

### 2. Otimizacao Completa (4.2M testes)

**RECOMENDADO - Usa batches para melhor performance:**

```powershell
.\optimize_batches.exe
```

Caracteristicas:
- Processa 4.233.600 combinacoes
- Usa TODOS os cores (Rayon)
- Barra de progresso em tempo real
- Salva resultados a cada batch
- Velocidade: 1000-5000 testes/segundo

Resultados salvos em:
- `results_batches_{timestamp}.csv`

### 3. Otimizacao Standalone

Para testes menores ou debugging:

```powershell
.\optimize_standalone.exe
```

### 4. Otimizacao com Threads Manuais

Versao alternativa com controle manual de threads:

```powershell
.\optimize_threads.exe
```

## Configuracao

Os executaveis buscam automaticamente:
- Golden Data: `../../data/golden/WINFUT_M5_Golden_Data.csv`
- Parametros: Hardcoded (mas podem ser modificados no fonte e recompilados)

### Parametros Testados (Barra Elefante)

- **min_body_percent**: [0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
- **min_volume_mult**: [1.2, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- **sl_mult**: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- **tp_mult**: [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
- **min_candles_sequence**: [1, 2, 3, 4, 5]
- **max_sequential_losses**: [2, 3, 4, 5, 6]
- **use_mm21_filter**: [true, false]
- **use_rsi_filter**: [true, false]
- **use_volume_filter**: [true, false]
- **use_atr_filter**: [true, false]
- **use_trend_filter**: [true, false]

Total: 8 × 7 × 7 × 7 × 5 × 5 × 2^5 = 4.233.600 combinacoes

## Performance

### Benchmarks (CPU 32 cores)

- **optimize_batches.exe**: ~3000-5000 testes/segundo
- **optimize_threads.exe**: ~2000-4000 testes/segundo
- **optimize_standalone.exe**: ~1000-2000 testes/segundo

Tempo estimado para 4.2M testes:
- Batches: 15-25 minutos
- Threads: 20-35 minutos
- Standalone: 35-70 minutos

## Comparacao com Python

### Vantagens Rust:
- 10-50x mais rapido
- Menor uso de memoria
- Processamento mais estavel
- Sem GIL (Global Interpreter Lock)

### Vantagens Python:
- Mais facil debug
- Bibliotecas ricas (pandas, numpy)
- Graficos e visualizacao
- Prototipagem rapida

## Arquivos de Saida

### Formato CSV

Colunas principais:
- Parametros da estrategia
- Total Trades
- Win Rate
- Profit Factor
- Sharpe Ratio
- Max Drawdown
- Total Return
- Avg Trade Duration

### Top Resultados

Os resultados sao ordenados automaticamente por:
1. Sharpe Ratio (primario)
2. Win Rate (secundario)
3. Total Return (terciario)

## Recompilacao

### Pre-requisitos

1. **Instalar Rust**:
   ```powershell
   # Baixar de https://rustup.rs/
   # Ou via winget:
   winget install Rustlang.Rustup
   ```

2. **Verificar instalacao**:
   ```powershell
   rustc --version
   cargo --version
   ```

### Compilar Todos os Binarios

```powershell
# Navegar ate o diretorio
cd engines/rust

# Executar script de build
.\build.ps1

# OU compilar manualmente:
cargo build --release
```

Isso gera todos os 4 executaveis em `target/release/`:
- `validate_single.exe`
- `optimize_standalone.exe`
- `optimize_threads.exe`
- `optimize_batches.exe`

### Compilar Binario Especifico

```powershell
# Apenas optimize_batches
cargo build --release --bin optimize_batches

# Apenas validate_single
cargo build --release --bin validate_single
```

### Modificar Parametros

Para alterar parametros testados (ex: ranges de min_body_percent):

1. Editar `src/strategy.rs` ou `src/bin/optimize_batches.rs`
2. Modificar os arrays de parametros
3. Recompilar: `cargo build --release`
4. Executavel atualizado em `target/release/`

### Exemplo: Alterar Grid de Parametros

```rust
// Em src/bin/optimize_batches.rs

// ANTES:
let min_body_percent = vec![0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95];

// DEPOIS (mais valores):
let min_body_percent = vec![0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00];
```

Salvar e recompilar.

## Troubleshooting

### "Cannot find Golden Data"
Certifique-se que os arquivos existem em:
```
release_1.0/data/golden/WINFUT_M5_Golden_Data.csv
```

### Performance baixa
- Feche outros programas pesados
- Verifique temperatura da CPU (thermal throttling)
- Use `optimize_batches.exe` ao inves de outros

### Memoria insuficiente
O Rust usa MUITO menos memoria que Python. Se mesmo assim faltar:
- Processe em batches menores (modificar fonte)
- Reduza o periodo de dados

## Proximos Passos

1. Execute `.\validate_single.exe` para confirmar funcionamento
2. Execute `.\optimize_batches.exe` para otimizacao completa
3. Compare resultados com Python usando `pipeline/comparar_motores.py`

