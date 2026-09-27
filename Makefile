# Space Miner

.DEFAULT_GOAL := run

# Phone held sideways, 20:9
PHONE_WINDOW := 960x432

.PHONY: help install run mobile check scenarios assets

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

scenarios:  ## Play scripted scenarios in windows, PHONE=1 as on phones
	uv run python -m tests.scenarios.run $(if $(PHONE),--phone)

assets:  ## Recolor the asteroids, paint the planets and the sky, draw ships
	uv run python -m tools.recolor
	uv run python -m tools.draw_earth
	uv run python -m tools.draw_planets
	uv run python -m tools.draw_ship
	uv run python -m tools.draw_sky
