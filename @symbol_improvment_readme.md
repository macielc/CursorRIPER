![CursorRIPER](./res/github-header.png)
# CursorRIPER Framework - @ Symbol Enhancement

This readme contains the implementation of the @ symbol enhancement branch for the CursorRIPER Framework. This enhancement integrates Cursor IDE's powerful @ symbol functionality throughout the framework to improve context referencing while preserving the core RIPER workflow.

## Directory Structure

```
CursorRIPER/
├── src/
│   ├── .cursor/
│   │   └── rules/
│   │       ├── core.mdc                  # Updated with @ symbol detection and suggestion
│   │       ├── state.mdc                 # Updated with @ symbol state tracking
│   │       ├── start-phase.mdc           # Updated with progressive symbol introduction
│   │       ├── riper-workflow.mdc        # Updated with mode-specific symbol guidance
│   │       └── customization.mdc         # Updated with symbol customization options
│   └── templates/
│       └── memory-bank/
│           └── @-symbol-registry.md      # NEW: Symbol registry template
└── docs/
    └── @-symbol-guide.md                # NEW: Comprehensive symbol usage guide
```

## Implementation Details

This enhancement adds @ symbol integration throughout the CursorRIPER Framework:

1. **Core Framework Updates**:
   - Symbol detection and suggestion rules
   - Symbol registry state tracking
   - Performance optimization guidance
   - Customization options

2. **START Phase Integration**:
   - Progressive symbol introduction in each step
   - Symbol discovery and registry setup

3. **RIPER Workflow Integration**:
   - Mode-specific symbol recommendations
   - Cross-mode consistency guidelines
   - Symbol-specific memory bank updates

4. **Memory Bank Enhancements**:
   - Comprehensive symbol registry template
   - Symbol sections in all memory bank templates

5. **Documentation**:
   - Detailed usage guide with visual diagrams
   - Best practices and troubleshooting
   - Project type-specific recommendations

## Installation

To implement this enhancement in an existing CursorRIPER project:

1. Backup your existing framework files:
   ```
   mkdir -p .backup/$(date +%Y-%m-%d)
   cp -r .cursor/rules/* .backup/$(date +%Y-%m-%d)/
   ```

2. Copy the updated framework files:
   ```
   cp -r implementation/src/.cursor/rules/* .cursor/rules/
   ```

3. Copy the new memory bank template:
   ```
   cp implementation/src/templates/memory-bank/@-symbol-registry.md memory-bank/
   ```

4. Copy the new documentation:
   ```
   cp implementation/docs/@-symbol-guide.md docs/
   ```

5. Initialize the @ symbol registry:
   - If in START phase: The registry will be created during step 6
   - If in DEVELOPMENT or MAINTENANCE phase: Create the registry manually based on the template

## Usage

Refer to the `@-symbol-guide.md` for comprehensive usage instructions.

Basic usage patterns for each mode:

- **RESEARCH**: Use `@Files`, `@Folders`, and `@Code` to explore the codebase
- **INNOVATE**: Use `@Web` and `@Docs` to research solutions
- **PLAN**: Use precise `@Files` and `@Code` references in your plans
- **EXECUTE**: Reference symbols from the plan during implementation
- **REVIEW**: Compare implemented files to planned targets using symbols

## Troubleshooting

If you encounter issues:

1. Verify state.mdc has been appropriately updated with @ symbol state tracking
2. Ensure the @-symbol-registry.md exists in your memory bank
3. Check customization.mdc for correct symbol preferences
4. Refer to the troubleshooting section in @-symbol-guide.md

## Credits
---

## License

MIT License - see LICENSE file in the root directory.
