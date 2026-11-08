# Інструменти

Для чистої локальної роботи спочатку налаштувати зовнішній `DUB_WORK_DIR`: [docs/local-workspace.md](../docs/local-workspace.md). Діагностика підтримує `--output`, нарізання — `--output-dir`; явні параметри переважають сесійний default. Без налаштування старі місця запису збережені.

Python 3.10+, стандартна бібліотека; FFmpeg/FFprobe на PATH для медіа. Не встановлювати PyTorch, ONNX Runtime або CUDA заради читання текстових файлів.

- diagnose_runtime.py — інвентаризація CPU/OS, GPU, RAM, диска й версій інструментів; local/runtime.json. Не доводить придатності ML-бібліотеки без короткого фактичного запуску.
- index_keyframes.py — пакетні прапори FFprobe → source/keyframes.csv, без декодування повного фільму.
- cut_media.py — точний уривок із відео й окремої української аудіодоріжки. Спочатку показує команду; --execute запускає.
- validate.py — CSV, ID, таймкоди, посилання глосарія, відсутність випадкового перекриття у виправленій суперечці та локальні SHA-256 погоджених медіа.

Підготовка: python pipeline/diagnose_runtime.py; потім local/media.json за media.example.json. Приклад пробної нарізки:

```powershell
python pipeline/cut_media.py --id P001 --start 00:26:30.000 --end 00:27:45.000
```

Синтез і фінальне складання ще не перенесені. Історичний сумісний стек описаний у skill runtime-diagnostics/references/legacy-runtime.md; це зафіксована попередня конфігурація, не автоматичний інсталятор.
