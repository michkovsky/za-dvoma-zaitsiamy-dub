# Джерела й часові шкали

- UK: [ewkaGqEH508](https://www.youtube.com/watch?v=ewkaGqEH508), зареєстрований source audio; окремий Opus — український звук, незалежно від помилкового language metadata контейнера.
- RU: [50A7fZbjrz8](https://www.youtube.com/watch?v=50A7fZbjrz8), оригінальна Russian original доріжка 251-2 з публікації Odesa Film Studio. Англійське auto-dub і автоматичні субтитри не використовуються.
- Попередня RU LmDsOGdm06Y не є входом P002.

## Робочі входи

Зовнішній exports/P002:

| Вхід | Вихідний інтервал | SHA-256 |
|---|---|---|
| P002_uk_source-00-24-30_to-00-32-05_asr.wav | UK 00:24:30.000–00:32:05.000 | ED21EF9A226C15014324E18831B7022C71A58A3DECF8189001424C5CA876BE68 |
| P002_ru_source-00-24-25.500_to-00-32-00.500_asr.wav | RU 00:24:25.500–00:32:00.500 | A4540B0990D3CF8A74595F289FC542F55173501CE4BAFCD4781DB6DA3351B6AE |

FFmpeg: mono PCM s16le, 16 kHz, без шумозаглушення/підсилення; 455 с кожен. Обидва UK-проходи читають один файл, не повторно нарізані варіанти. Короткий runtime-probe — окремий файл, не перший прохід сцени.

UK source = t_P002 +1470.000 с. UK no-ads = UK source −5.000 с; P001 local = UK source −1590.000 с. RU source = t_RU_clip +1465.500 с. Ці формули не доводять точного синхрону UK/RU: відповідність уточнюється локально; зміни монтажу фільму відомі.

Контекстний аркуш потрібний для навігації, не доводить голосової межі. Подробиці ширшого аудиту копій — зовнішній reports/copy-audit-2026-11-09. Медіа, абсолютні локальні шляхи та ваги не включаються в Git.

## ASR і апаратна перевірка

Whisper.cpp **v1.7.6**, ізольована збірка з офіційного [source archive](https://github.com/ggml-org/whisper.cpp/archive/refs/tags/v1.7.6.zip). GCC 16.2.0 (w64devkit 2.11.0), CMake 3.31.8, Vulkan SDK 1.3.296.0; SDK витягнуто як архів без системного встановлення. CPU: GGML_NATIVE=OFF, AVX=ON, AVX2/FMA/F16C/BMI2/AVX512/LLAMAFILE=OFF. GPU: GGML_VULKAN=ON. CPU F16C не потрібен для перевіреного GPU fp16-режиму; це різні можливості.

GTX 1650 4 GB реально використана: `whisper_backend_init_gpu: using Vulkan0 backend`. 12-секундна small-проба завершилася exit=0 за 6.859 с; потім повні UK1, RU й UK2. Vulkan device info: NVIDIA GTX 1650, fp16=1, matrix cores=none. CPU-збірка підготовлена як резерв; основні проходи не були CPU-only.

Модель контрольної пари — [ggml-small-q5_1.bin](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small-q5_1.bin), SHA-256 `ae85e4a935d7a567bd102fe55afc16bb595bdb618e11b2fc7591bc08120411bb`. Binary SHA-256 `ca92abf03591f6ad24fa3d0c911f331a787728cf7a1b7af8c0d88a344c7c8e52`. Параметри й порядок — [run-metadata.json](transcription/run-metadata.json). Вхід, модель та binary двох контрольних UK однакові, змінено лише prompt.

Після виродження контрольної пари виконано окремий chunked-повтор small: 30 с / крок 25 с, beam=5/best-of=5, fallback. Його не змішувати з контролем впливу опису. У chunk-05 з 00:02:05 вийшов лише дуже короткий машинний текст, тому повтор ще не є повною редакторською версією. Параметри й raw-записи кожного вікна збережено у зовнішньому reports/P002/pass-2-chunked.

Сильніша [medium q5_0](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium-q5_0.bin) пройшла окрему реальну 25-секундну GPU-пробу exit=0. Подальший medium-повтор має власний журнал і не перезаписує контрольну пару.
