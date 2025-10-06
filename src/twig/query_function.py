"""
Our default query function -- passed into Twig as a dependency.
Define your own for customization.
"""

from conduit.sync import Prompt, Model, Conduit, Response, Verbosity
from typing import Protocol


# First, our protocol
class QueryFunctionProtocol(Protocol):
    """
    Protocol for a query function. Customized query functions should match this signature.
    """

    def __call__(
        self,
        inputs: dict[str, str],
        preferred_model: str,
        nopersist: bool,
        verbose: Verbosity = Verbosity.PROGRESS,
    ) -> Response: ...


# Now, our default implementation -- the beauty of LLMs with POSIX philosophy
def default_query_function(
    inputs: dict[str, str],
    preferred_model: str,
    nopersist: bool,
    verbose: Verbosity = Verbosity.PROGRESS,
) -> Response:
    """
    Default query function.
    Note that the input dict will contain keys for all possible inputs, from the positional query, piped in context, and a potential "append" string.
    The simplest query functions will likely only want query_input.
    """
    # Extract inputs from dict
    query_input: str = inputs.get("query_input", "")
    context: str = (
        "<context>\n" + inputs.get("context", "") + "\n</context>"
        if inputs.get("context")
        else ""
    )
    append: str = inputs.get("append", "")
    # Twig's default POSIX philosophy: embrace pipes and redirection
    combined_query = "\n\n".join([query_input, context, append])
    # Our chain
    model = Model(preferred_model)
    prompt = Prompt(combined_query)
    conduit = Conduit(prompt=prompt, model=model)
    response = conduit.run(verbose=verbose, nopersist=nopersist)
    assert isinstance(response, Response), "Response is not of type Response"
    return response
