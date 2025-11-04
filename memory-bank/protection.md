# σ₆: Protection Registry
*v1.0 | Created: 2025-11-03 | Updated: 2025-11-03*
*Π: DEVELOPMENT | Ω: EXECUTE*

## 🛡️ Protected Regions

### Critical Protected Areas (Ψ₁·PROTECTED)

These sections are **CRITICAL** and should **NEVER** be modified without explicit approval and full validation workflow.

#### [P₁] Golden Data Files
**Location**: `data/golden/`
**Files**: 
- `WINFUT_M5_Golden_Data.csv`
- `WINFUT_M15_Golden_Data.csv`
- `metadata.json`

**Protection Level**: Ψ₁·PROTECTED (🔒)
**Rationale**: Single source of truth. Immutable historical data ensures reproducibility.
**Rules**:
- ❌ NEVER modify these files
- ❌ NEVER delete these files
- ❌ NEVER add columns or change format
- ✅ READ ONLY access
- ✅ Can create NEW golden data files with different date ranges (new files, not modifications)

**Violations**: None

**Approved Modifications**: None

---

#### [P₂] Rust Compiled Binaries
**Location**: `engines/rust/*.exe`
**Files**:
- `optimize_batches.exe`
- `optimize_threads.exe`
- `optimize_standalone.exe`
- `validate_single.exe`

**Protection Level**: Ψ₁·PROTECTED (🔒)
**Rationale**: Production executables. Deleting without rebuild capability is catastrophic.
**Rules**:
- ❌ DO NOT delete unless you can rebuild from source
- ✅ Can rebuild with `cargo build --release` or `build.ps1`
- ✅ Can update by recompiling from modified source

**Violations**: None

**Approved Modifications**: Replace only by recompiling from source

---

#### [P₃] Core Backtest Algorithms
**Location**: 
- `engines/python/core/backtest_engine.py` (lines 50-250, trade execution logic)
- `engines/rust/src/backtest_engine.rs` (lines 80-300, trade execution logic)

**Protection Level**: Ψ₁·PROTECTED (🔒)
**Rationale**: Core logic that determines trade execution. Changes risk breaking identity between engines.
**Rules**:
- ❌ DO NOT modify without:
  1. Complete understanding of both Python AND Rust implementations
  2. Test plan for identity verification
  3. Backup of current version
- ✅ Can add tests, comments, documentation
- ✅ Bug fixes allowed but require immediate re-verification of Python == Rust

**Violations**: None

**Approved Modifications**: None yet (mark sections with `# Ψ₁·PROTECTED` and `# END-P` when identified)

---

### Guarded Areas (Ψ₂·GUARDED)

These sections are **IMPORTANT** and require **CAUTION**. Request permission or create detailed plan before modifying.

#### [G₁] Metrics Calculation
**Location**:
- `engines/python/core/metrics.py`
- `engines/rust/src/metrics.rs`

**Protection Level**: Ψ₂·GUARDED (🛡️)
**Rationale**: Metrics must be calculated identically in both engines. Changes risk discrepancies.
**Rules**:
- ⚠️ Request review before modification
- ⚠️ Update both Python AND Rust simultaneously
- ✅ Can add new metrics if implemented in both
- ✅ Can refactor for clarity if behavior identical

**Approved Changes**: None yet

---

#### [G₂] Data Loading Logic
**Location**:
- `engines/python/core/data_loader.py`
- `engines/rust/src/backtest_engine.rs` (data loading sections)

**Protection Level**: Ψ₂·GUARDED (🛡️)
**Rationale**: Both engines must load data identically (same columns, same types, same order)
**Rules**:
- ⚠️ Changes must preserve data format and column order
- ⚠️ Verify both engines load identically after changes
- ✅ Can optimize performance if output identical
- ✅ Can add caching/memoization

**Approved Changes**: None yet

---

#### [G₃] Strategy Interface
**Location**:
- `engines/python/core/strategy_base.py` (base class)
- `strategies/barra_elefante/strategy.py` (implementation)

**Protection Level**: Ψ₂·GUARDED (🛡️)
**Rationale**: Strategy interface contract must remain stable. Changes affect all strategies.
**Rules**:
- ⚠️ Interface changes require updating ALL strategies
- ⚠️ Must remain compatible with both Python and Rust engines
- ✅ Can add optional methods (backward compatible)
- ✅ Can improve documentation

**Approved Changes**: None yet

---

#### [G₄] Pipeline Validation Criteria
**Location**:
- `pipeline/validators/fase3_walkforward.py` (line ~45, approval criteria)
- `pipeline/validators/fase4_out_of_sample.py` (line ~30, approval criteria)
- `pipeline/validators/fase5_outlier_analysis.py` (line ~50, approval criteria)
- `pipeline/validators/fase6_relatorio_final.py` (line ~60, final decision logic)

**Protection Level**: Ψ₂·GUARDED (🛡️)
**Rationale**: Approval criteria are system requirements. Changes affect what strategies get approved.
**Rules**:
- ⚠️ Document rationale for any threshold changes
- ⚠️ Update σ₁ (requirements) if criteria change
- ✅ Can add additional checks (more rigorous)
- ✅ Can adjust thresholds based on empirical data (with justification)

**Approved Changes**: None yet

---

### Informational Markers (Ψ₃·INFO)

Areas marked for information, no protection needed but worth noting.

#### [I₁] Configuration Files
**Location**:
- `engines/python/config.yaml`
- `engines/rust/Cargo.toml`

**Protection Level**: Ψ₃·INFO (ℹ️)
**Purpose**: Configuration is meant to be edited. Mark for visibility.
**Note**: Changes are normal and expected. Version control tracks history.

---

#### [I₂] Documentation Files
**Location**: All `README.md`, `*.md` files in `docs_mactester/`, etc.

**Protection Level**: Ψ₃·INFO (ℹ️)
**Purpose**: Documentation should evolve. Mark for tracking.
**Note**: Keep synchronized with code changes.

---

### Debug/Test Sections (Ψ₄·DEBUG, Ψ₅·TEST)

Code used for debugging or testing, can be modified freely.

#### [D₁] Example/Test Scripts
**Location**:
- `engines/rust/examples/`
- Any files named `test_*.py` or `*_test.py`

**Protection Level**: Ψ₅·TEST (🧪)
**Purpose**: Test code, modify as needed
**Note**: Can be deleted or changed without affecting production

---

## 📜 Protection History

### 2025-11-03: Initial Protection Registry
**Action**: Created protection registry during RIPER initialization
**Files Protected**: 
- Golden Data (Ψ₁·PROTECTED)
- Rust binaries (Ψ₁·PROTECTED)
- Core algorithms (Ψ₁·PROTECTED - sections to be marked)

**By**: RIPER Framework initialization
**Rationale**: Establish baseline protection for critical system components

---

## ✅ Approvals

*No modification approvals logged yet. When protected areas need changes, document here.*

### Approval Template
```
### [YYYY-MM-DD] Approval ID: A₁
**Protected Area**: [Which protected section]
**Requested By**: [Who]
**Reason**: [Why modification is needed]
**Change Description**: [What will change]
**Test Plan**: [How to verify safety]
**Approved By**: [Approval authority]
**Status**: APPROVED/REJECTED/PENDING
**Completed**: [Date or N/A]
```

---

## ⚠️ Permission Violations

*No violations logged yet. This section tracks unauthorized modifications to protected areas.*

### Violation Template
```
### [YYYY-MM-DD] Violation ID: V₁
**Protected Area**: [Which section was modified]
**Violation Type**: [Unauthorized modification, deletion, etc.]
**Detected By**: [System, user, automated check]
**Impact**: [CRITICAL/HIGH/MEDIUM/LOW]
**Details**: [What happened]
**Resolution**: [How it was fixed]
**Prevention**: [How to prevent recurrence]
```

---

## 🔐 Protection Implementation Status

### Applied Protections
- ✅ Golden Data (file-level, enforced by .gitignore for modifications)
- ✅ Rust binaries (documented, user awareness)
- 🔜 Core algorithms (need to add inline markers)
- 🔜 Metrics calculations (need to add inline markers)
- 🔜 Data loading (need to add inline markers)

### Pending Implementation
- [ ] Add inline Ψ markers to Python code (backtest_engine.py)
- [ ] Add inline Ψ markers to Rust code (backtest_engine.rs)
- [ ] Create pre-commit hook to warn on protected file changes
- [ ] Add automated checks for Golden Data integrity
- [ ] Document protection markers in code review guidelines

---

## 📋 Protection Application Guidelines

### How to Mark Protected Code

#### Python Example
```python
# Ψ₁·PROTECTED: Core trade execution logic
# DO NOT MODIFY without identity verification plan
# Changes must be synchronized with Rust implementation
def execute_trade(position, signal, price):
    # Core execution logic here
    ...
    return result
# END-P
```

#### Rust Example
```rust
// Ψ₁·PROTECTED: Core trade execution logic
// DO NOT MODIFY without identity verification plan
// Changes must be synchronized with Python implementation
fn execute_trade(position: &Position, signal: Signal, price: f64) -> Result<Trade> {
    // Core execution logic here
    ...
}
// END-P
```

### Protection Levels Reference

| Level | Symbol | Name | When to Use |
|-------|--------|------|-------------|
| Ψ₁ | 🔒 | PROTECTED | Mission-critical, immutable data, core algorithms |
| Ψ₂ | 🛡️ | GUARDED | Important logic, multi-engine coordination, interfaces |
| Ψ₃ | ℹ️ | INFO | Configuration, documentation (informational only) |
| Ψ₄ | 🐞 | DEBUG | Debug code, temporary instrumentation |
| Ψ₅ | 🧪 | TEST | Test code, examples, experiments |
| Ψ₆ | ⚠️ | CRITICAL | Life-safety or financial-critical code (future use) |

---

## 🎯 Protection Priorities

### High Priority (Implement Immediately)
1. **Mark Core Algorithms**: Add Ψ₁ markers to backtest engines
2. **Golden Data Integrity**: Verify checksums, document expected hashes
3. **Pre-commit Hooks**: Warn on modifications to protected files

### Medium Priority (Next Sprint)
4. **Metrics Protection**: Add Ψ₂ markers to metrics calculations
5. **Interface Protection**: Add Ψ₂ markers to strategy interfaces
6. **Documentation**: Create protection guidelines for contributors

### Low Priority (Future)
7. **Automated Enforcement**: CI/CD checks for protection violations
8. **Binary Verification**: Checksum verification for Rust executables
9. **Audit Logging**: Detailed logs of all protected area accesses

---

## 🔍 Related Memory Files

- [↗️σ₁] Project requirements define what needs protection
- [↗️σ₂] Architecture shows dependencies and critical paths
- [↗️σ₄] Active context tracks current protection work
- [↗️σ₅] Progress tracks protection implementation status

---

*σ₆ maintains protection registry and modification history to ensure system integrity*
