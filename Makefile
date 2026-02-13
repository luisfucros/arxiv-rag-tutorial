# Makefile

# Load .env if it exists
ifneq (,$(wildcard .env))
include .env
export
endif

.PHONY: install-dependencies package-wheel clean-wheels

# Files that trigger dependency install
DEPS_SOURCES := $(shell find . -name pyproject.toml) uv.lock

install-dependencies: $(DEPS_SOURCES)
	uv sync --all-groups

# Paths
ROOT_DIR := $(CURDIR)
WHEELS_DIR := $(ROOT_DIR)/wheels

TARGET_WHEEL_DIRS := \
	$(ROOT_DIR)/arxiv_api/ \
	$(ROOT_DIR)/data_ingestion/

TARGET_WHEEL_DIRS_RM := \
	$(ROOT_DIR)/arxiv_api/wheels \
	$(ROOT_DIR)/data_ingestion/wheels

# Sources that trigger wheel rebuild
PACKAGE_SOURCES := $(shell find common-lib -name "*.py") common-lib/pyproject.toml

package-wheel: $(PACKAGE_SOURCES)
	cd common-lib && \
	rm -rf $(WHEELS_DIR) $(TARGET_WHEEL_DIRS_RM) && \
	rm -rf build arxiv_lib.egg-info && \
	uv build --wheel -o $(WHEELS_DIR)

	@for dir in $(TARGET_WHEEL_DIRS); do \
		mkdir -p $$dir && cp -R $(WHEELS_DIR) $$dir; \
	done
