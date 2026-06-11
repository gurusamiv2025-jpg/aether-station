# Aether Station — common dev tasks
# Usage: `make` lists targets, `make test` runs the suite, etc.

.PHONY: help install test compile run cli demo docker docker-run lint clean

help:  ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install runtime + dev dependencies
	python -m pip install -U pip
	python -m pip install -r requirements.txt

test:  ## Run pytest
	pytest -q

compile:  ## Verify every .py compiles
	python -m compileall -q . tests

run:  ## Launch the Streamlit app
	streamlit run app.py

cli:  ## Print the CLI help
	python cli.py --help

demo:  ## Quick CLI smoke demo — Park on the Halberd incident
	python cli.py ask park "What's your read on the Halberd Mining Cooperative?"

docker:  ## Build the Docker image
	docker build -t aether-station .

docker-run: docker  ## Build then run the container on port 8501
	docker run --rm -p 8501:8501 aether-station

api:  ## Start the FastAPI HTTP server on port 8000
	python cli.py serve --port 8000

bench:  ## Run the per-character benchmark
	python cli.py bench

doctor:  ## Run cli.py doctor (32 subsystem checks)
	python cli.py doctor

clean:  ## Remove caches and build artifacts
	rm -rf __pycache__ */__pycache__ .pytest_cache .coverage build dist *.egg-info
