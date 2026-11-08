# Upstream Spec Kit assets

CLI: specify-cli 1.3.2, official PyPI distribution from github/spec-kit. Initialization used the package's bundled templates/scripts/workflow, Codex integration, script=py and events=false. Upstream license: LICENSE.spec-kit (MIT).

Upstream-generated assets: .specify/scripts/, .specify/templates/, .specify/workflows/, .specify/integrations/ manifests, .agents/skills/speckit-*/. Project-owned: memory/constitution.md and specs/ artifacts. Do not apply the upstream license automatically to original film or all project content.

Generated skill invocations resolved to python with the isolated tool environment first on PATH; no personal absolute interpreter paths are committed. Intentional upstream refreshes must review the diff and preserve project-specific artifacts. Installed features pointer and package environments remain local.


Локальні відмінності чотирьох generated skills після Copilot review: patches/codex-safety.patch. Вони запобігають інструкції скидання spec.md, спрямовують read-only перевірки через process-local env wrapper та прибирають вимогу плану для checklist. Оригінальні manifests не переписують hashes під ці зміни; порядок повторного застосування — patches/README.md.
