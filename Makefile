.PHONY: install test lint run format clean

install:
	npm install
	pip install -r requirements.txt

test:
	pytest api/tests/ -v

lint:
	npm run lint
	ruff check api/

run:
	npm run dev

build:
	npm run build

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .next
