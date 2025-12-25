# Quick Start Guide: Microservices Repository Structure

**Feature**: 001-microservices-structure
**Date**: 2025-12-25
**Audience**: Developers setting up local environment

## Prerequisites

- Docker 24.0+ and Docker Compose 2.20+
- Python 3.11+ (for local development without Docker)
- Git (for cloning repository)
- 8GB RAM minimum (for running all services)

---

## Quick Start (5 Minutes)

### 1. Clone and Setup

```bash
# Clone repository
cd /path/to/celery-example

# Create environment file from example
cp .env.example .env

# Edit .env if needed (defaults should work for local development)
# REDIS_BROKER_URL=redis://redis:6379/0
# REDIS_RESULT_BACKEND=redis://redis:6379/1
```

### 2. Build All Services

```bash
# Build all containers
docker-compose build

# Expected output: 4 services built (common, worker, example-service-1, example-service-2)
```

### 3. Start Services

```bash
# Start Redis + all services
docker-compose up

# Or run in background
docker-compose up -d

# Check service health
docker-compose ps
```

**Expected output**:
```
NAME                   STATUS    PORTS
redis                  Up        6379/tcp
worker                 Up
example-service-1      Up        8001:8000/tcp
example-service-2      Up        8002:8000/tcp
```

### 4. Verify Setup

```bash
# Test service 1 health
curl http://localhost:8001/health
# Expected: {"status": "healthy", "service": "example-service-1"}

# Test service 2 health
curl http://localhost:8002/health
# Expected: {"status": "healthy", "service": "example-service-2"}

# Test worker connectivity
docker-compose logs worker
# Expected: "celery@worker ready"
```

### 5. Run Example Workflow

```bash
# Submit order via service 1 (triggers order processing → notification)
curl -X POST http://localhost:8001/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-test-001",
    "customer_id": "CUST-123",
    "items": [{"product_id": "PROD-456", "quantity": 2}],
    "total_amount": 99.98
  }'

# Expected response:
# {
#   "status": "accepted",
#   "order_id": "ORD-test-001",
#   "task_id": "task-abc123"
# }

# Check worker logs to see task execution
docker-compose logs -f worker

# Check service 2 logs to see notification delivery
docker-compose logs -f example-service-2
```

---

## Development Workflow

### Running Individual Services

Each service can run in isolation for development:

```bash
# Run just Redis + specific service
docker-compose up redis example-service-1

# Or run service locally (outside Docker)
cd example-service-1
python -m pip install -e .
python -m service1.main
```

### Testing Service Isolation (User Story 1)

```bash
# Start only service 1 and Redis
docker-compose up redis example-service-1

# Service 1 should start successfully without service 2 or worker
curl http://localhost:8001/health
# Expected: 200 OK

# Stop and verify independence
docker-compose down
```

### Testing Shared Task Definitions (User Story 2)

```bash
# Make changes to common/src/common_tasks/tasks.py

# Rebuild services that depend on common module
docker-compose build worker example-service-1 example-service-2

# Restart services
docker-compose up -d

# Verify changes propagated
docker-compose logs worker | grep "tasks loaded"
```

### Testing Worker Scaling (User Story 3)

```bash
# Scale workers to 3 instances
docker-compose up -d --scale worker=3

# Verify 3 workers running
docker-compose ps worker
# Expected: worker_1, worker_2, worker_3 all Up

# Submit multiple tasks and watch distribution
for i in {1..10}; do
  curl -X POST http://localhost:8001/api/orders -d "{...}"
done

# Check which worker processed each task
docker-compose logs worker | grep "Task tasks.process_order"
```

---

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
docker-compose logs -f example-service-1

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

---

## Troubleshooting

### Service won't start

**Symptom**: `docker-compose up` shows service exiting immediately

**Check**:
```bash
# View service logs
docker-compose logs example-service-1

# Check for missing environment variables
docker-compose config
```

**Common fixes**:
- Verify `.env` file exists and has correct Redis URL
- Check if port 8001/8002 is already in use: `lsof -i :8001`
- Rebuild after dependency changes: `docker-compose build --no-cache`

### Worker not processing tasks

**Symptom**: Tasks submitted but not executed

**Check**:
```bash
# Verify worker is running
docker-compose ps worker

# Check worker logs for errors
docker-compose logs worker

# Verify Redis connection
docker-compose exec worker python -c "from common_tasks.celery_app import celery_app; print(celery_app.connection().ensure_connection())"
```

**Common fixes**:
- Ensure worker imports tasks: Check `worker/src/worker/main.py`
- Verify Redis is running: `docker-compose ps redis`
- Check queue names match: Worker must listen to correct queue

### Task fails with "ModuleNotFoundError"

**Symptom**: Worker logs show `ModuleNotFoundError: No module named 'common_tasks'`

**Fix**:
```bash
# Rebuild worker with common module
docker-compose build worker

# Verify common module installed in worker
docker-compose exec worker python -c "import common_tasks; print(common_tasks.__file__)"
```

### Services can't connect to Redis

**Symptom**: `ConnectionError: Error -2 connecting to redis:6379`

**Check**:
```bash
# Verify Redis container running
docker-compose ps redis

# Test Redis connectivity from another service
docker-compose exec example-service-1 ping redis

# Check Redis logs
docker-compose logs redis
```

**Common fixes**:
- Ensure Redis started before services: `docker-compose up redis` first
- Verify `.env` has correct `REDIS_BROKER_URL=redis://redis:6379/0`
- Check Docker network: `docker network inspect celery-example_default`

---

## Manual Testing Scenarios

### Scenario 1: Service Isolation (User Story 1)

**Goal**: Verify services run independently

```bash
# Start only service 1
docker-compose up -d redis example-service-1

# Service should start without errors
docker-compose logs example-service-1
# Expected: No connection errors to service 2 or worker

# Test API
curl http://localhost:8001/health
# Expected: 200 OK

# Stop
docker-compose down
```

**Success Criteria**: Service starts and responds to health checks without other services running

### Scenario 2: Shared Task Definitions (User Story 2)

**Goal**: Verify both services use same task definitions from common module

```bash
# Start all services
docker-compose up -d

# Check service 1 imports common_tasks
docker-compose exec example-service-1 python -c "from common_tasks import tasks; print(dir(tasks))"
# Expected: ['process_order', 'send_notification', 'health_check']

# Check service 2 imports same module
docker-compose exec example-service-2 python -c "from common_tasks import tasks; print(dir(tasks))"
# Expected: Same output as service 1

# Modify common module (add print statement to process_order)
# Edit common/src/common_tasks/tasks.py

# Rebuild and verify change propagated to both services
docker-compose build worker example-service-1 example-service-2
docker-compose up -d
docker-compose logs worker | grep "your print statement"
```

**Success Criteria**: Both services import and use identical task definitions

### Scenario 3: Worker Scaling (User Story 3)

**Goal**: Verify workers scale independently and process tasks in parallel

```bash
# Start with 1 worker
docker-compose up -d

# Submit 5 tasks
for i in {1..5}; do
  curl -X POST http://localhost:8001/api/orders -d '{"order_id":"ORD-'$i'", ...}'
done

# Check processing time
# (Baseline: 5 tasks × 2 seconds = ~10 seconds total)

# Scale to 3 workers
docker-compose up -d --scale worker=3

# Submit 5 more tasks
for i in {6..10}; do
  curl -X POST http://localhost:8001/api/orders -d '{"order_id":"ORD-'$i'", ...}'
done

# Check processing time
# (Expected: 5 tasks / 3 workers × 2 seconds = ~4 seconds total)

# Verify tasks distributed across workers
docker-compose logs worker | grep "Task tasks.process_order" | awk '{print $1}' | sort | uniq -c
# Expected: Tasks processed by multiple worker containers
```

**Success Criteria**: Throughput increases linearly with worker count; tasks distributed across workers

### Scenario 4: Containerized Deployment (User Story 4)

**Goal**: Verify same container works in different environments

```bash
# Build on local machine
docker-compose build example-service-1

# Export container
docker save -o service1.tar celery-example-example-service-1:latest

# Copy to another machine (simulated: just re-import)
docker load -i service1.tar

# Run with different environment variables
docker run -e REDIS_BROKER_URL=redis://different-host:6379/0 \
  celery-example-example-service-1:latest

# Verify service connects to different Redis host
```

**Success Criteria**: Same container image works in different environments with only env var changes

---

## Performance Benchmarks

### Expected Performance (POC)

- **Service startup time**: < 10 seconds (all services)
- **Task execution time**: 1-5 seconds (process_order)
- **Notification delivery**: < 1 second (send_notification)
- **Worker throughput**: ~20 tasks/minute/worker (single-threaded)

### Load Testing (Optional)

```bash
# Install Apache Bench
apt-get install apache2-utils  # or brew install httpd

# Submit 100 orders concurrently (10 at a time)
ab -n 100 -c 10 -T 'application/json' -p order.json \
  http://localhost:8001/api/orders

# Analyze results
# - Requests per second
# - Mean response time
# - Percentage of requests served within certain time
```

---

## Next Steps

After verifying POC works:

1. **Add production features** (see spec.md POC Exemptions):
   - Structured logging (structlog)
   - Metrics collection (Prometheus)
   - Circuit breakers (pybreaker)
   - Comprehensive tests (pytest)

2. **Implement real business logic**:
   - Replace example services with actual domain services
   - Add database persistence
   - Integrate external APIs (payment, email providers)

3. **Deploy to production**:
   - Kubernetes manifests
   - CI/CD pipeline
   - Monitoring dashboards
   - Auto-scaling policies

---

## References

- Docker Compose documentation: https://docs.docker.com/compose/
- Celery documentation: https://docs.celeryq.dev/
- Project README: `../../README.md`
- Architecture plan: `./plan.md`
- Task contracts: `./contracts/task-contracts.md`