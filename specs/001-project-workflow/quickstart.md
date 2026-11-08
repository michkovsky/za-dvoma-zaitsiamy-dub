# Setup and validation

## Local setup

Use a working Python 3.11+ executable (Store aliases alone may not work). The initial installation used local/tools/spec-kit; after adoption of the external-workspace policy, new setups must use the configured external DUB_WORK_DIR. The historical results below are unchanged.

```powershell
if (-not $env:DUB_WORK_DIR) { throw 'Configure the external DUB_WORK_DIR first; see docs/local-workspace.md.' }
$specKitEnv = Join-Path $env:DUB_WORK_DIR 'tools/spec-kit'
python -m venv $specKitEnv
& (Join-Path $specKitEnv 'Scripts/python.exe') -m pip install -r requirements-tools.txt
$env:Path=(Join-Path $specKitEnv 'Scripts')+';'+$env:Path
specify version
specify check
```

The checked-in scaffold is already initialized. Do not reinitialize by default. For a deliberate refresh on a clean branch, preserve constitution/domain skills and inspect the diff:

```powershell
specify init --here --force --non-interactive --integration codex --script py --integration-options="--events false"
git apply --check .specify/patches/codex-safety.patch
git apply .specify/patches/codex-safety.patch
```

## Select this feature and validate

```powershell
$env:SPECIFY_FEATURE_DIRECTORY='specs/001-project-workflow'
python .specify/scripts/python/resolve_template.py spec-template --json
python pipeline/speckit_readonly.py --json --require-spec --require-tasks --include-tasks
python pipeline/validate.py
```

Fresh Codex session: open repository root, then invoke $speckit-specify and subsequent skills with task context. In this existing parent-directory chat, installed SKILL.md instructions are read explicitly. New-session automatic discovery is not yet verified.

## Recorded results

- specify version: 1.3.2, Python 3.12.14, Windows AMD64; exit 0.
- init: codex/py, events=false; exit 0. Initial absolute interpreter path issue corrected by reinitializing with venv PATH.
- specify check: reports ready; unrelated agent CLIs not installed are informational.
- Existing tracked SHA-256 comparison after init and constitution restoration: no changed files before deliberate edits.
- Official spec/constitution resolver and setup_plan: exit 0.
- Task/prerequisite checks, local text validation and first remote CI results are recorded below with their actual scope.

## Owner review

Inspect this draft PR, specification, compatibility document and checks. This is not merge authorization. If approving, identify the current head or clearly the current PR version. No direct main push, forced update or auto-merge.


## Author consistency analysis before implementation

Read-only analysis under installed speckit-analyze instructions: 12/12 FR items covered by T001–T016 (100%); zero critical/high findings, no unmapped tasks, no blocking clarification. Assumptions explicitly distinguish policy from server protection, author checks from independent review and skills files from verified new-session discovery. Built-in requirements checklist passed; no reviewer-owned checklist was self-approved. This record was added during implementation after the read-only analysis step.


## Local implementation checks

- Official setup_tasks and check_prerequisites (--require-spec --require-tasks --include-tasks): exit 0.
- specify artifact list --json: exit 0; official command/template/script inventory available.
- Project validator: exit 0; 14 CSV tables, 1015 keyframe anchors, 30 character records, credit/concept/speaker links; two local pilot hashes and three local credit-evidence hashes checked.
- Baseline assertion: 41 protected domain files unchanged, including four domain skills and all character/language/source/pilot/scene files.
- Portable registration assertion: nine upstream skills without personal absolute interpreter paths; py scripts/events=false confirmed; no .codex/config.toml created.
- GitHub Actions YAML parses; contents:read only, official actions pinned to resolved commit SHAs. This local syntax check does not claim remote CI success.
- Initial convergence: two partial evidence gaps (draft PR URL and remote result) appended as T017–T018; no additional implementation or independent model review claimed.


## Remote delivery evidence

- Draft PR: https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/1, branch 001-project-workflow → main.
- Initial reviewed workflow head: 80e96420ada659eeeb68a1a670ef620bb5771bb4.
- GitHub Actions run: https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/actions/runs/42474876285 — completed, success.
- Linux/Python text validation result: 14 CSV tables, 1015 keyframe anchors, 30 character records; zero local media and evidence hashes checked because those files are absent in CI. No audio/video quality claim follows from this result.
- Remote main remains 8f436649d8e5ba09bfc629a4624aa7f7554466ad, the baseline before this feature. PR is draft, not merged, auto-merge not enabled.
- Evidence is tied to the run/head above. Subsequent documentation-only evidence commit triggers another run; latest status is visible in the PR.
- Independent model review: not performed. Owner review/merge approval: pending and outside feature delivery.


## Final author convergence

After delivery evidence was recorded, all 12 FR items, three user stories, four success criteria, plan decisions and seven constitution principles were assessed against the implementation. All 18 tasks are complete for draft delivery; zero actionable implementation gaps remain. tasks.md was left unchanged by this final convergence pass. Owner acceptance, independent model review, new-session discovery and nested dispatch are not reclassified as completed.


## Copilot follow-up (supersedes earlier review status)

Independent Copilot review of head 124fee0 is now available; three findings accepted, see reviews/copilot.md. Four generated skills have local, replayable corrections. Six real subprocess regression tests passed locally; patch replay on clean upstream copies passed. Run: python -m unittest discover -s tests -v. New-head CI and independent reassessment are separate from the earlier successful runs; no automatic thread resolution or owner approval is implied.
