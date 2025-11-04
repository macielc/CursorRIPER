# σ₄: Active Context
*v1.3 | Created: 2025-11-03 | Updated: 2025-11-03*
*Π: DEVELOPMENT | Ω: EXECUTE*

## 🔮 Current Focus

**Sistema Híbrido Python Monitor + MT5 Executor - IMPLEMENTADO** ✅

Mudança estratégica aprovada: ao invés de buscar identidade 100% Python ↔ MT5 EA, implementamos sistema híbrido onde Python detecta sinais e MT5 apenas executa. Sistema completo e pronto para testes.

### Active Tasks
- [✅] RIPER initialization complete (all 7 memory files)
- [✅] RIPER mode commands implemented (/r, /i, /p, /e, /rev)
- [✅] Python backtest janeiro/2024 complete (27 trades)
- [✅] **DECISÃO ESTRATÉGICA**: Sistema Híbrido ao invés de EA standalone
- [✅] **Ω₄·EXECUTE**: Sistema Híbrido implementado
- [✅] mt5_connector.py - Interface MT5 API
- [✅] signal_detector.py - Detector de sinais (reutiliza strategy.py)
- [✅] monitor_elefante.py - Loop principal de monitoramento
- [✅] config.yaml - Configurações completas
- [✅] test_connection.py - Script de validação
- [✅] README.md - Documentação completa
- [⏳] **PRÓXIMO**: Testar sistema em dry-run

## 📎 Context References

### 📄 Active Files
- `mt5_integration/ea_templates/EA_BarraElefante_SIMPLES.mq5` - EA under debug
- `strategies/barra_elefante/strategy.py` - Python reference implementation
- `test_smoke_simple.py` - Standalone Python test (janeiro/2024)
- `results/backtest_python_jan2024.json` - Python baseline results
- `results/comparacao_python_mt5_jan2024.md` - Divergence analysis

### 💻 Active Code
- `engines/python/core/backtest_engine.py` - Python backtest execution
- `engines/python/core/optimizer.py` - Parameter optimization
- `engines/rust/src/backtest_engine.rs` - Rust backtest implementation
- `strategies/barra_elefante/strategy.py` - Volume breakout logic

### 📚 Active Docs
- `README.md` - Main project documentation
- `ESTRUTURA_COMPLETA.md` - Complete file structure
- `docs_mactester/VISAO_GERAL_SISTEMA.md` - System overview
- `docs_mactester/WORKFLOW.md` - Complete workflow guide
- `engines/rust/ARQUITETURA.md` - Rust architecture details

### 📁 Active Folders
- `engines/` - Both Python and Rust backtest engines
- `strategies/barra_elefante/` - First validated strategy
- `data/golden/` - Immutable historical data source
- `pipeline/` - 6-phase validation system
- `mt5_integration/` - EA templates and generation

### 🔄 Git References
- Current branch: `main`
- Status: Reorganization in progress (moved RIPER docs to CursorRIPER.sigma/)
- Untracked: New structure with engines/, strategies/, pipeline/

### 📏 Active Rules
- RIPER Sigma v1.0.5 (Core framework)
- **Mode**: **Ω₁·RESEARCH** (investigation phase)
- **Permissions**: ℙ(Ω₁) = {C: ✗, R: ✓, U: ✗, D: ✗}
- **Commands**: /r, /i, /p, /e, /rev implemented

## 🔄 Recent Changes

- [2025-11-03 21:00] [C₁] RIPER mode commands implemented (/r, /i, /p, /e, /rev)
- [2025-11-03 20:30] [C₂] EA v2.00 corrected (removed slippage), tested, 0 trades
- [2025-11-03 20:00] [C₃] Python janeiro/2024 backtest complete (27 trades)
- [2025-11-03 19:30] [C₄] Created 5 analysis documents (divergence, instructions, params)
- [2025-11-03 19:00] [C₅] Identified MT5 v1.00 slippage issue (+10 min delay)
- [2025-11-03 18:00] [C₆] Fixed Python date filtering bug (ZeroDivisionError)
- [2025-11-03 17:00] [C₇] Enhanced run_pipeline.py with motor/period selection

## 🧠 Active Decisions

### [D₁] [✅] Dual Engine Architecture
**Decision**: Maintain both Python (development) and Rust (production) engines
**Status**: Implemented, both engines operational
**Rationale**: Balance development speed with execution performance

### [D₂] [✅] Golden Data as Single Source of Truth
**Decision**: Use immutable CSV files exported from MT5
**Status**: Implemented, ~670 MB of 5-year data
**Rationale**: Reproducibility and cross-engine identity verification

### [D₃] [⏳] 6-Phase Validation Pipeline
**Decision**: Rigorous multi-phase validation before live trading
**Status**: Partially implemented (validators exist, integration pending)
**Next**: Complete pipeline orchestration and testing

### [D₄] [⏳] Barra Elefante Strategy Validation
**Decision**: First strategy to fully validate through complete pipeline
**Status**: Strategy implemented, validation testing in progress
**Next**: Run smoke test (1 day) → 1 month → full pipeline

### [D₅] [🔜] Python ↔️ Rust Identity Verification
**Decision**: Require 100% identical results between engines
**Status**: Comparison tools exist but not yet executed
**Next**: Run identical parameter sets, compare trade-by-trade

## ⏭️ Next Steps

### Immediate (Blocked - Awaiting User Input)
1. [N₁] **Ω₁·RESEARCH**: Collect MT5 logs/info (compilação, Journal, dados históricos)
2. [N₂] **Ω₁·RESEARCH**: Identify root cause of EA 0 trades
3. [N₃] **Ω₃·PLAN**: Create structured fix plan (after diagnosis)
4. [N₄] **Ω₄·EXECUTE**: Implement EA correction v3.00

### Short Term (This Month)
5. [N₅] **1-month backtest** - January 2024, 1k parameter combinations
6. [N₆] **Strategy refinement** - Analyze results, adjust Barra Elefante if needed
7. [N₇] **Pipeline Phase 1-2** - Run Smoke Test and Mass Optimization phases
8. [N₈] **Documentation updates** - Document findings and best parameters

### Medium Term (Next Quarter)
9. [N₉] **Full pipeline execution** - All 6 phases with 3-6 month period
10. [N₁₀] **EA generation** - If approved, generate MT5 Expert Advisor
11. [N₁₁] **MT5 validation** - Verify EA matches Python/Rust (100% identity)
12. [N₁₂] **Second strategy** - Begin development of next trading strategy

### Long Term (6+ Months)
13. [N₁₃] **Paper trading** - Demo account with generated EA
14. [N₁₄] **Performance monitoring** - Real-time vs backtest comparison
15. [N₁₅] **Live trading consideration** - If paper trading successful
16. [N₁₆] **Multi-strategy portfolio** - Combine multiple validated strategies

## 🚧 Current Challenges

### [CH₁] Engine Identity Verification Not Yet Performed
**Challenge**: Python and Rust engines exist but haven't been compared yet
**Impact**: Unknown if implementations are truly identical
**Mitigation**: Priority task - run smoke test on both, compare results
**Blocked**: No blockers, ready to execute

### [CH₂] Pipeline Integration Incomplete
**Challenge**: Individual validators exist but orchestration not fully tested
**Impact**: Can't run complete 6-phase validation yet
**Mitigation**: Test `run_pipeline.py` with small dataset first
**Blocked**: No blockers, needs testing

### [CH₃] Golden Data Loading Performance
**Challenge**: 670 MB CSV files may have loading/parsing overhead
**Impact**: Slower iterative development cycles
**Mitigation**: Profile loading, consider caching or binary format (Parquet)
**Priority**: Low (optimize later if needed)

### [CH₄] Protection Markers Not Yet Applied
**Challenge**: No Ψ protection markers in critical codebase sections
**Impact**: Risk of accidentally modifying Golden Data or core algorithms
**Mitigation**: Identify and mark protected regions in σ₆
**Priority**: Medium (safety feature)

## 📊 Implementation Progress

### ✅ Completed
- [T₁] Project structure organized (engines/, strategies/, data/, pipeline/)
- [T₂] Python engine implemented and tested
- [T₃] Rust engine implemented and compiled (4 executables)
- [T₄] Barra Elefante strategy implemented
- [T₅] Golden Data exported from MT5 (5 years, M5 and M15)
- [T₆] Pipeline validators created (Phases 3-6)
- [T₇] MT5 EA templates created
- [T₈] Comparison tools implemented
- [T₉] Documentation created (READMEs, guides, workflow)
- [T₁₀] RIPER framework initialized (memory bank structure)

### ⏳ In Progress
- [T₁₁] RIPER memory files population (σ₁-σ₆)
- [T₁₂] Smoke test execution (not yet run)
- [T₁₃] Identity verification workflow (tools exist, not executed)
- [T₁₄] Pipeline integration testing

### 🔜 Planned
- [T₁₅] Full 6-phase pipeline execution
- [T₁₆] Protection markers application (Ψ system)
- [T₁₇] Unit test expansion (Python and Rust)
- [T₁₈] Performance profiling and optimization
- [T₁₉] EA generation and MT5 validation
- [T₂₀] Second strategy development
- [T₂₁] CI/CD setup (GitHub Actions)

## 📡 Context Status

### 🟣 Essential (Critical Path)
- `data/golden/` - Immutable data source, never modify
- `engines/python/mactester.py` - Main Python entry point
- `engines/rust/optimize_batches.exe` - Primary Rust executable
- `strategies/barra_elefante/strategy.py` - First strategy under validation
- `pipeline/run_pipeline.py` - Orchestrator for all validation phases

### 🟢 Active (Currently Working On)
- `memory-bank/` - RIPER initialization in progress
- `README.md` - Primary documentation reference
- `docs_mactester/` - System understanding and workflow
- All Python core modules (`engines/python/core/`)
- All Rust source files (`engines/rust/src/`)

### 🟡 Partially Relevant (Reference as Needed)
- `mt5_integration/` - Needed later for EA generation
- `results/` - Will populate after backtests
- `pipeline/validators/` - Phase-specific validation logic
- Historical documentation in `docs_RIPER/` and `CursorRIPER.sigma/docs/`

### 🔴 Deprecated (Ignore)
- Old `.cursor/rules/*.mdc` files (deleted, moved to CursorRIPER.sigma/)
- Old `docs/` folder (moved to `docs_RIPER/` and `CursorRIPER.sigma/docs/`)

## 🎯 Focus Areas for Current Mode (Ω₁·RESEARCH)

### Allowed Operations (ℙ(Ω₁))
- ✅ **Read**: All files, logs, documentation
- ✅ **Analyze**: Code, data, behavior patterns
- ✅ **Document**: Findings, hypotheses, observations
- ❌ **Create/Update/Delete**: No file modifications

### Current Investigation Scope
1. **Primary Question**: Why did EA detect 0 trades in janeiro/2024?
2. **Known Facts**:
   - Python: 27 trades, -3,105 pts ✅
   - EA v1.00 (old): 14 trades (had +10min slippage) ⚠️
   - EA v2.00 (corrected): 0 trades ❌
3. **Hypotheses**:
   - H₁: Dados históricos não disponíveis no MT5
   - H₂: Símbolo incorreto (WIN$ vs WINFUT)
   - H₃: Lookback CopyRates falha silenciosamente
   - H₄: Lógica de shift invertida (shift 0 vs 1)
4. **Awaiting**: User's MT5 logs and configuration details

### Blocked Until
- User provides: Compilation status, Journal/Experts logs, symbol/period config, historical data confirmation

---
*σ₄ captures current state, context references, and immediate next steps*
*[↗️σ₁] for project overview | [↗️σ₂] for architecture | [↗️σ₃] for tech stack | [↗️σ₅] for progress tracking*
