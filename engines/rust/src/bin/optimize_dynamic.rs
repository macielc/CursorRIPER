// OPTIMIZE DYNAMIC - Sistema 100% dinâmico com YAML
// Cada estratégia define seus próprios parâmetros em YAML
// SEM RECOMPILAÇÃO necessária!

extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, Optimizer, TradeType, ExitReason};
use polars::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::time::Instant;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use clap::Parser;

/// MacTester Rust Engine - 100% Dinâmico com YAML
#[derive(Parser, Debug)]
#[command(name = "optimize_dynamic")]
#[command(about = "Motor Rust com configuração YAML dinâmica", long_about = None)]
struct Args {
    /// Caminho do arquivo YAML de configuração da estratégia
    #[arg(short, long)]
    config: String,

    /// Caminho dos dados (Parquet)
    #[arg(short, long, default_value = "../../data/golden/WINFUT_M5_Golden_Data.parquet")]
    data: String,

    /// Arquivo de saída
    #[arg(short, long)]
    output: Option<String>,

    /// Número de cores (default: todos)
    #[arg(long)]
    cores: Option<usize>,

    /// Limite de testes (0 = todos)
    #[arg(short, long)]
    tests: Option<usize>,
}

// ============================================================================
// ESTRUTURAS YAML DINÂMICAS
// ============================================================================

#[derive(Debug, Deserialize, Serialize)]
struct StrategyConfig {
    strategy: StrategyInfo,
    param_grid: HashMap<String, ParamDefinition>,
    execution: Option<ExecutionConfig>,
    metadata: Option<HashMap<String, serde_yaml::Value>>,
}

#[derive(Debug, Deserialize, Serialize)]
struct StrategyInfo {
    name: String,
    description: Option<String>,
    version: Option<String>,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(tag = "type")]
enum ParamDefinition {
    #[serde(rename = "float")]
    Float {
        values: Vec<f32>,
        description: Option<String>,
        fixed: Option<bool>,
    },
    #[serde(rename = "integer")]
    Integer {
        values: Vec<i32>,
        description: Option<String>,
        fixed: Option<bool>,
    },
    #[serde(rename = "boolean")]
    Boolean {
        values: Vec<bool>,
        description: Option<String>,
        fixed: Option<bool>,
    },
}

#[derive(Debug, Deserialize, Serialize)]
struct ExecutionConfig {
    max_tests: Option<usize>,
    randomize: Option<bool>,
    batch_size: Option<usize>,
}

// ============================================================================
// VALORES DINÂMICOS
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(untagged)]
enum ParamValue {
    Float(f32),
    Integer(i32),
    Boolean(bool),
}

impl ParamValue {
    fn as_f32(&self) -> f32 {
        match self {
            ParamValue::Float(v) => *v,
            ParamValue::Integer(v) => *v as f32,
            ParamValue::Boolean(v) => if *v { 1.0 } else { 0.0 },
        }
    }

    fn as_i32(&self) -> i32 {
        match self {
            ParamValue::Float(v) => *v as i32,
            ParamValue::Integer(v) => *v,
            ParamValue::Boolean(v) => if *v { 1 } else { 0 },
        }
    }

    fn as_bool(&self) -> bool {
        match self {
            ParamValue::Float(v) => *v != 0.0,
            ParamValue::Integer(v) => *v != 0,
            ParamValue::Boolean(v) => *v,
        }
    }
}

type ParamSet = HashMap<String, ParamValue>;

// ============================================================================
// GERADOR DE GRID DINÂMICO
// ============================================================================

fn generate_dynamic_grid(
    config: &StrategyConfig,
    max_tests: Option<usize>
) -> Vec<ParamSet> {
    // Extrair todas as possibilidades de cada parâmetro
    let mut param_names: Vec<String> = Vec::new();
    let mut param_values: Vec<Vec<ParamValue>> = Vec::new();

    for (name, definition) in &config.param_grid {
        param_names.push(name.clone());

        let values = match definition {
            ParamDefinition::Float { values, .. } => {
                values.iter().map(|v| ParamValue::Float(*v)).collect()
            },
            ParamDefinition::Integer { values, .. } => {
                values.iter().map(|v| ParamValue::Integer(*v)).collect()
            },
            ParamDefinition::Boolean { values, .. } => {
                values.iter().map(|v| ParamValue::Boolean(*v)).collect()
            },
        };

        param_values.push(values);
    }

    // Gerar produto cartesiano (todas as combinações)
    let mut grid = Vec::new();
    generate_combinations_recursive(
        &param_names,
        &param_values,
        &mut HashMap::new(),
        0,
        &mut grid,
        max_tests
    );

    grid
}

fn generate_combinations_recursive(
    param_names: &[String],
    param_values: &[Vec<ParamValue>],
    current: &mut ParamSet,
    index: usize,
    grid: &mut Vec<ParamSet>,
    max_tests: Option<usize>
) {
    // Verificar limite de testes
    if let Some(max) = max_tests {
        if grid.len() >= max {
            return;
        }
    }

    if index == param_names.len() {
        // Combinação completa, adicionar ao grid
        grid.push(current.clone());
        return;
    }

    // Iterar sobre todos os valores do parâmetro atual
    for value in &param_values[index] {
        current.insert(param_names[index].clone(), value.clone());
        generate_combinations_recursive(
            param_names,
            param_values,
            current,
            index + 1,
            grid,
            max_tests
        );
    }
}

// ============================================================================
// CONVERTER PARAMSET → BARRAEELEFANTEPARAMS
// ============================================================================

fn paramset_to_barra_elefante(params: &ParamSet) -> BarraElefanteParams {
    BarraElefanteParams {
        min_amplitude_mult: params.get("min_amplitude_mult").unwrap().as_f32(),
        min_volume_mult: params.get("min_volume_mult").unwrap().as_f32(),
        max_sombra_pct: params.get("max_sombra_pct").unwrap().as_f32(),
        lookback_amplitude: params.get("lookback_amplitude").unwrap().as_i32() as usize,
        horario_inicio: params.get("horario_inicio").unwrap().as_i32(),
        minuto_inicio: params.get("minuto_inicio").unwrap().as_i32(),
        horario_fim: params.get("horario_fim").unwrap().as_i32(),
        minuto_fim: params.get("minuto_fim").unwrap().as_i32(),
        horario_fechamento: params.get("horario_fechamento").unwrap().as_i32(),
        minuto_fechamento: params.get("minuto_fechamento").unwrap().as_i32(),
        sl_atr_mult: params.get("sl_atr_mult").unwrap().as_f32(),
        tp_atr_mult: params.get("tp_atr_mult").unwrap().as_f32(),
        usar_trailing: params.get("usar_trailing").unwrap().as_bool(),
    }
}

// ============================================================================
// MAIN
// ============================================================================

fn main() {
    let args = Args::parse();

    println!("\n{}", "=".repeat(80));
    println!("MACTESTER RUST - OPTIMIZE DYNAMIC (100% YAML)");
    println!("{}\n", "=".repeat(80));

    // Carregar configuração YAML
    println!("1) Carregando configuração YAML...");
    println!("   Arquivo: {}", args.config);
    
    let yaml_content = fs::read_to_string(&args.config)
        .expect("Falha ao ler arquivo YAML");
    
    let config: StrategyConfig = serde_yaml::from_str(&yaml_content)
        .expect("Falha ao parsear YAML");

    println!("   Estratégia: {}", config.strategy.name);
    if let Some(desc) = &config.strategy.description {
        println!("   Descrição: {}", desc);
    }
    println!("   Parâmetros definidos: {}", config.param_grid.len());
    println!();

    // Exibir parâmetros
    println!("2) Parâmetros da estratégia:");
    for (name, def) in &config.param_grid {
        let count = match def {
            ParamDefinition::Float { values, .. } => values.len(),
            ParamDefinition::Integer { values, .. } => values.len(),
            ParamDefinition::Boolean { values, .. } => values.len(),
        };
        println!("   - {}: {} valores", name, count);
    }
    println!();

    // Configurar Rayon
    let num_cpus = args.cores.unwrap_or_else(|| 
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(32)
    );
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .build_global()
        .expect("Falha ao configurar Rayon");

    println!("3) Rayon configurado: {} threads\n", num_cpus);

    // Gerar grid dinâmico
    println!("4) Gerando grid de parâmetros...");
    let max_tests = args.tests.or(config.execution.as_ref().and_then(|e| e.max_tests));
    let param_grid = generate_dynamic_grid(&config, max_tests);
    let total = param_grid.len();
    
    println!("   Total de combinações: {}", total);
    if let Some(max) = max_tests {
        if total > max {
            println!("   Limitado a: {} testes", max);
        }
    }
    println!();

    // Carregar dados
    println!("5) Carregando dados Parquet...");
    let start_load = Instant::now();
    
    let df = LazyFrame::scan_parquet(&args.data, Default::default())
        .expect("Falha ao abrir Parquet")
        .collect()
        .expect("Falha ao carregar Parquet");

    println!("   Total: {} candles ({:.2}s)", df.height(), start_load.elapsed().as_secs_f64());

    // Filtrar horário de pregão (9h-15h, IGUAL AO PYTHON!)
    let df_filtered = df.lazy()
        .filter(col("hour").gt_eq(lit(9)).and(col("hour").lt_eq(lit(15))))
        .collect()
        .expect("Falha filtro horário");

    println!("   Filtrado (9h-15h): {} candles\n", df_filtered.height());

    if df_filtered.height() == 0 {
        println!("ERRO: Nenhum candle após filtros!");
        std::process::exit(1);
    }

    // Converter candles
    println!("6) Convertendo candles...");
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

    // Ler coluna is_warmup se existir (para suporte a datasets com warmup)
    let is_warmup_vals: Vec<bool> = if let Ok(is_warmup_col) = df_filtered.column("is_warmup") {
        is_warmup_col.bool().unwrap().into_iter().map(|v| v.unwrap_or(false)).collect()
    } else {
        vec![false; df_f32.height()]
    };

    let mut candles = Vec::new();
    let n = df_f32.height();
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
            is_warmup: is_warmup_vals[i],
        });
    }
    println!("   OK: {} candles\n", candles.len());

    // Converter ParamSet → BarraElefanteParams
    println!("7) Convertendo configuração para parâmetros da estratégia...");
    let barra_params: Vec<BarraElefanteParams> = param_grid.iter()
        .map(|ps| paramset_to_barra_elefante(ps))
        .collect();
    println!("   OK: {} configurações\n", barra_params.len());

    // Criar arquivo CSV de saída
    let timestamp = chrono::Local::now().format("%Y%m%d_%H%M%S");
    let filename = args.output.unwrap_or_else(|| 
        format!("results_{}_{}.csv", config.strategy.name, timestamp)
    );
    let mut wtr = csv::Writer::from_path(&filename).expect("Falha ao criar CSV");
    
    // Header (parâmetros + métricas)
    wtr.write_record(&[
        "min_amplitude_mult", "min_volume_mult", "max_sombra_pct", "lookback_amplitude",
        "horario_inicio", "minuto_inicio", "horario_fim", "minuto_fim",
        "horario_fechamento", "minuto_fechamento", "sl_atr_mult", "tp_atr_mult", "usar_trailing",
        "success", "total_return", "total_return_pct", "total_trades",
        "win_rate", "profit_factor", "sharpe_ratio", "max_drawdown_pct"
    ]).expect("Falha header");

    // Processar em batches
    let batch_size = config.execution.as_ref()
        .and_then(|e| e.batch_size)
        .unwrap_or(5000)
        .min(total);
    let num_batches = (total + batch_size - 1) / batch_size;
    
    println!("{}", "=".repeat(80));
    println!("PROCESSANDO EM {} BATCHES", num_batches);
    println!("{}\n", "=".repeat(80));

    let max_lookback = barra_params.iter().map(|p| p.lookback_amplitude).max().unwrap_or(30);
    println!("[CACHE] Pre-computando rolling means (lookback={})\n", max_lookback);

    let inicio_total = Instant::now();
    let processed = Arc::new(AtomicUsize::new(0));

    for batch_idx in 0..num_batches {
        let start_idx = batch_idx * batch_size;
        let end_idx = (start_idx + batch_size).min(total);
        let batch = &barra_params[start_idx..end_idx];
        
        let batch_start = Instant::now();
        
        let optimizer = Optimizer::new_with_cache(candles.to_vec(), max_lookback);
        let results = optimizer.optimize_parallel_with_stdout_progress(batch.to_vec());
        
        // Se é validação (max_tests == 1), salvar trades detalhados
        if max_tests == Some(1) && !results.is_empty() && results[0].success {
            // Salvar trades individuais
            let trades_file = filename.replace(".csv", "_trades_detailed.csv");
            let mut trades_wtr = csv::Writer::from_path(&trades_file)
                .expect("Falha ao criar CSV de trades");
            
            // Header
            trades_wtr.write_record(&[
                "entry_idx", "exit_idx", "type", "entry", "exit", 
                "sl", "tp", "pnl", "exit_reason"
            ]).expect("Falha header");
            
            // Trades
            for trade in &results[0].trades {
                let trade_type = match trade.trade_type {
                    TradeType::Long => "LONG",
                    TradeType::Short => "SHORT",
                };
                let exit_reason = match trade.exit_reason {
                    ExitReason::StopLoss => "SL",
                    ExitReason::TakeProfit => "TP",
                    ExitReason::IntradayClose => "INTRADAY",
                };
                
                trades_wtr.write_record(&[
                    trade.entry_idx.to_string(),
                    trade.exit_idx.to_string(),
                    trade_type.to_string(),
                    trade.entry_price.to_string(),
                    trade.exit_price.to_string(),
                    trade.sl.to_string(),
                    trade.tp.to_string(),
                    trade.pnl.to_string(),
                    exit_reason.to_string(),
                ]).expect("Falha ao escrever trade");
            }
            trades_wtr.flush().expect("Falha flush trades");
            println!("\n[TRADES] Salvos {} trades em: {}", results[0].trades.len(), trades_file);
        }
        
        // Salvar parâmetros + métricas
        for (idx, result) in results.iter().enumerate() {
            let params = &batch[idx];
            wtr.write_record(&[
                params.min_amplitude_mult.to_string(),
                params.min_volume_mult.to_string(),
                params.max_sombra_pct.to_string(),
                params.lookback_amplitude.to_string(),
                params.horario_inicio.to_string(),
                params.minuto_inicio.to_string(),
                params.horario_fim.to_string(),
                params.minuto_fim.to_string(),
                params.horario_fechamento.to_string(),
                params.minuto_fechamento.to_string(),
                params.sl_atr_mult.to_string(),
                params.tp_atr_mult.to_string(),
                params.usar_trailing.to_string(),
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
    println!("Estratégia: {}", config.strategy.name);
    println!("Tempo: {:.1} s ({:.2} min)", tempo_total, tempo_total / 60.0);
    println!("Velocidade média: {:.0} t/s", total as f64 / tempo_total);
    println!("Arquivo: {}", filename);
    println!("{}", "=".repeat(80));
}

