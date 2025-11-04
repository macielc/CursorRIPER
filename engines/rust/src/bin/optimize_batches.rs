// VERSAO BATCHES - Processa em lotes para evitar degradacao
extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, Optimizer};
use polars::prelude::*;
use std::time::Instant;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

fn main() {
    println!("\n{}", "=".repeat(80));
    println!("OTIMIZACAO BATCHES - SEM DEGRADACAO");
    println!("{}\n", "=".repeat(80));

    // Configurar Rayon
    let num_cpus = std::thread::available_parallelism().map(|n| n.get()).unwrap_or(32);
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .build_global()
        .expect("Falha ao configurar Rayon");

    println!("Sistema: {} cores", num_cpus);
    println!("Rayon: {} threads\n", rayon::current_num_threads());

    // Carregar dados
    println!("1) Carregando Golden Data...");
    let data_path = "C:/Users/AltF4/Documents/#__JUREAIS/data/WINFUT_M5_Golden_Data.parquet";
    let df = LazyFrame::scan_parquet(data_path, Default::default())
        .expect("Falha")
        .collect()
        .expect("Falha ao carregar");

    println!("   Total: {} candles", df.height());

    // Filtrar horario
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

    // Gerar grid
    println!("3) Gerando grid...");
    let param_grid = generate_full_grid();  // GRID COMPLETO 4.2M
    let total = param_grid.len();
    println!("   Total: {} testes\n", total);

    // Criar arquivo CSV
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = format!("results_batches_{}.csv", timestamp);
    let mut wtr = csv::Writer::from_path(&filename).expect("Falha ao criar CSV");
    
    // Header
    wtr.write_record(&[
        "success", "total_return", "total_return_pct", "total_trades",
        "win_rate", "profit_factor", "sharpe_ratio", "max_drawdown_pct"
    ]).expect("Falha header");

    // Processar em BATCHES de 20k (sweet spot - nao degrada)
    let batch_size = 20000;
    let num_batches = (total + batch_size - 1) / batch_size;
    
    println!("{}", "=".repeat(80));
    println!("PROCESSANDO EM {} BATCHES DE {}k TESTES", num_batches, batch_size/1000);
    println!("{}\n", "=".repeat(80));

    // ENCONTRAR max_lookback para pre-computacao
    let max_lookback = param_grid.iter().map(|p| p.lookback_amplitude).max().unwrap_or(30);
    println!("[CACHE] Pre-computando rolling means com lookback={}\n", max_lookback);

    let inicio_total = Instant::now();
    let processed = Arc::new(AtomicUsize::new(0));

    for batch_idx in 0..num_batches {
        let start_idx = batch_idx * batch_size;
        let end_idx = (start_idx + batch_size).min(total);
        let batch = &param_grid[start_idx..end_idx];
        
        let batch_start = Instant::now();
        
        // Processar batch COM CACHE (sem recalcular rolling means)
        let optimizer = Optimizer::new_with_cache(candles.to_vec(), max_lookback);
        let results = optimizer.optimize_parallel_with_stdout_progress(batch.to_vec());
        
        // Salvar imediatamente
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
            ]).expect("Falha ao escrever");
        }
        wtr.flush().expect("Falha flush");
        
        let batch_elapsed = batch_start.elapsed().as_secs_f64();
        let batch_vel = results.len() as f64 / batch_elapsed;
        
        processed.fetch_add(results.len(), Ordering::Relaxed);
        let proc = processed.load(Ordering::Relaxed);
        let pct = (proc as f64 / total as f64) * 100.0;
        
        let elapsed_total = inicio_total.elapsed().as_secs_f64();
        let vel_media = proc as f64 / elapsed_total;
        let eta_seg = ((total - proc) as f64 / vel_media).round() as usize;
        let eta_min = eta_seg / 60;
        
        println!("\n[BATCH {}/{}] {:.1}% | {}/{} | Vel: {:.0} t/s | ETA: {}min\n", 
                 batch_idx + 1, num_batches, pct, proc, total, vel_media, eta_min);
    }

    let tempo_total = inicio_total.elapsed().as_secs_f64();
    
    println!("\n{}", "=".repeat(80));
    println!("COMPLETO!");
    println!("{}\n", "=".repeat(80));
    println!("Tempo: {:.1} min", tempo_total / 60.0);
    println!("Velocidade media: {:.0} t/s", total as f64 / tempo_total);
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

fn generate_full_grid() -> Vec<BarraElefanteParams> {
    let mut grid = Vec::new();
    let min_amp_vals = vec![1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0];
    let min_vol_vals = vec![0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0];
    let max_sombra_vals = vec![0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0];
    let lookback_vals = vec![5, 10, 15, 20, 25, 30];
    let minuto_inicio_vals = vec![0, 10, 20, 30, 40];
    let horario_fim_vals = vec![10, 11, 12, 13, 14];
    let sl_vals = vec![0.5, 1.0, 1.5, 2.0, 2.5, 3.0];
    let tp_vals = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0];
    let trailing_vals = vec![false, true];  // 2 valores

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

