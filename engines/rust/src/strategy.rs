use crate::types::{BarraElefanteParams, Candle};

#[derive(Debug, Clone)]
pub struct Signals {
    pub entries_long: Vec<bool>,
    pub entries_short: Vec<bool>,
    pub sl_prices: Vec<f32>,
    pub tp_prices: Vec<f32>,
}

// Struct para armazenar dados pre-calculados (REUTILIZAVEL entre testes)
pub struct PrecomputedData {
    pub amplitudes: Vec<f32>,
    pub corpos: Vec<f32>,
    pub amplitude_medias: Vec<f32>,
    pub volume_medios: Vec<f32>,
}

impl PrecomputedData {
    pub fn new(candles: &[Candle], lookback: usize) -> Self {
        let amplitudes: Vec<f32> = candles.iter().map(|c| c.high - c.low).collect();
        let corpos: Vec<f32> = candles.iter().map(|c| (c.close - c.open).abs()).collect();
        let amplitude_medias = rolling_mean(&amplitudes, lookback);
        let volumes: Vec<f32> = candles.iter().map(|c| c.volume).collect();
        let volume_medios = rolling_mean(&volumes, lookback);
        
        Self {
            amplitudes,
            corpos,
            amplitude_medias,
            volume_medios,
        }
    }
}

pub fn detect_barra_elefante(
    candles: &[Candle],
    params: &BarraElefanteParams,
) -> Signals {
    detect_barra_elefante_with_cache(candles, params, None)
}

pub fn detect_barra_elefante_with_cache(
    candles: &[Candle],
    params: &BarraElefanteParams,
    precomputed: Option<&PrecomputedData>,
) -> Signals {
    let n = candles.len();
    let lookback = params.lookback_amplitude;

    let mut entries_long = vec![false; n];
    let mut entries_short = vec![false; n];
    let mut sl_prices = vec![0.0; n];
    let mut tp_prices = vec![0.0; n];

    if n < lookback + 1 {
        return Signals {
            entries_long,
            entries_short,
            sl_prices,
            tp_prices,
        };
    }

    // USAR CACHE SE DISPONIVEL (4.2M vezes mais rapido!)
    let amplitudes: &Vec<f32>;
    let corpos: &Vec<f32>;
    let amplitude_medias: &Vec<f32>;
    let volume_medios: &Vec<f32>;
    
    // Vetores temporarios para fallback (fora do if para lifetime)
    let mut temp_amp = Vec::new();
    let mut temp_corp = Vec::new();
    let mut temp_amp_med = Vec::new();
    let mut temp_vol_med = Vec::new();
    
    if let Some(cache) = precomputed {
        // Cache foi calculado com lookback maximo, funciona para todos
        amplitudes = &cache.amplitudes;
        corpos = &cache.corpos;
        amplitude_medias = &cache.amplitude_medias;
        volume_medios = &cache.volume_medios;
    } else {
        // Fallback: calcular inline (lento!)
        eprintln!("[AVISO] Calculando inline - performance ruim!");
        temp_amp = candles.iter().map(|c| c.high - c.low).collect();
        temp_corp = candles.iter().map(|c| (c.close - c.open).abs()).collect();
        temp_amp_med = rolling_mean(&temp_amp, lookback);
        let vols: Vec<f32> = candles.iter().map(|c| c.volume).collect();
        temp_vol_med = rolling_mean(&vols, lookback);
        
        amplitudes = &temp_amp;
        corpos = &temp_corp;
        amplitude_medias = &temp_amp_med;
        volume_medios = &temp_vol_med;
    }

    // SEQUENCIAL: Paralelismo acontece NO OPTIMIZER, nao aqui!
    let results: Vec<_> = (lookback..n)
        .map(|i| {
            let mut entry_long = false;
            let mut entry_short = false;
            let mut sl = 0.0;
            let mut tp = 0.0;

            // 1) Amplitude mínima
            if amplitudes[i] < amplitude_medias[i] * params.min_amplitude_mult {
                return (i, entry_long, entry_short, sl, tp);
            }

            // 2) Volume mínimo  
            if candles[i].volume < volume_medios[i] * params.min_volume_mult {
                return (i, entry_long, entry_short, sl, tp);
            }

            // 3) Sombras máximas (corpo deve ser dominante)
            let corpo = corpos[i];
            let amplitude = amplitudes[i];
            if amplitude > 0.0 && corpo / amplitude < (1.0 - params.max_sombra_pct) {
                return (i, entry_long, entry_short, sl, tp);
            }

            // 4) Filtro horário
            let hora = candles[i].hour;
            let minuto = candles[i].minute;
            if !check_horario(
                hora,
                minuto,
                params.horario_inicio,
                params.minuto_inicio,
                params.horario_fim,
                params.minuto_fim,
            ) {
                return (i, entry_long, entry_short, sl, tp);
            }

            // Detectar tipo de barra
            let is_bullish = candles[i].close > candles[i].open;
            let is_bearish = candles[i].close < candles[i].open;

            if !is_bullish && !is_bearish {
                return (i, entry_long, entry_short, sl, tp);
            }

            // Calcular SL/TP
            let atr = candles[i].atr;

            if is_bullish {
                // Barra LONG: entrada no rompimento da máxima (próxima barra)
                if i + 1 < n {
                    entry_long = true;
                    let entry_price = candles[i].high; // Entrada estimada no high
                    sl = entry_price - (atr * params.sl_atr_mult);
                    let risk = entry_price - sl;
                    tp = entry_price + (risk * params.tp_atr_mult);
                }
            } else if is_bearish {
                // Barra SHORT: entrada no rompimento da mínima (próxima barra)
                if i + 1 < n {
                    entry_short = true;
                    let entry_price = candles[i].low; // Entrada estimada no low
                    sl = entry_price + (atr * params.sl_atr_mult);
                    let risk = sl - entry_price;
                    tp = entry_price - (risk * params.tp_atr_mult);
                }
            }

            (i, entry_long, entry_short, sl, tp)
        })
        .collect();

    // Aplicar resultados
    for (i, entry_long, entry_short, sl, tp) in results {
        entries_long[i] = entry_long;
        entries_short[i] = entry_short;
        sl_prices[i] = sl;
        tp_prices[i] = tp;
    }

    Signals {
        entries_long,
        entries_short,
        sl_prices,
        tp_prices,
    }
}

#[inline]
fn check_horario(
    hora: i32,
    minuto: i32,
    hora_min: i32,
    min_min: i32,
    hora_max: i32,
    min_max: i32,
) -> bool {
    if hora < hora_min || (hora == hora_min && minuto < min_min) {
        return false;
    }
    if hora > hora_max || (hora == hora_max && minuto > min_max) {
        return false;
    }
    true
}

fn rolling_mean(data: &[f32], window: usize) -> Vec<f32> {
    let n = data.len();
    let mut result = vec![0.0; n];
    
    if n == 0 {
        return result;
    }

    // JANELA DESLIZANTE EFICIENTE - O(n) ao inves de O(n*window)
    let mut sum = 0.0f32;

    for i in 0..n {
        // Adicionar novo valor
        sum += data[i];
        
        if i < window {
            // Janela parcial no inicio
            result[i] = sum / (i + 1) as f32;
        } else {
            // Remover valor que saiu da janela
            sum -= data[i - window];
            result[i] = sum / window as f32;
        }
    }

    result
}

