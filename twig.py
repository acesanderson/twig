"""
This adapts Chain framework to a lightweight but flexible command line interface.
With twig, you can query LLMs, and do crazy stuff with pipes and tees.
"""

from rich.console import Console  # for rich output, including spinner
from rich.markdown import Markdown
from Chain import Model, MessageStore, Chain, Chat, ModelStore, ChainCache
import argparse, sys
from pathlib import Path

# Constants
console = Console(width=100)  # for spinner
Model._console = console
dir_path = Path(__file__).parent
Model._chain_cache = ChainCache(
    dir_path / ".twig_cache"
)  # Set the chain cache for Model
history_file = dir_path / ".twig_history.json"
log_file = dir_path / ".twig_log.txt"
preferred_model = "claude"  # we use a different alias for local models

# Load message store
messagestore = MessageStore(
    console=console, history_file=history_file, log_file=log_file, pruning=True
)
Chain._message_store = messagestore  # Set the message store for Chain

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


def grab_image_from_clipboard() -> tuple | None:
    """
    Attempt to grab image from clipboard; return tuple of mime_type and base64.
    """
    import os

    if "SSH_CLIENT" in os.environ or "SSH_TTY" in os.environ:
        console.print("Image paste not available over SSH.", style="red")
        return

    import warnings
    from PIL import ImageGrab
    import base64, io

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Suppress PIL warnings
        image = ImageGrab.grabclipboard()

    if image:
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        # Save for next query
        console.print("Image captured!", style="green")
        # Build our ImageMessage
        image_content = img_base64
        mime_type = "image/png"
        return mime_type, image_content
    else:
        console.print("No image detected.", style="red")
        sys.exit()


def create_image_message(
    combined_query: str, mime_type: str, image_content: str
) -> "ImageMessage | None":
    if not image_content or not mime_type:
        return
    role = "user"
    text_content = combined_query

    from Chain.message.imagemessage import ImageMessage

    imagemessage = ImageMessage(
        role=role,
        text_content=text_content,
        image_content=image_content,
        mime_type=mime_type,
    )
    return imagemessage


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
        "-i",
        "--image",
        action="store_true",
        help="Include an image in clipboard in query.",
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
    parser.add_argument(
        "-s",
        "--shell",
        action="store_true",
        help="Run in shell mode (interactive).",
    )
    args = parser.parse_args()
    temperature = float(args.temperature) if args.temperature else None
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
        console.print(ModelStore.models())
        sys.exit()
    if args.model:
        model = Model(args.model)
    elif args.ollama:
        model = Model("llama3.1:latest")
    else:
        model = Model(preferred_model)
    # If we want to chat so much that we want a shell, we use the Chat class.
    if args.shell:
        chat = Chat(model=model, console=console, messagestore=messagestore)
        chat.chat()
        sys.exit()
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
    # Construct message to add to message store.
    if combined_query.strip():
        if args.image:
            mime_type, image_content = grab_image_from_clipboard()
            imagemessage = create_image_message(
                combined_query, mime_type, image_content
            )
            messagestore.append(imagemessage)
        else:
            from Chain.message.textmessage import TextMessage

            textmessage = TextMessage(role="user", content=combined_query)
            messagestore.append(textmessage)
    # Check that we have messagestore.
    assert len(messagestore) > 0, "No messages in message store."
    # Now to generate our responses.
    from Chain.progress.verbosity import Verbosity

    ## Option 1: If we want to chat, we pass the message history to the model.
    if args.chat:
        # Construct a chain, which orchestrates persistence.
        chain = Chain(model=model)
        response = chain.run()
        response = model.query(
            query_input=messagestore.messages,
            temperature=temperature,
            verbose=Verbosity.SUMMARY,
        )
        if args.raw:
            print(response)
        else:
            print_markdown(response)
    ## Option 2: If we just want a one-off query, we pass only the final message (i.e. combined_query).
    else:
        response = model.query(
            query_input=messagestore.messages[-1],
            temperature=temperature,
            verbose=Verbosity.SUMMARY,
        )
        # Save the response to message store.
        messagestore.append(response.message)
        if args.raw:
            print(response)
        else:
            print_markdown(response)


if __name__ == "__main__":
    main()
