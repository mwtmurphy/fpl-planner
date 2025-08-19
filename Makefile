.PHONY: setup dev data optimise visualise all clean test fmt lint

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

dev:
	python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt -r dev-requirements.txt && pre-commit install

data:
	python scripts/fetch_data.py --config config.yaml

optimise:
	python scripts/optimise.py --config config.yaml

visualise:
	python scripts/visualise.py --config config.yaml

all: data optimise visualise

clean:
	rm -rf data/raw/* data/processed/* output/* *.log

test:
	pytest -q

fmt:
	black . && isort .

lint:
	ruff check .
