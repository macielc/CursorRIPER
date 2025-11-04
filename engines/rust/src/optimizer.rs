use crate::backtest_engine::BacktestEngine;
use crate::types::{BarraElefanteParams, BacktestResult, Candle};
use rayon::prelude::*;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use indicatif::{ProgressBar, ProgressStyle};

use crate::strategy::PrecomputedData;

pub struct Optimizer {
    candles: Arc<Vec<Candle>>,  // Arc para compartilhar entre threads SEM clonar
    precomputed: Option<Arc<PrecomputedData>>,  // Cache pre-calculado
}

impl Optimizer {
    pub fn new(candles: Vec<Candle>) -> Self {
        Self {
            candles: Arc::new(candles),
            precomputed: None,
        }
    }

    pub fn new_with_cache(candles: Vec<Candle>, max_lookback: usize) -> Self {
        let candles_arc = Arc::new(candles);
        
        println!("[OPTIMIZER] Pre-calculando cache com lookback={}...", max_lookback);
        let cache_start = std::time::Instant::now();
        let precomputed = Arc::new(PrecomputedData::new(&candles_arc, max_lookback));
        let cache_time = cache_start.elapsed().as_secs_f64();
        println!("[OPTIMIZER] Cache pronto em {:.2}s (economiza 4.2M calculos!)\n", cache_time);
        
        Self {
            candles: candles_arc,
            precomputed: Some(precomputed),
        }
    }

    pub fn optimize_parallel(
        &self,
        param_grid: Vec<BarraElefanteParams>,
        progress_callback: Option<Box<dyn Fn(usize, usize) + Send + Sync>>,
    ) -> Vec<BacktestResult> {
        let total = param_grid.len();
        let counter = Arc::new(AtomicUsize::new(0));

        let results: Vec<BacktestResult> = param_grid
            .par_iter()
            .map(|params| {
                // Compartilhar candles E cache via Arc (ZERO copy!)
                let engine = if let Some(ref cache) = self.precomputed {
                    BacktestEngine::new_with_precomputed(
                        Arc::clone(&self.candles),
                        Arc::clone(cache)
                    )
                } else {
                    BacktestEngine::new(Arc::clone(&self.candles))
                };
                let result = engine.run_strategy(params);

                // Atualizar progresso a cada 50 testes
                let count = counter.fetch_add(1, Ordering::Relaxed) + 1;
                if let Some(ref callback) = progress_callback {
                    if count % 50 == 0 || count == total {
                        callback(count, total);
                    }
                }

                result
            })
            .collect();

        results
    }

    pub fn optimize_parallel_with_stdout_progress(&self, param_grid: Vec<BarraElefanteParams>) -> Vec<BacktestResult> {
        let total = param_grid.len();
        let counter = Arc::new(AtomicUsize::new(0));

        use std::time::Instant;
        let start_time = Instant::now();
        
        // FORCAR USO DE TODOS OS CORES DISPONIVEIS
        let num_cpus = std::thread::available_parallelism()
            .map(|n| n.get())
            .unwrap_or(32);
        
        println!("\n[RUST MULTICORE] {} threads disponiveis", num_cpus);
        println!("[RUST] Iniciando {} testes...\n", total);
        
        // VERIFICAR se Rayon foi configurado corretamente
        let rayon_threads = rayon::current_num_threads();
        println!("[RUST] Rayon usando {} threads", rayon_threads);
        
        if rayon_threads < num_cpus {
            println!("[AVISO] Rayon usando menos threads que disponivel!");
            println!("[AVISO] Esperado: {}, Usando: {}", num_cpus, rayon_threads);
        }
        println!();
        
        // Thread separada para mostrar progresso VISUAL
        let counter_clone = Arc::clone(&counter);
        let progress_handle = std::thread::spawn(move || {
            let start = std::time::Instant::now();
            loop {
                std::thread::sleep(std::time::Duration::from_secs(2));
                let current = counter_clone.load(Ordering::Relaxed);
                if current >= total {
                    break;
                }
                let elapsed = start.elapsed().as_secs_f64();
                let velocity = if elapsed > 0.0 { current as f64 / elapsed } else { 0.0 };
                
                // Porcentagem
                let pct = (current as f64 / total as f64) * 100.0;
                
                // Barra visual
                let barra_len = 50;
                let filled = ((pct / 100.0) * barra_len as f64) as usize;
                let barra: String = "█".repeat(filled) + &"░".repeat(barra_len - filled);
                
                // ETA
                let eta_segundos = if velocity > 0.0 {
                    ((total - current) as f64 / velocity)
                } else {
                    0.0
                };
                let eta_min = (eta_segundos / 60.0) as usize;
                
                print!("\r[{}] {:.1}% | {}/{} | {:.0} t/s | ETA: {}min   ", 
                       barra, pct, current, total, velocity, eta_min);
                use std::io::Write;
                std::io::stdout().flush().unwrap();
            }
            println!(); // Nova linha ao terminar
        });
        
        // PROCESSAMENTO PARALELO
        // NAO criar pool local - usar o global ja configurado
        println!("[RUST] Iniciando par_iter() com {} threads Rayon", rayon::current_num_threads());
        
        // CORRECAO: par_iter() DIRETO - Rayon divide automaticamente o trabalho
        let results: Vec<BacktestResult> = param_grid
            .par_iter()
            .map(|params| {
                // SEM LOCKS! Cada thread trabalha independente + CACHE
                let engine = if let Some(ref cache) = self.precomputed {
                    BacktestEngine::new_with_precomputed(
                        Arc::clone(&self.candles),
                        Arc::clone(cache)
                    )
                } else {
                    BacktestEngine::new(Arc::clone(&self.candles))
                };
                let result = engine.run_strategy(params);
                counter.fetch_add(1, Ordering::Relaxed);
                result
            })
            .collect();
        
        println!("[RUST] par_iter() completo");
        
        // Aguardar thread de progresso terminar
        let _ = progress_handle.join();

        let elapsed = start_time.elapsed().as_secs_f64();
        let velocity = total as f64 / elapsed;
        let velocidade_single_core = 300.0;
        let speedup = velocity / velocidade_single_core;
        
        println!("\n[RUST COMPLETO] {} testes em {:.1}s = {:.0} t/s", total, elapsed, velocity);
        println!("[RUST] Speedup: {:.1}x (esperado: ~{}x)", speedup, num_cpus);
        
        if speedup < 5.0 {
            println!("[CRITICO] MULTICORE NAO FUNCIONOU! Rodou em single-core!");
        } else if speedup < num_cpus as f64 * 0.5 {
            println!("[AVISO] Multicore parcial - usando apenas {:.0}% dos cores", 
                     (speedup / num_cpus as f64) * 100.0);
        } else {
            println!("[OK] Multicore funcionando! Usando {}% dos cores disponiveis",
                     ((speedup / num_cpus as f64) * 100.0) as i32);
        }
        println!();

        results
    }

    pub fn optimize_single(&self, params: &BarraElefanteParams) -> BacktestResult {
        let engine = BacktestEngine::new(Arc::clone(&self.candles));
        engine.run_strategy(params)
    }
}

pub fn generate_param_grid(
    min_amplitude_mult_range: (f32, f32, f32), // (min, max, step)
    min_volume_mult_range: (f32, f32, f32),
    max_sombra_pct_range: (f32, f32, f32),
    sl_atr_mult_range: (f32, f32, f32),
    tp_atr_mult_range: (f32, f32, f32),
) -> Vec<BarraElefanteParams> {
    let mut grid = Vec::new();

    let mut min_amplitude_mult = min_amplitude_mult_range.0;
    while min_amplitude_mult <= min_amplitude_mult_range.1 {
        let mut min_volume_mult = min_volume_mult_range.0;
        while min_volume_mult <= min_volume_mult_range.1 {
            let mut max_sombra_pct = max_sombra_pct_range.0;
            while max_sombra_pct <= max_sombra_pct_range.1 {
                let mut sl_atr_mult = sl_atr_mult_range.0;
                while sl_atr_mult <= sl_atr_mult_range.1 {
                    let mut tp_atr_mult = tp_atr_mult_range.0;
                    while tp_atr_mult <= tp_atr_mult_range.1 {
                        grid.push(BarraElefanteParams {
                            min_amplitude_mult,
                            min_volume_mult,
                            max_sombra_pct,
                            sl_atr_mult,
                            tp_atr_mult,
                            ..Default::default()
                        });

                        tp_atr_mult += tp_atr_mult_range.2;
                    }
                    sl_atr_mult += sl_atr_mult_range.2;
                }
                max_sombra_pct += max_sombra_pct_range.2;
            }
            min_volume_mult += min_volume_mult_range.2;
        }
        min_amplitude_mult += min_amplitude_mult_range.2;
    }

    grid
}

