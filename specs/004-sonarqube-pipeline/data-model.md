# Data Model: SonarQube GitHub Pipeline

**Feature**: 004-sonarqube-pipeline
**Date**: 2025-12-29

## Overview

This feature involves configuration files rather than traditional data entities. The "data model" describes the structure of configuration files and their relationships.

## Configuration Entities

### 1. GitHub Actions Workflow (`sonarqube.yml`)

**Location**: `.github/workflows/sonarqube.yml`

**Schema**:
```yaml
name: string              # Workflow display name
on:                       # Trigger configuration
  pull_request:
    types: [opened, synchronize, reopened]
  push:
    branches: [main]

jobs:
  sonarcloud:
    name: string          # Job display name
    runs-on: string       # Runner type (ubuntu-latest)
    steps:
      - uses: string      # Action reference
        with:             # Action inputs
          key: value
        env:              # Environment variables
          key: value
```

**Required Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `name` | string | "SonarCloud Analysis" |
| `on.pull_request.types` | array | `[opened, synchronize, reopened]` |
| `jobs.sonarcloud.runs-on` | string | `ubuntu-latest` |
| `steps[].uses` | string | Action references |

### 2. SonarQube Project Properties (`sonar-project.properties`)

**Location**: Repository root

**Schema**:
```properties
# Required
sonar.projectKey=string           # Unique project identifier
sonar.organization=string         # SonarCloud organization key

# Source Configuration
sonar.sources=string              # Source directories (comma-separated)
sonar.exclusions=string           # Glob patterns to exclude

# Python-specific
sonar.python.version=string       # Python version (3.11)

# Test Configuration
sonar.tests=string                # Test directories
sonar.python.coverage.reportPaths=string  # Coverage report location

# Optional
sonar.projectName=string          # Display name in SonarCloud
sonar.sourceEncoding=string       # File encoding (UTF-8)
```

**Required Fields**:
| Field | Type | Description |
|-------|------|-------------|
| `sonar.projectKey` | string | Must match SonarCloud project |
| `sonar.organization` | string | SonarCloud org key |
| `sonar.sources` | string | Directories to analyze |

### 3. GitHub Secrets

**Location**: Repository Settings → Secrets and variables → Actions

**Required Secrets**:
| Name | Description | Source |
|------|-------------|--------|
| `SONAR_TOKEN` | SonarCloud authentication token | SonarCloud → My Account → Security |

**Note**: `GITHUB_TOKEN` is automatically provided by GitHub Actions.

## Relationships

```
┌─────────────────────────────┐
│   GitHub Repository         │
├─────────────────────────────┤
│ .github/workflows/          │
│   └── sonarqube.yml ───────┼──► Triggers on PR/push
│                             │
│ sonar-project.properties ──┼──► Configures analysis scope
│                             │
│ Settings/Secrets            │
│   └── SONAR_TOKEN ─────────┼──► Authenticates to SonarCloud
└─────────────────────────────┘
            │
            ▼
┌─────────────────────────────┐
│   SonarCloud                │
├─────────────────────────────┤
│ Organization                │
│   └── Project ─────────────┼──► Stores analysis results
│       └── Quality Gate ────┼──► Defines pass/fail criteria
└─────────────────────────────┘
            │
            ▼
┌─────────────────────────────┐
│   GitHub PR                 │
├─────────────────────────────┤
│ Check Status ──────────────┼──► Shows pass/fail
│ PR Decoration ─────────────┼──► Shows issue summary
│ Details Link ──────────────┼──► Links to SonarCloud
└─────────────────────────────┘
```

## State Transitions

### Workflow Execution States

```
[PR Opened/Updated]
        │
        ▼
   [Triggered]
        │
        ▼
  [Checkout Code]
        │
        ▼
 [Run SonarCloud Scanner]
        │
        ├──► [Success] ──► [Quality Gate Check]
        │                       │
        │                       ├──► [Passed] ──► ✅ Check Success
        │                       │
        │                       └──► [Failed] ──► ❌ Check Failed
        │
        └──► [Error] ──► ❌ Check Failed (with error message)
```

## Validation Rules

### sonar-project.properties

1. `sonar.projectKey` MUST match the project key in SonarCloud
2. `sonar.organization` MUST match the SonarCloud organization
3. `sonar.sources` MUST point to existing directories
4. `sonar.exclusions` SHOULD exclude non-source files (venv, cache, etc.)

### GitHub Workflow

1. Workflow MUST trigger on `pull_request` events
2. Workflow MUST include `GITHUB_TOKEN` for PR decoration
3. Workflow MUST include `SONAR_TOKEN` for authentication
4. Workflow SHOULD use latest version of SonarCloud action
