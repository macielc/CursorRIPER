# ⚡ QUICK START - Sistema Híbrido MacTester

**5 passos para começar a usar**

---

## 📦 **PASSO 1: Instalar** (2 minutos)

```bash
pip install MetaTrader5 pandas numpy pyyaml
```

---

## 🧪 **PASSO 2: Testar** (1 minuto)

```bash
cd live_trading
python test_connection.py
```

✅ Todos os testes devem passar!

---

## ⚙️ **PASSO 3: Configurar** (30 segundos)

Edite `config.yaml`:

```yaml
trading:
  symbol: "WINFUT"  # Seu símbolo no MT5

monitor:
  dry_run: true  # IMPORTANTE: true para testar!
```

---

## 🚀 **PASSO 4: Rodar** (5 segundos)

```bash
python monitor_elefante.py
```

Pronto! Sistema está monitorando.

---

## 📊 **PASSO 5: Verificar** (contínuo)

Acompanhe no console:
```
✅ Conectado ao MT5
🎯 SINAL DETECTADO
💭 DRY-RUN: Ordem NÃO executada
```

Logs em: `logs/monitor.log`

---

## 🎯 **PRÓXIMOS PASSOS**

### **Depois de validar dry-run**:

1. Configure `dry_run: false` no `config.yaml`
2. Teste em conta **DEMO** primeiro!
3. Monitore por 1 semana
4. Só então considere conta real

---

## 📝 **LEIA MAIS**

- **Documentação completa**: `README.md`
- **Arquitetura**: `../docs_mactester/SISTEMA_HIBRIDO_MT5_PYTHON.md`
- **Configuração**: `config.yaml` (com comentários)

---

**Dúvidas?** Verifique `README.md` seção Troubleshooting

**Boa sorte!** 🚀

