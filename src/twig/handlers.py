"""
Some guidelines for this Mixin:
- all methods must have the signature (self, *args, **kwargs)
- if the config file specifies a type for a command or flag, it must be one of: str, int, float, bool, and the method must handle that type accordingly
- the method names must match the handler names in the config file exactly, a la "handle_history", "handle_wipe", etc.

"handler": "handle_history"
"handler": "handle_wipe"
"handler": "handle_shell"
"handler": "handle_last"
"handler": "handle_get"
"type": "int",
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from Chain.message.imagemessage import ImageMessage


class HandlerMixin:
    def _validate_handlers(self):
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
        from rich.markdown import Markdown
        from rich.console import Console

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
            import sys

            sys.exit()

    def create_image_message(
        self, combined_query: str, mime_type: str, image_content: str
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

    # Handlers -- should match config file exactly (per validate_handlers)
    def handle_history(self):
        pass

    def handle_wipe(self):
        pass

    def handle_shell(self):
        pass

    def handle_last(self):
        pass

    def handle_get(self, index: int):
        pass

    def query(self):
        ...
        # Create combined query.

        # combined_query = "\n".join(
        #     [
        #         str(args.query) if args.query is not None else "",
        #         str(context) if context is not None else "",
        #         str(args.append) if args.append is not None else "",
        #     ]
        # )  # If these are nonetype, return empty string, not "None", \n for proper spacing.
        # # Construct message to add to message store.
        # if combined_query.strip():
        #     if args.image:
        #         mime_type, image_content = grab_image_from_clipboard()
        #         imagemessage = create_image_message(
        #             combined_query, mime_type, image_content
        #         )
        #         messagestore.append(imagemessage)
        #     else:
        #         from Chain.message.textmessage import TextMessage
        #
        #         textmessage = TextMessage(role="user", content=combined_query)
        #         messagestore.append(textmessage)
        # assert len(messagestore.messages) > 0, (
        #     "Message store is empty. Please provide a query."
        # )
        # # Now to generate our responses.
        # from Chain.progress.verbosity import Verbosity
        #
        # ## Option 1: If we want to chat, we pass the message history to the model.
        # if args.chat:
        #     # Construct a chain, which orchestrates persistence.
        #     response = model.query(
        #         query_input=messagestore.messages,
        #         temperature=temperature,
        #         verbose=Verbosity.SUMMARY,
        #     )
        #     if args.raw:
        #         print(response)
        #     else:
        #         print_markdown(response)
        # ## Option 2: If we just want a one-off query, we pass only the final message (i.e. combined_query).
        # else:
        #     response = model.query(
        #         query_input=messagestore.messages[-1],
        #         temperature=temperature,
        #         verbose=Verbosity.SUMMARY,
        #     )
        #     # Save the response to message store.
        #     messagestore.append(response.message)
        #     if args.raw:
        #         print(response)
        #     else:
        #         print_markdown(response)
