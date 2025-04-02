import logging

from pydantic import BaseModel

logger = logging.getLogger('agenticDocumentFiller.config')


class Config(BaseModel):
    name: str = 'agentic_document_form_filler'
    log_level: str = logging.DEBUG


default_config: Config = Config.factory()
