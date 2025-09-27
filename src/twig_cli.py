from Chain import MessageStore
from rich.console import Console
from argparse import ArgumentParser
from importlib.resources import files
import json

config_path = files("twig").joinpath("args.json")

# We need python type objects when we deserialize config from JSON.
## "type" should grab values from this dict.
TYPE_MAP = {"str": str, "int": int, "float": float, "bool": bool}


# Argument definitions
class TwigCLI:
    def __init__(self):
        self.messagestore = MessageStore()
        self.console = Console()

    def _validate_args(self) -> bool:
        """
        Ensure that create_parser arguments match our Flags and Commands attributes.
        """

    def create_parser(self) -> ArgumentParser:
        """
        All of our argparse setup lives here.
        """
        parser = ArgumentParser(
            description="Twig CLI - Interact with Twig AI from the command line"
        )

        # Global flags
        parser.add_argument(
            "-m",
            "--model",
            type=str,
            help="Specify the model to use; defaults to 'claude'",
            default="claude",
        )
        parser.add_argument(
            "-L",
            "--local",
            action="store_true",
            help="Use local SiphonServer instead of remote API",
        )
        parser.add_argument(
            "-r",
            "--raw",
            action="store_true",
            help="Print raw output without markdown formatting",
        )
        parser.add_argument(
            "-t",
            "--temperature",
            type=float,
            help="Set the temperature for the model (0.0 to 1.0)",
        )
        parser.add_argument(
            "-c",
            "--chat",
            action="store_true",
            help="Enable chat mode to include message history - i.e. remember previous messages",
        )

        # Commands
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-h", "--history", action="store_true", help="View message history"
        )
        group.add_argument(
            "-w", "--wipe", action="store_true", help="Wipe message history"
        )
        group.add_argument(
            "-s", "--shell", action="store_true", help="Enter interactive shell mode"
        )
        group.add_argument(
            "-l", "--last", action="store_true", help="Get the last message"
        )
        group.add_argument(
            "-g", "--get", type=int, help="Get a specific message from history"
        )

        # Positional argument for query
        parser.add_argument(
            "query",
            type=str,
            nargs="?",
            help="The query string to be executed",
        )
        return parser
