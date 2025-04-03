# Agentic Document Form Filler

An AI-powered tool that automatically fills out application forms using information from resumes. The tool uses RAG (Retrieval Augmented Generation) to extract relevant information and provide accurate form responses.

## Features

- Automated form field extraction from PDF documents
- Intelligent resume parsing and information retrieval
- Interactive feedback system for response validation
- Support for various resume formats
- Human-in-the-loop verification
- RAG-based accurate information extraction

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Groq API key
- LlamaIndex API key

### From Source
```bash
git clone https://github.com/amanlonare/agentic_document_form_filler.git
cd agentic_document_form_filler
make install
```

## Environment Setup

Create a `.env` file in your project root:

```ini
# Highlight important configuration
GROQ_API_KEY=your_groq_api_key                  # Required
LLAMA_INDEX_API_KEY=your_llama_index_api_key    # Required
LLAMA_CLOUD_BASE_URL=your_llama_cloud_base_url  # Optional
```

You can also export them as environment variable with their respective name as defined in the `agentic_document_form_filler/lib/config.py`.