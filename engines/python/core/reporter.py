"""
Gerador de Relatórios

Gera relatórios detalhados em texto e markdown
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ReportGenerator:
    """
    Gera relatórios de validação de estratégias
    """
    
    def __init__(self, output_dir: str = '../reports'):
        """
        Args:
            output_dir: Diretório para salvar relatórios
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_optimization_report(
        self,
        results_df: pd.DataFrame,
        param_grid: Dict,
        total_tests: int,
        duration_minutes: float
    ) -> str:
        """
        Gera relatório de otimização
        
        Returns:
            Path do relatório gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f'optimization_report_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# RELATORIO DE OTIMIZACAO\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Resumo Executivo
            f.write("## RESUMO EXECUTIVO\n\n")
            f.write(f"- **Testes executados:** {total_tests:,}\n")
            f.write(f"- **Duracao:** {duration_minutes:.1f} minutos\n")
            if duration_minutes > 0:
                f.write(f"- **Velocidade:** {total_tests/duration_minutes:.1f} testes/min\n")
            else:
                f.write(f"- **Velocidade:** >1000 testes/min (muito rapido!)\n")
            f.write(f"- **Setups validos:** {len(results_df):,}\n\n")
            
            # Grid de Parâmetros
            f.write("## GRID DE PARAMETROS\n\n")
            f.write("```\n")
            for param, values in param_grid.items():
                if hasattr(values, '__len__'):
                    f.write(f"{param}: {len(values)} valores\n")
            f.write("```\n\n")
            
            # Top 10
            f.write("## TOP 10 SETUPS\n\n")
            
            if len(results_df) > 0:
                top_10 = results_df.head(10)
                
                for idx, (i, row) in enumerate(top_10.iterrows(), 1):
                    f.write(f"### {idx}. Setup #{i}\n\n")
                    f.write("**Metricas:**\n")
                    f.write(f"- Score: {row['score']:.2f}\n")
                    f.write(f"- Sharpe Ratio: {row['sharpe_ratio']:.2f}\n")
                    f.write(f"- Total Return: {row['total_return']:.2f} ({row['total_return_pct']:.2f}%)\n")
                    f.write(f"- Win Rate: {row['win_rate']:.1%}\n")
                    f.write(f"- Profit Factor: {row['profit_factor']:.2f}\n")
                    f.write(f"- Max Drawdown: {row['max_drawdown']:.2f} ({row['max_drawdown_pct']:.1f}%)\n")
                    f.write(f"- Total Trades: {row['total_trades']}\n\n")
                    
                    f.write("**Parametros:**\n")
                    params = row['params']
                    for k, v in params.items():
                        if isinstance(v, float):
                            f.write(f"- {k}: {v:.2f}\n")
                        else:
                            f.write(f"- {k}: {v}\n")
                    f.write("\n")
            
            # Distribuição de Métricas
            f.write("## DISTRIBUICAO DE METRICAS\n\n")
            
            metrics = ['sharpe_ratio', 'win_rate', 'profit_factor', 'total_return_pct']
            
            for metric in metrics:
                if metric in results_df.columns:
                    f.write(f"**{metric}:**\n")
                    f.write(f"- Media: {results_df[metric].mean():.2f}\n")
                    f.write(f"- Mediana: {results_df[metric].median():.2f}\n")
                    f.write(f"- Std: {results_df[metric].std():.2f}\n")
                    f.write(f"- Min: {results_df[metric].min():.2f}\n")
                    f.write(f"- Max: {results_df[metric].max():.2f}\n\n")
            
            f.write("---\n")
            f.write("*Gerado automaticamente pelo MacTester*\n")
        
        print(f"Relatorio salvo em: {report_file}")
        return str(report_file)
    
    def generate_permutation_report(
        self,
        results: List[Dict],
        output_name: str = "permutation_report"
    ) -> str:
        """
        Gera relatório de testes de permutação
        
        Returns:
            Path do relatório gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f'{output_name}_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# RELATORIO DE TESTE DE PERMUTACAO\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Resumo
            significant_count = sum(
                1 for r in results 
                if r.get('success') and 
                r['significance']['sharpe'] and 
                r['significance']['total_return']
            )
            
            f.write("## RESUMO EXECUTIVO\n\n")
            f.write(f"- **Setups testados:** {len(results)}\n")
            f.write(f"- **Setups significativos:** {significant_count}\n")
            f.write(f"- **Taxa de aprovacao:** {significant_count/len(results):.1%}\n\n")
            
            # Resultados individuais
            f.write("## RESULTADOS INDIVIDUAIS\n\n")
            
            for i, result in enumerate(results, 1):
                if not result.get('success'):
                    f.write(f"### Setup {i}: FALHOU\n")
                    f.write(f"Erro: {result.get('error', 'Desconhecido')}\n\n")
                    continue
                
                f.write(f"### Setup {i}\n\n")
                
                # Métricas reais
                real = result['real_metrics']
                f.write("**Metricas Reais:**\n")
                f.write(f"- Sharpe: {real['sharpe']:.2f}\n")
                f.write(f"- Return: {real['total_return']:.2f}\n")
                f.write(f"- Win Rate: {real['win_rate']:.1%}\n")
                f.write(f"- Trades: {real['total_trades']}\n\n")
                
                # P-values
                pvals = result['p_values']
                sig = result['significance']
                
                f.write("**Teste de Permutacao:**\n")
                f.write(f"- Sharpe: p={pvals['sharpe']:.4f} ")
                f.write("[OK] SIGNIFICATIVO\n" if sig['sharpe'] else "[X] NAO SIGNIFICATIVO\n")
                
                f.write(f"- Return: p={pvals['total_return']:.4f} ")
                f.write("[OK] SIGNIFICATIVO\n" if sig['total_return'] else "[X] NAO SIGNIFICATIVO\n")
                
                f.write(f"- Win Rate: p={pvals['win_rate']:.4f} ")
                f.write("[OK] SIGNIFICATIVO\n" if sig['win_rate'] else "[X] NAO SIGNIFICATIVO\n")
                
                f.write(f"\n**Conclusao:** ")
                if sig['sharpe'] and sig['total_return']:
                    f.write("APROVADO - Metricas sao estatisticamente significativas\n\n")
                else:
                    f.write("REPROVADO - Resultados podem ser aleatorios\n\n")
            
            f.write("---\n")
            f.write("*Gerado automaticamente pelo MacTester*\n")
        
        print(f"Relatorio salvo em: {report_file}")
        return str(report_file)
    
    def generate_walkforward_report(
        self,
        analysis_results: Dict,
        output_name: str = "walkforward_report"
    ) -> str:
        """
        Gera relatório de walk-forward analysis
        
        Returns:
            Path do relatório gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f'{output_name}_{timestamp}.md'
        
        summary = analysis_results['summary']
        windows = analysis_results['windows']
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# RELATORIO DE WALK-FORWARD ANALYSIS\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Resumo
            f.write("## RESUMO EXECUTIVO\n\n")
            f.write(f"- **Total de janelas:** {summary['total_windows']}\n")
            f.write(f"- **Janelas validas:** {summary['successful_windows']}\n")
            f.write(f"- **Taxa de sucesso:** {summary['success_rate']:.1%}\n\n")
            
            f.write("**Performance Out-of-Sample (media):**\n")
            f.write(f"- Sharpe OOS: {summary['avg_oos_sharpe']:.2f}\n")
            f.write(f"- Return OOS: {summary['avg_oos_return']:.2f}\n")
            f.write(f"- Win Rate OOS: {summary['avg_oos_wr']:.1%}\n\n")
            
            f.write("**Degradacao (IS -> OOS):**\n")
            f.write(f"- Degradacao Sharpe: {summary['degradation_sharpe']:.1%}\n")
            f.write(f"- Degradacao Return: {summary['degradation_return']:.1%}\n\n")
            
            # Janelas individuais
            f.write("## RESULTADOS POR JANELA\n\n")
            
            for i, window in enumerate(windows, 1):
                f.write(f"### Janela {i}\n\n")
                
                if not window['success']:
                    f.write("**Status:** FALHOU\n\n")
                    continue
                
                f.write(f"**Periodo de Treino:** {window['train_start'].date()} ate {window['train_end'].date()}\n")
                f.write(f"**Periodo de Teste:** {window['test_start'].date()} ate {window['test_end'].date()}\n\n")
                
                f.write(f"**Performance OOS:**\n")
                f.write(f"- Sharpe: {window['avg_oos_sharpe']:.2f}\n")
                f.write(f"- Return: {window['avg_oos_return']:.2f}\n")
                f.write(f"- Win Rate: {window['avg_oos_wr']:.1%}\n\n")
            
            f.write("---\n")
            f.write("*Gerado automaticamente pelo MacTester*\n")
        
        print(f"Relatorio salvo em: {report_file}")
        return str(report_file)
    
    def generate_final_report(
        self,
        strategy_name: str,
        best_setup: Dict,
        optimization_summary: Dict,
        permutation_result: Dict,
        walkforward_summary: Optional[Dict] = None
    ) -> str:
        """
        Gera relatório final consolidado
        
        Returns:
            Path do relatório gerado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f'final_report_{strategy_name}_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# RELATORIO FINAL - {strategy_name.upper()}\n\n")
            f.write(f"**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            f.write("## VEREDICTO FINAL\n\n")
            
            # Determinar viabilidade
            is_statistically_valid = (
                permutation_result.get('success') and
                permutation_result['significance']['sharpe'] and
                permutation_result['significance']['total_return']
            )
            
            is_temporally_robust = (
                walkforward_summary is not None and
                walkforward_summary['success_rate'] >= 0.7 and
                walkforward_summary['avg_oos_sharpe'] > 1.0
            )
            
            if is_statistically_valid and is_temporally_robust:
                verdict = "APROVADO PARA LIVE TRADING"
                color = "VERDE"
            elif is_statistically_valid:
                verdict = "APROVADO COM RESSALVAS (validar robustez temporal)"
                color = "AMARELO"
            else:
                verdict = "NAO RECOMENDADO PARA LIVE TRADING"
                color = "VERMELHO"
            
            f.write(f"**Status:** {verdict}\n\n")
            
            # Melhor Setup
            f.write("## MELHOR SETUP ENCONTRADO\n\n")
            f.write("**Parametros:**\n")
            for k, v in best_setup['params'].items():
                if isinstance(v, float):
                    f.write(f"- {k}: {v:.2f}\n")
                else:
                    f.write(f"- {k}: {v}\n")
            f.write("\n")
            
            f.write("**Performance:**\n")
            f.write(f"- Sharpe Ratio: {best_setup['sharpe_ratio']:.2f}\n")
            f.write(f"- Total Return: {best_setup['total_return']:.2f} ({best_setup['total_return_pct']:.2f}%)\n")
            f.write(f"- Win Rate: {best_setup['win_rate']:.1%}\n")
            f.write(f"- Profit Factor: {best_setup['profit_factor']:.2f}\n")
            f.write(f"- Max Drawdown: {best_setup['max_drawdown_pct']:.1f}%\n")
            f.write(f"- Total Trades: {best_setup['total_trades']}\n\n")
            
            # Validação Estatística
            f.write("## VALIDACAO ESTATISTICA\n\n")
            if permutation_result.get('success'):
                pvals = permutation_result['p_values']
                sig = permutation_result['significance']
                
                f.write(f"**Teste de Permutacao (n={permutation_result['n_permutations']:,}):**\n")
                f.write(f"- Sharpe: p={pvals['sharpe']:.4f} ")
                f.write("[OK] APROVADO\n" if sig['sharpe'] else "[X] REPROVADO\n")
                
                f.write(f"- Return: p={pvals['total_return']:.4f} ")
                f.write("[OK] APROVADO\n" if sig['total_return'] else "[X] REPROVADO\n")
                
                f.write(f"- Win Rate: p={pvals['win_rate']:.4f} ")
                f.write("[OK] APROVADO\n" if sig['win_rate'] else "[X] REPROVADO\n")
            else:
                f.write("**ERRO:** Teste de permutacao falhou\n")
            f.write("\n")
            
            # Walk-Forward
            if walkforward_summary:
                f.write("## ROBUSTEZ TEMPORAL (WALK-FORWARD)\n\n")
                f.write(f"- Taxa de sucesso: {walkforward_summary['success_rate']:.1%}\n")
                f.write(f"- Sharpe OOS medio: {walkforward_summary['avg_oos_sharpe']:.2f}\n")
                f.write(f"- Degradacao: {walkforward_summary['degradation_sharpe']:.1%}\n\n")
            
            # Recomendações
            f.write("## RECOMENDACOES\n\n")
            if verdict == "APROVADO PARA LIVE TRADING":
                f.write("1. Iniciar com lote minimo em conta demo\n")
                f.write("2. Monitorar drawdown maximo\n")
                f.write("3. Reavaliar a cada 3 meses\n")
            elif verdict == "APROVADO COM RESSALVAS (validar robustez temporal)":
                f.write("1. Executar walk-forward analysis completa\n")
                f.write("2. Validar em mais dados out-of-sample\n")
                f.write("3. Considerar reducao de alavancagem\n")
            else:
                f.write("1. NAO operar este setup em live trading\n")
                f.write("2. Revisar logica da estrategia\n")
                f.write("3. Testar parametros alternativos\n")
            
            f.write("\n---\n")
            f.write("*Gerado automaticamente pelo MacTester*\n")
        
        print()
        print("="*80)
        print(f"RELATORIO FINAL GERADO: {report_file}")
        print("="*80)
        
        return str(report_file)

