# Tasks: External workspace
## Phase 1: Setup and design
- [x] T001 Resolve official templates, preserve originals and define spec/plan in specs/002-external-workspace/ (FR-001, FR-005).
- [x] T002 Analyze precedence, backwards compatibility and requirement coverage before code (FR-002–FR-007).
## Phase 2: User Story 1
- [x] T003 [US1] Add environment/default output resolution in pipeline/common.py, diagnose_runtime.py, cut_media.py (FR-002–FR-004).
- [x] T004 [US1] Add functional path regression cases in tests/test_output_paths.py (FR-001–FR-004).
## Phase 3: User Story 2
- [x] T005 [US2] Configure external session launcher and durable media mapping, no junction/profile changes (FR-001, FR-005).
- [x] T006 [US2] Run hardware inventory, short null decodes and source preservation checks externally (FR-006).
- [x] T007 [US2] Update docs/local-workspace.md and runtime/media skill routing (FR-005, FR-007).
## Phase 4: Verify and deliver
- [x] T008 Remove only this operation's known temporary files, validate and assess convergence (FR-007).
- [x] T009 Publish draft PR, check CI and request Copilot review; no merge (SC-003).
- [x] T010 Address Copilot source-directory/output protection findings with regression coverage (FR-001–FR-004). Final review outcome is recorded in the PR.

T001–T002 precede code; tests/setup follow implementation; delivery follows local checks. FR coverage: 001→003/004/005, 002–004→003/004, 005→005/007, 006→006, 007→007/008. Owner approval is outside delivery.
