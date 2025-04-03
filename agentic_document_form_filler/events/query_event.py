from llama_index.core.workflow import Event


class QueryEvent(Event):
    """Custom event to query the resume."""

    query: str
    field: str
