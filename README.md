![CursorRIPER](./res/github-header.png)
# CursorRIPER Framework 

A comprehensive framework for AI-assisted software development in [Cursor IDE](https://www.cursor.com/) that combines structured workflow with persistent memory.

## Overview

CursorRIPER provides a systematic approach to software development through five distinct operational modes:

1. **Research**: Information gathering and understanding existing code
2. **Innovate**: Brainstorming potential approaches and solutions
3. **Plan**: Creating detailed technical specifications
4. **Execute**: Implementing approved plans with precision
5. **Review**: Validating implementation against plans

This framework prevents unintended modifications while maintaining perfect continuity across coding sessions.

```mermaid
flowchart TD
    Start([Start]) --> Init{Project<br>Initialized?}
    Init -->|No| StartPhase[START Phase]
    Init -->|Yes| RIPER[RIPER Workflow]
    
    subgraph StartPhase[START Phase]
        S1[Requirements] --> S2[Technology]
        S2 --> S3[Architecture]
        S3 --> S4[Scaffolding]
        S4 --> S5[Environment]
        S5 --> S6[Memory Bank]
    end
    
    subgraph RIPER[RIPER Workflow]
        R[Research] --> I[Innovate]
        I --> P[Plan]
        P --> E[Execute]
        E --> Rev[Review]
        Rev -.-> R
    end
    
    StartPhase --> RIPER
```

## Features

- **Structured Workflow**: Clear separation of development phases
- **Memory Bank**: Persistent documentation across sessions
- **Project Intelligence**: Learning from patterns and preferences
- **State Management**: Explicit tracking of project phase and mode
- **Safe Initialization**: Guided setup with protection against re-initialization
- **@ Symbol Integration**: Enhanced context referencing with Cursor's @ symbols

## Getting Started

1. Copy the framework files to your project and change the extension to .mdc:
   ```bash
   cp -r /path/to/CursorRIPER/src/.cursor/* .cursor/
   rename 's/\.md$/.mdc/' *.md
   ```

2. Initialize your project with:
   ```
   /start
   ```

3. Follow the START phase to set up your project structure and memory bank

4. Use the RIPER workflow for ongoing development

## @ Symbol Enhancement (New in v1.0.3)

The framework now integrates with Cursor IDE's powerful @ symbol functionality to provide enhanced context referencing:

- **Mode-Specific Symbols**: Optimized symbol patterns for each RIPER mode
- **Symbol Registry**: Track important project references in the memory bank
- **Progressive Introduction**: Symbols introduced gradually during START phase
- **Performance Optimization**: Guidance for handling large files and directories
- **Customizable**: Configure symbol preferences in customization.mdc

```mermaid
flowchart LR
    A["@ Symbols"] --> R["RESEARCH<br>@Files, @Folders, @Code"]
    A --> I["INNOVATE<br>@Web, @Docs, @Files"]
    A --> P["PLAN<br>@Files, @Code, @Folders"]
    A --> E["EXECUTE<br>@Files, @Code, @Tests"]
    A --> Rev["REVIEW<br>@Files, @Git, @Code"]
```

## Documentation

- [Setup Guide](docs/setup-guide.md)
- [START Phase Guide](docs/start-phase-guide.md)
- [RIPER Workflow Guide](docs/riper-workflow-guide.md)
- [Memory Bank Guide](docs/memory-bank-guide.md)
- [Custom Modes Guide](docs/custom-modes-guide.md)
- [Troubleshooting Guide](docs/troubleshooting-guide.md)
- [@ Symbol Guide](docs/@-symbol-guide.md) (New)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
The original RIPER framework is by: [robotlovehuman](https://github.com/robotlovehuman)

*The CursorRIPER Framework prevents coding disasters while maintaining perfect continuity across sessions.*
