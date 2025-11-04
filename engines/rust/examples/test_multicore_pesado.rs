use rayon::prelude::*;
use std::time::Instant;
use std::thread;

fn trabalho_pesado(n: usize) -> u64 {
    // Trabalho MUITO pesado - calcular primos
    let mut count = 0u64;
    for i in 2..n {
        let mut is_prime = true;
        for j in 2..((i as f64).sqrt() as usize + 1) {
            if i % j == 0 {
                is_prime = false;
                break;
            }
        }
        if is_prime {
            count += 1;
        }
    }
    count
}

fn main() {
    // Configurar Rayon
    let num_cpus = thread::available_parallelism().unwrap().get();
    rayon::ThreadPoolBuilder::new()
        .num_threads(num_cpus)
        .build_global()
        .unwrap();
    
    println!("=== TESTE MULTICORE PESADO ===");
    println!("Cores: {}", num_cpus);
    println!("Rayon threads: {}", rayon::current_num_threads());
    println!();
    println!("OLHE O TASK MANAGER!");
    println!();
    
    let test_size = 1000;
    let work_per_item = 5000; // Cada item vai calcular primos ate 5000
    
    // Teste 1: Sequencial
    println!("1) SEQUENCIAL");
    let start = Instant::now();
    let sum_seq: u64 = (0..test_size)
        .map(|_| trabalho_pesado(work_per_item))
        .sum();
    let elapsed_seq = start.elapsed().as_secs_f64();
    println!("   Tempo: {:.2}s", elapsed_seq);
    println!("   Resultado: {}", sum_seq);
    println!();
    
    // Teste 2: Paralelo
    println!("2) PARALELO");
    let start = Instant::now();
    let sum_par: u64 = (0..test_size)
        .into_par_iter()
        .map(|_| trabalho_pesado(work_per_item))
        .sum();
    let elapsed_par = start.elapsed().as_secs_f64();
    println!("   Tempo: {:.2}s", elapsed_par);
    println!("   Resultado: {}", sum_par);
    println!();
    
    // Comparação
    let speedup = elapsed_seq / elapsed_par;
    println!("=== RESULTADO ===");
    println!("Speedup: {:.2}x", speedup);
    println!("Esperado: ~{}x", num_cpus);
    println!();
    
    if speedup > num_cpus as f64 * 0.7 {
        println!("STATUS: MULTICORE FUNCIONANDO PERFEITAMENTE! ✓✓✓");
    } else if speedup > 4.0 {
        println!("STATUS: Multicore funcionando parcialmente");
    } else {
        println!("STATUS: MULTICORE NAO FUNCIONA! ✗✗✗");
    }
}

