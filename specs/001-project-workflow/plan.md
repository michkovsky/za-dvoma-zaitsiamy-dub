# Implementation Plan: Керований процес змін

**Branch**: `001-project-workflow` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from specs/001-project-workflow/spec.md.

## Summary

Установити справжній Spec Kit 1.3.2 з Codex skills і Python-скриптами, зберігши наявні матеріали. Запровадити PR-процес документами, шаблоном і легкою перевіркою таблиць. Провести цю зміну через той самий процес. Не змінювати матеріали перекладу й не зливати PR.

## Technical Context

**Language/Version**: Markdown, CSV, Python 3.11+ для Spec Kit; наявний validator працює на 3.10+.

**Primary Dependencies**: specify-cli==1.3.2 в local/tools/spec-kit; Git; gh; GitHub Actions для validator. Жодних залежностей озвучення для CI.

**Storage**: Versioned text; ignored local/ for environment, logs and evidence. Spec Kit local feature pointer remains ignored.

**Testing**: CLI version/check, official template resolver and prerequisite scripts, project validator, domain baseline hashes, staged diff, draft PR/CI observation.

**Target Platform**: Windows locally; Linux runner for dependency-free text validation. Automatic skill discovery in a fresh Codex session is explicitly not claimed as tested.

**Project Type**: Existing research/dubbing repository with CLI helpers and project documentation.

**Performance Goals**: No full movie decoding or model inference; CI checks only text.

**Constraints**: No direct main push; owner merge approval; no secrets or machine-specific paths in generated skills; retain existing domain files. Codex events disabled, no nested codex exec. No branch protection or paid service changes.

**Scale/Scope**: One feature, three stories, 12 requirements; nine upstream skills plus four existing domain skills.

## Constitution Check

Before research: PASS. I–II: original evidence and common/multilingual data unchanged. III: Markdown/CSV retained, tool dependency isolated. IV: no ML install; CLI gets real startup/resolver checks. V: accepted pilot unchanged. VI: version and verification recorded. VII: current branch, draft PR, no merge.

After design: PASS with explicit limits: owner approval pending; automatic session discovery and nested workflow dispatch unverified. Independent review not performed. These limits remain visible rather than converted to successful checks.

## Project Structure

### Documentation (this feature)

spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md and built-in checklists/requirements.md. No API contracts: this is an internal contribution workflow.

### Source Code (repository root)

```text
.specify/                       # upstream templates/scripts/workflow, updated constitution
.agents/skills/speckit-*/        # upstream Codex integration
.github/PULL_REQUEST_TEMPLATE.md
.github/workflows/validate.yml
CONTRIBUTING.md
AGENTS.md
requirements-tools.txt
docs/codex-speckit.md
pipeline/validate.py             # existing check, behavior preserved
```

**Structure Decision**: Use official scaffold and existing validator, not a custom orchestration engine. Preserve upstream MIT notice. Generated invocations use python on activated environment PATH, not a personal absolute path.

## Phases

0. Research current CLI and Codex compatibility, resolve installation mode and review authority.
1. Define change/review lifecycle and reproducible setup; check requirements quality.
2. Generate tasks and perform author consistency analysis before workflow implementation.
3. Implement contribution rules, PR template and light CI; record actual verification.
4. Check convergence, publish branch/draft PR, observe CI. Owner review/merge stays pending.

## Complexity Tracking

No constitution exception. Nine upstream skills and CLI dependencies are required by the adopted framework; no community extension or additional model service is installed. Branch creation and PR publishing use existing Git/gh rather than extra Spec Kit extensions.


## Review-driven correction

До FR-006 додано три сценарії безпеки контексту. Мінімальний стандартнобібліотечний pipeline/speckit_readonly.py задає SPECIFY_FEATURE_NO_PERSIST=1 лише дочірньому процесу й делегує upstream checker без послаблення передумов. Для checklist використовуються paths-only плюс окремий resolver. Збереження spec.md при повторному specify задається виправленою агентною інструкцією. Чотири локальні зміни skills збережені git-патчем; core upstream scripts не змінюються. Шість subprocess regression tests запускаються локально та в CI. Окремий звіт рецензії з рішеннями — reviews/copilot.md.
