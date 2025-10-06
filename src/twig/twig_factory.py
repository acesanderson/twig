"""
Customize Twig quickly with a query function, if you don't worry about custom parameters.
A simple query_function that ONLY takes query_input and returns a Response object is enough.
"""

from twig.twig_class import Twig, DEFAULT_PREFERRED_MODEL, DEFAULT_VERBOSITY
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from conduit.sync import Verbosity


def wrap_query_function(query_function):
    """
    Wrap a simple query function to match the expected signature for Twig.

    Discard extra parameters, as well as extra context (i.e. contex / append).
    """

    def wrapped(
        inputs: dict[str, str],
        preferred_model: str = DEFAULT_PREFERRED_MODEL,
        verbose: "Verbosity" = DEFAULT_VERBOSITY,
        nopersist: bool = False,
    ):
        query_input = inputs.get("query_input", "")
        _ = preferred_model  # Discarded
        _ = verbose  # Discarded
        _ = nopersist  # Discarded
        return query_function(query_input)

    return wrapped


def twig_factory(query_function) -> Twig:
    """
    Factory function to create a Twig instance with a simple query function.
    """
    wrapped_function = wrap_query_function(query_function)
    twig_instance = Twig(query_function=wrapped_function)
    return twig_instance
