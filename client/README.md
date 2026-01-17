# Client Configuration

This folder contains AI assistant guidance files for different tools. These teach the AI how to use the FIWARE MCP server effectively.

## Setup by Tool

### Cursor

Copy the rules file to your project or global Cursor config:

```bash
# Project-level (recommended)
mkdir -p .cursor
cp client/CLAUDE.md .cursor/rules

# Or global
cp client/CLAUDE.md ~/.cursor/rules
```

### Claude Code (CLI)

Copy to your project root:

```bash
cp client/CLAUDE.md ./CLAUDE.md
```

Claude Code automatically reads `CLAUDE.md` from the working directory.

### Windsurf

```bash
cp client/CLAUDE.md .windsurfrules
```

### Other Tools

Copy the content of `CLAUDE.md` into your tool's system prompt or rules configuration.

## What's Included

The guidance file contains:
- Available tools and their parameters
- Recommended workflows (exploring, creating entities, historical data, alerts)
- Common query patterns
- Error handling tips
- Best practices for Smart Data Models
