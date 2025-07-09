MAKEFLAGS += --no-print-directory --warn-undefined-variables --output-sync=target

################################################################################
#                                  Variables                                   #
################################################################################

.PHONY: help makeinfo all
.DEFAULT_GOAL := help
WRANGLER = npx wrangler@latest
SHELL := bash -e
PYTHON_CMD := $(shell type -fp python3)
PYTHON_VENV := .venv
NB_SOURCE_DIR := notebooks
NB_EXPORT_DIR := export/html-wasm
INDEX_DIR := $(shell echo '$(NB_EXPORT_DIR)' | cut -d/ -f1)
PAGES_DIR := pages

ifneq ($(wildcard .env),)
	include .env
endif

.PHONY: all
all: makeinfo venv ## all: Ensure virtual environment is ready and show basic instructions
	@printf '\n==> Run "source .venv/bin/activate" to activate the virtual environment.\n'
	@printf '\n==> Run "make edit" to start a local notebook server.\n'
	@printf '==> Run "make export" to generate the WASM notebooks.\n'
	@printf '==> Run "make preview" to serve the WASM notebooks.\n'

$(PYTHON_VENV): requirements.txt $(PYTHON_CMD) ## $(PYTHON_VENV): Create Python virtual environment and install requirements
	$(PYTHON_CMD) -m venv $(PYTHON_VENV)
	$(PYTHON_VENV)/bin/pip install --disable-pip-version-check --upgrade -r requirements.txt
	@touch $(PYTHON_VENV)
	@printf "\n==> A self-contained python environment has been created with all the required dependencies.\n"
	@printf "==> To activate that environment and start the notebooks server, run the following commands:\n"
	@printf "\n\tsource $(PYTHON_VENV)/bin/activate\n\tmake edit\n\n"


node_modules: makeinfo package.json # node_modules: Install npm dependencies
	npm install
	touch node_modules


.PHONY: venv
venv: makeinfo $(PYTHON_VENV) ## venv: Alias to set up Python virtual environment

.PHONY: lint
lint: makeinfo $(PYTHON_VENV) node_modules ## lint: Run Python and JavaScript linters
	$(PYTHON_VENV)/bin/flake8 $(NB_SOURCE_DIR) $(PAGES_DIR)
	npm run lint

.PHONY: html-wasm-clean
html-wasm-clean: makeinfo # html-wasm-clean: Remove exported HTML/WASM directory
	rm -rf $(NB_EXPORT_DIR)
	rm -rf $(NB_SOURCE_DIR)
	rm -rf 
	mkdir -p $(NB_EXPORT_DIR)
	mkdir -p $(NB_SOURCE_DIR)
	cp -r ../../$(NB_SOURCE_DIR)/* $(NB_SOURCE_DIR)/
	mkdir -p $(NB_SOURCE_DIR)/public
	cp -r public/* $(NB_SOURCE_DIR)/public/
	@echo "🛞 Copying wheel file to export directory..."
	@if [ -f "public/$(WHEEL_BASENAME)" ]; then \
		cp public/$(WHEEL_BASENAME) $(INDEX_DIR)/; \
		echo "✅ Wheel file copied to $(INDEX_DIR)/$(WHEEL_BASENAME)"; \
	else \
		echo "⚠️  Warning: public/$(WHEEL_BASENAME) not found"; \
	fi
	@echo $(WHEEL_BASENAME) > $(INDEX_DIR)/WHEEL_FILENAME.txt
	@echo "🔧 Injecting micropip installation into notebooks..."
	@for notebook in $(NB_SOURCE_DIR)/*.py; do \
		if [ -f "$$notebook" ]; then \
			$(PYTHON_CMD) scripts/inject_micropip.py "$$notebook"; \
		fi \
	done

$(NB_EXPORT_DIR)/%.html: $(NB_SOURCE_DIR)/%.py makeinfo $(PYTHON_VENV)
	@if $(PYTHON_VENV)/bin/python -c 'import sys, notebooks.$(basename $(notdir $<)) as m; sys.exit(0 if hasattr(m, "__generated_with") else 1)' ; then \
		echo "$<: $@" ; \
		$(PYTHON_VENV)/bin/marimo -q -y export html-wasm "$<" -o "$@" --mode edit ; \
	fi

$(INDEX_DIR)/index.html: makeinfo notebooks.yaml $(PAGES_DIR)/index.py $(shell find $(PAGES_DIR)/template -type f) $(patsubst $(NB_SOURCE_DIR)/%.py,$(NB_EXPORT_DIR)/%.html,$(filter-out $(NB_SOURCE_DIR)/__init__.py,$(wildcard $(NB_SOURCE_DIR)/*.py))) ## Generate the main index.html from notebooks.yaml and template files
	$(PYTHON_VENV)/bin/python $(PAGES_DIR)/index.py --lint $(NB_EXPORT_DIR) $(INDEX_DIR)

$(INDEX_DIR)/_redirects: makeinfo $(PAGES_DIR)/_redirects ## Copy _redirects configuration to the output directory
	mkdir -p $(shell dirname "$@")
	cp $(PAGES_DIR)/_redirects $@


$(INDEX_DIR)/_routes.json: makeinfo $(PAGES_DIR)/_routes.json ## Copy _routes.json configuration to the output directory
	mkdir -p $(shell dirname "$@")
	cp $(PAGES_DIR)/_routes.json $@

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

# html-wasm: Full build of HTML/WASM notebooks including linting and index
.PHONY: html-wasm
html-wasm: makeinfo html-wasm-clean lint $(INDEX_DIR)/_redirects $(INDEX_DIR)/_routes.json $(patsubst $(NB_SOURCE_DIR)/%.py,$(NB_EXPORT_DIR)/%.html,$(filter-out $(NB_SOURCE_DIR)/__init__.py,$(wildcard $(NB_SOURCE_DIR)/*.py))) $(INDEX_DIR)/index.html

.PHONY: export
export: wheel makeinfo html-wasm ## export: Build HTML/WASM and show preview instructions
	@printf '\n==> To see the exported notebooks, run the following command and open the displayed URL in your browser:\n'
	@printf '\n\tmake preview\n\n'

.PHONY: preview
preview: makeinfo html-wasm ## preview: Serve the exported notebooks locally
	npm run preview

## edit: Launch local Marimo notebook server for editing
.PHONY: edit
edit: makeinfo $(PYTHON_VENV)
	cd notebooks && ../$(PYTHON_VENV)/bin/marimo edit --skip-update-check --port 8088

## deploy: Run lint, build HTML/WASM, and deploy via npm
deploy: makeinfo node_modules lint html-wasm
	npm run deploy

# clean: Remove temporary files, caches, and build artifacts
.PHONY: clean
clean: makeinfo
	find . -name '*~' -type f -delete
	find . -name '*.pyc' -type f -delete
	find . -name '__pycache__' -type d -delete
	rm -rf "$(NB_EXPORT_DIR)" "$(INDEX_DIR)" node_modules

# distclean: Deep clean including removal of the Python virtual environment
.PHONY: distclean
distclean: makeinfo clean
	rm -rf "$(PYTHON_VENV)"

################################################################################
#                            Utility Commands                                  #
################################################################################

upgrade: makeinfo ## Upgrade Node (from .nvmrc), npm, and all dependencies
	@echo "📦 Reading Node version from .nvmrc..."
	@export NODE_VERSION=$$(cat .nvmrc); \
	bash -c '\
		export NVM_DIR="$$HOME/.nvm"; \
		[ -s "$$NVM_DIR/nvm.sh" ] && . "$$NVM_DIR/nvm.sh"; \
		echo "⬇️  Installing Node $$NODE_VERSION..."; \
		nvm install $$NODE_VERSION --reinstall-packages-from=current && \
		nvm alias default $$NODE_VERSION && \
		nvm use $$NODE_VERSION && \
		echo "🔧 Using Node: $$(node -v)"; \
		echo "🔧 Using npm: $$(npm -v)"'
	npm install -g npm-check-updates
	ncu -u

help: makeinfo # Show available make commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

makeinfo: # Shows the current make command running
	@goal="$(MAKECMDGOALS)"; \
	if [ "$$goal" = "" ] || [ "$$goal" = "makeinfo" ]; then goal="help"; fi; \
	echo ""; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo "🛠  Running: \033[35m$$goal\033[0m"; \
	echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"; \
	echo ""
