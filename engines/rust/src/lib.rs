mod backtest_engine;
mod metrics;
mod optimizer;
mod strategy;
mod types;

// Exportar para uso em binarios
pub use backtest_engine::BacktestEngine;
pub use optimizer::{generate_param_grid, Optimizer};
pub use types::{BarraElefanteParams, BacktestResult, Candle, Metrics};

#[cfg(feature = "python")]
use numpy::{PyArray1, PyReadonlyArray1};
#[cfg(feature = "python")]
use pyo3::prelude::*;
#[cfg(feature = "python")]
use pyo3::types::PyDict;

#[cfg(feature = "python")]
#[pyfunction]
fn run_backtest_rust(
    py: Python,
    open: PyReadonlyArray1<f32>,
    high: PyReadonlyArray1<f32>,
    low: PyReadonlyArray1<f32>,
    close: PyReadonlyArray1<f32>,
    volume: PyReadonlyArray1<f32>,
    atr: PyReadonlyArray1<f32>,
    hour: PyReadonlyArray1<i32>,
    minute: PyReadonlyArray1<i32>,
    params_dict: &Bound<'_, PyDict>,
) -> PyResult<Py<PyDict>> {
    // Converter arrays NumPy para Vec
    let open_slice = open.as_slice()?;
    let high_slice = high.as_slice()?;
    let low_slice = low.as_slice()?;
    let close_slice = close.as_slice()?;
    let volume_slice = volume.as_slice()?;
    let atr_slice = atr.as_slice()?;
    let hour_slice = hour.as_slice()?;
    let minute_slice = minute.as_slice()?;

    let n = open_slice.len();

    // Criar candles
    let mut candles = Vec::with_capacity(n);
    for i in 0..n {
        candles.push(Candle {
            open: open_slice[i],
            high: high_slice[i],
            low: low_slice[i],
            close: close_slice[i],
            volume: volume_slice[i],
            atr: atr_slice[i],
            hour: hour_slice[i],
            minute: minute_slice[i],
        });
    }

    // Extrair params do dict
    let params = BarraElefanteParams {
        min_amplitude_mult: params_dict
            .get_item("min_amplitude_mult")?
            .unwrap()
            .extract()?,
        min_volume_mult: params_dict
            .get_item("min_volume_mult")?
            .unwrap()
            .extract()?,
        max_sombra_pct: params_dict
            .get_item("max_sombra_pct")?
            .unwrap()
            .extract()?,
        lookback_amplitude: params_dict
            .get_item("lookback_amplitude")?
            .unwrap()
            .extract()?,
        horario_inicio: params_dict
            .get_item("horario_inicio")?
            .unwrap()
            .extract()?,
        minuto_inicio: params_dict
            .get_item("minuto_inicio")?
            .unwrap()
            .extract()?,
        horario_fim: params_dict.get_item("horario_fim")?.unwrap().extract()?,
        minuto_fim: params_dict.get_item("minuto_fim")?.unwrap().extract()?,
        horario_fechamento: params_dict
            .get_item("horario_fechamento")?
            .unwrap()
            .extract()?,
        minuto_fechamento: params_dict
            .get_item("minuto_fechamento")?
            .unwrap()
            .extract()?,
        sl_atr_mult: params_dict.get_item("sl_atr_mult")?.unwrap().extract()?,
        tp_atr_mult: params_dict.get_item("tp_atr_mult")?.unwrap().extract()?,
        usar_trailing: params_dict
            .get_item("usar_trailing")
            .ok()
            .flatten()
            .and_then(|v| v.extract().ok())
            .unwrap_or(false),
    };

    // Executar backtest
    use std::sync::Arc;
    let engine = BacktestEngine::new(Arc::new(candles));
    let result = engine.run_strategy(&params);

    // Converter resultado para dict Python
    let result_dict = PyDict::new(py);
    result_dict.set_item("success", result.success)?;
    result_dict.set_item("total_return", result.metrics.total_return)?;
    result_dict.set_item("total_return_pct", result.metrics.total_return_pct)?;
    result_dict.set_item("total_trades", result.metrics.total_trades)?;
    result_dict.set_item("winning_trades", result.metrics.winning_trades)?;
    result_dict.set_item("losing_trades", result.metrics.losing_trades)?;
    result_dict.set_item("win_rate", result.metrics.win_rate)?;
    result_dict.set_item("avg_win", result.metrics.avg_win)?;
    result_dict.set_item("avg_loss", result.metrics.avg_loss)?;
    result_dict.set_item("avg_trade", result.metrics.avg_trade)?;
    result_dict.set_item("profit_factor", result.metrics.profit_factor)?;
    result_dict.set_item("sharpe_ratio", result.metrics.sharpe_ratio)?;
    result_dict.set_item("sortino_ratio", result.metrics.sortino_ratio)?;
    result_dict.set_item("max_drawdown", result.metrics.max_drawdown)?;
    result_dict.set_item("max_drawdown_pct", result.metrics.max_drawdown_pct)?;
    result_dict.set_item("max_consecutive_wins", result.metrics.max_consecutive_wins)?;
    result_dict.set_item("max_consecutive_losses", result.metrics.max_consecutive_losses)?;
    result_dict.set_item("expectancy", result.metrics.expectancy)?;

    if let Some(err) = result.error_msg {
        result_dict.set_item("error", err)?;
    }

    Ok(result_dict.into())
}

#[cfg(feature = "python")]
#[pyfunction]
fn optimize_rust(
    py: Python,
    open: PyReadonlyArray1<f32>,
    high: PyReadonlyArray1<f32>,
    low: PyReadonlyArray1<f32>,
    close: PyReadonlyArray1<f32>,
    volume: PyReadonlyArray1<f32>,
    atr: PyReadonlyArray1<f32>,
    hour: PyReadonlyArray1<i32>,
    minute: PyReadonlyArray1<i32>,
    param_ranges: &Bound<'_, PyDict>,
) -> PyResult<Vec<Py<PyDict>>> {
    // Converter arrays NumPy para Vec
    let open_slice = open.as_slice()?;
    let high_slice = high.as_slice()?;
    let low_slice = low.as_slice()?;
    let close_slice = close.as_slice()?;
    let volume_slice = volume.as_slice()?;
    let atr_slice = atr.as_slice()?;
    let hour_slice = hour.as_slice()?;
    let minute_slice = minute.as_slice()?;

    let n = open_slice.len();

    // Criar candles
    let mut candles = Vec::with_capacity(n);
    for i in 0..n {
        candles.push(Candle {
            open: open_slice[i],
            high: high_slice[i],
            low: low_slice[i],
            close: close_slice[i],
            volume: volume_slice[i],
            atr: atr_slice[i],
            hour: hour_slice[i],
            minute: minute_slice[i],
        });
    }

    // Extrair ranges de parametros
    let min_amp_range: (f32, f32, f32) = param_ranges
        .get_item("min_amplitude_mult")?
        .unwrap()
        .extract()?;
    let min_vol_range: (f32, f32, f32) = param_ranges
        .get_item("min_volume_mult")?
        .unwrap()
        .extract()?;
    let max_sombra_range: (f32, f32, f32) = param_ranges
        .get_item("max_sombra_pct")?
        .unwrap()
        .extract()?;
    let sl_range: (f32, f32, f32) = param_ranges
        .get_item("sl_atr_mult")?
        .unwrap()
        .extract()?;
    let tp_range: (f32, f32, f32) = param_ranges
        .get_item("tp_atr_mult")?
        .unwrap()
        .extract()?;

    // Gerar grid de parametros
    let param_grid = generate_param_grid(
        min_amp_range,
        min_vol_range,
        max_sombra_range,
        sl_range,
        tp_range,
    );

    // CONFIGURAR RAYON APENAS UMA VEZ (build_global falha se ja configurado)
    use std::sync::Once;
    static RAYON_INIT: Once = Once::new();
    
    let num_cpus = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(32);
    
    RAYON_INIT.call_once(|| {
        match rayon::ThreadPoolBuilder::new()
            .num_threads(num_cpus)
            .stack_size(2 * 1024 * 1024)
            .build_global() 
        {
            Ok(_) => {
                println!("[RUST] Rayon configurado com {} threads", num_cpus);
                println!("[RUST] Rayon threads ativos: {}", rayon::current_num_threads());
            }
            Err(e) => {
                println!("[RUST ERRO] Falha ao configurar Rayon: {:?}", e);
                println!("[RUST] Usando configuracao default (provavelmente JA configurado)");
            }
        }
    });

    // LIBERAR GIL DO PYTHON DURANTE PROCESSAMENTO RUST
    // Isso permite que todas as threads Rust trabalhem em paralelo
    let results = py.allow_threads(|| {
        let optimizer = Optimizer::new(candles);
        optimizer.optimize_parallel_with_stdout_progress(param_grid)
    });

    // Converter resultados para lista de dicts Python
    let mut py_results = Vec::new();
    for result in results {
        let result_dict = PyDict::new(py);
        result_dict.set_item("success", result.success)?;
        result_dict.set_item("total_return", result.metrics.total_return)?;
        result_dict.set_item("total_return_pct", result.metrics.total_return_pct)?;
        result_dict.set_item("total_trades", result.metrics.total_trades)?;
        result_dict.set_item("win_rate", result.metrics.win_rate)?;
        result_dict.set_item("profit_factor", result.metrics.profit_factor)?;
        result_dict.set_item("sharpe_ratio", result.metrics.sharpe_ratio)?;
        result_dict.set_item("max_drawdown_pct", result.metrics.max_drawdown_pct)?;

        py_results.push(result_dict.into());
    }

    Ok(py_results)
}

#[cfg(feature = "python")]
#[pyfunction]
fn optimize_rust_with_progress(
    py: Python,
    open: PyReadonlyArray1<f32>,
    high: PyReadonlyArray1<f32>,
    low: PyReadonlyArray1<f32>,
    close: PyReadonlyArray1<f32>,
    volume: PyReadonlyArray1<f32>,
    atr: PyReadonlyArray1<f32>,
    hour: PyReadonlyArray1<i32>,
    minute: PyReadonlyArray1<i32>,
    param_ranges: &Bound<'_, PyDict>,
    progress_callback: PyObject,
) -> PyResult<Vec<Py<PyDict>>> {
    // Converter arrays NumPy para Vec
    let open_slice = open.as_slice()?;
    let high_slice = high.as_slice()?;
    let low_slice = low.as_slice()?;
    let close_slice = close.as_slice()?;
    let volume_slice = volume.as_slice()?;
    let atr_slice = atr.as_slice()?;
    let hour_slice = hour.as_slice()?;
    let minute_slice = minute.as_slice()?;

    let n = open_slice.len();

    // Criar candles
    let mut candles = Vec::with_capacity(n);
    for i in 0..n {
        candles.push(Candle {
            open: open_slice[i],
            high: high_slice[i],
            low: low_slice[i],
            close: close_slice[i],
            volume: volume_slice[i],
            atr: atr_slice[i],
            hour: hour_slice[i],
            minute: minute_slice[i],
        });
    }

    // Extrair ranges de parametros
    let min_amp_range: (f32, f32, f32) = param_ranges
        .get_item("min_amplitude_mult")?
        .unwrap()
        .extract()?;
    let min_vol_range: (f32, f32, f32) = param_ranges
        .get_item("min_volume_mult")?
        .unwrap()
        .extract()?;
    let max_sombra_range: (f32, f32, f32) = param_ranges
        .get_item("max_sombra_pct")?
        .unwrap()
        .extract()?;
    let sl_range: (f32, f32, f32) = param_ranges
        .get_item("sl_atr_mult")?
        .unwrap()
        .extract()?;
    let tp_range: (f32, f32, f32) = param_ranges
        .get_item("tp_atr_mult")?
        .unwrap()
        .extract()?;

    // Gerar grid de parametros
    let param_grid = generate_param_grid(
        min_amp_range,
        min_vol_range,
        max_sombra_range,
        sl_range,
        tp_range,
    );

    let _total = param_grid.len();

    // Criar callback que chama Python (requer GIL)
    let callback = Box::new(move |current: usize, total: usize| {
        Python::with_gil(|py| {
            let _ = progress_callback.call1(py, (current, total));
        });
    });

    // LIBERAR GIL durante processamento Rust
    // Nota: callbacks para Python vao re-adquirir GIL temporariamente
    let results = py.allow_threads(|| {
        let optimizer = Optimizer::new(candles);
        optimizer.optimize_parallel(param_grid, Some(callback))
    });

    // Converter resultados para lista de dicts Python
    let mut py_results = Vec::new();
    for result in results {
        let result_dict = PyDict::new(py);
        result_dict.set_item("success", result.success)?;
        result_dict.set_item("total_return", result.metrics.total_return)?;
        result_dict.set_item("total_return_pct", result.metrics.total_return_pct)?;
        result_dict.set_item("total_trades", result.metrics.total_trades)?;
        result_dict.set_item("win_rate", result.metrics.win_rate)?;
        result_dict.set_item("profit_factor", result.metrics.profit_factor)?;
        result_dict.set_item("sharpe_ratio", result.metrics.sharpe_ratio)?;
        result_dict.set_item("max_drawdown_pct", result.metrics.max_drawdown_pct)?;

        py_results.push(result_dict.into());
    }

    Ok(py_results)
}

#[cfg(feature = "python")]
#[pymodule]
fn mactester_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(run_backtest_rust, m)?)?;
    m.add_function(wrap_pyfunction!(optimize_rust, m)?)?;
    m.add_function(wrap_pyfunction!(optimize_rust_with_progress, m)?)?;
    Ok(())
}
