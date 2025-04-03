from llama_index.core.workflow import Event


class ParseFormEvent(Event):
    """Custom event to parse the form."""

    application_form: str
