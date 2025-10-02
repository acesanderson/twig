from rich.console import Console
from argparse import ArgumentParser
from twig.config_loader import ConfigLoader
from twig.logs.logging_config import configure_logging
from twig.handlers import HandlerMixin
from conduit.progress.verbosity import Verbosity
import sys

logger = configure_logging(level=30)  # WARNING
console = Console()
DEFAULT_VERBOSITY = Verbosity.COMPLETE


class TwigCLI(HandlerMixin):
    """
    Main class for the Twig CLI application.
    Combines argument parsing, configuration loading, and command handling.
    Attributes:
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

    description: str = "Twig: The LLM CLI"

    def __init__(self, cache: bool = True, verbosity: Verbosity = DEFAULT_VERBOSITY):
        logger.info("Initializing TwigCLI")
        # Basic constants
        self.console = console  # rich console for output
        self.verbosity = verbosity  # verbosity level for LLM responses
        self.cache = cache  # whether to use caching for LLM responses
        # Set up cache
        self.config: dict = ConfigLoader().config
        self._validate_handlers()  # from HandlerMixin
        self.stdin: str = self._get_stdin()  # capture stdin if piped
        # Setup parser and parse args
        self.flags: dict = {}  # This will hold all the flag values after parsing
        self.parser: ArgumentParser = self._setup_parser()
        # If no args, print help and exit
        if len(sys.argv) == 1 and not self.stdin:
            self.parser.print_help(sys.stderr)
            sys.exit(1)
        # Parse args
        self._parse_args()

    def _get_stdin(self) -> str:
        """
        Get implicit context from clipboard or other sources.
        """
        context = sys.stdin.read() if not sys.stdin.isatty() else ""
        return context

    def _coerce_query_input(self, query_input: str | list) -> str:
        """
        Coerce query input to a string.
        If input is a list, join with spaces.
        """
        if isinstance(query_input, list):
            coerced_query_input = " ".join(query_input)
        elif isinstance(query_input, str):
            coerced_query_input = query_input
        return coerced_query_input

    def _setup_parser(self):
        """
        Setup the argument parser based on the configuration.
        """
        parser = ArgumentParser()
        parser.description = TwigCLI.description
        self.attr_mapping = {}
        self.command_mapping = {}

        # Handle positional args (i.e. query string if provided)
        for pos_arg in self.config.get("positional_args", []):
            dest = pos_arg.pop("dest")
            self.attr_mapping[dest] = dest
            parser.add_argument(
                dest,
                **pos_arg,
            )

        # Handle flags
        # Handle flags
        for flag in self.config["flags"]:
            abbrev = flag.pop("abbrev", None)
            name = flag.pop("name")

            args = [abbrev, name] if abbrev else [name]
            arg_name = name.lstrip("-").replace("-", "_")
            self.attr_mapping[arg_name] = arg_name  # Same as dest
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

    def _parse_args(self):
        """
        Parse arguments and execute commands or prepare for query processing.
        """
        self.args = self.parser.parse_args()

        # Create flags dictionary
        self.flags = {}
        for arg_name, attr_name in self.attr_mapping.items():
            if hasattr(self.args, arg_name):
                self.flags[attr_name] = getattr(self.args, arg_name)

        # Coerce query input to string if necessary
        self.flags["query_input"] = self._coerce_query_input(self.flags["query_input"])

        # Check if any commands were specified and execute them
        for arg_name, handler_name in self.command_mapping.items():
            if getattr(self.args, arg_name, False):
                handler = getattr(self, handler_name)
                if getattr(self.args, arg_name) not in [True, False]:
                    handler(getattr(self.args, arg_name))
                else:
                    handler()
                return

        # If no commands were executed and we have query input, process it
        if self.args.query_input:
            self.query()

    # Debugging methods
    def _print_all_attrs(self, pretty: bool = True):
        """
        Debugging method to print all attributes of the instance.
        """
        if pretty:
            from rich.pretty import Pretty

            self.console.print(Pretty(vars(self)))
            return
        else:
            attrs = vars(self)
            for attr, value in attrs.items():
                print(f"{attr}: {value}")

    def _get_handler_for_command(self, command_name: str):
        """
        Given a command-line argument name, return the corresponding handler method.
        """
        handler_name = self.command_mapping.get(command_name)
        if handler_name and hasattr(self, handler_name):
            return getattr(self, handler_name)
        return None


def main():
    TwigCLI()


if __name__ == "__main__":
    main()
