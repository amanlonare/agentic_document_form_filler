import logging

from llama_index.core.workflow import HumanResponseEvent, InputRequiredEvent

from agentic_document_form_filler.lib.config import default_config as config
from agentic_document_form_filler.lib.rag_workflow import RAGWorkflow

logger = logging.getLogger(config.name)


async def fill(res_path: str, form_path: str) -> str:
    """
    Fill the form with the resume.
    Args:
        res_path (str): Path to the resume.
        form_path (str): Path to the form.
    Returns:
        str: The filled form.
    """
    workflow = RAGWorkflow(timeout=600, verbose=False)
    handler = workflow.run(
        resume_file=res_path,
        application_form=form_path,
    )

    async for event in handler.stream_events():
        if isinstance(event, InputRequiredEvent):
            logger.info("We've filled in your form! Here are the results:\n")
            logger.info(event.result)
            # now ask for input from the keyboard
            response = input(event.prefix)
            handler.ctx.send_event(HumanResponseEvent(response=response))

    response = await handler
    return str(response)
