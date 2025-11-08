"""
Compara resultados Python vs Rust trade-by-trade

Uso:
    python comparar_engines.py <python_results.json> <rust_results.json>

Exemplo:
    python comparar_engines.py ../results/backtests/python/smoke_test_20251015.json \
                                ../results/backtests/rust/smoke_test_20251015.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple


def load_results(filepath: str) -> Dict:
    """Carrega arquivo JSON de resultados"""
    path = Path(filepath)
    if not path.exists():
        print(f"❌ ERRO: Arquivo não encontrado: {filepath}")
        sys.exit(1)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def compare_trades(python_trades: List[Dict], rust_trades: List[Dict], tolerance=1.0) -> Tuple[bool, str]:
    """
    Compara trades com tolerância de 1 ponto
    
    Args:
        python_trades: Lista de trades do Python
        rust_trades: Lista de trades do Rust
        tolerance: Tolerância em pontos (default: 1.0)
    
    Returns:
        (sucesso, mensagem)
    """
    disc repancies = []
    
    # Verificar número de trades
    if len(python_trades) != len(rust_trades):
        return False, f"❌ Número de trades diferente: Python={len(python_trades)}, Rust={len(rust_trades)}"
    
    if len(python_trades) == 0:
        return True, "⚠️ AVISO: Nenhum trade encontrado em ambos os engines (resultado válido)"
    
    # Comparar trade por trade
    for i, (pt, rt) in enumerate(zip(python_trades, rust_trades)):
        trade_num = i + 1
        
        # Comparar timestamps (±5 min = ±300s)
        try:
            pt_time = datetime.fromisoformat(pt.get('timestamp', pt.get('time', '')))
            rt_time = datetime.fromisoformat(rt.get('timestamp', rt.get('time', '')))
            time_diff = abs((pt_time - rt_time).total_seconds())
            
            if time_diff > 300:  # 5 minutos
                discrepancies.append(f"Trade #{trade_num}: Timestamp diff = {time_diff}s (Python: {pt_time}, Rust: {rt_time})")
        except (ValueError, KeyError) as e:
            discrepancies.append(f"Trade #{trade_num}: Erro ao comparar timestamps: {e}")
        
        # Comparar preços de entrada
        pt_price = pt.get('entry_price', pt.get('price', 0))
        rt_price = rt.get('entry_price', rt.get('price', 0))
        
        if abs(pt_price - rt_price) > tolerance:
            discrepancies.append(f"Trade #{trade_num}: Entry price diff = {abs(pt_price - rt_price):.2f} pts (Python: {pt_price}, Rust: {rt_price})")
        
        # Comparar SL
        pt_sl = pt.get('sl', pt.get('sl_price', 0))
        rt_sl = rt.get('sl', rt.get('sl_price', 0))
        
        if abs(pt_sl - rt_sl) > tolerance:
            discrepancies.append(f"Trade #{trade_num}: SL diff = {abs(pt_sl - rt_sl):.2f} pts (Python: {pt_sl}, Rust: {rt_sl})")
        
        # Comparar TP
        pt_tp = pt.get('tp', pt.get('tp_price', 0))
        rt_tp = rt.get('tp', rt.get('tp_price', 0))
        
        if abs(pt_tp - rt_tp) > tolerance:
            discrepancies.append(f"Trade #{trade_num}: TP diff = {abs(pt_tp - rt_tp):.2f} pts (Python: {pt_tp}, Rust: {rt_tp})")
        
        # Comparar PnL (se disponível)
        pt_pnl = pt.get('pnl_points', pt.get('pnl', None))
        rt_pnl = rt.get('pnl_points', rt.get('pnl', None))
        
        if pt_pnl is not None and rt_pnl is not None:
            if abs(pt_pnl - rt_pnl) > tolerance:
                discrepancies.append(f"Trade #{trade_num}: PnL diff = {abs(pt_pnl - rt_pnl):.2f} pts (Python: {pt_pnl}, Rust: {rt_pnl})")
        
        # Comparar ação (buy/sell)
        pt_action = pt.get('action', '').lower()
        rt_action = rt.get('action', '').lower()
        
        if pt_action != rt_action:
            discrepancies.append(f"Trade #{trade_num}: Action diff (Python: {pt_action}, Rust: {rt_action})")
    
    # Resultado final
    if discrepancies:
        return False, "❌ DISCREPÂNCIAS ENCONTRADAS:\n" + "\n".join(discrepancies)
    else:
        return True, f"✅ IDENTIDADE 100% VERIFICADA! ({len(python_trades)} trades comparados)"


def compare_metrics(python_results: Dict, rust_results: Dict) -> str:
    """Compara métricas gerais"""
    lines = []
    lines.append("\n📊 COMPARAÇÃO DE MÉTRICAS:")
    lines.append("=" * 60)
    
    # Trades totais
    py_trades = len(python_results.get('trades', []))
    ru_trades = len(rust_results.get('trades', []))
    lines.append(f"Total de trades: Python={py_trades}, Rust={ru_trades}")
    
    # Métricas (se disponíveis)
    py_metrics = python_results.get('metrics', {})
    ru_metrics = rust_results.get('metrics', {})
    
    for metric in ['win_rate', 'sharpe_ratio', 'max_drawdown', 'total_pnl']:
        if metric in py_metrics and metric in ru_metrics:
            py_val = py_metrics[metric]
            ru_val = ru_metrics[metric]
            diff = abs(py_val - ru_val)
            lines.append(f"{metric}: Python={py_val:.4f}, Rust={ru_val:.4f}, Diff={diff:.4f}")
    
    return "\n".join(lines)


def main():
    """Função principal"""
    print("=" * 80)
    print("🔬 COMPARADOR DE ENGINES - Python vs Rust")
    print("=" * 80)
    
    if len(sys.argv) < 3:
        print("\n❌ ERRO: Argumentos insuficientes")
        print("\nUso:")
        print("  python comparar_engines.py <python_results.json> <rust_results.json>")
        print("\nExemplo:")
        print("  python comparar_engines.py ../results/backtests/python/smoke_test.json \\")
        print("                              ../results/backtests/rust/smoke_test.json")
        sys.exit(1)
    
    python_file = sys.argv[1]
    rust_file = sys.argv[2]
    
    print(f"\n📂 Arquivos:")
    print(f"  Python: {python_file}")
    print(f"  Rust:   {rust_file}")
    
    # Carregar resultados
    print("\n📥 Carregando resultados...")
    try:
        python_results = load_results(python_file)
        rust_results = load_results(rust_file)
    except Exception as e:
        print(f"\n❌ ERRO ao carregar arquivos: {e}")
        sys.exit(1)
    
    print(f"  Python: {len(python_results.get('trades', []))} trades")
    print(f"  Rust:   {len(rust_results.get('trades', []))} trades")
    
    # Comparar trades
    print("\n🔍 Comparando trades...")
    identical, message = compare_trades(
        python_results.get('trades', []),
        rust_results.get('trades', [])
    )
    
    # Comparar métricas
    metrics_comparison = compare_metrics(python_results, rust_results)
    print(metrics_comparison)
    
    # Resultado final
    print("\n" + "=" * 80)
    if identical:
        print("✅ SUCESSO: Engines são idênticas!")
        print(message)
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ ERRO: Discrepâncias encontradas!")
        print(message)
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()

