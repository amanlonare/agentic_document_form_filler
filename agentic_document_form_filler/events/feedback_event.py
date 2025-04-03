from llama_index.core.workflow import Event


class FeedbackEvent(Event):
    """Custom event to return the feedback."""

    feedback: str
