# Implementation Plan: P002 — два проходи

**Branch**: `codex/p002-two-pass-transcription` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

## Summary

Повна підготовка до візиту як окремий пілот. Прохід 1: сирий UK без підказки → локально синхронізований RU і його розшифровка → попередня UK-редакція з гіпотезами → фіксація результату. Далі опис сцени. Прохід 2: повторний UK із описовим контекстом → повторна перевірка RU-гіпотез за UK-звуком → порівняння. P001 не змінюється.

## Technical Context

**Language/Version**: Markdown/CSV/JSON, Python 3.12, FFmpeg/FFprobe.
**Primary Dependencies**: ізольований Whisper.cpp і багатомовна small q5_1; основний кандидат — Vulkan на GTX 1650, CPU-збірка як резерв. Сумісна збірка та мала реальна GPU-проба перед повною сценою. Старий runtime у доступних робочих каталогах не знайдений.
**Storage**: читабельні матеріали в pilots/P002; медіа, ваги, binary, prompts і сирі журнали — зовнішній work_dir.
**Testing**: validator, diff check, реальна коротка ASR-проба, SHA й порядок стадій, незмінність P001. CI не прослуховує звук.
**Target Platform**: Windows, Xeon без AVX2, GTX 1650 4 GB. FMA/F16C невідомі, їх не вмикати.
**Project Type**: дослідний пілот без універсального нового pipeline.
**Performance Goals**: перевірити короткий уривок до сцени; немає обіцянки швидкості або точності.
**Constraints**: без зміни погодженого P001, без підміни UK зворотним перекладом RU, без автоматичного verified/approved.
**Scale/Scope**: одна підготовка до візиту, два UK-проходи, опис і допоміжний RU; новий дубляж поза обсягом.

## Constitution Check

До й після дизайну: факти відділені від ASR; сталі ID; прості формати; перевірка CPU до запуску; джерела й журнали поза Git. Межі proposed до прослуховування. P002 не стає S001 і не змінює основне coverage. Порушень принципів немає. Copilot read-only review дозволений окремим дорученням власника.

## Project Structure

```text
specs/005-p002-two-pass/
  spec.md, plan.md, research.md, data-model.md, quickstart.md, tasks.md
  checklists/requirements.md
pilots/P002/
  README.md, workflow.md, sources.md, scene.md
  transcription/pass-1.uk.md, pass-2.uk.md, reference.ru.md, comparison.md
```

Сегмент ASR не є підтвердженою реплікою. dialogue.uk.csv та нові глобальні ID створюються після встановлення мовців, до того — Markdown із unknown/кандидатами й [?]. Старі P001-Lxxx не дублюються як нові canonical-рядки.

## Implementation sequence

Підготовка → сумісний ASR і коротка проба → сирий UK і SHA → RU та попередня UK-редакція з явним внеском RU → опис → другий UK з точно збереженою підказкою та повторною RU-перевіркою → порівняння → перевірки → Copilot review → draft PR. При зміні входу повторюються обидва проходи; старі результати зберігаються. RU-текст не підставляється в prompt першого сирого UK-розпізнавання, але використовується до завершення першого основного проходу.

## Complexity Tracking

Нових зовнішніх інтерфейсів немає, contracts/ не потрібні. Дослідження інструментів виконує автор; окремі дослідницькі агенти не доручені.
