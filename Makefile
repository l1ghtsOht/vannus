.PHONY: install test run-api

install:
	python -m pip install --upgrade pip
	if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
	if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

test:
	python -m pytest -q

run-api:
	uvicorn praxis.api:app --reload --port 8000
