"""
Twig is our conduit library as a CLI application.

Customize the query_function to specialize for various prompts / workflows while retaining archival and other functionalities.

To customize:
1. Define your own query function matching the QueryFunctionProtocol signature.
2. Pass your custom function to the Twig class upon instantiation.

This allows you to tailor the behavior of Twig while leveraging its existing features.
"""

from rich.console import Console
from argparse import ArgumentParser, Namespace
from twig.config_loader import ConfigLoader
from twig.logs.logging_config import configure_logging
from twig.handlers import HandlerMixin
from twig.query_function import QueryFunctionProtocol, default_query_function
from conduit.progress.verbosity import Verbosity
from pathlib import Path
import sys

# Defaults
DEFAULT_NAME = "twig"
DEFAULT_DESCRIPTION = "Twig: The LLM CLI"
DEFAULT_QUERY_FUNCTION = default_query_function
DEFAULT_VERBOSITY = Verbosity.COMPLETE
DEFAULT_PREFERRED_MODEL = "claude"
DEFAULT_CONSOLE = Console()
DEFAULT_CACHE_SETTING = True
DEFAULT_PERSISTENT_SETTING = True


class Twig(HandlerMixin):
    """
    Main class for the Twig CLI application.
    Combines argument parsing, configuration loading, and command handling.
    Attributes:
    - name: Name of the CLI application.
    - description: Description of the CLI application.
    - verbosity: Verbosity level for LLM responses.
    - preferred_model: Default LLM model to use.
    - console: Instance of rich.console.Console for rich text output.
    - config: Configuration dictionary loaded from ConfigLoader.
    - attr_mapping: Maps command-line argument names to internal attribute names.
    - command_mapping: Maps command-line argument names to their respective handler method names.
    - flags: Dictionary to hold parsed flag values.
    - parser: ArgumentParser instance for parsing command-line arguments.
    - args: Parsed arguments from the command line.
    - stdin: Captured standard input if piped.
    - query_function: Function to handle queries, adhering to QueryFunctionProtocol.
    - cache: Boolean indicating whether to use caching for LLM responses.
    Methods:
    - setup_parser(): Sets up the argument parser based on the loaded configuration.
    Methods from HandlerMixin:
    - validate_handlers(): Validates that all handlers specified in the config are implemented.
    - all handler methods (e.g., handle_history, handle_wipe, etc.) should be implemented in this class.
    """

    def __init__(
        self,
        name: str = "twig",
        description: str = DEFAULT_DESCRIPTION,
        query_function: QueryFunctionProtocol = DEFAULT_QUERY_FUNCTION,
        verbosity: Verbosity = DEFAULT_VERBOSITY,
        preferred_model: str = DEFAULT_PREFERRED_MODEL,
        console: Console = DEFAULT_CONSOLE,
        cache: bool = DEFAULT_CACHE_SETTING,
        persistent: bool = DEFAULT_PERSISTENT_SETTING,
    ):
        # Set log level up front
        self.logger = configure_logging(level=30)  # WARNING
        self.logger.info("Initializing TwigCLI")
        # Parameters
        self.name: str = name  # Name of the CLI application
        self.description: str = description  # description of the CLI application
        # Query function -- must adhere to QueryFunctionProtocol
        self.query_function: QueryFunctionProtocol = (
            query_function  # function to handle queries
        )
        assert isinstance(query_function, QueryFunctionProtocol), (
            "query_function must adhere to QueryFunctionProtocol"
        )
        # Configs
        self.verbosity: Verbosity = verbosity  # verbosity level for LLM responses
        self.preferred_model: str = preferred_model  # default LLM model
        self.console: Console = console  # rich console for output
        self.cache: bool = cache  # whether to use caching for LLM responses
        # Get XDG paths
        self.history_file: Path
        self.config_dir: Path
        self.cache_file: Path
        self.history_file, self.config_dir, self.cache_file = (
            self._construct_xdg_paths()
        )
        # Persistence
        if persistent:
            self.logger.info(f"Using persistent history at {self.history_file}")
            from conduit.message.messagestore import MessageStore
            from conduit.sync import Conduit

            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            message_store = MessageStore(history_file=self.history_file)
            Conduit.message_store = message_store
        else:
            self.logger.info("Using in-memory history (no persistence)")
        # Cache
        if cache:
            self.logger.info(f"Using cache at {self.cache_file}")
            from conduit.sync import Model
            from conduit.cache.cache import ConduitCache

            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            Model.conduit_cache = ConduitCache(db_path=self.cache_file)
        else:
            self.logger.info("Caching disabled")
        # Set up config
        self.attr_mapping: dict = {}
        self.command_mapping: dict = {}
        self.parser: ArgumentParser | None = None
        self.args: Namespace | None = None
        self.flags: dict = {}  # This will hold all the flag values after parsing
        self.config: dict = ConfigLoader().config
        self._validate_handlers()  # from HandlerMixin

    def run(self):
        """
        Run the CLI application.
        """
        self.logger.info("Running TwigCLI")
        self.stdin: str = self._get_stdin()  # capture stdin if piped
        # Setup parser and parse args
        self.parser = self._setup_parser()
        # If no args, print help and exit
        if len(sys.argv) == 1 and not self.stdin:
            self.parser.print_help(sys.stderr)
            sys.exit(1)
        # Parse args
        self._parse_args()

    def _construct_xdg_paths(self) -> tuple[Path, Path, Path]:
        """
        Construct XDG-compliant paths for history, config, and cache files.
        The name (self.name) is used as the application directory for each.

        Returns a tuple of Paths: (history_file, config_file, cache_file)

        Note: config_file is not currently used but reserved for future use.
        """
        from xdg_base_dirs import xdg_data_home, xdg_config_home, xdg_cache_home

        history_file = xdg_data_home() / self.name / "history.json"
        config_file = xdg_config_home() / self.name / "config.yaml"
        cache_file = xdg_cache_home() / self.name / "cache.sqlite"

        return history_file, config_file, cache_file

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
        else:
            coerced_query_input = query_input
        return coerced_query_input

    def _setup_parser(self):
        """
        Setup the argument parser based on the configuration.
        """
        self.logger.info("Setting up argument parser")
        parser = ArgumentParser()
        parser.description = self.description
        self.attr_mapping = {}
        self.command_mapping = {}

        # Handle positional args (i.e. query string if provided)
        self.logger.info("Adding positional arguments to parser")
        for pos_arg in self.config.get("positional_args", []):
            dest = pos_arg.pop("dest")
            self.attr_mapping[dest] = dest
            parser.add_argument(
                dest,
                **pos_arg,
            )

        # Handle flags
        self.logger.info("Adding flags to parser")
        for flag in self.config["flags"]:
            abbrev = flag.pop("abbrev", None)
            name = flag.pop("name")

            args = [abbrev, name] if abbrev else [name]
            arg_name = name.lstrip("-").replace("-", "_")
            self.attr_mapping[arg_name] = arg_name  # Same as dest
            parser.add_argument(*args, **flag)

        # Handle commands
        self.logger.info("Adding commands to parser")
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
        self.logger.info("Parsing arguments")
        self.args = self.parser.parse_args()
        self.logger.debug(f"Parsed args: {self.args}")

        # Create flags dictionary
        self.logger.info("Creating flags dictionary")
        self.flags = {}
        for arg_name, attr_name in self.attr_mapping.items():
            if hasattr(self.args, arg_name):
                self.flags[attr_name] = getattr(self.args, arg_name)

        # Set logging if requested
        if self.flags.get("log"):
            match self.flags["log"].lower():
                case "d":
                    self.logger.setLevel(10)  # DEBUG
                case "i":
                    self.logger.setLevel(20)  # INFO
                case "w":
                    self.logger.setLevel(30)  # WARNING

        # Coerce query input to string if necessary
        self.flags["query_input"] = self._coerce_query_input(self.flags["query_input"])

        # Check if any commands were specified and execute them
        self.logger.info("Checking for commands to execute")
        for arg_name, handler_name in self.command_mapping.items():
            if getattr(self.args, arg_name, False):
                handler = getattr(self, handler_name)
                if getattr(self.args, arg_name) not in [True, False]:
                    handler(getattr(self.args, arg_name))
                else:
                    handler()
                return

        # If no commands were executed and we have query input, process it
        self.logger.info("No commands executed; checking for query input")
        if self.args.query_input:
            self.query_handler()

    # Debugging methods
    def _print_all_attrs(self, pretty: bool = True):
        """
        Debugging method to print all attributes of the instance.
        """
        self.logger.info("Printing all attributes of the instance")
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
        self.logger.info(f"Getting handler for command: {command_name}")
        handler_name = self.command_mapping.get(command_name)
        if handler_name and hasattr(self, handler_name):
            return getattr(self, handler_name)
        return None
