# Tasks: SonarQube GitHub Pipeline Check

**Input**: Design documents from `/specs/004-sonarqube-pipeline/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in spec - test tasks omitted.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- GitHub workflow: `.github/workflows/`
- Configuration: Repository root
- Documentation: `specs/004-sonarqube-pipeline/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: SonarCloud account and repository configuration

- [ ] T001 Create SonarCloud account and organization (manual step in SonarCloud UI) ⚠️ MANUAL
- [ ] T002 Install SonarCloud GitHub App on repository (manual step in GitHub) ⚠️ MANUAL
- [ ] T003 Create project in SonarCloud linked to celery-example repository (manual step) ⚠️ MANUAL
- [ ] T004 Generate SONAR_TOKEN in SonarCloud (My Account → Security) ⚠️ MANUAL
- [ ] T005 Add SONAR_TOKEN as GitHub repository secret in Settings → Secrets → Actions ⚠️ MANUAL

**Checkpoint**: SonarCloud prerequisites complete - configuration files can now be created

---

## Phase 2: Foundational (Configuration Files)

**Purpose**: Create configuration files that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until these files are in place

- [X] T006 [P] Create sonar-project.properties in repository root from contracts/sonar-project.properties
- [X] T007 [P] Create .github/workflows/sonarqube.yml from contracts/sonarqube-workflow.yml
- [ ] T008 Update sonar.organization value in sonar-project.properties with actual organization key ⚠️ MANUAL

**Checkpoint**: Foundation ready - pipeline will trigger on next PR

---

## Phase 3: User Story 1 - Automated Code Quality Check on PR (Priority: P1) 🎯 MVP

**Goal**: Code quality checks run automatically when PRs are opened or updated

**Independent Test**: Open a PR and verify SonarCloud analysis runs automatically

### Implementation for User Story 1

- [X] T009 [US1] Verify workflow triggers on pull_request events in .github/workflows/sonarqube.yml
- [X] T010 [US1] Verify workflow triggers on push to main branch in .github/workflows/sonarqube.yml
- [X] T011 [US1] Ensure checkout step uses fetch-depth: 0 for full history in .github/workflows/sonarqube.yml
- [X] T012 [US1] Verify Python setup step uses correct version (3.11) in .github/workflows/sonarqube.yml
- [X] T013 [US1] Verify SonarCloud action uses latest version (v3) in .github/workflows/sonarqube.yml
- [X] T014 [US1] Verify GITHUB_TOKEN and SONAR_TOKEN environment variables are configured in .github/workflows/sonarqube.yml
- [ ] T015 [US1] Test by creating a test PR and verifying analysis runs ⚠️ MANUAL

**Checkpoint**: User Story 1 complete - PRs automatically trigger SonarCloud analysis

---

## Phase 4: User Story 2 - Quality Gate Status Visibility (Priority: P1)

**Goal**: Quality gate status visible directly in GitHub PR interface

**Independent Test**: View a PR after analysis and confirm pass/fail status in checks section

### Implementation for User Story 2

- [ ] T016 [US2] Verify SonarCloud GitHub App provides PR decoration (automatic with app installed)
- [ ] T017 [US2] Verify check status appears in GitHub PR checks section after analysis
- [ ] T018 [US2] Verify clicking check details links to SonarCloud dashboard
- [ ] T019 [US2] Test with a PR containing code quality issues to verify failure status displays

**Checkpoint**: User Story 2 complete - Quality gate status visible in all PRs

---

## Phase 5: User Story 3 - Branch Protection Integration (Priority: P2)

**Goal**: SonarQube check enforceable via branch protection rules

**Independent Test**: Configure branch protection and verify merge blocked when quality gate fails

### Implementation for User Story 3

- [ ] T020 [US3] Navigate to GitHub repository Settings → Branches
- [ ] T021 [US3] Add or edit branch protection rule for main branch
- [ ] T022 [US3] Enable "Require status checks to pass before merging"
- [ ] T023 [US3] Search and select "SonarCloud Analysis" as required check
- [ ] T024 [US3] Test by attempting to merge PR with failing quality gate (merge should be blocked)
- [ ] T025 [US3] Test by merging PR with passing quality gate (merge should succeed)

**Checkpoint**: User Story 3 complete - Branch protection enforces quality gates

---

## Phase 6: User Story 4 - Manual Analysis Trigger (Priority: P3)

**Goal**: Developers can manually re-run SonarCloud analysis

**Independent Test**: Click re-run on completed check and verify analysis executes again

### Implementation for User Story 4

- [ ] T026 [US4] Verify GitHub Actions "Re-run" button is available on completed checks (automatic)
- [ ] T027 [US4] Test manual re-run by clicking "Re-run jobs" on a completed analysis
- [ ] T028 [US4] Verify analysis runs again without requiring new commits

**Checkpoint**: User Story 4 complete - Manual re-run available for all checks

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation

- [ ] T029 [P] Update quickstart.md with actual SonarCloud organization and project keys in specs/004-sonarqube-pipeline/quickstart.md
- [ ] T030 [P] Document any project-specific exclusions needed in sonar-project.properties
- [ ] T031 Run full validation using quickstart.md verification checklist
- [ ] T032 Verify analysis completes within 10-minute target (FR-006)
- [ ] T033 Test error handling by simulating SonarCloud unavailability (FR-007)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - start immediately (manual SonarCloud setup)
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 can proceed in parallel (both P1)
  - US3 depends on US1/US2 (needs working check for branch protection)
  - US4 depends on US1 (needs working check to re-run)
- **Polish (Phase 7)**: Depends on all user stories complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires US1 to be complete to verify
- **User Story 3 (P2)**: Requires US1/US2 complete (needs working check to protect against)
- **User Story 4 (P3)**: Requires US1 complete (needs working check to re-run)

### Parallel Opportunities

- T006 and T007 can run in parallel (different files)
- T029 and T030 can run in parallel (different sections)
- US1 and US2 can be validated in parallel once pipeline runs

---

## Parallel Example: Foundational Phase

```bash
# Launch both configuration file tasks together:
Task: "Create sonar-project.properties in repository root"
Task: "Create .github/workflows/sonarqube.yml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (SonarCloud account, token, secrets)
2. Complete Phase 2: Foundational (configuration files)
3. Complete Phase 3: User Story 1 (automated analysis on PR)
4. **STOP and VALIDATE**: Open test PR and verify analysis runs
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Pipeline configured
2. Add User Story 1 → Test independently → PRs trigger analysis (MVP!)
3. Add User Story 2 → Test independently → Status visible in PRs
4. Add User Story 3 → Test independently → Branch protection enforced
5. Add User Story 4 → Test independently → Manual re-run available
6. Each story adds value without breaking previous stories

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**

This delivers the core value: automated code quality analysis on every PR.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Most tasks in this feature are configuration/verification rather than code
- Manual steps (T001-T005) require SonarCloud UI access
- T020-T023 require GitHub repository admin access
- Commit workflow and properties files after Phase 2
- Stop at any checkpoint to validate story independently
