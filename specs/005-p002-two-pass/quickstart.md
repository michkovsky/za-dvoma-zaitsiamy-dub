# Перевірка P002

1. Відкрити pilots/P002/README.md та workflow.md: обсяг, джерела, межі, стан стадій.
2. У зовнішньому work_dir перевірити входи й зафіксований pass-1 до створення scene.md.
3. Зіставити сирий UK pass-1 → reference.ru.md і попередню UK-редакцію → scene.md → pass-2 з повторною RU-перевіркою → comparison.md; підказка не містить готової розшифровки.
4. Перевірити reference.ru.md: українські [?] не зняті лише через RU.
5. З кореня репозиторію оновити базу PR (`git fetch origin main`; для PR #11 база — main) і виконати окремо перевірки закоміченого diff та робочого дерева:

   ```text
   python pipeline/validate.py
   git diff --check origin/main...HEAD
   git diff --exit-code origin/main...HEAD -- pilots/P001
   git diff --check
   git diff --cached --check
   git diff --exit-code -- pilots/P001
   git diff --cached --exit-code -- pilots/P001
   ```

   Усі команди мають завершитися exit=0; порівняння P001 — без diff. `origin/main...HEAD` охоплює коміти PR від спільної бази, а дві останні команди — відповідно unstaged і staged зміни. Порожній `git diff -- pilots/P001` сам по собі не доводить незмінності P001 у PR.
6. Межі, слова й мовців перевіряти прослуховуванням. Текстовий validator цього не підтверджує.

Copilot review — read-only для конкретного snapshot/коміту, з моделлю, доказами й рішеннями. Draft PR без злиття.

## Перевірка опублікованих входів перекладу

У pilots/P002/translation-ab/metadata.json старі source_sha256, prompt_sha256 та ненульовий context_sha256 — історичні SHA-256 UTF-8-файлів із CRLF. Їх не замінено. Поле published_inputs_utf8_lf_sha256 у кожній умові містить SHA опублікованих файлів із LF. Це суми байтів файлів, не серіалізованого аргументу CLI. Нормалізація нижче замінює лише CRLF на LF, не змінює JSON-форматування, не обрізає пробілів або завершальних переносів.

Запустити Python із кореня репозиторію з таким кодом (перевіряє 5 входів у двох умовах, спільне source.json — двічі):

```python
from pathlib import Path
import hashlib
import json

root = Path("pilots/P002/translation-ab")
records = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
checked = 0
for record in records:
    for filename, expected in record["published_inputs_utf8_lf_sha256"].items():
        data = (root / filename).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(data).hexdigest() == expected, filename
        checked += 1
assert checked == 5
print("OK: 5 published UTF-8/LF input hashes")
```
