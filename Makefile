# LocalStack configuration
ENDPOINT=http://localhost:4566
BUCKET=arxiv-service
REGION=us-east-1

export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=$(REGION)

.PHONY: install-dependencies package-wheel clean-wheels create-bucket list-buckets delete-bucket

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

make-local-bucket:
	aws --endpoint-url=$(ENDPOINT) s3 mb s3://$(BUCKET)

# todo: workflow docker compose + make local bucket
run-app:
	@package-wheel
	docker compose watchup --build -d
	@make-local-bucket