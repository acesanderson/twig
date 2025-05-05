"""
This adapts Chain framework to a lightweight but flexible command line interface.
With twig, you can query LLMs, and do crazy stuff with pipes and tees.
"""

from rich.console import Console  # for rich output, including spinner

console = Console(width=100)  # for spinner

# Imports are slow (until I refactor Chain to lazy load!), so let's add a spinner.
with console.status(f"[green]Loading...[/green]", spinner="dots"):
    from rich.markdown import Markdown  # for markdown output
    from Chain import Model, MessageStore, Chain  # for querying models
    import argparse  # for command line arguments
    import sys  # to capture stdin, and sys.exit
    from pathlib import Path  # for file paths

# Constants
dir_path = Path(__file__).parent
history_file = dir_path / ".history.pickle"
log_file = dir_path / ".twig_log.txt"

preferred_model = "claude"  # we use a different alias for local models

# Load message store
messagestore = MessageStore(
    console=console, history_file=history_file, log_file=log_file, pruning=True
)
Chain._message_store = messagestore

# Our functions


def print_markdown(markdown_string: str):
    """
    Prints formatted markdown to the console.
    """
    # Create a Markdown object
    border = "-" * 100
    markdown_string = f"{border}\n{markdown_string}\n\n{border}"
    md = Markdown(markdown_string)
    console.print(md)


# Main
# ------------------------------------------------------------------------------


def main():
    # Capture stdin if it's being piped into script
    if not sys.stdin.isatty():
        context = sys.stdin.read()
        # We add this as context to the query
        context = f"\n<context>\n{context}</context>"
    else:
        context = ""
    # Load message store
    messagestore.load()
    # Capture arguments
    parser = argparse.ArgumentParser(
        description="Twig: A lightweight command line interface for Chain framework."
    )
    parser.add_argument(
        "query", type=str, nargs="?", help="Query string to be executed."
    )
    parser.add_argument("-m", "--model", type=str, help="Model file to be used.")
    parser.add_argument(
        "-li", "--list", action="store_true", help="List all available models."
    )
    parser.add_argument(
        "-o", "--ollama", action="store_true", help="Use llama3.1 locally."
    )
    parser.add_argument(
        "-r", "--raw", action="store_true", help="Print raw output (not markdown)."
    )
    parser.add_argument(
        "-l", "--last", action="store_true", help="Return the last output."
    )
    parser.add_argument(
        "-hi", "--history", action="store_true", help="Access the history."
    )
    parser.add_argument("-g", "--get", type=int, help="Get a message from the history.")
    parser.add_argument(
        "-cl", "--clear", action="store_true", help="Clear the history."
    )
    parser.add_argument(
        "-t",
        "--temperature",
        type=str,
        help="Set temperature for query (0-1 for OpenAI, 0-2 for Anthropic and Gemini).",
    )
    parser.add_argument(
        "-a", "--append", type=str, help="Append to prompt (after context)."
    )
    parser.add_argument(
        "-p",
        "--print_input",
        action="store_true",
        help="Print the input (useful when piping and debugging).",
    )
    parser.add_argument(
        "-c",
        "--chat",
        action="store_true",
        help="Pass message history to model (i.e. chat).",
    )
    args = parser.parse_args()
    if args.temperature:
        temperature = float(args.temperature)
    else:
        temperature = None
    if args.print_input:
        if context:
            print(context)
        else:
            print("No input provided.")
    if args.clear:
        messagestore.clear()
        sys.exit()
    if args.last:
        if args.raw:
            print(messagestore.last().content)
        else:
            print_markdown(messagestore.last().content)
        sys.exit()
    if args.history:
        messagestore.view_history()
        sys.exit()
    if args.get:
        if args.raw:
            print(messagestore.get(args.get).content)
        else:
            print_markdown(messagestore.get(args.get).content)
        sys.exit()
    if args.list:
        console.print(Model.models)
        sys.exit()
    if args.model:
        model = Model(args.model)
    elif args.ollama:
        model = Model("llama3.1:latest")
    else:
        model = Model(preferred_model)
    """
    Our prompt is the query, context, and append.
    Query is the default here.
    Context is grabbed from stdin.
    Append is an optional addition by user.
    """
    combined_query = "\n".join(
        [
            str(args.query) if args.query is not None else "",
            str(context) if context is not None else "",
            str(args.append) if args.append is not None else "",
        ]
    )  # If these are nonetype, return empty string, not "None", \n for proper spacing.
    if combined_query.strip():
        messagestore.add_new("user", combined_query)
        with console.status(f"[green]Querying...[green]", spinner="dots"):
            # If we want to chat, we pass the message history to the model.
            if args.chat:
                response = model.query(
                    input=messagestore.messages, temperature=temperature, verbose=True
                )
                if args.raw:
                    print(response)
                else:
                    print_markdown(response)
            # Default is a one-off, i.e. a single message object.
            else:
                response = model.query(
                    combined_query, temperature=temperature, verbose=True
                )
                if args.raw:
                    print(response)
                else:
                    print_markdown(response)
        messagestore.add_new("assistant", response)


if __name__ == "__main__":
    main()
