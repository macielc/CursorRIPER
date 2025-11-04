"""
Teste Simplificado Python - Smoke Test 1 Dia
Carrega dados de 1 dia específico e roda estratégia Barra Elefante
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from pathlib import Path

# Teste standalone - sem imports de estratégia
# Implementação manual da lógica Barra Elefante

def load_month(year=2024, month=1):
    """Carrega dados de um mês completo"""
    print(f"\nCarregando dados de {month:02d}/{year}...")
    
    df = pd.read_csv('data/golden/WINFUT_M5_Golden_Data.csv')
    print(f"   Total rows in CSV: {len(df):,}")
    
    # Converter time para datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Filtrar apenas o mês desejado
    df_month = df[(df['time'].dt.year == year) & (df['time'].dt.month == month)].copy()
    
    # Filtrar apenas horário de pregão (9h-15h)
    df_month = df_month[(df_month['time'].dt.hour >= 9) & (df_month['time'].dt.hour <= 14)].copy()
    
    print(f"   Candles no mes {month:02d}/{year}: {len(df_month):,}")
    print(f"   Periodo: {df_month['time'].min()} ate {df_month['time'].max()}")
    
    if len(df_month) == 0:
        raise ValueError(f"Nenhum dado encontrado para {month:02d}/{year}")
    
    return df_month

def calculate_atr(df, period=14):
    """Calcula ATR manualmente"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr

def run_simple_backtest(df, params):
    """
    Backtest simplificado da estratégia Barra Elefante
    
    Parâmetros testados:
    - min_amplitude_mult: Multiplicador de amplitude para detectar elefante
    - min_volume_mult: Multiplicador de volume para detectar elefante
    - max_sombra_pct: % máxima de sombra (corpo deve ser 1-max_sombra)
    """
    print(f"\nRodando backtest com parametros:")
    for k, v in params.items():
        print(f"   {k}: {v}")
    
    # Calcular ATR
    df['atr_calc'] = calculate_atr(df, 14)
    
    # Adicionar amplitude e corpo se não existir
    if 'amplitude' not in df.columns:
        df['amplitude'] = df['high'] - df['low']
    if 'body' not in df.columns:
        df['body'] = abs(df['close'] - df['open'])
    
    # Médias móveis de amplitude e volume
    lookback_amp = params.get('lookback_amplitude', 25)
    lookback_vol = params.get('lookback_volume', 20)
    
    df['amplitude_ma'] = df['amplitude'].rolling(window=lookback_amp).mean()
    df['volume_ma'] = df['real_volume'].rolling(window=lookback_vol).mean()
    
    # Detectar barras elefante
    elefantes = []
    trades = []
    position = None
    
    for i in range(max(lookback_amp, lookback_vol) + 1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Se tem posição, verificar saída
        if position is not None:
            # Fechar no final do dia (12:15) ou por SL/TP
            if current['time'].hour >= 12 and current['time'].minute >= 15:
                # Fechar posição
                exit_price = current['close']
                pnl = (exit_price - position['entry_price']) if position['direction'] == 'BUY' else (position['entry_price'] - exit_price)
                
                trades.append({
                    'entry_time': position['entry_time'],
                    'entry_price': position['entry_price'],
                    'exit_time': current['time'],
                    'exit_price': exit_price,
                    'direction': position['direction'],
                    'pnl': pnl,
                    'exit_reason': 'INTRADAY_CLOSE'
                })
                position = None
                continue
            
            # Check SL/TP
            if position['direction'] == 'BUY':
                if current['low'] <= position['sl']:
                    trades.append({
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': current['time'],
                        'exit_price': position['sl'],
                        'direction': position['direction'],
                        'pnl': position['sl'] - position['entry_price'],
                        'exit_reason': 'SL'
                    })
                    position = None
                    continue
                elif current['high'] >= position['tp']:
                    trades.append({
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': current['time'],
                        'exit_price': position['tp'],
                        'direction': position['direction'],
                        'pnl': position['tp'] - position['entry_price'],
                        'exit_reason': 'TP'
                    })
                    position = None
                    continue
            else:  # SELL
                if current['high'] >= position['sl']:
                    trades.append({
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': current['time'],
                        'exit_price': position['sl'],
                        'direction': position['direction'],
                        'pnl': position['entry_price'] - position['sl'],
                        'exit_reason': 'SL'
                    })
                    position = None
                    continue
                elif current['low'] <= position['tp']:
                    trades.append({
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': current['time'],
                        'exit_price': position['tp'],
                        'direction': position['direction'],
                        'pnl': position['entry_price'] - position['tp'],
                        'exit_reason': 'TP'
                    })
                    position = None
                    continue
        
        # Se não tem posição, procurar entrada
        if position is None and i > 0:
            # Verificar se barra anterior (i-1) é elefante
            hora = prev['time'].hour
            minuto = prev['time'].minute
            
            # Filtro horário: 9:15 até 11:00
            if not (hora >= 9 and (hora < 11 or (hora == 11 and minuto == 0))):
                continue
            
            # Checar se é elefante
            amp_prev = prev['amplitude']
            vol_prev = prev['real_volume']
            amp_ma_prev = prev['amplitude_ma']
            vol_ma_prev = prev['volume_ma']
            
            if pd.isna(amp_ma_prev) or pd.isna(vol_ma_prev):
                continue
            
            # Filtros de elefante
            if amp_prev < amp_ma_prev * params['min_amplitude_mult']:
                continue
            
            if vol_prev < vol_ma_prev * params['min_volume_mult']:
                continue
            
            # Filtro de corpo (sombras pequenas)
            body_prev = prev['body']
            if amp_prev == 0:
                continue
            
            body_pct = body_prev / amp_prev
            required_body = 1.0 - params['max_sombra_pct']
            
            if body_pct < required_body:
                continue
            
            # ELEFANTE DETECTADO!
            is_bullish = prev['close'] > prev['open']
            
            # Verificar rompimento na barra ATUAL (i)
            if is_bullish:
                if current['high'] > prev['high']:
                    # COMPRA
                    entry_price = current['open']  # Simplificação: entra no open
                    atr = current['atr_calc']
                    
                    if not pd.isna(atr):
                        sl = entry_price - (atr * params['sl_atr_mult'])
                        tp = entry_price + (atr * params['tp_atr_mult'])
                        
                        position = {
                            'direction': 'BUY',
                            'entry_time': current['time'],
                            'entry_price': entry_price,
                            'sl': sl,
                            'tp': tp
                        }
                        
                        elefantes.append({
                            'time': prev['time'],
                            'direction': 'BULLISH',
                            'amplitude': amp_prev,
                            'volume': vol_prev,
                            'rompeu': True
                        })
            else:
                if current['low'] < prev['low']:
                    # VENDA
                    entry_price = current['open']
                    atr = current['atr_calc']
                    
                    if not pd.isna(atr):
                        sl = entry_price + (atr * params['sl_atr_mult'])
                        tp = entry_price - (atr * params['tp_atr_mult'])
                        
                        position = {
                            'direction': 'SELL',
                            'entry_time': current['time'],
                            'entry_price': entry_price,
                            'sl': sl,
                            'tp': tp
                        }
                        
                        elefantes.append({
                            'time': prev['time'],
                            'direction': 'BEARISH',
                            'amplitude': amp_prev,
                            'volume': vol_prev,
                            'rompeu': True
                        })
    
    # Calcular métricas
    if len(trades) == 0:
        return {
            'params': params,
            'total_trades': 0,
            'elefantes_detectados': len(elefantes),
            'win_rate': 0,
            'total_pnl': 0,
            'avg_trade': 0,
            'trades': []
        }
    
    wins = sum(1 for t in trades if t['pnl'] > 0)
    win_rate = wins / len(trades)
    total_pnl = sum(t['pnl'] for t in trades)
    avg_trade = total_pnl / len(trades)
    
    return {
        'params': params,
        'total_trades': len(trades),
        'elefantes_detectados': len(elefantes),
        'wins': wins,
        'losses': len(trades) - wins,
        'win_rate': win_rate,
        'total_pnl': total_pnl,
        'avg_trade': avg_trade,
        'trades': trades
    }

def main():
    print("="*80)
    print("TESTE PYTHON - JANEIRO 2024 COMPLETO")
    print("="*80)
    
    # Carregar dados de janeiro/2024
    df = load_month(year=2024, month=1)
    
    # Parâmetros EXATOS dos EAs do MT5
    params = {
        'min_amplitude_mult': 1.35,      # InpMinAmplitudeMult
        'min_volume_mult': 1.3,          # InpMinVolumeMult
        'max_sombra_pct': 0.30,          # InpMaxSombraPct
        'lookback_amplitude': 25,        # InpLookbackAmplitude
        'lookback_volume': 20,           # InpLookbackVolume
        'sl_atr_mult': 2.0,              # InpSL_ATR_Mult
        'tp_atr_mult': 3.0               # InpTP_ATR_Mult
    }
    
    print("\n" + "="*80)
    print("PARAMETROS DO MT5 (copie esses valores):")
    print("="*80)
    print("InpMinAmplitudeMult = 1.35")
    print("InpMinVolumeMult = 1.3")
    print("InpMaxSombraPct = 0.30")
    print("InpLookbackAmplitude = 25")
    print("InpLookbackVolume = 20")
    print("InpHoraInicio = 9")
    print("InpMinutoInicio = 15")
    print("InpHoraFim = 11")
    print("InpMinutoFim = 0")
    print("InpSL_ATR_Mult = 2.0")
    print("InpTP_ATR_Mult = 3.0")
    print("InpHoraFechamento = 12")
    print("InpMinutoFechamento = 15")
    print("="*80)
    
    # Rodar backtest
    result = run_simple_backtest(df, params)
    
    # Exibir resultados
    print("\n" + "="*80)
    print("RESULTADOS DO BACKTEST - JANEIRO 2024")
    print("="*80)
    print(f"\nPeriodo: Janeiro/2024 (01/01 a 31/01)")
    print(f"Candles processados: {len(df):,}")
    print(f"\nElefantes detectados: {result['elefantes_detectados']}")
    print(f"Total de trades: {result['total_trades']}")
    
    if result['total_trades'] > 0:
        print(f"Wins: {result['wins']}")
        print(f"Losses: {result['losses']}")
        print(f"Win Rate: {result['win_rate']:.1%}")
        print(f"Total PnL: {result['total_pnl']:.2f} pontos")
        print(f"Media por trade: {result['avg_trade']:.2f} pontos")
        
        # Converter para R$
        pnl_reais = result['total_pnl'] * 0.20  # WIN$ = R$ 0,20 por ponto
        print(f"Total PnL em R$: R$ {pnl_reais:,.2f}")
        
        print(f"\n{'='*80}")
        print("DETALHES DE TODOS OS TRADES:")
        print('='*80)
        for i, trade in enumerate(result['trades'], 1):
            entry_date = str(trade['entry_time']).split()[0]
            entry_time = str(trade['entry_time']).split()[1]
            exit_date = str(trade['exit_time']).split()[0]
            exit_time = str(trade['exit_time']).split()[1]
            
            pnl_reais_trade = trade['pnl'] * 0.20
            
            print(f"\nTrade #{i}: {trade['direction']}")
            print(f"  Entrada: {entry_date} {entry_time} @ {trade['entry_price']:.2f}")
            print(f"  Saida:   {exit_date} {exit_time} @ {trade['exit_price']:.2f}")
            print(f"  PnL: {trade['pnl']:+.2f} pontos (R$ {pnl_reais_trade:+.2f})")
            print(f"  Motivo: {trade['exit_reason']}")
        print('='*80)
    else:
        print("\n*** Nenhum trade executado em janeiro/2024 ***")
        print("Isso pode significar:")
        print("  - Parametros muito restritivos")
        print("  - Poucos elefantes no periodo")
        print("  - Horario de entrada muito limitado (9:15-11:00)")
    
    # Salvar resultado
    output_file = f'results/backtest_python_jan2024.json'
    Path('results').mkdir(exist_ok=True)
    
    # Converter trades para formato serializável
    result_copy = result.copy()
    for trade in result_copy['trades']:
        trade['entry_time'] = str(trade['entry_time'])
        trade['exit_time'] = str(trade['exit_time'])
    
    with open(output_file, 'w') as f:
        json.dump(result_copy, f, indent=2)
    
    print(f"\nResultado salvo em: {output_file}")
    print("\n" + "="*80)

if __name__ == '__main__':
    main()

