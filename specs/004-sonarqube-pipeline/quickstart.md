# Quickstart: SonarQube GitHub Pipeline Check

**Feature**: 004-sonarqube-pipeline
**Date**: 2025-12-29

## Prerequisites

Before implementing this feature, complete the following setup:

### 1. SonarCloud Account Setup

1. Go to [SonarCloud](https://sonarcloud.io) and sign in with your GitHub account
2. Create or select an organization
3. Note your **organization key** (found in Organization Settings)

### 2. Create SonarCloud Project

1. In SonarCloud, click "+" → "Analyze new project"
2. Select `celery-example` repository from the list
3. Choose "With GitHub Actions" as the analysis method
4. Note the **project key** (usually `<org>_<repo-name>`)

### 3. Generate SonarCloud Token

1. Go to SonarCloud → My Account → Security
2. Generate a new token with a descriptive name (e.g., "celery-example-github-actions")
3. Copy the token (you won't see it again)

### 4. Add GitHub Secret

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SONAR_TOKEN`
4. Value: Paste the token from step 3
5. Click "Add secret"

## Implementation Steps

### Step 1: Create Workflow File

Copy the workflow from `specs/004-sonarqube-pipeline/contracts/sonarqube-workflow.yml` to `.github/workflows/sonarqube.yml`

### Step 2: Create Properties File

Copy `specs/004-sonarqube-pipeline/contracts/sonar-project.properties` to repository root as `sonar-project.properties`

**Important**: Update `sonar.organization` with your actual organization key

### Step 3: Enable Branch Protection (Optional)

1. Go to GitHub repository → Settings → Branches
2. Add or edit branch protection rule for `main`
3. Enable "Require status checks to pass before merging"
4. Search and select "SonarCloud Analysis"

## Verification

### Test the Pipeline

1. Create a new branch: `git checkout -b test-sonarcloud`
2. Make a small change to any Python file
3. Push and create a PR: `git push -u origin test-sonarcloud`
4. Observe the SonarCloud check running in the PR

### Expected Results

- GitHub Actions workflow triggers automatically
- SonarCloud analysis runs (visible in Actions tab)
- Check status appears in PR (pass/fail)
- Clicking "Details" links to SonarCloud dashboard

### Troubleshooting

| Issue | Solution |
|-------|----------|
| "Token not found" error | Verify `SONAR_TOKEN` secret is set correctly |
| "Project not found" error | Ensure `sonar.projectKey` matches SonarCloud project |
| Analysis runs but no results | Check `sonar.sources` path is correct |
| PR decoration not showing | Verify SonarCloud GitHub App is installed |

## File Checklist

After implementation, verify these files exist:

- [ ] `.github/workflows/sonarqube.yml` - GitHub Actions workflow
- [ ] `sonar-project.properties` - SonarCloud configuration
- [ ] GitHub Secret: `SONAR_TOKEN` - Authentication token

## Next Steps

After successful verification:

1. Run `/speckit.tasks` to generate implementation tasks
2. Follow the tasks to complete the implementation
3. Test with a real PR containing code quality issues
