# Implementation Plan: SonarQube GitHub Pipeline Check

**Branch**: `004-sonarqube-pipeline` | **Date**: 2025-12-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-sonarqube-pipeline/spec.md`

## Summary

Add automated SonarQube code quality analysis to the GitHub CI/CD pipeline. The implementation creates a GitHub Actions workflow that triggers SonarQube analysis on every pull request, reports results as GitHub check status, and integrates with branch protection rules to enforce quality gates.

## Technical Context

**Language/Version**: YAML (GitHub Actions), Python 3.11+ (project being analyzed)
**Primary Dependencies**: GitHub Actions, SonarQube Scanner, sonar-scanner-cli
**Storage**: N/A (stateless CI/CD pipeline)
**Testing**: Manual PR testing, workflow validation via act (optional)
**Target Platform**: GitHub Actions runners (ubuntu-latest)
**Project Type**: CI/CD configuration
**Performance Goals**: Analysis completes within 10 minutes for typical PRs
**Constraints**: Requires SonarQube server/cloud accessible from GitHub Actions
**Scale/Scope**: Single repository, Python microservices codebase

**Dependency Management**: This project uses `uv` as the standard tool for dependency management. The GitHub Actions workflow MUST use `uv` for installing project dependencies instead of pip.

**Monorepo Structure**: This is a monorepo with multiple Python packages (common, api-gateway, example-service-1, example-service-2, worker). Test coverage collection MUST aggregate coverage from all packages intelligently using pytest-cov's `--cov` flag for each package source directory.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance | Notes |
|-----------|------------|-------|
| I. Microservices Architecture | ✅ N/A | CI/CD pipeline, not a microservice |
| II. Task Idempotency & Reliability | ✅ N/A | GitHub Actions handles idempotency |
| III. Monitoring & Observability | ✅ PASS | SonarQube provides comprehensive code quality metrics and reports |
| IV. Error Handling & Resilience | ✅ PASS | Workflow includes graceful error handling for SonarQube unavailability |
| V. Simplicity First | ✅ PASS | Uses standard GitHub Actions + SonarQube scanner - minimal complexity |
| Dependency Management | ✅ PASS | Workflow uses `uv` for dependency installation per constitution |

**Gate Status**: PASS - No violations. Proceeding to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-sonarqube-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output - SonarQube integration patterns
├── data-model.md        # Phase 1 output - Workflow configuration schema
├── quickstart.md        # Phase 1 output - Setup and verification guide
├── contracts/           # Phase 1 output - Workflow definitions
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
# Monorepo structure
.github/
└── workflows/
    └── sonarqube.yml    # SonarQube analysis workflow

sonar-project.properties # SonarQube project configuration (root)

# Python packages (coverage sources)
common/src/              # Shared utilities
api-gateway/src/         # API gateway service
example-service-1/src/   # Example service 1
example-service-2/src/   # Example service 2
worker/src/              # Celery worker
```

**Structure Decision**: CI/CD configuration stored in standard `.github/workflows/` directory. SonarQube configuration in repository root. Coverage collection must span all package `src/` directories in the monorepo.

## Complexity Tracking

No complexity violations to document. Implementation uses standard GitHub Actions patterns and official SonarQube scanner.
