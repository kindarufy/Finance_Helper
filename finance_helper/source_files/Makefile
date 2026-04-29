.PHONY: venv install migrate run-finance run-analytics run-gateway run-bot seed-demo test compile clean

PYTHON ?= python3
VENV ?= venv
VENV_PYTHON ?= $(VENV)/bin/python

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements.txt

migrate:
	cd services/finance-service && ../../$(VENV_PYTHON) -m alembic upgrade head

run-finance:
	cd services/finance-service && ../../$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8001

run-analytics:
	cd services/analytics-service && ../../$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8002

run-gateway:
	cd services/api-gateway && ../../$(VENV_PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000

run-bot:
	cd services/bot-service && ../../$(VENV_PYTHON) -m app.main

seed-demo:
	$(VENV_PYTHON) scripts/seed_demo.py

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(VENV_PYTHON) -m pytest -q

compile:
	$(PYTHON) -m compileall services tests scripts

clean:
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
