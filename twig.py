"""
This adapts Chain framework to a lightweight but flexible command line interface.
With twig, you can query LLMs, and do crazy stuff with pipes and tees.
"""

from rich.console import Console            # for rich output, including spinner
console = Console(width=80) # for spinner

# Imports are slow (until I refactor Chain to lazy load!), so let's add a spinner.
with console.status(f'[bold green]Loading...[/bold green]', spinner="dots"):
    from Chain import Model, Chain              # for querying models
    import argparse                             # for command line arguments
    import sys                                  # to capture stdin, and sys.exit

# Our functions

def query(model, query):
    chain = Chain(model)
    response = chain.run(query)
    return response

if __name__ == "__main__":
    # Capture stdin if it's being piped into script
    if not sys.stdin.isatty():
        context = sys.stdin.read()
        # We add this as context to the query
        context = f"\n<context>\n{context}</context>"
    else:
        context = None
    # Capture arguments
    parser = argparse.ArgumentParser(description="Twig: A lightweight command line interface for Chain framework.")
    parser.add_argument("query", type=str, nargs="?", help="Query string to be executed.")
    parser.add_argument("-m", "--model", type=str, help="Model file to be used.")
    parser.add_argument("-l", "--list", action="store_true", help="List all available models.")
    args = parser.parse_args()
    if args.list:
        console.print(Chain.models)
        sys.exit()
    if args.model:
        model = Model(args.model)
    else:
        model = Model("gpt")
    if args.query:
        with console.status(f'[bold green]Querying...[/bold green]', spinner="dots"):
            response = model.query(args.query + context, verbose=False)
            console.print(response)


