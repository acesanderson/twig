Here's how to restructure this using common patterns:

1. Command Pattern for argument handling:
```python
class CommandHandler:
    def __init__(self, messagestore, model):
        self.messagestore = messagestore
        self.model = model

    def handle_clear(self):
        self.messagestore.clear()
        sys.exit()

    def handle_last(self, raw):
        content = self.messagestore.last().content
        self._print_output(content, raw)
        sys.exit()

    def handle_query(self, query, context, append, chat, raw):
        combined_query = self._build_query(query, context, append)
        if combined_query.strip():
            self.messagestore.add_new("user", combined_query)
            response = self._get_response(combined_query, chat)
            self._print_output(response, raw)
            self.messagestore.add_new("assistant", response)

    def _build_query(self, query, context, append):
        return "\n".join([
            str(query) if query else "",
            str(context) if context else "",
            str(append) if append else "",
        ])
```

2. Factory Pattern for model creation:
```python
class ModelFactory:
    @staticmethod
    def create_model(args):
        if args.model:
            return Model(args.model)
        elif args.ollama:
            return Model("llama3.1:latest")
        return Model(preferred_model)
```

3. Main function becomes orchestrator:
```python
def main():
    args = parse_arguments()
    context = get_stdin_context()
    
    model = ModelFactory.create_model(args)
    handler = CommandHandler(messagestore, model)

    if args.clear:
        handler.handle_clear()
    elif args.last:
        handler.handle_last(args.raw)
    elif args.query or context or args.append:
        handler.handle_query(args.query, context, args.append, args.chat, args.raw)
```

This restructuring:
1. Separates concerns
2. Makes code more testable
3. Reduces cognitive load
4. Makes flow more explicit
5. Easier to maintain and extend

The main architectural patterns applied here are:
- Command Pattern
- Factory Pattern
- Dependency Injection
- Single Responsibility Principle

Each class/function has one job and the flow is more clearly defined.
