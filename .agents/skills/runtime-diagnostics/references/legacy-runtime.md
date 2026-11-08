# Історична робоча конфігурація пілота

Спостереження попередніх сесій; повторно перевірити на поточному комп'ютері. Абсолютні локальні шляхи й файли моделей не входять у Git.

- Xeon E3-1240, Sandy Bridge, AVX підтримувався; AVX2/FMA/F16C не були доступні. GTX 1650, 4 GB VRAM; доступний обсяг змінюється.
- Whisper.cpp: робоча CPU-збірка з SSE4.2/AVX, без AVX2/FMA/F16C; 4 threads, CPU inference. Stock x64 міг падати з illegal instruction. Збережений локальний whisper-cli.exe — у старому work/build-gcc/bin, DLL від w64devkit. Моделі base і small-q5_1. Прапори локальної збірки: -ng -nfa -t 4 -bs 1 -bo 1.
- Chatterbox 0.1.2, torch 2.6.0+cu124, torchaudio 2.6, transformers 4.46.3, huggingface-hub 0.36.2, numpy 1.26, scipy 1.14.1, numba 0.61.2, librosa 0.11. Це історичний список, не повний перевірений lockfile.
- Перед import torch: ATEN_CPU_CAPABILITY=default, ONEDNN_MAX_CPU_ISA=AVX, MKL_ENABLE_INSTRUCTIONS=SSE4_2. Використовувати лише для відтворення сумісного режиму на старому CPU. HF_HUB_DISABLE_XET=1; локальні HF_HOME та NUMBA_CACHE_DIR.
- Гібрид: модель завантажувалася CPU; тільки t3 переносився на CUDA (~2 GB). s3gen лишався CPU; speech_tokens перед декодером переводилися .cpu(). Підготовка conditioning — CPU, потім model.conds.t3.to(device='cuda'). Аргумент device тут іменований.
- T3 conditioning: не deepcopy non-leaf tensors. Для експерименту Явдохи зберігався identity=model.conds; після нової підказки поверталися identity.t3.speaker_emb та identity.gen.
- Локальна правка s3tokenizer/utils.py: import ONNX перенесено всередину невикористаної функції onnx2torch, бо DLL ONNX не завантажувалась. Це правка залежності, яку треба окремо відтворити/перевірити при міграції.
- Для розділення звуку працював ONNX Runtime 1.17.3; NumPy 1.26; Kim_Vocal_2.onnx. n_fft=7680, hop=1024, bins=3072, frames=256, compensation=1.009; оригінал 44.1 kHz stereo. Це не гарантія сумісності новішого ORT.

Масовий синтез ще залежить від старих work/clone-deps та work/clone-extra. Не встановлювати стек навмання поверх системного Python. Спочатку відновити ізольоване середовище, перевірити малі операції й лише тоді зафіксувати повний lockfile.

Публікація gh працює через окремий локальний GH_CONFIG_DIR, який задається зовнішнім середовищем. Не шукати токен у репозиторії й не копіювати hosts.yml до нього. Системний Git shell/credential helper у sandbox міг відмовляти з NtCreateDirectoryObject; це не свідчить про несправність GitHub-авторизації.
