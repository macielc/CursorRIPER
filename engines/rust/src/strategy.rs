use crate::types::{BarraElefanteParams, Candle};

#[derive(Debug, Clone)]
pub struct Signals {
    pub entries_long: Vec<bool>,
    pub entries_short: Vec<bool>,
    pub sl_prices: Vec<f32>,  // Será 0.0, calculado dinamicamente no backtest
    pub tp_prices: Vec<f32>,  // Será 0.0, calculado dinamicamente no backtest
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
        
        // Calcular médias
        let mut amplitude_medias = rolling_mean(&amplitudes, lookback);
        let volumes: Vec<f32> = candles.iter().map(|c| c.volume).collect();
        let mut volume_medios = rolling_mean(&volumes, lookback);
        
        // SHIFT DE 1: Usar média ATÉ barra anterior (não incluir barra atual)
        // Igual Python: np.roll(amplitude_media, 1)
        shift_right(&mut amplitude_medias);
        shift_right(&mut volume_medios);
        
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
        
        // SHIFT DE 1: Usar média ATÉ barra anterior
        shift_right(&mut temp_amp_med);
        shift_right(&mut temp_vol_med);
        
        amplitudes = &temp_amp;
        corpos = &temp_corp;
        amplitude_medias = &temp_amp_med;
        volume_medios = &temp_vol_med;
    }

    // SEQUENCIAL: Paralelismo acontece NO OPTIMIZER, nao aqui!
    let results: Vec<_> = (lookback..n)
        .map(|i| {
            let entry_long = false;
            let entry_short = false;
            let sl = 0.0;
            let tp = 0.0;

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

            // VERIFICAR ROMPIMENTO NA PRÓXIMA BARRA (igual Python!)
            if i + 1 >= n {
                return (i, entry_long, entry_short, sl, tp);
            }

            // Barra de ALTA: verificar se próxima rompe a máxima
            if is_bullish {
                let maxima_elefante = candles[i].high;
                if candles[i + 1].high > maxima_elefante {
                    // Verificar horário da barra de ENTRADA (i+1)
                    if check_horario(
                        candles[i + 1].hour,
                        candles[i + 1].minute,
                        params.horario_inicio,
                        params.minuto_inicio,
                        params.horario_fim,
                        params.minuto_fim,
                    ) {
                        // Marcar sinal na barra de rompimento (i+1)
                        // MAS retornar o índice i (loop está em i, e o sinal será aplicado em i+1 depois)
                        // Precisamos retornar i+1 para marcar corretamente
                        return (i + 1, true, false, sl, tp);
                    }
                }
            }
            // Barra de BAIXA: verificar se próxima rompe a mínima
            else if is_bearish {
                let minima_elefante = candles[i].low;
                if candles[i + 1].low < minima_elefante {
                    // Verificar horário da barra de ENTRADA (i+1)
                    if check_horario(
                        candles[i + 1].hour,
                        candles[i + 1].minute,
                        params.horario_inicio,
                        params.minuto_inicio,
                        params.horario_fim,
                        params.minuto_fim,
                    ) {
                        // Marcar sinal na barra de rompimento (i+1)
                        return (i + 1, false, true, sl, tp);
                    }
                }
            }

            (i, entry_long, entry_short, sl, tp)
        })
        .collect();

    // Aplicar resultados (usar |= para não sobrescrever sinais já marcados)
    for (i, entry_long, entry_short, sl, tp) in results {
        entries_long[i] |= entry_long;  // OR: preserva sinais anteriores
        entries_short[i] |= entry_short;
        if sl > 0.0 {
            sl_prices[i] = sl;
        }
        if tp > 0.0 {
            tp_prices[i] = tp;
        }
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

/// Shift direita (roll) - move todos elementos 1 posição para direita
/// Primeiro elemento vira 0.0 (igual Python: np.roll + [0] = 0.0)
fn shift_right(data: &mut [f32]) {
    if data.len() == 0 {
        return;
    }
    
    // Shift: mover todos para direita
    for i in (1..data.len()).rev() {
        data[i] = data[i - 1];
    }
    
    // Primeiro elemento = 0.0
    data[0] = 0.0;
}

