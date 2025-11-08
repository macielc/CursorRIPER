// VALIDACAO - Roda UM teste e salva detalhes completos
extern crate engine_rust;
use engine_rust::{BarraElefanteParams, Candle, BacktestEngine};
use polars::prelude::*;
use std::sync::Arc;

fn main() {
    println!("\n{}", "=".repeat(80));
    println!("VALIDACAO RUST - Teste Unico com Detalhes");
    println!("{}\n", "=".repeat(80));

    // Carregar dados
    println!("1) Carregando Golden Data...");
    let data_path = "C:/Users/AltF4/Documents/#__JUREAIS/data/WINFUT_M5_Golden_Data.parquet";
    let df = LazyFrame::scan_parquet(data_path, Default::default())
        .expect("Falha")
        .collect()
        .expect("Falha");

    // Filtrar horário
    let df_filtered = df.lazy()
        .filter(
            col("hour").gt_eq(lit(9))
            .and(col("hour").lt_eq(lit(18)))
        )
        .slice(0, 2500)  // Aproximadamente Janeiro 2024 (2486 candles)
        .collect()
        .expect("Falha");

    println!("   Total: {} candles\n", df_filtered.height());

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
            is_warmup: false,
        });
    }
    println!("   OK: {} candles\n", candles.len());

    // PARAMETROS DE TESTE (vou usar valores medios)
    let params = BarraElefanteParams {
        min_amplitude_mult: 2.0,
        min_volume_mult: 1.5,
        max_sombra_pct: 0.3,
        lookback_amplitude: 20,
        horario_inicio: 9,
        minuto_inicio: 30,
        horario_fim: 12,
        minuto_fim: 30,
        horario_fechamento: 13,
        minuto_fechamento: 30,
        sl_atr_mult: 2.0,
        tp_atr_mult: 3.0,
        usar_trailing: false,
    };

    println!("3) Parametros do teste:");
    println!("   min_amplitude_mult: {}", params.min_amplitude_mult);
    println!("   min_volume_mult: {}", params.min_volume_mult);
    println!("   max_sombra_pct: {}", params.max_sombra_pct);
    println!("   lookback_amplitude: {}", params.lookback_amplitude);
    println!("   horario_inicio: {}:{}", params.horario_inicio, params.minuto_inicio);
    println!("   horario_fim: {}:{}", params.horario_fim, params.minuto_fim);
    println!("   horario_fechamento: {}:{}", params.horario_fechamento, params.minuto_fechamento);
    println!("   sl_atr_mult: {}", params.sl_atr_mult);
    println!("   tp_atr_mult: {}", params.tp_atr_mult);
    println!("   usar_trailing: {}\n", params.usar_trailing);

    // Rodar backtest COM CACHE
    println!("4) Rodando backtest...");
    let candles_arc = Arc::new(candles);
    let engine = BacktestEngine::new_with_cache(candles_arc, params.lookback_amplitude);
    let result = engine.run_strategy(&params);

    // Mostrar resultados
    println!("\n{}", "=".repeat(80));
    println!("RESULTADOS");
    println!("{}\n", "=".repeat(80));
    println!("Success: {}", result.success);
    println!("Total Trades: {}", result.metrics.total_trades);
    println!("Win Rate: {:.2}%", result.metrics.win_rate * 100.0);
    println!("Total Return: R$ {:.2}", result.metrics.total_return);
    println!("Total Return %: {:.2}%", result.metrics.total_return_pct);
    println!("Profit Factor: {:.2}", result.metrics.profit_factor);
    println!("Sharpe Ratio: {:.2}", result.metrics.sharpe_ratio);
    println!("Max Drawdown %: {:.2}%", result.metrics.max_drawdown_pct);

    // Salvar TRADES em CSV para comparacao
    println!("\n5) Salvando trades para validacao...");
    let mut wtr = csv::Writer::from_path("validation_rust_trades.csv").expect("Falha");
    
    wtr.write_record(&[
        "entry_idx", "exit_idx", "direction", "entry_price", "exit_price",
        "exit_reason", "pnl", "pnl_pct", "return_pct"
    ]).expect("Falha header");

    for trade in &result.trades {
        let pnl_pct = trade.pnl / trade.entry_price;
        let return_pct = trade.pnl / 10000.0; // capital inicial
        
        wtr.write_record(&[
            trade.entry_idx.to_string(),
            trade.exit_idx.to_string(),
            format!("{:?}", trade.trade_type),
            format!("{:.2}", trade.entry_price),
            format!("{:.2}", trade.exit_price),
            format!("{:?}", trade.exit_reason),
            format!("{:.2}", trade.pnl),
            format!("{:.6}", pnl_pct),
            format!("{:.6}", return_pct),
        ]).expect("Falha");
    }
    wtr.flush().expect("Falha flush");

    // Salvar METRICAS
    let mut wtr_metrics = csv::Writer::from_path("validation_rust_metrics.csv").expect("Falha");
    wtr_metrics.write_record(&[
        "success", "total_trades", "winning_trades", "losing_trades", "win_rate",
        "total_return", "total_return_pct", "avg_win", "avg_loss", "avg_return",
        "profit_factor", "sharpe_ratio", "max_drawdown", "max_drawdown_pct"
    ]).expect("Falha header");
    
    wtr_metrics.write_record(&[
        result.success.to_string(),
        result.metrics.total_trades.to_string(),
        result.metrics.winning_trades.to_string(),
        result.metrics.losing_trades.to_string(),
        format!("{:.6}", result.metrics.win_rate),
        format!("{:.2}", result.metrics.total_return),
        format!("{:.6}", result.metrics.total_return_pct),
        format!("{:.2}", result.metrics.avg_win),
        format!("{:.2}", result.metrics.avg_loss),
        format!("{:.2}", result.metrics.avg_trade),  // avg_trade, nao avg_return
        format!("{:.6}", result.metrics.profit_factor),
        format!("{:.6}", result.metrics.sharpe_ratio),
        format!("{:.2}", result.metrics.max_drawdown),
        format!("{:.6}", result.metrics.max_drawdown_pct),
    ]).expect("Falha");
    wtr_metrics.flush().expect("Falha flush");

    println!("\nArquivos salvos:");
    println!("  - validation_rust_trades.csv ({} trades)", result.trades.len());
    println!("  - validation_rust_metrics.csv");
    println!("\n{}", "=".repeat(80));
}

