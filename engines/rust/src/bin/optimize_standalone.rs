extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, Optimizer};
use polars::prelude::*;
use std::time::Instant;

fn main() {
    println!("\n{}", "=".repeat(80));
    println!("OTIMIZACAO RUST STANDALONE - 4.2M TESTES");
    println!("{}\n", "=".repeat(80));

    // Configurar Rayon para usar TODOS os cores
    let num_cpus = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(32);
    
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .stack_size(4 * 1024 * 1024)  // 4MB stack
        .build_global()
        .expect("Falha ao configurar Rayon");

    println!("Sistema: {} cores disponiveis", num_cpus);
    println!("Rayon: {} threads configuradas\n", rayon::current_num_threads());

    // 1. CARREGAR PARQUET
    println!("1) Carregando Golden Data...");
    let data_path = "C:/Users/AltF4/Documents/#__JUREAIS/data/WINFUT_M5_Golden_Data.parquet";
    
    let df = LazyFrame::scan_parquet(data_path, Default::default())
        .expect("Falha ao abrir parquet")
        .collect()
        .expect("Falha ao carregar dados");

    let total_candles = df.height();
    println!("   Total: {} candles", total_candles);

    // Filtrar apenas horario de trading (9:00-18:00)
    println!("   Filtrando horario de trading (9:00-18:00)...");
    let df_filtered = df
        .lazy()
        .filter(
            col("hour")
                .gt_eq(lit(9))
                .and(col("hour").lt_eq(lit(18))),
        )
        .collect()
        .expect("Falha ao filtrar");

    println!("   Apos filtro: {} candles\n", df_filtered.height());

    // 2. CONVERTER PARA STRUCT CANDLE
    println!("2) Convertendo para estrutura interna...");
    let open = df_filtered
        .column("open")
        .expect("Coluna open nao encontrada")
        .f32()
        .expect("open nao eh f32");
    let high = df_filtered
        .column("high")
        .expect("Coluna high nao encontrada")
        .f32()
        .expect("high nao eh f32");
    let low = df_filtered
        .column("low")
        .expect("Coluna low nao encontrada")
        .f32()
        .expect("low nao eh f32");
    let close = df_filtered
        .column("close")
        .expect("Coluna close nao encontrada")
        .f32()
        .expect("close nao eh f32");
    let volume = df_filtered
        .column("real_volume")
        .expect("Coluna real_volume nao encontrada")
        .f32()
        .expect("real_volume nao eh f32");
    let atr = df_filtered
        .column("atr_14")
        .expect("Coluna atr_14 nao encontrada")
        .f32()
        .expect("atr_14 nao eh f32");
    let hour = df_filtered
        .column("hour")
        .expect("Coluna hour nao encontrada")
        .f32()
        .expect("hour nao eh f32");
    let minute = df_filtered
        .column("minute")
        .expect("Coluna minute nao encontrada")
        .f32()
        .expect("minute nao eh f32");

    let n = df_filtered.height();
    let mut candles = Vec::with_capacity(n);

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
            is_warmup: false,
        });
    }

    println!("   {} candles convertidos\n", candles.len());

    // 3. GERAR GRID DE PARAMETROS (4.2M combinacoes)
    println!("3) Gerando grid de parametros...");
    let param_grid = generate_full_grid();
    println!("   Total: {} combinacoes\n", param_grid.len());

    // 4. OTIMIZAR COM RAYON MULTICORE + CACHE
    println!("{}", "=".repeat(80));
    println!("PROCESSANDO COM {} CORES + CACHE OTIMIZADO", num_cpus);
    println!("{}\n", "=".repeat(80));

    // Criar optimizer com CACHE (lookback maximo = 30)
    let max_lookback = 30;
    let optimizer = Optimizer::new_with_cache(candles, max_lookback);

    let inicio = Instant::now();
    let results = optimizer.optimize_parallel_with_stdout_progress(param_grid);
    let tempo_total = inicio.elapsed().as_secs_f64();

    println!("\n{}", "=".repeat(80));
    println!("COMPLETO!");
    println!("{}\n", "=".repeat(80));
    println!("Tempo total: {:.1} minutos ({:.2} horas)", tempo_total / 60.0, tempo_total / 3600.0);
    println!("Testes: {}", results.len());
    println!("Velocidade: {:.0} t/s\n", results.len() as f64 / tempo_total);

    // 5. SALVAR RESULTADOS EM CSV
    println!("5) Salvando resultados...");
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = format!("results_4_2M_rust_{}.csv", timestamp);

    let mut wtr = csv::Writer::from_path(&filename).expect("Falha ao criar CSV");

    // Header
    wtr.write_record(&[
        "success",
        "total_return",
        "total_return_pct",
        "total_trades",
        "winning_trades",
        "losing_trades",
        "win_rate",
        "avg_win",
        "avg_loss",
        "avg_trade",
        "profit_factor",
        "sharpe_ratio",
        "sortino_ratio",
        "max_drawdown",
        "max_drawdown_pct",
        "max_consecutive_wins",
        "max_consecutive_losses",
        "expectancy",
    ])
    .expect("Falha ao escrever header");

    // Data
    for result in &results {
        wtr.write_record(&[
            result.success.to_string(),
            result.metrics.total_return.to_string(),
            result.metrics.total_return_pct.to_string(),
            result.metrics.total_trades.to_string(),
            result.metrics.winning_trades.to_string(),
            result.metrics.losing_trades.to_string(),
            result.metrics.win_rate.to_string(),
            result.metrics.avg_win.to_string(),
            result.metrics.avg_loss.to_string(),
            result.metrics.avg_trade.to_string(),
            result.metrics.profit_factor.to_string(),
            result.metrics.sharpe_ratio.to_string(),
            result.metrics.sortino_ratio.to_string(),
            result.metrics.max_drawdown.to_string(),
            result.metrics.max_drawdown_pct.to_string(),
            result.metrics.max_consecutive_wins.to_string(),
            result.metrics.max_consecutive_losses.to_string(),
            result.metrics.expectancy.to_string(),
        ])
        .expect("Falha ao escrever linha");
    }

    wtr.flush().expect("Falha ao finalizar CSV");

    println!("   Salvo: {}\n", filename);

    // 6. ESTATISTICAS
    let validos: Vec<_> = results.iter().filter(|r| r.success).collect();
    println!("6) Estatisticas:");
    println!("   Testes validos: {} de {} ({:.1}%)", 
             validos.len(), 
             results.len(), 
             validos.len() as f64 / results.len() as f64 * 100.0);

    if !validos.is_empty() {
        let sharpe_medio: f32 = validos.iter().map(|r| r.metrics.sharpe_ratio).sum::<f32>()
            / validos.len() as f32;
        let sharpe_max = validos
            .iter()
            .map(|r| r.metrics.sharpe_ratio)
            .fold(f32::NEG_INFINITY, f32::max);

        println!("   Sharpe medio: {:.2}", sharpe_medio);
        println!("   Sharpe maximo: {:.2}", sharpe_max);

        let excelentes = validos.iter().filter(|r| r.metrics.sharpe_ratio > 1.0).count();
        println!("   Sharpe > 1.0: {} ({:.1}%)", 
                 excelentes,
                 excelentes as f64 / validos.len() as f64 * 100.0);
    }

    println!("\n{}", "=".repeat(80));
    println!("OTIMIZACAO COMPLETA!");
    println!("{}\n", "=".repeat(80));
}

fn generate_full_grid() -> Vec<BarraElefanteParams> {
    let mut grid = Vec::new();

    // Grid FULL CORRETO (4.233.600 combinacoes)
    let min_amp_vals = vec![1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0];  // 7
    let min_vol_vals = vec![0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0];  // 7
    let max_sombra_vals = vec![0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0];  // 8
    let lookback_vals = vec![5, 10, 15, 20, 25, 30];  // 6
    let minuto_inicio_vals = vec![0, 10, 20, 30, 40];  // 5
    let horario_fim_vals = vec![10, 11, 12, 13, 14];  // 5
    let sl_vals = vec![0.5, 1.0, 1.5, 2.0, 2.5, 3.0];  // 6
    let tp_vals = vec![1.0, 2.0, 3.0, 4.0, 5.0, 6.0];  // 6
    // usar_trailing removido do Rust (nao implementado ainda)
    // Total: 7 × 7 × 8 × 6 × 5 × 5 × 6 × 6 = 2.116.800 (sem trailing)

    for &min_amp in &min_amp_vals {
        for &min_vol in &min_vol_vals {
            for &max_sombra in &max_sombra_vals {
                for &lookback in &lookback_vals {
                    for &min_inicio in &minuto_inicio_vals {
                        for &hr_fim in &horario_fim_vals {
                            for &sl in &sl_vals {
                                for &tp in &tp_vals {
                                    grid.push(BarraElefanteParams {
                                        min_amplitude_mult: min_amp,
                                        min_volume_mult: min_vol,
                                        max_sombra_pct: max_sombra,
                                        lookback_amplitude: lookback,
                                        horario_inicio: 9,
                                        minuto_inicio: min_inicio,
                                        horario_fim: hr_fim,
                                        minuto_fim: 30,
                                        horario_fechamento: 13,  // 13h30 como pedido
                                        minuto_fechamento: 30,
                                        sl_atr_mult: sl,
                                        tp_atr_mult: tp,
                                        usar_trailing: false,  // Nao implementado ainda
                                    });
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

