# Tasks: Керований процес змін

Input: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md).

## Phase 1: Setup

- [x] T001 Install and verify specify-cli 1.3.2 in local/tools/spec-kit/; record in requirements-tools.txt (FR-005).
- [x] T002 Preserve baseline hashes and initialize .specify/ plus Codex skills with py scripts/events=false (FR-007).

## Phase 2: Foundation

- [x] T003 Amend .specify/memory/constitution.md and create specs/001-project-workflow/spec.md with built-in quality checklist (FR-003, FR-004).
- [x] T004 Complete specs/001-project-workflow/plan.md and design artifacts, resolve compatibility assumptions (FR-004, FR-006).
- [x] T005 Analyze spec/plan/tasks coverage before implementation; report author checks and limits in specs/001-project-workflow/quickstart.md (FR-004, SC-002).

## Phase 3: User Story 1 — Review before acceptance

Goal: owner can inspect a bounded change before acceptance.
Independent test: draft PR has purpose/scope/sources/checks/open questions/spec link; main unchanged.

- [x] T006 [US1] Write CONTRIBUTING.md with branch, draft, approval, stale-head and editorial-change rules (FR-001, FR-003, FR-010).
- [x] T007 [US1] Add .github/PULL_REQUEST_TEMPLATE.md covering required review context (FR-002).
- [x] T008 [US1] Add .github/workflows/validate.yml invoking existing pipeline/validate.py without media dependencies (FR-011).
- [x] T009 [US1] Align AGENTS.md, docs/workflow.md and specs/README.md with installed process and approval boundary (FR-001, FR-004, FR-010).

## Phase 4: User Story 2 — Repeatable agent workflow

Goal: a subsequent agent can find installed instructions and knows actual support limits.
Independent test: version/template/prerequisite commands work; compatible invocation is documented without personal paths.

- [x] T010 [US2] Pin requirements-tools.txt and complete docs/codex-speckit.md with setup and capability matrix (FR-005, FR-006).
- [x] T011 [US2] Verify generated portable invocations, upstream .specify/NOTICE.md and preservation of existing domain files (FR-007).
- [x] T012 [US2] Execute template/prerequisite checks and validator; record exit codes and limitations in specs/001-project-workflow/quickstart.md (FR-005, FR-006, FR-011).

## Phase 5: User Story 3 — Attributed model review

Goal: findings have provenance and disposition, not simulated consensus.
Independent test: review template can capture reviewer/model, head, question, evidence, finding and disposition; unused review is not claimed.

- [x] T013 [US3] Add templates/model-review.md and its usage rules in CONTRIBUTING.md (FR-008, FR-009).

## Phase 6: Polish and delivery

- [x] T014 Run convergence against current tasks and document gaps without self-approving owner review in specs/001-project-workflow/quickstart.md (FR-004, FR-012).
- [ ] T015 Commit/push only 001-project-workflow and open draft PR linked to specs/001-project-workflow/spec.md (FR-001, FR-002, FR-012).
- [ ] T016 Observe PR validation and verify main remains at baseline; report actual results in specs/001-project-workflow/quickstart.md (FR-011, FR-012, SC-003, SC-004).

## Dependencies and delivery

T001–T004 precede T005; T005 precedes implementation T006–T013. T014 follows local implementation and checks; T015 follows convergence; T016 observes remote delivery. US3 can be implemented after foundation independently of US1/US2, but no parallel agent execution is required. Within each story tasks are sequential to avoid overlapping documentation edits. MVP is US1, then compatibility support US2 and optional review mechanism US3. Owner approval and merge are deliberately outside this change's completion tasks.

## Requirement coverage

| Requirement | Tasks |
|---|---|
| FR-001 | T006, T009, T015 |
| FR-002 | T007, T015 |
| FR-003 | T003, T006 |
| FR-004 | T003, T004, T005, T009, T014 |
| FR-005 | T001, T010, T012 |
| FR-006 | T004, T010, T012 |
| FR-007 | T002, T011 |
| FR-008 | T013 |
| FR-009 | T013 |
| FR-010 | T006, T009 |
| FR-011 | T008, T012, T016 |
| FR-012 | T014, T015, T016 |


## Phase 7: Convergence

Initial author convergence found two remaining evidence gaps in quickstart.md; implementation files otherwise satisfy the reviewed design. Delivery is still pending T015–T016.

- [ ] T017 Record the actual draft PR URL and branch in specs/001-project-workflow/quickstart.md per FR-012 (partial).
- [ ] T018 Record the observed remote validation result and main-baseline check in specs/001-project-workflow/quickstart.md per FR-011, SC-003 (partial).
