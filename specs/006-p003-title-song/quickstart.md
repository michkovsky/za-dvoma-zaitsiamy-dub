# Перевірка P003

1. Прочитати `pilots/P003/README.md` і `sources.md`; налаштувати зовнішній DUB_WORK_DIR за `docs/local-workspace.md`.
2. Перевірити `<work>/reports/runtime.json`, потім коротку реальну ASR-пробу в `<work>/reports/P003/probe/`.
3. Зіставити SHA в `transcription/run-metadata.json` з робочими входами й сирими результатами. UK1 та UK2 повинні мати однакові input/model/binary hashes, а опис — бути збережений до UK2.
4. Прослухати контекст обох меж і непевні слова; raw ASR не є verified. Перевірити локальну RU-відповідність до використання.
5. Для англійського тексту перевірити source_id, зміст, наголоси, музичні вікна; для співу — короткий сольний вокал і мікс окремо.
6. Запустити `python -B pipeline/validate.py` і `git diff --check`. Повністю декодувати видану версію; перевірити видимий субтитр, тривалість і clipping. Ці перевірки не приймають звук за власника.

## Чинна інструментальна проба за нотами

ASR і ML-моделі для її побудови не потрібні. Читати pilots/P003/music-map.md та music/score.json. Запустити стандартний Python:

```powershell
python -B pipeline/render_p003_score.py --output-dir "$env:DUB_WORK_DIR/exports/P003/my-score-check" --key Am --bpm 110 --verses 1
```

Вихідний каталог має бути новим і зовнішнім. Очікуються MIDI, MusicXML та окремі WAV мелодії/гітари/міксу з manifest.json. Перевірити 8 тактів, 32 чверті, 39 атак і 17.455 с музики при 110 BPM. `--verses 3` дає 117 атак і 52.364 с музики; мелодія повторів тотожна, MusicXML показує один шаблон із трьома текстами. `--key 'C#m'` відновлює вихідне прочитання на 4 півтони вище Am. Це слухова проба нотної редакції, не синхронізована фонограма.

## Офлайн-аудит A68/A69

Запускати з кореня репозиторію. Потрібні зовнішній пакет P003 та сумісні NumPy, SciPy, librosa, SoundFile і PyWORLD. У збереженій сесії P003 шлях до перевіреного Python і вже наявних бібліотек указано в локальному додатку до передачі дослідження.

```powershell
$p003 = (Get-Content -Raw local/p003-session.json | ConvertFrom-Json).work_dir
$runtime = Get-Content -Raw (Join-Path $p003 'reports/P003/research-handoff-local.json') | ConvertFrom-Json
$env:PYTHONPATH = $runtime.site_paths -join ';'
$env:OPENBLAS_CORETYPE = $runtime.env_guards.OPENBLAS_CORETYPE
$env:OPENBLAS_NUM_THREADS = '1'
$env:NUMBA_DISABLE_JIT = '1'
& $runtime.python_executable -B pipeline/audit_p003_conditioning.py --work-dir $p003
```

Скрипт читає `exports/P003/neural-tuning/borisov-verse3-full-v1`, карту й чотири WAV із `exports/P003/verse-3-trial/v5`, мітки з `reports/P003/verse-3-trial/phones-v5.json`. За замовчуванням створює новий `reports/P003/audit-A68-A69.json` у вибраному work_dir. Для повторного запуску передайте `--output` із новим зовнішнім шляхом. У `vowels` наведено порівняння до й після вокодера та вимірювання AM. У `slots` знайдіть слово й номер рядка. `source_s` у мітках відраховано від відповідного spoken WAV, `target_s` у слоті — від початку куплету. `mapped_ms` показує, скільки часу слота отримала мітка, `mapped_core_ms` — скільки з нього припало на утримуване ядро. Найбільші локальні зміни спектра й можливі релізи /p/ наведено в тій самій джерельній шкалі.
