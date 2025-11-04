# 🎛️ COMANDOS RIPER - REFERÊNCIA RÁPIDA

*Criado: 2024-11-03*
*Projeto: MACTESTER*

---

## 🔄 COMANDOS DE MODO

### **Ω₁ - RESEARCH MODE** 🔍
```
/research  ou  /r
```

**Objetivo**: Investigar, analisar, observar
**Permissões**: ℙ(Ω₁) = {R: ✓, C: ✗, U: ✗, D: ✗}
**Ações permitidas**: 
- ✅ Ler arquivos
- ✅ Analisar código
- ✅ Buscar informações
- ✅ Documentar descobertas
- ❌ Criar/modificar/deletar arquivos

**Atualiza**: σ₂ (systemPatterns), σ₃ (techContext)
**Contexto**: 📚 Docs, 📁 Folders, 🔄 Git

---

### **Ω₂ - INNOVATE MODE** 💡
```
/innovate  ou  /i
```

**Objetivo**: Explorar possibilidades, sugerir soluções
**Permissões**: ℙ(Ω₂) = {R: ✓, C: ~, U: ✗, D: ✗}
**Ações permitidas**:
- ✅ Ler arquivos
- ✅ Sugerir ideias
- ✅ Avaliar abordagens
- ~ Criar conceitos (não código real)
- ❌ Modificar/deletar arquivos

**Atualiza**: σ₃ (techContext), σ₄ (activeContext)
**Contexto**: 💻 Code, 📚 Docs, 📝 Notepads

---

### **Ω₃ - PLAN MODE** 📝
```
/plan  ou  /p
```

**Objetivo**: Planejar mudanças estruturadas
**Permissões**: ℙ(Ω₃) = {R: ✓, C: ✓, U: ~, D: ✗}
**Ações permitidas**:
- ✅ Ler arquivos
- ✅ Criar planos
- ✅ Definir checklists
- ~ Atualizar planos apenas
- ❌ Executar mudanças
- ❌ Deletar arquivos

**Atualiza**: σ₃ (techContext), σ₄ (activeContext), σ₅ (progress)
**Contexto**: 📄 Files, 📁 Folders, 📏 Rules

---

### **Ω₄ - EXECUTE MODE** ⚙️
```
/execute  ou  /e
```

**Objetivo**: Implementar código seguindo o plano
**Permissões**: ℙ(Ω₄) = {R: ✓, C: ✓, U: ✓, D: ~}
**Ações permitidas**:
- ✅ Ler arquivos
- ✅ Criar arquivos
- ✅ Modificar arquivos
- ✅ Seguir o plano
- ~ Deletar (escopo limitado)
- ❌ Improvisar/desviar do plano

**Atualiza**: σ₄ (activeContext), σ₅ (progress)
**Contexto**: 💻 Code, 📄 Files, 📌 Pinned

---

### **Ω₅ - REVIEW MODE** 🔎
```
/review  ou  /rev
```

**Objetivo**: Validar resultados, verificar qualidade
**Permissões**: ℙ(Ω₅) = {R: ✓, C: ✗, U: ✗, D: ✗}
**Ações permitidas**:
- ✅ Ler arquivos
- ✅ Analisar código
- ✅ Verificar testes
- ✅ Reportar status (✅|⚠️)
- ❌ Modificar código
- ❌ Criar/deletar arquivos

**Atualiza**: σ₄ (activeContext), σ₅ (progress), σ₆ (protection)
**Contexto**: 💻 Code, 📄 Files, 🔄 Git

---

## 🔄 FLUXO RECOMENDADO

```
/r → Investigar problema
  ↓
/i → Explorar soluções
  ↓
/p → Criar plano detalhado
  ↓
/e → Executar implementação
  ↓
/rev → Validar resultado
```

---

## 🎯 EXEMPLO DE USO

### **Cenário**: Corrigir bug no EA

```bash
# 1. Investigar
/r
# → AI coleta informações, analisa código, identifica causa raiz

# 2. Explorar soluções
/i
# → AI sugere 3 abordagens possíveis, avalia prós/contras

# 3. Planejar correção
/p
# → AI cria checklist detalhado, define passos

# 4. Executar
/e
# → AI implementa mudanças seguindo o plano

# 5. Validar
/rev
# → AI verifica se correção funcionou, testa edge cases
```

---

## 📊 MATRIZ DE PERMISSÕES

| Ação | Ω₁ (R) | Ω₂ (I) | Ω₃ (P) | Ω₄ (E) | Ω₅ (RV) |
|------|--------|--------|--------|--------|---------|
| **Read** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Create** | ❌ | ~ | ✅ | ✅ | ❌ |
| **Update** | ❌ | ❌ | ~ | ✅ | ❌ |
| **Delete** | ❌ | ❌ | ❌ | ~ | ❌ |

**Legenda**:
- ✅ = Permitido
- ❌ = Bloqueado
- ~ = Parcialmente (com restrições)

---

## 🚨 VIOLAÇÕES

Se AI tentar ação não permitida no modo atual:

```
𝕍(op, Ω) = {
  log_violation(op, Ω),
  create_backup(),
  revert_to_safe_mode(),  // Volta para Ω₃ (Plan)
  notify_violation(op, Ω)
}
```

---

## 🛡️ PROTEÇÃO DE CÓDIGO

Mesmo em **Execute Mode**, respeitar:

```
Ψ = [PROTECTED, GUARDED, INFO, DEBUG, TEST, CRITICAL]
```

- **PROTECTED**: Nunca modificar sem permissão explícita
- **GUARDED**: Modificar com cautela, após confirmação
- **INFO/DEBUG/TEST**: Modificar conforme necessário
- **CRITICAL**: Backup obrigatório antes de qualquer mudança

---

## 📝 DOCUMENTAÇÃO AUTOMÁTICA

Cada transição de modo atualiza:

- **σ₃ (techContext.md)**: Decisões técnicas
- **σ₄ (activeContext.md)**: Foco atual + próximos passos
- **σ₅ (progress.md)**: Status + milestones
- **σ₆ (protection.md)**: Violações (se houver)

---

## 🔗 COMANDOS AUXILIARES

### **Contexto**
```
!af <file>      # Add file to context
!ad <folder>    # Add folder to context
!cc             # Clear all context
!cm             # Set context for current mode
```

### **Permissões**
```
!ckp            # Check current permissions
!pm <op>        # Check if operation is permitted
!sp <mode>      # Show permissions for mode
```

### **Debug**
```
!gr <query>     # GitHub repository search
!ws <query>     # Web search
```

---

## 📖 REFERÊNCIAS

- **Framework**: CursorRIPER♦Σ 1.0.5
- **Documentação completa**: `CursorRIPER.sigma/docs/`
- **Symbol Reference**: `memory-bank/symbols.md`
- **Protection Guide**: `CursorRIPER.sigma/docs/ProtectionCommands.md`

---

*Use `/r`, `/i`, `/p`, `/e`, `/rev` para navegar entre modos*
*Cada modo tem permissões específicas para garantir segurança e qualidade*


