"""
Some guidelines for this Mixin:
- all methods must have the signature (self, *args, **kwargs)
- if the config file specifies a type for a command or flag, it must be one of: str, int, float, bool, and the method must handle that type accordingly
- the method names must match the handler names in the config file exactly, a la "handle_history", "handle_wipe", etc.
"""

from twig.logs.logging_config import get_logger
from conduit.sync import Conduit, Verbosity
from rich.markdown import Markdown
from rich.console import Console
import sys

logger = get_logger(__name__)

# Constants
DEFAULT_VERBOSITY = Verbosity.PROGRESS


class HandlerMixin:
    def _validate_handlers(self):
        logger.debug("Validating handlers...")
        self.config: dict  # TwigCLI has self.config (generated from ConfigLoader)
        for command in self.config["commands"]:
            handler_name = command.get("handler")
            if not hasattr(self, handler_name):
                raise ValueError(
                    f"Handler {handler_name} not implemented in {self.__class__.__name__}"
                )
            if not callable(getattr(self, handler_name)):
                raise ValueError(
                    f"Handler {handler_name} is not callable in {self.__class__.__name__}"
                )

    # Convenience methods
    def print_markdown(self, markdown_string: str):
        """
        Prints formatted markdown to the console.
        """
        # Create a Markdown object
        border = "-" * 100
        markdown_string = f"{border}\n{markdown_string}\n\n{border}"
        md = Markdown(markdown_string)
        self.console: Console
        self.console.print(md)

    def grab_image_from_clipboard(self) -> tuple | None:
        """
        Attempt to grab image from clipboard; return tuple of mime_type and base64.
        """
        logger.info("Attempting to grab image from clipboard...")
        import os

        if "SSH_CLIENT" in os.environ or "SSH_TTY" in os.environ:
            self.console.print("Image paste not available over SSH.", style="red")
            return

        import warnings
        from PIL import ImageGrab
        import base64, io

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress PIL warnings
            image = ImageGrab.grabclipboard()

        if image:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")  # type: ignore
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            # Save for next query
            self.console.print("Image captured!", style="green")
            # Build our ImageMessage
            image_content = img_base64
            mime_type = "image/png"
            return mime_type, image_content
        else:
            self.console.print("No image detected.", style="red")

            sys.exit()

    def create_image_message(
        self, combined_query: str, mime_type: str, image_content: str
    ) -> "ImageMessage | None":
        logger.info("Creating ImageMessage...")
        if not image_content or not mime_type:
            return
        role = "user"
        text_content = combined_query

        from conduit.message.imagemessage import ImageMessage

        imagemessage = ImageMessage(
            role=role,
            text_content=text_content,
            image_content=image_content,
            mime_type=mime_type,
        )
        return imagemessage

    # Handlers -- should match config file exactly (per validate_handlers)
    def handle_history(self):
        """
        View message history and exit.
        """
        logger.info("Viewing message history...")
        Conduit.message_store.view_history()
        sys.exit()

    def handle_wipe(self):
        """
        Clear the message history after user confirmation.
        """
        logger.info("Wiping message history...")
        from rich.prompt import Confirm

        confirm = Confirm.ask(
            "[red]Are you sure you want to wipe the message history? This action cannot be undone.[/red]",
            default=False,
        )
        if confirm:
            Conduit.message_store.clear()
            self.console.print("[green]Message history wiped.[/green]")
        else:
            self.console.print("[yellow]Wipe cancelled.[/yellow]")

    def handle_shell(self):
        pass

    def handle_last(self):
        """
        Print the last message in the message store and exit.
        """
        logger.info("Viewing last message...")
        import sys

        # Get last message
        last_message = Conduit.message_store.last()
        # If no messages, inform user
        if not last_message:
            self.console.print("[red]No messages in history.[/red]")
            sys.exit()
        # Print last message
        if self.flags["raw"]:
            print(last_message)
        else:
            self.print_markdown(str(last_message))
        sys.exit()

    def handle_get(self, index: int):
        pass

    def query_handler(self):
        """
        Handle a query by combining query input, context, and append, then sending to model.

        Simplest usage:
            `twig "What is the capital of France?"`
        Maximal usage:
            `cat "some_document.md" | twig -q "Look at this doc." -a " Please summarize."`
        """
        logger.info("Handling query...")
        # Type hints since mixins confuse IDEs
        self.flags: dict
        self.stdin: str
        self.verbosity: Verbosity

        # Assemble the parts of the query
        logger.debug("Assembling query parts...")
        inputs = {
            "query_input": self.flags.get("query_input", ""),
            "context": f"<context>{self.stdin}</context>" if self.stdin else "",
            "append": self.flags.get("append") or "",
        }

        # Grab our flags
        logger.debug("Grabbing flags...")
        ## NOTE: we need to implement temperature, image, and other flags here.
        chat = self.flags["chat"]
        raw = self.flags["raw"]
        preferred_model = self.flags["model"]
        # Start our spinner
        with self.console.status(
            "[bold green]Thinking...[/bold green]", spinner="dots"
        ):
            # Our switch logic
            match (chat, raw):
                case (False, False):  # One-off request, pretty print
                    logger.debug("One-off request, pretty print...")
                    response = self.query_function(
                        inputs,
                        preferred_model=preferred_model,
                        verbose=self.verbosity,
                        nopersist=True,
                    )
                    self.print_markdown(str(response.content))
                    sys.exit()
                case (False, True):  # One-off request, raw print
                    logger.debug("One-off request, raw print...")
                    response = self.query_function(
                        inputs,
                        preferred_model=preferred_model,
                        verbose=self.verbosity,
                        nopersist=True,
                    )
                    print(response)
                    sys.exit()
                case (True, False):  # Chat (with history), pretty print
                    logger.debug("Chat (with history), pretty print...")
                    response = self.query_function(
                        inputs,
                        preferred_model=preferred_model,
                        verbose=self.verbosity,
                        nopersist=False,
                    )
                    print(response)
                    sys.exit()
                case (True, True):  # Chat (with history), raw print
                    logger.debug("Chat (with history), raw print...")
                    response = self.query_function(
                        inputs,
                        preferred_model=preferred_model,
                        verbose=self.verbosity,
                        nopersist=False,
                    )
                    print(response)
                    sys.exit()
