from Chain import MessageStore, ChainCache, Model
from rich.console import Console
from argparse import ArgumentParser
from twig.config_loader import ConfigLoader
from twig.handlers import HandlerMixin


class TwigCLI(HandlerMixin):
    """
    Main class for the Twig CLI application.
    Combines argument parsing, configuration loading, and command handling.
    Attributes:
    - messagestore: Instance of MessageStore to manage messages.
    - console: Instance of rich.console.Console for rich text output.
    - config: Configuration dictionary loaded from ConfigLoader.
    - attr_mapping: Maps command-line argument names to internal attribute names.
    - command_mapping: Maps command-line argument names to their respective handler method names.
    Methods:
    - setup_parser(): Sets up the argument parser based on the loaded configuration.
    Methods from HandlerMixin:
    - validate_handlers(): Validates that all handlers specified in the config are implemented.
    - all handler methods (e.g., handle_history, handle_wipe, etc.) should be implemented in this class.
    """

    def __init__(self):
        self.console = Console()
        self.messagestore = MessageStore(
            history_file=".twig_history.json", pruning=True, console=self.console
        )
        self.config = ConfigLoader().config
        self.validate_handlers()  # from HandlerMixin
        self.parser = self.setup_parser()

    def setup_parser(self):
        parser = ArgumentParser()
        self.attr_mapping = {}
        self.command_mapping = {}

        # Handle flags
        for flag in self.config["flags"]:
            attr = flag.pop("attr")
            abbrev = flag.pop("abbrev", None)
            name = flag.pop("name")

            # Combine into args list for argparse
            args = [abbrev, name] if abbrev else [name]
            arg_name = name.lstrip("-").replace("-", "_")
            self.attr_mapping[arg_name] = attr
            parser.add_argument(*args, **flag)

        # Handle commands
        command_group = parser.add_mutually_exclusive_group()
        for command in self.config["commands"]:
            handler = command.pop("handler")
            abbrev = command.pop("abbrev", None)
            name = command.pop("name")

            args = [abbrev, name] if abbrev else [name]
            arg_name = name.lstrip("-").replace("-", "_")
            self.command_mapping[arg_name] = handler
            command_group.add_argument(*args, **command)

        return parser


if __name__ == "__main__":
    cli = TwigCLI()
