.PHONY: install run test test-cov typecheck lint format precommit-install precommit-run allure-results allure-report allure-open allure-open-cli check

ALLURE_HOST ?= 127.0.0.1
ALLURE_PORT ?= 8091

install:
	python3 -m pip install -r requirements.txt

run:
	uvicorn app.main:app --reload

test:
	pytest -q

test-cov:
	pytest

typecheck:
	python3 -m mypy app tests

lint:
	python3 -m ruff check app tests
	python3 -m black --check app tests
	python3 -m isort --check-only app tests

format:
	python3 -m isort app tests
	python3 -m black app tests
	python3 -m ruff check app tests --fix

precommit-install:
	python3 -m pre_commit install

precommit-run:
	python3 -m pre_commit run --all-files

allure-results:
	pytest --alluredir=allure-results

allure-report: allure-results
	npx -y allure-commandline generate allure-results -o allure-report --clean

allure-open: allure-report
	@echo "Open Allure report at http://$(ALLURE_HOST):$(ALLURE_PORT)"
	python3 -m http.server $(ALLURE_PORT) --bind $(ALLURE_HOST) --directory allure-report

allure-open-cli: allure-report
	npx -y allure-commandline open allure-report

check: lint typecheck test
