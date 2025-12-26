.PHONY: docker-build docker-build-all docker-push docker-push-all docker-setup-buildx

# Setup buildx builder for multi-platform builds
docker-setup-buildx:
	@if ! docker buildx ls | grep -q multiarch; then \
		echo "Creating buildx builder for multi-platform builds..."; \
		docker buildx create --name multiarch --use || docker buildx use multiarch; \
	fi
	@docker buildx inspect --bootstrap

# Extract positional arguments

# Extract positional arguments
SERVICE = $(word 2, $(MAKECMDGOALS))
VERSION = $(word 3, $(MAKECMDGOALS))

# Mark arguments as phony so make doesn't try to build them as files
ifneq ($(SERVICE),)
  .PHONY: $(SERVICE)
  $(SERVICE):
	@:
endif
ifneq ($(VERSION),)
  .PHONY: $(VERSION)
  $(VERSION):
	@:
endif

# Build a single service with version
# Usage: make docker-build worker 0.0.1
docker-build:
	@if [ -z "$(SERVICE)" ] || [ -z "$(VERSION)" ]; then \
		echo "Usage: make docker-build <service> <version>"; \
		echo "Services: worker, service-1, service-2, api-gateway"; \
		exit 1; \
	fi
	@case "$(SERVICE)" in \
		worker) \
			dockerfile="worker/Dockerfile"; \
			image="failwin/celery-example-worker"; \
			;; \
		service-1) \
			dockerfile="example-service-1/Dockerfile"; \
			image="failwin/celery-example-service-1"; \
			;; \
		service-2) \
			dockerfile="example-service-2/Dockerfile"; \
			image="failwin/celery-example-service-2"; \
			;; \
		api-gateway) \
			dockerfile="api-gateway/Dockerfile"; \
			image="failwin/celery-example-api-gateway"; \
			;; \
		*) \
			echo "Unknown service: $(SERVICE)"; \
			echo "Services: worker, service-1, service-2, api-gateway"; \
			exit 1; \
			;; \
	esac; \
	echo "Building $$image:$(VERSION) for linux/amd64,linux/arm64..."; \
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f $$dockerfile \
		-t $$image:$(VERSION) \
		. && \
	echo "Loading native platform image into local Docker..."; \
	docker build \
		-f $$dockerfile \
		-t $$image:$(VERSION) \
		. && \
	echo "Successfully built $$image:$(VERSION) for both architectures (multi-platform in buildx cache, native platform loaded locally - use docker-push to push all platforms)"

# Extract version for docker-build-all
VERSION_ALL = $(word 2, $(MAKECMDGOALS))
ifneq ($(VERSION_ALL),)
  .PHONY: $(VERSION_ALL)
  $(VERSION_ALL):
	@:
endif

# Build all services with version
# Usage: make docker-build-all 0.0.1
docker-build-all: docker-setup-buildx
	@if [ -z "$(VERSION_ALL)" ]; then \
		echo "Usage: make docker-build-all <version>"; \
		exit 1; \
	fi
	@echo "Building all services with version $(VERSION_ALL) for linux/amd64,linux/arm64..."
	@$(MAKE) docker-build worker $(VERSION_ALL)
	@$(MAKE) docker-build service-1 $(VERSION_ALL)
	@$(MAKE) docker-build service-2 $(VERSION_ALL)
	@$(MAKE) docker-build api-gateway $(VERSION_ALL)
	@echo "All services built successfully for both architectures!"

# Push a single service with version
# Usage: make docker-push worker 0.0.1
docker-push: docker-setup-buildx
	@if [ -z "$(SERVICE)" ] || [ -z "$(VERSION)" ]; then \
		echo "Usage: make docker-push <service> <version>"; \
		exit 1; \
	fi
	@case "$(SERVICE)" in \
		worker) \
			dockerfile="worker/Dockerfile"; \
			image="failwin/celery-example-worker"; \
			;; \
		service-1) \
			dockerfile="example-service-1/Dockerfile"; \
			image="failwin/celery-example-service-1"; \
			;; \
		service-2) \
			dockerfile="example-service-2/Dockerfile"; \
			image="failwin/celery-example-service-2"; \
			;; \
		api-gateway) \
			dockerfile="api-gateway/Dockerfile"; \
			image="failwin/celery-example-api-gateway"; \
			;; \
		*) echo "Unknown service: $(SERVICE)"; exit 1; ;; \
	esac; \
	echo "Building and pushing $$image:$(VERSION) for linux/amd64,linux/arm64..."; \
	docker buildx build \
		--platform linux/amd64,linux/arm64 \
		-f $$dockerfile \
		-t $$image:$(VERSION) \
		--push \
		. && \
	echo "Successfully built and pushed $$image:$(VERSION) for both architectures"

# Extract version for docker-push-all
VERSION_PUSH_ALL = $(word 2, $(MAKECMDGOALS))
ifneq ($(VERSION_PUSH_ALL),)
  .PHONY: $(VERSION_PUSH_ALL)
  $(VERSION_PUSH_ALL):
	@:
endif

# Push all services with version
# Usage: make docker-push-all 0.0.1
docker-push-all: docker-setup-buildx
	@if [ -z "$(VERSION_PUSH_ALL)" ]; then \
		echo "Usage: make docker-push-all <version>"; \
		exit 1; \
	fi
	@echo "Building and pushing all services with version $(VERSION_PUSH_ALL) for linux/amd64,linux/arm64..."
	@$(MAKE) docker-push worker $(VERSION_PUSH_ALL)
	@$(MAKE) docker-push service-1 $(VERSION_PUSH_ALL)
	@$(MAKE) docker-push service-2 $(VERSION_PUSH_ALL)
	@$(MAKE) docker-push api-gateway $(VERSION_PUSH_ALL)
	@echo "All services built and pushed successfully for both architectures!"
