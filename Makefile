# Space Miner

.DEFAULT_GOAL := run

# Phone held sideways, 20:9
PHONE_WINDOW := 960x432

.PHONY: help install run mobile check assets

help:  ## List the targets
	@grep -E '^[a-z]+:.*## ' $(MAKEFILE_LIST) \
		| awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

install:  ## Install the game and its development tools
	uv sync

run:  ## Play on a computer, fullscreen
	uv run main.py

mobile:  ## Play the phone interface, in a phone sized window
	SPACE_MINER_PLATFORM=android SPACE_MINER_WINDOW=$(PHONE_WINDOW) \
		uv run main.py

check:  ## Lint, type-check and test
	uv run ruff check
	uv run mypy
	uv run pytest -q

assets:  ## Recolor the asteroids, draw the ships
	uv run python -m tools.recolor
	uv run python -m tools.draw_ship
