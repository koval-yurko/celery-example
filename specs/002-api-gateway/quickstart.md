# Quickstart: API Gateway Service

**Feature**: 002-api-gateway
**Date**: 2025-12-26

## Prerequisites

- Python 3.11+
- uv (dependency manager)
- Docker and Docker Compose (for full stack testing)
- Backend services running (example-service-1, example-service-2)

## Local Development Setup

### 1. Install Dependencies

From repository root:

```bash
# Install all workspace packages including api-gateway
uv sync

# Verify installation
python -c "from api_gateway.main import app; print('Gateway module loaded')"
```

### 2. Configure Environment

Create `api-gateway/.env` (or export variables):

```bash
# Gateway configuration
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
GATEWAY_TIMEOUT=30
GATEWAY_LOG_LEVEL=INFO

# Backend service URLs
SERVICE1_URL=http://localhost:8001
SERVICE2_URL=http://localhost:8002
```

### 3. Start the Gateway

```bash
# From repository root
cd api-gateway
uvicorn api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
```

Or using the module:

```bash
python -m api_gateway.main
```

## Docker Compose Setup

### 1. Start Full Stack

```bash
# From repository root
docker-compose up --build
```

This starts:
- Redis (message broker)
- example-service-1 (port 8001)
- example-service-2 (port 8002)
- api-gateway (port 8000)
- worker (Celery worker)

### 2. Verify Gateway

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","service":"api-gateway","version":"0.1.0","timestamp":"..."}
```

## Integration Scenarios

### Scenario 1: Route Request to Service1

**Test**: Verify requests to `/api/service1/*` are forwarded correctly.

```bash
# Create an order through the gateway
curl -X POST http://localhost:8000/api/service1/orders \
  -H "Content-Type: application/json" \
  -d '{"order_id": "ORD-001", "customer_id": "CUST-001", "items": [], "total": 99.99}'

# Expected: Response from service1's /api/orders endpoint
```

### Scenario 2: Route Request to Service2

**Test**: Verify requests to `/api/service2/*` are forwarded correctly.

```bash
# Send notification through the gateway
curl -X POST http://localhost:8000/api/service2/notifications/send \
  -H "Content-Type: application/json" \
  -d '{"recipient": "user@example.com", "message": "Hello", "type": "EMAIL"}'

# Expected: Response from service2's /api/notifications/send endpoint
```

### Scenario 3: Health Check

**Test**: Verify health endpoint returns gateway status.

```bash
curl http://localhost:8000/health

# Expected:
# {
#   "status": "healthy",
#   "service": "api-gateway",
#   "version": "0.1.0",
#   "timestamp": "2025-12-26T12:00:00Z"
# }
```

### Scenario 4: Gateway-Owned Endpoints

**Test**: Verify gateway handles its own endpoints without forwarding.

```bash
# Get gateway status
curl http://localhost:8000/api/gateway/status

# Expected:
# {
#   "status": "running",
#   "version": "0.1.0",
#   "services": [
#     {"name": "service1", "prefix": "/api/service1", "status": "configured"},
#     {"name": "service2", "prefix": "/api/service2", "status": "configured"}
#   ]
# }

# List registered services
curl http://localhost:8000/api/gateway/services

# Expected: Array of ServiceInfo objects
```

### Scenario 5: Unknown Route (404)

**Test**: Verify 404 response for unknown service paths.

```bash
curl http://localhost:8000/api/service3/unknown

# Expected:
# {
#   "error": "not_found",
#   "message": "No route found for path: /api/service3/unknown",
#   "path": "/api/service3/unknown",
#   "timestamp": "...",
#   "status_code": 404
# }
```

### Scenario 6: Backend Unavailable (503)

**Test**: Verify 503 response when backend is down.

```bash
# Stop service1, then:
curl http://localhost:8000/api/service1/orders

# Expected:
# {
#   "error": "service_unavailable",
#   "message": "Backend service 'service1' is not responding",
#   "path": "/api/service1/orders",
#   "timestamp": "...",
#   "status_code": 503
# }
```

### Scenario 7: Request Timeout (504)

**Test**: Verify 504 response when backend takes too long.

```bash
# With GATEWAY_TIMEOUT=1 (very short):
curl http://localhost:8000/api/service1/slow-endpoint

# Expected (if backend takes >1s):
# {
#   "error": "gateway_timeout",
#   "message": "Request to 'service1' timed out after 1 seconds",
#   "path": "/api/service1/slow-endpoint",
#   "timestamp": "...",
#   "status_code": 504
# }
```

### Scenario 8: Preserve Headers and Query Params

**Test**: Verify headers and query parameters are forwarded.

```bash
# With custom header and query params
curl "http://localhost:8000/api/service1/orders?status=pending&limit=10" \
  -H "Authorization: Bearer token123" \
  -H "X-Custom-Header: custom-value"

# Verify in service1 logs that it received:
# - Query params: status=pending, limit=10
# - Headers: Authorization, X-Custom-Header
```

## Performance Validation

### SC-001/SC-002: Request Overhead (<100ms)

```bash
# Direct to service1
time curl http://localhost:8001/api/health

# Through gateway
time curl http://localhost:8000/api/service1/health

# Compare times - gateway should add <100ms
```

### SC-003: Health Check Response (<50ms)

```bash
# Time health check endpoint
for i in {1..10}; do
  time curl -s http://localhost:8000/health > /dev/null
done
```

### SC-004: Concurrent Requests (100)

```bash
# Using Apache Benchmark
ab -n 100 -c 100 http://localhost:8000/health

# Or using hey
hey -n 100 -c 100 http://localhost:8000/health
```

## Troubleshooting

### Gateway won't start

1. Check environment variables are set
2. Verify Python 3.11+ is installed
3. Run `uv sync` to ensure dependencies

### 503 errors for all requests

1. Check backend services are running
2. Verify SERVICE1_URL and SERVICE2_URL are correct
3. Check Docker network connectivity

### Timeout errors

1. Increase GATEWAY_TIMEOUT value
2. Check backend service performance
3. Verify network connectivity

## Next Steps

After verifying all scenarios:

1. Run `/speckit.tasks` to generate implementation tasks
2. Follow task list to implement the gateway
3. Run integration tests
4. Update docker-compose.yml with gateway service
