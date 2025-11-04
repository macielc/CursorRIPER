# σ₃: Technical Context
*v1.0 | Created: 2025-11-03 | Updated: 2025-11-03*
*Π: DEVELOPMENT | Ω: EXECUTE*

## 🛠️ Technology Stack

### 🐍 Python Engine (Primary Development)
- **Version**: Python 3.8+
- **Core Libraries**:
  - `pandas` - Data manipulation and CSV loading
  - `numpy` - Numerical computations and array operations
  - `PyYAML` - Configuration file parsing (`config.yaml`)
  - `matplotlib` / `seaborn` - Visualization and plotting
  - `scipy` - Statistical analysis
  - `joblib` - Parallel processing
- **Purpose**: Rapid prototyping, debugging, visualization, validation development
- **Entry Point**: `engines/python/mactester.py`
- **CLI**: Argparse-based command-line interface

### 🦀 Rust Engine (Production Performance)
- **Version**: Rust 1.70+ (2021 edition)
- **Core Crates**:
  - `serde` + `serde_json` - Serialization/deserialization
  - `csv` - CSV file parsing
  - `rayon` - Data parallelism
  - `chrono` - Date/time handling
  - `clap` - Command-line argument parsing
  - `indicatif` - Progress bars for long-running optimizations
- **Build**: Cargo-based, PowerShell build script (`build.ps1`)
- **Binaries**:
  - `optimize_batches.exe` - Batch optimization with progress tracking
  - `optimize_threads.exe` - Multi-threaded optimization
  - `optimize_standalone.exe` - Single-run optimizer
  - `validate_single.exe` - Single parameter set validator
- **Purpose**: Production-grade performance (10-50x Python), massive parameter sweeps
- **Architecture**: Multi-threaded, immutable data structures where possible

### 📊 MetaTrader 5 (Trading Platform)
- **Language**: MQL5 (C++-like)
- **Purpose**: Live trading execution, EA validation, data export
- **Integration**: 
  - Expert Advisors (EAs) generated from Python/Rust validated results
  - Strategy Tester for EA validation
  - Data export to Golden Data CSV files
- **Templates**: `mt5_integration/ea_templates/`

### 🗄️ Data Storage
- **Format**: CSV (Comma-Separated Values)
- **Golden Data Files**:
  - `WINFUT_M5_Golden_Data.csv` (~500 MB, 5-minute bars, 5 years)
  - `WINFUT_M15_Golden_Data.csv` (~170 MB, 15-minute bars, 5 years)
- **Metadata**: `metadata.json` (file info, date ranges, column descriptions)
- **Results**: JSON (metrics, parameters) + CSV (trade logs, equity curves)
- **No Database**: Intentional choice for simplicity and portability

### 🔄 Version Control
- **System**: Git
- **Platform**: GitHub (presumed)
- **Ignore**: `.gitignore` excludes results/, large data files (use Git LFS if needed)
- **Structure**: Mono-repo with engines/, strategies/, data/, pipeline/

## 🌍 Environment

### Development Environment
- **OS**: Windows 10+ (primary target for MT5 integration)
- **Shell**: PowerShell 7+ (for Rust build scripts)
- **Python**: Virtual environment recommended (`venv` or `conda`)
- **Rust**: Installed via `rustup`, targets `x86_64-pc-windows-msvc`

### File Structure
```
release_1.0/
├── engines/
│   ├── python/        # Python engine + core modules
│   └── rust/          # Rust source + compiled binaries
├── strategies/        # Strategy modules
├── data/golden/       # Golden Data (immutable)
├── results/           # Output (gitignored)
├── pipeline/          # Validation orchestration
├── mt5_integration/   # EA templates and generation
└── memory-bank/       # RIPER memory files (this system)
```

### Configuration Files
- **Python**: `engines/python/config.yaml` (strategy params, risk settings, paths)
- **Rust**: `engines/rust/Cargo.toml` (dependencies, build config)
- **Pipeline**: Inline configuration in `run_pipeline.py`

### Testing Environments
- **Smoke Test**: 1 day, 10-1000 parameter combinations
- **Development Test**: 1 week - 1 month periods
- **Full Validation**: 3-12+ months via pipeline
- **MT5 Strategy Tester**: Match historical period used in backtest

## 📦 Dependencies

### Python Core Dependencies (`requirements.txt`)
```txt
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing  
PyYAML>=6.0            # Config file parsing
matplotlib>=3.7.0      # Plotting
seaborn>=0.12.0        # Statistical visualization
scipy>=1.10.0          # Statistics
joblib>=1.3.0          # Parallel processing
ta-lib>=0.4.0          # Technical indicators (optional)
```

### Python Development Dependencies
```txt
pytest>=7.0.0          # Unit testing
black>=23.0.0          # Code formatting
flake8>=6.0.0          # Linting
ipython>=8.0.0         # Interactive shell
jupyter>=1.0.0         # Notebook development
```

### Rust Core Dependencies (`Cargo.toml`)
```toml
[dependencies]
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
csv = "1.2"
rayon = "1.7"          # Parallelism
chrono = "0.4"         # Date/time
clap = { version = "4.0", features = ["derive"] }
indicatif = "0.17"     # Progress bars
```

### MT5 Requirements
- MetaTrader 5 (build 3000+)
- WIN$ (WINFUT) market data subscription
- Strategy Tester enabled
- MQL5 compiler (included with MT5)

## 🔑 Configuration

### Python Configuration (`config.yaml`)
```yaml
strategy:
  name: barra_elefante
  timeframe: 5  # minutes
  
risk:
  risk_percent: 1.0
  max_positions: 1
  
data:
  golden_data_path: ../../data/golden/
  results_path: ../../results/backtests/python/
  
optimization:
  n_jobs: -1  # Use all CPU cores
  verbose: 1
```

### Rust Configuration
- **Compile-time**: Via `Cargo.toml` features
- **Runtime**: Command-line arguments (no config file)
- **Build**: `build.ps1` script for Windows-specific compilation

### Pipeline Configuration
- **Inline**: Defined in `run_pipeline.py` as constants
- **Phases**: Each phase in `validators/` subfolder
- **Criteria**: Hardcoded validation thresholds (can extract to YAML if needed)

## 🔐 Secrets Management

**Current State**: No secrets required
- No API keys (offline historical data)
- No database credentials (CSV files)
- No cloud services (local execution)

**Future Considerations** (if live trading):
- MT5 broker credentials (environment variables)
- Telegram bot token for notifications (environment variables)
- Use `.env` file (excluded from git) for local secrets

## 🧰 Development Tools

### IDE / Editors
- **Cursor IDE**: Primary development environment with RIPER framework
- **VS Code**: Alternative for Python development
- **RustRover / VS Code**: Rust development with rust-analyzer

### Version Control
- **Git**: Distributed version control
- **GitHub**: Remote repository (assumed)
- **Git LFS**: For large Golden Data files (optional, currently not used)

### Testing
- **Python**: `pytest` for unit tests (to be expanded)
- **Rust**: `cargo test` for unit tests
- **Integration**: Identity verification tools (manual/scripted comparison)
- **MT5**: Strategy Tester for EA validation

### Performance Profiling
- **Python**: `cProfile`, `line_profiler` for bottleneck detection
- **Rust**: `cargo flamegraph`, built-in benchmarks
- **Comparison**: Custom scripts measure Python vs Rust speedup

### Build & Deployment
- **Python**: No build step, run directly (`python mactester.py`)
- **Rust**: 
  - `cargo build --release` for optimized binaries
  - `build.ps1` for Windows-specific compilation
  - Pre-compiled `.exe` files included in repo
- **MT5 EAs**: MetaEditor compiles `.mq5` to `.ex5` (automatic)

### Documentation
- **Code**: Inline comments, docstrings
- **Architecture**: `ARQUITETURA.md` (Rust), `docs_mactester/` folder
- **Memory Bank**: RIPER memory files (this system: σ₁-σ₆)
- **README**: Per-component README.md files

### CI/CD
**Current**: Manual execution, local testing
**Future Enhancements**:
- GitHub Actions for automated testing
- Rust compilation verification
- Python linting and formatting checks
- Identity verification on PR

## 📊 Data Specifications

### Golden Data Schema (CSV)
**Columns** (example for M5 data):
```
timestamp,open,high,low,close,volume,tick_volume,spread,ma_20,ma_50,ma_200,rsi_14,atr_14
2020-01-01 09:00:00,105000,105500,104900,105300,1234,5678,5,105200,105100,104800,52.3,450
...
```

### Results JSON Schema (Example)
```json
{
  "strategy": "barra_elefante",
  "parameters": {
    "volume_mult": 2.5,
    "atr_mult": 1.5,
    "min_body_pct": 0.6
  },
  "metrics": {
    "total_trades": 87,
    "win_rate": 0.574,
    "sharpe_ratio": 1.23,
    "profit_factor": 1.87,
    "max_drawdown": 0.089,
    "total_return": 0.245
  },
  "trades": [ ... ]
}
```

## 🔧 Setup Instructions

### Python Setup
```powershell
cd engines/python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python mactester.py --help
```

### Rust Setup (Compilation)
```powershell
cd engines/rust
.\build.ps1
# Or manually:
cargo build --release --bin optimize_batches
```

### Verification
```powershell
# Python smoke test (1 day)
cd engines/python
python mactester.py optimize --strategy barra_elefante --tests 10 --period "2024-01-02" "2024-01-02"

# Rust validation
cd engines/rust
.\validate_single.exe
```

## 🎯 Technical Priorities

### Performance Targets
- **Python**: < 1 second per backtest (1 month, single parameter set)
- **Rust**: < 0.1 second per backtest (same workload)
- **Rust Speedup**: 10-50x vs Python
- **Parallel Rust**: Linear scaling with cores (8 cores = ~8x single-core)

### Code Quality
- **Modularity**: Engines and strategies independent
- **Reproducibility**: Deterministic results for same inputs
- **Maintainability**: Clear code structure, documented decisions
- **Testability**: Unit testable components (expand coverage)

### Future Tech Debt
- Expand unit test coverage (Python and Rust)
- Extract pipeline config to YAML
- Add type hints throughout Python codebase
- Implement Rust benchmarks suite
- Consider Python CLI refactor (click/typer vs argparse)

---
*σ₃ captures technical stack and implementation details*
*[↗️σ₁] for requirements | [↗️σ₂] for architecture | [↗️σ₄] for active development focus*
