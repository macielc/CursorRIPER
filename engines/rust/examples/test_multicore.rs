use rayon::prelude::*;
use std::time::Instant;
use std::thread;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

fn heavy_computation(n: usize) -> usize {
    // Simulação de trabalho pesado
    let mut result = 0;
    for i in 0..10000 {
        result += (n * i) % 997;
    }
    result
}

fn main() {
    // Configurar Rayon
    let num_cpus = thread::available_parallelism().unwrap().get();
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .build_global()
        .unwrap();
    
    println!("=== TESTE MULTICORE RAYON ===");
    println!("Cores detectados: {}", num_cpus);
    println!("Rayon threads: {}", rayon::current_num_threads());
    println!();
    
    let test_size = 100000;
    
    // Teste 1: Sequencial
    println!("Teste 1: SEQUENCIAL");
    let start = Instant::now();
    let results_seq: Vec<_> = (0..test_size)
        .map(|i| heavy_computation(i))
        .collect();
    let elapsed_seq = start.elapsed().as_secs_f64();
    println!("Tempo: {:.2}s", elapsed_seq);
    println!();
    
    // Teste 2: Paralelo
    println!("Teste 2: PARALELO com Rayon");
    let start = Instant::now();
    let counter = Arc::new(AtomicUsize::new(0));
    
    let results_par: Vec<_> = (0..test_size)
        .into_par_iter()
        .map(|i| {
            let result = heavy_computation(i);
            let count = counter.fetch_add(1, Ordering::Relaxed) + 1;
            
            if count % 10000 == 0 {
                let elapsed = start.elapsed().as_secs_f64();
                let velocity = count as f64 / elapsed;
                println!("  {} / {} ({:.0} ops/s)", count, test_size, velocity);
            }
            
            result
        })
        .collect();
    
    let elapsed_par = start.elapsed().as_secs_f64();
    println!("Tempo: {:.2}s", elapsed_par);
    println!();
    
    // Comparação
    let speedup = elapsed_seq / elapsed_par;
    println!("=== RESULTADO ===");
    println!("Speedup: {:.2}x", speedup);
    
    if speedup > num_cpus as f64 * 0.5 {
        println!("STATUS: MULTICORE FUNCIONANDO! ✓");
    } else if speedup > 2.0 {
        println!("STATUS: Paralelismo parcial (pode melhorar)");
    } else {
        println!("STATUS: MULTICORE NAO ESTA FUNCIONANDO! ✗");
    }
}

