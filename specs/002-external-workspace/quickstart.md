# Verification
Run python -B -m unittest discover -s tests -v and python -B pipeline/validate.py. Verify DUB_WORK_DIR paths, explicit precedence and legacy behavior with no source media needed. On target machine, run inventory externally and decode short video/audio segments to null, preserving source listing. Session entry is the locally generated Enter-2V.ps1 outside the repo. Personal paths and results are not committed. Completion evidence is appended after execution.


## Recorded local results

Eight output-path scenarios and six existing safety cases passed (14 total), including rejection of outputs inside source directories before writes. Project validator passed. Hardware inventory completed externally, showing AVX available, AVX2 unavailable, FMA/F16C unknown; GPU inventory found GTX 1650 with 4 GB VRAM. This does not qualify ML inference libraries.

Video and separate audio decoded 0.25 seconds at source 00:26:30 to null, exit 0. No probe media files were written. Original directory still contains the same three files with unchanged size/mtime. Local mapping contains work_dir; production dry-run without DUB_WORK_DIR selected external exports. Known setup template files removed; tmp is empty. No junction, global profile change, media/model installation or legacy artifact migration.

Author analysis: 7/7 FR items covered before implementation. Draft PR 3 published and initial CI passed. Copilot found two source-protection gaps; both addressed with regression coverage. Final CI and review outcomes are recorded in the PR. Personal paths, machine configuration, launcher and reports are outside Git. Owner approval remains pending.
