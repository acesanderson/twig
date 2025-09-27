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


class HandlerMixin:
    def validate_handlers(self):
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
