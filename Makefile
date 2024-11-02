# Space Miner

.DEFAULT_GOAL := run

.PHONY: help install run check

help:  ## List the targets
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) \
		| awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

install:  ## Install the game and its development tools
	uv sync

run:  ## Play on a computer, fullscreen
	uv run main.py

check:  ## Lint, type-check and test
	uv run ruff check
	uv run mypy
	uv run pytest -q
