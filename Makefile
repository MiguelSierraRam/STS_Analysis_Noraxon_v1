.PHONY: help install install-dev test lint format clean docs

help:
	@echo "STS Analysis Tool - Tareas disponibles"
	@echo "======================================"
	@echo "  make install      - Instalar dependencias"
	@echo "  make install-dev  - Instalar con dependencias de desarrollo"
	@echo "  make test         - Ejecutar tests con pytest"
	@echo "  make test-cov     - Tests con cobertura"
	@echo "  make lint         - Validar código (flake8)"
	@echo "  make format       - Formatear código (black)"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make build        - Construir distribución"

install:
	pip install -r requirements.txt

install-dev:
	pip install -e .[dev]

test:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=src --cov-report=html

lint:
	flake8 src/ tests/ sts_analysis_tool_enhanced_v2.py --max-line-length=120

format:
	black src/ tests/ sts_analysis_tool_enhanced_v2.py --line-length=120

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .tox/ htmlcov/ dist/ build/ *.egg-info
	rm -rf .coverage

build:
	python setup.py sdist bdist_wheel

run-analysis:
	python sts_analysis_tool_enhanced_v2.py --show-config

.DEFAULT_GOAL := help
