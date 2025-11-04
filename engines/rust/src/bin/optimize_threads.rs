// VERSAO STD::THREAD - Controle manual sem Rayon
extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, BacktestEngine};
use polars::prelude::*;
use std::time::Instant;
use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};
use std::sync::mpsc;
use std::thread;

fn main() {
    println!("\n{}", "=".repeat(80));
    println!("OTIMIZACAO STD::THREAD (SEM RAYON)");
    println!("{}\n", "=".repeat(80));

    let num_cpus = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(32);
    println!("Sistema: {} cores", num_cpus);
    println!("Usando std::thread manual (sem Rayon)\n");

    // Carregar dados
    println!("1) Carregando Golden Data...");
    let data_path = "C:/Users/AltF4/Documents/#__JUREAIS/data/WINFUT_M5_Golden_Data.parquet";
    let df = LazyFrame::scan_parquet(data_path, Default::default())
        .expect("Falha")
        .collect()
        .expect("Falha");

    println!("   Total: {} candles", df.height());

    let df_filtered = df.lazy()
        .filter(col("hour").gt_eq(lit(9)).and(col("hour").lt_eq(lit(18))))
        .collect()
        .expect("Falha");

    println!("   Filtrado: {} candles\n", df_filtered.height());

    // Converter candles
    println!("2) Convertendo...");
    let mut candles = Vec::new();
    let n = df_filtered.height();
    
    let open = df_filtered.column("open").unwrap().f32().unwrap();
    let high = df_filtered.column("high").unwrap().f32().unwrap();
    let low = df_filtered.column("low").unwrap().f32().unwrap();
    let close = df_filtered.column("close").unwrap().f32().unwrap();
    let volume = df_filtered.column("real_volume").unwrap().f32().unwrap();
    let atr = df_filtered.column("atr_14").unwrap().f32().unwrap();
    let hour = df_filtered.column("hour").unwrap().f32().unwrap();
    let minute = df_filtered.column("minute").unwrap().f32().unwrap();

    for i in 0..n {
        candles.push(Candle {
            open: open.get(i).unwrap(),
            high: high.get(i).unwrap(),
            low: low.get(i).unwrap(),
            close: close.get(i).unwrap(),
            volume: volume.get(i).unwrap(),
            atr: atr.get(i).unwrap(),
            hour: hour.get(i).unwrap() as i32,
            minute: minute.get(i).unwrap() as i32,
        });
    }
    println!("   OK: {} candles\n", candles.len());

    // Gerar grid (versão reduzida para teste)
    println!("3) Gerando grid...");
    let param_grid = generate_test_grid();  // Grid pequeno para testar
    let total = param_grid.len();
    println!("   Total: {} testes\n", total);

    println!("{}", "=".repeat(80));
    println!("PROCESSANDO COM {} THREADS MANUAIS", num_cpus);
    println!("{}\n", "=".repeat(80));

    // ENCONTRAR max_lookback para pre-computacao
    let max_lookback = param_grid.iter().map(|p| p.lookback_amplitude).max().unwrap_or(30);
    println!("[CACHE] Pre-computando rolling means com lookback={}\n", max_lookback);

    let inicio = Instant::now();
    let candles_arc = Arc::new(candles);
    
    // Dividir trabalho entre threads
    let chunk_size = (total + num_cpus - 1) / num_cpus;
    let (tx, rx) = mpsc::channel();
    let processed = Arc::new(AtomicUsize::new(0));
    
    // Thread de progresso
    let processed_clone = Arc::clone(&processed);
    let progress_handle = thread::spawn(move || {
        let start = Instant::now();
        loop {
            thread::sleep(std::time::Duration::from_secs(2));
            let current = processed_clone.load(Ordering::Relaxed);
            if current >= total {
                break;
            }
            let elapsed = start.elapsed().as_secs_f64();
            let velocity = if elapsed > 0.0 { current as f64 / elapsed } else { 0.0 };
            let pct = (current as f64 / total as f64) * 100.0;
            let barra_len = 50;
            let filled = ((pct / 100.0) * barra_len as f64) as usize;
            let barra: String = "█".repeat(filled) + &"░".repeat(barra_len - filled);
            let eta_min = if velocity > 0.0 {
                ((total - current) as f64 / velocity / 60.0) as usize
            } else {
                0
            };
            print!("\r[{}] {:.1}% | {}/{} | {:.0} t/s | ETA: {}min   ", 
                   barra, pct, current, total, velocity, eta_min);
            use std::io::Write;
            std::io::stdout().flush().unwrap();
        }
        println!();
    });
    
    // Criar worker threads
    let mut handles = vec![];
    
    for chunk in param_grid.chunks(chunk_size) {
        let tx = tx.clone();
        let chunk = chunk.to_vec();
        let candles = Arc::clone(&candles_arc);
        let processed = Arc::clone(&processed);
        
        let handle = thread::spawn(move || {
            for params in chunk {
                // USAR CACHE - sem recalcular rolling means
                let engine = BacktestEngine::new_with_cache(candles.clone(), max_lookback);
                let result = engine.run_strategy(&params);
                tx.send(result).unwrap();
                processed.fetch_add(1, Ordering::Relaxed);
            }
        });
        
        handles.push(handle);
    }
    
    drop(tx); // Importante!
    
    // Coletar resultados
    let mut results = vec![];
    for result in rx {
        results.push(result);
    }
    
    // Aguardar todas threads
    for handle in handles {
        handle.join().unwrap();
    }
    
    let _ = progress_handle.join();
    
    let tempo_total = inicio.elapsed().as_secs_f64();
    
    println!("\n{}", "=".repeat(80));
    println!("COMPLETO!");
    println!("{}\n", "=".repeat(80));
    println!("Tempo: {:.1}s ({:.2} min)", tempo_total, tempo_total / 60.0);
    println!("Testes: {}", results.len());
    println!("Velocidade: {:.0} t/s", results.len() as f64 / tempo_total);
    println!();
    
    // Salvar resultados
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = format!("results_threads_{}.csv", timestamp);
    let mut wtr = csv::Writer::from_path(&filename).expect("Falha ao criar CSV");
    
    wtr.write_record(&[
        "success", "total_return", "total_return_pct", "total_trades",
        "win_rate", "profit_factor", "sharpe_ratio", "max_drawdown_pct"
    ]).expect("Falha header");

    for result in &results {
        wtr.write_record(&[
            result.success.to_string(),
            result.metrics.total_return.to_string(),
            result.metrics.total_return_pct.to_string(),
            result.metrics.total_trades.to_string(),
            result.metrics.win_rate.to_string(),
            result.metrics.profit_factor.to_string(),
            result.metrics.sharpe_ratio.to_string(),
            result.metrics.max_drawdown_pct.to_string(),
        ]).expect("Falha");
    }
    wtr.flush().expect("Falha flush");
    
    println!("Arquivo: {}\n", filename);
}

fn generate_test_grid() -> Vec<BarraElefanteParams> {
    // Grid PEQUENO para teste comparativo (50k testes)
    let mut grid = Vec::new();
    let min_amp_vals = vec![1.5, 2.0, 2.5, 3.0];  // 4
    let min_vol_vals = vec![0.5, 1.0, 1.5, 2.0];  // 4
    let max_sombra_vals = vec![0.2, 0.3, 0.4, 0.5];  // 4
    let lookback_vals = vec![15, 20, 25];  // 3
    let minuto_inicio_vals = vec![0, 20];  // 2
    let horario_fim_vals = vec![11, 12, 13];  // 3
    let sl_vals = vec![1.0, 1.5, 2.0, 2.5];  // 4
    let tp_vals = vec![2.0, 3.0, 4.0];  // 3
    let trailing_vals = vec![false, true];  // 2
    // Total: 4×4×4×3×2×3×4×3×2 = 55,296 testes

    for &min_amp in &min_amp_vals {
        for &min_vol in &min_vol_vals {
            for &max_sombra in &max_sombra_vals {
                for &lookback in &lookback_vals {
                    for &min_inicio in &minuto_inicio_vals {
                        for &hr_fim in &horario_fim_vals {
                            for &sl in &sl_vals {
                                for &tp in &tp_vals {
                                    for &trailing in &trailing_vals {
                                        grid.push(BarraElefanteParams {
                                            min_amplitude_mult: min_amp,
                                            min_volume_mult: min_vol,
                                            max_sombra_pct: max_sombra,
                                            lookback_amplitude: lookback,
                                            horario_inicio: 9,
                                            minuto_inicio: min_inicio,
                                            horario_fim: hr_fim,
                                            minuto_fim: 30,
                                            horario_fechamento: 13,
                                            minuto_fechamento: 30,
                                            sl_atr_mult: sl,
                                            tp_atr_mult: tp,
                                            usar_trailing: trailing,
                                        });
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    grid
}

