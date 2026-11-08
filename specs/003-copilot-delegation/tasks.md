# Tasks: Copilot delegation

Input: spec.md, plan.md, research.md, data-model.md, quickstart.md.

## Phase 1: Setup
- [x] T001 Resolve official templates and define requirements in specs/003-copilot-delegation/spec.md and checklists/requirements.md.
- [x] T002 Define plan/research/data-model/quickstart in specs/003-copilot-delegation/ and check requirement coverage before implementation (FR-001–FR-007).

## Phase 2: User Story 1 — Optional selection
- [x] T003 [US1] Write selection/authorization rules in .agents/skills/copilot-delegation/SKILL.md and implicit UI metadata in agents/openai.yaml (FR-001–FR-002).
- [x] T004 [US1] Link optional selection from AGENTS.md and CONTRIBUTING.md (FR-001–FR-002).

## Phase 3: User Story 2 — Execution and acceptance
- [x] T005 [US2] Complete task handoff, execution, permissions, storage and acceptance in .agents/skills/copilot-delegation/SKILL.md (FR-003–FR-007).
- [x] T006 [US2] Exercise manual scenarios and skill/project validators; record actual results in specs/003-copilot-delegation/quickstart.md (SC-001–SC-002).

## Phase 4: Delivery
- [x] T007 Assess convergence against spec/plan/tasks and tracked scope; record evidence in specs/003-copilot-delegation/quickstart.md (FR-001–FR-007).
- [x] T008 Publish draft PR, check CI and request Copilot review; wait for response and address findings, record outcome in PR (SC-003). Докази PR №4 на перевіреному SHA наведені в quickstart.md; позначку узгоджено після фактичного злиття.

Dependencies: T001→T002→T003→T004→T005→T006→T007→T008. MVP is US1; US2 extends the same skill, so edits are sequential. After T003, AGENTS.md and CONTRIBUTING.md references can be edited independently; no extra agents are needed. No implementation tests are added for a documentation-only change.
