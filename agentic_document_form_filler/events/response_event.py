from llama_index.core.workflow import Event


class ResponseEvent(Event):
    """Custom event to return the response."""

    response: str
