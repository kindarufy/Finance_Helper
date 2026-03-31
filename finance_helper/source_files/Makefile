.PHONY: up down rebuild logs test seed-demo clean compile

up:
	docker compose up --build

down:
	docker compose down

rebuild:
	docker compose down -v
	docker compose up --build

logs:
	docker compose logs -f

test:
	python -m pytest -q

compile:
	python -m compileall services tests scripts

seed-demo:
	docker compose --profile demo run --rm demo-seed

clean:
	rm -rf .pytest_cache htmlcov .coverage
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
