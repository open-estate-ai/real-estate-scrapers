SHELL := /usr/bin/env bash

# --- CDK Environment Targets ---
CDK_DIR=cdk
CDK_VENV=$(CDK_DIR)/.cdk-venv
CDK_REQ=$(CDK_DIR)/requirements-cdk.txt


# default env; override with: make cdk-synth ENV=prod
ENV ?= dev
PARAM_FILE := envs/$(ENV).params.json
OUT_DIR := $(CDK_DIR)/output/$(ENV)


# Default architecture
ARCH ?= x86_64

.PHONY: build cdk-env cdk-activate cdk-synth cdk-deploy cdk-destroy

build:
	./scripts/build_scraper.sh --arch $(ARCH)

# Setup CDK venv, install deps, and print activation instructions
cdk-env:
	cd $(CDK_DIR) && python3 -m venv .cdk-venv
	cd $(CDK_DIR) && . .cdk-venv/bin/activate && pip install --upgrade pip setuptools wheel
	cd $(CDK_DIR) && . .cdk-venv/bin/activate && pip install -r requirements-cdk.txt
	@echo ""
	@echo "✅ CDK environment ready."
	@echo "To activate run:"
	@echo "source $(CDK_VENV)/bin/activate"

# Cleanup CDK venv
cdk-clean:
	@echo "Removing CDK venv: $(CDK_VENV)"
	deactivate 2>/dev/null || true
	rm -rf $(CDK_VENV)

# Synthesize CloudFormation template for ENV using params from JSON
cdk-synth:
	./scripts/build_scraper.sh --arch $(ARCH)
	./scripts/cdk-cli.sh synth $(ENV)

cdk-deploy:
	./scripts/build_scraper.sh --arch $(ARCH)
	./scripts/cdk-cli.sh deploy $(ENV)

cdk-destroy:
	./scripts/cdk-cli.sh destroy $(ENV)
