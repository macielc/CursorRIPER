// OPTIMIZE SMART - Versao com CLI completo usando clap
// Compativel com mactester.py Python
extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, Optimizer};
use polars::prelude::*;
use std::time::Instant;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use clap::Parser;

/// MacTester Rust Engine - Otimizacao Massiva Paralela
#[derive(Parser, Debug)]
#[command(name = "optimize_smart")]
#[command(about = "Motor Rust de backtesting com CLI completo", long_about = None)]
struct Args {
    /// Estrategia a otimizar
    #[arg(short, long, default_value = "barra_elefante")]
    strategy: String,

    /// Numero de testes (combinacoes)
    #[arg(short = 'n', long, default_value = "1000")]
    tests: usize,

    /// Timeframe em minutos (5, 15, 30, 60)
    #[arg(short, long, default_value = "5")]
    timeframe: i32,

    /// Data inicial (YYYY-MM-DD) - SIMPLIFICADO: filtro manual apos carregar
    #[arg(long)]
    start_date: Option<String>,

    /// Data final (YYYY-MM-DD) - SIMPLIFICADO: filtro manual apos carregar
    #[arg(long)]
    end_date: Option<String>,

    /// Caminho dos dados (Parquet apenas)
    #[arg(short, long, default_value = "../../data/golden/WINFUT_M5_Golden_Data.parquet")]
    data: String,

    /// Arquivo de saida
    #[arg(short, long)]
    output: Option<String>,

    /// Numero de cores (default: todos)
    #[arg(short, long)]
    cores: Option<usize>,
}

fn main() {
    let args = Args::parse();

    println!("\n{}", "=".repeat(80));
    println!("MACTESTER RUST - OPTIMIZE SMART");
    println!("{}\n", "=".repeat(80));

    // Configurar Rayon
    let num_cpus = args.cores.unwrap_or_else(|| 
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(32)
    );
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .build_global()
        .expect("Falha ao configurar Rayon");

    println!("Sistema: {} cores disponiveis", 
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(32));
    println!("Rayon: {} threads\n", rayon::current_num_threads());
    println!("Estrategia: {}", args.strategy);
    println!("Testes: {}", args.tests);
    println!("Timeframe: M{}", args.timeframe);
    println!("Dataset: {}\n", args.data);

    // Carregar dados (PARQUET APENAS - mais rapido)
    println!("1) Carregando Parquet...");
    let start_load = Instant::now();
    
    let df = LazyFrame::scan_parquet(&args.data, Default::default())
        .expect("Falha ao abrir Parquet")
        .collect()
        .expect("Falha ao carregar Parquet");

    println!("   Total: {} candles ({:.2}s)", df.height(), start_load.elapsed().as_secs_f64());

    // Filtrar horario de pregao (9h-14h59)
    println!("   Filtrando horario 9h-15h...");
    let df_filtered = df.lazy()
        .filter(col("hour").gt_eq(lit(9)).and(col("hour").lt_eq(lit(14))))
        .collect()
        .expect("Falha filtro horario");

    println!("   Filtrado: {} candles\n", df_filtered.height());

    if df_filtered.height() == 0 {
        println!("ERRO: Nenhum candle apos filtros!");
        std::process::exit(1);
    }

    // TODO: Implementar filtro de data quando descobrir API correta do Polars 0.45
    if args.start_date.is_some() || args.end_date.is_some() {
        println!("   AVISO: Filtro de data ainda nao implementado (API Polars 0.45)");
        println!("   Use dataset pre-filtrado por enquanto.");
    }

    // Converter candles
    println!("2) Convertendo candles...");
    let mut candles = Vec::new();
    let n = df_filtered.height();
    
    // Converter todas colunas para f32 (lazy cast)
    let df_f32 = df_filtered.clone().lazy()
        .with_column(col("open").cast(DataType::Float32))
        .with_column(col("high").cast(DataType::Float32))
        .with_column(col("low").cast(DataType::Float32))
        .with_column(col("close").cast(DataType::Float32))
        .with_column(col("real_volume").cast(DataType::Float32))
        .with_column(col("atr_14").cast(DataType::Float32))
        .collect()
        .expect("Falha cast f32");
    
    let open = df_f32.column("open").unwrap().f32().unwrap();
    let high = df_f32.column("high").unwrap().f32().unwrap();
    let low = df_f32.column("low").unwrap().f32().unwrap();
    let close = df_f32.column("close").unwrap().f32().unwrap();
    let volume = df_f32.column("real_volume").unwrap().f32().unwrap();
    let atr = df_f32.column("atr_14").unwrap().f32().unwrap();
    
    // hour e minute podem ser i32/i64 no Parquet
    let hour = df_filtered.column("hour").unwrap();
    let minute = df_filtered.column("minute").unwrap();
    
    let hour_vals: Vec<i32> = if hour.dtype() == &DataType::Int32 {
        hour.i32().unwrap().into_iter().map(|v| v.unwrap_or(0)).collect()
    } else if hour.dtype() == &DataType::Int64 {
        hour.i64().unwrap().into_iter().map(|v| v.unwrap_or(0) as i32).collect()
    } else {
        hour.f32().unwrap().into_iter().map(|v| v.unwrap_or(0.0) as i32).collect()
    };
    
    let minute_vals: Vec<i32> = if minute.dtype() == &DataType::Int32 {
        minute.i32().unwrap().into_iter().map(|v| v.unwrap_or(0)).collect()
    } else if minute.dtype() == &DataType::Int64 {
        minute.i64().unwrap().into_iter().map(|v| v.unwrap_or(0) as i32).collect()
    } else {
        minute.f32().unwrap().into_iter().map(|v| v.unwrap_or(0.0) as i32).collect()
    };

    for i in 0..n {
        candles.push(Candle {
            open: open.get(i).unwrap(),
            high: high.get(i).unwrap(),
            low: low.get(i).unwrap(),
            close: close.get(i).unwrap(),
            volume: volume.get(i).unwrap(),
            atr: atr.get(i).unwrap(),
            hour: hour_vals[i],
            minute: minute_vals[i],
            is_warmup: false,
        });
    }
    println!("   OK: {} candles\n", candles.len());

    // Gerar grid limitado
    println!("3) Gerando grid de parametros...");
    let param_grid = generate_limited_grid(args.tests);
    let total = param_grid.len();
    println!("   Total: {} testes\n", total);

    // Criar arquivo CSV de saida
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = args.output.unwrap_or_else(|| 
        format!("results_rust_smart_{}.csv", timestamp)
    );
    let mut wtr = csv::Writer::from_path(&filename).expect("Falha ao criar CSV");
    
    // Header
    wtr.write_record(&[
        "success", "total_return", "total_return_pct", "total_trades",
        "win_rate", "profit_factor", "sharpe_ratio", "max_drawdown_pct"
    ]).expect("Falha header");

    // Processar em batches
    let batch_size = 5000.min(total);
    let num_batches = (total + batch_size - 1) / batch_size;
    
    println!("{}", "=".repeat(80));
    println!("PROCESSANDO EM {} BATCHES", num_batches);
    println!("{}\n", "=".repeat(80));

    let max_lookback = param_grid.iter().map(|p| p.lookback_amplitude).max().unwrap_or(30);
    println!("[CACHE] Pre-computando rolling means (lookback={})\n", max_lookback);

    let inicio_total = Instant::now();
    let processed = Arc::new(AtomicUsize::new(0));

    for batch_idx in 0..num_batches {
        let start_idx = batch_idx * batch_size;
        let end_idx = (start_idx + batch_size).min(total);
        let batch = &param_grid[start_idx..end_idx];
        
        let batch_start = Instant::now();
        
        // Processar batch
        let optimizer = Optimizer::new_with_cache(candles.to_vec(), max_lookback);
        let results = optimizer.optimize_parallel_with_stdout_progress(batch.to_vec());
        
        // Salvar
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
    println!("Tempo: {:.1} s ({:.2} min)", tempo_total, tempo_total / 60.0);
    println!("Velocidade media: {:.0} t/s", total as f64 / tempo_total);
    println!("Arquivo: {}", filename);
    println!("{}", "=".repeat(80));
}

// Gerar grid limitado (parecido com Python)
fn generate_limited_grid(max_tests: usize) -> Vec<BarraElefanteParams> {
    let mut grid = Vec::new();
    
    // Ranges reduzidos para atingir ~1000 testes
    let min_amplitude_mults = vec![1.5, 2.0, 2.5];
    let min_volume_mults = vec![1.3, 1.5, 2.0];
    let max_sombra_pcts = vec![0.3, 0.4, 0.5];
    let lookback_amplitudes = vec![10, 15, 20];
    let horario_inicios = vec![9, 10];
    let horario_fins = vec![12, 13];
    let sl_atr_mults = vec![1.5, 2.0];
    let tp_atr_mults = vec![2.0, 3.0];
    let usar_trailings = vec![true, false];

    for &min_amplitude_mult in &min_amplitude_mults {
        for &min_volume_mult in &min_volume_mults {
            for &max_sombra_pct in &max_sombra_pcts {
                for &lookback_amplitude in &lookback_amplitudes {
                    for &horario_inicio in &horario_inicios {
                        for &horario_fim in &horario_fins {
                            for &sl_atr_mult in &sl_atr_mults {
                                for &tp_atr_mult in &tp_atr_mults {
                                    for &usar_trailing in &usar_trailings {
                                        if grid.len() >= max_tests {
                                            return grid;
                                        }
                                        
                                        grid.push(BarraElefanteParams {
                                            min_amplitude_mult,
                                            min_volume_mult,
                                            max_sombra_pct,
                                            lookback_amplitude,
                                            horario_inicio,
                                            minuto_inicio: 0,  // Fixo
                                            horario_fim,
                                            minuto_fim: 0,  // Fixo
                                            horario_fechamento: 14,  // Fixo (14h45)
                                            minuto_fechamento: 45,  // Fixo
                                            sl_atr_mult,
                                            tp_atr_mult,
                                            usar_trailing,
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
