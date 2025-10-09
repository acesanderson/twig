# Twig

A command-line interface for LLM interactions built on top of the Conduit framework. Twig provides POSIX-style interaction patterns with pipes, redirection, and persistent message history.

## Project Purpose

Twig is a CLI wrapper around the Conduit LLM framework that enables terminal-based LLM queries with support for piped input, persistent conversation history, caching, and customizable query handlers. It follows POSIX conventions for composability with standard Unix tools while providing features like message archival, image input from clipboard, and flexible model selection.

## Architecture Overview

- **Twig**: Main CLI application class that orchestrates argument parsing, configuration loading, and command execution. Manages persistence, caching, and XDG-compliant file paths.
- **HandlerMixin**: Provides command handlers for history management, query processing, and utility operations. Implements validation logic to ensure all configured handlers exist.
- **ConfigLoader**: Loads and deserializes CLI configuration from JSON, rehydrating type annotations for argument parsing.
- **QueryFunctionProtocol**: Protocol defining the signature for query functions. Enables custom query implementations while maintaining interface compatibility.
- **default_query_function**: Default implementation that combines query input, piped context, and append strings into LLM prompts via Conduit.
- **twig_factory**: Factory function to wrap simple query functions into full Twig instances with minimal configuration.

## Dependencies

Major dependencies (inferred from imports):
- **conduit**: Core LLM framework providing Model, Response, Prompt, MessageStore, and caching infrastructure (appears to be a local/internal dependency)
- **rich**: Terminal formatting and progress indicators
- **xdg-base-dirs**: XDG Base Directory specification compliance
- **Pillow (PIL)**: Image processing for clipboard operations
- **argparse**: Command-line argument parsing (standard library)

## API Documentation

### Twig Class

```python
class Twig(HandlerMixin):
    def __init__(
        self,
        name: str = "twig",
        description: str = "Twig: The LLM CLI",
        query_function: QueryFunctionProtocol = default_query_function,
        verbosity: Verbosity = Verbosity.COMPLETE,
        preferred_model: str = "claude",
        console: Console = Console(),
        cache: bool = True,
        persistent: bool = True,
    )
```

Main CLI application class. Instantiate with custom parameters to modify behavior.

**Key Parameters:**
- `query_function`: Custom query handler matching QueryFunctionProtocol
- `preferred_model`: Default LLM model identifier
- `cache`: Enable/disable response caching
- `persistent`: Enable/disable message history persistence

**Methods:**
- `run()`: Execute the CLI application with parsed arguments

### twig_factory

```python
def twig_factory(query_function) -> Twig
```

Factory function to create Twig instances from simple query functions. Wraps functions that only accept `query_input` and return `Response` objects.

**Parameters:**
- `query_function`: Function accepting query string and returning Response

**Returns:** Configured Twig instance

### default_query_function

```python
def default_query_function(
    inputs: dict[str, str],
    preferred_model: str,
    include_history: bool,
    verbose: Verbosity = Verbosity.PROGRESS,
) -> Response
```

Default query implementation combining query input, piped context, and append strings.

**Parameters:**
- `inputs`: Dictionary with keys "query_input", "context", "append"
- `preferred_model`: Model identifier string
- `include_history`: Whether to include message history in query
- `verbose`: Verbosity level for output

**Returns:** Response object from Conduit framework

### QueryFunctionProtocol

Protocol defining the required signature for custom query functions:

```python
class QueryFunctionProtocol(Protocol):
    def __call__(
        self,
        inputs: dict[str, str],
        preferred_model: str,
        include_history: bool,
        verbose: Verbosity = Verbosity.PROGRESS,
    ) -> Response: ...
```

## Usage Examples

### Basic CLI Usage

```bash
# Simple query
twig "What is the capital of France?"

# Query with piped context
cat document.md | twig "Summarize this document"

# Chat mode with history
twig --chat "Continue our previous conversation"

# View message history
twig --history

# Use specific model
twig --model gpt-4 "Explain quantum computing"
```

### Programmatic Usage with Default Configuration

```python
from twig.twig_class import Twig

# Create and run CLI with defaults
twig = Twig()
twig.run()
```

### Custom Query Function with Factory

```python
from twig.twig_factory import twig_factory
from conduit.sync import Model, Prompt, Conduit, Response

def custom_query(query_input: str) -> Response:
    """Custom handler that adds system instructions."""
    model = Model("claude")
    enhanced_prompt = f"Be concise. {query_input}"
    prompt = Prompt(enhanced_prompt)
    conduit = Conduit(prompt=prompt, model=model)
    return conduit.run()

# Create custom Twig instance
custom_twig = twig_factory(custom_query)
custom_twig.run()
```

### Advanced Customization

```python
from twig.twig_class import Twig
from conduit.sync import Response, Verbosity

def specialized_query(
    inputs: dict[str, str],
    preferred_model: str,
    include_history: bool,
    verbose: Verbosity = Verbosity.PROGRESS,
) -> Response:
    """Specialized query handler with custom logic."""
    query = inputs.get("query_input", "")
    # Custom preprocessing
    processed_query = f"SPECIALIZED: {query}"
    # Use Conduit framework for actual query
    from conduit.sync import Model, Prompt, Conduit
    model = Model(preferred_model)
    conduit = Conduit(prompt=Prompt(processed_query), model=model)
    return conduit.run(verbose=verbose, include_history=include_history)

# Instantiate with custom configuration
twig = Twig(
    query_function=specialized_query,
    preferred_model="gpt-4",
    cache=True,
    persistent=True,
    verbosity=Verbosity.COMPLETE
)
twig.run()
```