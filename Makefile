.PHONY: run test lint fmt coverage


run:
uvicorn app.main:app --reload


test:
pytest -q


coverage:
pytest --cov=app --cov-report=term-missing


lint:
flake8