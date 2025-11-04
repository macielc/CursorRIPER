use crate::types::{Metrics, Trade, TradeType, ExitReason};

pub fn calculate_metrics(trades: &[Trade]) -> Metrics {
    if trades.is_empty() {
        return Metrics::default();
    }

    let total_trades = trades.len();
    let returns: Vec<f32> = trades.iter().map(|t| t.pnl).collect();
    let total_return: f32 = returns.iter().sum();

    // Separar winners e losers
    let winning_trades: Vec<&Trade> = trades.iter().filter(|t| t.pnl > 0.0).collect();
    let losing_trades: Vec<&Trade> = trades.iter().filter(|t| t.pnl < 0.0).collect();

    let win_rate = winning_trades.len() as f32 / total_trades as f32;

    let avg_win = if !winning_trades.is_empty() {
        winning_trades.iter().map(|t| t.pnl).sum::<f32>() / winning_trades.len() as f32
    } else {
        0.0
    };

    let avg_loss = if !losing_trades.is_empty() {
        losing_trades.iter().map(|t| t.pnl).sum::<f32>() / losing_trades.len() as f32
    } else {
        0.0
    };

    let avg_trade = returns.iter().sum::<f32>() / total_trades as f32;

    // Profit Factor
    let gross_profit: f32 = winning_trades.iter().map(|t| t.pnl).sum();
    let gross_loss: f32 = losing_trades.iter().map(|t| t.pnl.abs()).sum();
    let profit_factor = if gross_loss > 0.0 {
        gross_profit / gross_loss
    } else {
        0.0
    };

    // Sharpe Ratio
    let sharpe_ratio = calculate_sharpe(&returns);

    // Sortino Ratio
    let sortino_ratio = calculate_sortino(&returns);

    // Max Drawdown
    let (max_dd, max_dd_pct) = calculate_max_drawdown(&returns);

    // Consecutive wins/losses
    let max_consecutive_wins = max_consecutive(trades, true);
    let max_consecutive_losses = max_consecutive(trades, false);

    // Expectancy
    let expectancy = (win_rate * avg_win) + ((1.0 - win_rate) * avg_loss);

    Metrics {
        total_return,
        total_return_pct: (total_return / 10000.0) * 100.0,
        total_trades,
        winning_trades: winning_trades.len(),
        losing_trades: losing_trades.len(),
        win_rate,
        avg_win,
        avg_loss,
        avg_trade,
        profit_factor,
        sharpe_ratio,
        sortino_ratio,
        max_drawdown: max_dd,
        max_drawdown_pct: max_dd_pct,
        max_consecutive_wins,
        max_consecutive_losses,
        expectancy,
    }
}

fn calculate_sharpe(returns: &[f32]) -> f32 {
    if returns.is_empty() {
        return 0.0;
    }

    let mean = returns.iter().sum::<f32>() / returns.len() as f32;
    let variance = returns.iter().map(|r| (r - mean).powi(2)).sum::<f32>() / returns.len() as f32;
    let std = variance.sqrt();

    if std > 0.0 {
        mean / std * (252.0_f32).sqrt()  // Anualized (252 trading days)
    } else {
        0.0
    }
}

fn calculate_sortino(returns: &[f32]) -> f32 {
    if returns.is_empty() {
        return 0.0;
    }

    let mean = returns.iter().sum::<f32>() / returns.len() as f32;
    
    // Downside deviation (apenas retornos negativos)
    let downside_returns: Vec<f32> = returns.iter().filter(|&&r| r < 0.0).copied().collect();
    
    if downside_returns.is_empty() {
        return 0.0;
    }

    let downside_variance = downside_returns.iter().map(|r| r.powi(2)).sum::<f32>() / downside_returns.len() as f32;
    let downside_std = downside_variance.sqrt();

    if downside_std > 0.0 {
        mean / downside_std * (252.0_f32).sqrt()
    } else {
        0.0
    }
}

fn calculate_max_drawdown(returns: &[f32]) -> (f32, f32) {
    if returns.is_empty() {
        return (0.0, 0.0);
    }

    // Calcular equity curve (cumsum)
    let mut equity_curve = Vec::with_capacity(returns.len());
    let mut cumsum = 0.0;
    for &ret in returns {
        cumsum += ret;
        equity_curve.push(cumsum);
    }

    let mut max_equity = f32::NEG_INFINITY;
    let mut max_dd = 0.0;

    for &equity in &equity_curve {
        if equity > max_equity {
            max_equity = equity;
        }
        let dd = max_equity - equity;
        if dd > max_dd {
            max_dd = dd;
        }
    }

    let max_dd_pct = if max_equity > 0.0 {
        (max_dd / max_equity) * 100.0
    } else {
        0.0
    };

    (max_dd, max_dd_pct)
}

fn max_consecutive(trades: &[Trade], wins: bool) -> usize {
    let mut max_count = 0;
    let mut current_count = 0;

    for trade in trades {
        let is_win = trade.pnl > 0.0;
        if is_win == wins {
            current_count += 1;
            if current_count > max_count {
                max_count = current_count;
            }
        } else {
            current_count = 0;
        }
    }

    max_count
}

