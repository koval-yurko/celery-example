# Celery Microservices POC

A proof-of-concept demonstration of microservices architecture using Celery for inter-service communication via task queues.

## Architecture Overview

This project demonstrates a microservices architecture with:
- **Isolated services**: Each service runs independently with its own dependencies
- **Shared task definitions**: Common task contracts via the `common_tasks` module
- **Dedicated workers**: Scalable task execution separate from business services
- **Containerized deployment**: Docker-based deployment for consistency across environments

### Services

- **api-gateway/**: Single entry point for all client requests (routes to backend services)
- **common/**: Shared task definitions and Celery configuration
- **worker/**: Dedicated Celery worker service for task execution
- **example-service-1/**: Example business service (publishes tasks)
- **example-service-2/**: Example business service (consumes tasks)

## Prerequisites

- Python 3.11+
- Docker 24.0+ and Docker Compose 2.20+
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

## Quick Start

### 1. Clone and Setup

```bash
# Create environment file
cp .env.example .env

# Edit .env if needed (defaults work for local development)
```

### 2. Start All Services with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Verify Services

```bash
# Check API Gateway health (single entry point)
curl http://localhost:8000/health

# Check services via gateway
curl http://localhost:8000/api/service1/health
curl http://localhost:8000/api/service2/health

# Check gateway status
curl http://localhost:8000/api/gateway/status

# Or check services directly (for debugging)
curl http://localhost:8001/health  # example-service-1
curl http://localhost:8002/health  # example-service-2

# View logs
docker-compose logs -f worker
```

### 4. Test Task Flow

```bash
# Submit a task via API Gateway (recommended - single entry point)
curl -X POST http://localhost:8000/api/service1/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-001", "customer_id": "CUST-123", "items": [{"product_id": "PROD-456", "quantity": 2}], "total_amount": 99.98}'

# Or directly to service-1 (for debugging)
curl -X POST http://localhost:8001/api/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-001", "customer_id": "CUST-123", "items": [{"product_id": "PROD-456", "quantity": 2}], "total_amount": 99.98}'

# Watch worker logs to see task execution
docker-compose logs -f worker
```

## Development Workflow

### Running Services Individually

Each service can run in isolation for development:

```bash
# Run just Redis + one service
docker-compose up redis example-service-1

# Or run service locally (outside Docker)
cd example-service-1
uv sync
uv run python -m service1.main
```

### Testing Service Isolation

```bash
# Start only service-1 and Redis
docker-compose up redis example-service-1

# Service should start successfully without other services
curl http://localhost:8001/health
```

### Scaling Workers

```bash
# Scale workers to 3 instances
docker-compose up -d --scale worker=3

# Verify 3 workers running
docker-compose ps worker
```

## Docker Build & Deployment

The project includes Makefile commands for building and pushing Docker images with version tags. All images are built for both **linux/amd64** and **linux/arm64** architectures (supporting both Intel/AMD and Apple Silicon Macs, as well as Linux servers).

### Building Docker Images

Build a single service with a specific version (creates multi-platform images in buildx cache):

```bash
# Build worker service
make docker-build worker 0.0.1

# Build service-1
make docker-build service-1 0.0.1

# Build service-2
make docker-build service-2 0.0.1

# Build API gateway
make docker-build api-gateway 0.0.1
```

Build all services at once:

```bash
# Build all services with the same version
make docker-build-all 0.0.1
```

**Note:** The `docker-build` command creates multi-platform images for both architectures and also loads the native platform image into your local Docker daemon (so it appears in `docker images`). The multi-platform images are stored in the buildx cache and can be pushed to a registry using `docker-push`. For local development and testing, you can also use `docker-compose` which builds images for your native platform.

### Pushing Docker Images

Push a single service (builds first, then pushes):

```bash
# Push worker service
make docker-push worker 0.0.1

# Push service-1
make docker-push service-1 0.0.1

# Push service-2
make docker-push service-2 0.0.1

# Push API gateway
make docker-push api-gateway 0.0.1
```

Push all services at once:

```bash
# Build and push all services
make docker-push-all 0.0.1
```

### Multi-Platform Builds

All images are built for both architectures:
- **linux/amd64** - Intel/AMD processors (Intel Macs, Linux servers)
- **linux/arm64** - ARM processors (Apple Silicon Macs, ARM-based servers)

The Makefile automatically uses Docker buildx to create multi-platform images. On first use, it will set up the buildx builder if needed.

### Image Tags

All images are tagged with the format: `failwin/celery-example-{service-name}:{version}`

Examples:
- `failwin/celery-example-worker:0.0.1`
- `failwin/celery-example-service-1:0.0.1`
- `failwin/celery-example-service-2:0.0.1`
- `failwin/celery-example-api-gateway:0.0.1`

### Available Services

The following service names are supported:
- `worker` - Celery worker service
- `service-1` - Example service 1
- `service-2` - Example service 2
- `api-gateway` - API Gateway service

## Project Structure

```
.
├── api-gateway/             # API Gateway (single entry point)
│   ├── src/api_gateway/    # Routing, proxy, health checks
│   ├── pyproject.toml
│   └── Dockerfile
├── common/                  # Shared task definitions
│   ├── src/common_tasks/   # Task definitions, schemas, Celery config
│   ├── pyproject.toml
│   └── Dockerfile
├── worker/                  # Dedicated worker service
│   ├── src/worker/         # Worker configuration and startup
│   ├── pyproject.toml
│   └── Dockerfile
├── example-service-1/       # Example business service
│   ├── src/service1/       # Service logic, API, task publishers
│   ├── pyproject.toml
│   └── Dockerfile
├── example-service-2/       # Example business service
│   ├── src/service2/       # Service logic, task consumers
│   ├── pyproject.toml
│   └── Dockerfile
├── docker-compose.yml       # Local orchestration
└── .env.example            # Environment variables template
```

## Development with uv

### Managing Dependencies

```bash
# Add dependency to a service
cd example-service-1
uv add package-name

# Add development dependency
uv add --dev pytest

# Update dependencies
uv lock --upgrade
```

### Running Tests

```bash
# Run tests for a service
cd example-service-1
uv run pytest

# Run all tests
docker-compose run --rm example-service-1 pytest
```

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker

# Last 100 lines
docker-compose logs --tail=100 worker
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart worker

# Rebuild and restart (after code changes)
docker-compose up -d --build worker
```

### Clean Up

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clears Redis data)
docker-compose down -v

# Remove all containers and images
docker-compose down --rmi all
```

## Troubleshooting

### Service won't start

```bash
# View service logs
docker-compose logs example-service-1

# Check environment variables
docker-compose config

# Rebuild without cache
docker-compose build --no-cache
```

### Worker not processing tasks

```bash
# Verify worker is running
docker-compose ps worker

# Check worker logs
docker-compose logs worker

# Verify Redis connection
docker-compose exec worker python -c "from common_tasks.celery_app import celery_app; print(celery_app.connection())"
```

### Task fails with ModuleNotFoundError

```bash
# Rebuild worker with common module
docker-compose build worker

# Verify common module installed
docker-compose exec worker python -c "import common_tasks; print(common_tasks.__file__)"
```

## API Gateway

The API Gateway provides a single entry point for all client requests, routing them to the appropriate backend services.

### Routing Patterns

| Path Pattern | Target Service |
|-------------|----------------|
| `/api/service1/*` | example-service-1 |
| `/api/service2/*` | example-service-2 |
| `/api/gateway/*` | Gateway-owned endpoints |
| `/health` | Gateway health check |

### Gateway Endpoints

```bash
# Gateway health check
curl http://localhost:8000/health

# Gateway status (includes registered services)
curl http://localhost:8000/api/gateway/status

# List registered services
curl http://localhost:8000/api/gateway/services
```

### Configuration

Environment variables for the API Gateway:

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_HOST` | `0.0.0.0` | Bind address |
| `GATEWAY_PORT` | `8000` | Listen port |
| `GATEWAY_TIMEOUT` | `30` | Default request timeout (seconds) |
| `GATEWAY_LOG_LEVEL` | `INFO` | Logging level |
| `SERVICE1_URL` | - | Backend URL for service1 |
| `SERVICE2_URL` | - | Backend URL for service2 |

### Error Responses

The gateway returns structured error responses:

```json
{
  "error": "service_unavailable",
  "message": "Backend service 'service1' is not responding",
  "path": "/api/service1/orders",
  "timestamp": "2024-01-15T10:30:00Z",
  "status_code": 503
}
```

Error codes: `not_found` (404), `bad_gateway` (502), `service_unavailable` (503), `gateway_timeout` (504)

## Documentation

- **Architecture Plan**: `specs/001-microservices-structure/plan.md`
- **Feature Specification**: `specs/001-microservices-structure/spec.md`
- **Task Contracts**: `specs/001-microservices-structure/contracts/task-contracts.md`
- **Quick Start Guide**: `specs/001-microservices-structure/quickstart.md`
- **API Gateway Plan**: `specs/002-api-gateway/plan.md`
- **API Gateway Spec**: `specs/002-api-gateway/spec.md`

## POC Scope

This is a proof-of-concept focused on demonstrating core Celery microservices patterns. Production-grade features (structured logging, metrics, circuit breakers, comprehensive error handling) are intentionally deferred. See `specs/001-microservices-structure/spec.md` for migration path to production features.

## License

[Your License Here]