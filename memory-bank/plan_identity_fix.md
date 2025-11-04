# 📝 PLANO: Alcançar 100% de Identidade Python ↔ MT5

*Criado: 2024-11-03*
*Modo: Ω₃·PLAN*
*Objetivo: MT5 detectar 27 trades (igual Python) em janeiro/2024*

---

## 🎯 OBJETIVO

**Meta**: MT5 deve detectar **exatamente os mesmos trades** que Python
- Python: 27 trades, -3,105 pts
- MT5 atual: 14 trades (~52%)
- **Gap**: 13 trades faltando (48%)

---

## 🔍 ANÁLISE DA CAUSA RAIZ

### **Hipótese Principal**: Diferença na lógica de lookback/shift

**Python** (strategy.py linha 143-185):
```python
for i in range(lookback, n):
    # Calcula médias usando barras ANTES de i
    amplitude_media = mean(amplitude[i-lookback:i])
    volume_media = mean(volume[i-lookback:i])
    
    # Verifica se barra i-1 é elefante
    if is_elephant(i-1):
        # Verifica se barra i rompeu
        if breakout(i):
            entries[i+1] = True  # Entra na próxima barra
```

**MT5_CORRIGIDO**:
```mql5
// Shift 1 = última barra fechada
CopyRates(_Symbol, PERIOD_M5, 1, 1, rates);  // Pega shift 1

// Calcula médias usando shift 1 em diante
CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackAmplitude, ratesAmp);
// PROBLEMA: Isso pega shift 1, 2, 3... até 25
// Mas deveria pegar shift 2, 3, 4... até 26 (ANTES do elefante)
```

### **Problema Identificado**: 🔴
O lookback do MT5 está **INCLUINDO a barra candidata** no cálculo da média!

**Python correto**:
- Barra i-1: candidata a elefante
- Média calculada: barras [i-26] até [i-2] (25 barras ANTES)

**MT5 incorreto**:
- Shift 1: candidata a elefante
- Média calculada: shift 1 até 25 (INCLUI a barra candidata!)
- **Resultado**: Média inflada, detecta menos elefantes

---

## 📋 PLANO DE AÇÃO

### **FASE 1: Correção da Lógica de Lookback** ⚙️

**Tarefa 1.1**: Corrigir `DetectarElefante()` no EA_CORRIGIDO
```mql5
// ANTES (errado):
CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackAmplitude, ratesAmp);
// Pega: shift 1, 2, 3... 25

// DEPOIS (correto):
CopyRates(_Symbol, PERIOD_M5, 2, InpLookbackAmplitude, ratesAmp);
// Pega: shift 2, 3, 4... 26 (ANTES do elefante shift 1)
```

**Tarefa 1.2**: Aplicar mesma correção para volume
```mql5
// ANTES:
CopyRates(_Symbol, PERIOD_M5, 1, InpLookbackVolume, ratesVol);

// DEPOIS:
CopyRates(_Symbol, PERIOD_M5, 2, InpLookbackVolume, ratesVol);
```

**Resultado esperado**: MT5 detectará MAIS elefantes (médias menores)

---

### **FASE 2: Validação com Logs Detalhados** 🔍

**Tarefa 2.1**: Adicionar logs de debug no EA
```mql5
void DetectarElefante()
{
   // ... código ...
   
   Print("DEBUG: Shift 1 time=", TimeToString(rates[0].time));
   Print("DEBUG: Amplitude candidata=", amplitude);
   Print("DEBUG: Amplitude média=", ampMedia);
   Print("DEBUG: Ratio=", amplitude/ampMedia);
   Print("DEBUG: Mínimo requerido=", InpMinAmplitudeMult);
   
   if(amplitude < ampMedia * InpMinAmplitudeMult)
   {
      Print("DEBUG: REJEITADO - amplitude insuficiente");
      return;
   }
   
   Print("DEBUG: ELEFANTE DETECTADO!");
}
```

**Tarefa 2.2**: Rodar teste de 09/01/2024 (1 dia)
- Python detectou 2 trades neste dia
- Verificar se MT5 detecta os mesmos
- Comparar logs de amplitude/volume

---

### **FASE 3: Teste Incremental** 📈

**Tarefa 3.1**: Teste de 1 dia (09/01/2024)
- Objetivo: 2 trades SELL
- Critério: Horários ±5 minutos do Python

**Tarefa 3.2**: Teste de 1 semana (09-15/01/2024)
- Objetivo: ~10 trades
- Critério: Quantidade ±1 trade

**Tarefa 3.3**: Teste de janeiro completo
- Objetivo: 27 trades
- Critério: 100% identidade

---

### **FASE 4: Análise de Discrepâncias Remanescentes** 🔬

Se após Fase 1-3 ainda houver diferenças:

**Investigar**:
1. Precisão de cálculos (float vs double)
2. Arredondamentos de preço
3. Diferenças nos dados históricos MT5 vs Golden Data
4. Cálculo de ATR (Python usa ta-lib, MT5 calcula manual)

**Ações**:
- Comparar 10 candles aleatórios (OHLCV)
- Comparar médias calculadas
- Ajustar tolerâncias se necessário

---

### **FASE 5: Documentação Final** 📝

**Tarefa 5.1**: Criar tabela de identidade
```
| Data | Python Trade | MT5 Trade | Δ Horário | Δ Preço | Status |
|------|--------------|-----------|-----------|---------|--------|
| ...
```

**Tarefa 5.2**: Atualizar σ₅ (progress.md)
- Marcar identidade Python ↔ MT5 como ✅

**Tarefa 5.3**: Criar EA_BarraElefante_FINAL.mq5
- Versão final validada
- Comentários explicativos
- Pronto para produção

---

## ✅ CRITÉRIOS DE SUCESSO

### **Mínimo Aceitável** (90%):
- ✅ 24-27 trades em janeiro
- ✅ Win rate 27-32%
- ✅ PnL -2,800 a -3,400 pts

### **Ideal** (100%):
- ✅ Exatamente 27 trades
- ✅ Mesmos dias/horários (±5 min)
- ✅ Mesmas direções (BUY/SELL)
- ✅ PnL ±5% do Python

---

## ⏱️ CRONOGRAMA

```
Fase 1: 15 minutos (correção de código)
Fase 2: 30 minutos (debug e logs)
Fase 3: 45 minutos (testes incrementais)
Fase 4: 1 hora (análise detalhada, se necessário)
Fase 5: 30 minutos (documentação)

Total: ~3 horas
```

---

## 🚧 RISCOS E MITIGAÇÕES

### Risco 1: Dados históricos diferentes
**Probabilidade**: Média
**Impacto**: Alto
**Mitigação**: Comparar candles específicos MT5 vs Golden Data

### Risco 2: Lógica Python tem bug não documentado
**Probabilidade**: Baixa
**Impacto**: Alto
**Mitigação**: Revisar strategy.py linha por linha

### Risco 3: MT5 API tem limitações
**Probabilidade**: Baixa
**Impacto**: Médio
**Mitigação**: Usar workarounds documentados na comunidade MQL5

---

## 📌 BLOQUEIOS ATUAIS

- ❌ Nenhum bloqueio
- ✅ Todas as informações necessárias disponíveis
- ✅ Pronto para executar Fase 1

---

## 🎯 PRÓXIMO PASSO IMEDIATO

**Executar Fase 1, Tarefa 1.1**:
- Modificar `EA_BarraElefante_CORRIGIDO.mq5`
- Corrigir linha do CopyRates (shift 1 → shift 2)
- Recompilar
- Testar em 09/01/2024

---

*Plano criado em Ω₃·PLAN mode*
*Aguardando aprovação para /execute*

