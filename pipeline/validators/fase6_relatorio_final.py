"""
FASE 6: RELATORIO FINAL

Consolida resultados de todas as fases e gera decisão final.
"""
import json
from pathlib import Path
from datetime import datetime


def gerar_relatorio_final(strategy_name: str):
    """
    Consolida resultados de todas as fases
    
    Args:
        strategy_name: Nome da estratégia
    
    Returns:
        Dict com decisão final
    """
    print("\n" + "="*80)
    print("FASE 6: RELATORIO FINAL")
    print("="*80 + "\n")
    
    results_dir = Path('results')
    
    # Carregar resultados de cada fase
    fase3_files = sorted(results_dir.glob(f'fase3_walkforward_{strategy_name}_*.json'))
    fase4_files = sorted(results_dir.glob(f'fase4_oos_{strategy_name}_*.json'))
    fase5_files = sorted(results_dir.glob(f'fase5_outliers_{strategy_name}_*.json'))
    
    if not fase3_files or not fase4_files or not fase5_files:
        print("ERRO: Execute todas as fases primeiro!")
        print(f"  Fase 3 (Walk-Forward): {'OK' if fase3_files else 'FALTANDO'}")
        print(f"  Fase 4 (Out-of-Sample): {'OK' if fase4_files else 'FALTANDO'}")
        print(f"  Fase 5 (Outlier Analysis): {'OK' if fase5_files else 'FALTANDO'}")
        return None
    
    # Carregar últimos resultados
    with open(fase3_files[-1], 'r') as f:
        fase3 = json.load(f)
    
    with open(fase4_files[-1], 'r') as f:
        fase4 = json.load(f)
    
    with open(fase5_files[-1], 'r') as f:
        fase5 = json.load(f)
    
    # Verificar trades mínimos
    top_50_files = sorted(Path('results/optimization').glob('top_50_*.json'), 
                          key=lambda p: p.stat().st_mtime)
    with open(top_50_files[-1], 'r') as f:
        data = json.load(f)
        results = data['top_50'] if 'top_50' in data else data
        melhor = sorted(results, key=lambda x: x['sharpe_ratio'], reverse=True)[0]
        total_trades = melhor['total_trades']
    
    criterio_trades = total_trades >= 50
    
    # Contabilizar critérios (garantir que são booleans)
    criterios = {
        'walk_forward': bool(fase3.get('aprovado', False)),
        'out_of_sample': bool(fase4.get('aprovado', False)),
        'outlier_analysis': bool(fase5.get('aprovado', False)),
        'trades_suficientes': bool(criterio_trades)
    }
    
    aprovados = sum(1 for v in criterios.values() if v)
    decisao_final = aprovados >= 3
    
    print(f"ESTRATEGIA: {strategy_name}")
    print(f"Total de trades: {total_trades}\n")
    
    print("RESULTADOS POR CRITERIO:")
    print("-" * 80)
    print(f"[{'OK' if criterios['walk_forward'] else 'FAIL'}] Walk-Forward Analysis")
    if criterios['walk_forward'] and fase3:
        print(f"     Sharpe medio: {fase3.get('sharpe_medio', 0):.2f}")
        janelas_pos = fase3.get('janelas_positivas', 0)
        total_janelas = fase3.get('total_janelas', 1)
        pct_pos = fase3.get('pct_positivas', 0)
        print(f"     Janelas positivas: {janelas_pos}/{total_janelas} ({pct_pos:.0f}%)")
    
    print(f"\n[{'OK' if criterios['out_of_sample'] else 'FAIL'}] Out-of-Sample Test")
    if criterios['out_of_sample'] and fase4:
        print(f"     Trades: {fase4.get('trades', 0)}")
        print(f"     Sharpe: {fase4.get('sharpe', 0):.2f}")
    
    print(f"\n[{'OK' if criterios['outlier_analysis'] else 'FAIL'}] Outlier Analysis")
    if 'sharpe_original' in fase5 and 'sharpe_sem_outliers' in fase5:
        print(f"     Sharpe original: {fase5['sharpe_original']:.2f}")
        print(f"     Sharpe sem outliers: {fase5['sharpe_sem_outliers']:.2f}")
        print(f"     Degradacao: {fase5.get('degradacao_pct', 0):.1f}%")
    else:
        print(f"     Sharpe: {fase5.get('sharpe_sem_outliers', fase5.get('sharpe', 0)):.2f}")
        if 'trades_removidos' in fase5:
            print(f"     Trades removidos: {fase5['trades_removidos']}")
    
    print(f"\n[{'OK' if criterios['trades_suficientes'] else 'FAIL'}] Trades Suficientes (>= 50)")
    print(f"     Total: {total_trades} trades")
    
    print("\n" + "="*80)
    print(f"CRITERIOS APROVADOS: {aprovados}/4")
    print("="*80 + "\n")
    
    if decisao_final:
        print("DECISAO FINAL: APROVADO PARA LIVE TRADING")
        
        # Ressalvas
        if not criterios['outlier_analysis']:
            print("\nRESSALVAS:")
            print("  - Estrategia DEPENDE de trades extremos")
            print("  - Recomendado: Paper trading com gestao conservadora")
    else:
        print("DECISAO FINAL: REJEITADO")
        print("\nMOTIVOS:")
        for nome, passou in criterios.items():
            if not passou:
                print(f"  - {nome.replace('_', ' ').title()}")
    
    # Salvar relatório
    relatorio = {
        'estrategia': strategy_name,
        'timestamp': datetime.now().isoformat(),
        'total_trades': total_trades,
        'criterios': criterios,
        'aprovados': aprovados,
        'decisao_final': 'APROVADO' if decisao_final else 'REJEITADO',
        'fase3': fase3,
        'fase4': fase4,
        'fase5': fase5
    }
    
    output_file = Path(f'results/RELATORIO_FINAL_{strategy_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(output_file, 'w') as f:
        json.dump(relatorio, f, indent=2, default=str)
    
    print(f"\nRelatorio completo salvo: {output_file}")
    
    return relatorio


def main():
    # Detectar estratégia do último resultado
    results_dir = Path('results/optimization')
    top_50_files = sorted(results_dir.glob('top_50_*.json'), key=lambda p: p.stat().st_mtime)
    
    if not top_50_files:
        print("ERRO: Execute primeiro a otimizacao!")
        return
    
    with open(top_50_files[-1], 'r') as f:
        data = json.load(f)
    
    strategy_name = data.get('strategy')
    
    if not strategy_name:
        print("ERRO: Nome da estrategia nao encontrado!")
        return
    
    gerar_relatorio_final(strategy_name)


if __name__ == '__main__':
    main()

