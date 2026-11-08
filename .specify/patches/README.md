# Локальні виправлення Codex skills

codex-safety.patch змінює чотири згенеровані skills Spec Kit 1.3.2 після ініціалізації codex/py з переносимими python-командами. Підстави — Copilot review PR #1, коментарі 4506041382, 4506041393, 4506041403. Виправлення вже застосовані до файлів у Git; повторно застосовувати їх у звичайному checkout не потрібно.

Після свідомого upstream refresh, якщо згенеровані skills повернулися до вихідного стану:

```text
git apply --check .specify/patches/codex-safety.patch
git apply .specify/patches/codex-safety.patch
python -m unittest discover -s tests -v
```

Якщо --check не проходить, зупинитися й переглянути відмінності/версію; не застосовувати force і не продовжувати з втраченими виправленнями. Перед refresh працювати з чистою гілкою та перевіряти diff. Wrapper pipeline/speckit_readonly.py має лишитися доступним. Upstream manifests зберігають вихідні hashes; ці явно задокументовані локальні зміни не видаються за незмінений upstream.

Patch replay перевірено на чистих копіях чотирьох upstream-файлів. Це тест переносності патча; він не доводить автоматичної поведінки моделі.
