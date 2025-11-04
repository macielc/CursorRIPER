# ⚠️ ATENÇÃO: CONTA REAL DETECTADA

## 🚨 INFORMAÇÕES DA SUA CONTA

```
Login: 586125
Servidor: GenialInvestimentos-PRD
Tipo: REAL
Saldo: R$ 312,00
```

---

## ⚠️ IMPORTANTE

Sua conta MT5 é **REAL**, não é demo!

Isso significa que se você rodar o monitor com `dry_run: false`, ele irá:
- ✅ Executar ordens DE VERDADE
- ✅ Usar seu dinheiro REAL
- ✅ Gerar lucros/prejuízos REAIS

---

## 🛡️ RECOMENDAÇÕES DE SEGURANÇA

### **1. SEMPRE teste com dry_run PRIMEIRO**

No arquivo `config.yaml`:
```yaml
monitor:
  dry_run: true  # MANTENHA true até ter certeza!
```

Com `dry_run: true`:
- ✅ Monitora mercado
- ✅ Detecta sinais
- ✅ Mostra logs
- ❌ **NÃO executa ordens de verdade**

---

### **2. Considere abrir conta DEMO**

**Por quê?**
- Testar sistema sem risco
- Validar por 1 semana
- Ver resultados reais sem perder dinheiro

**Como abrir demo**:
1. No MT5: Arquivo → Abrir Conta
2. Escolha GenialInvestimentos
3. Selecione "Conta Demo"
4. Preencha dados
5. Use essa conta para testes

---

### **3. Se for usar conta REAL**

#### **Checklist OBRIGATÓRIO**:

- [ ] Testei com `dry_run: true` por **pelo menos 1 dia**
- [ ] Entendi como o sistema funciona
- [ ] Configurei `max_daily_loss_points` (loss máximo)
- [ ] Configurei `max_positions: 1` (só 1 posição)
- [ ] Tenho margem suficiente (pelo menos R$ 3.000)
- [ ] Estou monitorando ativamente (não deixar sozinho)
- [ ] Aceito os riscos (pode perder dinheiro)

#### **Configurações de segurança**:

```yaml
risk:
  max_daily_loss_points: 500  # Ajuste conforme seu risco
  max_consecutive_losses: 3   # Para após 3 losses
  max_positions: 1            # Só 1 trade por vez

trading:
  volume: 1.0  # Comece com 1 contrato apenas
```

---

### **4. Saldo atual: R$ 312,00**

⚠️ **ALERTA**: Saldo baixo para operar WIN$!

**Margem necessária** (aproximada):
- 1 contrato WIN$: ~R$ 2.500 - 3.000
- Seu saldo: R$ 312,00
- **Status**: ❌ **INSUFICIENTE**

**Ações**:
1. **Opção A**: Depositar mais (mínimo R$ 3.000)
2. **Opção B**: Usar conta demo para testes
3. **Opção C**: Operar outro ativo com margem menor

---

## 🧪 PLANO DE TESTES SEGURO

### **Fase 1: Dry-Run (Hoje)** ✅ FAÇA ISSO

```bash
# 1. Confirme dry_run: true no config.yaml

# 2. Execute teste novamente
python test_connection.py

# 3. Se todos testes OK, rode monitor
python monitor_elefante.py

# 4. Observe por 1 hora (horário de mercado)
# - Console mostrará sinais
# - Nenhuma ordem será executada
```

---

### **Fase 2: Demo (Esta semana)** 🔜 RECOMENDADO

```bash
# 1. Abra conta demo
# 2. Configure MT5 com demo
# 3. Rode monitor com dry_run: false
# 4. Monitore por 1 semana
# 5. Compare com backtest
```

---

### **Fase 3: Real (Quando validado)** ⚠️ CUIDADO

```bash
# SOMENTE se:
# - Demo funcionou perfeitamente
# - Tem capital suficiente (R$ 5k+)
# - Aceita os riscos

# Então:
# 1. Configure dry_run: false
# 2. Comece com 1 contrato
# 3. Monitore MUITO ativamente
# 4. Pare se der problemas
```

---

## 📊 EXPECTATIVAS REALISTAS

### **Baseado em backtest (Janeiro/2024)**

```
Trades/mês: ~27
Win rate: ~30%
PnL médio: Variável (-3,105 pts em jan/2024)
```

**Janeiro foi MÊS NEGATIVO** (R$ -621)!

Isso significa:
- ⚠️ Sistema não garante lucro
- ⚠️ Pode ter meses negativos
- ⚠️ Estratégia precisa validação de longo prazo
- ⚠️ Use apenas capital que pode perder

---

## 🚨 QUANDO PARAR IMEDIATAMENTE

### **Pare se**:

1. ❌ Sistema apresentar erros
2. ❌ Ordens sendo executadas erradas
3. ❌ Loss diário exceder limite
4. ❌ Comportamento inesperado
5. ❌ Não conseguir monitorar ativamente

### **Como parar**:

```bash
# No terminal onde rodou monitor:
Ctrl + C

# Ou feche todas posições no MT5 manualmente
```

---

## 📞 SUPORTE

### **Se tiver dúvidas**:

1. Leia `README.md` completo
2. Verifique logs em `logs/monitor.log`
3. Teste com `dry_run: true` primeiro
4. **NÃO arrisque capital que não pode perder**

---

## ✅ PRÓXIMO PASSO SEGURO

**AGORA (5 minutos)**:

```bash
# 1. Execute teste corrigido
python test_connection.py

# 2. Se passar, rode em dry-run
python monitor_elefante.py

# 3. Observe (SEM ordens reais)

# 4. Me avise o resultado!
```

---

**⚠️ LEMBRE-SE**: 

**Trading automatizado envolve RISCO REAL de perda de capital!**

Teste MUITO antes de usar com dinheiro real.

---

*Criado em: 2024-11-03*  
*Sistema: MacTester Release 1.0*

