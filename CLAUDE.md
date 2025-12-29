# celery-example Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-12-25

## Active Technologies
- Redis (message broker and result backend) (001-microservices-structure)
- Python 3.11+ (consistent with existing services) + FastAPI 0.100+, httpx 0.25+ (async HTTP client), uvicorn 0.23+ (002-api-gateway)
- N/A (stateless proxy, no persistence required) (002-api-gateway)
- YAML (GitHub Actions), Python 3.11+ (project being analyzed) + GitHub Actions, SonarQube Scanner, sonar-scanner-cli (004-sonarqube-pipeline)
- N/A (stateless CI/CD pipeline) (004-sonarqube-pipeline)

- Python 3.11+ + Celery 5.3+, Redis 7.0+, Docker 24.0+, Docker Compose 2.20+ (001-microservices-structure)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 004-sonarqube-pipeline: Added YAML (GitHub Actions), Python 3.11+ (project being analyzed) + GitHub Actions, SonarQube Scanner, sonar-scanner-cli
- 004-sonarqube-pipeline: Added YAML (GitHub Actions), Python 3.11+ (project being analyzed) + GitHub Actions, SonarQube Scanner, sonar-scanner-cli
- 002-api-gateway: Added Python 3.11+ (consistent with existing services) + FastAPI 0.100+, httpx 0.25+ (async HTTP client), uvicorn 0.23+


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
