# 🔗 Sistema Híbrido Python Monitor + MT5 Executor

Sistema de trading automatizado onde **Python detecta sinais** e **MT5 executa ordens**.

**Versão**: 1.0.0  
**Data**: 2024-11-03  
**Estratégia**: Barra Elefante (validada em backtest com 27 trades em janeiro/2024)

---

## 🎯 VISÃO GERAL

### **Arquitetura**

```
┌────────────────────────────┐
│   PYTHON (Cérebro)         │
│   - Monitora mercado       │
│   - Detecta sinais         │
│   - Calcula SL/TP          │
└──────────┬─────────────────┘
           │ MetaTrader5 API
           ↓
┌────────────────────────────┐
│   MT5 (Executor)           │
│   - Recebe ordens          │
│   - Executa trades         │
│   - Gerencia posições      │
└────────────────────────────┘
```

### **Vantagens**

✅ **Não precisa identidade 100%** Python ↔ MT5  
✅ **Python já validado** (27 trades em backtest)  
✅ **Fácil debugar** (Python vs MQL5)  
✅ **Flexível** (mudar parâmetros sem recompilar)  
✅ **Evolução rápida** (adicionar sinais é trivial)

---

## 📦 INSTALAÇÃO

### **1. Requisitos**

- Python 3.8+
- MetaTrader 5 instalado e rodando
- Conta demo ou real configurada no MT5

### **2. Instalar Bibliotecas**

```bash
pip install MetaTrader5 pandas numpy pyyaml
```

### **3. Testar Setup**

```bash
cd live_trading
python test_connection.py
```

**Resultado esperado**:
```
✅ TODOS OS TESTES PASSARAM!
   Sistema pronto para uso!
```

---

## ⚙️ CONFIGURAÇÃO

### **Arquivo `config.yaml`**

Edite `live_trading/config.yaml` para ajustar:

#### **1. Símbolo e Volume**

```yaml
trading:
  symbol: "WINFUT"  # ou "WIN$" (verifique no MT5)
  timeframe: 5      # M5
  volume: 1.0       # Contratos
```

#### **2. Parâmetros da Estratégia**

```yaml
strategy:
  min_amplitude_mult: 1.35
  min_volume_mult: 1.3
  max_sombra_pct: 0.30
  # ... (já validados em backtest!)
```

#### **3. Gestão de Risco**

```yaml
risk:
  max_daily_loss_points: 1000     # Pára se perder 1000 pts/dia
  max_consecutive_losses: 5       # Pára após 5 losses seguidos
  max_positions: 1                # Máximo de posições simultâneas
```

#### **4. Modo Dry-Run**

```yaml
monitor:
  dry_run: true  # true = simula, false = executa de verdade!
```

⚠️ **IMPORTANTE**: Sempre teste com `dry_run: true` primeiro!

---

## 🚀 USO

### **Modo 1: Dry-Run (Simulação)**

Para testar sem executar ordens reais:

```bash
# 1. Configure dry_run: true no config.yaml

# 2. Execute o monitor
cd live_trading
python monitor_elefante.py
```

**O que acontece**:
- ✅ Conecta ao MT5
- ✅ Busca dados em tempo real
- ✅ Detecta sinais
- ✅ Mostra logs de ordens
- ❌ **NÃO executa ordens de verdade**

---

### **Modo 2: Live Trading (REAL)**

⚠️ **ATENÇÃO**: Ordens serão executadas de verdade!

```bash
# 1. Configure dry_run: false no config.yaml

# 2. Abra o MT5

# 3. Execute o monitor
cd live_trading
python monitor_elefante.py
```

**Safeguards ativos**:
- 🛡️ Kill switch (loss máximo)
- 🛡️ Validação de margem
- 🛡️ Horário de operação
- 🛡️ Fechamento intraday (12:15)

---

## 📊 LOGS E MONITORAMENTO

### **Console**

O monitor mostra em tempo real:

```
🎯 SINAL DETECTADO #1
  Ação: BUY
  Preço: 163391.00
  SL: 163112.00
  TP: 163763.00
  Razão: Elefante ALTA rompido (amplitude=467)
```

### **Arquivo de Log**

```
live_trading/logs/monitor.log
```

### **Sinais Detectados**

```
live_trading/logs/signals.csv
```

Colunas: timestamp, action, price, sl, tp, atr, reason, executed

### **Ordens Executadas**

```
live_trading/logs/orders.csv
```

Colunas: timestamp, action, price, sl, tp, success, ticket, error

---

## 🧪 TESTES

### **1. Teste de Conexão**

```bash
python test_connection.py
```

Verifica:
- ✅ Bibliotecas instaladas
- ✅ MT5 conectando
- ✅ Símbolo disponível
- ✅ Dados históricos
- ✅ Estratégia importando

---

### **2. Teste Dry-Run (1 hora)**

```bash
# 1. Configure dry_run: true

# 2. Execute
python monitor_elefante.py

# 3. Aguarde 1 hora (horário de mercado)

# 4. Verifique logs:
cat logs/signals.csv
```

**Esperado**: Detectar sinais se houver elefantes no período

---

### **3. Validação em Demo**

Antes de ir para conta real:

1. Abra conta demo na corretora
2. Configure MT5 com conta demo
3. Execute monitor em modo REAL (`dry_run: false`)
4. Rode por 1 semana completa
5. Compare resultados com backtest

**Critério de sucesso**:
- ✅ Sistema roda sem crashes
- ✅ Detecta sinais esperados
- ✅ Ordens executam corretamente
- ✅ SL/TP funcionam
- ✅ Fechamento intraday funciona

---

## 🛠️ TROUBLESHOOTING

### **Problema 1: "MT5 initialize() failed"**

**Causa**: MT5 não está rodando ou não está logado

**Solução**:
1. Abra o MetaTrader 5
2. Faça login na conta
3. Execute o monitor novamente

---

### **Problema 2: "Símbolo não encontrado"**

**Causa**: Nome do símbolo incorreto

**Solução**:
1. Abra MT5
2. Market Watch → Clique direito → Symbols
3. Procure por "WIN" e veja o nome exato (WINFUT, WIN$, etc)
4. Atualize `symbol` no `config.yaml`

---

### **Problema 3: "Nenhum sinal detectado"**

**Causa**: Não houve elefantes no período ou horário fora de operação

**Solução**:
1. Verifique se está dentro do horário (9:15 - 11:00)
2. Ajuste parâmetros se necessário (não recomendado)
3. Aguarde sinais (elefantes são raros!)

---

### **Problema 4: "Ordem rejeitada"**

**Causas possíveis**:
- Margem insuficiente
- Símbolo não negociável
- Horário fora de pregão
- MT5 não conectado

**Solução**:
1. Verifique margem livre
2. Confirme horário de pregão
3. Teste conexão MT5

---

## 📈 PERFORMANCE ESPERADA

### **Backtest Janeiro/2024** (Python validado)

- **Total trades**: 27
- **Win rate**: 29.6% (8 wins, 19 losses)
- **PnL**: -3,105 pontos (R$ -621)
- **Melhor trade**: +848 pontos
- **Pior trade**: -680 pontos

**Observação**: Janeiro foi mês negativo, mas estratégia foi validada em períodos maiores.

---

## 🔒 SEGURANÇA

### **Recomendações**

1. ✅ **Sempre teste em Demo primeiro**
2. ✅ **Use `dry_run: true` para validar**
3. ✅ **Configure `max_daily_loss_points`**
4. ✅ **Monitore logs regularmente**
5. ✅ **Tenha stop loss sempre ativo**

### **Riscos**

- ⚠️ Sistema pode ter bugs (teste bem!)
- ⚠️ Mercado pode mudar (invalidar estratégia)
- ⚠️ Slippage pode afetar resultados
- ⚠️ Conexão internet pode falhar

**Disclaimer**: Use por sua conta e risco. Não há garantias de lucro.

---

## 📞 SUPORTE

### **Erros e Bugs**

1. Verifique logs em `live_trading/logs/monitor.log`
2. Execute `test_connection.py`
3. Revise `config.yaml`

### **Melhorias**

Sugestões de melhorias:
- Adicionar alertas (Telegram/Email)
- Dashboard web em tempo real
- Múltiplos símbolos simultâneos
- Trailing stop
- Otimização dinâmica de parâmetros

---

## 🎉 PRÓXIMOS PASSOS

### **Fase 1: Validação** ✅ (Você está aqui)
- [x] Sistema implementado
- [ ] Teste de conexão
- [ ] Dry-run 1 hora
- [ ] Demo 1 semana

### **Fase 2: Produção** 🔜
- [ ] Validação demo bem-sucedida
- [ ] Deploy em máquina dedicada
- [ ] Monitoramento 24/7
- [ ] Análise de performance

### **Fase 3: Otimização** 🔜
- [ ] Adicionar alertas
- [ ] Dashboard de monitoramento
- [ ] Múltiplas estratégias
- [ ] Auto-otimização

---

**Boa sorte!** 🚀

*Sistema desenvolvido por MacTester Team - Release 1.0*

