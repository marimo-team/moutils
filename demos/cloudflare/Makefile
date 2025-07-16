MAKEFLAGS += --no-print-directory --warn-undefined-variables --output-sync=target

################################################################################
#                                  Variables                                   #
################################################################################

.PHONY: help makeinfo all
.DEFAULT_GOAL := help
WRANGLER = npx wrangler@latest
SHELL := bash -e
MAKECMDGOALS ?= help
PYTHON_CMD := $(shell type -fp python3)
PYTHON_VENV := .venv
NB_SOURCE_DIR := notebooks
NB_EXPORT_DIR := export/html-wasm
INDEX_DIR := $(shell echo '$(NB_EXPORT_DIR)' | cut -d/ -f1)
PAGES_DIR := pages

ifneq ($(wildcard .env),)
	include .env
endif

################################################################################
#                              Main Workflow                                   #
################################################################################

$(PYTHON_VENV): requirements.txt $(PYTHON_CMD) # Create Python virtual environment and install requirements
	$(PYTHON_CMD) -m venv $(PYTHON_VENV)
	$(PYTHON_VENV)/bin/pip install --disable-pip-version-check --upgrade -r requirements.txt
	@touch $(PYTHON_VENV)
	@printf "\n==> A self-contained python environment has been created with all the required dependencies.\n"
	@printf "==> To activate that environment and start the notebooks server, run the following commands:\n"
	@printf "\n\tsource $(PYTHON_VENV)/bin/activate\n\tmake edit\n\n"

.PHONY: edit
edit: makeinfo $(PYTHON_VENV) ## [PYTHON][WORKSPACE][*] Launch marimo edit in workspace mode
	# Install the local wheel in the virtual environment (skip wheel building)
	$(PYTHON_VENV)/bin/pip install --force-reinstall public/$(WHEEL_BASENAME)
	# Copy notebooks without micropip injection for Python environment
	mkdir -p $(NB_SOURCE_DIR)
	cp -r ../../$(NB_SOURCE_DIR)/* $(NB_SOURCE_DIR)/
	mkdir -p $(NB_SOURCE_DIR)/public
	cp -r public/* $(NB_SOURCE_DIR)/public/
	cd notebooks && ../$(PYTHON_VENV)/bin/marimo edit --port 2718

.PHONY: export
export: makeinfo wheel html-wasm ## [WASM BUILD][*] Build HTML/WASM and show preview instructions
	@printf '\n==> To see the exported notebooks, run the following command and open the displayed URL in your browser:\n'
	@printf '\n\tmake preview\n\n'

.PHONY: preview
preview: makeinfo wheel html-wasm ## [WASM SERVE][*] Serve the exported notebooks locally
	npm run preview

################################################################################
#                              Other Commands                                  #
################################################################################

.PHONY: clean-deep
clean-deep: makeinfo clean ## Deep clean including removal of the Python virtual environment
	rm -rf $(PYTHON_VENV) || true
	rm -rf $(NB_SOURCE_DIR)/.venv || true
	rm -rf .venv || true
	rm -rf .wrangler || true

.PHONY: clean
clean: makeinfo ## Remove temporary files, caches, and build artifacts
	find . -name '*~' -type f -delete || true
	find . -name '*.pyc' -type f -delete || true
	find . -name '__pycache__' -type d -delete || true
	rm -rf $(INDEX_DIR) node_modules notebooks || true
	rm -rf $(NB_SOURCE_DIR)/.python-version || true
	rm -rf $(NB_SOURCE_DIR)/README.md || true
	rm -rf $(NB_SOURCE_DIR)/pyproject.toml || true
	rm -rf $(NB_SOURCE_DIR)/uv.lock || true
	rm -rf $(NB_SOURCE_DIR)/__marimo__ || true
	rm -rf $(NB_SOURCE_DIR)/__pycache__ || true

deploy: makeinfo node_modules lint html-wasm ## Run lint, build HTML/WASM, and deploy via npm
	npm run deploy

.PHONY: edit-notebook
edit-notebook: makeinfo ## [PYTHON][NOTEBOOK] Launch marimo edit for a specific notebook (default: _start.py)
	@echo "Starting marimo for a specific notebook (single notebook)"
	cd notebooks && ../$(PYTHON_VENV)/bin/marimo edit $${notebook:-_start.py} --port 2718 --sandbox

.PHONY: edit-uv-notebook
edit-uv-notebook: makeinfo ## [PYTHON][NOTEBOOK] Launch marimo with uv for a specific notebook (default: _start.py)
	@echo "Starting marimo with uv for a specific notebook (single notebook)"
	cd notebooks && uv init 2>/dev/null || true && uv add marimo --active && uv run --active marimo edit $${notebook:-_start.py} --port 2718 --sandbox

.PHONY: edit-uv-workspace
edit-uv-workspace: makeinfo ## [PYTHON][WORKSPACE] Launch marimo with uv in workspace mode
	@echo "Starting marimo with uv workspace (entire notebooks directory)"
	cd notebooks && uv init 2>/dev/null || true && uv add marimo --active && uv run --active marimo edit --port 2718

.PHONY: lint
lint: makeinfo $(PYTHON_VENV) node_modules ## Run Python and JavaScript linters
	$(PYTHON_VENV)/bin/flake8 $(NB_SOURCE_DIR) $(PAGES_DIR) --exclude=$(PYTHON_VENV)
	npm run lint

.PHONY: venv
venv: makeinfo $(PYTHON_VENV) ## Alias to set up Python virtual environment

################################################################################
#                              Build Dependencies                              #
################################################################################

node_modules: makeinfo package.json # node_modules: Install npm dependencies
	npm install
	touch node_modules

.PHONY: html-wasm-clean
html-wasm-clean: makeinfo # Remove exported HTML/WASM directory
	rm -rf "$(NB_EXPORT_DIR)"
	rm -rf "$(INDEX_DIR)"

$(NB_EXPORT_DIR)/%.html: $(NB_SOURCE_DIR)/%.py makeinfo $(PYTHON_VENV)
	@if $(PYTHON_VENV)/bin/python -c 'import sys, notebooks.$(basename $(notdir $<)) as m; sys.exit(0 if hasattr(m, "__generated_with") else 1)' ; then \
		echo "$<: $@" ; \
		$(PYTHON_VENV)/bin/marimo -q -y export html-wasm "$<" -o "$@" --mode edit ; \
	fi

$(INDEX_DIR)/index.html: makeinfo notebooks.yaml $(PAGES_DIR)/index.py $(shell find $(PAGES_DIR)/template -type f) $(patsubst $(NB_SOURCE_DIR)/%.py,$(NB_EXPORT_DIR)/%.html,$(wildcard $(NB_SOURCE_DIR)/*.py)) # Generate the main index.html from notebooks.yaml and template files
	$(PYTHON_VENV)/bin/python $(PAGES_DIR)/index.py --lint $(NB_EXPORT_DIR) $(INDEX_DIR)

$(INDEX_DIR)/_redirects: makeinfo $(PAGES_DIR)/_redirects # Copy _redirects configuration to the output directory
	mkdir -p $(shell dirname "$@")
	cp $(PAGES_DIR)/_redirects $@

$(INDEX_DIR)/_routes.json: makeinfo $(PAGES_DIR)/_routes.json # Copy _routes.json configuration to the output directory
	mkdir -p $(shell dirname "$@")
	cp $(PAGES_DIR)/_routes.json $@

$(INDEX_DIR)/$(WHEEL_BASENAME): makeinfo public/$(WHEEL_BASENAME) # Copy wheel file to export directory
	mkdir -p $(shell dirname "$@")
	cp public/$(WHEEL_BASENAME) $@
	@echo "✅ Wheel file copied to $@"

.PHONY: setup-notebooks
setup-notebooks: makeinfo # Set up notebooks directory with wheel injection
	# Create WHEEL_FILENAME.txt for inject_micropip script
	mkdir -p $(INDEX_DIR)
	@echo $(WHEEL_BASENAME) > $(INDEX_DIR)/WHEEL_FILENAME.txt
	# Set up notebooks directory
	mkdir -p $(NB_SOURCE_DIR)
	cp -r ../../$(NB_SOURCE_DIR)/* $(NB_SOURCE_DIR)/
	mkdir -p $(NB_SOURCE_DIR)/public
	cp -r public/* $(NB_SOURCE_DIR)/public/
	@echo "🔧 Injecting micropip installation into notebooks..."
	@for notebook in $(NB_SOURCE_DIR)/*.py; do \
		if [ -f "$$notebook" ]; then \
			$(PYTHON_CMD) scripts/inject_micropip.py "$$notebook"; \
		fi \
	done

.PHONY: export-notebooks
export-notebooks:
	mkdir -p $(NB_EXPORT_DIR)
	@for notebook in $(NB_SOURCE_DIR)/*.py; do \
		if [ -f "$$notebook" ]; then \
			$(PYTHON_VENV)/bin/marimo -q -y export html-wasm "$$notebook" -o "$(NB_EXPORT_DIR)/$$(basename "$$notebook" .py).html" --mode edit; \
		fi \
	done
	# Set up export directory structure
	mkdir -p $(NB_EXPORT_DIR)/public
	find $(NB_SOURCE_DIR)/public -type f ! -name 'login.html' ! -name '*.whl' -exec cp {} $(NB_EXPORT_DIR)/public/ \;
	cp $(NB_SOURCE_DIR)/public/login.html $(NB_EXPORT_DIR)/
	if ls $(NB_SOURCE_DIR)/public/*.whl 1> /dev/null 2>&1; then cp $(NB_SOURCE_DIR)/public/*.whl $(NB_EXPORT_DIR)/; fi

html-wasm: makeinfo html-wasm-clean setup-notebooks lint export-notebooks $(INDEX_DIR)/_redirects $(INDEX_DIR)/_routes.json $(INDEX_DIR)/$(WHEEL_BASENAME) $(INDEX_DIR)/index.html # html-wasm: Full build of HTML/WASM notebooks including linting and index
	# Export notebooks to HTML/WASM
	@for notebook in $(NB_SOURCE_DIR)/*.py; do \
		if [ -f "$$notebook" ]; then \
			$(PYTHON_VENV)/bin/marimo -q -y export html-wasm "$$notebook" -o "$(NB_EXPORT_DIR)/$$(basename "$$notebook" .py).html" --mode edit; \
		fi \
	done
	# Set up export directory structure
	mkdir -p $(NB_EXPORT_DIR)/public
	# Copy all files except login.html and the wheel to public/
	find $(NB_SOURCE_DIR)/public -type f ! -name 'login.html' ! -name '*.whl' -exec cp {} $(NB_EXPORT_DIR)/public/ \;
	# Copy login.html and the wheel file to html-wasm root
	cp $(NB_SOURCE_DIR)/public/login.html $(NB_EXPORT_DIR)/
	if ls $(NB_SOURCE_DIR)/public/*.whl 1> /dev/null 2>&1; then cp $(NB_SOURCE_DIR)/public/*.whl $(NB_EXPORT_DIR)/; fi

# Find a working python3 interpreter (prefers 3.13, then 3.12, then 3.11, then 3.10, then 3.9, then 3.8, then any python3)
PYTHON_BUILD := $(shell command -v python3.13 2>/dev/null || command -v python3.12 2>/dev/null || command -v python3.11 2>/dev/null || command -v python3.10 2>/dev/null || command -v python3.9 2>/dev/null || command -v python3.8 2>/dev/null || command -v python3 2>/dev/null)

# Check if 'build' is installed for the selected python
HAVE_BUILD := $(shell $(PYTHON_BUILD) -m pip show build >/dev/null 2>&1 && echo yes || echo no)

# Find the latest built wheel
WHEEL_FILE := $(shell ls -t ../../dist/moutils-*.whl 2>/dev/null | head -1)
WHEEL_BASENAME := $(shell basename $(WHEEL_FILE))

.PHONY: wheel
wheel:
ifeq ($(HAVE_BUILD),no)
	@echo "Installing 'build' module for $(PYTHON_BUILD)..."
	$(PYTHON_BUILD) -m pip install build
endif
	cd ../../ && $(PYTHON_BUILD) -m build --wheel
	@echo "Latest wheel: $(WHEEL_FILE)"
	@cp $(WHEEL_FILE) public/


.PHONY: rebuild
rebuild: makeinfo ## [WASM BUILD][*] Rebuild the HTML/WASM and show preview instructions
	make clean-deep && deactivate || true && make venv && source .venv/bin/activate && make export

################################################################################
#                            Utility Commands                                  #
################################################################################

help: makeinfo # Show available make commands
	@echo "Main workflow:"; \
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E '\[\*\]' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'; \
	echo ""; \
	echo "Other commands:"; \
	grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v -E '\[\*\]' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

makeinfo: # Shows the current make command running
	@goal="$(MAKECMDGOALS)"; \
	if [ "$$goal" = "" ] || [ "$$goal" = "makeinfo" ]; then goal="help"; fi; \
	echo ""; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "🛠  Running: $$goal"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo ""

# EOF - Makefile
