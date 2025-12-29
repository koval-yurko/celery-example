# Research: SonarQube GitHub Pipeline Integration

**Feature**: 004-sonarqube-pipeline
**Date**: 2025-12-29

## Research Topics

### 1. SonarQube vs SonarCloud for GitHub Integration

**Decision**: SonarCloud (SonarQube Cloud service)

**Rationale**:
- SonarCloud is the cloud-hosted version designed specifically for CI/CD integration
- Native GitHub integration with automatic PR decoration
- No server setup or maintenance required
- Free tier available for public repositories
- Official GitHub Action available: `SonarSource/sonarcloud-github-action`

**Alternatives Considered**:
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Self-hosted SonarQube | Full control, on-premise | Requires infrastructure, maintenance | Adds operational complexity |
| SonarCloud | Zero maintenance, GitHub native | External dependency | Selected - best fit for GitHub workflow |

### 2. GitHub Actions Workflow Pattern

**Decision**: Use `SonarSource/sonarcloud-github-action` with pull_request trigger

**Rationale**:
- Official action maintained by SonarSource
- Handles scanner installation, configuration, and execution
- Automatic quality gate status reporting to GitHub
- Supports PR analysis with changed files only (incremental)

**Workflow Trigger Pattern**:
```yaml
on:
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]
```

**Alternatives Considered**:
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| sonar-scanner CLI directly | More control | Manual setup, more YAML | Unnecessary complexity |
| SonarSource official action | Simple, maintained | Less customization | Selected - matches Simplicity First principle |
| Third-party actions | Various features | Maintenance risk | Official action is better supported |

### 3. Python Project Configuration

**Decision**: Use `sonar-project.properties` file in repository root

**Rationale**:
- Standard SonarQube configuration approach
- Version controlled with the code
- Easy to maintain and review

**Key Configuration Properties**:
```properties
sonar.projectKey=celery-example
sonar.organization=<org-key>
sonar.sources=.
sonar.python.version=3.11
sonar.exclusions=**/__pycache__/**,**/.venv/**,**/tests/**
sonar.tests=**/tests/**
sonar.python.coverage.reportPaths=coverage.xml
```

### 4. Quality Gate Configuration

**Decision**: Use SonarCloud default quality gate with customization in SonarCloud UI

**Rationale**:
- Quality gate thresholds should be managed in SonarCloud, not in code
- Allows non-developers to adjust thresholds
- Spec states "quality gates are pre-configured in the SonarQube instance"

**Default Quality Gate Conditions**:
- No new bugs
- No new vulnerabilities
- No new security hotspots reviewed as "safe"
- No new code smells
- Code coverage on new code ≥ 80% (adjustable)
- Duplication on new code < 3%

### 5. Secrets Management

**Decision**: Use GitHub repository secrets for SonarCloud token

**Required Secrets**:
| Secret Name | Description | Where to Create |
|-------------|-------------|-----------------|
| `SONAR_TOKEN` | SonarCloud authentication token | SonarCloud → My Account → Security |

**Rationale**:
- GitHub secrets are secure and automatically masked in logs
- Standard practice for CI/CD authentication
- Organization-level secrets can be shared across repos

### 6. PR Decoration and Check Status

**Decision**: Enable automatic PR decoration via SonarCloud GitHub App

**Rationale**:
- SonarCloud GitHub App provides native PR comments with issue summary
- Check status appears automatically when using official action
- Link to SonarCloud dashboard included in check details

**Setup Requirements**:
1. Install SonarCloud GitHub App on repository
2. Connect repository in SonarCloud
3. Configure workflow with proper token

### 7. Incremental Analysis (PR-only changes)

**Decision**: Use SonarCloud's automatic PR analysis mode

**Rationale**:
- SonarCloud automatically detects PR context from GitHub Actions
- Analyzes only new/changed code in the PR
- Reports new issues vs. overall project status separately

**Implementation**:
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}  # Needed for PR decoration
  SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

### 8. Dependency Management in CI/CD

**Decision**: Use `uv` for dependency installation in GitHub Actions workflow

**Rationale**:
- Project constitution mandates `uv` as the standard dependency management tool
- `uv` is significantly faster than pip for dependency resolution and installation
- Consistent with local development workflow
- Supports monorepo workspace configuration

**Implementation**:
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v4

- name: Install dependencies
  run: |
    uv sync --all-packages
```

**Alternatives Considered**:
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| pip install | Universal, simple | Slow, no lockfile support | Constitution requires uv |
| poetry | Good dependency management | Slower than uv, different from local | Constitution requires uv |
| uv | Fast, lockfile support, constitution compliant | Newer tool | Selected - per constitution |

### 9. Monorepo Test Coverage Collection

**Decision**: Use pytest-cov with multiple `--cov` flags to collect coverage from all package source directories

**Rationale**:
- This is a Python monorepo with multiple packages: common, api-gateway, example-service-1, example-service-2, worker
- Each package has its own `src/` directory with source code
- Coverage must aggregate across all packages for accurate SonarCloud reporting
- Single coverage.xml file required by SonarCloud

**Implementation**:
```yaml
- name: Run tests with coverage
  run: |
    uv run pytest \
      --cov=common/src \
      --cov=api-gateway/src \
      --cov=example-service-1/src \
      --cov=example-service-2/src \
      --cov=worker/src \
      --cov-report=xml:coverage.xml \
      --cov-report=term-missing
```

**SonarCloud Configuration**:
```properties
# Source directories for monorepo
sonar.sources=common/src,api-gateway/src,example-service-1/src,example-service-2/src,worker/src

# Test directories
sonar.tests=common/tests,api-gateway/tests,example-service-1/tests,example-service-2/tests,worker/tests

# Coverage report
sonar.python.coverage.reportPaths=coverage.xml
```

**Alternatives Considered**:
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Single --cov=. | Simple | Includes non-source dirs, slower | Inefficient, includes venv |
| coverage.py combine | Full control | Complex setup, extra steps | Unnecessary complexity |
| Multiple --cov flags | Precise, fast | More verbose | Selected - exact source targeting |

### 10. Error Handling Strategy

**Decision**: Use `continue-on-error: false` with clear failure messages

**Rationale**:
- Failed analysis should block PR (quality gate purpose)
- GitHub Actions provides automatic retry capability
- SonarCloud handles transient failures with retries internally

**Error Scenarios**:
| Scenario | Handling |
|----------|----------|
| SonarCloud unavailable | Workflow fails with clear error message |
| Invalid token | Workflow fails with authentication error |
| Analysis timeout | Workflow fails after GitHub Actions timeout |
| Quality gate fails | Check marked as failed, PR blocked |

## Summary of Decisions

| Topic | Decision |
|-------|----------|
| Platform | SonarCloud (cloud service) |
| GitHub Action | `SonarSource/sonarcloud-github-action@v3` |
| Configuration | `sonar-project.properties` in repo root |
| Quality Gates | Managed in SonarCloud UI |
| Secrets | GitHub repository secrets (`SONAR_TOKEN`) |
| PR Decoration | SonarCloud GitHub App |
| Dependency Management | `uv` via `astral-sh/setup-uv@v4` action |
| Monorepo Coverage | Multiple `--cov` flags for each package src/ |
| Error Handling | Fail workflow on any error |

## Prerequisites Checklist

Before implementation:
- [ ] Create SonarCloud account and organization
- [ ] Install SonarCloud GitHub App on repository
- [ ] Create project in SonarCloud linked to GitHub repo
- [ ] Generate SONAR_TOKEN and add to GitHub secrets
- [ ] Configure quality gate in SonarCloud (optional - default works)
