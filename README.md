# Celery Microservices POC

A proof-of-concept demonstration of microservices architecture using Celery for inter-service communication via task queues.

## Architecture Overview

This project demonstrates a microservices architecture with:
- **Isolated services**: Each service runs independently with its own dependencies
- **Shared task definitions**: Common task contracts via the `common_tasks` module
- **Dedicated workers**: Scalable task execution separate from business services
- **Containerized deployment**: Docker-based deployment for consistency across environments

### Services

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
# Check service health
curl http://localhost:8001/health  # example-service-1
curl http://localhost:8002/health  # example-service-2

# View logs
docker-compose logs -f worker
```

### 4. Test Task Flow

```bash
# Submit a task via service-1 (triggers cross-service communication)
curl -X POST http://localhost:8001/api/orders \\
  -H "Content-Type: application/json" \\
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

## Project Structure

```
.
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

## Documentation

- **Architecture Plan**: `specs/001-microservices-structure/plan.md`
- **Feature Specification**: `specs/001-microservices-structure/spec.md`
- **Task Contracts**: `specs/001-microservices-structure/contracts/task-contracts.md`
- **Quick Start Guide**: `specs/001-microservices-structure/quickstart.md`

## POC Scope

This is a proof-of-concept focused on demonstrating core Celery microservices patterns. Production-grade features (structured logging, metrics, circuit breakers, comprehensive error handling) are intentionally deferred. See `specs/001-microservices-structure/spec.md` for migration path to production features.

## License

[Your License Here]