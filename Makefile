# fde-starter: a checked, reproducible development environment for the FDE program.
# Windows without make: README.md gives every target as a PowerShell command.
PYTHON ?= python3.12
PY := $(if $(wildcard .venv/bin/python),.venv/bin/python,$(PYTHON))
QDRANT_PORT ?= $(or $(shell grep -E '^QDRANT_PORT=' .env 2>/dev/null | cut -d= -f2),6333)

.PHONY: help setup check hello up ping down clean

help:
	@echo "make setup | check | hello | up | ping | down | clean"

setup:                 ## virtual environment + pinned requirements
	$(PYTHON) -m venv .venv
	.venv/bin/pip install -r requirements.txt

check:                 ## the ✅/❌ checklist (python, venv, git, code, docker, .env, key, live call)
	@$(PY) scripts/check_env.py

hello:                 ## one real LLM call, key read from .env
	@$(PY) hello_llm.py

up:                    ## start Qdrant in Docker (port from QDRANT_PORT, default 6333)
	docker compose up -d

ping:                  ## is Qdrant answering?
	curl -s localhost:$(QDRANT_PORT) ; echo

down:                  ## stop and remove the containers (the data volume stays)
	docker compose down

clean:                 ## remove the virtual environment and caches
	rm -rf .venv __pycache__ scripts/__pycache__
