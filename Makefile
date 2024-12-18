COLOR_RESET=\033[0m
COLOR_GREEN=\033[32m
COLOR_YELLOW=\033[33m
MAKEFILE_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

.PHONY: help update-requirements format-python

help:
	@echo "$(COLOR_YELLOW)Available targets:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'

update-requirements: ## Update requirements.txt with installed packages
	@echo "$(COLOR_YELLOW)Updating requirements.txt...$(COLOR_RESET)"
	@pip freeze > requirements.txt
	@echo "$(COLOR_GREEN)requirements.txt updated.$(COLOR_RESET)"

format-python: ## Autoformat python code
	@echo "$(COLOR_YELLOW)Formatting python files...$(COLOR_RESET)"
	@black .
	@isort .
	@echo "$(COLOR_YELLOW)done.$(COLOR_RESET)"

distribute: ## Create standalone exe
	@pyinstaller --onefile \
		--add-data "src/resources:resources" \
		--add-data "bins:bins" \
		--paths src \
		--paths src/animation_converter \
		src/animation_converter/main.py

.DEFAULT_GOAL := help
