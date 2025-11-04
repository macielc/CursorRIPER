# 🔣 Symbol Reference Guide
*v1.0 | Created: 2025-11-03 | Updated: 2025-11-03*

## 📁 File System Symbols
- 📂 = `/memory-bank/`
- 📦 = `/memory-bank/backups/`

## 🧠 Memory Files (σ₁-σ₆)
- σ₁ = 📋 `projectbrief.md` - Project requirements, scope, criteria
- σ₂ = 🏛️ `systemPatterns.md` - Architecture, patterns, decisions
- σ₃ = 💻 `techContext.md` - Technology stack, environment, dependencies
- σ₄ = 🔮 `activeContext.md` - Current focus, changes, next steps, context references
- σ₅ = 📊 `progress.md` - Status, milestones, issues
- σ₆ = 🛡️ `protection.md` - Protected regions, history, approvals, violations

## 🔄 RIPER Modes (Ω)
- Ω₁ = 🔍R (RESEARCH) - Read-only observation and documentation
- Ω₂ = 💡I (INNOVATE) - Ideation without code implementation
- Ω₃ = 📝P (PLAN) - Specification and planning
- Ω₄ = ⚙️E (EXECUTE) - Implementation following plan
- Ω₅ = 🔎RV (REVIEW) - Validation without modification

## 🏗️ Project Phases (Π)
- Π₁ = 🌱 UNINITIATED - Framework installed, project not started
- Π₂ = 🚧 INITIALIZING - START active, setup ongoing
- Π₃ = 🏗️ DEVELOPMENT - Main development, RIPER active
- Π₄ = 🔧 MAINTENANCE - Long-term support, RIPER active

## 🔐 Protection Levels (Ψ)
- Ψ₁ = 🔒 PROTECTED - Critical code, no modifications
- Ψ₂ = 🛡️ GUARDED - Important code, request permission
- Ψ₃ = ℹ️ INFO - Informational markers
- Ψ₄ = 🐞 DEBUG - Debug/development code
- Ψ₅ = 🧪 TEST - Test code
- Ψ₆ = ⚠️ CRITICAL - Mission-critical code

## 📎 Context References (Γ)
- Γ₁ = 📄 @Files - File references
- Γ₂ = 📁 @Folders - Folder references
- Γ₃ = 💻 @Code - Code references
- Γ₄ = 📚 @Docs - Documentation references
- Γ₅ = 📏 @Cursor Rules - Rules references
- Γ₆ = 🔄 @Git - Git references
- Γ₇ = 📝 @Notepads - Notepad references
- Γ₈ = 📌 #Files - Pinned file references

## 🔐 CRUD Permissions (ℙ)
- ℙ = {C: create, R: read, U: update, D: delete}

### Permission Matrix
```
Mode    | Create | Read | Update | Delete
--------|--------|------|--------|--------
Ω₁ (R)  |   ✗    |  ✓   |   ✗    |   ✗
Ω₂ (I)  |   ~    |  ✓   |   ✗    |   ✗
Ω₃ (P)  |   ✓    |  ✓   |   ~    |   ✗
Ω₄ (E)  |   ✓    |  ✓   |   ✓    |   ~
Ω₅ (RV) |   ✗    |  ✓   |   ✗    |   ✗
```
*Legend: ✓=allowed, ✗=forbidden, ~=limited*

## 🔗 Cross-Reference Notation
- `[↗️σₓ:Rₓ]` - Reference to memory file section
- `[Γₓ:name]` - Context reference
- `[Ψₓ+Γₓ:location]` - Protection with context
- `[ℙ(Ωₓ):operation]` - Permission reference

## 📊 Status Indicators
- ✅ Completed
- ⏳ In Progress
- 🔜 Planned
- ⚠️ Issue/Warning
- ❌ Blocked/Failed
- 🟢 Active
- 🟡 Partially Relevant
- 🟣 Essential
- 🔴 Deprecated

## 🎯 Tool Operations (𝕋)
```
𝕋 = [
  0-3:  read_files, ask_questions, observe_code, document_findings,
  4-6:  suggest_ideas, explore_options, evaluate_approaches,
  7-9:  create_plan, detail_specifications, sequence_steps,
  10-12: implement_code, follow_plan, test_implementation,
  13-15: validate_output, verify_against_plan, report_deviations
]
```

## 🔍 Quick Command Reference

### Mode Transitions
- `/r` or `/research` → Ω₁ (RESEARCH)
- `/i` or `/innovate` → Ω₂ (INNOVATE)
- `/p` or `/plan` → Ω₃ (PLAN)
- `/e` or `/execute` → Ω₄ (EXECUTE)
- `/rev` or `/review` → Ω₅ (REVIEW)

### Context Commands
- `!af(file)` - Add file reference
- `!ad(folder)` - Add folder reference
- `!ac(code)` - Add code reference
- `!adoc(doc)` - Add documentation reference
- `!ar(rule)` - Add rule reference
- `!ag(git)` - Add git reference
- `!an(notepad)` - Add notepad reference
- `!pf(file)` - Pin file to context
- `!cs(ref, status)` - Set context status
- `!cr(ref)` - Remove context reference
- `!cc` - Clear all context references
- `!cm` - Set context for current mode

### Permission Commands
- `!ckp` - Check current permissions
- `!pm(operation)` - Check if operation permitted
- `!sp(mode)` - Show permissions for mode
- `!vm(operation)` - Verify appropriate mode

### Protection Commands
- `!cp` - Check protected regions
- `!cg` - Check guarded regions
- `!ci` - Check info markers
- `!cd` - Check debug markers
- `!ct` - Check test markers
- `!cc` - Check critical markers

## 📚 Usage Examples

### Cross-Reference
```markdown
The authentication system [↗️σ₂:A₁] uses JWT tokens defined in [Γ₃:auth.py].
```

### Protection Marker
```python
# Ψ₁·PROTECTED
def critical_calculation():
    # This algorithm is protected
    pass
# END-P
```

### Context Reference
```markdown
Active code modules [Γ₃:backtest_engine.py, optimizer.py]
```

## 🔄 Workflow Example

1. **Research** (Ω₁): Understand codebase
   - `!af(engines/python/mactester.py)`
   - Document findings in σ₄

2. **Innovate** (Ω₂): Brainstorm improvements
   - Suggest architectural changes
   - Update σ₂ with design decisions

3. **Plan** (Ω₃): Create detailed specification
   - Create implementation checklist
   - Update σ₄ with planned changes

4. **Execute** (Ω₄): Implement the plan
   - Follow checklist strictly
   - Update σ₅ with progress

5. **Review** (Ω₅): Validate results
   - Verify against plan
   - Report in σ₅

---

*This guide provides quick reference for all RIPER symbols and commands*

