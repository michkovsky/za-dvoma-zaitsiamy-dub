# Research: decisions and compatibility

## Official distribution and version

Decision: official PyPI specify-cli 1.3.2, isolated venv; pin CLI version. Rationale: uv absent, Python 3.12 available, official installation documentation supports pip. Alternatives: global install would mix environments; moving Git main would not pin behavior. Source: https://github.github.io/spec-kit/installation.html.

## Codex integration

Decision: integration=codex, script=py, --integration-options="--events false". Rationale: current integration uses project skills, while sandbox previously rejected MSYS shell helper operations. Events and nested codex exec are not needed for agent-led steps. Source: https://github.github.io/spec-kit/integrations/codex.html; installed specify_cli/integrations/codex/__init__.py and base.py.

Actual issue: first init embedded a personal absolute Python path because PATH resolved only Store aliases. Reinitialized with the venv Scripts directory first on PATH. Upstream renderer then emitted portable python commands; no manual fork of generated skills was needed.

## Existing project preservation

Decision: init on a clean feature branch, record tracked SHA-256, back up and restore constitution before deliberate amendment. Rationale: --force can replace managed files. All tracked hashes matched after init/restoration, including domain skills and character data. Source: https://github.github.io/spec-kit/how-to/existing-projects.html.

## Specification scope and approvals

Decision: substantial changes use the full SDD sequence, editorial corrections can reference an existing spec; every change uses PR. Owner explicitly approves merge of current changes. Rationale: user requested reviewable PRs and real Spec Kit adoption, not per-replica bureaucracy. No technical branch protection is implied.

## Model review

Decision: independent models only on assignment; record model, commit/context, evidence, limitations and disposition. No automatic agreement voting. Rationale: independent critique adds value but is not a source of facts or merge authority. This PR has author checks only unless later reviewed independently.

## Text validation

Decision: run existing standard-library validator in pull_request CI, no media/model downloads. Rationale: contributor does not need original film to check tables. Use official checkout/setup-python actions pinned to resolved commit SHAs; permission contents:read. No server configuration change.

## Unresolved research

None blocking design. Fresh-session skill discovery and nested Codex dispatch are intentionally unverified capabilities, not requirements for preparing this draft PR. Credential configuration remains outside the repository.
