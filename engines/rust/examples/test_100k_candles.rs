use rayon::prelude::*;
use std::time::Instant;

#[derive(Clone)]
struct Candle {
    high: f32,
    low: f32,
    volume: f32,
}

fn process_candles(candles: &[Candle], multiplier: f32) -> f32 {
    // Simular processamento similar ao backtest
    let mut sum = 0.0;
    
    for i in 20..candles.len() {
        // Calcular amplitude media (rolling)
        let mut amp_sum = 0.0;
        for j in (i-20)..i {
            amp_sum += candles[j].high - candles[j].low;
        }
        let amp_media = amp_sum / 20.0;
        
        // Filtros simples
        let amplitude = candles[i].high - candles[i].low;
        if amplitude > amp_media * multiplier {
            sum += amplitude;
        }
    }
    
    sum
}

fn main() {
    // Gerar 100k candles
    let candles: Vec<Candle> = (0..100000)
        .map(|i| Candle {
            high: 100.0 + (i as f32 * 0.01),
            low: 99.0 + (i as f32 * 0.01),
            volume: 1000.0,
        })
        .collect();
    
    println!("100k candles gerados");
    println!("Configurando Rayon com todos os cores...");
    
    let num_threads = std::thread::available_parallelism().unwrap().get();
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_threads)
        .build_global()
        .unwrap();
    
    println!("Rayon: {} threads", rayon::current_num_threads());
    println!();
    
    // Teste com 10k combinacoes
    let params: Vec<f32> = (0..10000).map(|i| 1.0 + (i as f32 * 0.0001)).collect();
    
    println!("Teste 1: SEQUENCIAL (10k testes)");
    let start = Instant::now();
    let results_seq: Vec<f32> = params
        .iter()
        .map(|&p| process_candles(&candles, p))
        .collect();
    let elapsed_seq = start.elapsed().as_secs_f64();
    println!("  Tempo: {:.2}s", elapsed_seq);
    println!("  Velocidade: {:.0} t/s", params.len() as f64 / elapsed_seq);
    println!();
    
    println!("Teste 2: PARALELO (10k testes)");
    let start = Instant::now();
    let results_par: Vec<f32> = params
        .par_iter()
        .map(|&p| process_candles(&candles, p))
        .collect();
    let elapsed_par = start.elapsed().as_secs_f64();
    println!("  Tempo: {:.2}s", elapsed_par);
    println!("  Velocidade: {:.0} t/s", params.len() as f64 / elapsed_par);
    println!();
    
    let speedup = elapsed_seq / elapsed_par;
    println!("Speedup: {:.1}x (esperado: ~{}x)", speedup, num_threads);
    
    if speedup > num_threads as f64 * 0.7 {
        println!("STATUS: MULTICORE PERFEITO!");
    } else if speedup > 5.0 {
        println!("STATUS: Multicore parcial");
    } else {
        println!("STATUS: SINGLE CORE - PROBLEMA!");
    }
    
    // Verificar resultados
    assert_eq!(results_seq.len(), results_par.len());
    println!("\nResultados OK (sum seq: {:.2}, sum par: {:.2})", 
             results_seq.iter().sum::<f32>(), 
             results_par.iter().sum::<f32>());
}

