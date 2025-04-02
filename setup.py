import os
import re
import sys

from setuptools import find_packages, setup

src_path = os.path.dirname(os.path.abspath(__file__))
old_path = os.getcwd()
os.chdir(src_path)
sys.path.insert(0, src_path)

PACKAGE_NAME = 'agentic_document_form_filler'

requires = [
    'pydantic~=2.8', 'ipykernel', 'ipython', 'python-dotenv',
    'nest-asyncio', 'llama-parse', 'llama-index',
    'llama-index-embeddings-huggingface', 'ipywidgets',
    'llama-index-llms-groq',
]
extras_requires = {
}

with open(os.path.join(
        os.path.dirname(__file__), PACKAGE_NAME, '__init__.py'), 'r') as f:
    m = re.search(r'''__version__ = ['"]([0-9.]+)['"]''', f.read())
    version = m.group(1) if m is not None else ''

setup(
    name='agentic-document-form-filler',
    version=version,
    description='fill application form based on the document',
    author='Aman Lonare',
    author_email='amanlonare95@gmail.com',
    url='https://github.com/amanlonare/agentic_document_form_filler',
    install_requires=requires,
    # `pip install agentic_document_form_filler[base|dev|test]` or
    # `pip install -e ".[dev]"`
    extras_require=extras_requires,
    packages=find_packages(
        include=[PACKAGE_NAME, f'{PACKAGE_NAME}.*'],
        exclude=[
            'tests', 'tests.*', '*.tests.*', '*.test.*', 'test_.*',
            'docs', 'docs.*', '*.docs.*',
        ]
    ),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3 :: Only',
    ],
    python_requires='>=3.10',
)
