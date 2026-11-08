# Implementation Plan: Copilot delegation

**Branch**: `003-copilot-delegation` | **Date**: 2026-11-08 | **Spec**: [spec.md](spec.md)

## Summary
Один проєктний skill із правилами вибору, передачі й приймання; посилання в AGENTS.md та CONTRIBUTING.md. Без runner, автоматичних запусків і нових залежностей.

## Technical Context
Markdown UTF-8, UI metadata YAML. CLI потрібний лише для фактичного делегування. Журнали — зовнішній work_dir. Перевірки: quick_validate.py зі skill-creator, validator проєкту, ручні сценарії та diff --check. Тести формулювань не потрібні.
CLI flags звіряти з установленою версією; Windows launcher може не розпаковуватися у sandbox. Media/ML не запускаються.

## Constitution Check
До дослідження та після дизайну всі сім принципів дотримані: джерельні артефакти не змінюємо, прості формати, апаратна діагностика лише для задач із media/ML. Доручення іншій моделі потрібне перед запуском, злиття окремо. Конфліктів немає.

## Project Structure
- .agents/skills/copilot-delegation/SKILL.md — процес і компактний шаблон завдання.
- .agents/skills/copilot-delegation/agents/openai.yaml — UI назва, опис, приклад; implicit selection дозволений.
- AGENTS.md — умови вибору та межа запуску.
- CONTRIBUTING.md — посилання, розрізнення виконання/рев’ю.
- specs/003-copilot-delegation/ — вимоги, дизайн, перевірки й завдання.

Внутрішній workflow без публічного API: contracts/ не потрібен. Невідомих рішень і дослідницьких підзадач немає; дослідницькі агенти не потрібні.
