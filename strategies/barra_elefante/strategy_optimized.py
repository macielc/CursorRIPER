"""
BARRA ELEFANTE - VERSÃO ULTRA OTIMIZADA
Todas as otimizações Numba implementadas
"""

import numpy as np
import pandas as pd
from typing import Dict
from core.strategy_base import StrategyBase
from numba import njit, prange, vectorize, float32, float64, int64, boolean, set_num_threads

# Limitar a 1 thread por worker
set_num_threads(1)


# ============================================================================
# OTIMIZAÇÃO 1: @vectorize para cálculos elemento-a-elemento
# ============================================================================

@vectorize(['float32(float32, float32)'], target='parallel', cache=True)
def calc_amplitude_vec(high, low):
    """Calcula amplitude vetorizada (PARALELO)"""
    return high - low


@vectorize(['float32(float32, float32)'], target='parallel', cache=True)
def calc_corpo_vec(close_price, open_price):
    """Calcula corpo vetorizada (PARALELO)"""
    if close_price >= open_price:
        return close_price - open_price
    else:
        return open_price - close_price


# ============================================================================
# OTIMIZAÇÃO 2: Funções inline para reduzir overhead
# ============================================================================

@njit(inline='always')
def check_amplitude(amp, amp_media, min_mult):
    """Check amplitude inline (sem overhead de chamada)"""
    return amp >= amp_media * min_mult


@njit(inline='always')
def check_volume(vol, vol_media, min_mult):
    """Check volume inline"""
    return vol >= vol_media * min_mult


@njit(inline='always')
def check_horario(hora, minuto, hora_min, min_min, hora_max, min_max):
    """Check horário inline"""
    # Antes do início
    if hora < hora_min or (hora == hora_min and minuto < min_min):
        return False
    # Depois do fim
    if hora > hora_max or (hora == hora_max and minuto > min_max):
        return False
    return True


# ============================================================================
# OTIMIZAÇÃO 3: Função principal com parallel=True e prange
# ============================================================================

@njit(
    # OTIMIZAÇÃO 4: Signature para tipos explícitos
    'Tuple((boolean[:], boolean[:]))(float32[:], float32[:], float32[:], float32[:], '
    'float32[:], float32[:], float32[:], float32[:], float32[:], '
    'int64[:], int64[:], int64, int64, float32, float32, float32, '
    'int64, int64, int64, int64)',
    parallel=False,  # DESATIVADO: Causa deadlock com multiprocessing
    cache=True,
    fastmath=True,
    nogil=True
)
def _detect_elephant_bars_ultra_optimized(
    high, low, close_arr, open_arr, amplitude, amplitude_media, corpo, 
    volume, volume_media, horas, minutos, n, lookback, 
    min_amp_mult, min_vol_mult, max_sombra_pct,
    hora_inicio, min_inicio, hora_fim, min_fim
):
    """
    VERSÃO ULTRA OTIMIZADA COM PARALELIZAÇÃO
    
    Otimizações:
    - parallel=True: Loop paralelizado
    - prange: Divide trabalho entre threads
    - Signature: Tipos explícitos
    - fastmath: Matemática rápida
    - nogil: Sem GIL
    - Inline functions: Sem overhead
    """
    # Pre-alocar arrays de saída
    entries_long = np.zeros(n, dtype=np.bool_)
    entries_short = np.zeros(n, dtype=np.bool_)
    
    # LOOP PARALELIZADO com prange
    for i in prange(lookback, n - 1):  # prange ao invés de range!
        # 1) Check amplitude (inline)
        if not check_amplitude(amplitude[i], amplitude_media[i], min_amp_mult):
            continue
        
        # 2) Check volume (inline)
        if not check_volume(volume[i], volume_media[i], min_vol_mult):
            continue
        
        # 3) DOJI: bloquear
        if corpo[i] < 1.0:
            continue
        
        # 4) Corpo grande (poucas sombras)
        if amplitude[i] > 0.0:
            pct_corpo = corpo[i] / amplitude[i]
            if pct_corpo < (1.0 - max_sombra_pct):
                continue
        else:
            continue
        
        # 5) Filtro horário (inline)
        if not check_horario(horas[i], minutos[i], hora_inicio, min_inicio, hora_fim, min_fim):
            continue
        
        # 6) Gerar sinal
        close_i = close_arr[i]
        open_i = open_arr[i]
        
        # Barra de ALTA
        if close_i > open_i:
            maxima_elefante = high[i]
            if high[i+1] > maxima_elefante:
                # Check horário entrada
                if check_horario(horas[i+1], minutos[i+1], hora_inicio, min_inicio, hora_fim, min_fim):
                    entries_long[i+1] = True
        
        # Barra de BAIXA
        elif close_i < open_i:
            minima_elefante = low[i]
            if low[i+1] < minima_elefante:
                # Check horário entrada
                if check_horario(horas[i+1], minutos[i+1], hora_inicio, min_inicio, hora_fim, min_fim):
                    entries_short[i+1] = True
    
    return entries_long, entries_short


# ============================================================================
# OTIMIZAÇÃO 5: Loop unrolling para moving average
# ============================================================================

@njit(cache=True, fastmath=True)
def moving_average_unrolled(arr, window):
    """Moving average com loop unrolling"""
    n = len(arr)
    result = np.empty(n, dtype=np.float32)
    result[:window] = np.nan
    
    # Primeira janela
    soma = np.float32(0.0)
    for i in range(window):
        soma += arr[i]
    result[window] = soma / window
    
    # Rolling com unrolling (processar 4 por vez)
    i = window + 1
    while i <= n - 4:
        # Remover 4 antigos, adicionar 4 novos
        soma = soma - arr[i-window-3] - arr[i-window-2] - arr[i-window-1] - arr[i-window]
        soma = soma + arr[i] + arr[i+1] + arr[i+2] + arr[i+3]
        result[i] = soma / window
        result[i+1] = (soma - arr[i] + arr[i+1]) / window
        result[i+2] = (soma - arr[i+1] + arr[i+2]) / window
        result[i+3] = (soma - arr[i+2] + arr[i+3]) / window
        i += 4
    
    # Processar resto
    while i < n:
        soma = soma - arr[i-window] + arr[i]
        result[i] = soma / window
        i += 1
    
    return result


# ============================================================================
# Warm-up
# ============================================================================

def warmup_numba():
    """Pre-compilar todas as funções"""
    n = 100
    high = np.random.rand(n).astype(np.float32) * 100 + 100000
    low = (high - np.random.rand(n).astype(np.float32) * 50)
    close_arr = (low + np.random.rand(n).astype(np.float32) * (high - low))
    open_arr = (low + np.random.rand(n).astype(np.float32) * (high - low))
    
    # Vetorizado
    amplitude = calc_amplitude_vec(high, low)
    corpo = calc_corpo_vec(close_arr, open_arr)
    
    # Moving average
    amplitude_media = moving_average_unrolled(amplitude, 20)
    volume = np.random.rand(n).astype(np.float32) * 1000
    volume_media = moving_average_unrolled(volume, 20)
    
    horas = np.random.randint(9, 15, n, dtype=np.int64)
    minutos = np.random.randint(0, 59, n, dtype=np.int64)
    
    # Detectar (paralelo)
    _detect_elephant_bars_ultra_optimized(
        high, low, close_arr, open_arr, amplitude, amplitude_media, corpo,
        volume, volume_media, horas, minutos, n, 20,
        np.float32(2.0), np.float32(1.5), np.float32(0.3),
        9, 0, 14, 0
    )
    
    print("[NUMBA] Compilação ultra-otimizada concluída!")


print("[NUMBA] Módulo otimizado carregado (parallel + vectorize + inline + unrolling)")

