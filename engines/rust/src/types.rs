use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct Candle {
    pub open: f32,
    pub high: f32,
    pub low: f32,
    pub close: f32,
    pub volume: f32,
    pub atr: f32,
    pub hour: i32,
    pub minute: i32,
    #[serde(default)]
    pub is_warmup: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub entry_idx: usize,
    pub exit_idx: usize,
    pub trade_type: TradeType,
    pub entry_price: f32,
    pub exit_price: f32,
    pub sl: f32,
    pub tp: f32,
    pub pnl: f32,
    pub exit_reason: ExitReason,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum TradeType {
    Long,
    Short,
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub enum ExitReason {
    StopLoss,
    TakeProfit,
    IntradayClose,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BarraElefanteParams {
    pub min_amplitude_mult: f32,
    pub min_volume_mult: f32,
    pub max_sombra_pct: f32,
    pub lookback_amplitude: usize,
    pub horario_inicio: i32,
    pub minuto_inicio: i32,
    pub horario_fim: i32,
    pub minuto_fim: i32,
    pub horario_fechamento: i32,
    pub minuto_fechamento: i32,
    pub sl_atr_mult: f32,
    pub tp_atr_mult: f32,
    pub usar_trailing: bool,
}

impl Default for BarraElefanteParams {
    fn default() -> Self {
        Self {
            min_amplitude_mult: 1.5,
            min_volume_mult: 1.2,
            max_sombra_pct: 0.4,
            lookback_amplitude: 20,
            horario_inicio: 9,
            minuto_inicio: 15,
            horario_fim: 11,
            minuto_fim: 0,
            horario_fechamento: 12,
            minuto_fechamento: 15,
            sl_atr_mult: 2.0,
            tp_atr_mult: 3.0,
            usar_trailing: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub trades: Vec<Trade>,
    pub metrics: Metrics,
    pub success: bool,
    pub error_msg: Option<String>,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct Metrics {
    pub total_return: f32,
    pub total_return_pct: f32,
    pub total_trades: usize,
    pub winning_trades: usize,
    pub losing_trades: usize,
    pub win_rate: f32,
    pub avg_win: f32,
    pub avg_loss: f32,
    pub avg_trade: f32,
    pub profit_factor: f32,
    pub sharpe_ratio: f32,
    pub sortino_ratio: f32,
    pub max_drawdown: f32,
    pub max_drawdown_pct: f32,
    pub max_consecutive_wins: usize,
    pub max_consecutive_losses: usize,
    pub expectancy: f32,
}

