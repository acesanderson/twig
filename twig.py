"""
This adapts Chain framework to a lightweight but flexible command line interface.
With twig, you can query LLMs, and do crazy stuff with pipes and tees.
"""

from rich.console import Console  # for rich output, including spinner

console = Console(width=100)  # for spinner

# Imports are slow (until I refactor Chain to lazy load!), so let's add a spinner.
with console.status(f"[bold green]Loading...[/bold green]", spinner="dots"):
	from rich.markdown import Markdown  # for markdown output
	from Chain import Model, Chain  # for querying models
	import argparse  # for command line arguments
	import sys  # to capture stdin, and sys.exit
	from message_store import MessageStore  # type: ignore -- our own class for storing messages
	import os

file_path = ".history.pickle"
preferred_model = "gpt"  # going local for data security purposes

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


if __name__ == "__main__":
	# Get the path of this file, then the pickle path
	dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"
	file_path = dir_path + file_path
	messagestore = MessageStore(console=console, file_path=file_path)
	# Capture stdin if it's being piped into script
	if not sys.stdin.isatty():
		context = sys.stdin.read()
		# We add this as context to the query
		context = f"\n<context>\n{context}</context>"
	else:
		context = ""
	# Load message store
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
		"-a", "--append", type=str, help="Append to prompt (after context)."
	)
	# parser.add_argument("-c", "--chat", action="store_true", help="Start a chat with this exchange.")
	args = parser.parse_args()
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
		console.print(Chain.models)
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
		[str(args.query), str(context), str(args.append)]
	)  # Str because these can be Nonetype, \n for proper spacing.
	if combined_query:
		messagestore.add("user", combined_query)
		with console.status(f"[bold green]Querying...[/bold green]", spinner="dots"):
			response = model.query(combined_query, verbose=False)
			if args.raw:
				print(response)
			else:
				print_markdown(response)
		messagestore.add("assistant", response)
