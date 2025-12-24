# celery-example

A Python project for working with Celery, managed with [uv](https://github.com/astral-sh/uv).

## Prerequisites

- [uv](https://github.com/astral-sh/uv) package manager installed
- Python 3.13 or higher
- [Docker](https://www.docker.com/get-started) and Docker Compose (for running Redis)

## Running Redis with Docker

This project uses Redis as a message broker for Celery. A Docker Compose configuration is provided for easy local development.

## Quick Start

### 1. Start Redis
```bash
docker-compose up -d
```

### 2. Start Celery Worker (in one terminal)
```bash
uv run celery-worker
```

### 3. Run the Example (in another terminal)
```bash
uv run celery-example
```

## Working with uv

### Managing Dependencies

Add a new dependency:
```bash
uv add package-name
```

Add a development dependency:
```bash
uv add --dev package-name
```

Remove a dependency:
```bash
uv remove package-name
```

Update dependencies:
```bash
uv lock --upgrade
```

### Installing Dependencies

Install all project dependencies:
```bash
uv sync
```

### Virtual Environment

uv automatically manages virtual environments, but if you need to activate it manually:

```bash
# Create/sync the environment
uv sync

# Activate the virtual environment
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate     # On Windows
```

### Other Useful Commands

Check installed packages:
```bash
uv pip list
```

Show project information:
```bash
uv tree
```

### Running Tests

Add a testing framework:
```bash
uv add --dev pytest
```

Run tests:
```bash
uv run pytest
```
