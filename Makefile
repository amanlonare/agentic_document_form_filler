.PHONY: clean build install-dev lint test
CONTAINER_NAME=amanlonare/agentic_document_form_filler

clean:
	rm -rf .eggs __pycache__ .pytest_cache agentic_document_form_filler/__pycache__ agentic_document_form_filler/lib/__pycache__ \
	agentic_document_form_filler.egg-info notebooks/__pycache__

install-dev:
	pip install -e .[dev]

install:
	pip install -e .

package:
	pip install --upgrade build
	python -m build

lint:
	flake8 agentic_document_form_filler --count --show-source --statistics

publish:
	pip install --upgrade twine
	python -m twine upload dist/*