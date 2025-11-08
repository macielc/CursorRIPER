use crate::metrics::calculate_metrics;
use crate::strategy::{detect_barra_elefante, Signals, PrecomputedData};
use crate::types::{
    BarraElefanteParams, BacktestResult, Candle, ExitReason, Metrics, Trade, TradeType,
};

use std::sync::Arc;

pub struct BacktestEngine {
    pub candles: Arc<Vec<Candle>>,  // Arc para compartilhar entre threads
    pub precomputed: Option<Arc<PrecomputedData>>,  // Dados pre-calculados (CACHE)
    pub initial_capital: f32,
}

impl BacktestEngine {
    pub fn new(candles: Arc<Vec<Candle>>) -> Self {
        Self {
            candles,
            precomputed: None,  // Por enquanto nao usa cache
            initial_capital: 10000.0,
        }
    }
    
    pub fn new_with_cache(candles: Arc<Vec<Candle>>, lookback: usize) -> Self {
        // PRE-CALCULAR rolling means UMA VEZ (compartilhado por todos os testes)
        let precomputed = Arc::new(PrecomputedData::new(&candles, lookback));
        
        Self {
            candles,
            precomputed: Some(precomputed),
            initial_capital: 10000.0,
        }
    }

    pub fn new_with_precomputed(candles: Arc<Vec<Candle>>, precomputed: Arc<PrecomputedData>) -> Self {
        Self {
            candles,
            precomputed: Some(precomputed),
            initial_capital: 10000.0,
        }
    }

    pub fn run_strategy(&self, params: &BarraElefanteParams) -> BacktestResult {
        // Gerar sinais - USAR CACHE SE DISPONIVEL
        let signals = if let Some(ref precomp) = self.precomputed {
            crate::strategy::detect_barra_elefante_with_cache(&self.candles, params, Some(precomp))
        } else {
            detect_barra_elefante(&self.candles, params)
        };

        // Simular trades
        let trades = self.simulate_trades(&signals, params);

        if trades.is_empty() {
            return BacktestResult {
                trades: vec![],
                metrics: Metrics::default(),
                success: false,
                error_msg: Some("Nenhum trade gerado".to_string()),
            };
        }

        // Calcular métricas
        let metrics = calculate_metrics(&trades);

        BacktestResult {
            trades,
            metrics,
            success: true,
            error_msg: None,
        }
    }

    fn simulate_trades(
        &self,
        signals: &Signals,
        params: &BarraElefanteParams,
    ) -> Vec<Trade> {
        let n = self.candles.len();
        let mut trades = Vec::new();
        let mut position: Option<Position> = None;
        let mut pending_entry: Option<PendingEntry> = None;

        for i in 0..n {
            // SLIPPAGE: Processar entrada pendente da barra anterior
            if let Some(pending) = pending_entry.take() {
                if position.is_none() {
                    let entry_price = self.candles[i].open; // OPEN da barra atual
                    let atr = self.candles[i].atr; // ATR da barra de entrada

                    // Calcular SL/TP com base no preço de entrada REAL
                    // TP baseado no RISCO (não em ATR direto!)
                    let (sl, tp) = match pending.trade_type {
                        TradeType::Long => {
                            let sl = entry_price - (atr * params.sl_atr_mult);
                            let risk = entry_price - sl;  // Risk = ATR × sl_atr_mult
                            let tp = entry_price + (risk * params.tp_atr_mult);  // TP = entry + (risk × tp_atr_mult)
                            (sl, tp)
                        }
                        TradeType::Short => {
                            let sl = entry_price + (atr * params.sl_atr_mult);
                            let risk = sl - entry_price;  // Risk = ATR × sl_atr_mult
                            let tp = entry_price - (risk * params.tp_atr_mult);  // TP = entry - (risk × tp_atr_mult)
                            (sl, tp)
                        }
                    };

                    position = Some(Position {
                        entry_idx: i,
                        trade_type: pending.trade_type,
                        entry_price,
                        sl,
                        tp,
                    });
                }
            }

            // FECHAMENTO INTRADAY: Fechar posição ao final do dia
            if let Some(pos) = position.take() {
                let hora = self.candles[i].hour;
                let minuto = self.candles[i].minute;

                if hora > params.horario_fechamento
                    || (hora == params.horario_fechamento && minuto >= params.minuto_fechamento)
                {
                    let exit_price = self.candles[i].close;
                    let pnl = calculate_pnl(pos.trade_type, pos.entry_price, exit_price);

                    trades.push(Trade {
                        entry_idx: pos.entry_idx,
                        exit_idx: i,
                        trade_type: pos.trade_type,
                        entry_price: pos.entry_price,
                        exit_price,
                        sl: pos.sl,
                        tp: pos.tp,
                        pnl,
                        exit_reason: ExitReason::IntradayClose,
                    });

                    // Permitir novo sinal no mesmo candle
                } else {
                    // Restaurar posição se não fechou
                    position = Some(pos);
                }
            }

            // Verificar saída se tem posição
            if let Some(pos) = &position {
                let candle = &self.candles[i];
                let mut exit_signal = false;
                let mut exit_price = 0.0;
                let mut exit_reason = ExitReason::StopLoss;

                match pos.trade_type {
                    TradeType::Long => {
                        // SL atingido
                        if candle.low <= pos.sl {
                            exit_price = pos.sl;
                            exit_reason = ExitReason::StopLoss;
                            exit_signal = true;
                        }
                        // TP atingido
                        else if candle.high >= pos.tp {
                            exit_price = pos.tp;
                            exit_reason = ExitReason::TakeProfit;
                            exit_signal = true;
                        }
                    }
                    TradeType::Short => {
                        // SL atingido
                        if candle.high >= pos.sl {
                            exit_price = pos.sl;
                            exit_reason = ExitReason::StopLoss;
                            exit_signal = true;
                        }
                        // TP atingido
                        else if candle.low <= pos.tp {
                            exit_price = pos.tp;
                            exit_reason = ExitReason::TakeProfit;
                            exit_signal = true;
                        }
                    }
                }

                if exit_signal {
                    let pnl = calculate_pnl(pos.trade_type, pos.entry_price, exit_price);

                    trades.push(Trade {
                        entry_idx: pos.entry_idx,
                        exit_idx: i,
                        trade_type: pos.trade_type,
                        entry_price: pos.entry_price,
                        exit_price,
                        sl: pos.sl,
                        tp: pos.tp,
                        pnl,
                        exit_reason,
                    });

                    position = None;
                }
            }

            // Detectar novos sinais (SLIPPAGE: entrada na próxima barra)
            if position.is_none() && pending_entry.is_none() {
                if signals.entries_long[i] {
                    pending_entry = Some(PendingEntry {
                        trade_type: TradeType::Long,
                    });
                } else if signals.entries_short[i] {
                    pending_entry = Some(PendingEntry {
                        trade_type: TradeType::Short,
                    });
                }
            }
        }

        trades
    }
}

#[derive(Debug, Clone)]
struct Position {
    entry_idx: usize,
    trade_type: TradeType,
    entry_price: f32,
    sl: f32,
    tp: f32,
}

#[derive(Debug, Clone)]
struct PendingEntry {
    trade_type: TradeType,
    // SL/TP serão calculados dinamicamente no momento da entrada
}

#[inline]
fn calculate_pnl(trade_type: TradeType, entry: f32, exit: f32) -> f32 {
    match trade_type {
        TradeType::Long => exit - entry,
        TradeType::Short => entry - exit,
    }
}

