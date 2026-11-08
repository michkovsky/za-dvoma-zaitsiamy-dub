# Workflow entities and states

No new database or content format.

## Change

Identity: branch + PR number + current head SHA. Attributes: purpose, scope, source evidence, linked spec, checks, open questions. States: preparing → draft PR → ready for owner review → approved for a specific head → merged, or closed. The agent does not perform the approval transition on behalf of the owner. A substantive new head invalidates prior approval for workflow purposes.

## Specification

Identity: specs/<number-short-name>. Attributes: user stories, FR IDs, criteria, plan, task IDs, built-in requirements checklist. Local .specify/feature.json selects the current feature and is ignored by Git. Existing simple edits can reference an applicable spec; expanding the scope requires updating requirements first.

## Review

Identity: reviewer/model + reviewed head/context + question. Fields: evidence, limitation, finding ID, severity (blocking/non-blocking), author disposition (accepted/rejected/deferred), reasoning. An old-head review is labeled stale or explicitly reassessed. Lack of a second model is recorded as not performed, not independent approval.

## Check

Fields: command, environment, exit code, scope, result. Text-only CI cannot establish audio quality, pronunciation, video sync or model/runtime compatibility. Author inspection is distinguished from owner acceptance.
