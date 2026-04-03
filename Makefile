# =============================================================================
# arxiv-rag-tutorial — local development vs AWS/Terraform deploy
# =============================================================================
# Local:   make local-help
# AWS:     copy infrastructure/terraform.tfvars.sample → terraform.tfvars
#          copy infrastructure/secrets.auto.tfvars.sample → secrets.auto.tfvars
#          make prod-help && make prod-deploy
# Terraform auto-loads terraform.tfvars and *.auto.tfvars from infrastructure/
# (no manual export of TF_VAR_* required for normal use).
# =============================================================================

SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

AWS_PROFILE ?= default
export AWS_PROFILE

TF_DIR := infrastructure
IMAGE_TAG ?= latest

ROOT_DIR := $(CURDIR)
WHEELS_DIR := $(ROOT_DIR)/wheels

TARGET_WHEEL_DIRS := \
	$(ROOT_DIR)/arxiv_backend/ \
	$(ROOT_DIR)/data_ingestion/ \
	$(ROOT_DIR)/migrations/

TARGET_WHEEL_DIRS_RM := \
	$(ROOT_DIR)/arxiv_backend/wheels \
	$(ROOT_DIR)/data_ingestion/wheels \
	$(ROOT_DIR)/migrations/wheels

PACKAGE_SOURCES := $(shell find common-lib -name '*.py' 2>/dev/null) common-lib/pyproject.toml

# AWS region for CLI: terraform.tfvars aws_region → env AWS_REGION → aws configure → us-east-1
_tf_region_from_file := $(shell grep -E '^\s*aws_region\s*=' "$(TF_DIR)/terraform.tfvars" 2>/dev/null | head -1 | sed -E 's/.*=\s*"([^"]+)".*/\1/')
TF_AWS_REGION ?= $(_tf_region_from_file)
ifeq ($(strip $(TF_AWS_REGION)),)
  TF_AWS_REGION := $(shell printenv AWS_REGION)
endif
ifeq ($(strip $(TF_AWS_REGION)),)
  TF_AWS_REGION := $(shell aws configure get region 2>/dev/null)
endif
ifeq ($(strip $(TF_AWS_REGION)),)
  TF_AWS_REGION := us-east-1
endif
export TF_AWS_REGION

.PHONY: help local-help prod-help
.PHONY: local-install local-package-wheels local-clean-wheels local-up local-watch local-down
.PHONY: prod-check-config prod-tf-init prod-tf-validate prod-tf-plan prod-tf-apply
.PHONY: prod-docker-login prod-docker-push-all prod-run-migration prod-ecs-rollout prod-deploy

help:
	@echo "Targets — local: make local-help | AWS: make prod-help"

# =============================================================================
# Local — Docker Compose + wheels (no Terraform)
# =============================================================================

local-help:
	@echo "Local development targets:"
	@echo "  local-install          uv sync (repo root)"
	@echo "  local-package-wheels   build common-lib wheel + copy into app images"
	@echo "  local-clean-wheels     remove wheels/ and app wheels dirs"
	@echo "  local-up               docker compose up --build -d"
	@echo "  local-watch            docker compose watch (dev sync)"
	@echo "  local-down             docker compose down"

local-install:
	uv sync --all-groups

local-package-wheels: $(PACKAGE_SOURCES)
	cd common-lib && \
	rm -rf "$(WHEELS_DIR)" $(TARGET_WHEEL_DIRS_RM) && \
	rm -rf build arxiv_lib.egg-info && \
	uv build --wheel -o "$(WHEELS_DIR)"
	@for dir in $(TARGET_WHEEL_DIRS); do \
		mkdir -p $$dir/wheels && cp -R "$(WHEELS_DIR)"/* $$dir/wheels/; \
	done

local-clean-wheels:
	rm -rf "$(WHEELS_DIR)" $(TARGET_WHEEL_DIRS_RM)

local-up: local-package-wheels
	docker compose up --build -d

local-watch: local-package-wheels
	docker compose watch

local-down:
	docker compose down

# =============================================================================
# Production / CI — Terraform + ECR + ECS (vars from tfvars files only)
# =============================================================================

prod-help:
	@echo "AWS deploy targets (requires $(TF_DIR)/terraform.tfvars + secrets.auto.tfvars):"
	@echo "  prod-check-config       verify tfvars files exist"
	@echo "  prod-tf-init            terraform init"
	@echo "  prod-tf-validate          terraform validate"
	@echo "  prod-tf-plan            terraform plan"
	@echo "  prod-tf-apply           terraform apply -auto-approve"
	@echo "  prod-docker-login       ECR login (uses terraform outputs + aws_region from tfvars)"
	@echo "  prod-docker-push-all    build+push migration, backend, frontend, data_ingestion"
	@echo "  prod-run-migration      one-shot Fargate migration task (private subnets)"
	@echo "  prod-ecs-rollout        force new deployment on app ECS services"
	@echo "  prod-deploy             apply → login → push all → migrate → rollout"
	@echo ""
	@echo "First-time: copy terraform.tfvars.sample and secrets.auto.tfvars.sample into $(TF_DIR)/"

prod-check-config:
	@test -f "$(TF_DIR)/terraform.tfvars" || \
		(echo "Missing $(TF_DIR)/terraform.tfvars — copy from terraform.tfvars.sample"; exit 1)
	@test -f "$(TF_DIR)/secrets.auto.tfvars" || \
		(echo "Missing $(TF_DIR)/secrets.auto.tfvars — copy from secrets.auto.tfvars.sample"; exit 1)

prod-tf-init: prod-check-config
	cd "$(TF_DIR)" && terraform init

prod-tf-validate: prod-check-config
	cd "$(TF_DIR)" && terraform validate

prod-tf-plan: prod-check-config
	cd "$(TF_DIR)" && terraform plan

prod-tf-apply: prod-check-config
	cd "$(TF_DIR)" && terraform apply -auto-approve

prod-docker-login: prod-check-config
	@cd "$(TF_DIR)" && \
	URL=$$(terraform output -json ecr_repository_urls | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['migration'])") && \
	REGISTRY=$${URL%%/*} && \
	echo "ECR registry: $$REGISTRY (region $(TF_AWS_REGION))" && \
	aws ecr get-login-password --region "$(TF_AWS_REGION)" | docker login --username AWS --password-stdin "$$REGISTRY"

prod-docker-push-all: prod-check-config local-package-wheels prod-docker-login
	@cd "$(TF_DIR)" && \
	MIG=$$(terraform output -json ecr_repository_urls | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['migration'])") && \
	BE=$$(terraform output -json ecr_repository_urls | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['backend'])") && \
	FE=$$(terraform output -json ecr_repository_urls | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['frontend'])") && \
	WK=$$(terraform output -json ecr_repository_urls | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['data_ingestion'])") && \
	cd "$(ROOT_DIR)" && \
	echo "== Build/push migration $$MIG:$(IMAGE_TAG) ==" && \
	docker build -t "$$MIG:$(IMAGE_TAG)" -f migrations/Dockerfile migrations && \
	docker push "$$MIG:$(IMAGE_TAG)" && \
	echo "== Build/push backend $$BE:$(IMAGE_TAG) ==" && \
	docker build -t "$$BE:$(IMAGE_TAG)" -f arxiv_backend/Dockerfile arxiv_backend && \
	docker push "$$BE:$(IMAGE_TAG)" && \
	echo "== Build/push frontend $$FE:$(IMAGE_TAG) ==" && \
	docker build --build-arg VITE_API_URL= -t "$$FE:$(IMAGE_TAG)" -f frontend/Dockerfile frontend && \
	docker push "$$FE:$(IMAGE_TAG)" && \
	echo "== Build/push data_ingestion $$WK:$(IMAGE_TAG) ==" && \
	docker build -t "$$WK:$(IMAGE_TAG)" -f data_ingestion/Dockerfile data_ingestion && \
	docker push "$$WK:$(IMAGE_TAG)"

prod-run-migration: prod-check-config
	@cd "$(TF_DIR)" && \
	CLUSTER=$$(terraform output -raw migration_cluster_name) && \
	TASK_DEF=$$(terraform output -raw migration_task_definition_arn) && \
	SG=$$(terraform output -raw ecs_security_group_id) && \
	SUBNETS=$$(terraform output -json private_subnet_ids | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print('['+','.join(v)+']')") && \
	echo "Running migration task on cluster $$CLUSTER (private subnets, no public IP)…" && \
	TASK_ARN=$$(aws ecs run-task \
		--region "$(TF_AWS_REGION)" \
		--cluster "$$CLUSTER" \
		--task-definition "$$TASK_DEF" \
		--launch-type FARGATE \
		--count 1 \
		--network-configuration "awsvpcConfiguration={subnets=$$SUBNETS,securityGroups=[$$SG],assignPublicIp=DISABLED}" \
		--query 'tasks[0].taskArn' --output text) && \
	echo "Waiting for task: $$TASK_ARN" && \
	aws ecs wait tasks-stopped --region "$(TF_AWS_REGION)" --cluster "$$CLUSTER" --tasks "$$TASK_ARN"

prod-ecs-rollout: prod-check-config
	@cd "$(TF_DIR)" && \
	CLUSTER=$$(terraform output -raw ecs_app_cluster_name) && \
	BE=$$(terraform output -json ecs_app_service_names | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['backend'])") && \
	FE=$$(terraform output -json ecs_app_service_names | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['frontend'])") && \
	WK=$$(terraform output -json ecs_app_service_names | python3 -c "import json,sys;d=json.load(sys.stdin);v=d['value'] if isinstance(d,dict) and 'value' in d else d;print(v['worker'])") && \
		for SVC in "$$BE" "$$FE" "$$WK"; do \
		echo "Force new deployment: $$CLUSTER / $$SVC"; \
		AWS_PAGER= aws ecs update-service --region "$(TF_AWS_REGION)" --cluster "$$CLUSTER" --service "$$SVC" --force-new-deployment; \
	done

# Full pipeline: infra → images → DB migrate → recycle ECS tasks
prod-deploy: prod-tf-apply prod-docker-push-all prod-run-migration prod-ecs-rollout
	@cd "$(TF_DIR)" && echo "Public app URL: http://$$(terraform output -raw public_alb_dns_name)"
