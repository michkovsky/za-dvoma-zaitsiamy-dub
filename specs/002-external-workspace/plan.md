# Implementation Plan: Зовнішнє сховище
**Branch**: 002-external-workspace | **Date**: 2026-11-08 | **Spec**: spec.md

## Summary
Додати два необов'язкові CLI-параметри й DUB_WORK_DIR. Використати стандартну бібліотеку й наявний Python/FFmpeg. Налаштування конкретної машини лишаються локальними.
## Technical Context
Python 3.10+ pipeline, Python 3.11+ Spec Kit. JSON/Markdown; без нових пакетів. Локально Windows, тести cross-platform. Сховище — файлова система; не junction. CI без ML/оригіналу. No full movie processing.
## Constitution Check
PASS before/after design: прості формати, діагностика до ML, оригінал не змінюється, одна гілка/PR, локальні шляхи не публікуються. Наявні skills застосовуються читанням інструкцій.
## Project Structure
pipeline/common.py — допоміжний external work path; diagnose_runtime.py --output; cut_media.py --output-dir. tests/test_output_paths.py — зовнішній/default/preview/precedence. docs/local-workspace.md та skill посилання. Локальні launcher/config/report — за межами Git, media.json лише durable mapping.
## Decisions
Явний CLI path > DUB_WORK_DIR > local/media.json work_dir > legacy default. Environment only per session; optional persistent work_dir in ignored media config. Empty/unset env means legacy. Для work env вимагати абсолютний зовнішній шлях; не приймати каталог усередині repo. Temp probes use null output. Немає external API contracts; це внутрішні CLI helpers.
## Verification
Subprocess tests, наявний validator, runtime report зовні та два короткі FFmpeg decode-to-null. Зіставити список медіа до/після. Публікувати draft PR; main не змінювати.
