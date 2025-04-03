import logging
import os

from pydantic import BaseModel

logger = logging.getLogger("agenticDocumentFiller.config")


class Config(BaseModel):
    """
    Configuration for the agentic document form filler.
    """

    name: str = "agentic_document_form_filler"
    log_level: str = logging.DEBUG
    groq_api_key: str = "YOUR_GROQ_API_KEY"
    llama_index_api_key: str = "YOUR_LLAMA_INDEX_API_KEY"
    storage_dir: str = "./storage"
    groq_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    @classmethod
    def factory(cls) -> "Config":
        """Configuration reader."""
        # overwrite configs by environment variables
        config = cls()
        config.groq_api_key = os.getenv("GROQ_API_KEY", config.groq_api_key)
        config.llama_index_api_key = os.getenv(
            "LLAMA_INDEX_API_KEY", config.llama_index_api_key
        )
        config.storage_dir = os.getenv("STORAGE_DIR", config.storage_dir)
        config.groq_model = os.getenv("GROQ_MODEL", config.groq_model)
        config.embedding_model = os.getenv("EMBEDDING_MODEL",
                                           config.embedding_model)

        return config


default_config: Config = Config.factory()
