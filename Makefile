COLOR_RESET=\033[0m
COLOR_GREEN=\033[32m
COLOR_YELLOW=\033[33m
COLOR_RED=\033[31m
MAKEFILE_DIR := $(dir $(lastword $(MAKEFILE_LIST)))

.PHONY: help update-requirements format-python lint-python check-python distribute distribute-fast distribute-debug distribute-pyinstaller clean test-nuitka check-python check-bins

help:
	@echo "$(COLOR_YELLOW)Available targets:$(COLOR_RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}'

check-python: ## Check if Python is compatible with Nuitka
	@echo "$(COLOR_YELLOW)Checking Python compatibility...$(COLOR_RESET)"
	@python -c "import sys; print(f'Python: {sys.executable}'); print(f'Version: {sys.version}')"
	@if python -c "import sys; sys.exit(0 if '/usr/bin/python' not in sys.executable else 1)"; then \
		echo "$(COLOR_GREEN)Python is compatible with Nuitka$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_YELLOW)WARNING: You're using Apple's system Python. Install Python from:$(COLOR_RESET)"; \
		echo "  - Homebrew: brew install python"; \
		echo "  - python.org: https://www.python.org/downloads/macos/"; \
		echo "  - pyenv: pyenv install 3.11.7"; \
	fi

check-bins: ## Check bins directory structure
	@echo "$(COLOR_YELLOW)Checking bins directory...$(COLOR_RESET)"
	@if [ -d "bins" ]; then \
		echo "$(COLOR_GREEN)bins directory found$(COLOR_RESET)"; \
		find bins -type f -exec ls -la {} \; | while read line; do echo "  $$line"; done; \
	else \
		echo "$(COLOR_YELLOW)WARNING: bins directory not found!$(COLOR_RESET)"; \
	fi

update-requirements: ## Update requirements.txt with installed packages
	@echo "$(COLOR_YELLOW)Updating requirements.txt...$(COLOR_RESET)"
	@pip freeze > requirements.txt
	@echo "$(COLOR_GREEN)requirements.txt updated.$(COLOR_RESET)"

lint-python: ## Lint Python code with Ruff
	@echo "$(COLOR_YELLOW)Linting Python files with Ruff...$(COLOR_RESET)"
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
		if [ $$? -eq 0 ]; then \
			echo "$(COLOR_GREEN)✓ All linting checks passed!$(COLOR_RESET)"; \
		else \
			echo "$(COLOR_RED)✗ Linting issues found$(COLOR_RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(COLOR_RED)Ruff not installed. Installing...$(COLOR_RESET)"; \
		pip install ruff; \
		ruff check .; \
	fi

format-python: ## Format Python code with Black and fix with Ruff
	@echo "$(COLOR_YELLOW)Formatting Python files...$(COLOR_RESET)"
	@if command -v black >/dev/null 2>&1; then \
		echo "$(COLOR_YELLOW)Running Black formatter...$(COLOR_RESET)"; \
		black .; \
	else \
		echo "$(COLOR_RED)Black not installed. Installing...$(COLOR_RESET)"; \
		pip install black; \
		black .; \
	fi
	@if command -v ruff >/dev/null 2>&1; then \
		echo "$(COLOR_YELLOW)Running Ruff auto-fixes...$(COLOR_RESET)"; \
		ruff check --fix .; \
	else \
		echo "$(COLOR_RED)Ruff not installed. Installing...$(COLOR_RESET)"; \
		pip install ruff; \
		ruff check --fix .; \
	fi
	@echo "$(COLOR_GREEN)✓ Code formatting complete!$(COLOR_RESET)"

check-format: ## Check if code is properly formatted (CI-friendly)
	@echo "$(COLOR_YELLOW)Checking code formatting...$(COLOR_RESET)"
	@if command -v black >/dev/null 2>&1; then \
		black --check --diff .; \
		if [ $$? -ne 0 ]; then \
			echo "$(COLOR_RED)✗ Code is not formatted with Black$(COLOR_RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(COLOR_RED)Black not installed!$(COLOR_RESET)"; \
		exit 1; \
	fi
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check .; \
		if [ $$? -ne 0 ]; then \
			echo "$(COLOR_RED)✗ Ruff checks failed$(COLOR_RESET)"; \
			exit 1; \
		fi; \
	else \
		echo "$(COLOR_RED)Ruff not installed!$(COLOR_RESET)"; \
		exit 1; \
	fi
	@echo "$(COLOR_GREEN)✓ All formatting checks passed!$(COLOR_RESET)"

install-dev-tools: ## Install development tools (Black, Ruff)
	@echo "$(COLOR_YELLOW)Installing development tools...$(COLOR_RESET)"
	@pip install black ruff
	@echo "$(COLOR_GREEN)Development tools installed!$(COLOR_RESET)"

test-nuitka: ## Test if Nuitka is working
	@echo "$(COLOR_YELLOW)Testing Nuitka installation...$(COLOR_RESET)"
	@python -m nuitka --version || { echo "$(COLOR_YELLOW)Installing Nuitka...$(COLOR_RESET)"; pip install nuitka; }
	@echo "$(COLOR_GREEN)Nuitka is ready!$(COLOR_RESET)"

distribute: ## Create standalone exe with Nuitka (optimized)
	@echo "$(COLOR_YELLOW)Building animation-tool with Nuitka...$(COLOR_RESET)"
	@$(MAKE) check-python
	@$(MAKE) check-bins
	@mkdir -p dist
	@PYTHONPATH=src:src/animation_converter python -m nuitka \
		--onefile \
		--standalone \
		--output-filename=animation-tool \
		--output-dir=dist \
		--include-data-dir=src/resources/test-program=src/resources/test-program \
		--include-data-files=bins/linux/64tass=bins/linux/64tass \
		--include-data-files=bins/macos/64tass=bins/macos/64tass \
		--include-data-files=bins/windows/64tass.exe=bins/windows/64tass.exe \
		--enable-plugin=tk-inter \
		--follow-imports \
		--lto=yes \
		--show-progress \
		--assume-yes-for-downloads \
		--warn-implicit-exceptions \
		--warn-unusual-code \
		src/animation_converter/main.py
	@echo "$(COLOR_GREEN)Build complete: dist/animation-tool$(COLOR_RESET)"

distribute-fast: ## Create standalone exe with Nuitka (fast build)
	@echo "$(COLOR_YELLOW)Building animation-tool with Nuitka (fast build)...$(COLOR_RESET)"
	@$(MAKE) check-python
	@$(MAKE) check-bins
	@mkdir -p dist
	@echo "$(COLOR_YELLOW)Explicitly checking files before build:$(COLOR_RESET)"
	@ls -la bins/linux/64tass bins/macos/64tass bins/windows/64tass.exe
	@PYTHONPATH=src:src/animation_converter python -m nuitka \
		--onefile \
		--standalone \
		--output-filename=animation-tool \
		--output-dir=dist \
		--include-data-dir=src/resources/test-program=src/resources/test-program \
		--include-data-files=bins/linux/64tass=bins/linux/64tass \
		--include-data-files=bins/macos/64tass=bins/macos/64tass \
		--include-data-files=bins/windows/64tass.exe=bins/windows/64tass.exe \
		--enable-plugin=numpy \
		--enable-plugin=multiprocessing \
		--follow-imports \
		--assume-yes-for-downloads \
		--verbose \
		src/animation_converter/main.py
	@echo "$(COLOR_GREEN)Fast build complete: dist/animation-tool$(COLOR_RESET)"

distribute-debug: ## Create debug build with Nuitka
	@echo "$(COLOR_YELLOW)Building animation-tool with Nuitka (debug)...$(COLOR_RESET)"
	@$(MAKE) check-python
	@$(MAKE) check-bins
	@mkdir -p dist
	@PYTHONPATH=src:src/animation_converter python -m nuitka \
		--onefile \
		--standalone \
		--output-filename=animation-tool-debug \
		--output-dir=dist \
		--include-data-dir=src/resources/test-program=src/resources/test-program \
		--include-data-files=bins/linux/64tass=bins/linux/64tass \
		--include-data-files=bins/macos/64tass=bins/macos/64tass \
		--include-data-files=bins/windows/64tass.exe=bins/windows/64tass.exe \
		--enable-plugin=numpy \
		--enable-plugin=multiprocessing \
		--follow-imports \
		--debug \
		--unstripped \
		--assume-yes-for-downloads \
		src/animation_converter/main.py
	@echo "$(COLOR_GREEN)Debug build complete: dist/animation-tool-debug$(COLOR_RESET)"

distribute-pyinstaller: ## Fallback: Create exe with PyInstaller (your original)
	@echo "$(COLOR_YELLOW)Building with PyInstaller (fallback)...$(COLOR_RESET)"
	@pyinstaller --onefile \
		--name animation-tool \
		--add-data "src/resources/test-program:src/resources/test-program" \
		--add-data "bins:bins" \
		--paths src \
		--paths src/animation_converter \
		--hidden-import=numba \
		--bootloader-ignore-signals \
		--noupx \
		src/animation_converter/main.py
	@echo "$(COLOR_GREEN)PyInstaller build complete$(COLOR_RESET)"

clean: ## Clean build artifacts
	@echo "$(COLOR_YELLOW)Cleaning build artifacts...$(COLOR_RESET)"
	@rm -rf dist build *.spec __pycache__
	@find . -name "*.pyc" -delete
	@find . -name "*.pyo" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(COLOR_GREEN)Clean complete$(COLOR_RESET)"

# Convenience aliases and compound targets
format: format-python ## Alias for format-python
lint: lint-python ## Alias for lint-python

pre-build: lint-python format-python ## Run linting and formatting before build
	@echo "$(COLOR_GREEN)✓ Pre-build checks complete!$(COLOR_RESET)"

ci-check: check-format lint-python ## CI-friendly checks (no auto-fixes)
	@echo "$(COLOR_GREEN)✓ All CI checks passed!$(COLOR_RESET)"

.DEFAULT_GOAL := help