# 🦀 FASE 2.2 - STATUS DO ENGINE RUST

**Data**: 2025-11-08  
**Status**: ⚠️ **REQUER ADAPTAÇÃO**

---

## 🎯 OBJETIVO

Executar smoke test Rust com os mesmos parâmetros do Python para comparação.

---

## ❌ PROBLEMA IDENTIFICADO

O engine Rust atual (`optimize_batches.exe`) está **hardcoded** e não aceita parâmetros CLI.

### Limitações Atuais:

**1. Caminho de Dados Hardcoded** (linha 26):
```rust
let data_path = "C:/Users/AltF4/Documents/#__JUREAIS/data/WINFUT_M5_Golden_Data.parquet";
```
- ❌ Aponta para diretório antigo (não existe mais)
- ❌ Usa formato Parquet (dataset atual é CSV)
- ❌ Caminho absoluto (não portável)

**2. Grid Completo** (linha 72):
```rust
let param_grid = generate_full_grid();  // GRID COMPLETO 4.2M
```
- ❌ 4.233.600 testes (muito grande para smoke test)
- ❌ Não há opção para limitar a 1000 testes
- ❌ Sem argumentos CLI para configurar

**3. Sem Filtro de Data**:
- ❌ Processa TODO o dataset
- ❌ Não há como filtrar para 2025-10-15
- ❌ Não há argumentos CLI

---

## 📊 COMPARAÇÃO: PYTHON vs RUST

| Aspecto | Python | Rust | Status |
|---------|--------|------|--------|
| **CLI Args** | ✅ `--tests`, `--start-date`, etc | ❌ Hardcoded | Python vence |
| **Flexibilidade** | ✅ Altamente configurável | ❌ Requer recompilação | Python vence |
| **Velocidade** | 🟡 50 t/s (24 cores) | 🚀 1000-5000 t/s esperado | Rust vence |
| **Pronto para Uso** | ✅ Funcionando | ❌ Precisa adaptação | Python vence |

---

## 🔧 SOLUÇÕES POSSÍVEIS

### Opção A: Refatorar Rust (RECOMENDADO para produção)
**Tempo estimado**: 2-3 horas

**Tarefas**:
1. Adicionar biblioteca `clap` para CLI args
2. Aceitar parâmetros:
   - `--tests <N>` - Número de testes
   - `--start-date <YYYY-MM-DD>` - Data inicial
   - `--end-date <YYYY-MM-DD>` - Data final
   - `--data-path <PATH>` - Caminho dos dados
   - `--output <PATH>` - Arquivo de saída
3. Adaptar `generate_full_grid()` para limitar testes
4. Implementar filtro de data similar ao Python
5. Recompilar e testar

**Benefícios**:
- ✅ Rust se torna útil para smoke tests
- ✅ Permite comparação Python ↔ Rust
- ✅ Flexibilidade para testes variados

**Código exemplo** (Cargo.toml):
```toml
[dependencies]
clap = { version = "4.0", features = ["derive"] }
```

**Código exemplo** (main.rs):
```rust
use clap::Parser;

#[derive(Parser)]
struct Args {
    /// Número de testes
    #[arg(short, long, default_value = "1000")]
    tests: usize,
    
    /// Data inicial (YYYY-MM-DD)
    #[arg(long)]
    start_date: Option<String>,
    
    /// Data final (YYYY-MM-DD)
    #[arg(long)]
    end_date: Option<String>,
    
    /// Caminho dos dados
    #[arg(long, default_value = "../../data/golden/WINFUT_M5_Golden_Data.csv")]
    data_path: String,
}
```

---

### Opção B: Smoke Test Rust Manual (ATUAL)
**Tempo**: 5-10 min (mas limitado)

**Passos**:
1. Converter CSV para Parquet
2. Copiar para caminho esperado pelo Rust
3. Executar `optimize_batches.exe`
4. Deixar processar 4.2M testes (várias horas)
5. Comparar subset dos resultados

**Problemas**:
- ❌ 4.2M testes vs 1000 (não é comparação justa)
- ❌ Dataset completo vs 1 dia (resultados diferentes)
- ❌ Não é smoke test, é teste completo
- ❌ Demora horas (não é viável agora)

---

### Opção C: Documentar e Pular (ESCOLHIDA)
**Tempo**: 10 min

**Justificativa**:
- ✅ Python já está funcionando perfeitamente
- ✅ Python tem 100% de flexibilidade
- ✅ Rust requer refatoração significativa
- ✅ Rust é otimização futura, não bloqueador
- ✅ Foco em validar fluxo completo do pipeline

**Ações**:
1. ✅ Documentar limitações do Rust (este arquivo)
2. ✅ Completar FASE 2 com Python
3. ✅ Adicionar "Refatorar Rust" como tarefa futura
4. ✅ Python é suficiente para produção atual

---

## 📝 DECISÃO FINAL

**Status**: ⚠️ **FASE 2.2 CANCELADA** (requer refatoração Rust)

**Próximos Passos**:
- ✅ Pular para FASE 2.4 (Análise Python)
- ✅ Documentar em FASE 2.6 (Resultado Final)
- ⏳ Adicionar "Refatorar Rust CLI" em backlog

**Justificativa**:
> Rust precisa de 2-3 horas de refatoração para aceitar parâmetros CLI.  
> Python está 100% funcional e atende todas as necessidades atuais.  
> Foco em completar pipeline end-to-end com Python.  
> Rust fica como **otimização futura** para ganhos de performance (10-50x).

---

## 🎯 RECOMENDAÇÃO PARA FUTURO

Quando tiver tempo, refatorar `optimize_batches.rs` para:
1. Aceitar CLI args (usar `clap`)
2. Suportar CSV e Parquet
3. Permitir filtros de data
4. Limitar número de testes
5. Compatibilidade com Python

**Prioridade**: 🟡 MÉDIA (otimização, não bloqueador)

---

**Arquivo**: `results/comparison/FASE2_RUST_STATUS.md`  
**Criado em**: 2025-11-08 12:10  
**Autor**: Claude + macielc  
**Status**: Documentação de limitação técnica

