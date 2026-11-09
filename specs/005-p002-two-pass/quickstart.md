# Перевірка P002

1. Відкрити pilots/P002/README.md та workflow.md: обсяг, джерела, межі, стан стадій.
2. У зовнішньому work_dir перевірити входи й зафіксований pass-1 до створення scene.md.
3. Зіставити сирий UK pass-1 → reference.ru.md і попередню UK-редакцію → scene.md → pass-2 з повторною RU-перевіркою → comparison.md; підказка не містить готової розшифровки.
4. Перевірити reference.ru.md: українські [?] не зняті лише через RU.
5. Запустити `python pipeline/validate.py`, `git diff --check`, `git diff -- pilots/P001` (останній порожній).
6. Межі, слова й мовців перевіряти прослуховуванням. Текстовий validator цього не підтверджує.

Copilot review — read-only для конкретного snapshot/коміту, з моделлю, доказами й рішеннями. Draft PR без злиття.
