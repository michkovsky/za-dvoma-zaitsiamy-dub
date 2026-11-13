# P003 — передача контексту для окремого дослідження співу

Дата: 2026-11-11. Гілка: codex/p003-title-song. Базовий commit перед цією передачею: 039e16e. Чинний draft PR: [#12](https://github.com/michkovsky/za-dvoma-zaitsiamy-dub/pull/12).

## 1. Стан і завдання дослідження

**Працездатного фінального англійського співу ще немає.** Останню повну пробу третього куплету A69 користувач відхилив: дикція потребує роботи, дрижання лишилося. A68 — її сухий вокал, окремо останнім відгуком не оцінений. Вдалий CUDA render не є підтвердженням акустичної якості.

Мета окремого дослідження — встановити причини дзижчання/дрижання протяжних голосних і втрат англійської артикуляції та запропонувати перевірений шлях до природного співу на задану мелодію з ідентичністю Борисова. Потрібне дослідження ланцюжка, а не ще один необґрунтований підбір seed/CFG/кількості кроків.

Поточний фокус — **лише Борисов**. Низького виконавця користувач ідентифікував як **Грудинин Валентин Гурьевич, бас**; у документації — Валентин Грудинін. Його профіль/партію відкладено. Гіпотеза про модуляцію Борисова замість окремого низького виконавця більше не є актуальною основою casting.

Цей файл передає контекст; окремий чат/агент і нові фонові досліди під час його підготовки не запускалися.

## 2. Що прочитати та де знайти файли

Спочатку прочитати AGENTS.md, .specify/memory/constitution.md, CONTRIBUTING.md, docs/workflow.md, docs/formats.md та docs/local-workspace.md. Skills за операцією: runtime-diagnostics, voice-profiles, scene-dubbing, за потреби media-preparation і встановлені speckit skills. Не імітувати skill вкладеним codex exec. Поточне дослідження стосується специфікації 006-p003-title-song.

Основні джерела в репозиторії:

- [artifacts.csv](artifacts.csv) — сталі ID, точні відносні файли, SHA-256, status, scope і feedback. Approved завжди читати разом зі scope.
- [voice-profiles.md](voice-profiles.md) — докладна історія LC-відгуків; останні розділи переважають старі припущення.
- [voices.json](voices.json) — актуальна модель акторів, посилання на кеші та результати проб.
- [borisov-profile.json](borisov-profile.json) — оригінальні еталони Борисова й native conditioning. Не плутати з навченими новими вагами.
- [score.json](music/score.json), [music-map.md](music-map.md) — нотна основа.
- [song.en.md](../../languages/en/pilots/P003/song.en.md), [adaptation-brief.md](adaptation-brief.md), [editorial.uk.md](transcription/editorial.uk.md) — слова та погоджена смислова основа.
- [spec.md](../../specs/006-p003-title-song/spec.md), plan.md, research.md, tasks.md у тій самій папці — рамки й технічні рішення.

Бінарні входи, аудіо, моделі й експериментальні скрипти **не в Git**. Для цього циклу P003 зовнішній work_dir зафіксований у local/p003-session.json; також перевірити сесійний DUB_WORK_DIR перед новою роботою. Не підміняти його автоматично work_dir із local/media.json: останній використовується також для спільних інструментів/старого runtime report.

У цьому workspace машинні абсолютні шляхи зведено до окремого локального файла: **<work_dir>/reports/P003/research-handoff-local.json**. Він не комітиться. Також є історичний <work_dir>/reports/P003/RESUME.md; він доповнювався протягом багатьох етапів, тому читати останні записи, не лише початок.

Приклад отримання інтерпретатора без Windows python alias:

    $p003Session = Get-Content local/p003-session.json -Raw | ConvertFrom-Json
    $p003Work = $p003Session.work_dir
    $p003Local = Get-Content (Join-Path $p003Work 'reports/P003/research-handoff-local.json') -Raw | ConvertFrom-Json
    & $p003Local.python_executable -B pipeline/validate.py

Відносні exports/... та reports/... у таблицях нижче відраховуються від зовнішнього work_dir. Скрипти дослідів лежать у reports/P003/neural-tuning/. Не запускати їх наосліп: частина каталогів уже існує, частина скриптів — одноразові прототипи, а не підтримуваний універсальний CLI.

## 3. Незмінні вимоги й погодження

### Музика і текст

- Одна спільна мелодія для трьох куплетів. Раніше три голосові виконання помилково інтерпретувалися як різні мелодії; користувач це виправив.
- Основа — надані користувачем баянові ноти й верхня акордна схема Am. Прочитання вихідної партитури C-sharp minor; демонстраційна транспозиція −4 півтони в Am.
- 8 тактів, 32 чверті, 39 складових атак; рядки 10/9/10/10. Демонстраційні 110 BPM не є перевіреним темпом фонограми.
- Поточні чоловічі проби на октаву нижче виписаної мелодії. Не змінювати ноти довільно, щоб штучно зробити тембр басовим.
- Гітара у пробах — редакторський акомпанемент із нотної основи, не точна розпізнана гітарна фонограма.
- Текст перекладу, фонетичний prompt і текст ASR — різні речі. Помилки ASR не є новою версією перекладу.

Поточний третій куплет:

    My dear mother has a heart warm and kind,
    And my papa has himself a shop.
    And they never hurt these feelings of mine,
    I'm their only son, the cream of the crop.

Не переробляти поезію, щоб приховати дефекти синтезу. Загальна адаптація зберігає контрлексичний удар: ніжний/улесливий початок завершується словом з іншого лексичного набору — геометричний horizon/parallel, дешеві солодощі, shop. Слабке nudge другого куплету лишається окремим відкладеним питанням, не акустичною задачею цього дослідження.

### Актори і джерела

- Користувач установив: пісню виконував Олег Борисов; він озвучував обидві мовні версії. Користувач вважає російську доріжку історично чистішою — вона основна для профілю.
- Основний голос у canary opening і mother line — той самий виконавець. Ехо початку пояснюється виходом з арки; його не включати в базовий тембр.
- R01/R02 — сталі ID виконавських доріжок, не номери файлів або доказ двох автоматично знайдених профілів. Нумерацію користувача 1/4/5 раніше помилково прирівнювали до reel/file IDs.
- Низька papa/shop партія за останнім уточненням — Грудинін; зараз відкладена. Старий опис R02 як звичайного баритона та same-Borisov-modulation гіпотеза — історичні, не актуальний доказ типу голосу Грудиніна.
- **Перекриття mother/papa немає**: користувач переслухав і скасував попередню гіпотезу накладання.
- Поліфонічні/хорові зразки не використовувати як сольний conditioning. Не призначати всі невстановлені рядки Борисову як факт оригінального casting.
- Повний A69 — тимчасове виконання всіх чотирьох рядків одним Борисовим для досліду. Це не фінальне відтворення складу співаків.

### Що дійсно прийнято

- A07, A09, A10 — старі **нейтральні** проби вимови/збірки третього куплету; це не прийнятий клон Борисова. Особливо зберегти погоджені feelings of mine і the cream of the crop.
- A21 — точний другий блок українського Rubber Band roundtrip, не нейронний ланцюжок.
- A27/A28 — лише відсутність названого дьбре в конкретних українських DTW-контролях.
- A39 — лише відсутність дрижання в конкретному BigVGAN vocoder-only блоці.
- A41 — лише відсутність вираженого електронного тремтіння в українській пробі; слабке залишкове можливе.
- A53 — майже усунене дрижання, включно із серце, **лише для exact self-reference**.
- A56/A57 — прийнята основа оригінальних еталонів/профілю Борисова. Жодне нове англійське виконання цим не прийняте.
- У A46 користувач схвалив виправлення mother; повна пара відхилена за іншими дефектами.
- У A64 h працює; відкриті/піввідкриті A дрижать, тому повний запис відхилений.
- У відгуку на A67 has добре й чітко, heart дрижить, warm and kind погано розбірливі. **Блок A/B не названий** — не вигадувати точне ширше погодження A66.

Не перезаписувати ці файли і не поширювати вузькі погодження на весь метод.

## 4. Карта невдалих спроб і часткових результатів

Окремі старі comparison artifacts лишилися зі status=proposed, хоча feedback містить негативний або вузький результат. Таблиця описує слухову історію, а не підвищує статуси автоматично.

| Спроба / артефакти | Що робилося | Результат | Межа висновку |
|---|---|---|---|
| Нейтральний Piper + WORLD, A07/A09/A10 | Мовлення підганялося до нот, окремо ремонтувалися of і два the | Користувач прийняв окремі вимови й нейтральну збірку | Доказ, що слова можуть бути зрозумілими; не доказ природного акторського співу |
| Формантне зниження papa, A11 | Інший тембр отримувався обробкою | Не стало окремим акторським профілем | Не плутати DSP-варіант із новим виконавцем |
| Ранні S3/HiFT профілі й pitch restoration, A13–A19 | Voice conversion, відновлення нот WORLD, потім Rubber Band | Частина технічних нот краща, але голос штучний; A19 відхилений за дикцією. Дистанція висот була прийнятна | Pitch error не вимірює природності; рання двоакторна модель потім уточнювалася |
| Український original / roundtrip / S3+pitch, A20/A21 | Розділено прямий pitch roundtrip і повний ланцюжок | Блоки 1–2 добрі, у 3 дрижання; точний блок 2 збережений як A21 | Не трактувати stress roundtrip як прийняту нейроконверсію |
| Повільніший pitch controller, A22 | Згладження керування після raw S3 | Дьоьобрье / дьбре, муагазин; відхилено | Просте згладжування F0 не усунуло дефект |
| Source F0 у HiFT, сила mel 100% → 35%, A23 | Заміна F0 predictor і частковий log-mel blend | Другий трохи кращий, слабке дьобре лишилося | 65% source mel зберігає вихідний тембр; не доведене перенесення ідентичності |
| RU source замість UK, A24/A25 | Джерельна зміна при незмінних профілях | RU частково краща, але ще не чисте виконання | Не доводить, що всі дефекти — тільки акустика UK |
| Band-limited cepstral DTW + 35%/20%, A26–A28 | Узгодження фаз фонем/спектрограм | Користувач перестав чути конкретне дьбре | Вузький український успіх не перенісся автоматично на English |
| English transfer і local envelope repair, A29–A31 | Перенесено параметри, потім ремонтували has/shop через низькі DCT-компоненти і згладження | Електронне тремтіння has/shop, потім майже всіх голосних; A29/A30 відхилені | Локальний ремонт двох слів був недостатнім |
| Старий HiFT stage control, A32 | Guide → source mel/source F0 vocoder → neural35% | Збережено, але немає однозначного відгуку, який локалізує його три блоки | Асинхронна відповідь користувача стосувалася пізніше показаних файлів; не плутати з A37 |
| Seed-VC v1 singing, A33–A36 | Нативна F0-conditioned модель 44.1 kHz | Українська й англійська конверсії теж тремтять | Заміна speech VC на SVC сама по собі проблеми не розв'язала |
| BigVGAN source-mel roundtrip, A37/A39 | Original → vocoder-only → SVC, однаковий source | Користувач чує тремтіння лише в третьому блоці | У цьому українськомовному контролі з content із RU-доріжки vocoder-only не вводить дефект. Не доведено, який підмодуль SVC винен |
| CFG0.7 → 0, A40/A41 | Обидва режими перерендерено зі seed reset per phrase | Виражене електронне тремтіння майже відсутнє в обох; другий, можливо, трохи кращий | Новий baseline теж змінився відносно попереднього RNG-проходу; перевага CFG непевна. CFG0 зберігає conditional conversion |
| English CFG0, A42 | Українські параметри перенесено на англійський guide | Has чітке; mother й інші голосні тремтять; shop нечіткий | Українське приймання не дорівнює English generalization |
| FP32 замість FP16, 30 steps, A44/A45 | Та сама генерація з іншою precision | Mother waveform correlation ≈0.99846, mean log-mel delta ≈0.00281 | Значного виправлення лише від precision не доведено; це внутрішній контроль |
| FP32/100 steps і /p/ у guide, A46/A47 | Збільшено steps; для R02 також замінено кінцевий /p/ | Mother виправлено; shop звучить shAaagh; інші вібрації лишаються | Для R02 одночасно змінені precision/steps і guide, чистий ефект одного параметра не ізольовано |
| Виразніший /p/ із A shop again, A48/A49 | Взято closure/release, включно з transition після приблизного phone end | O/A тремтить у source guide і conversion, у conversion ширше; можливо дещо краще, але користувач втомився й не певен | Є підозра на upstream внесок, але це не доказ єдиної причини; /p/ остаточно не прийнятий |
| UK original performance → SVC FP32/100, A50/A51 | Вхід — природний український спів із RU-треку; reference — окремий UK singing fragment | Сеерце / дообре: кілька повторних спадань голосної; нейронне виконання відхилене | Штучний English guide не може бути єдиним поясненням усіх дефектів |
| Exact self-reference, A52/A53 | Вхідний R01 WAV одночасно подано як reference | Майже позбулися дрижання, також у серце | Змінюється не лише якість джерела, а й точний збіг content/reference. Це не доказ cross-language conversion |
| Англійська з RU singing refs, A54/A55 | Заміна UK-еталонів на відповідні RU-еталони | Ревербераційний присмак на всіх голосних; A54 відхилено | Висновок про достатність чистішої доріжки спростований цією пробою |
| Прийнятий speech profile Борисова, A56–A59 | Профіль з оригінальної мови/співу; English guide через primary RU speech B01 | Оригінали прийняті; новий English singing A58 знов дзижчить, shop геть нечіткий | Валідний оригінальний профіль не доводить якість співочого рушія |
| Speech-only English VC, A60 | Той самий B01, звичайний Piper spoken-line-2, без WORLD/розтягування | ASR: And my papa has himself a shot | Більша частина рядка збережена, але shop/shot плутаються; слухового приймання немає |
| Direct score semantic warp, A61/A62 | Spoken features → нотні тривалості/F0 → native CFM/BigVGAN; без WORLD waveform | ASR упізнав shop; користувач почув кххх у has/heart і дрижання open A | Це інший, експериментальний шлях, а не доведене виправлення попереднього |
| Voicing fix і h boundaries, A63–A65 | Усунуто hard-mask помилку, уточнено початок sustain; steady semantic core | H працює, відкриті/піввідкриті A дрижать; A64 у цілому відхилений | Реальну кодову помилку виправлено, але не всі причини flutter |
| Amplitude-only local control, A66/A67 | Інверсія 3.5–12 Hz log-envelope, ±2 dB лише в ядрах has/heart | AM plateau RMS ≈0.70→0.18 і 0.97→0.36 dB. Has чітке, heart дрижить, warm and kind погано розбірливі | Менша AM-метрика не доводить усунення pitch/formant/phase нестійкості. Блок відгуку A/B не уточнений |
| Суцільний повний куплет на CUDA, A68/A69 | 4 рядки одним neural context, без незалежної генерації кожної фрази | Генерація успішна, але користувач знов відхилив дикцію й дрижання | Більший контекст і апаратне прискорення не розв'язали акустичну проблему |

## 5. Найважливіші діагностичні факти

### Реальна помилка voiced/unvoiced керування — не гіпотеза про весь рушій

У першому direct-score коді спочатку вмикався voiced vowel nucleus, а потім приблизна phone mask могла знову його вимкнути. Has мав 39 zero-F0 кадрів ядра по 11.61 ms, приблизно 453 ms; heart — 4 кадри. Пріоритет виправлено, в цих контрольних ядрах zero-F0 кадрів стало нуль.

Крім того, has vowel window 0.695–0.755 s перетинав приблизний h interval до 0.73143 s; heart 0.935–1.010 — h до 0.94041. У A64 sustain починається після h end +8 ms, мінімальна core width 20 ms; semantic core має переходи 55 ms. Це редакторська гіпотеза меж. Користувач схвалив h, але не все звучання A.

### Pitch, AM і темброва нестійкість — різні виміри

Для A64 приблизні interiors: has 1.22–1.76 s; heart 2.32–2.83 s. DIO дав медіану близько145.9 Hz та p10–p90 pitch spread близько61/40 cents. AM3.5–12Hz RMS близько0.72/0.95 dB. Це не встановлює, що саме слухач сприймає як електронне дрижання.

Важливе виправлення методики: короткі10ms RMS frames із sampling100Hz можуть alias-ити pitch harmonics у modulation band. Старий широкий LC-044 RMS аналіз не слід використовувати як причинний доказ AM. Новий аналіз спершу фільтрує signal power LP30Hz при native sample rate, потім семплює огинаючу100Hz.

У A66 gain-контроль діє лише в двох interiors, fades45ms, максимум±2dB. Усі PCM-семпли поза масками тотожні A64, включно з h. Pitch не коригувався. Слуховий дефект heart залишився.

### Тести з реальним українським виконанням мають пріоритет над припущенням про English guide

BigVGAN vocoder-only A39 не вводить помітного дрижання в цьому контролі; окрема SVC-конверсія вводить. Exact self-reference A53 значно кращий. Однак природний UK-вхід з іншим reference може тремтіти, а synthetic English guide іноді вже тремтить до конверсії. **Одна-єдина причина ще не доведена.**

## 6. Актуальний профіль і апаратний стек

Профіль P003-VOICE-BORISOV, primary B01:

- RU speech: source 00:12:06.800–00:12:12.000, 5.2 s, самопредставлення Голохвостого.
- UK speech: source 00:12:09.800–00:12:17.000, 7.2 s, відповідний діалоговий контекст. Не застосовувати song-only RU/UK mapping до діалогів автоматично.
- RU/UK mother singing references збережені окремими варіантами тієї самої ідентичності.
- B05/B06 low examples **виключені з ідентичності Борисова**, атрибуція Грудиніну уточнена в canonical JSON. Старий зовнішній A57 — історичний snapshot, не дозвіл використати їх як Борисова.
- Native .pt: reference_mel, speech_features, reference_f0, style, prompt_condition. CAMPPlus style — 192D. Сам embedding не є повним conditioning.
- Еталони не усереднювалися і не склеювалися в спільний acoustic prompt. Версії можуть містити те саме вихідне виконання, а не незалежні навчальні приклади.
- Українська подача може мати специфічні Щ та інші артикуляційні риси. Відділяти їх від ідентичності/тембру, перевіряти перенесення акценту на English.

Поточний перевірений runtime:

- Xeon E3-1240, AVX є, **AVX2 немає**, FMA/F16C не підтверджені. Не ставити довільні сучасні native binaries без короткого реального тесту.
- GTX1650, 4GB VRAM; PyTorch2.6.0+cu124, Python3.12.14. Поточні реальні neural forward працювали на CUDA.
- Seed-VC v1 singing: Whisper-small, F0 conditioning, CFM/DiT, BigVGAN44.1kHz/128mels/hop512. FP32, 100 Euler steps, CFG0, seed23. CFG0 прибирає додаткову extrapolation, **не conditional voice conversion**.
- Код закріплено на 51383efd921027683c89e5348211d93ff12ac2a8; source archive і його SHA у tools/seed-vc/source.json.
- Model revision 257283f9f41585055e8f858fba4fd044e5caed6e; checkpoint DiT_seed_v2_uvit_whisper_base_f0_44k_bigvgan_pruned_ft_ema_v2.pth, SHA256 42aef93ffe65857c840d270252fa040f7ba04514945ec460f3ac1ac2a96de684.
- Усі model/config revisions і SHA — tools/seed-vc/models/manifest.json. Офіційний [код](https://github.com/Plachtaa/seed-vc/tree/51383efd921027683c89e5348211d93ff12ac2a8), [моделі](https://huggingface.co/Plachta/Seed-VC/tree/257283f9f41585055e8f858fba4fd044e5caed6e). Репозиторій був архівованим під час перевірки; не вважати активним найновішим backend.
- Працездатний torch не замінювали суперечливим upstream requirements.txt. Ізольовано додано munch4.0.0; у зовнішній копії відкладено невикористані DAC/plotting imports. CUDA kernels BigVGAN не компілювалися, use_cuda_kernel=False.
- Audit не знайшов пропущених активних навчуваних checkpoint weights. Зайві параметри іншої вихідної гілки й службові buffers пояснені в weight-audit/logs. Це авторська перевірка, не незалежне рев'ю.
- Whisper.cpp small/medium quantized binaries є в shared_asr_tools, перевірений build-vulkan реально використовує GTX1650. FFmpeg аудіодекодування — CPU. Нові залежності/ваги й caches тримати поза repo та original media, без junction.

Середовище старих залежностей та перевірені CPU env guards наведено в локальному annex. Не імпортувати torch/важкі бібліотеки в головний процес інвентаризації. Python alias у Windows не працював; використовувати python_executable із runtime report.

## 7. Останній повний ланцюжок — що саме відхилено

Borisov-verse3-full-v1:

1. Чотири старі Piper spoken-line WAV із verse-3-trial/v5, без WORLD waveform, об'єднано з120ms source gaps.
2. Один Whisper semantic context; монотонний map source/vowel windows на39 нотних слотів. Target pauses мапляться до кінця відповідного source line, не всього source.
3. F0 задано безпосередньо нотами Am/110BPM, octave−12. Vowel nuclei мають пріоритет над phone masks; h boundaries уточнено. Steady semantic core лише has/heart першого рядка.
4. B01 cached mel/style/prompt → native length regulator → один CFM context → один BigVGAN forward.
5. Неактивні weights паркувалися на CPU; усі neural forwards — CUDA. Prompt+verse помістився у2048 frames.
6. Native waveform збережений. Dry має поточний local AM-control двох перших vowel cores; mix додає редакторську гітару.

Час після підготовки входів: CFM≈49.85s, з vocoder≈56.22s. Torch peak allocated≈2102MiB; у процесі nvidia-smi показував100% GPU та≈2354MiB total used. Отже, **апаратне прискорення працює, а якість лишається проблемою**.

Останні файли:

| Артефакт | Файл від work_dir | SHA256 |
|---|---|---|
| A69, відхилений mix,17.705s | exports/P003/neural-tuning/borisov-verse3-full-v1/mix.wav | 7d1ee0f0fad89f2a4247e0ae0c9f6a11c3e99373d88d0c3c5ac681f04c664d5f |
| A68, dry,17.455s | exports/P003/neural-tuning/borisov-verse3-full-v1/vocal.wav | f2d399644eea81d08b8c6efae806a6cf631cddf3057f0f5084aff79950ece2b1 |
| A64, h працює, A дрижить | exports/P003/neural-tuning/seed-borisov-h-boundary-v1/borisov-line.wav | eb40a0d30869e1d4034dc5fe4c979d89b0921784a578b0b2e09eb35d8ad395c9 |
| A66, AM-only контроль | exports/P003/neural-tuning/borisov-vowel-envelope-v1/borisov-vowel-am-control.wav | 51d4ed3b93478c6d34177231c1fd82071240928b25dc7c7999d718d6e498b494 |

У папці повного куплету також є native-vocal.wav, vocal-raw-normalized.wav, conditioning.npz, manifest.json, assembly.json, asr.txt/log/srt. Conditioning NPZ містить generated mel, score F0, slot IDs, source-time map і semantic features. Вони корисніші для offline аналізу, ніж повторне генерування без нової гіпотези.

ASR останньої проби — **не цільовий текст**:

    My dear mother is a heart-worn and kind,
    And my papa is himself a shop,
    And they never heard these feelings of mine,
    And their only son, Udakr, Udakrara.

## 8. Навігація по зовнішніх прототипах

У reports/P003/neural-tuning/:

| Скрипт | Призначення |
|---|---|
| bench-english-aligned-v1.py, repair-envelope-v2/v3.py | Історичний Chatterbox mel/DTW/envelope шлях |
| isolate-english-v1.py | A32, старий HiFT stage control |
| seed-run.py, seed-vocoder-only.py | Початковий Seed-VC і source-mel BigVGAN контроль |
| seed-cfg-control.py | Pairwise CFG0.7/0, seed reset |
| seed-uk-self-reference.py | Exact same-WAV source/reference R01 |
| build-borisov-profile.py, finalize-borisov-profile.py | Оригінальні референси й native conditioning на CUDA |
| seed-english-borisov.py | English singing guide → accepted B01 profile |
| seed-borisov-speech-control.py | Natural spoken English через той самий profile |
| seed-direct-score.py | Перший direct semantic-duration/score-F0 прототип; **містить стару voicing bug** |
| seed-borisov-vowel-fix.py, seed-borisov-h-boundary.py | Корекції voice mask, h onset і vowel core |
| borisov-vowel-envelope.py, borisov-vowel-am-control.py | Anti-aliased AM/pitch аналіз і amplitude-only діагностика |
| borisov-verse3-full.py, assemble-borisov-verse3-full.py | Останній суцільний повний куплет / GPU offload / dry+mix |

Не всі скрипти універсальні або повторно безпечно перезапускаються в тому самому output-dir. Це дослідні файли з локальними шляхами, а не повністю мігрований відтворюваний generator у pipeline. Перевірити маніфест, seed, conditioning, input hashes і output-dir перед новою операцією.

## 9. Рекомендований напрямок незалежного дослідження

Це **гіпотези для перевірки**, не встановлені причини:

1. Провести факторний контроль same-actor source/reference: exact same-content проти іншої репліки з тієї самої доріжки. Відділити acoustic cleanliness від переваги точного content match. Не повторювати висновок, що чистіша RU-доріжка сама усуне flutter.
2. Перевірити, чи узгоджуються generated-mel harmonic structure, target F0 і фактичний waveform. Розділити F0 variation, AM, spectral/formant motion, фазове биття/ревербераційний присмак. Стабільна задана F0 не гарантує стабільного звука.
3. Аудитувати source/target phoneme boundaries на реальному аудіо. Piper durations зі stress/space markers і автоматичні vowel windows вже конфліктували; фінальний /p/ мав слабкий release або transition за межами label. Повторне розтягування/фіксація цих меж без перевірки може продовжувати приголосний замість голосної.
4. Перевірити припущення про допустимість warping/утримання Whisper features як singing content. Це власний експеримент, не доказ, що офіційний SVC навчений так керувати phoneme durations.
5. Якщо потрібен інший frontend/SVS/SVC backend, обирати його за конкретною необхідністю, актуальними первинними джерелами й малою реальною runtime-пробою. Можливий напрямок — якісний нейронний English singing guide з explicit phoneme/note durations, потім identity conversion; це ще не вибране рішення.
6. Для кожного нового тесту зберігати одну контрольовану зміну, джерела/SHA, output і власні числові перевірки. Слуховий висновок не підміняти ASR чи signal metric. Не навантажувати втомленого користувача серією майже тотожних неперевірених варіантів.

Практична ознака успіху: чисті сталі відкриті голосні без електронного/ревербераційного призвуку; розбірливі всі слова, особливо has/heart, warm and kind, shop і cream of the crop; задані ноти/ритм; упізнавана ідентичність Борисова. Жодне з цих положень не випливає лише з no clipping/exit0/низької F0 error.

## 10. Правила збереження результатів

- Нові тести — в нових зовнішніх каталогах. Старі WAV, approved SHA і сталі ID не змінювати.
- Абсолютні машинні шляхи, моделі, media, caches і local-конфігурації не комітити. Не створювати junction у source/media.
- Після CSV змін — pipeline/validate.py. Він не підтверджує звук і в поточній локальній конфігурації перевіряє **0 media/evidence hashes**; важливі SHA звірялися окремо.
- Усі repo зміни — в окремій гілці/PR. Не зливати PR і не пушити main без явного дозволу. Чинний draft PR12 не є прийманням акустичної якості.
- Авторський аналіз у цій історії не є незалежним модельним рев'ю. Незалежних агентів без доручення не запускати.
- Зберігати окремо: факти/слухові відгуки, знайдені кодові помилки, неперевірені причинні гіпотези та запропоновані наступні кроки.
