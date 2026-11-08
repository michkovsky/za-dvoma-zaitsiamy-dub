# Перевірка skill

1. Прочитати .agents/skills/copilot-delegation/SKILL.md явно; автовиявлення в поточному чаті не припускати.
2. Запустити quick_validate.py зі встановленого skill-creator для каталогу skill; python -B pipeline/validate.py; git diff --check.
3. Оцінити: ізольований скрипт → пропозиція; проста помилка літери → самостійно; явне доручення Copilot → без повторного погодження в тих самих межах (SC-001).
4. Скласти завдання реалізації скрипта та окремого read-only рев’ю SHA. Перевірити контекст, межі, критерії, дозволи, зовнішні журнали й приймання (SC-002).
5. Diff містить лише skill, посилання та spec, без логів/медіа/конфігурацій. Відкрити draft PR, перевірити CI, запросити Copilot review та дочекатися відповіді; без merge (SC-003).

Підготовка не включає платний запуск CLI. Першу авторизовану роботу перевіряти окремо й не оголошувати вже виконаною.

## Фактичні результати 2026-11-08

- Spec Kit: інструкції specify/plan/tasks/analyze/implement/converge прочитані явно. resolve_template, setup_plan, setup_tasks і read-only prerequisites виконані; hooks відсутні. Автовиявлення не перевірено.
- Аналіз до реалізації: 7/7 FR мають tasks (001–002 → T003/T004, 003–007 → T005/T006); суперечностей із конституцією, непокритих вимог і невирішених уточнень немає. Це авторська перевірка.
- quick_validate.py: Skill is valid. У bundled Python немає PyYAML; використано вже наявний модуль із попереднього локального tool environment через процесний PYTHONPATH, без установлення чи зміни global profile.
- YAML UI розібрано: implicit invocation true, default_prompt містить $copilot-delegation. Усі локальні посилання skill існують.
- Validator проєкту: OK (14 CSV, 1015 keyframe anchors, 30 characters); diff --check без зауважень.
- Ручні сценарії SC-001: ізольований скрипт → запропонувати; літера → зробити самостійно; явне доручення в тих самих межах → не перепитувати. Жодного CLI модельного запуску.
- SC-002, реалізація: приклад завдання — виправити конкретний скрипт на заданому SHA, лише названі pipeline/test файли, потрібні read/write/test tools, незакомічений diff, цільова команда перевірки, зовнішні журнали. Приймання: diff і фактична команда, без push/merge.
- SC-002, рев’ю: окреме завдання перевірки актуального SHA за spec з read-only доступом, знахідками path/line/evidence, без редагувань і mutations. Приймання: звірити докази, записати рішення за model-review. Шаблон skill містить усі ці поля.
- SC-003: публікація, CI й висновок Copilot фіксуються в PR; злиття не виконується.
- Convergence після implement: 7 FR, 6 acceptance scenarios, 3 SC, рішення дизайну та 7 принципів перевірені. Реалізовані вимоги й межі виконані; прогалин, що потребують нових implementation tasks, немає. Залишено delivery T008; незалежне рев’ю не підміняється цим авторським висновком.

## Підтвердження доставки після початкового convergence

- [PR №4](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/4) злитий; merge commit 57341339765a144826b49ed69076fec4e9e00056.
- Copilot review коміту 91459a5864e8c50da063154db98dee90bb6a1d10: Approval recommended, No open issues; точна модель сервісом не розкрита. Це GitHub review документації skill, не авторизований запуск локального Copilot CLI.
- [CI цього head](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/actions/runs/42497446080): success. T008 завершено за цими доказами; старий запис вище описує стан до доставки.
