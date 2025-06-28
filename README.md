# Twig

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**A lightweight command-line interface for querying LLMs with powerful piping and context injection capabilities.**

Twig transforms the Chain framework into a flexible CLI tool that lets you seamlessly integrate AI queries into your terminal workflow. Pipe data, compose complex prompts, and get intelligent responses without leaving your command line.

## Quick Start

```bash
# Install
pip install -e .

# Simple query
twig "Explain this error message"

# Pipe content for context
cat error.log | twig "What's wrong with this code?"

# Advanced prompt composition
echo "$(cat myfile.py)" | twig "Review this code" -a "Focus on performance issues" -m claude
```

## Key Features

- **🔄 Seamless Piping**: Pipe any content directly into your prompts as context
- **🧩 Flexible Prompt Structure**: Compose prompts with head, context, and tail components  
- **💬 Multiple Interaction Modes**: One-shot queries, persistent chat, or interactive shell
- **🖼️ Image Support**: Include clipboard images in your queries
- **📚 Conversation History**: Automatic message storage and retrieval
- **🎯 Model Selection**: Easy switching between different LLM providers
- **⚡ Rich Output**: Beautiful markdown formatting with syntax highlighting

## Installation

### Prerequisites
- Python 3.7+
- Chain framework (dependency)
- Rich library for enhanced terminal output

### Install
```bash
git clone <repository-url>
cd twig
pip install -e .
```

## Core Usage Patterns

### Basic Query
```bash
twig "What is machine learning?"
```

### Pipe Content as Context
```bash
# Debug code
cat script.py | twig "Find bugs in this code"

# Analyze logs  
tail -f app.log | twig "Summarize recent errors"

# Process data
curl api.example.com/data | twig "Extract key insights"
```

### Prompt Composition Structure
Twig builds prompts in three parts:
```
<query>        # Your main question
<context>      # Piped content (stdin)  
<append>       # Additional instructions (-a flag)
```

### Advanced Example
```bash
echo "$(cat chain.py)" | \
twig "Review this Python module" \
-a "Focus on error handling and suggest improvements" \
-m "gpt-4" \
-c
```

## Command Reference

### Core Options
- `twig "query"` - Basic query
- `-m, --model MODEL` - Select specific model
- `-c, --chat` - Include conversation history  
- `-s, --shell` - Interactive chat mode
- `-a, --append TEXT` - Append to prompt

### Input/Output
- `-i, --image` - Include clipboard image
- `-r, --raw` - Raw text output (no markdown)
- `-p, --print_input` - Show constructed prompt

### History Management  
- `-l, --last` - Show last response
- `-hi, --history` - View conversation history
- `-g, --get N` - Get specific message by index
- `-cl, --clear` - Clear history

### Model Options
- `-o, --ollama` - Use local Llama model
- `-li, --list` - List available models  
- `-t, --temperature N` - Set response randomness

## Real-World Examples

### Code Review Workflow
```bash
# Get comprehensive code analysis
echo "# $(basename $PWD)\n$(find . -name '*.py' -exec cat {} \;)" | \
twig "Analyze this Python project" \
-a "Check for security issues, performance problems, and suggest architectural improvements"
```

### Log Analysis
```bash
# Continuous monitoring
tail -f /var/log/app.log | twig "Monitor for anomalies and alert on issues"

# Error investigation  
grep ERROR app.log | twig "Categorize these errors and suggest fixes"
```

### Documentation Generation
```bash
# Generate README from code
cat main.py | twig "Create documentation for this script" -a "Include usage examples"
```

### Data Processing
```bash
# Analyze CSV data
cat sales_data.csv | twig "What trends do you see in this sales data?" -a "Provide actionable insights"
```

## Interactive Modes

### Shell Mode
```bash
twig -s  # Enter interactive chat
```

### Chat Mode
```bash
# Maintain conversation context across queries
twig "Explain quantum computing" -c
twig "How does it relate to cryptography?" -c  # References previous exchange
```

## Configuration

Twig stores configuration and history in:
- `.history.pickle` - Conversation history
- `.twig_log.txt` - Query logs

Default model: `claude` (configurable in `preferred_model` variable)

## Integration Examples

### Git Workflow
```bash
# Commit message generation
git diff --cached | twig "Generate a commit message for these changes"

# Code review
git show HEAD | twig "Review this commit" -a "Check for potential issues"
```

### System Administration  
```bash
# Performance analysis
ps aux | twig "Identify resource-intensive processes"

# Configuration review
cat nginx.conf | twig "Optimize this Nginx configuration"
```

## Troubleshooting

**Image paste not working**: Image clipboard functionality requires a desktop environment and is disabled over SSH.

**Slow startup**: The loading spinner indicates Chain framework imports are in progress.

**Model not found**: Use `twig -li` to see available models.

## Development

Built on the [Chain framework](link-to-chain-repo) for LLM interactions. Requires Chain to be installed and configured with your API keys.

### Project Structure
```
twig/
├── twig.py          # Main CLI implementation
├── setup.py         # Package configuration  
└── README.md        # This file
```

## License

MIT License - see LICENSE file for details.

---

**Pro Tip**: Combine twig with standard Unix tools for powerful AI-assisted workflows. The ability to pipe any content as context makes it incredibly versatile for code analysis, log processing, and data interpretation tasks.
