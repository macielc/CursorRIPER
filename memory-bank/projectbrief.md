# σ₁: Project Brief
*v1.0 | Created: 2025-11-03 | Updated: 2025-11-03*
*Π: DEVELOPMENT | Ω: EXECUTE*

## 🏆 Overview
**MacTester Release 1.0** is a professional, multi-engine backtesting and validation system for day trading strategies on WIN$ (Brazilian Mini-Index Futures). The system enables rigorous testing of trading strategies using historical data, validates statistical robustness through a 6-phase pipeline, compares results across multiple execution engines (Python, Rust, MT5), and automatically generates Expert Advisors for live trading.

## 📋 Requirements

### Core Requirements
- [R₁] **Multi-Engine Architecture**: Support Python (rapid prototyping) and Rust (production performance) engines with guaranteed result identity
- [R₂] **Modular Strategy System**: Isolated, plug-and-play strategy modules that integrate with engines without modification
- [R₃] **Golden Data Foundation**: Immutable historical dataset (5 years, M5/M15 timeframes) exported from MT5 as single source of truth
- [R₄] **6-Phase Validation Pipeline**: Smoke Test → Mass Optimization → Walk-Forward → Out-of-Sample → Outlier Analysis → Final Report
- [R₅] **MT5 Integration**: Automatic EA generation and validation that results match backtest engines 100%
- [R₆] **Result Identity Verification**: Python == Rust == MT5 trade-by-trade comparison
- [R₇] **Menor-para-Maior Methodology**: Always test small periods first (1 day → 1 week → 1 month → 3+ months)
- [R₈] **Statistical Rigor**: Multiple metrics (Sharpe, Win Rate, Profit Factor, Max DD, Outlier Analysis)

### Strategy Requirements
- [R₉] **Barra Elefante Strategy**: First validated strategy with volume + candlestick pattern detection
- [R₁₀] **Extensibility**: Easy addition of new strategies without touching engine code

## ✅ Success Criteria
- [C₁] **Engine Identity**: Python and Rust produce 100% identical results for same inputs
- [C₂] **MT5 Validation**: Generated EA produces 100% identical results to Python/Rust engines
- [C₃] **Pipeline Approval**: Strategy passes 3 of 4 validation criteria:
  - Walk-Forward: Sharpe > 0.8 AND 60%+ positive windows
  - Out-of-Sample: Min 5 trades AND Sharpe > 0.5
  - Outlier Analysis: Sharpe without outliers > 0.7
  - Volume: Min 50 trades in complete period
- [C₄] **Performance**: Rust engine 10-50x faster than Python for same workload
- [C₅] **Reproducibility**: Same parameters always produce same results from Golden Data
- [C₆] **Documentation**: Complete workflow documentation and usage examples

## 🔍 Scope

### ✓ In Scope
- [S₁] Python backtest engine with full metrics suite
- [S₂] Rust backtest engine (compiled executables: batches, threads, standalone, validate)
- [S₃] Barra Elefante strategy (volume breakout with elephant candles)
- [S₄] Golden Data (WINFUT_M5 and WINFUT_M15, 5 years, ~670 MB)
- [S₅] 6-phase validation pipeline implementation
- [S₆] Engine comparison tools (Python vs Rust, Python vs MT5, Rust vs MT5)
- [S₇] MT5 EA templates and automatic generation
- [S₈] Result visualization and reporting
- [S₉] Walk-forward analysis (12m train / 3m test windows)
- [S₁₀] Outlier detection and analysis
- [S₁₁] Configuration management (YAML for Python)
- [S₁₂] Comprehensive documentation

### ❌ Out of Scope
- [O₁] Real-time market data feeds (uses historical Golden Data only)
- [O₂] Live trading execution (EA generation only, execution is manual)
- [O₃] Multiple asset classes (WIN$ only for Release 1.0)
- [O₄] Machine learning / AI optimization (classical optimization only)
- [O₅] Web interface / GUI (command-line only)
- [O₆] Real-time strategy monitoring during live trading
- [O₇] Broker integration / order routing
- [O₈] Portfolio management across multiple strategies

## ⏱️ Timeline
- [T₁] **Release 1.0 Complete**: 2025-11-03 ✅
- [T₂] **Barra Elefante Validation (1 month)**: Q4 2025
- [T₃] **Full Pipeline Testing (3-6 months)**: Q1 2026
- [T₄] **Paper Trading**: Q2 2026
- [T₅] **Live Trading Consideration**: Q3 2026 (if all validations pass)

## 👥 Stakeholders
- [STK₁] **Primary User/Developer**: System architect and trader
- [STK₂] **Strategy Designer**: Day trading strategy development
- [STK₃] **Risk Manager**: Validation and risk assessment
- [STK₄] **System Validator**: Multi-engine identity verification

## 🎯 Project Goals
1. **Confidence**: Eliminate uncertainty through rigorous validation
2. **Speed**: Rust enables testing millions of parameter combinations
3. **Safety**: Detect overfitting, outliers, and unrealistic results before risking capital
4. **Modularity**: Easy strategy development and testing
5. **Reproducibility**: Consistent results across engines and time

## 📊 Key Metrics Targets
- **Sharpe Ratio**: > 1.0 (ideal), > 0.8 (good), > 0.5 (acceptable)
- **Win Rate**: > 55% (ideal), > 50% (acceptable)
- **Profit Factor**: > 2.0 (ideal), > 1.5 (good), > 1.2 (acceptable)
- **Max Drawdown**: < 10% (ideal), < 20% (acceptable)
- **Minimum Trades**: > 50 trades for statistical significance

---
*σ₁ foundation document informing all other memory files*
*[↗️σ₂] for architecture details | [↗️σ₃] for tech stack | [↗️σ₅] for current progress*