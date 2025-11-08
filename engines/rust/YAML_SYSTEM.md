# 🎯 Sistema YAML Dinâmico - Rust Engine

**Versão**: 2.0  
**Data**: 2025-11-08  
**Status**: ✅ PRONTO PARA USO

---

## 🌟 O QUE É?

Sistema **100% dinâmico** que permite testar **qualquer estratégia** sem recompilar o Rust!

### Antes (❌ Ruim)
```bash
# Mudar estratégia = editar código + recompilar (7 min)
cargo build --release  # 😴 Esperar...
optimize_smart.exe --tests 1000
```

### Agora (✅ BOM!)
```bash
# Mudar estratégia = editar YAML (0 min)
optimize_dynamic.exe --config strategies/power_breakout/config_rust.yaml --tests 1000
```

**SEM RECOMPILAÇÃO!** 🚀

---

## 📋 COMO FUNCIONA

### 1. Criar Arquivo YAML para Sua Estratégia

```yaml
# strategies/minha_estrategia/config_rust.yaml

strategy:
  name: "minha_estrategia"
  description: "Descrição da estratégia"

param_grid:
  # Parâmetros FLOAT
  stop_loss:
    type: float
    values: [0.01, 0.02, 0.03]
    description: "Stop loss percentual"
  
  # Parâmetros INTEGER
  period:
    type: integer
    values: [10, 20, 50, 100]
    description: "Período da média móvel"
  
  # Parâmetros BOOLEAN
  use_filter:
    type: boolean
    values: [true, false]
    description: "Usar filtro de tendência"
  
  # Parâmetros FIXOS (não variam)
  horario_inicio:
    type: integer
    values: [9]
    fixed: true

execution:
  max_tests: 1000  # Limitar testes (0 = todos)
  randomize: false
  batch_size: 5000
```

---

### 2. Executar Otimização

```bash
cd engines/rust

# Teste rápido (100 combos)
.\target\release\optimize_dynamic.exe \
  --config ../../strategies/barra_elefante/config_rust.yaml \
  --tests 100 \
  --output results_test.csv \
  --cores 24

# Grid completo (todas as combinações)
.\target\release\optimize_dynamic.exe \
  --config ../../strategies/barra_elefante/config_rust.yaml \
  --output results_full.csv \
  --cores 24

# Com dataset específico
.\target\release\optimize_dynamic.exe \
  --config ../../strategies/power_breakout/config_rust.yaml \
  --data /caminho/para/dataset.parquet \
  --tests 5000 \
  --cores 16
```

---

## 🎨 EXEMPLOS DE ESTRATÉGIAS

### Exemplo 1: Barra Elefante

**Arquivo**: `strategies/barra_elefante/config_rust.yaml`

**Parâmetros**:
- `min_amplitude_mult` (float): 1.5, 2.0, 2.5, 3.0
- `min_volume_mult` (float): 1.3, 1.5, 2.0, 2.5
- `max_sombra_pct` (float): 0.3, 0.4, 0.5
- `lookback_amplitude` (integer): 10, 15, 20, 25, 30
- `usar_trailing` (boolean): true, false
- ... (13 parâmetros total)

**Total de combinações**: 46,080

---

### Exemplo 2: Power Breakout (Exemplo)

**Arquivo**: `strategies/power_breakout/config_rust.yaml`

**Parâmetros DIFERENTES**:
- `bb_period` (integer): 20, 30, 40
- `bb_std` (float): 2.0, 2.5, 3.0
- `min_volume_ratio` (float): 1.5, 2.0, 3.0
- `ema_fast` (integer): 9, 12, 21
- `ema_slow` (integer): 50, 100, 200
- ... (9 parâmetros)

**Total de combinações**: 8,748

---

## 🔧 CRIANDO SUA PRÓPRIA ESTRATÉGIA

### Passo 1: Criar Diretório

```bash
mkdir strategies/minha_estrategia
```

---

### Passo 2: Criar config_rust.yaml

```yaml
strategy:
  name: "minha_estrategia"
  description: "Minha estratégia personalizada"
  version: "1.0"

param_grid:
  # IMPORTANTE: Adicione TODOS os parâmetros que sua estratégia usa
  # Se faltar algum, vai dar erro na conversão
  
  parametro_1:
    type: float
    values: [1.0, 2.0, 3.0]
  
  parametro_2:
    type: integer
    values: [10, 20, 30]
  
  parametro_3:
    type: boolean
    values: [true, false]

execution:
  max_tests: 0  # 0 = todas as combinações
  randomize: false
  batch_size: 5000
```

---

### Passo 3: Implementar Estratégia em Rust

**ATENÇÃO**: Atualmente o sistema YAML só funciona com `BarraElefanteParams` porque a conversão está hardcoded.

Para adicionar suporte a novas estratégias, você precisa:

1. Criar struct em `src/types.rs`:

```rust
#[derive(Debug, Clone)]
pub struct MinhaEstrategiaParams {
    pub parametro_1: f32,
    pub parametro_2: i32,
    pub parametro_3: bool,
}
```

2. Adicionar conversão em `optimize_dynamic.rs`:

```rust
fn paramset_to_minha_estrategia(params: &ParamSet) -> MinhaEstrategiaParams {
    MinhaEstrategiaParams {
        parametro_1: params.get("parametro_1").unwrap().as_f32(),
        parametro_2: params.get("parametro_2").unwrap().as_i32(),
        parametro_3: params.get("parametro_3").unwrap().as_bool(),
    }
}
```

3. Adicionar lógica de escolha por estratégia no main().

---

## 📊 FORMATO DO YAML

### Tipos Suportados

| Tipo | Descrição | Exemplo |
|------|-----------|---------|
| `float` | Números decimais | `[1.5, 2.0, 2.5]` |
| `integer` | Números inteiros | `[10, 20, 30, 40]` |
| `boolean` | Verdadeiro/Falso | `[true, false]` |

---

### Opções Especiais

```yaml
parametro:
  type: integer
  values: [10]
  fixed: true  # NÃO varia (sempre 10)
  description: "Descrição opcional"
```

---

## 🎯 ARGUMENTOS CLI

```bash
optimize_dynamic.exe [OPTIONS]

OBRIGATÓRIO:
  --config <ARQUIVO>    Caminho do YAML de configuração

OPCIONAIS:
  --data <ARQUIVO>      Dados Parquet [default: ../../data/golden/...]
  --output <ARQUIVO>    Arquivo de saída CSV
  --tests <N>           Limitar número de testes (0 = todos)
  --cores <N>           Número de cores [default: todos]
  -h, --help            Mostrar ajuda
```

---

## 📈 VANTAGENS

✅ **Sem Recompilação**: Mude parâmetros instantaneamente  
✅ **Flexível**: Cada estratégia tem seus próprios parâmetros  
✅ **Documentado**: YAML é auto-explicativo  
✅ **Versionável**: Commitar YAMLs no Git  
✅ **Colaborativo**: Equipe pode criar configs  
✅ **Experimentação Rápida**: Testar variações facilmente

---

## ⚠️ LIMITAÇÕES ATUAIS

1. **Conversão Hardcoded**: Só funciona com `BarraElefanteParams`
   - **Solução**: Implementar sistema genérico de estratégias (futuro)

2. **Filtro de Data**: Ainda não implementado via YAML
   - **Workaround**: Usar dataset pré-filtrado

3. **Validação Limitada**: Não valida se parâmetros fazem sentido
   - **Cuidado**: Conferir YAML manualmente

---

## 🔮 FUTURO (ROADMAP)

### Fase 1: Sistema Genérico de Estratégias ⏳
- Trait `Strategy` genérico
- Conversão automática YAML → Strategy
- Suporte a qualquer estratégia sem código

### Fase 2: Validação Avançada ⏳
- Ranges (min/max/step)
- Validação de tipos
- Dependências entre parâmetros

### Fase 3: Features Avançadas ⏳
- Otimização Bayesiana
- Grid Search inteligente
- Paralelização distribuída

---

## 📝 EXEMPLOS PRÁTICOS

### Smoke Test Rápido (100 testes)
```bash
optimize_dynamic.exe \
  --config ../../strategies/barra_elefante/config_rust.yaml \
  --tests 100 \
  --cores 24
```

### Grid Completo (46k testes)
```bash
optimize_dynamic.exe \
  --config ../../strategies/barra_elefante/config_rust.yaml \
  --output full_grid.csv
```

### Múltiplas Estratégias
```bash
# Barra Elefante
optimize_dynamic.exe --config strategies/barra_elefante/config_rust.yaml

# Power Breakout
optimize_dynamic.exe --config strategies/power_breakout/config_rust.yaml

# Inside Bar (quando implementar)
optimize_dynamic.exe --config strategies/inside_bar/config_rust.yaml
```

---

## 🎓 RESUMO

**Antes**: Rust = rígido, recompilação constante  
**Agora**: Rust = flexível, zero recompilação  

**Workflow**:
1. Criar `config_rust.yaml`
2. Executar `optimize_dynamic.exe --config ...`
3. Analisar resultados
4. Ajustar YAML e repetir

**SEM RECOMPILAR!** 🎉

---

**Documentação**: `engines/rust/YAML_SYSTEM.md`  
**Exemplos**: `strategies/*/config_rust.yaml`  
**Código**: `engines/rust/src/bin/optimize_dynamic.rs`  
**Criado**: 2025-11-08  
**Versão**: 2.0

