# Research

- Decision: project-local skill, implicit selection enabled. Rationale: власник хоче пропозиції агента; explicit-only приховав би skill від вибору. Автозапуск не дозволяється.
- Decision: інструкція без runner. CLI вже має -p, -C, --log-dir, --share, --resume, --allow-tool, --deny-tool; користь обгортки ще не доведена.
- Decision: дозволи під задачу. Installed help 1.0.107 підтверджує відхилення неавторизованих tool requests у prompt mode. [Офіційний guide](https://docs.github.com/en/copilot/how-tos/copilot-cli/automate-copilot-cli/run-cli-programmatically) радить мінімальні дозволи; [reference](https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-programmatic-reference) описує flags. Перевірено 2026-11-08.
- Verification boundary: version/help виконані раніше в цій сесії. Авторизований модельний запуск, редагування через CLI й автовиявлення нового skill не перевірені. Підготовка не потребує платної сесії.
